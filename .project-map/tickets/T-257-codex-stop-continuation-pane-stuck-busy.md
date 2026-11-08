---
id: T-257
title: Codex 回执在 Stop 钩子返回前贴入，同一 turn 续跑后窗格永远停在 busy，回收被拒，队列卡住
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
---

## What to build

2026-11-08 T-249-1 第三次派发时发现（执行主控自建的缺陷票，T-004 范围内）。它挡住了 T-249-1 的重派；修不修、何时重启后台等用户决定。

现象（launch `f36d7d22-41a2-4819-ba48-36ebda96a99a`，Codex CLI 0.167.0，attempt `6bab2eb9-0d63-4bb1-b325-f70fa6df2d2b`，`orchestration_events`）：

- 09:06:39.457Z 第一个 Stop（`stop_hook_active: false`），后台处理这一回合的 4 个请求，用时约 2.4 秒。
- 09:06:41.900Z `pane_idle`；09:06:41.996Z 门禁回执 #30 贴入窗格。
- 09:06:51.356Z `turn_start_signal`，`turn_id` 与上一回合相同（`01a1ba59-d21a-…`）。
- 09:06:58.923Z 第二个 Stop（`stop_hook_active: true`，同一 `turn_id`），记为 `stop_not_matched`。
- 09:06:59.208Z 原生记录 `task_complete`：Codex 已结束，后台没有再记 `pane_idle`。
- 09:12:50.576Z 门禁退回 #32 进入队列，到 09:17Z 仍没有贴入。
- `reclaim` 返回 `worker_working`。worker 工作区干净，HEAD 是 `0c3da7ade`。

推断（读 `workbench/src/panes.ts`，未做隔离复现）：回执在 Stop 钩子返回 Codex 之前贴入，Codex 把它当成同一 turn 的继续；后台已把这个 turn 算结束，第二个 Stop 匹配不上，窗格一直 busy。

后果：worker 回收不了、路径不释放、新 worker 派不出去，排队的门禁消息也送不到。一回合内有多个请求时 Stop 处理变长，更容易碰上，T-250 也可能遇到。

## Acceptance

- [ ] 修前红态：真实入口下，回执在 Stop 钩子返回前贴入，窗格停在 busy，`reclaim` 返回 `worker_working`。
- [ ] 修后：同一场景窗格回到空闲，排队消息照常发送，`reclaim` 成功；真在工作中的回合仍返回 `worker_working`（反例）。
