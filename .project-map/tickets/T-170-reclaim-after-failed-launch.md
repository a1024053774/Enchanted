---
id: T-170
title: 原生 CLI 在建立会话前启动失败，attempt 无法回收（reclaim 报 identity_conflict），任务停在 claimed
type: build
status: closed
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

- [x] 红态：修前，用真实后台/PTY 与重放 B a2 原始终端输出的 Codex 替身，复现 reclaim 报 identity_conflict、任务不能再派发。
- [x] 绿态：同一序列下 reclaim 受理，工作区移除，任务可再派发。
- [x] 反例：原生会话为空但 CLI 仍在运行时 reclaim 仍拒绝；T-158、T-146 回归不变。

## 不做

不处理 Codex 账号路由超时本身（外部）；范围外的问题经问题上报。

## Resolution

2026-10-24 PASS。三次提交、三次 agy 审查：
- 第一版（aa2d7104a，审查 01 PASS，合并 121f604e8）：原生会话为空、窗格已停止、无回合、provider 不在的 attempt 可 reclaim。
- 后续（c822751c8，审查 02 PASS）：CLI 在 dispatch 回执前就退出时，dispatch 先保存 claimed 与观察到的身份再拒绝 run_blocked；reclaim 的“从未启动”分支不要求 leader 已观察到。红态 `--scenario fast` 在修前与第一版各 1 次复现，绿态 fast ×2、failed、hang 反例 PASS。
- 测试修正（b89f64b75，审查 03 PASS）：现场记录随测试携带，缺失即报夹具错误；此前全量回归 11/12 的 T-170 项因稀疏检出缺记录而替身立即崩溃，原因已在 RESULTS 与 merge-wave README 更正。
- 全量回归 `RUN-MERGE-REGRESSION-12` 在 b89f64b75：首跑 54/55（t141-green 公网 curl 超时 exit 28），单独重跑通过；T-170 三个场景按设计 PASS。
- 未覆盖：未逐项变异 neverStarted 的各条件；未在真实 Codex 路由失败下复验（外部故障不可控），留给 T-164 第四轮顺带观察。
