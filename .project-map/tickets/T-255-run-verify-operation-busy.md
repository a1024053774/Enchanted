---
id: T-255
title: run 的 verify 碰上 operation_busy 就暂停，同一回合后面还有请求时必现
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
---

## What to build

2026-11-08 T-249-1 第三次派发时发现（执行主控自建的缺陷票，T-004 范围内）。本票只记录，修复等用户决定先后。

现象：`run` 在 2026-11-08T09:06:41.377Z 以 `error: operation_busy`、`outcome: paused`、`phase: verifying` 结束，任务停在 `submitted`。门禁没有坏，手动发 `verify` 当场成功（09:07:37Z 机械验收通过）。

原因（读 `state.sqlite3` 的 `orchestration_events` 与 `workbench/src/gates/core.ts`）：

- worker 在回合结束时把 4 个请求一起交给后台（issue、issue、submit、issue）。后台按顺序处理：submit 处理完（41.230Z）任务变成 `submitted`，下一个 issue 拿着同一把操作锁（`relay_received` 41.230Z，`relay_processed` 41.672Z）。
- `follow` 看到 `submitted`，立即发 `verify`。`operationLock` 的 `busy_timeout` 是 0，返回 `operation_busy`。
- `core.ts:3205` 的 integrate 分支遇到 `operation_busy` 会等 100ms 再试；verify 分支（紧接 `task.state === "submitted" && !task.repair` 的那段）没有这段，直接抛出，`runFailed` 把 run 记为 paused。

后果：run 不再跟进后面的审查与集成，没有人主动提醒；主控不看结果就会以为 run 还在盯。

## Acceptance

- [ ] 修前红态：真实入口下，同一回合先 submit 再上报 issue，run 以 `operation_busy` 暂停。
- [ ] 修后：同一场景 run 继续走到 `reviewing`；verify 的其他拒绝照旧让 run 暂停（反例）。
