---
id: T-246
title: 普通终端里已退出 CLI 的钩子晚到时，会覆盖当前前台 CLI 的原生会话报告
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

2026-11-03 T-242 复审（[REREVIEW.md](../../evidence/2026-11-03-batch31/review-3/REREVIEW.md)）指出：回合状态只有一个槽位，已退出 CLI 的钩子晚到时，会覆盖当前前台 CLI 的状态。T-242 已改为按进程号分别保存（`workbench/src/shellTurns.ts`）。主控按同一条不变式（钩子报告只属于报告它的进程）搜索相关代码时，发现 T-195 的原生会话报告也是同样的写法，只读代码推导，没有运行复现：

- `workbench/src/panes.ts` 的 `noteShellHook` 无条件执行 `pane.native = report.session`，`noteNativeReport` 用最后到达的报告覆盖唯一的 `pane.nativeReport`，并写 `shell_native_session` 事件。
- 时序：终端里 A（Claude Code 或 Codex）退出，B 启动并报告了自己的会话；A 的一个钩子随后才到。`nativeReport` 变成 A 的，读取时进程号不符，B 的会话显示为没有；`pane.native` 是 A 的会话；状态库里最后一条 `shell_native_session` 也是 A 的。这些都要等 B 再发一次钩子才恢复。

要做的：先经真实入口或注入晚到钩子复现，确认 `pane.native` 与记录被改写各自的影响；再按根因修（例如只接受当前前台进程或尚未被取代的进程的报告），并穷举事件顺序验证。

## Acceptance

- [ ] 复现，或附依据说明这条时序到不了。
- [ ] 若是缺陷：修前留红态；修后 B 的会话报告不被 A 的晚到钩子改写，记录里不出现 A 覆盖 B 的条目。
- [ ] 独立审查无未处理的阻塞意见。

## Resolution
