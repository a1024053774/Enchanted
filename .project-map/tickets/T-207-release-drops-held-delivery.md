---
id: T-207
title: 按 Esc 再发消息后，worker 的交付在“放行”后不进门禁
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

来源：真实用户式试用第 3 轮 3b（[RESULTS](../../evidence/2026-10-27-batch28/UAT-03/RESULTS.md) 发现 2）。

经过（测试状态库 `/private/tmp/uat3/state` 的事件，seq 为 orchestration_events）：

1. worker 在派发回合里干活时，用户按 Esc（536 `claude_submission_retired` reason `user-esc`），接着发了一句话（540 `user_prompt_unregistered`，541 用户回合 `cb16e0b6`）。
2. worker 在这个用户回合里改完代码并提交交付请求；回合结束（689 Stop），后台判为 `current_turn_untrusted`，窗格仍是“被打断、等用户放行”，请求文件留在请求目录里没处理。
3. 用户在任务页点“输入框已空，放行”（789 `user_queue_release`）。`releaseByUser` 只清掉窗格状态并 drain 派发队列，没有处理请求目录里搁着的请求，也没有提示。门禁仍是 `claimed`，主控 `verify` 得到 `not_submitted`。
4. 直到用户又让 worker 跑了一个回合（878），那个回合结束时请求才被收下（904、906 `relay_received`），门禁变为已交付。

要定的是：被打断后用户自己发出的回合里，worker 经 a2a 接口交的请求怎么处理才对——例如回合结束时就按该回合的身份核对并受理；或放行时一并受理、拒收并说明原因。先定方案再做。不能为了放行就跳过身份核对。

## Acceptance

- [ ] 修前版本经真实入口复现：Esc、发一句话、worker 在该回合交付、放行后门禁仍未收到交付。
- [ ] 修后同一操作：交付按方案被受理，或被明确拒收并在界面和 worker 窗格说明下一步；不需要再让 worker 跑一个回合。
- [ ] 身份核对不放宽：伪造的或别的回合的请求仍被拒收。

通用：先在真实入口留红态再修根因；独立审查。

## 不做

改 Esc 的打断语义；T-206 的输入记录方式。

## Resolution
