---
id: T-252
title: Codex、agy、opencode worker 的回合不可信时，Stop 被拒在窗格转空闲之前，窗格永远在回合中、回收不了、派不出新 worker
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

T-251 的后续（执行主控自建的缺陷票，T-004 范围内）。用户 2026-11-07 看了 T-249 那次对话后说：“现在这样的问题得修复,而且为什么旧 worker 不回收就派发不了新 worker”。T-251 只修了 Claude worker（`claudeStop`），票里写明 Codex、agy、opencode 的 Stop 留作后续：它们的 cwd 不随 `cd` 变，触发面小，但一旦触发会同样卡死。本票把 T-251 的做法推广到这两段。

原因链（读 `workbench/src/panes.ts` 核对，产品源码版本 `8e546df51`）：

- Codex 的钩子在 `signal` 里先过 `validateHookEnvelope`（cwd 在本次启动的工作区以内、`transcript_path` 是本会话的记录文件、`turn_id` 是当前回合）。核对不上时 `signal` 的 catch 记 `native_question_unverified`，`currentTurnTrust` 把这一回合判为 `unknown`，之后不会恢复。
- agy、opencode 没有按会话的钩子，回合结束由后台按 OSC 7501 自己发 Stop（`reportedStop`）。同一个 launch 进来的其他钩子在 `reportedStop` 的第一项检查被拒（`unsupported_hook`），同样记 `native_question_unverified`，回合同样变成 `unknown`。
- Codex 共用的 Stop 段（`signal` 里 `if (active) check(currentTurnTrust(...) === 'verified', 'current_turn_untrusted')` 那一块）和 `reportedStop` 在回合不可信时抛 `current_turn_untrusted`，抛在把窗格记为空闲之前。窗格永远算“在回合中”：`reclaim` 被拒 `worker_working`，同一任务再派被拒（`already_claimed`；revise 后是 `path_overlap`，旧 attempt 的会话没回收、仍占着卡里的路径）。交付请求留在请求目录里没有被消费，任务停在 `claimed`，没有任何人收到提醒。

要做的（照 T-251 在 `claudeStop` 里的做法，复用已有接口，不另开平行接口）：

- worker 的回合不可信、Stop 与当前回合匹配时：把 `refusal='current_turn_untrusted'` 交给 transfer；`relay.receive(..., refusal)` 不执行请求、按拒收记账（以后的 Stop 只重放拒收）；后台随后调 `gates.turnRefused(...)` 给执行主控追加阻塞系统问题并经收件箱送达；回合照常结束（被打断时仍 busy）。
- 不放宽：请求仍不执行；reviewer、monitor、controller 的不可信回合仍按旧行为拒绝；Stop 不匹配当前回合时仍按旧行为。
- 系统问题里的回合号：Codex、agy、opencode 的 Stop 没有 `prompt_id`，取 `turn_id`。

## Acceptance

- [x] 修前红态：真实入口下，Codex worker（真实 Codex CLI，模型换成本地脚本化 Responses 接口）的回合里进来一条工作区以外的钩子，再 submit：窗格停在回合中，回收被拒 `worker_working`，再派被拒，执行主控的 `status` 里没有问题。agy 或 opencode（T-187 的替身 CLI）同一场景同样红。（实测：Codex 经 `run` 派出时回收被拒 `worker_working`；agy、opencode 的窗格被记为失败，回收被拒 `run_external_unknown`；Codex 经 `dispatch` 派出时被拒 `identity_conflict`，是另一个根因，见 T-253。）
- [x] 修后：同一场景请求记为拒收、不执行（任务仍 claimed，没有候选提交）；回合结束后窗格不在回合中；执行主控的 `status` 有一条阻塞系统问题，写明 `current_turn_untrusted` 和被拒的 `submit`，交给收件箱；旧 attempt 能回收；回收后同一任务能派出新 worker。（Codex 只在 `run` 派出的路径上全过；`dispatch` 派出的回收见 T-253。）
- [x] 每条修复各有一个变异版本被测试判失败。
- [x] 回归：T-207、T-157、T-165、T-166 一类与 Codex、agy/opencode 正常交付 PASS。
- [x] 独立审查（Codex gpt-6.1-sol high，`codex exec -s read-only`，新开干净会话）一次。

## 不做

不改正在运行的 /Applications/Enchanted.app；不 push。线上 T-249-1 的卡住另行处理（要换版才生效）。

## Resolution

2026-11-07 关闭，PASS（[结果](../../evidence/2026-11-07-batch33/T-252/RESULTS.md)），分支 `claude/dreamy-ptolemy-d0f2f0`（在未合并的 `fix/t251-untrusted-turn` 之上），产品源码最终版本 `6159e7697`。

- Codex 的 Stop 钩子与 agy、opencode 由 OSC 7501 得出的回合结束（`reportedStop`），照 T-251 在 `claudeStop` 里的做法：worker 回合不可信、Stop 与当前回合匹配时，请求记为拒收、永不执行，回合照常结束，给执行主控一条阻塞系统问题（回合号取 `turn_id`）。复用 `refusal` 参数与 `gates.turnRefused`，没有新接口。
- 端到端：修前三家都红（Codex run 回收被拒 `worker_working`；agy、opencode 窗格被记为失败，回收被拒 `run_external_unknown`；再派都被拒 `already_claimed`，`status` 里没有问题）。修后 Codex（run）、agy、opencode 都 PASS，按修复提交重跑结果相同；5 个变异各在自己针对的检查上失败；回归 PASS。
- 另一个根因：经 `dispatch` 派出的 Codex worker 没有一次被受理的交付时回收被拒 `identity_conflict`（attempt 的 `native_session` 没绑定），与回合可信度无关，记为 [T-253](T-253-codex-dispatch-reclaim-identity-unbound.md)，待定。所以本票对 Codex 只证明了 `run` 派出的路径。
- 审查：审查 01 INCOMPLETE（没有确认本票新增的缺陷；审查中 HEAD 变动、绿态未绑提交号）；按提交号重跑绿态后，复审 02 在固定提交 `1e424ccc4` 上判 PASS（可合并，没有必须修的；`reportedEnding` 与快速连续 OSC 7501 报告的交错仍“未证实”），没有开第三轮。
- 没做：送进在线执行主控 CLI 引用 T-251 的 `untrusted-online` 场景（与 worker 用哪个 CLI 无关），本票没有再跑；`relay_scope` 与全量测试没跑；正在运行的 /Applications/Enchanted.app 未换版。
