# Worker 任务书：T-063 重开已有 profile 停在启动 logo、会话空态文字与 logo 重叠（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code）。只做 T-063（`.project-map/tickets/T-063-*.md`，依据 **ready_rev 1**；用户原话"两条范围外的界面问题都做"，见 inbox `20261010T024718Z-ideation-assign-001`）。

## 背景
两条问题都由 T-062 上一轮 worker 发现：
1. 重开：`evidence/2026-10-09-batch11/T-062/resume01.json`、`resume01-5.png`、`issue-reopen.md`。隔离 dev UI 用已有 profile 重开后约 11 秒只有启动 logo、无报错。
2. 空态重叠：`green03-initial.png`、`green03-narrow.png`、`issue-narrow.md`。
T-062 的夹具（`panel-title-*.mjs`、`fixture-identity.json`、`start-isolated.py` 等，见 `evidence/2026-10-09-batch11/T-062/` 与 `T-057/`）可起隔离 dev UI 并截图，沿用即可；不改不删它们，新文件放 `T-063/`。

## 要做
- 问题 1：先查明是产品缺陷还是隔离 dev 环境才有（例如 dev server/HMR、夹具重开方式、profile 锁）。是产品缺陷就先红后绿：同一 profile 重开后在合理时限内出现主界面；是环境问题就写依据，并让重开路径在验收环境里能走通。不得把"诊断命令退出 0"当作重开通过。
- 问题 2：先红后绿的界面用例，1600×1050 与 1280×900 下文字与 logo 不重叠，截图作证；外观由用户判断，你只判断是否重叠。
- ticket"说明"里的失败方式清单逐条在 RESULTS 写处理方式。
- 修复点在 `apps/web/src/a2a` 之外时：只改问题直接所在的组件及其直接样式，并列入上游文件改动清单；需要改启动流程、服务端、Electron 主进程或多个无关组件时，先停下说明位置与最小改动，等我批准。
- T-062 的 worker 可能刚改过 `Sidebar.tsx`；从 fork `a2a` 分支当前 HEAD 开始，开工时在 RESULTS 记下基线提交。
- 既有相关测试、全 workspace typecheck、lint、fmt:check 通过。

## 独立审查
- 冻结候选 = fork 提交 + 你的 a2a 证据提交。审查请求里写明：审查者**不得读** `RESULTS*.md`、ticket 的 Resolution、inbox 条目正文；只读 ticket 的 What/Acceptance/说明、diff、截图和重放命令。`evidence/2026-10-09-batch11/controller-poll.log`、`dispatch.jsonl`、`panes.txt` 是主控持续追加的日志，不属于候选。
- 审查一次。FAIL 时修复后不自行追审，交 INCOMPLETE，我审修复 diff。

## 交付
Herdr 期：fork 提交（如有）+ a2a 证据提交 + `T-063/RESULTS.md` + ticket Resolution（保持 open，写"待主控关闭"）+ 终端一行 `T-063 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。不走门禁 submit，不需要真实模型调用。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
