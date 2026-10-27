---
id: T-193
title: 主控可在多个已打开项目里建任务和派发
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

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)（U06、U11）。决定见 [T-189](T-189-real-use-fixes-decisions.md)第 1 条。

- 主控身份绑终端，不再由启动目录决定项目；建卡、派发、验收时指定项目，限已打开的项目。门禁对每个任务仍只认一个仓库。
- 额外目录说明改清楚：其中改动不进审查与集成；跨仓库请拆任务。
- 角色卡、`a2a help` 与产品页同步。

## Acceptance

- [ ] 在 a2a 目录启动并获批的执行主控，能给 github.io 建卡并派发，worker 出现在 github.io 下。
- [ ] 未打开的项目拒绝建卡并说明原因。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution
