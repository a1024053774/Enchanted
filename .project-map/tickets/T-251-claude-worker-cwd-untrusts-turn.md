---
id: T-251
title: Claude worker 在 Bash 里 cd 进子目录后，整个回合被判不可信，交付请求被静默丢弃
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by: executor
ready_rev: 1
---

## What to build

2026-11-07 T-249-1 第一次派发时发现（执行主控自建的缺陷票，T-004 范围内）。用户当时说：“worker 应该卡住了,你并没有做好状态监控”。

现象：worker（Claude Code 2.1.319，`claude-opus-5-5` medium）在 18:02Z 提交了 `ed080306f`，并运行了 submit，回执是 `queued:true, delivered:false`，之后回合结束。门禁的任务一直停在 `claimed`，没有报错，也没有提醒任何人；交付请求和一条 issue 一直留在 `/private/tmp/a2a-requests-byPTXZ/`。4 个多小时后用户发现卡住了。

原因（只读查 `state.sqlite3` 的 `orchestration_events`，launch `6611fc18-…`）：

- `questions.ts` 的 `validateHookEnvelope` 要求钩子的 `value.cwd === pane.record.worktree`。Claude Code 钩子上报的 cwd 跟着 Bash 的当前目录走。
- 17:51:29Z，worker 第一次 `cd` 进 `workbench/app/panels`，之后每个 PreToolUse / PostToolUse 都记成 `native_question_unverified`（`question_origin_unverified`）。
- `currentTurnTrust` 把这一回合判为 `unknown`，而且这个判定不会再恢复。18:02:44Z 的 Stop 信号带着 relay 文件进来，被拒为 `current_turn_untrusted`；请求文件没有被消费，也没有生成任何提醒。

要做的（待用户决定是否现在做）：

- cwd 在 worker 工作区以内（含子目录）的钩子按本会话处理；工作区以外的仍拒绝。
- Stop 带着交付请求却被拒时，要让主控看得到：任务页或 `status` 写明原因；不能只留一条事件、任务停在 claimed。

## Acceptance

- [ ] 修前红态：真实入口下，Claude worker 先 `cd` 进工作区子目录，再 submit，任务停在 claimed，请求没被消费。
- [ ] 修后：同一场景交付进入 submitted；cwd 在工作区以外的钩子仍被拒（反例）。
- [ ] 交付请求被拒时，执行主控的 `status` 能看到原因。

## 不做

不在本票改正在运行的 /Applications/Enchanted.app；修好后什么时候换版另行决定。

## 临时做法

T-249-1 第二次派发时，任务卡要求 worker 把 Bash 的当前目录保持在工作区根目录（不 `cd`，用相对路径、`git -C`、`npm --prefix`）。第一次交付的提交用分支 `keep/T-249-1-a1` 钉住，新 attempt 从它 cherry-pick。
