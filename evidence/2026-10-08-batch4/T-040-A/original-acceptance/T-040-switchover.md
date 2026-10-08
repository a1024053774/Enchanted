---
id: T-040
title: 切换到工作台并删除旧运行路径
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
---

## What to build

M1 第 1～5 项通过且用户认可界面后，主控与 worker 的日常分派改到 Synara；删除 a2a 仓库中 Muster 引擎与 `coop.py` 的运行路径，参考实现留在 git 历史与证据中。更新 AGENTS.md、README、CONTEXT.md 与地图。

## Acceptance

- [x] 用户确认界面外观与切换时机。
- [ ] 删除后仓库内无 Muster/coop.py 运行入口；门禁 8/9/18 项经原生入口仍通过。
- [ ] 一次日常分派经 Synara 完成并留证据。

## 用户决定（2026-10-08）

- 外观："还可以，外观先这样"（T-043）。
- Q1 = A：日常用 fork 构建的桌面版，专用数据目录（`~/Library/Application Support/a2a-workbench`），与可能已装的官方 Synara 分开；Codex 用用户自己的登录。
- Q2 = A：主控仍是终端中的 Claude Code，派发、查状态、回收改为调用门禁 CLI/MCP；worker 由 Synara 原生创建为 Codex 会话，用户在任务窗口看进度。以后再考虑把主控搬进 Synara。
- Q3：先推送（a2a `be59634`、fork `d3b5bcc` 已推送），再开始删除。

分两部分并行：A 删除旧运行路径（a2a 仓库，经 Herdr worker）；B 工作台启动器与专用数据目录（fork）。两者完成后，主控经 Synara 完成第一次日常派发。

## Resolution
