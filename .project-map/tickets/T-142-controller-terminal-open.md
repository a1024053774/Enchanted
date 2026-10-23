---
id: T-142
title: 主控命令 terminal_open：让经批准的主控在项目内直接开界面里的普通终端
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 在本 session 逐字（第 5 条）：“5.按建议来”

现状：守护进程有 `shell_start`，但经角色申请成为主控的 CLI 只能 `a2a call` 门禁命令，开不了界面终端，只能让用户按 ⌘T（用户 2026-10-23 的截图里主控自己说“我开不了 Enchanted 终端”）。

1. 加主控命令 `terminal_open`：参数 `cwd`，必须在项目主目录或 T-140 的额外目录之内；在界面里开一个该项目的普通终端，返回终端标识。
2. 只对本项目已批准的主控开放，沿用 `role_command_not_scoped` 的范围规则；`a2a help` 与插件 SKILL.md 补上用法。
3. 不为每个 harness 加启动参数适配（用户裁定“按建议来”）。

## Acceptance

- [ ] 真实：已批准的主控 `a2a call terminal_open` 后界面出现新终端，cwd 正确。
- [ ] 越界目录、未批准会话、其他项目的主控均被拒（各一条反例）。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

