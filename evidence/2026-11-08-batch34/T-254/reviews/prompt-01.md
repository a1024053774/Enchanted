你是 a2a（Enchanted）仓库的独立审查员，只读：不改任何文件、不提交、不运行会写仓库的命令。用中文写结论。这是 T-254 的审查 01。

固定候选：`653456fe3`（本地 main）。一律按这个 SHA 判断（`git show 653456fe3`、`git show 653456fe3:<路径>`、`git diff 1bb19fa21 653456fe3`），不按工作区：工作区里有作者正在跑的测试写出的未跟踪证据文件，还有与本票无关的用户改动（几个 controller-poll.log、`records/launches.jsonl`），都不是候选的一部分。审查期间作者不会提交；发现 `653456fe3` 本身变了，写 INCOMPLETE。

需求：`.project-map/tickets/T-254-shutdown-binding-wait-bound.md`（在候选里）。来由是 T-253 的修复让后台停止时等还在进行的原生会话绑定收尾，但这一步没有上限；用户要求“这个应该设置一个合理的上限”。审查约定见 `REVIEW.md`，项目规则见 `AGENTS.md`。T-253 的背景见 `.project-map/tickets/T-253-codex-dispatch-reclaim-identity-unbound.md` 与 `evidence/2026-11-08-batch34/T-253/RESULTS.md`。

改动（`653456fe3`）：
1. `workbench/src/daemon.ts`：
   - 新常量 `BINDING_STOP_WAIT_MS = 10_000`；
   - 每次绑定登记为一个对象（launch 记录、会话号、`abandoned` 标记、Promise）；
   - `shutdown()` 里原来的 `await Promise.all([...bindings])` 改成和一个 10 秒计时器赛跑，按时收尾就清计时器；到期时把仍在进行的绑定标为放弃，并在关库前逐个记 `native_session_bind_abandoned`（会话号、实际等了多少毫秒）；
   - 绑定的 `.catch` 在已放弃时直接返回，不再写库。
2. 测试：`workbench/tests/t253_shutdown_host.ts` 加场景 `binding_outlives_stop`（停止开始后窗格读取 30 秒才返回）；`workbench/tests/test_t253_shutdown.py` 加这一场景的检查、三个场景共用的 `pid_removed`、`stop_while_binding` 的“关库后 3 秒内退出”，以及 4 个变异（`stop-wait-unbounded`、`abandon-unmarked`、`abandon-unrecorded`、`timer-kept`）。

作者已有的结果（未跟踪文件，可以读，不是候选的一部分）：
- 修前红态 `evidence/2026-11-08-batch34/T-254/red/shutdown-1bb19fa21.json`：`binding_outlives_stop` 在 30 秒时才关库，没有放弃记录；另两个场景通过。
- 修后（工作区源码，与 `653456fe3` 相同）`green/shutdown-worktree.json`：10 秒时关库，一条 `native_session_bind_abandoned`（`waited_ms` 10001），读取在关库后返回，没有再写，后台以 0 退出。
- 按 `653456fe3` 的绿态、变异与回归还在跑，结果会出现在 `green/`、`mutants/`、`regression/`；跑完前看不到的，不要推测。

请重点找这些问题。每条给出文件:行号、具体输入或时序、会出什么错；拿不准的写“未证实”，不要当成缺陷：
- 上限本身：10 秒的理由（停止开始后，绑定在它手上这一次窗格读取返回后就结束；读取里的进程查询有 5 秒 exec 超时）是否成立。读 `workbench/src/panes.ts` 的 `readThread`、`processInfo` 与 `workbench/src/gates/core.ts` 的 `nativeSessionLearned` 核对：停止开始后，一次绑定还会不会做第二次窗格读取或等锁，从而超过这个估计；有没有别的地方会让读取超过 5 秒。
- 赛跑与计时器：`Promise.race` 的两边会不会拒绝；计时器在两种结局下是否都清掉；`bindings` 在等待开始后还能不能新增成员；到期后遍历 `bindings` 与 `.finally` 删除之间有没有竞态，会不会漏记或多记。
- 放弃之后：被放弃的绑定之后收尾时，`.catch` 直接返回，`.finally` 照常删除；它要是成功（没被拒）会怎样，能不能在库关闭后写 `runtime_bound`；`gates.close()` 之后它再调门禁的哪些东西会抛错。
- `store.event("native_session_bind_abandoned", ...)` 本身写失败时会怎样（这时 `shutdown()` 抛错，后台以 1 退出、库没关）：是否可以接受，与 T-253 的 `event_write_failed` 约定是否一致。
- 不做的项：票据把停止流程里其他没有期限的等待（请求排空、恢复、`resumedRunsSettled`、窗格终止）列为不做。只核对这个范围划分有没有让本票的结论失真，不要求本票去改它们；发现其中有会让 `binding_outlives_stop` 这类场景照样挂住的，写出来。
- 测试能否区分对错：新场景能否区分修前与修后；每个变异是否被至少一个检查判红（看 `mutants/` 结果，跑完前不推测）；期望值是否来自票据与用户要求，而不是实现输出；30 秒读取和 15 秒、3 秒这些阈值是否合理、会不会抖动误判。
- 有没有违反 AGENTS.md / REVIEW.md：门禁唯一入口、操作锁语义、不加无证据的 fallback 或重试。

结尾给结论：可合并 / 需修复（列出必须修的）/ 无法判断（缺什么）。
