---
id: T-253
title: 经 dispatch 派出的 Codex worker 没成功交付过就回收不了（identity_conflict），同一任务派不出新 worker
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

- [ ] 修前红态：经 `dispatch` 派出的 Codex worker，交付被拒或没交付就结束回合后，回收被拒 `identity_conflict`。
- [ ] 修后：同一场景回收成功、同一任务能派出新 worker；窗格身份与 attempt 记录不一致时（别的 launch、别的 shell 进程）仍拒 `identity_conflict`（反例）。
- [ ] 变异判失败；T-170（启动失败的回收）与 T-252 回归 PASS。

## 不做

不改正在运行的 /Applications/Enchanted.app。
