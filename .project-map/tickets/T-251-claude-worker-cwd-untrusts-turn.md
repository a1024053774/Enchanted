---
id: T-251
title: Claude worker 在 Bash 里 cd 进子目录后，整个回合被判不可信，交付请求被静默丢弃
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 2
---

## What to build

2026-11-07 T-249-1 第一次派发时发现（执行主控自建的缺陷票，T-004 范围内）。用户当时说：“worker 应该卡住了,你并没有做好状态监控”。

现象：worker（Claude Code 2.1.319，`claude-opus-5-5` medium）在 18:02Z 提交了 `ed080306f`，并运行了 submit，回执是 `queued:true, delivered:false`，之后回合结束。门禁的任务一直停在 `claimed`，没有报错，也没有提醒任何人；交付请求和一条 issue 一直留在 `/private/tmp/a2a-requests-byPTXZ/`。4 个多小时后用户发现卡住了。

原因（只读查 `state.sqlite3` 的 `orchestration_events`，launch `6611fc18-…`）：

- `questions.ts` 的 `validateHookEnvelope` 要求钩子的 `value.cwd === pane.record.worktree`。Claude Code 钩子上报的 cwd 跟着 Bash 的当前目录走。
- 17:51:29Z，worker 第一次 `cd` 进 `workbench/app/panels`，之后每个 PreToolUse / PostToolUse 都记成 `native_question_unverified`（`question_origin_unverified`）。
- `currentTurnTrust` 把这一回合判为 `unknown`，而且这个判定不会再恢复。18:02:44Z 的 Stop 信号带着 relay 文件进来，被拒为 `current_turn_untrusted`；请求文件没有被消费，也没有生成任何提醒。

要做的：

- cwd 在 worker 工作区以内（含子目录）的钩子按本会话处理；工作区以外的仍拒绝。
- Stop 带着交付请求却被拒时，要让主控看得到：任务页或 `status` 写明原因；不能只留一条事件、任务停在 claimed。

### 2026-11-07 用户要求修（rev 2）

用户在 Claude Code 桌面会话里看了 T-249 那段对话后说：“从这个对话开始,现在这样的问题得修复,而且为什么旧 worker 不回收就派发不了新 worker”。本票按这句话标就绪并由 Claude Code 在当前会话里修（2026-11-01 起的分工），Codex 只读审查。

为什么旧 worker 不回收就派不出新的（读代码核对）：一个任务同一时间只有一个 current attempt；`revise` 把旧 attempt 记为 revoked，但它的会话没回收，`checkClaimPaths` 仍算它占着卡里的路径（同一任务的旧 attempt 也算），所以新的 `dispatch` 被拒（`path_overlap`；没 revise 时是 `already_claimed`）。只有 `reclaim` 停掉并归档旧会话后路径才释放，而 `reclaim` 要求 worker 不在回合中（`worker_working`），免得门禁杀掉正在干活的 agent。这条规则本身没错；错的是“它还在回合中”这个事实：Stop 因回合不可信被拒时，`claudeStop` 在把窗格记为空闲之前就抛错，窗格永远停在 busy，`reclaim` 永远被拒，新 worker 也就永远派不出去。

同类问题，一并修：

- 回合中途 Claude Code 压缩上下文后会发 `source: "compact"` 的 SessionStart（T-249 worker 在 18:57:07Z 真实发过一次）。旧代码只认 startup/resume，判成 `session_start_mismatch` 并记为身份不符，同样会让那一回合不可信。
- 真不可信的回合（确有来源核对不上的钩子）不放宽：请求仍不执行，但要记为拒收（以后的 Stop 也不重放），回合照常结束（窗格回到空闲，能回收、能重派），并给执行主控一条阻塞的系统问题（`status` 可见，经收件箱送达）。
- 执行主控技能第 4 步原来允许“dispatch 后查一次 status 就结束回合”，正是那次没人盯的做法；改为默认用后台 `run` 盯到结果，阻塞问题和门禁拒收经收件箱送到主控终端。

本票只改 Claude worker 的 Stop。Codex 与 agy/opencode 的 Stop（`panes.ts` 的共用 Stop 段与 `reportedStop`）在回合不可信时仍是旧行为；它们的 cwd 不随 `cd` 变，触发面小，留作后续。

## Acceptance

- [x] 修前红态：真实入口下，Claude worker 先 `cd` 进工作区子目录，再 submit，任务停在 claimed，请求没被消费。
- [x] 修后：同一场景交付进入 submitted；cwd 在工作区以外的钩子仍被拒（反例）。
- [x] 交付请求被拒时，执行主控的 `status` 能看到原因。
- [x] 回合中途的 compact SessionStart 不让回合变成不可信，交付照常受理（修前红态、修后绿态）。
- [x] 真不可信的回合结束后窗格不在回合中，旧 attempt 能回收，回收后同一任务能派出新 worker（修前：`worker_working`、派不出）。
- [x] 每条修复各有一个变异版本被测试判失败；单元测试拒绝前缀相同的兄弟目录、`..` 逃出工作区、相对路径。
- [x] 独立审查（GPT 只读，新开干净会话）。

## 不做

不在本票改正在运行的 /Applications/Enchanted.app；修好后什么时候换版另行决定。

## 临时做法

T-249-1 第二次派发时，任务卡要求 worker 把 Bash 的当前目录保持在工作区根目录（不 `cd`，用相对路径、`git -C`、`npm --prefix`）。第一次交付的提交用分支 `keep/T-249-1-a1` 钉住，新 attempt 从它 cherry-pick。

## Resolution

2026-11-07 关闭，PASS（[结果](../../evidence/2026-11-07-batch33/T-251/RESULTS.md)），分支 `fix/t251-untrusted-turn`，产品源码最终版本 `8e546df51`。

- 钩子、SessionEnd、compact SessionStart 与排队输入的会话记录：cwd 在本次启动的工作区或 extra 目录以内（含子目录）即算本会话。排队输入一项是审查 01 列为未证实、经 T-249 worker 真实会话记录核对属实后一并修的。
- 真不可信的 Claude worker 回合：请求记为拒收、永不执行；回合照常结束；给执行主控一条阻塞系统问题，`status` 可见，并实际送进在线执行主控的 CLI（端到端 `untrusted-online`）。修前该场景窗格一直在回合中，回收被拒 `worker_working`，再派被拒 `already_claimed`。
- 端到端三个原场景加在线主控场景，修前红、修后绿；6 个变异各在自己针对的检查上失败；单元与回归 PASS。`relay_scope` 有 4 项失败，父提交上同样失败，是已有问题。
- 审查：审查 01 需修复（3 条 P2）；第 2、3 条已改，第 1 条（符号链接）用真实 Claude Code 探针核对后复现不了，不改。复审 02 认可修复，缺送达证据，已由在线场景补上，没有开第三轮。
- 没做：Codex、agy、opencode 回合不可信时的 Stop 仍是旧行为（会同样卡住，触发面小）；正在运行的 /Applications/Enchanted.app 未换版，线上 T-249-1 仍卡着（22:26Z 回收被拒 `worker_working`）。
