# Worker 任务书：T-065 短窗口加问题面板时输入框要在首屏可见（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code）。只做 T-065（`.project-map/tickets/T-065-*.md`，依据 **ready_rev 1**；用户原话"不能"，见 inbox `20261010T035708Z-ideation-assign-001`）。

## 背景
T-063 在 fork `e94a0efc3` 改了 `apps/web/src/components/ChatView.tsx` 空态块：横幅、logo、标题、输入区按正常流排布，放不下时整体滚动。副作用是 1280×900 开着问题面板时输入框掉到首屏下。T-063 的夹具、反例和截图在 `evidence/2026-10-09-batch11/T-063/`（`REPLAY.md`、`*-command.json`、`browser-pinned.config.mts`、固定 Playwright 浏览器在外置盘），沿用即可；不改不删它们，新文件放 `T-065/`。

## 要做
- 先红：在 `e94a0efc3` 上，1280×900、问题面板开着且至少 3 条待决定问题时，输入框不在首屏内，用例失败。
- 修：空间不够时先收起或缩小次要内容（导入横幅、logo、标题），输入框始终完整在首屏内、可直接点击输入。按设计收起的内容在 RESULTS 写清哪种视口收起什么；不能靠藏文字通过重叠检查。
- 绿：1600×1050、1280×900、1280×720 三种视口，开或不开问题面板，输入框完整在首屏内；T-063 的反例（两两相交面积 0、加长中文文案、尺寸来回改变）照常通过。
- ticket"说明"里的失败方式逐条写处理方式（面板宽度改变、问题很多时面板自身滚动、中英文案长度、浏览器缩放 125%）。
- 上游文件预计只改 `ChatView.tsx` 空态块；需要改别的上游文件先停下说明。不做启动耗时对照（用户："没必要测"）。
- 从 fork `a2a` 分支当前 HEAD 开始，开工时在 RESULTS 记下基线提交；T-057 可能刚合入改动。
- 相关既有测试、全 workspace typecheck、lint、fmt:check 通过。

## 独立审查
- 冻结候选 = fork 提交 + 你的 a2a 证据提交。审查请求写明：审查者**不得读** `RESULTS*.md`、ticket 的 Resolution、inbox 条目正文；只读 ticket 的 What/Acceptance/说明、diff、截图、原始机械输出和重放命令。`evidence/2026-10-09-batch11/controller-poll.log`、`dispatch.jsonl`、`panes.txt` 是主控持续追加的日志，不属于候选。
- 审查一次。FAIL 时修复后不自行追审，交 INCOMPLETE，我审修复 diff。

## 交付
Herdr 期：fork 提交 + a2a 证据提交 + `T-065/RESULTS.md` + ticket Resolution（保持 open，写"待主控关闭"）+ 终端一行 `T-065 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。不走门禁 submit，不需要真实模型调用。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
