# T-056 决定 04 工程交付

**PASS（本轮获批修正及检查）；保持 open，待执行主控自审与关闭。** 已完成受管结构化答复显示的真实入口红绿、已知坏实现反例、最终冻结候选 gap 补验和相关检查。按决定 04 没有启动独立审查，不代替执行主控宣布整票已验收、集成或关闭。之前两次 FAIL、一次 INCOMPLETE 与所有原始失败均保留。

依据 `ready_rev: 2`、[controller-decision-04.md](controller-decision-04.md) 和主控 #12。本轮父修订 `ddcff9a643e15dd68c18186782e688e492bb44a8`；最终 fork **`e9545960c50e4d0f8d687aef0da8073b2419adaa`**，分支 a2a，未 push。[最终源码与差异](final-source-71/revision.json)、[版本及检查索引](final-versions-71.json) 绑定该候选。

## 修正与验收

Tracer bullet 走受控待答请求、真实 WS、SQLite 输入/人工介入、实际 web 解析器。Deep modules 的派生事实仍在门禁同一事务生成；Ubiquitous language 沿用 request、channel、用户输入与人工介入。

修正只涉及门禁核心、web 解析器、回归测试和 README 四个文件。派生事件新增 `request_id` 与 `channel`，取自原输入；解析器仅对 `form: answer`、`channel: ws-rpc`、message 为空且 request 非空的组合接受无消息身份。消息渠道或问题面板的 answer 仍要求有效 message；空/错误 request、错误 message、错配 attempt 继续拒绝。没有发明 messageId、吞掉格式错误、改 provider 语义或界面布局，也没有修改历史记录。

| 检查 | 结果与证据 |
| --- | --- |
| dd 真实入口红态 | PASS（缺陷红态证据）：[answer-red-62](answer-red-62/answer-oracle.json) 的待答 request 在实际 pending repository 中为 pending；受管 WS 答复正常接受且相同命令去重，输入及人工介入各一条，实际 web 解析器因空 message 抛错，helper 退出 1。失败不是准备错误 |
| 新回归测试反事实 | PASS：answer-unit-red-63.json 在尚未修改产品的 dd 上退出 1；新增测试来自决定 04 的有效/无效身份组合 |
| 冻结候选真实入口绿态 | PASS：[answer-final-74](answer-final-74/answer-oracle.json) 及 structured-answer-fixture.json 保留真实请求、原答复、SQLite 派生事件、重复命令和实际解析结果；attempt 预期来自独立 gate dispatch 收据，不取输入记录自身当答案。所有启动记录均为 e954、受控文件干净 |
| 全部 answer 放行的 mutant | PASS（反例拒绝）：[broad-answer-mutant-final-74.json](broad-answer-mutant-final-74.json) 在外部缺 request 反例上退出 1，明确为 `Invalid answer accepted: missing-request`；不是 import/启动错误。实际解析器同一组正反例通过 |
| 当前候选 gap 分支 | PASS：[gap-final-69](gap-final-69/gap-oracle.json)。普通 WS 输入、ingress、去重 INSERT 同时失败，两个业务 RPC 仍正常接受，observer 保持 healthy；来源不可恢复时只补一条 gap，覆盖序号 52–54，项目/thread 正确、task/attempt 为空、原因保留，未猜为用户或 ui-derived action、未派生人工介入；再次重启全部输入与门禁事件逐条相同 |
| gap 版本及入口绑定 | PASS：初次启动和两次恢复均保存正确 fork cwd、`./a2a/scripts/bun` argv、完整 e954、干净受控状态和 ready source_revision；新的隔离目录，原故障库保留。恢复只在完整副本去掉夹具故障 trigger |
| 最终静态与相关测试 | PASS：final-*-69.command.json / log，fmt、lint、全 workspace typecheck、migrations:check、gates 10、server 77、web 5 均通过；web 为 humanIntervention 与 uiFontSize 两个实际测试文件，不把未匹配文件算成已跑 |
| 最终既有 35 项 | PASS：[编排 18/18](orchestration-final-69/command.json)、[交付 8 + 恢复 9](delivery-recovery-final-69/command.json)，完整版本 e954，原断言与期限未变 |
| 独立审查/执行主控自审 | 本轮不启动独立审查，按决定 04 交执行主控自行审查差异与证据；worker 未代其审查、验收或关闭 |

