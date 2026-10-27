---
id: T-195
title: 右键复制会话的 CLI 名、原生会话 ID 与记录路径
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)（U10）。决定见 [T-189](T-189-real-use-fixes-decisions.md)第 4 条。

- 每个会话右键“复制深度链接”：复制形如“Claude Code 会话 <id>，记录 <路径>”的文本。
- 记录真实原生 ID：Claude Code 已有；Codex 取线程 ID；agy、opencode 先实测能否拿到并定位记录文件，拿不到的置灰并说明原因，不用我们自造的编号冒充。

## Acceptance

- [ ] Claude Code 与 Codex 会话复制出的 ID 与路径能直接打开对应记录文件。
- [ ] agy、opencode 的实测结论写进 findings；拿不到时菜单置灰。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution
