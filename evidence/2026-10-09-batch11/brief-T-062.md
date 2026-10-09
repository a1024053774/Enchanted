# Worker 任务书：T-062 修复任务窗口里盖住问题上报面板标题的浮层（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code，Herdr pane wF:pM）。只做 T-062（`.project-map/tickets/T-062-*.md`，依据 ready_rev 1；用户原话"浮层这个要修复"）。
- 先看 `evidence/2026-10-09-batch8/T-055/round4/panel-final-before-send.png`、`panel-final-after-send.png`，以及 T-055/T-057 的面板脚本（`evidence/2026-10-09-batch8/T-055/panel-send.mjs`、`evidence/2026-10-09-batch11/T-057/panel-complete.mjs`、`panel-slice.mjs`、`web-fixture.ts`、`start-isolated.py`）——它们已能起隔离 dev UI 并截图；T-055 报告提到过"延迟导览"和"Skip tour"，可能相关。
- fork `~/Documents/Code/synara`，分支 `a2a`（当前 `d9fc40a5f`）。先查明浮层来源（产品缺陷还是隔离 dev 环境才有）。若是产品缺陷：修复点若在 `apps/web/src/a2a` 之外（例如导览组件或任务窗口布局），先停下说明位置与最小改动，主控批准后再改。若是环境原因：说明依据，并让验收截图不再带它（只改夹具，不改产品）。
- 截图证据由用户判断外观；你只判断"浮层是否仍遮挡标题"。
- Herdr 期交付：fork 提交（如有）+ a2a 证据提交 + RESULTS + 终端 DONE 行，不走门禁 submit。不需要真实模型调用。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、你的 ticket、fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket，不来自实现输出；失败原样保留；只跑相关测试。
- 证据 `evidence/2026-10-09-batch11/T-062/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次，FAIL 时修复后不自行追审，交付 INCOMPLETE。最后终端回复一行：`T-062 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
