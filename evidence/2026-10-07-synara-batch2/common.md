## 共同规则（T-037、T-038 并行）
- 先读：a2a 的 AGENTS.md、intent.md、CONTEXT.md、.project-map/specs/synara-m1-2026-10-07.md、你的 ticket（验收以它为准）、evidence/2026-10-07-synara-batch1/T-036/RESULTS.md，以及 fork 的 AGENTS.md、CLAUDE.md。
- fork `~/Documents/Code/synara`，分支 `a2a`（当前 `a9cc30c`）。Bun/Node 只经 `a2a/scripts/bun`。两个 worker 同时在这个 checkout 工作：只暂存、提交你自己负责的文件（`git add -- <路径>`，不用 `git add -A`），提交前 `git status` 确认没有带上对方的文件；不 rebase、不 reset、不 stash、不 checkout 别的分支。不 push。
- 文件归属：T-037 独占 `packages/a2a-gates/src/core.ts`、`packages/a2a-gates/src/cli.ts`、`apps/server/src/a2a/tools.ts` 及其新增的编排文件。T-038 独占 `apps/web/src/a2a/**` 与它新建的归属文件（例如 `packages/a2a-gates/src/membership.ts`、`apps/server/src/a2a/membership*.ts`）。两边都需要改的共用接入文件（服务注册、路由挂载、`packages/contracts/src/a2aGates.ts` 等）：先停下告诉主控，由主控指定写入者。
- a2a 仓库：只写你的 ticket 与你的证据目录 `evidence/2026-10-07-synara-batch2/T-0xx/`；不改 MAP.md、AGENTS.md、README.md、CONTEXT.md、acceptance 下的现有文件。
- 运行 Synara 只用隔离数据目录与身份，不读写用户可能已安装的 Synara 数据，不碰用户正在用的 Herdr。测试中启动的后台服务必须脱离调用者进程组。只停你启动的进程，只删你创建的文件。
- 本 ticket 不做真实模型调用；需要时先停下问主控。遇到权限请求或需要用户决定的事，停下说明。
- 先红后绿；不从实现输出取预期；失败与异常原样保留。冻结候选后做一次 fresh-context 只读独立审查，明确冻结清单（排除主控持续写的 controller-poll.log、launch-argv.txt、panes.txt）。
- ticket 保持 open，结论写"待主控关闭"。a2a 本地 commit 只含你的文件。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。
