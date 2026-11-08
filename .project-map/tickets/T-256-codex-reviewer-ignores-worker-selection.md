---
id: T-256
title: Codex 审查员不跟随 worker 的模型与强度，派发时指定的选择只对 worker 生效
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
---

## What to build

2026-11-08 T-249-1 第三次派发时发现（执行主控自建的缺陷票，T-004 范围内）。本票只记录，修不修、怎么修等用户决定。

用户要求（2026-11-08，Claude Code 会话 `local_e9998522-d926-46a1-aac9-eda70d24d2b9`）：

> 先装新版,然后你自己启动软件继续,这次用 opus5.5 extra 当主控,然后 astra extra 当 worker 和 reviewer

现象：worker 启动记录 `f36d7d22-…` 是 `gpt-6-astra`、`xhigh`。审查员启动记录 `60d51e63-…` 是 `gpt-6.1-sol`、`high`（出厂设置）。

原因：`workbench/src/panes.ts` 的 `createReview` 写的是 `if (task.card.executor.cli !== "Codex") { 用 worker 启动记录的选择 } else await this.createPane(task, attempt, reviewConfig, review);`。Codex 审查员不带覆盖参数，`executionSelection("reviewer", {})` 只取工作台设置，任务卡的 `executor` 和 `dispatch`、`run` 的 `model`、`effort` 都不影响它。

说法不一致的地方：`a2a` 技能第 4 步写“审查者默认用同一个 CLI 与模型”；AGENTS.md 写“reviewer 默认与 worker 使用同一个模型（取设置）”。只有设置里两个角色相同时，这两句才都成立；主控按用户要求覆盖 worker 时就不成立。

## 待决定

选一个写法，并让代码、技能、AGENTS.md 说同一件事：

- 甲：Codex 审查员也跟随 worker 启动记录的模型与强度（和其他 CLI 一样）。
- 乙：审查员永远取设置，改技能说明，并让 `dispatch`、`run` 能显式指定审查员的选择。

## Acceptance

- [ ] 修前红态：真实入口下，Codex worker 按 `gpt-6-astra` xhigh 派发，审查员启动记录不是这个选择。
- [ ] 修后按决定的写法，审查员启动记录符合预期；设置与派发参数的优先级有反例。
