---
id: T-193
title: 主控可在多个已打开项目里建任务和派发
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

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)（U06、U11）。决定见 [T-189](T-189-real-use-fixes-decisions.md)第 1 条与 [T-196](T-196-path-judgement-by-controller.md)第 3 条。

- 主控身份绑终端，不再由启动目录决定项目；建卡、派发、验收时指定项目，限已打开的项目。门禁对每个任务仍只认一个仓库。
- 跨仓库的拆法由主控判断（[T-196](T-196-path-judgement-by-controller.md)第 3 条）。额外目录给不给写、给哪些由主控按任务决定（派发时指定，记入启动记录）；说明写明其中改动不经审查与集成，要进门禁的跨仓库改动拆成每仓一个任务。
- 角色卡、`a2a help` 与产品页同步。

## Acceptance

- [x] 在 a2a 目录启动并获批的执行主控，能给 github.io 建卡并派发，worker 出现在 github.io 下。
- [x] 未打开的项目拒绝建卡并说明原因。
- [x] 主控派发时指定的额外目录写进 worker 启动参数与启动记录；未指定时不给。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution

2026-10-27 PASS。主控按 `project` 或完整任务 id 在已打开项目里建卡、派发，未打开的拒绝；额外目录派发时逐次指定，记入 attempt、启动记录与 argv，未指定不给；获批后恢复、冲突替换和启动前都只核对不重新解释。真实入口红态、绿态、变异与 T-123/T-140/T-141 回归，独立审查 4 轮（前 3 轮 NO_GO，已修），见 [RESULTS](../../evidence/2026-10-27-batch28/T-193/RESULTS.md)。
