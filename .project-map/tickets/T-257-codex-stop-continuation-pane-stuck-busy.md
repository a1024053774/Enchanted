---
id: T-257
title: Codex 回执在 Stop 钩子返回前贴入，同一 turn 续跑后窗格永远停在 busy，回收被拒，队列卡住
type: build
status: closed
blocked_by: []
claimed_by: executor-55d61e9f
supersedes:
ready: yes
ready_by: executor
ready_rev: 3
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

- [x] 修前红态：真实入口下，回执在 Stop 钩子返回前贴入，窗格停在 busy，`reclaim` 返回 `worker_working`。
- [x] 修后：同一场景窗格回到空闲，排队消息照常发送，`reclaim` 成功；真在工作中的回合仍返回 `worker_working`（反例）。

## 本轮执行授权与计划（2026-11-08）

用户本轮逐字要求：“先修 T-257，走门禁派发并盯到结果，再继续 T-249/T-250；别启动 Claude，别跳过敏感变更集成前的用户证据批准。”用户选择：“先修 T-257，再继续两个面板（推荐）”。完整原话与此前现场见 [执行交接](../../evidence/2026-11-08-controller-switch/executor-handoff.md)。本轮执行主控的 Enchanted 角色申请 `94be9df4-1496-4c90-8a11-f3218398fa32` 已于 10:41:50Z 获界面批准。

范围只含本票缺陷；T-255、T-256 与两个面板的实现不在这个 worker 子任务中。worker/reviewer 均用 Codex `gpt-6-astra`、`xhigh`、普通速度。经门禁 dispatch，submitted 后手动 verify；不用自动集成的 run。

REALITY GATE: INCOMPLETE。已观察到旧 attempt 的 Stop/续跑/未匹配 Stop 与 busy 记录；“反馈先于 Stop 钩子返回导致同 turn 续跑”仍是待验证推断。worker 先经隔离真实后台、门禁、原生 Codex CLI 复现，记录时间顺序与 reclaim 返回，再决定最小修复；实现前不得将推断写成事实。预期是结束后空闲、反馈继续投递且可回收；负例是真正在工作时仍拒绝回收。不得通过重启、改库、伪造 idle 或宽松回收掩盖问题。

证据放 `evidence/2026-11-08-batch34/T-257/`；主控维护本票与该目录的 controller 子目录，worker 只写 worker 子目录及任务卡列出的实现/测试文件。旧现场保留。

## 红态与恢复（2026-11-08，ready_rev 2）

REALITY GATE: PASS（仅因果复现）。隔离真实后台/门禁/交互 Codex 已复现首 Stop 未返回时贴入回执、同 turn 续跑后 Stop 不匹配、busy 与 reclaim worker_working；真正工作中的两次回收也拒绝。见 [红态摘要](../../evidence/2026-11-08-batch34/T-257/controller/red-controller-diagnostic-02.json) 与 [恢复记录](../../evidence/2026-11-08-batch34/T-257/controller/recovery-approved.md)。产品修复仍为 INCOMPLETE。

正式 worker 自身也触发此缺陷，主控答复未送达。用户本轮在“是否批准现在正常重启 Enchanted 后台、保留现有提交与证据，再经门禁回收旧 attempt 并用 astra xhigh 重派继续修复？”下明确回答：“批准重启并经门禁恢复（推荐）”。已正常停止旧后台和受管进程，正式应用启动新后台 71177，主控身份仍有效，旧 worker stopped=true、queued=[]；随后经门禁修订、回收、重新派发。

旧提交 e9e9f2db8ce6f2c50b453a868c8bcaa026e9fa8b 保存在 keep/T-257-1-a1。v2 延续相同范围与 Acceptance：继承复现测试、修正第二个 Stop 的多余 active=true 限定与跨进程时间排序，基于已取得红态做最小修复。沙箱外真实测试由主控运行，worker 不扩大权限；未完成实测必须明示，候选通过门禁及敏感变更的用户证据批准后才集成。

