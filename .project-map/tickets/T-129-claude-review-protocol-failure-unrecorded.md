---
id: T-129
title: Claude reviewer 的结果格式不对时，门禁记不下审查协议失败
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

来源：T-123 端到端开发运行（2026-10-22）。执行主控在已批准范围内自建的缺陷级 ticket。

事实：reviewer 的最终消息不合审查协议时（`reviewRequest` 抛 `QualityProtocolError`），`workbench/src/daemon.ts` 调 `panes.caller({ ...identity, native_session: stop.session_id })` 取身份后再调 `gates.failReviewProtocol`。Claude Code 的身份核对要求 `prompt_id`（`src/panes.ts` 中 `pane.claudePromptId === turn`），这里没传，于是抛 `native_identity_required`：门禁没有记下审查失败，Stop 转交失败，任务停在 `reviewing`、审查停在 `running`，直到超时。T-123 开发运行 `dev7`（reviewer 事件 seq 298 `stop_transfer_failed`、299 `native_question_unverified`）与 T-122 端到端 `t122-dev` 都这样表现；当时触发协议错误的是 T-123 改动中漏改的 task 字符集，已在 T-123 中修正，本缺陷与之独立。

要做的：协议失败路径传入与正常路径相同的身份字段（含 `prompt_id`），让 Claude reviewer 的协议失败按 T-122 的规则记下，任务回到可重审状态。

## Acceptance

- [ ] Claude reviewer 最终消息不合协议时，门禁记下审查协议失败，任务不停在 `reviewing`；在真实入口用脚本化 Claude 复现。
- [ ] 去掉修复的变异在同一场景失败于 `native_identity_required`。
