# T-199 独立审查第 2 轮（只读）

你是新的独立审查员。只读审查，不改仓库文件，不操作 /private/tmp/t190 下的后台或应用，不碰 ~/Library/Application Support/a2a-orchestrator。报告只写到 `/private/tmp/t199-review2/REPORT.md`。用中文。

仓库 `/Users/luckye/Documents/Code/a2a`（sparse checkout，不要 checkout 或切分支）。候选改动：`/private/tmp/t199-review2/change.diff`。票：`.project-map/tickets/T-199-gone-pane-size.md`；证据与说明：`evidence/2026-10-27-batch28/T-199/RESULTS.md`；第 1 轮报告：同目录 `review-01/REPORT.md`。

第 1 轮提出三点：证据没有绑定代码版本（P2）、界面类型没有声明 null（P3）、建议在替身上显式标记“没有终端”。本轮处理：`registerGone` 的替身加 `gone: true`，`status()` 按它返回 `size: null`；`renderer.tsx` 的类型加 `| null`；`tests/test_t124_controller_e2e.py` 的 restart-working 场景加两项检查和 `gone-size-empty` 变异；补了端到端绿态、修前版本 606a5e193、变异三份结果，以及最终构建的界面复验与构建记录；README 补一句。

请：
1. 核对三点是否处理到位，`gone` 标记是否只覆盖替身，Pane 的其他使用者（例如 reclaim、archive、signal 里对 `pane.pty` 的使用）在替身上是否本来就有同类问题；只报与本改动相关、确定的问题。
2. 核对端到端证据：`e2e/*.json` 与 RESULTS 表格一致；检查是否真能区分修前和修后。你可以自己重跑（耗时几分钟）：`cd workbench && python3 tests/test_t124_controller_e2e.py --end restart-working --summary /private/tmp/t199-review2/<名>.json [--revision 606a5e193 | --mutant gone-size-empty]`；注意它用工作树源码，不要改仓库。
3. README 措辞是否与实现一致。

每条问题写：位置（文件:行）、失败场景、严重程度。最后给结论：`可合并` 或 `需修复`。不要把没查的写成已查。
