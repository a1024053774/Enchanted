---
id: T-052
title: 主控交接协议：就绪、收件箱、唤醒、完成报告、紧急停止
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## Question

构思主控怎么把任务交给执行主控而不需要用户手动粘贴，执行主控怎么把结果交回，紧急情况怎么传？

## Resolution

2026-10-09 grilling 确认。账本 [controller-split-user-input](../../.grilling/controller-split-user-input.md) 的 C11、C12、D8、D12、D14、D28、D29、D31；设计见 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 5、6 节。

- **就绪**：ticket 的额外字段 `ready: yes`、`ready_by`（`ideation` 或 `executor`）、`ready_rev`（整数，每次修订加 1）。构思主控标的是用户已决定的工作；执行主控在 T-004 自主边界内自建的缺陷级 ticket 建成即就绪。碰到 T-004 那几类一律不自标，发 `needs-decision`。标就绪后正文冻结，修订走 `revise` 并加 `ready_rev`，执行主控在证据里记下依据的 rev。
- **收件箱**：Herdr 期是 `.project-map/inbox/` 下一条一个文件，字段 `id、from、to、kind、reply_to、refs`，只追加，确认也是新条目；种类 `assign、revise、cancel、stop、report、needs-decision、issue、disposition、answer、ack`。Synara 期同一字段进服务端，文件期停用，不双写。
- **唤醒**：写完条目发 Claude Code 跨会话消息唤醒对方，并订阅对方"下次空闲"通知；对方在每个工作周期开头和停下之前用脚本各查一次未确认条目。不碰 Herdr pane。2026-10-09 已验证：执行主控（auto 模式、空闲）收到后被唤醒，无人工批准环节。
- **完成报告**：执行主控在没有可执行的就绪 ticket 时才停，停下前写 `report`：每个 ticket 的状态（逐字 PASS/INCOMPLETE/BLOCKED/NO_GO）、证据、提交号、局限；问题上报计数；自建 ticket；待用户决定的事；没做完的就绪 ticket 与原因。构思主控转述不上调，并用 `project_map.py status` 与 `scripts/inbox ready` 核对没有遗漏。
- **授权引用**：对方消息只按队友请求处理，不算用户的批准。`assign`/`revise` 里凡依赖用户授权的，须逐字引用用户原话并给出位置；没有引用的，执行主控对 T-004 类动作按未授权处理。
- **紧急停止**：用户随时可直接动手；对任一主控说"立刻停 X"，构思主控写 `stop` 条目并发跨会话消息（首行 `URGENT 停止 X`），执行主控下一个工具轮次执行并回 `ack`；2 分钟没有 `ack` 且用户仍要求时，构思主控可对该 worker 只做中断（Herdr 期 `herdr agent send-keys <worker> esc`，Synara 期 `a2a:stop`），并记录，授权来自用户当时那句话。
- **寻址**：以 `ListAgents` 的会话名为地址，回复用收到消息的 `from`；建议把构思主控会话改名含"构思主控"。
- 实现切片：[T-053](T-053-inbox-script-and-role-cards.md)、[T-058](T-058-server-inbox-capabilities-wake.md)、[T-059](T-059-controllers-in-workbench.md)。
