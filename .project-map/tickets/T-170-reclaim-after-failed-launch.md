---
id: T-170
title: 原生 CLI 在建立会话前启动失败，attempt 无法回收（reclaim 报 identity_conflict），任务停在 claimed
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：T-164 第三轮（实例 `/private/tmp/t164-dogfood-0zw8tib0`），B 的 attempt a2（launch `51773fcf-231c-471d-9bc1-ed8b26915a39`，Codex `zcode/GLM-5.3-Flash` max）。Codex CLI 0.164.0 启动约 16 秒后退出 1，终端原文 “Error: account/read failed during TUI bootstrap: account/read failed: workspace routing discovery timed out (code -32603)”，没有建立原生会话；后台记 `launch_failed`，如实。之后应用内主控 reclaim 被拒 `identity_conflict`：门禁 reclaim 要求 `native_session` 非空，且失败窗格 `blocked` 使 `checkErrorReclaim`/`run_blocked` 也拒绝。会话建立前就失败的 attempt 因此永远无法回收，任务停在 claimed，不能修订后重派。属 T-164 已批准范围（“被打回照常重派不限次数”）内的缺陷级票，执行主控按 T-004 自建。

目标：进程已确认退出、从未建立原生会话、没有回合、provider 已不在的 attempt，经门禁 reclaim 正常回收（停止、归档、清理工作区），任务可再派发。原生会话为空但 CLI 仍在运行时照旧拒绝。不按超时、不改状态绕过。

## Acceptance

- [ ] 红态：修前，用真实后台/PTY 与重放 B a2 原始终端输出的 Codex 替身，复现 reclaim 报 identity_conflict、任务不能再派发。
- [ ] 绿态：同一序列下 reclaim 受理，工作区移除，任务可再派发。
- [ ] 反例：原生会话为空但 CLI 仍在运行时 reclaim 仍拒绝；T-158、T-146 回归不变。

## 不做

不处理 Codex 账号路由超时本身（外部）；范围外的问题经问题上报。