待答请求通过实际引擎的 `user-input.requested` activity 建立，读取实际持久 pending repository 确认，不再用只有孤立 UUID 的答复目标。该状态是授权的受控 provider 状态，provider 全部禁用；证明 WS 记录和显示解析，不主张真实模型发问或 provider 回调送达。产品 provider turn 为 0。此前 c7 的真实问答与后续重放仍在旧报告中，未把它冒称为本轮新模型验证。

## 失败现场和重放

failure-modes-61.md 在改产品前列出了显示、身份、重复、旧消息和 gap 的失败方式。answer-red-62 与 answer-unit-red-63 原样保留。中间版本 23ec 的功能绿态、mutant、35 项也保留，但它的 typecheck 首轮失败，不用来为最终 e954 背书：新测试把 `attempt` 直接写在严格事件参数的对象字面量中，触发 TS2353；改为命名 fixture 变量，未改断言或产品规则，e954 的完整检查通过。

gap-final-66 的首轮恢复断言通过后，清理 helper 用 kill(pid, 0) 等待自己已退出但尚未 wait 回收的子进程，误报未退出。该次整体不是 PASS；原库、恢复副本、日志与异常保留。gap-entry-68.py 在发 SIGTERM 后对自己的 Popen 调用 wait，再核对退出，最终两个重启完成。没有把清理失败当产品失败，也没有覆盖现场。

主要入口可用新标签重放：

```sh
python3 evidence/2026-10-09-batch11/T-056/start-server-61.py NEW_ANSWER
python3 evidence/2026-10-09-batch11/T-056/answer-entry-73.py NEW_ANSWER
python3 evidence/2026-10-09-batch11/T-056/start-server-61.py NEW_GAP
python3 evidence/2026-10-09-batch11/T-056/gap-entry-68.py NEW_GAP
```

NEW_ANSWER、NEW_GAP 须为未使用的标签，gap 要求冻结干净候选。answer 结束后用 cleanup-fixtures-70.py 加新 launch 文件核对并停止自建服务；gap helper 自己核对 PID、启动时间、argv 并收尾。实际外部命令、WS 输入、协议帧、request 状态、查询结果及 parser stdout/stderr/退出码都在相应证据目录。35 项完整重放命令、环境与源码副本在各 command.json/sources/；静态检查 helper 的输出名固定 69，再跑需另存新编号，不能覆盖旧文件。

本轮所有自建服务已停止，见 cleanup-final-70、cleanup-answer-final-74 及 gap-oracle 内的 cleanup。完整 Git/worktree 与门禁场景在 retained-decision04-git-gates-71.tar.gz、retained-answer-final-75.tar.gz，索引记录路径，原目录保留；原生 journal/profile 留本机，不打包认证，不登记 gitlink。未读写正式工作台、Herdr、用户配置、dist 或依赖，未 push。他人的 `.grok/` 与 controller-poll.log 保留。

本轮没有新增上游接入文件；完整票此前的五个上游接入仍见 RESULTS-03，当前差异仅四个获批模块文件。没改 AGENTS、CONTEXT、地图、其他 ticket 或 attempt。README 已同步，所有报告只写中文，旧文不覆盖。相关 checks 通过后没有扩展全仓测试、Electron 构建或 GUI 外观验收。project-map status、UTF-8/链接与暂存差异检查另存本轮证据；原始日志空白不改写。

按决定 02 的 Herdr 交付约定，交 fork commit、a2a 证据 commit、本报告与 DONE 行；不要求门禁 submit 或 attempt/session/fence。Acceptance 保持原样，ticket 保持 open，执行主控自审后决定关闭。
