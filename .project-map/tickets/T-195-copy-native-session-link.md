---
id: T-195
title: 右键复制会话的 CLI 名、原生会话 ID 与记录路径
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)（U10）。决定见 [T-189](T-189-real-use-fixes-decisions.md)第 4 条。

- 每个会话右键“复制深度链接”：复制形如“Claude Code 会话 <id>，记录 <路径>”的文本。
- 记录真实原生 ID：Claude Code 已有；Codex 取线程 ID；agy、opencode 先实测能否拿到并定位记录文件，拿不到的置灰并说明原因，不用我们自造的编号冒充。

## Acceptance

- [x] Claude Code 与 Codex 会话复制出的 ID 与路径能直接打开对应记录文件。
- [x] agy、opencode 的实测结论写进 findings；拿不到时菜单置灰。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution

2026-10-27 PASS。侧栏会话右键“复制深度链接”，后台 `native_link` 只给“现在这个会话”的原生号与记录路径：受管 Claude、Codex 核对窗格里没换会话或线程，Codex 记录读不了即置灰；终端里 Claude、Codex 按报告它的进程，agy、opencode 一律置灰并说明原因。真实 Claude Code 与真实 Codex 的记录独立核对、红态、变异与回归，独立审查 5 轮（前 4 轮 NO_GO，已修；第 5 轮无发现，审查沙箱内完整 e2e 超时已归因于环境），见 [RESULTS](../../evidence/2026-10-27-batch28/T-195/RESULTS.md)。T-104 回归的既有失败与本票无关，归因见同文件。
