---
id: T-191
title: 侧栏按 CLI 显示图标与名称；agy、opencode worker 状态取回合信号
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

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)（U04、U05、U09）。决定见 [T-189](T-189-real-use-fixes-decisions.md)。

- 每个 agent 行前显示所属 CLI 的图标（Claude Code、Codex、agy、opencode），标签不再把后两家写成“未知”；CLI 识别集中在 `terminalClis` 一处。
- worker、审查员的状态对 agy、opencode 取 OSC 7501 回合信号（与主控一致），不再只看窗格是否存活。图标来源与许可在 README 写明。

## Acceptance

- [ ] 四种 CLI 的 worker 在侧栏各显示正确图标与名称。
- [ ] agy worker 交付后回到空闲时侧栏显示空闲（修前同场景一直转圈）。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution
