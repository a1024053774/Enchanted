你是 a2a（Enchanted）仓库的独立审查员，只读：不改任何文件、不提交、不运行会写仓库的命令。用中文写结论。

固定候选：`dbde5eeb444faa95e173ba06b3ee33b56d57e75f`（分支 `claude/dreamy-ptolemy-d0f2f0`，工作目录就是这个提交，审查期间作者不会提交）。一律按这个 SHA 判断（`git diff faf1b0d7a dbde5eeb4`、`git show dbde5eeb4:<路径>`），不按 HEAD；发现这个 SHA 以外的东西变了，写 INCOMPLETE。产品源码与测试在 `cd69040d1`，`dbde5eeb4` 只加证据目录 `evidence/2026-11-08-batch34/T-253/`。

需求：`.project-map/tickets/T-253-codex-dispatch-reclaim-identity-unbound.md`。经 `dispatch` 派出的 Codex worker 没有一次被受理的交付时，回收被拒 `identity_conflict`，因为 attempt 的 `native_session` 没绑定。用户选方案 B：后台在得知 Codex 原生会话号时就把它绑定到 attempt。审查约定见 `REVIEW.md`，项目规则见 `AGENTS.md`；前因见 T-252 票与 `evidence/2026-11-07-batch33/T-252/RESULTS.md`。

改动要点：
1. `workbench/src/panes.ts` 的 `scan()`：worker 窗格第一次从根 rollout 的 `session_meta` 得知会话号时，调 `nativeSessionLearned` 回调。
2. `workbench/src/daemon.ts`：把回调接到 `gates.nativeSessionLearned(task, attempt, thread)`；被拒时记 `native_session_bind_failed`。
3. `workbench/src/gates/core.ts`：新方法 `nativeSessionLearned`。先在锁外 `readThread`，再拿任务操作锁（`operation_busy` 时等 100ms 重来），锁内 `current` 加 `bindObservedIdentity`，写 `runtime_bound`（带 `by: "native_session_learned"`）。
4. README 一段说明。
5. 测试：`workbench/tests/t253_native_bind.ts` 与 `test_t253_native_bind.py`（门禁单元测试，含反例与 3 个变异）；`test_t252_untrusted_turn_other_cli_e2e.py` 加了变异 `t253-no-bind` 和回收前的绑定事件记录。结果与说明见 `evidence/2026-11-08-batch34/T-253/RESULTS.md`。

请重点找这些问题。每条给出文件:行号、具体输入或时序、会出什么错；拿不准的写“未证实”，不要当成缺陷：
- 绑定会不会写进不属于这个 attempt 的身份：别的 launch、别的 shell 进程、领导进程变了、attempt 已换掉、revise 后的新 attempt、reviewer 窗格、恢复后的窗格。
- 锁：会不会持锁跨 await；会不会和 `observeRun`、`dispatch`、`submit`、`reclaim` 撞锁，导致它们失败、死锁或重复写；等锁循环在什么情况下不会结束，后台停止时会怎样。
- 时序：会话号在 `dispatch` 存下 attempt 之前就被得知时（startThread、readThread 的 await 期间），会不会丢绑定或报错；`scan()` 的其他调用点（signal、onData、onExit 的 final 读、caller）会不会让回调重复触发或在不该触发时触发。
- `daemon.ts` 的 `.catch`：会不会吞掉本该让人看到的错误；`store.event` 本身失败时会怎样。
- 回收语义：T-170 的 `neverStarted` 例外，以及“原生会话为空但 CLI 还在跑时仍拒”，是否保持不变。
- 测试能否区分对错：期望值是否来自需求；单元测试直接写入的任务记录是否像真实派发后的样子；变异是否覆盖每条修复；端到端的 `identity_binding` 记录能否说明绑定是 B 做的；RESULTS 有没有夸大或漏写（例如后台重启后的窗格、"没交付就结束回合"没单独跑）。
- 有没有违反 AGENTS.md / REVIEW.md：门禁唯一入口、操作锁语义、不加无证据的 fallback 或重试。

结尾给结论：可合并 / 需修复（列出必须修的）/ 无法判断（缺什么）。
