---
id: T-246
title: 普通终端里已退出 CLI 的钩子晚到时，会覆盖当前前台 CLI 的原生会话报告
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

2026-11-03 T-242 复审（[REREVIEW.md](../../evidence/2026-11-03-batch31/review-3/REREVIEW.md)）指出：回合状态只有一个槽位，已退出 CLI 的钩子晚到时，会覆盖当前前台 CLI 的状态。T-242 已改为按进程号分别保存（`workbench/src/shellTurns.ts`）。主控按同一条不变式（钩子报告只属于报告它的进程）搜索相关代码时，发现 T-195 的原生会话报告也是同样的写法，只读代码推导，没有运行复现：

- `workbench/src/panes.ts` 的 `noteShellHook` 无条件执行 `pane.native = report.session`，`noteNativeReport` 用最后到达的报告覆盖唯一的 `pane.nativeReport`，并写 `shell_native_session` 事件。
- 时序：终端里 A（Claude Code 或 Codex）退出，B 启动并报告了自己的会话；A 的一个钩子随后才到。`nativeReport` 变成 A 的，读取时进程号不符，B 的会话显示为没有；`pane.native` 是 A 的会话；状态库里最后一条 `shell_native_session` 也是 A 的。这些都要等 B 再发一次钩子才恢复。

要做的：先经真实入口或注入晚到钩子复现，确认 `pane.native` 与记录被改写各自的影响；再按根因修（例如只接受当前前台进程或尚未被取代的进程的报告），并穷举事件顺序验证。

## Acceptance

- [x] 复现，或附依据说明这条时序到不了。（票面“退出后晚到”附依据说明很窄、未复现；同一不变式经嵌套 `claude -p` 复现）
- [x] 若是缺陷：修前留红态；修后 B 的会话报告不被 A 的晚到钩子改写，记录里不出现 A 覆盖 B 的条目。
- [x] 独立审查无未处理的阻塞意见。（复审第 1 条附证据答复为已知局限，按 T-240 不再开轮）

## Resolution

2026-11-03 关闭（PASS）：用户“做 T-246”。普通终端的原生会话报告与回合状态按报告它的进程（进程号加启动时间）分别保存，只用前台进程自己报的（`workbench/src/byProcess.ts`，由 T-242 的 `shellTurns.ts` 泛化）；重启按全部记录重建；前台复查失败时不留会话。真实 Claude Code 端到端（外层 Bash 工具运行内层 `claude -p`）修前失败于“内层运行时链接不可用、`native_session` 是内层的”，修后八项 PASS，两个变异体与前台复查失败注入各失败于预期处；`test_by_process.ts` 穷举 PASS，四个坏实现都失败；t195、t242、t184、t133 回归 PASS。已知局限：进程号在钩子请求路上被复用（macOS 顺序分配，实测见证据）；Codex 嵌套没有端到端跑过。

证据：[T-246 RESULTS.md](../../evidence/2026-11-03-batch31/T-246/RESULTS.md)。

2026-11-04 补记：Codex 嵌套端到端已补做（用户：“这条要做”）。`test_t246_nested_codex_native_e2e.py` 八项 PASS，变异体失败于预期处。补做过程中发现普通终端里交互式 Codex 根本报不来会话，拆为 [T-247](T-247-terminal-codex-hook-cli-unrecognized.md) 修复。证据见 `evidence/2026-11-03-batch31/T-246/codex-nested/`。
