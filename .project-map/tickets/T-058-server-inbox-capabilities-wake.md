---
id: T-058
title: 服务端收件箱、能力预设与写条目即唤醒
type: build
status: open
blocked_by: [T-055]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

让两个主控在工作台里也能用 Herdr 期同一套协议交接：

- 服务端收件箱：条目种类与字段同 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 5 节，只追加，确认也是新条目；MCP、HTTP、CLI 三种入口走同一个核心。
- 门禁全套命令的 MCP 工具，开放给执行主控。
- 能力预设：执行主控、构思主控、worker、reviewer/monitor 各一套，在 attach 或创建会话时选择。
- 写条目即唤醒：向某个角色写条目，服务端内部唤醒该角色的会话，两个主控不需要通用的 `thread:write`。
- 一个窄的紧急停止能力 `a2a:stop`，只给构思主控。

## Acceptance

- [ ] 红态在先：父修订上没有这些工具与预设，用例失败；保存输出与重放命令。
- [ ] 收件箱：种类集合、字段、`reply_to`、只追加、确认也是新条目，与 spec 第 5 节一致；MCP 工具 `a2a_inbox_send`、`a2a_inbox_list`、`a2a_inbox_ack`（能力 `a2a:inbox`）与 HTTP、CLI 走同一核心；无编辑、无删除。
- [ ] 门禁全套 MCP 工具（能力 `a2a:operate`）：create、claim、dispatch、attach、verify、integrate、reclaim、run、revoke、revise、status、events，与 CLI/HTTP 同一核心；契约不变，既有 35 项不变并通过。
- [ ] 能力预设与预期工具集：每个预设的 `tools/list` 精确等于 spec 第 1 节表格推出的预期集合，预期手写，不从实现输出复制。
- [ ] 反例：worker 凭据调不了 operate 与 inbox 工具；构思主控调不了 operate；reviewer/monitor 只能 `a2a_raise`；改能力需要重新发凭据（沿用 Synara 现有行为）。
- [ ] 写条目即唤醒：向某角色写条目后，该角色会话收到一条来源为 `agent` 的唤醒消息（含条目 id 与首行摘要）并起新 turn；目标会话不存在或已结束时不报成功，条目保留并标未送达；同一条目不重复唤醒。
- [ ] `a2a:stop`：只能中断；目标必须是受管或 attach 的 worker/reviewer/monitor 会话，不能是主控会话；仅当存在发给执行主控、超过 2 分钟仍无 `ack` 的 `stop` 条目时放行。逐条反例：无 stop 条目、不足 2 分钟、已确认、目标是主控会话、凭据无此能力。
- [ ] 角色预设在 attach 或创建时选择，不提供自由编辑能力的界面。
- [ ] 与 Herdr 期条目字段一致；本票不迁移旧文件条目，切换时旧文件冻结、不双写。
- [ ] 既有套件、typecheck、lint 通过；对上游文件的改动列清单。

## 说明

- 开工前对照 T-055 的实际结果重读 spec；发现不符，停下发 `needs-decision`，不绕开。
- 工具与能力的最终名字以本票 RESULTS 为准；改名须同步 spec 对应表格（走新 ticket）。
- 失败方式清单（处理方式写进 RESULTS）：目标角色有多个会话；目标会话正忙；唤醒消息与用户消息交叠；条目写入成功但唤醒失败；重复确认；能力集合在会话中途变化。
- 与 [T-056](T-056-user-input-coverage.md)、[T-057](T-057-issue-panel-completion.md) 会改同一批文件，同一文件同一时间只能有一个写入者，由执行主控串行安排。
- 授权来源：`ready_by: ideation`，`ready_rev: 1`。

## Resolution
