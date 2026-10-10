# Worker 任务书：T-064 工作台设置里调各角色的权限（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code）。只做 T-064（`.project-map/tickets/T-064-*.md`，依据 **ready_rev 1**；用户原话见 ticket 与 inbox `20261010T032521Z-ideation-assign-001`）。

## 范围提醒（用户逐字）
"我要的是synara软件层面的，不是让你在Claude code和codex里改权限ok？"——只改 Synara 工作台自己的设置、凭据签发与权限决策；**不读写** `~/.claude`、`~/.codex` 或任何 Claude Code / Codex 的权限配置，也不应用 T-054 的权限建议文件。

## 起点
- T-058 的预设与凭据冻结：`evidence/2026-10-09-batch11/T-058/`（`controller-decision-01.md` 批准了 Services/Layers `AgentGatewaySessionRegistry.ts` 挂载），fork 里 `packages/a2a-gates`、`apps/server/src/a2a`。T-055 的 `a2a_raise` 免确认口径：`evidence/2026-10-09-batch8/T-055/RESULTS-03.md`（`computerToolPermission.ts` 的网关目录项）。
- 从 fork `a2a` 分支当前 HEAD 开始，开工时在 RESULTS 记下基线提交。

## 上游接入
- 逻辑放 a2a 模块（`packages/a2a-gates`、`packages/contracts`、`apps/server/src/a2a`、`apps/web/src/a2a`）。
- 预计需要的上游接入：设置页挂一个"角色权限"分区（Synara 设置路由/导航的挂载点）；免确认需要在 `apps/server/src/agentGateway/computerToolPermission.ts` 的网关工具判断处读取用户选择。**开始改这些文件前先停下**，列出文件、行号和最小改动，等我批准。T-058 说过不碰 `computerToolPermission.ts`，那是 T-058 的范围；本票的免确认入口由用户要求，我会逐项审批。
- 不得给 `dismiss` 或"主控关闭 blocking"提供开关；它们留在核心强制。

## 要做
按 ticket Acceptance 逐条做：先红；五个角色预设逐项对照 spec 第 1 节手写的预期；改动后新签发凭据按新集合冻结、旧凭据不变（真实 MCP `tools/list` 与调用，正反例各一）；免确认正反例与 T-055 同口径；每次修改与恢复默认记一条用户输入（形态 `action`，渠道设置页）和可读的变更记录；无自定义时与 T-058 行为一致（反例）。失败方式清单逐条写处理方式。截图作证，外观由用户判断。不需要真实模型调用时就不用；需要时遵守隔离 CODEX_HOME 规则。

## 独立审查
- 冻结候选 = fork 提交 + 你的 a2a 证据提交。审查请求写明：审查者**不得读** `RESULTS*.md`、ticket 的 Resolution、inbox 条目正文、旧审查；只读 ticket 的 What/Acceptance/说明、spec 第 1 节、diff、截图、原始机械输出和重放命令。`evidence/2026-10-09-batch11/controller-poll.log`、`dispatch.jsonl`、`panes.txt` 是主控持续追加的日志，不属于候选。
- 审查一次。FAIL 时修复后不自行追审，交 INCOMPLETE，我审修复 diff。

## 交付
Herdr 期：fork 提交 + a2a 证据提交 + `T-064/RESULTS.md` + ticket Resolution（保持 open，写"待主控关闭"）+ 终端一行 `T-064 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。不走门禁 submit。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
