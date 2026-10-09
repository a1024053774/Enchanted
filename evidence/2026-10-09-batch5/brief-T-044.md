# Worker 任务书：T-044 任务窗口由 agent 驱动（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-044（`.project-map/tickets/T-044-agent-driven-task-window.md`，验收以它为准，含用户已确认的设计）。

## 先读
a2a：`AGENTS.md`、`CONTEXT.md`、`intent.md`、T-044；T-037 RESULTS（run 编排、dispatch、人工介入）、T-038 RESULTS 与 `grouping-comparison.md`（membership 设计）、T-043 RESULTS（任务窗口现状）。fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。

## 范围
- fork `~/Documents/Code/synara`，分支 `a2a`（当前 `28e2f1b`）。主要改动在 `packages/a2a-gates`、`packages/contracts/src/a2aGates.ts` 与 `a2aMembership.ts`、`apps/server/src/a2a/`、`apps/web/src/a2a/`。状态变更仍只在门禁核心；membership 写入由核心在同一操作内完成或经同一锁保护，不另开一条写入路径。改其他上游文件先停下问主控。不 push。
- 另一个 worker 在单独 worktree `~/Documents/Code/synara-t045` 做 T-045，不要动它。
- **用户的正式工作台正在用这个 checkout 的构建产物运行**（`./a2a/scripts/workbench status`）。不要在此 checkout 运行 `build:desktop` 或任何会改写 `apps/*/dist` 的命令，不要停止或重启正式工作台，不要读写 `~/Library/Application Support/a2a-workbench`。界面验证用隔离 dev 实例（T-043 的 `bun run dev` 方式、外置盘数据目录、provider 关闭）。严禁移动、替换或链接构建输出与依赖目录。
- 界面截图：可用 fork 现有的 Playwright，或在 Codex CLI 中使用 Computer Use（只操作你自己启动的隔离窗口；权限请求由主控代批，遇到系统设置、登录、密码、付款界面停下）。
- 不做真实模型调用。

## 要做的
1. `create` 自动建立任务窗口条目；`dispatch` 自动把 worker 会话归入任务（角色 worker）。
2. 新增 `attach` 命令：参数含 task、role、模型/参数、指令；创建普通 Synara 会话并归入任务；记一条事件；该会话不得经 `a2a_submit` 或其他门禁命令推进业务状态。
3. 回收后会话在 membership 中标为已结束，界面淡化显示；历史保留。
4. 先红后绿：用真实 CLI/HTTP 入口取得缺失实现的红态；反例：attach 会话调用 a2a_submit 被拒、业务状态不变。35 项与 membership 场景重跑。
5. 任务窗口截图：全程只用门禁命令（不手动操作 membership），出现任务、worker、reviewer，以及回收后的淡化状态。

## 交付
证据 `evidence/2026-10-09-batch5/T-044/`，中文 `RESULTS.md`；fork 在 `a2a` 分支提交；a2a 只提交你的证据与 T-044 Resolution（保持 open）。fresh-context 独立审查一次。最后终端回复一行：`T-044 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。需要决定的事停下说明。
