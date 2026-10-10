# Worker 任务书：T-062 ready_rev 2——修 Synara 首次使用 Activity 提示（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code）。只做 T-062（`.project-map/tickets/T-062-*.md`，依据 **ready_rev 2**；用户原话"062选B"，见 inbox `20261010T024718Z-ideation-revise-001`）。

## 背景
上一轮（worker s11-t062）已查明：浮层是 Synara 首次使用 Activity 提示（`apps/web/src/components/Sidebar.tsx:1157` 附近），全新 profile 在 Skip tour 后出现，约 8 秒自动关闭，正式工作台也会出现；提示框白底浅色字几乎看不清。上一轮只改了截图夹具。上一轮证据在 `evidence/2026-10-09-batch11/T-062/`（`red03-*`、`green03-*`、`panel-title-*.mjs`、`fixture-identity.json` 等），原样保留，不改不删。

## 要做
- 改 `Sidebar.tsx` 及其直接样式，让该提示**不再压住任务窗口**（改位置，或任务窗口打开时不弹——取最小改动，在 RESULTS 说明理由）；提示框文字修到可读（亮色、暗色主题都看一下）。不改导览其他步骤。允许改的上游文件**仅限** `Sidebar.tsx` 及其直接样式；其他上游文件需要改就停下说明。
- 先红后绿：用**全新 profile、提示出现期间**（不能再等它消失）在真实 dev UI 截图，1600×1050 与 1280×900；父修订 `d9fc40a5f` 上红（提示压住面板标题），修复后绿。判断只做"是否压住标题、文字是否可读"，外观由用户判断。
- 截图脚本沿用上一轮夹具，新文件用新名字（如 `rev2-*`），不覆盖旧文件。
- 既有相关测试、全 workspace typecheck、lint、fmt:check 通过；上游文件改动列清单。

## 独立审查（上一轮无效，这次必须有效）
- 冻结候选 = fork 提交 + 你的 a2a 证据提交。审查请求里写明：
  - 审查者**不得读** `RESULTS*.md`、ticket 的 Resolution、inbox 条目正文、旧的 `acceptance-review-*`；只读 ticket 的 What/Acceptance、diff、截图和重放命令。
  - `evidence/2026-10-09-batch11/controller-poll.log`、`dispatch.jsonl`、`panes.txt` 是主控持续追加的日志，不属于候选，变化不算候选失效。
- 审查一次。FAIL 时修复后不自行追审，交 INCOMPLETE，我审修复 diff。

## 交付
Herdr 期：fork 提交 + a2a 证据提交 + `T-062/RESULTS-02.md` + ticket Resolution 追加（保持 open，写"待主控关闭"）+ 终端一行 `T-062 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。不走门禁 submit，不需要真实模型调用。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
