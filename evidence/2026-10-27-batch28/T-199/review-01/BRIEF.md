# T-199 独立审查（只读）

你是独立审查员。只读审查，不改仓库文件，不操作 /private/tmp/t190 下正在运行的后台或应用，不碰 ~/Library/Application Support/a2a-orchestrator。报告只写到 `/private/tmp/t199-review/REPORT.md`。用中文。

仓库 `/Users/luckye/Documents/Code/a2a`（主 checkout 是 sparse，不要 checkout 或切分支）。候选改动：`/private/tmp/t199-review/change.diff`（`workbench/src/panes.ts` 一处）。

问题：后台重启后，已确认进程消失的 worker/reviewer 窗格由 `registerGone`（`workbench/src/panes.ts` 约 600～626 行）重建为只有 `pty: { pid }` 的替身；`status()` 原样返回 `size: { cols: pane.pty.cols, rows: pane.pty.rows }`，序列化成 `{}`。界面 `workbench/app/renderer.tsx` 约 260、347 行把它当作 PTY 尺寸，在只读分支调用 xterm `term.resize(undefined, undefined)`，窗格显示 “Error: This API only accepts integers”，内容不显示。修复：替身没有终端，`status()` 对它返回 `size: null`。

证据在 `evidence/2026-10-27-batch28/T-199/`：
- 红态：`red-pane-status.json`（size `{}`）、`ui/01-red-integer-error.jpg`。
- 绿态：`green-pane-status-gone.json`（size null）、`green-pane-status-live-shell.json`（活终端 160×45）、`ui/02-green-gone-pane-readonly.jpg`。
- 收尾：`cleanup-*.json`。

请：
1. 核对根因判断。其他会让 `pane.pty.cols` 不是整数的路径？`size` 的其他读者（`renderer.tsx:538` 的 data-readonly 等）在 null 时行为是否正确？
2. 判断修复层次：用 `Number.isSafeInteger(pane.pty.cols)` 判断“没有终端”，还是应该让替身显式标记“没有终端”，或在 `registerGone` 处改。按项目规则，不接受吞异常、兜底或兼容分支；请说明这里是否属于此类。
3. 红态证据是否来自未修代码的真实入口，绿态是否覆盖活窗格不受影响。

每条问题写：位置（文件:行）、失败场景、严重程度。最后给结论：`可合并` 或 `需修复`。不要把没查的写成已查。
