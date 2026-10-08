# Worker 任务书：T-037 原生 run 编排与人工介入记录（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-037（`.project-map/tickets/T-037-native-run-orchestration.md`）。另读冻结规格 `.project-map/specs/supervised-run-2026-10-06.md`（契约原文）、`acceptance/test_run_e2e.py`（18 项，只读）、`coop.py` 的 run 部分（参考实现，只读）。

## 要做的
1. run 编排进门禁核心：dispatch 经 Synara 内部服务创建 worker thread（worktree 环境、baseRef 为集成头、明确模型与参数，任务说明写入 attempt 身份与交付方式）；只有当前 attempt 的 `a2a_submit` 推进；verify/integrate/reclaim 绑定原 attempt；回收停止并归档本 run 创建的 thread；运行时身份核对 thread、turn、worktree。所有状态变更仍只在核心中。
2. 人工介入：受管 worker thread 中由人直接输入的消息，记为绑定 task/attempt/thread 的事件；先核实 Synara 区分用户输入与 agent/工具输入的位置，接入点尽量少。
3. 18 项：把 `test_run_e2e.py` 中 Herdr 边界替身改成新运行时的替身（例如受控的 thread 服务替身），放在你的证据目录副本里；业务断言与预期不变，差异逐条记录。先在缺失实现时取得红态。
4. 反例：保存"空闲/done 而无 submit 即接受"、"忽略 expected attempt"两个 mutant 在同一套验收下的业务红态。
5. 交付 8 项、恢复 9 项在新候选上经 T-036 的同一入口重跑。
## 共同规则（T-037、T-038 并行）
- 先读：a2a 的 AGENTS.md、intent.md、CONTEXT.md、.project-map/specs/synara-m1-2026-10-07.md、你的 ticket（验收以它为准）、evidence/2026-10-07-synara-batch1/T-036/RESULTS.md，以及 fork 的 AGENTS.md、CLAUDE.md。
- 你的 checkout：`~/Documents/Code/synara`，分支 `a2a`。T-038 在单独的 worktree `~/Documents/Code/synara-t038`（分支 `a2a-t038`）并行工作，不要动它。
- fork 起点 `a9cc30c`。Bun/Node 只经 `a2a/scripts/bun`。只暂存、提交你自己负责的文件（`git add -- <路径>`，不用 `git add -A`），提交前 `git status` 确认没有带上对方的文件；不 rebase、不 reset、不 stash、不 checkout 别的分支。不 push。
- 文件归属：T-037 独占 `packages/a2a-gates/src/core.ts`、`packages/a2a-gates/src/cli.ts`、`apps/server/src/a2a/tools.ts` 及其新增的编排文件。T-038 独占 `apps/web/src/a2a/**` 与它新建的归属文件（例如 `packages/a2a-gates/src/membership.ts`、`apps/server/src/a2a/membership*.ts`）。两边都需要改的共用接入文件（服务注册、路由挂载、`packages/contracts/src/a2aGates.ts` 等）：先停下告诉主控，由主控指定写入者。
- a2a 仓库：只写你的 ticket 与你的证据目录 `evidence/2026-10-07-synara-batch2/T-0xx/`；不改 MAP.md、AGENTS.md、README.md、CONTEXT.md、acceptance 下的现有文件。
- 运行 Synara 只用隔离数据目录与身份，不读写用户可能已安装的 Synara 数据，不碰用户正在用的 Herdr。测试中启动的后台服务必须脱离调用者进程组。只停你启动的进程，只删你创建的文件。
- 本 ticket 不做真实模型调用；需要时先停下问主控。遇到权限请求或需要用户决定的事，停下说明。
- 先红后绿；不从实现输出取预期；失败与异常原样保留。冻结候选后做一次 fresh-context 只读独立审查，明确冻结清单（排除主控持续写的 controller-poll.log、launch-argv.txt、panes.txt）。
- ticket 保持 open，结论写"待主控关闭"。a2a 本地 commit 只含你的文件。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。
