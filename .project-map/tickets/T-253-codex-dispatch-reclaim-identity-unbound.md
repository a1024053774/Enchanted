---
id: T-253
title: 经 dispatch 派出的 Codex worker 没成功交付过就回收不了（identity_conflict），同一任务派不出新 worker
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

2026-11-07 做 T-252 时实测发现（执行主控记录的缺陷，改的是门禁回收的身份规则，等用户或构思主控决定是否开工）。和用户 2026-11-07 问的“为什么旧 worker 不回收就派发不了新 worker”是同一类后果，根因不同：与回合可信度无关。

现象（`evidence/2026-11-07-batch33/T-252/`）：

- `red/e2e-codex.json`（修前源码）与 `green/e2e-codex-dispatch.json`（T-252 修后源码）：执行主控用 `dispatch` 派出 Codex worker，worker 的交付被拒（不可信回合）。修后窗格已回到空闲、问题已送进收件箱，但 `reclaim` 仍被拒 `identity_conflict`，再派被拒 `already_claimed`。修后那次 attempt 的 `runtime_identity` 里 `leader_pid` 已绑定，`native_session` 为空。
- 同一场景改用 `run` 派出（`green/e2e-codex-run.json`）：回收与再派都成功。

原因（读 `workbench/src/gates/core.ts` 核对）：

- `dispatch` 在 `startThread` 之后读一次窗格并绑定身份（`bindObservedIdentity`）。Codex 这时还没开始回合，原生会话号要等它写出 rollout 才知道，所以 attempt 的 `native_session`（有时连 `leader_pid`）是空的。
- 之后只有三处会补绑：`run` 每轮的 `observeRun`、worker 一次被受理的 `submit`、审查的提交。`raiseIssue` 不绑。
- `reclaim` 要求 attempt 的 `leader_pid` 与 `native_session` 都已绑定（`neverStarted` 的例外只给启动就失败的会话，T-170），否则拒 `identity_conflict`。

所以经 `dispatch` 派出的 Codex worker，只要没有一次被受理的 submit（交付被拒、只上报了问题就停下、被用户打断后不再交付），就永远回收不了，同一任务也派不出新 worker。Claude worker 不受影响（会话号在启动参数里，派发时已知）；agy、opencode 用后台自造的会话号，派发时已知。

可能的修法（不在 T-252 做）：

- A：`reclaim` 在核对前用当前窗格读数补绑身份，与 `observeRun` 相同（先 `checkThread` 核对 launch、thread、shell 进程一致，再补空项），在任务操作锁内写回。
- B：后台在得知 Codex 原生会话号时（首个钩子或 rollout 扫描）就把它绑定到 attempt。

决定（2026-11-08）：用户选 B，原话“先合并,然后修法选 B”（用户在本会话的父会话“Worker 回收与派发问题” `local_e9998522-d926-46a1-aac9-eda70d24d2b9` 里答复合并问题，由该会话逐字转来）。T-251、T-252 已先合并进本地 main（`faf1b0d7a`）。

## Acceptance

- [x] 修前红态：经 `dispatch` 派出的 Codex worker，交付被拒或没交付就结束回合后，回收被拒 `identity_conflict`。（实测“交付被拒”；“没交付就结束回合”没有单独跑，绑定与之后交不交付无关。）
- [x] 修后：同一场景回收成功、同一任务能派出新 worker；窗格身份与 attempt 记录不一致时（别的 launch、别的 shell 进程）仍拒 `identity_conflict`（反例）。（反例在门禁单元测试里，绑定被拒后回收仍拒 `identity_conflict`。）
- [x] 变异判失败；T-170（启动失败的回收）与 T-252 回归 PASS。（7 个变异；另有 T-127 与 `native_final_read` 回归。）

## 不做

不改正在运行的 /Applications/Enchanted.app。

## Resolution

2026-11-08 关闭，PASS（[结果](../../evidence/2026-11-08-batch34/T-253/RESULTS.md)），分支 `claude/dreamy-ptolemy-d0f2f0`（在 `faf1b0d7a` 之上），产品源码最终版本 `b01096b84`。

- 方案 B：窗格从根 rollout 的 `session_meta` 第一次得知会话号时（`panes.scan()`，后台得知 Codex 会话号只有这一处），后台调门禁的 `nativeSessionLearned`。和 run 的 `observeRun` 一样，在任务操作锁外读窗格，锁内用 `bindObservedIdentity` 核对身份再补空项，写 `runtime_bound`（`by: native_session_learned`）；从不持锁等待，锁被占着时隔 100ms 再试。attempt 已换掉、窗格身份不符、后台在停时不写，记 `native_session_bind_failed`，回收照旧拒绝。与 `observeRun` 不重复写：两处都只补空项。
- 端到端（真实 Codex CLI 0.164.0，本地脚本化模型）：修前回收拒 `identity_conflict`、再派拒 `already_claimed`；修后回收与再派都成功，事件顺序为 `dispatched`（会话为空）→ `pane_native_session` → `runtime_bound`。
- 审查 01（候选 `dbde5eeb4`）判 FAIL：P2 是停止时还有绑定在进行，关库后拒绝记录再抛错，成为未处理的 Promise 拒绝；P3 是 RESULTS 说宽了重启后的补绑。先用真实后台复现 P2，再在 `b01096b84` 修：
  - 读完窗格后查停止；
  - 停止流程关库前等登记过的绑定；
  - 拒绝记录写失败时照 `panes.recordFailure` 报 `event_write_failed`。

  新增后台层测试 `test_t253_shutdown.py`。复审 02 在固定提交 `8fad54c0d` 上判 PASS（可合并，没有必须修的），没有开第三轮。
- 回归：T-170 三个场景、T-252 的 Codex（run）、agy、opencode、T-127、`native_final_read` 都 PASS。`test_startup_shutdown_e2e.py` 的宿主不建操作者凭据，自 T-078-1 起就起不来，与本票无关，未计入。
- 没覆盖：
  - 后台重启后恢复的窗格不会再“第一次得知”，B 不调用。在“得知”与“写入”之间停掉的 attempt、本修复之前派出的 attempt，仍回收不了。`observeRun` 只补仍在运行的窗格。
  - 真实 CLI 下停止与绑定重叠的时序没有端到端证据。
  - 停止时等绑定没有超时。
  - 全量测试与真实厂商模型没跑。
  - 正在运行的 /Applications/Enchanted.app 未换版。
