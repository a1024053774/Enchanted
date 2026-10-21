---
id: T-121
title: 在项目终端里认领主控：a2a 命令与 skill、界面批准、侧栏显示角色
type: build
status: open
blocked_by: [T-120]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：[T-119](T-119-herdr-style-terminals-claimed-roles.md)、[spec](../specs/herdr-style-claimed-roles-2026-10-21.md)。用户 2026-10-21 让主控直接实现（“都由你来做吧,codex 太慢了”）。

第一条贯通切片。用户添加项目后打开的终端在项目目录里，和一般终端一样。终端里有 `a2a` 命令，支持的 CLI 按 T-120 的结论自动读到使用说明。

用户在终端里启动 Claude Code，说“你去做执行主控”，agent 用 `a2a` 申请这个角色。Enchanted 显示“窗格 X 申请成为执行主控”，用户点批准后，侧栏里这个会话显示为执行主控，`a2a` 能报出它的身份。只有已批准的主控身份才能用主控才有的 `a2a` 操作。

只有主控走认领与批准。worker、reviewer 由后台启动时定身份，见 T-122。

## Acceptance

- [ ] 真实入口：打包测试版里，项目终端中的真实 Claude Code 按 skill 申请执行主控，界面批准后侧栏显示“执行主控”，`a2a` 报出的身份与之一致。截图、后台库事件读回、重现命令留证。
- [ ] 未批准、被拒绝的申请，以及没有认领的普通终端，调用主控操作时都被门禁拒绝，并留下拒绝记录。
- [ ] 认领申请里的角色、窗格、项目由后台核对，窗格不能替别的窗格申请；同一项目同一主控角色同时只能有一个已批准的会话。
- [ ] 不写 `~/.claude`、`~/.codex` 和用户项目仓库（运行前后核对）。
- [ ] 修前版本跑同一入口失败（没有 `a2a` 命令或没有认领流程）。
- [ ] `project_map.py status` 0 问题。
