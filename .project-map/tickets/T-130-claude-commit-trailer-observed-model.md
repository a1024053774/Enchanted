---
id: T-130
title: Claude worker 的提交尾注写本回合实际的模型与强度，不再是 unknown
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

来源：T-129 真实运行（2026-10-22，sonnet 5.5 medium）。用户逐字：“修这个票”（指执行主控报告里的“Claude worker 提交尾注 A2A-Model、A2A-Effort 为 unknown”）。T-075 记为已知缺口，T-076 要求写实际值。

事实：
- `workbench/hooks/hook.py` 的 Claude 分支直接返回 `unknown, unknown`，注释称模型与强度要到 Stop 钩子才观测得到。
- 实际上，Claude Code 在会话记录（`<配置目录>/projects/*/<会话 id>.jsonl`）里给每条助手回复都写了实际回复的模型（`message.model`）和强度：新版写 `effort` 与 `perTurnEffort`，旧版只写其中一个。本机 192 份记录里，两者同时出现时从未不一致。
- 提交这条命令本身就是一条已写入的助手回复，所以提交时已经能读到本回合的事实。
- Codex 分支已经从原生会话记录读本回合事实，T-127 真实运行的尾注是实际值。

要做的：
- 钩子的 Claude 分支按 worker 启动时的原生会话 id（`A2A_NATIVE_SESSION`），在 `CLAUDE_CONFIG_DIR`（没有则 `$HOME/.claude`）的 `projects/*/` 下找唯一的会话记录。
- 取最后一条非 `<synthetic>` 的助手回复，写它的模型与强度。
- 规则与 Codex 分支一致：
  - 记录缺失时写 `unknown`；
  - 记录不唯一或越界、会话 id 不符时拒绝提交；
  - 两个强度字段都有但不一致时拒绝；都没有时写 `unknown`。
- 门禁规则不变：模型与交付记录一致，或者是字面量 `unknown`。Claude 的强度仍允许 `unknown`（记录行没写强度时），只把门禁里过时的注释改准确。

## Acceptance

- [x] 真实入口（T-122 端到端，真实 Claude Code 加脚本化接口）：Claude worker 的提交尾注 `A2A-Model` 是接口实际回复的模型（不同于请求的模型），`A2A-Effort` 是任务卡的强度；门禁 `trailer_check` 通过。修前版本在同一检查上失败。
- [x] 钩子在隔离条件下按失败清单检查：半行、`<synthetic>`、别的会话的记录、记录不唯一、两种强度字段、强度字段不一致、记录缺失。每项都有已知坏实现的反例。
- [x] 真实运行一次（真实模型）：尾注是实际值，并与 `native_turn_facts` 一致。
- [x] T-122 正常流程、T-127（Codex 尾注）回归通过。

## Resolution

2026-10-22 PASS，候选 566e54b57（README 619bb849）。提交钩子的 Claude 分支按启动会话号在 `CLAUDE_CONFIG_DIR`（或 `$HOME/.claude`）的 `projects/*/` 下读唯一的会话记录，写最后一条非 `<synthetic>` 回复的模型与强度；记录不唯一、越界、会话号不符或两种强度字段不一致时拒绝提交，缺失时写 unknown。门禁规则不变。证据：钩子单元 12 项，修前钩子与 9 个变异各自失败；T-122 端到端（真实 Claude Code 加以另一模型名回复的脚本化接口）尾注为接口实际回复的模型与任务卡强度，门禁 `trailer_check` 通过并走到集成，修前版本失败；T-127、T-129 两场景回归通过；真实运行（sonnet 5.5 medium）尾注 `claude-sonnet-5-5 / medium` 与 `native_turn_facts` 一致。见 [RESULTS](../../evidence/2026-10-22-batch20/T-130/candidate-1/RESULTS.md)。独立审查 agy（gemini-3.8-flash-high）PASS，无发现（`candidate-1/review-01.md`）。已知边界：提交后、交付前若会话换了模型，尾注与交付记录不一致，门禁按既有规则拒收（与 Codex 相同）。
