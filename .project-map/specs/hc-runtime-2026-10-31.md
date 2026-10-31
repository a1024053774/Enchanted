# Spec: hc 运行时与问题先给主控（2026-10-31）

## Problem

用户这边看到的问题有三个：

- 终端层（编排后台里的 node-pty、终端查询应答、进程快照、重启恢复）只有用户一个人维护，维护不过来。
- 编排后台一重启，worker 和审查员随之消失，门禁只能回收、重派新 attempt，进行中的活白干。
- worker 卡住或上报问题时主控不知道，要靠轮询；问题界面里堆着主控本来能答的问题，blocking 的一上报就落到用户头上。

## Solution

- Enchanted 随应用打包固定版本的 Herdr `hc`，编排后台用独立 `HC_SESSION` 启动私有 core。项目终端、主控、worker、审查员、监视器都是这个 core 里的终端。用户自己的 Herdr 与它互不相连。
- 界面照旧显示 xterm.js 窗格；输出来自 hc 的 attach 流，按键和派发文字都经编排后台写进 attach 通道。门禁、任务卡、钩子、用户输入与派发记录留在编排后台。
- 编排后台重启后接回仍在运行的终端，原 attempt 继续；只有程序真的没了才走原生会话续接。
- 状态统一取 hc 的 OSC 7501 事件（Claude Code、Codex、agy、opencode），侧栏不再出现“未知”。
- worker 是主控终端的子终端：worker 卡住、出错、退出时，hc 给主控终端写一条通知；worker 上报问题时，门禁立即投给执行主控。主控能答的自己答，答不了或属于只交用户的类别才交给用户。
- 侧栏顶部有跨项目的“等你”分组，标签页有红点，应用内有提示；问题界面默认只显示“等你决定”。

## Decisions

- [T-209 用 Herdr 的 hc 当 Enchanted 的终端运行时](../tickets/T-209-hc-as-runtime.md)
- [T-210 问题先给主控处理，主控答不了的才交给用户](../tickets/T-210-issues-controller-first.md)
- 沿用：[T-124](../tickets/T-124-terminal-controller-answers-attach-run.md)（主控回答记为主控的话）、[T-051](../tickets/T-051-issue-reports-and-panel.md)（其余部分）、[T-206](../tickets/T-206-record-input-on-send.md)（发送时记录输入）

## Test seam

真实入口：真实编排后台加真实私有 hc core，经工作台现有的端到端测试驱动（`workbench/tests/test_daemon_gates_e2e.py`、`test_daemon_recovery_e2e.py`、`test_orchestrator_e2e.py`、`test_electron_e2e.py`）。门禁换了运行时，交付、恢复、编排场景须在 hc 上重新取得红态、绿态与反例，旧的通过结论不替新实现背书。真实 CLI 的测试用 Haiku（Claude）或用户设定的 Codex 模型，测试启动的 core 用测试专属 `HC_SESSION`，结束后停止并删除其状态目录。

## Slices

先切三张：

1. [T-211](../tickets/T-211-hc-facts-probe.md) hc 事实探针（无依赖）。
2. [T-212](../tickets/T-212-private-core-and-shell-panes.md) 私有 core 与项目终端走 hc（依赖 T-211）。
3. [T-216](../tickets/T-216-issues-pushed-to-controller.md) 问题上报即推给执行主控（无依赖，与 T-211、T-212 并行）。

前三张关闭后，按实际情况再切：受管窗格（worker、审查员、监视器）走 hc 并重新证明交付与编排场景；后台重启接回原 attempt 并修订恢复规格；状态统一取 hc 事件；worker 卡住经父子通知推给主控；跨项目“等你”分组与问题界面默认视图。

## Out of scope

- 多机（hc 的 SSH 机器）。
- 兼容 Herdr 的 mods。
- 改 hc 源码或 fork；碰到 hc 做不到的需求时另开决定票。
- 改门禁检查串本身的语义（只换运行时）。
