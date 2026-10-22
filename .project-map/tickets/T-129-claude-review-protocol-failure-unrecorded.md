---
id: T-129
title: Claude reviewer 的结果格式不对时，门禁记不下审查协议失败
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

来源：T-123 端到端开发运行（2026-10-22）。执行主控在已批准范围内自建的缺陷级 ticket。

事实：reviewer 的最终消息不合审查协议时（`reviewRequest` 抛 `QualityProtocolError`），`workbench/src/daemon.ts` 调 `panes.caller({ ...identity, native_session: stop.session_id })` 取身份后再调 `gates.failReviewProtocol`。Claude Code 的身份核对要求 `prompt_id`（`src/panes.ts` 中 `pane.claudePromptId === turn`），这里没传，于是抛 `native_identity_required`：门禁没有记下审查失败，Stop 转交失败，任务停在 `reviewing`、审查停在 `running`，直到超时。T-123 开发运行 `dev7`（reviewer 事件 seq 298 `stop_transfer_failed`、299 `native_question_unverified`）与 T-122 端到端 `t122-dev` 都这样表现；当时触发协议错误的是 T-123 改动中漏改的 task 字符集，已在 T-123 中修正，本缺陷与之独立。

要做的：协议失败路径传入与正常路径相同的身份字段（含 `prompt_id`），让 Claude reviewer 的协议失败按 T-122 的规则记下，任务回到可重审状态。

## Acceptance

- [x] Claude reviewer 最终消息不合协议时，门禁记下审查协议失败，任务不停在 `reviewing`；在真实入口用脚本化 Claude 复现。
- [x] 去掉修复的变异在同一场景失败于 `native_identity_required`。

## Resolution

2026-10-22 PASS，候选 b3bd8aa84（README 补充 03965053）。用户：“既然不是模型的问题那就修，然后实测一次”。Claude reviewer 的两条失败路径（结论不合协议、合协议但被门禁拒收）取调用者身份时补上 `prompt_id`，与正常路径一致；门禁按既有规则记下 `review_protocol_failed`，审查 `unknown`、任务 `paused` 并开质量问题，不再停在 `reviewing` 等超时。重新审查经处理质量问题后的 reclaim/revise 或受管 run 的新 attempt（门禁状态机不变）。证据：T-122 端到端加 `--review-result malformed|rejected`，两例在修后通过，修前版本与只去掉任一处修复的变异都失败于 `native_identity_required`；T-122 正常流程、T-124 restart-verified、T-127 回归通过；真实运行（用户自己的 claude，sonnet 5.5 medium 的执行主控、worker、reviewer）走到集成，没有出现 Stop 转交失败。见 [RESULTS](../../evidence/2026-10-22-batch20/T-129/candidate-1/RESULTS.md)。独立审查 agy（gemini-3.8-flash-high）PASS，无发现（`candidate-1/review-01.md`）。顺带发现 Claude 尾注模型为 unknown，用户要求修，另开 T-130。
