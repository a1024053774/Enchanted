# A-07 I1 active 提交恢复分析

只读现场：A-07 controller pane 为 `busy`，active dispatch 是 `7d714d00-bdd0-40aa-88b3-871916938bae`，`nativeTurn=null`；事件有 `dispatch_queued`、`paste_intent`、`paste_written`、`turn_submit_intent`、`turn_submitted`，没有 `turn_start_signal`、`Stop` 或 API request。故 hookTrace 红态发生在 Claude UserPromptSubmit 之前，当前提交没有可匹配的 Claude prompt_id。

现有路径的边界：

- `panes.signal` 的 Stop 只有在 `pane.claudePromptId` 与 Stop 的 `prompt_id` 匹配时才会清 active；当前没有 prompt_id，伪造 Stop 会得到 `stop_not_matched`，不能收回。
- `A2AGates.emergencyStop` 只接受 worker/reviewer/monitor target；controller 会被 `worker_target_required` 拒绝，不能用 operator stop 代替。
- `Panes.stopThread` 只接受 idle pane；当前 busy active 会被 `worker_not_idle` 拒绝。
- `daemon_stop` 会关闭整个 A-07 root，属于现场回收，不是单回合恢复。
- 认证窗口的用户 Esc 路径会记录真实用户 action、退休 active 并进入声明/放行语义；当前现场没有已建立的 window identity，且本轮不启动 Electron、不发送 Esc，因此未执行。

结论：在当前授权和现场状态下，没有可由 operator 或 hook 伪造的安全收回路径。若主控能批准一次现有窗口用户 Esc → 声明/放行，则可保留 A-07；若不能提供该用户动作，需 A-08 重建：daemon_stop/panes.shutdown 关闭 A-07 的 7 个进程，归档读回 root，重新生成带 hookTrace 修复的材料并重走 Stage A/B1，成本是一次新的 Stage-A/B1 审批与逐屏流程，A-07 active 证据保留为红态。
