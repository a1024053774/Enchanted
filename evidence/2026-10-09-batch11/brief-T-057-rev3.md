# Worker 任务书：T-057 ready_rev 3 恢复——通知两路、启动提醒、MCP 逐个处置（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code）。只做 T-057（`.project-map/tickets/T-057-issue-panel-completion.md`，依据 **ready_rev 3**；用户原话见 inbox `20261010T032521Z-ideation-revise-001`）。

## 起点
- 上一轮冻结候选 fork `7831241`（已在 `a2a` 分支历史里），报告 `evidence/2026-10-09-batch11/T-057/RESULTS-02.md`，独立审查 `acceptance-review-01.md`（INCOMPLETE，四项限制），主控转交 `executor-forward-02.md`。之后 `a2a` 分支又合入 T-061、T-056、T-058、T-062、T-063 的改动；从 `a2a` 当前 HEAD 开始，开工时在 RESULTS 记下基线提交。上一轮证据原样保留，不改不删，新文件用 `*-rev3-*` 或 `-03` 后缀。
- 已批准的上游接入沿用 `T-057/controller-decision-01.md`（Sidebar 徽标挂载、`__root.tsx` 挂提醒组件、AgentGateway 注册处置工具；不改 `computerToolPermission.ts`）。

## 本轮要做（对应 ticket 未完成项）
1. **通知两路**：问题上报的一般变化（新上报、关闭、送达等）只发软件内通知；需要用户做决定或回复的——blocking、新的"等你决定"、主控停下等用户答复——另发系统通知（应用不在前台时，同一批合并，不发声音），设置里可关。路由按条目种类与状态字段，不判断正文含义。系统通知沿用 `window.desktopBridge.notifications.show`；"设置里可关"优先复用现有通知开关并在 RESULTS 说明；若你判断必须新增设置字段或改其他上游文件，先停下说明位置与最小改动。"主控停下等用户答复"在服务端有哪种可路由的字段，若现有数据里没有，停下说明，不要自造内容判断。
2. **启动提醒**：修 `IssueNotifications.tsx`（约第 15 行）把首次读取记为已观察的行为：打开应用时已有待决定的 blocking 或"等你决定"问题，提醒一次（走系统通知那一路）；同一批只提醒一次，重启不重复提醒已提醒过的。先红后绿，注入时钟/前后台状态。
3. **七个处置动作逐个经 MCP 入口**（close、needs-user、forward、reopen、snooze、dismiss、delivered）：每个动作经真实 MCP 工具调用一次，核对追加记录与派生状态；`dismiss` 由非用户角色经 MCP 调用时应被拒，blocking 被主控 close 时应被拒。不需要真实模型调用时就别用模型。
4. **面板按钮不被截断**这一项若上一轮未有截图证据，补 1600×1050 与 1280×900 截图。
5. "未确认列表可见"已由 T-058 补证、用户同意并入：在 RESULTS 引用 T-058 证据（`evidence/2026-10-09-batch11/T-058/`），不必重做。
6. **真实 macOS 系统通知**：用户还没选验证方式，本轮**不做**，不启动任何 Electron 去弹真实通知。因此本轮最好结果是 INCOMPLETE（该项待用户），不得写 PASS。

## 独立审查
- 冻结候选 = fork 提交 + 你的 a2a 证据提交。审查请求写明：审查者**不得读** `RESULTS*.md`、ticket 的 Resolution、inbox 条目正文、旧 `acceptance-review-*`；只读 ticket 的 What/Acceptance/说明、diff、截图、原始机械输出和重放命令。`evidence/2026-10-09-batch11/controller-poll.log`、`dispatch.jsonl`、`panes.txt` 是主控持续追加的日志，不属于候选。
- 审查一次。FAIL 时修复后不自行追审，交 INCOMPLETE，我审修复 diff。

## 交付
Herdr 期：fork 提交 + a2a 证据提交 + `T-057/RESULTS-03.md` + ticket Resolution 追加（保持 open，写"待主控关闭"）+ 终端一行 `T-057 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。不走门禁 submit。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
