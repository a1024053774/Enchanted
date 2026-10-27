# T-194 独立只读审查（第 3 轮）

## STATUS

**INCOMPLETE**。本轮定向修复 **PASS**：第 2 轮 F2 已在传输生命周期的根因层关闭；第 1 轮 F1 仍保持关闭，未确认新的生产代码缺陷。当前候选的完整“交付 → 审查 → 集成”及两入口完整记录一致性未取得本轮绿色证据，因此不将整票验收上调为 PASS。

TARGET：`/private/tmp/t194-cand3`，`058698568b7e6c0c7e52b3fa3e023571227241da`。重点审查 `1d3d022 → 0586985` 的四文件修复，并简要复核相对 `ed5a63b` 的 T-194 整票差异；父提交 T-195 不在范围。开始、结束的 HEAD 与 Git 状态一致，唯一未跟踪项都是既有 `workbench/node_modules`。未修改候选、未提交；本轮产物全部写入 review3。

依据为 T-194 三项 Acceptance、T-189 第 3 条、既有“调用方停止等待即撤回申请”的角色契约。外部依据也独立核对了：[MCP 2025-06-18 生命周期规范](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle#stdio)规定客户端先关闭服务器输入，再等待退出；[官方 TypeScript SDK 的 stdio 关闭说明](https://ts.sdk.modelcontextprotocol.io/v2/serving/stdio#shut-down-cleanly)描述 EOF 中止在途请求且不再回答。SDK 说明用于独立校验关闭语义，不代表本项目使用了该 SDK。

沿用 **Ubiquitous language**：终端身份负责权限，原生会话号是调用方报告的数据。以真实后台、终端、MCP 子进程的 **Tracer bullet** 检查关闭边界；按 **Deep modules** 检查后台仍承担角色与门禁规则，协议层只承担传输生命周期。

## FINDINGS

### F2 · 本轮关闭：PASS

根因修复在正确负责层：

- [terminalMcp.ts:84](/private/tmp/t194-cand3/workbench/src/terminalMcp.ts:84) 的会话状态统一控制写回，成功与异常回包均经同一 `write`。结束时先将 `open` 置为 false，再 abort 在途调用，避免 abort 引起的异步拒绝继续向关闭的会话写回。
- [terminalMcp.ts:96](/private/tmp/t194-cand3/workbench/src/terminalMcp.ts:96) 将 EOF 与 EPIPE 归入同一个结束函数。它中止当前后台连接，由 `transport.ts` 和后台现有 `asker.gone` 规则撤回申请，没有复制角色状态机。
- [terminalMcp.ts:99](/private/tmp/t194-cand3/workbench/src/terminalMcp.ts:99) 只将 stdout 的 `EPIPE` 解释为客户端不再读输出，其他错误原样抛出。没有增加重试、备用 API、成功兜底或吞掉任意输出错误。
- [terminalCli.ts:141](/private/tmp/t194-cand3/workbench/src/terminalCli.ts:141) 等待 `serveMcp` 返回的会话结束 Promise，再返回 0；输出先断开时不再等一个可能不会发生的 stdin `end`。这同时解决了实现中保留的退出码 13 失败。

独立真实入口探针 [probe-v3-lifecycle-01.json](probe-v3-lifecycle-01.json) 完成标准初始化后验证：

1. 待批申请期间关闭 stdin、保留 stdout：申请进入 `ended/asker_gone`，迟到批准返回 `request_not_pending`，`confirmed_at=null`、角色为空；stdout 无关闭后回包，stderr 为空，退出码 0。
2. 先关闭 stdin、再立即关闭 stdout 读取端：同样撤回申请、拒绝迟到批准、无角色，stderr 为空，退出码 0。没有逐项取消通知或进程信号。
3. **新增独立场景**：待批申请期间只关闭 stdout 读取端，保持 stdin 打开，再发 ping 让写入检测到 EPIPE。另一个仍等待的角色申请随即撤回，迟到批准被拒，角色为空，stderr 为空，退出码 0。这排除了“只消除异常日志、没有统一中止其他调用”的修法。

候选自身的“输出关闭后用户拒绝申请”场景也以 0 退出，没有未处理 EPIPE，见 [candidate-lifecycle-01.json](candidate-lifecycle-01.json)。

非 EPIPE 的独立边界检查向实际 CLI 进程的 stdout 发出带新 sentinel 的 `EIO` 错误事件：原错误出现在 stderr，栈指向 `terminalMcp.ts:100`，进程退出码 1，见 [non-epipe-01.json](non-epipe-01.json)。这是错误事件注入，证明分支不吞其他错误；没有把它称为操作系统真实产生 EIO 的端到端证据。

### F1 · 保持关闭；正常路径定向复验：PASS

[transport.ts:29](/private/tmp/t194-cand3/workbench/src/transport.ts:29) 仍在创建连接前拒绝已中止信号；申请与后续确认仍共用该 signal。EOF 和 EPIPE 都经同一 abort 关闭后台连接，由 [daemon.ts:280](/private/tmp/t194-cand3/workbench/src/daemon.ts:280) 的既有规则撤回待批申请。

本轮真实入口覆盖通知取消、用户拒绝、正常批准与确认，以及批准成功后 EOF。通知取消返回 `outcome_unknown` 并撤回；正常批准记录确认且终端成为 executor；正常批准后的原生会话号为本轮输入的 `review3-sentinel-4`。已确认角色在 MCP EOF 后仍保留，符合身份绑定终端的边界。

[probe-v3-run-wait-01.json](probe-v3-run-wait-01.json) 使用真实后台、真实 Claude worker、隔离 HOME 与本地脚本化模型：正常等待约 **12.633 秒**后返回 `run_deadline`；另一场景在 run 已保存后关闭 MCP stdin，服务器以 0 退出且没有回包，此时数据库 run 仍为 `running`，约 **12.705 秒**后才按自己的期限进入 `deadline`。每个任务只观察到一个 run，终端角色保持 executor。修复没有把“停止等待”变成回滚后台工作。此证据只证明有界等待、断开与自身超时，不证明成功交付或实等 660 秒。

### 完整流程重验缺口：INCOMPLETE

原样运行候选 `test_t194_mcp_entry_e2e.py`，在第一轮脚本化模型请求中失败，尚未进入原来的八项断言：[candidate-fullflow-01.json](candidate-fullflow-01.json)、[stderr](candidate-fullflow-01.stderr.txt)。

这次失败是验收脚本的启动竞态：`plan` 在 [test_t194_mcp_entry_e2e.py:81](/private/tmp/t194-cand3/workbench/tests/test_t194_mcp_entry_e2e.py:81) 看到尚无具体 MCP 工具名便断言入口不存在；对应 Claude 会话明确记录 `pendingMcpServers=["plugin:enchanted-a2a:enchanted"]`，并提示先用 ToolSearch 等待连接。随后同一次运行的 MCP 日志记录连接成功、`hasTools=true`。原始 [Claude 会话](t194-3u51u35u/home/.claude/projects/-private-tmp-t194-review3-t194-3u51u35u-demo/91f549ec-1572-41a3-88e5-8d10dc1b0827.jsonl) 和 [MCP 日志](t194-3u51u35u/home/Library/Caches/claude-cli-nodejs/-private-tmp-t194-review3-t194-3u51u35u-demo/mcp-logs-plugin-enchanted-a2a-enchanted/2026-10-27T14-43-38-552Z.jsonl) 均保留。因此不能从这次断言失败推出 v3 挂载回归。

本轮另写了有界审查探针 [probe_claude_discovery.py](probe_claude_discovery.py)：复用原场景夹具，在未拿到具体工具名时先发一次 `ToolSearch(query="+enchanted")`，后续仍从真实工具表取得名称；保留原前四项断言，完成角色与会话核对后停止。结果 [probe-claude-discovery-01.json](probe-claude-discovery-01.json) 四项 **PASS**，并观察到实际调用与后台确认记录。没有伪造工具表，也没有把这个缩小场景标成完整流程 PASS。

候选测试未修改。最小后续动作是由实现方让完整验收脚本先经真实 ToolSearch 等待服务器连接，再保持原八项断言重跑；在允许既有 worker 提交路径运行的环境取得当前候选完整证据。第 2 轮在 worker 提交阶段另受 `sandbox-exec: sandbox_apply: Operation not permitted` 限制；本轮未推进到该阶段，不能声称这项限制已消失或是本轮失败原因。

## EVIDENCE

### 执行、独立判据与反事实

精确命令、退出码及清理核对见 [execution-index.json](execution-index.json)；反事实详见 [counterfactual-executions.json](counterfactual-executions.json)。运行 Node `v26.5.0`、Claude Code `2.1.311`。模型场景均使用本地脚本化 Messages 服务，没有供应商模型调用；结论取自后台状态、真实 socket、进程输出／退出、CLI 自己的会话记录，不取自模型自报。

| 检查 | 本轮观察 |
| --- | --- |
| 候选六项生命周期检查 | [candidate-lifecycle-01.json](candidate-lifecycle-01.json)：六项 PASS，命令退出码 0，测试 stderr 为空。 |
| 独立生命周期与权限参数伪造 | [probe-v3-lifecycle-01.json](probe-v3-lifecycle-01.json)：EOF 无回包、双端关闭、EPIPE 撤回另一个在途申请、取消、拒绝、批准及新会话 sentinel 均通过。无角色时伪造 `command` 和 operator `identity` 仍得到 `approved_role_required`。 |
| 上一版反事实 | [candidate-red-v2-01.json](candidate-red-v2-01.json)：在 `1d3d022` 上重跑，申请撤回通过，但 `eof_ends_quietly` 因实际收到关闭后的 `outcome_unknown` 回包失败。 |
| 去掉关闭后的写回限制 | [candidate-mutant-write-01.json](candidate-mutant-write-01.json)：同一无回包断言拒绝该坏实现。 |
| 去掉 stdout 错误监听 | [candidate-mutant-stdout-01.json](candidate-mutant-stdout-01.json)：输出关闭场景实得未处理 EPIPE、被测进程退出码 1，`output_closed_ends_quietly` 失败。 |
| 去掉关闭时 abort | [candidate-mutant-close-01.json](candidate-mutant-close-01.json)：真实后台申请未在期限内撤回，目标等待断言失败。 |
| 已中止仍发送 | [candidate-mutant-aborted-01.json](candidate-mutant-aborted-01.json)：前五项通过，socket 对端实际收到 1 次连接，`aborted_request_not_sent` 失败。 |
| 非 EPIPE 错误 | [non-epipe-01.json](non-epipe-01.json)：合成 EIO 错误事件仍抛出，原 sentinel 可核对，退出码 1；没有伪装正常结束。 |
| 后台断开与包装脚本 | [probe-v3-boundaries-01.json](probe-v3-boundaries-01.json)：故障 socket 对端接收一次请求后断开，MCP 返回 `outcome_unknown`，观察窗口无重放；包装脚本的 argv／环境边界检查通过。 |
| 有界 run 等待与 EOF 后独立推进 | [probe-v3-run-wait-01.json](probe-v3-run-wait-01.json)：两项 PASS，边界见上文。 |
| 真实 Claude 的工具与角色 | [probe-claude-discovery-01.json](probe-claude-discovery-01.json)：四项 PASS；完整原样运行为 INCOMPLETE，未隐去失败。 |

上述五个反事实命令都以 1 退出。其 JSON 保持脚本原有 `INCOMPLETE`，没有改写成 PASS；可用证据是它们在目标行为处的具体失败，而非“运行失败就算抓到坏实现”。EPIPE 崩溃是对应断言要检测的实际缺陷，不是依赖缺失。

新检查的预期来自契约：EOF 表示会话终止，终止后不再回答；停止等待撤回待批申请，之后不能确认；正常等待批准仍须确认生效。退出码 0 来自正常关闭的交付要求，非 EPIPE 仍抛出来自不得把未知输出故障伪装成正常结束的边界。断言没有导入生产常量、生产辅助函数或生产输出作为答案；Fixture 只创建后台、项目和终端凭据，申请状态从后台读取，退出与字节从真实子进程读取。

精确批准／确认窗口过窄，候选第六项用实际 Unix socket 对端隔离 `requestAt` 的发送前中止条件；它与“删掉检查后对端收到连接”的反事实相互印证。该项不能替代整个竞态的端到端穷举。

已只读核对主仓库证据中的 `lifecycle-green-04.json`、`lifecycle-green-03.json`、旧版本失败和四种生命周期变体。`green-03` 的退出码 13 失败确实保留；`green-04` 的六项与本轮重跑一致。这些历史文件的 `revision=null`，不单凭名称绑定冻结候选；本轮运行明确使用候选绝对路径，开始／结束版本见 [candidate-start.json](candidate-start.json)、[candidate-final.json](candidate-final.json)。

### 前两轮其余 PASS 项在 v3 上的复核

| 范围 | 结论与边界 |
| --- | --- |
| 同一门禁、权限信封、无平行业务入口 | **PASS（所审静态路径及定向入口）**。普通 MCP 工具仍映射到原 `send`，终端凭据固定于外层信封；后台核对角色、项目后进入同一个 `gates.call`。参数伪造检查再次拒绝；没有新增角色、门禁或任务的第二套实现。 |
| 未知结果、不重放 | **PASS（取消／故障对端范围）**。真实入口重测结果未知与一次请求；v3 只改变会话已结束后的结果写回，不自动重发。 |
| 包装脚本和全局配置边界 | **PASS（静态与 argv／环境）**。Codex 显式 `-c ...tool_timeout_sec=23` 仍位于注入 660 后，用户 developer instructions 未被改写；opencode 默认配置、用户配置、显式 standalone 分支均重测。接收端为 stub，不外推真实 CLI 所有配置解析。新增生产路径未见全局配置写入。 |
| Claude 挂载、无角色拒绝、原生会话号 | **PASS（本轮真实 CLI、脚本化模型）**。有界探针前四项通过，后台会话号等于该 Claude 自己的 JSONL 文件名；会话号仍不是认证信息。 |
| 四家 CLI 取舍 | v3 未改包装脚本、插件和会话来源。既有真实 Codex／opencode 申请拒绝记录、agy 交互模式 NO_TOOL 及 print 模式回显，仍支持原限定结论。本轮未重跑这三家真实 CLI 或真实供应商模型，不宣称普遍版本兼容。 |
| 完整交付、两入口记录、worker 归属、评分 | **INCOMPLETE（本轮重验）**。保留主仓库 `green-08.json` 的八项历史 PASS，但没有用它代替 v3 完整证据。`same_gate_events` 仍只比较选定事件的首次出现／字段集合及部分值，不能扩大成全部原始事件的顺序、次数和字段值相同。 |
| README | **PASS（静态及已测关闭路径）**。新增句与 EOF、实际写入检测到 EPIPE 后结束会话的观察一致。它不提供操作系统尚未报告断管时就能预知客户端关闭的保证。 |

复现本轮定向信号时换用新文件名，避免覆盖证据：

```sh
cd /private/tmp/t194-review3
python3 -B run_candidate_test.py test_t194_mcp_lifecycle_e2e.py --summary /private/tmp/t194-review3/candidate-lifecycle-replay.json
python3 -B probe_v3_lifecycle.py --summary /private/tmp/t194-review3/probe-v3-lifecycle-replay.json
python3 -B run_review_probe.py probe_claude_discovery.py --summary /private/tmp/t194-review3/probe-claude-discovery-replay.json
```

F2 的防回归负责层仍是现有 `test_t194_mcp_lifecycle_e2e.py`，候选现在已有对应检查。删除写回限制、去掉 stdout error 监听都能被目标断言拒绝；无需再增加仅靠文字约束的规则或平行测试框架。

## LIMITATIONS

- **整体 INCOMPLETE 的具体缺口**是当前候选的完整交付、审查、集成及两入口记录重验。原始全流程失败保留，有界 Claude 探针只补齐前四项；没有将缩小检查范围等同于完成整票验收。本轮授权为只读审查，不修候选验收脚本或调整 worker 沙箱。
- 没有实等 120／600／660／720 秒边界，没有穷举批准／确认、撤权、重复请求 id、全部工具、并发或完整 MCP 协议。12 秒 run 场景不证明长时成功交付。
- stdout 读取端关闭只有在写入产生 EPIPE 时才被此处理器发现；本轮证明的是检测到该传输终止后统一结束会话、撤回仍在等待的申请，没有宣称能在尚无写入时立刻察觉对端读取端关闭。
- Agent 产品证据本轮主要达到真实进程、socket、CLI 与后台存储边界；脚本化模型不证明真实模型理解与自主规划，未涉及生产外部写入。检索／记忆与媒体生成能力不属于本次传输修复范围，N/A；文件交付与审查路径按上文明确为未完成重验。
- 候选不含 `.project-map/MAP.md`，未初始化或补写；主仓库只读 status 开始、结束均为 Problems 0、Stale living docs 0，收尾输出见 [project-map-status-final.txt](project-map-status-final.txt)。`git diff --check ed5a63b HEAD` 退出码 0。这些不能替代行为验收。
- 所有业务操作只发生于本轮隔离夹具；模型场景使用隔离 HOME 和本地服务。10 个后台夹具均已停止，收尾核对各自的 control socket 与 daemon.pid 均不存在，见执行索引。源码坏变体在 review3 内独立副本执行，未修改冻结候选或丢弃旧失败现场。
