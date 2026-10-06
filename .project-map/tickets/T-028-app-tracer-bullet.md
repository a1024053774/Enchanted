---
id: T-028
title: Muster.app 的第一颗 tracer bullet
type: build
status: open
blocked_by: [T-027, T-025]
claimed_by:
supersedes:
---

## What to build

用户打开 Muster.app，看到一个项目窗口：顶部是该项目的任务标签页，主体是当前任务的 pane。pane 显示实时终端，可以用键盘和系统拼音输入法输入，状态在界面上可见。关掉窗口后，agent 继续在引擎里运行；重新打开时，窗口、任务页和 pane 都恢复。

应用只通过引擎的客户端协议与引擎交互，不持有 PTY 或进程，见 [spec](../specs/workbench-m1-2026-10-06.md) 的"引擎与应用的边界"。本切片不要求玻璃质感和强调色。

## Acceptance

- [ ] 启动 Muster.app 时，能连接已运行的引擎，或在引擎未运行时拉起它；窗口显示一个项目、它的任务标签页和当前任务的 pane。
- [ ] pane 显示实时终端：在 pane 中运行的命令输出，静止时与 `muster pane read` 一致，覆盖中英混排和宽字符。
- [ ] 键盘输入和系统拼音输入都到达 pane，内容与预期一致，且只到达一次。
- [ ] pane 的 working、blocked、idle、done 状态在界面上可见，并随 Codex pane 的真实状态变化。
- [ ] 关闭窗口后 agent 继续运行；重新打开后，窗口、任务页和 pane 都恢复。
- [ ] 构建在外置盘上进行；截图和录屏已存档，外观由用户判断。

## Resolution

未执行。
