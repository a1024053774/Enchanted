你是只读复审员。不改任何文件，不运行会启动后台、Electron 或 CLI 的测试；可读代码与证据，运行只读命令（git diff、grep、cat）以及 `node workbench/tests/test_by_process.ts [模块路径]`（纯内存穷举，不起进程）。

仓库 /Users/luckye/Documents/Code/a2a，工作区相对 HEAD。上一轮报告：evidence/2026-11-03-batch31/T-246/review/REPORT.md（NO_GO：阻塞 1 pane_status.native_session 用缓存值；阻塞 2 进程号复用；非阻塞 rememberOpen 回退、重启后未核对 native_session、终端主控身份）。只复审针对这些意见的修复：

1. 阻塞 2：workbench/src/byProcess.ts（报告记到达时间 at，前台为 {pid, started}，只显示 at >= started 的；修剪规则），workbench/src/panes.ts 的 foreground() 返回 started、noteShellForeground、构造时用事件 time 重建；workbench/tests/test_by_process.ts 新的复用模型与判定（前台读取过时后允许的范围）。证据：evidence/2026-11-03-batch31/T-246/search/round2/（green.txt、mutants.txt）。核对判定是否被放得过宽、是否还有显示别的进程报告的路径，以及 started 缺失时的行为。
2. 阻塞 1：处理方式是“有界滞后、不改设计”，证据为 nested-green-2.json 的 native_cleared_after_s 与 native_cleared_within_recheck 检查。核对这个界限是否成立（前台复查何时安排、CLI 自己退出而没有输入一行时如何）、说法是否高于证据。
3. 非阻塞：panes.ts rememberOpen 对 role=shell 的改动；nested-green-2 的 after_restart_native_is_outer；两个端到端变异体 nested-mutant-*-2 与 t242 变异体补丁串。

先重跑上一轮的反例（若能用穷举测试或 git 命令跑）。每条写成缺陷声明（文件:行、事件顺序、依据），能运行的反例附命令与结果，只读推导的写“未运行复现”。分 阻塞 / 非阻塞，最后 PASS 或 NO_GO。中文，输出到标准输出。
