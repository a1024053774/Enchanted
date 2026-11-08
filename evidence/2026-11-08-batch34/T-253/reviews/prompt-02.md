你是 a2a（Enchanted）仓库的独立审查员，只读：不改任何文件、不提交、不运行会写仓库的命令。用中文写结论。这是 T-253 的复审 02，也是最后一轮。

固定候选：`8fad54c0d`（分支 `claude/dreamy-ptolemy-d0f2f0`，工作目录就是这个提交，审查期间作者不会提交）。一律按这个 SHA 判断（`git diff dbde5eeb4 8fad54c0d`、`git show 8fad54c0d:<路径>`），不按 HEAD；发现这个 SHA 以外的东西变了，写 INCOMPLETE。代码改动只在 `b01096b84`，`8fad54c0d` 只改证据目录 `evidence/2026-11-08-batch34/T-253/`。

背景：审查 01（`evidence/2026-11-08-batch34/T-253/reviews/review-01.md`，候选 `dbde5eeb4`）判 FAIL：
- P2：还在进行的原生会话绑定没有纳入停止流程；关库后拒绝记录再抛错，成为未处理的 Promise 拒绝；`readThread` 返回后不再查停止。
- P3：RESULTS 把“重启后靠 observeRun 补绑”说宽了。

本轮只审这两项的修复，以及修复本身有没有引入新问题。需求见 `.project-map/tickets/T-253-codex-dispatch-reclaim-identity-unbound.md`，审查约定见 `REVIEW.md`，项目规则见 `AGENTS.md`。

修复要点（`b01096b84`）：
1. `workbench/src/gates/core.ts` 的 `nativeSessionLearned`：停止检查从循环开头移到 `readThread` 之后、拿锁之前。
2. `workbench/src/daemon.ts`：用一个 Set 登记每次绑定的 Promise，完成后移除；拒绝记录外加 try/catch，写失败时照 `panes.recordFailure` 报 `event_write_failed` 并调 `panes.onEventWriteFailed`；`shutdown()` 在两个服务关闭之后、`gates.close(); store.close()` 之前 `await Promise.all([...bindings])`。
3. README 一段说明。
4. 测试：
   - `workbench/tests/t253_native_bind.ts` 加“读窗格期间停止”“等锁期间停止”两个检查；
   - 新增后台层测试 `workbench/tests/t253_shutdown_host.ts` 与 `test_t253_shutdown.py`，用真实 `serve()` 加夹具窗格；
   - 新变异 `stop-not-rechecked`、`shutdown-skips-bindings`、`bind-record-unguarded`。

结果与说明见 `evidence/2026-11-08-batch34/T-253/RESULTS.md`：
- 顶层是按 `b01096b84` 跑的结果；
- `red/*-cd69040d1.json` 是 P2 在修复前的复现；
- `r2/` 是审查 01 审过的那一轮。

请重点找这些问题。每条给出文件:行号、具体输入或时序、会出什么错；拿不准的写“未证实”，不要当成缺陷：
- 停止流程会不会因为等绑定而挂住或变慢：绑定在等锁、窗格读取卡住、窗格已被 `panes.shutdown()` 终止后再读、`readThread` 抛非 Refusal 错误时，各会怎样。等待放在服务关闭之后，有没有绑定会在 `await Promise.all` 开始之后才登记，从而漏等。
- `daemon.ts` 的 `.finally` 与 Set 的写法：Promise 会不会拒绝、会不会漏删或重复删；`.catch` 体里还有没有能抛出的地方。
- `event_write_failed` 的接收者：调用 `panes.onEventWriteFailed` 把用户输入记录标为失败，是否与项目已有约定一致，是否过重或过轻。
- 停止检查移到读之后：一个在停止开始后才开始的绑定会先读一次窗格，有没有副作用；与 `observeRun` 等其他读窗格的地方是否一致。
- 测试能否区分对错：
  - 后台层测试的夹具窗格、脚本化读取和“最多等 2 秒”的设计，能否真的区分修前与修后；
  - 修后绿态里 `stop_while_binding` 的记录落在 `daemon_stopped` 之后，这是否可以接受；
  - 每条修复是否都有变异覆盖；
  - 期望值是否来自需求和审查 01，而不是实现输出。
- RESULTS 有没有夸大或漏写，尤其是 P3 的新写法、`test_startup_shutdown_e2e.py` 判为与本票无关的理由、T-127 第一次运行失败的解释。
- 有没有违反 AGENTS.md / REVIEW.md：门禁唯一入口、操作锁语义、不加无证据的 fallback 或重试。

结尾给结论：可合并 / 需修复（列出必须修的）/ 无法判断（缺什么）。
