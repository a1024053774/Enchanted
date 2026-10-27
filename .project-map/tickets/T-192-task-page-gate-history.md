---
id: T-192
title: 任务页显示门禁全程，已结束的票不再是空页
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

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)（U07、U08）。决定见 [T-189](T-189-real-use-fixes-decisions.md)。

- 点进任务时，不论有没有存活窗格，都显示：任务卡（目标、路径、完成条件）、每个 attempt 的时间线（认领、交付、检查、审查、集成、回收及原因）、审查报告、打分、集成提交与尾注。有存活窗格时窗格在上，记录在下。
- 门禁增加任务关闭状态（主控经门禁关闭），关闭的票不再显示“待认领”。
- 对照产品页第 1 节第 3 步的说法，做不到的改产品页。

## Acceptance

- [ ] 已回收的票（如 a2a+T-138）点进去能看到上述内容，不是空页。
- [ ] 关闭后的票在任务格显示“已关闭”。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution
