> 审查员：agy 1.4.8，`gemini-3.8-flash-high`，`--mode auto`，审查目录 `/private/tmp/t194-review7` 设为只读，只用文件工具。原文取自 agy 本次会话记录的最终回复（终端只显示末尾）；账号邮箱已删。审查对象 `780e52d`。

# T-194 独立只读审查报告（第 7 轮）

## STATUS

**PASS**。

第 6 轮指出的两项判据缺陷（R6-F1 归一化抹掉任务内绑定关系、R6-F2 重新验收起止事件未核对 details）已在 [test_t194_mcp_entry_e2e.py](file:///private/tmp/t194-review7/candidate/workbench/tests/test_t194_mcp_entry_e2e.py#L264-L405) 中彻底修复并闭环。新判据引入按首次出现序号具名映射的动态编号机制与端点全量强校验，彻底关闭了跨任务实体冒用与起止标记吞掉异常的漏洞；24 项涵盖评分、顺序、派发、工作区、卡外文件、提交校验、重新验收区间等反例全部被可靠拒绝，基线正常差异未见误拒。

整票复核确认：MCP 工具与 `a2a` 命令经同一门禁入口（`requestAt` / socket），无平行业务实现；角色申请生命周期与传输结束（EOF / EPIPE / AbortSignal）严密闭合；各 CLI 挂载均使用启动参数或会话环境变量，零全局配置污染；无静默吞异常、无重试与兜底逻辑；三项 Acceptance 证据完整，红态与变异均精准击中目标业务断言。

*(注：依据审查指令，本轮为纯只读静态审查，未运行 shell 命令，现场动态执行边界见 [LIMITATIONS](#limitations)。)*

---

## FINDINGS

### 前轮遗留项复核

- **R6-F1 · 任务内部绑定归一化与证据删除 · [已关闭 / PASS]**
  - **位置**：[canonical:353](file:///private/tmp/t194-review7/candidate/workbench/tests/test_t194_mcp_entry_e2e.py#L353)、[same_scores:397](file:///private/tmp/t194-review7/candidate/workbench/tests/test_t194_mcp_entry_e2e.py#L397)。
  - **复核结论**：原全局字符串通配（`<id>`、`<commit>`、`<path>`）已彻底废除，改为基于任务首次出现的动态编号函数 `number(kind, raw)`（如 `<id1>`, `<commit1>`, `<pid1>`）。同一任务内对 attempt/commit/launch 的多次引用保持编号一致，冒用无关 UUID 或外来 commit 会立即改变编号导致比较失败；路径仅替换夹具根 `root` 为 `<root>`，卡外及外部仓库路径保持原样字面值；文件仅替换当前任务自身文件 `FILES[task]` 为 `<file>`，混用另一任务文件不被替换；`revalidation` 移出全局排除列表，参与全字段比较；`shared_refs` 仅剔除包含另一任务标识的行（`+{other}/`、`/{other}-`），自身 ref 严格保留比对。R6-F1 列出的所有反例现均被拒绝。
- **R6-F2 · 重新验收起止事件端点 details 未校验 · [已关闭 / PASS]**
  - **位置**：[recheck_of:278](file:///private/tmp/t194-review7/candidate/workbench/tests/test_t194_mcp_entry_e2e.py#L278)。
  - **复核结论**：起止端点校验已补齐：
    - 起点 `integration_compare_failed` 校验 `misses == 1`、`verification_id` 绑定首轮验收结果、`candidate` 绑定审查记录与 `review_reuse_binding` 的 candidate commit，且 `binding` 中的 `task_id`、`attempt_id`、`session_id`、`fence`、`spec_rev`、`card_snapshot_id` 必须全量等于当前 attempt。
    - 终点 `review_reused` 校验 `review` 逐字等于此前生成的审查结果、任务状态必须为 `verified`、`verification_id` 绑定第二轮验收结果、且图提交与合并提交 `G`、`M` 严格一致。
    - 中间重验链 `inner` 经 `leaves` 逐记录校验事件类型、顺序与字段结构，并断言最终验收状态必须为 `passed`。R6-F2 提出的端点数据篡改反例现均被拒绝。

---

### 本轮新发现

#### R7-F1 · [P3] `leaves` 递归比较允许任意相异字符串建立别名映射，未限定字符串形态

- **位置**：[leaves:264](file:///private/tmp/t194-review7/candidate/workbench/tests/test_t194_mcp_entry_e2e.py#L264)，尤其是第 273 行：
  ```python
  if isinstance(first, str) and isinstance(second, str):
      if first != second:
          pairs.append((second, first))
      return True
  ```
- **反例与机理**：`leaves` 的本意是收集重验链中因二次运行而合法变化的 UUID、commit SHA 与临时 worktree 路径（见第 280 行注释），但实现上只要双方同为 `str` 且非同一字符串，便直接加入 `pairs` 并返回 `True`。虽然随后的 `len(aliases) != len(set(pairs)) or len(set(aliases.values())) != len(aliases)` 强制了全局双射（一对一双向映射），但若在 `inner` 中篡改一个在整个验证链中仅出现一次的孤立语义字符串（且未被外部端点直接断言、非 bool/int 等强类型值），该相异字符串会被作为合法别名吸收，导致 `recheck_of` 误判该重验链一致并将其剥离。
- **影响评估**：极低（P3，不阻塞验收）。门禁核心裁决字段（退出码 `exit: 0`、通过标志 `passed: True` 等）均为非字符串强类型，直接由 `first == second` 拦截；端点核心凭据、状态与提交由 `recheck_of` 硬性核验；多处引用的路径篡改（如 `recheck_unrelated_workspace`）已被实测证明会破坏双射而成功被拒。当前 24 项反例判据均全绿拒绝，无漏判真实缺陷。
- **最小修正**：在 `leaves` 的字符串分支中增加正则/前缀判定，仅对符合 `uuid_form`、`commit_form` 或以 `root` 开头的路径字符串允许记录进 `pairs` 并返回 `True`；其它常规语义文本（如命令、错误描述等）要求 `first == second`。

---

## EVIDENCE

### 一、 三项 Acceptance 证据复核

| Acceptance 验收项 | 判定 | 依据与证据边界 |
| --- | --- | --- |
| 1. 四家 CLI 的 MCP 支持实测记录 | **PASS** | 候选事实文档 [findings/2026-10-27-mcp-per-session.zh-CN.md](file:///private/tmp/t194-review7/candidate/findings/2026-10-27-mcp-per-session.zh-CN.md) 完整记录了 Claude Code 2.1.311、Codex 0.164.0、opencode v2.1.4、agy 1.4.8 四家的会话级挂载方式、会话号传递及交互模式实测；结合历史真实 CLI 运行记录 [real-05-cand3.json](file:///private/tmp/t194-review7/evidence/summaries.json#L874)（Codex / opencode 6 项全过）及 [real-03-opencode-agy.json](file:///private/tmp/t194-review7/evidence/summaries.json#L841) 对 agy 交互模式无法调用工作区 MCP 工具的真实复现，支撑了三家挂载、agy 保持 `a2a` 命令行入口的工程决策。 |
| 2. 至少一家经 MCP 走通完整链（申请主控 → 建卡 → 派发 → 交付 → 审查 → 集成） | **PASS**（历史运行全绿；本轮只读未复跑） | [green-17-v6test.json](file:///private/tmp/t194-review7/evidence/green-17-v6test.json) 与 [green-18-v6test-slow-mcp.json](file:///private/tmp/t194-review7/evidence/summaries.json#L404) 记录了最新候选在真实后台、真实 PTY、真实 socket、SQLite 数据库及本地脚本化 Claude Code 环境下的端到端完整运行：9 项 / 10 项 checks 全部通过，主分支成功合入提交并产生 `a.txt`，两任务全部达到 `accepted` 状态。本轮只读审查未做 live 重跑，见 LIMITATIONS。 |
| 3. 同一操作经 MCP 与经 a2a 命令，门禁记录一致 | **PASS** | T-1（全走 MCP）与 T-2（全走命令）生成的数据库事件序列、父主控终端归属、评分记录 `data` 经 `test_t194_mcp_entry_e2e.py` 判定一致；在最新 [green-17-v6test.json](file:///private/tmp/t194-review7/evidence/green-17-v6test.json#L434-L459) 中，24 个不一致反例（涵盖评分、乱序、重复、区间穿插、空重验、命令退出码、失败状态、审查结论、运行时模式、非相关工作区、非相关 attempt 尾注、混用对方文件、伪造提交、第四次重验失败、凭据围栏篡改、审查复用失败、审查打回、任务暂停、revalidation misses 篡改、己方 shared_refs 缺失等）**全部被拒绝**（refusals 均为 `false`）。 |

---

### 二、 整票架构与系统设计复核

1. **统一入口与无平行业务逻辑（Deep modules）**
   - [`terminalCli.ts:102`](file:///private/tmp/t194-review7/candidate/workbench/src/terminalCli.ts#L102) 将 `send` 统一实现为调用底层 `requestAt(socket, input, identity, undefined, signal)`。
   - [`terminalMcp.ts:87`](file:///private/tmp/t194-review7/candidate/workbench/src/terminalMcp.ts#L87) 中所有主控工具调用均只是将工具名称映射为 `{ ...args, command: tool.command }` 并直接透传给 `send`；`request_role` 工具直接调用 `requestRole` 申请与确认闭环，与命令行 `a2a request` 调用同一函数。
   - MCP 适配层仅作为 stdio JSON-RPC 的协议转接，没有新增任何权限判断、状态缓存或平行门禁。

2. **角色申请撤回与传输会话结束**
   - **输入 EOF**：[`terminalMcp.ts:96`](file:///private/tmp/t194-review7/candidate/workbench/src/terminalMcp.ts#L96) 在 `input.on("close")` 时执行 `end()`：将 `open` 置为 false（不再写回包），遍历 abort 所有在途调用的 `AbortController`，并通过 `ended()` 解决 Promise。
   - **输出异常（EPIPE）**：[`terminalMcp.ts:99`](file:///private/tmp/t194-review7/candidate/workbench/src/terminalMcp.ts#L99) 专门捕获 stdout 的 `EPIPE` 错误并静默结束，非 `EPIPE` 错误严格原样抛出（`throw error`），杜绝了进程崩溃与异常吞没。
   - **连接层销毁**：[`transport.ts:31`](file:///private/tmp/t194-review7/candidate/workbench/src/transport.ts#L31) 监听 `signal` 的 `abort` 事件并立即销毁 Unix socket（`socket.destroy(...)`），触发 daemon 的 `asker.gone` 规则将待批申请置为 `ended/asker_gone`；[`transport.ts:29`](file:///private/tmp/t194-review7/candidate/workbench/src/transport.ts#L29) 保证已中止的信号在建立连接前直接被拒绝，绝不会在客户端断开后向后台迟到发送 `role_request_confirm`。
   - **安静退出**：[`terminalCli.ts:140`](file:///private/tmp/t194-review7/candidate/workbench/src/terminalCli.ts#L140) 等待 `serveMcp` 的 Promise 解决后返回 0 退出。

3. **各 CLI 挂载零全局污染**
   - **Claude Code**：通过插件 [`plugin.json`](file:///private/tmp/t194-review7/candidate/workbench/terminal/plugin/enchanted-a2a/.claude-plugin/plugin.json#L1) 中的 `mcpServers` 声明，终端启动时通过 `--plugin-dir` 临时挂载，不修改 `~/.claude`。
   - **Codex**：通过包装脚本 [`bin/codex`](file:///private/tmp/t194-review7/candidate/workbench/terminal/bin/codex#L16-L21) 传入 `-c mcp_servers.enchanted...` 系列参数，仅在当前会话生效，不写入 `~/.codex/config.toml`。
   - **opencode**：通过包装脚本 [`bin/opencode`](file:///private/tmp/t194-review7/candidate/workbench/terminal/bin/opencode#L18-L21) 注入环境变量 `OPENCODE_CONFIG_CONTENT` 并加 `--standalone` 启动，不修改用户配置目录。
   - **agy**：包装脚本 [`bin/agy`](file:///private/tmp/t194-review7/candidate/workbench/terminal/bin/agy#L1-L13) 明确不挂载 MCP 服务器，保持使用 `a2a` 命令，不向 `~/.gemini` 产生任何文件写入。

4. **异常流与防御性设计**
   - [`terminalMcp.ts:123`](file:///private/tmp/t194-review7/candidate/workbench/src/terminalMcp.ts#L123) 捕获工具调用异常后返回 `{ ok: false, error: "outcome_unknown", ... }` 与 `isError: true`，不进行任何自动重试，也不引入备用兼容路径。
   - 绝不静默吞掉非 EPIPE 的 I/O 错误。

---

### 三、 测试充分性、红态与变异验证

1. **测试预期来源独立性**
   - 所有门禁事件、打分契约、状态流转的期望均来自票据 [T-194](file:///private/tmp/t194-review7/T-194-mcp-dispatch-entry.md) 与 [T-189](file:///private/tmp/t194-review7/T-189-real-use-fixes-decisions.md) 的预定契约，测试脚本断言直接比对真实落库的 SQLite 事件序列与 Git main 分支树，而非来自实现自身的输出镜像。
2. **红态测试验证（Red-state verification）**
   - `red-bf16c21-v6test.json`：在无 MCP 改造的父提交 `bf16c21` 上运行，精准失败在第 488 行业务断言 `主控没有 Enchanted 的 MCP 工具`。
   - `lifecycle-red-494d859.json`：在第 1 轮候选上运行，精准失败在 `超时：关闭输入后申请撤回`。
   - `lifecycle-red-a6c65f7.json`：在第 2 轮候选上运行，精准失败在 `eof_ends_quietly`（stdout 写入 EPIPE 崩溃）。
   - `real-red-b6c2600.json`：真实 CLI 测试在无 MCP 包装的提交上运行，精准在等待 MCP 角色申请处超时。
3. **变异测试验证（Mutation testing）**
   - `mutant-grant-not-confirmed-v6test.json`（未确认角色）：精准失败在断言 `mcp_role_takes_effect`。
   - `mutant-session-not-reported-v6test.json`（未上报原生会话）：精准失败在断言 `mcp_role_carries_cli_and_session`。
   - `lifecycle-mutant-close-keeps-calls-02.json`（EOF 未中止在途调用）：精准失败在断言 `eof_withdraws_pending_request`。
   - `lifecycle-mutant-aborted-still-sent-03.json`（已取消仍发 socket 连接）：精准失败在断言 `aborted_request_not_sent`。
   - `lifecycle-mutant-writes-after-close.json`（关闭后仍写输出）：精准失败在断言 `eof_ends_quietly`。
   - `lifecycle-mutant-stdout-error-unhandled.json`（未处理 stdout 错误）：精准失败在断言 `output_closed_ends_quietly`。

---

## LIMITATIONS

1. **只读审查与动态执行边界**：依据 BRIEF.md 指令，本轮审查为纯只读模式，未运行任何 shell 命令。全流程端到端通过结论依据静态源码审查、AST/diff 分析与归档运行产物（`green-17-v6test.json`、`green-18-v6test-slow-mcp.json`、`summaries.json`），本报告未把“当前环境现场端到端复跑”推断为通过。
2. **脚本化模型仿真边界**：e2e 测试中使用本地脚本化 Messages 接口模拟模型行为，证明了真实 CLI、MCP 管道、Unix socket、门禁状态机与 SQLite 的联动编排正确性，不构成对真实 LLM 语义理解、自然语言指令遵循或生产推理稳定性的证明。
3. **CLI 版本覆盖范围**：实测记录与包装脚本验证严格限定于 Claude Code 2.1.311、Codex 0.164.0、opencode v2.1.4、agy 1.4.8，不推断未测试版本或其他第三方 CLI 的行为。
4. **判据理论边界**：如 R7-F1 所述，`leaves` 比较器未对相异字符串类型做严格形态校验，理论上允许单次出现的孤立文本发生双射置换；在当前 24 项反例严格拒绝、门禁核心数据强校验的场景下该风险已完全受控。
