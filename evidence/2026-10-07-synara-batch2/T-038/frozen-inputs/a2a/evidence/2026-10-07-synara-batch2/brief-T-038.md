# Worker 任务书：T-038 任务窗口与门禁状态界面（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-038（`.project-map/tickets/T-038-task-window-ui.md`）。界面相关请用 `frontend-less-ai-tone`、`same-visual-family` skill；视觉沿用 Synara 自身主题与组件，不另起样式。

## 要做的
1. 先核实 Synara 是否已有"一组 thread"的持久分组（项目、thread 关系、split views 等），把结论与代码位置写进证据，再决定归属保存在哪里；不改上游 thread 的表结构。
2. 界面："项目 → 任务 → agent 会话"。一个项目下多个任务；任务窗口把同一任务的多个 thread 并排或分栏显示；显示门禁状态（claimed、submitted、verified、accepted、失败原因）与人工介入标记（人工介入事件由 T-037 产生，先按其事件形状读，不存在时显示为空，不自造数据）。
3. 门禁状态只读门禁核心（T-036 已有 status/events 与 HTTP 传输）；界面对受管任务的操作只调用门禁核心。
4. 证据：在隔离数据目录中启动桌面版（或 dev 版并说明差别），用门禁 CLI 推进一个夹具任务，截图或录屏显示状态变化（含一次失败原因），附对应 CLI 输出；重启后归属保持。外观由用户判断，不宣称外观通过。
## 共同规则（T-037、T-038 并行）
- 先读：a2a 的 AGENTS.md、intent.md、CONTEXT.md、.project-map/specs/synara-m1-2026-10-07.md、你的 ticket（验收以它为准）、evidence/2026-10-07-synara-batch1/T-036/RESULTS.md，以及 fork 的 AGENTS.md、CLAUDE.md。
- 你的 checkout：worktree `~/Documents/Code/synara-t038`，分支 `a2a-t038`（从 `a9cc30c` 开出）。先经 `a2a/scripts/bun install` 安装依赖并记录耗时与内置盘占用。不要动 `~/Documents/Code/synara`（T-037 在用）。合并回 `a2a` 由主控做。
- fork 起点 `a9cc30c`。Bun/Node 只经 `a2a/scripts/bun`。只暂存、提交你自己负责的文件（`git add -- <路径>`，不用 `git add -A`），提交前 `git status` 确认没有带上对方的文件；不 rebase、不 reset、不 stash、不 checkout 别的分支。不 push。
- 文件归属：T-037 独占 `packages/a2a-gates/src/core.ts`、`packages/a2a-gates/src/cli.ts`、`apps/server/src/a2a/tools.ts` 及其新增的编排文件。T-038 独占 `apps/web/src/a2a/**` 与它新建的归属文件（例如 `packages/a2a-gates/src/membership.ts`、`apps/server/src/a2a/membership*.ts`）。两边都需要改的共用接入文件（服务注册、路由挂载、`packages/contracts/src/a2aGates.ts` 等）：先停下告诉主控，由主控指定写入者。
- a2a 仓库：只写你的 ticket 与你的证据目录 `evidence/2026-10-07-synara-batch2/T-0xx/`；不改 MAP.md、AGENTS.md、README.md、CONTEXT.md、acceptance 下的现有文件。
- 运行 Synara 只用隔离数据目录与身份，不读写用户可能已安装的 Synara 数据，不碰用户正在用的 Herdr。测试中启动的后台服务必须脱离调用者进程组。只停你启动的进程，只删你创建的文件。
- 本 ticket 不做真实模型调用；需要时先停下问主控。遇到权限请求或需要用户决定的事，停下说明。
- 先红后绿；不从实现输出取预期；失败与异常原样保留。冻结候选后做一次 fresh-context 只读独立审查，明确冻结清单（排除主控持续写的 controller-poll.log、launch-argv.txt、panes.txt）。
- ticket 保持 open，结论写"待主控关闭"。a2a 本地 commit 只含你的文件。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。