## 第二次交付与验收准备（ready_rev 3）

候选 5484315a5e318bce557dcc32e429f5d251453e84 的 4 行生产差异已通过真实入口绿态、同测试坏版本红态及 T-252 Codex 回归，见 [候选检查点](../../evidence/2026-11-08-batch34/T-257/controller/candidate-a2-checkpoint.md)。整体仍 INCOMPLETE，尚无独立审查或集成。

主控在派发后新增保留引用导致 verify 被共享 Git 元数据保护拒绝，该引用已撤回并保留拒绝证据；旧正式运行时又使 submit 回执续跑卡 busy，门禁退回无法送达。沿用本轮已批准的正常重启和门禁恢复。v3 只把门禁工作区的既有依赖准备写进完成及红态命令，导入已提交的卡内候选，不更改 Acceptance，不绕过重新交付或验收。

## 门禁通过与集成

v3 attempt `6ca3622b-b0e7-41ad-a21f-7ff810441994` 交付 `045e815ff390a0e2e50b7788966e2a5bf655fbdb`。完成检查和红态对照均经真实后台/门禁/Codex 0.167.0；父版本命中 5 项业务失败，候选 9 项业务检查通过。独立 astra xhigh 审查 `1042a9e2-4d76-4b00-8213-e4cb4252462c` 可合并、无 findings，104 个模块场景通过、4 个错误变异全部拒绝，结束边界与回收完成后任务进入 verified。

已经唯一门禁 integrate 合入本地 main：`bf4b855619283711aff0a2f9ff2047e689e21fcb`，未 push。见 [门禁结果](../../evidence/2026-11-08-batch34/T-257/controller/gate-v3-mechanical.json)、[独立审查](../../evidence/2026-11-08-batch34/T-257/controller/review-v3-result.json)、[集成收据](../../evidence/2026-11-08-batch34/T-257/controller/integration-v3.json)。实际产品差异不在 REVIEW.md 的敏感代码段。README 已改正“回执必定新建原生回合”的描述，并核对地图 Verified。全套测试未运行，既有 T-252 Codex 相关回归通过。

代码修复 PASS；正式应用更新与旧 worker 回收待标准打包安装后完成。门禁保留了含测试摘要的验证工作区（问题 `b45f888d-b9f4-4b20-a584-0ed9866d48a2`），摘要已另存，不强制删除或改库掩盖清理失败。

## Resolution

2026-11-08 13:27Z。

PASS：修复已集成并装入正式应用。版本 0.1.6，包源码 `08b8318f54224790916b7b95016e551499a0a0fa`，产品代码与门禁集成一致；新后台 PID 36212，原执行主控身份继续有效。T-257 a3 和旧 T-249 attempt 均经门禁回收成功，后者恢复 ready。见 [安装收据](../../evidence/2026-11-08-batch34/T-257/controller/installation.json) 和 [恢复结果](../../evidence/2026-11-08-batch34/T-257/controller/recovery-final.json)。

Works：同一真实入口在父版本命中 5 项业务失败，在候选通过 9 项业务检查；完成后空闲、排队消息只发送一次、可回收，以及真实工作中拒绝回收均有证据。独立审查无 findings。

No regression：T-252 Codex 相关 7 项回归、104 个模块场景通过，独立 4 项错误变异拒绝；标准打包与签名校验通过。未跑全套测试。project-map 脚本在本轮收尾读取外部技能路径时阻塞，没有取得新的脚本通过结果；README stale 已人工按实际产品差异核对并更新 Verified。

Risk / undo：旧安装包保留在 `/private/tmp/enchanted-rollback-t257-20261108-1/Enchanted.app`。需要撤回时走正常停止后台、恢复旧包和重启；代码可经新门禁任务撤回 4 行产品差异。门禁验证工作区清理失败的现场仍保留，未强制删除；本次打包与下载缓存约 721 MB 已记录体量后清理。
