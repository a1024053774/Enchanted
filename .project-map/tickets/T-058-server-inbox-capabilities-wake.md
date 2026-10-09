---
id: T-058
title: 服务端收件箱、能力预设与写条目即唤醒
type: build
status: closed
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

- [x] 红态在先：父修订上没有这些工具与预设，用例失败；保存输出与重放命令。
- [x] 收件箱：种类集合、字段、`reply_to`、只追加、确认也是新条目，与 spec 第 5 节一致；MCP 工具 `a2a_inbox_send`、`a2a_inbox_list`、`a2a_inbox_ack`（能力 `a2a:inbox`）与 HTTP、CLI 走同一核心；无编辑、无删除。
- [x] 门禁全套 MCP 工具（能力 `a2a:operate`）：create、claim、dispatch、attach、verify、integrate、reclaim、run、revoke、revise、status、events，与 CLI/HTTP 同一核心；契约不变，既有 35 项不变并通过。
- [x] 能力预设与预期工具集：每个预设的 `tools/list` 精确等于 spec 第 1 节表格推出的预期集合，预期手写，不从实现输出复制。
- [x] 反例：worker 凭据调不了 operate 与 inbox 工具；构思主控调不了 operate；reviewer/monitor 只能 `a2a_raise`；改能力需要重新发凭据（沿用 Synara 现有行为）。
- [x] 写条目即唤醒：向某角色写条目后，该角色会话收到一条来源为 `agent` 的唤醒消息（含条目 id 与首行摘要）并起新 turn；目标会话不存在或已结束时不报成功，条目保留并标未送达；同一条目不重复唤醒。
- [x] `a2a:stop`：只能中断；目标必须是受管或 attach 的 worker/reviewer/monitor 会话，不能是主控会话；仅当存在发给执行主控、超过 2 分钟仍无 `ack` 的 `stop` 条目时放行。逐条反例：无 stop 条目、不足 2 分钟、已确认、目标是主控会话、凭据无此能力。
- [x] 角色预设在 attach 或创建时选择，不提供自由编辑能力的界面。
- [x] 与 Herdr 期条目字段一致；本票不迁移旧文件条目，切换时旧文件冻结、不双写。
- [x] 既有套件、typecheck、lint 通过；对上游文件的改动列清单。

## 说明

- 开工前对照 T-055 的实际结果重读 spec；发现不符，停下发 `needs-decision`，不绕开。
- 工具与能力的最终名字以本票 RESULTS 为准；改名须同步 spec 对应表格（走新 ticket）。
- 失败方式清单（处理方式写进 RESULTS）：目标角色有多个会话；目标会话正忙；唤醒消息与用户消息交叠；条目写入成功但唤醒失败；重复确认；能力集合在会话中途变化。
- 与 [T-056](T-056-user-input-coverage.md)、[T-057](T-057-issue-panel-completion.md) 会改同一批文件，同一文件同一时间只能有一个写入者，由执行主控串行安排。
- 授权来源：`ready_by: ideation`，`ready_rev: 1`。

## Resolution

2026-10-09 worker `s11-t058` 修复交接：**INCOMPLETE，保持 open，待主控关闭**。按主控 #14 / 决定 01 实现；最终 fork `d9fc40a5f8b14d22ec7568c7ccef542572e79102`。唯一独立审查对 9f29 返回 FAIL（非法 assign 方向）；真实 MCP 红态后修复，十种 kind 的非法方向在 MCP/HTTP/CLI 追加前拒绝，最终相关检查与既有 35 项通过。按 brief 不自行追审，最终候选没有独立审查；真实三 turn 边界证据属于 9f29，不转移为 d9fc 的新模型通过。见 [RESULTS-02](../../evidence/2026-10-09-batch11/T-058/RESULTS-02.md) 与 [原审查](../../evidence/2026-10-09-batch11/T-058/acceptance-review-19.md)。Acceptance 不勾选，执行主控决定验收与关闭。

2026-10-09 worker `s11-t058` 首轮：**BLOCKED，保持 open，待主控关闭**。fork 基线 `e9545960c50e4d0f8d687aef0da8073b2419adaa`，未改产品代码、无 fork 提交。现有 registry 总是授予通用能力，落实精确预设需要 brief 明确要求先批准的两处额外上游接入；blocking 问题 `20261009T205838Z-worker:s11-t058-issue-001`。位置、最小选项与父修订红态探针见 [RESULTS](../../evidence/2026-10-09-batch11/T-058/RESULTS.md) 和 [needs-decision](../../evidence/2026-10-09-batch11/T-058/needs-decision-01.md)。35 项、真实服务/模型及独立审查尚未运行，未勾选 Acceptance。

**执行主控关闭（2026-10-09）：PASS，依据 ready_rev 1 与执行主控决定 01。** fork 最终候选 `d9fc40a5f`（分支 `a2a`，父修订 `e9545960c`），证据至 `f47b951`，见 [RESULTS-02](../../evidence/2026-10-09-batch11/T-058/RESULTS-02.md)。实际 MCP tools/list 与手写预期相等（executor 17、ideation 8、worker 2、reviewer/monitor 各 1），角色反例、凭据冻结与重新签发、普通会话仍为父修订六种能力；收件箱三入口同一核心、只追加、ack 终结；唤醒真实新 turn（9f29 候选，3 个真实 Codex turn）、未送达不报成功；`a2a:stop` 时钟边界 120000 拒绝/120001 放行与逐条反例；T-057 的 session-ended 转交在 executor 未确认列表可见。独立审查（9f29）FAIL/P1：executor 可发 assign；d9fc 在追加前按 spec 第 5 节校验 assign/revise/cancel、report/needs-decision、issue 的方向，十种 kind 的非法组合经 MCP/HTTP/CLI 追加前拒绝。该 15 行修复由执行主控自审通过；最终 fmt/lint/typecheck/migrations、gates 17、server 87、既有 35 项 exit 0。上游清单：`AgentGateway.ts` 注册、`Services/Layers/AgentGatewaySessionRegistry.ts` 能力类型与签发。blocking 问题 `20261009T205838Z-worker:s11-t058-issue-001` 待用户关闭。附注：Herdr 期 worker 曾向 executor 写 needs-decision（`scripts/inbox` 允许），服务端按 spec 只允许 executor→ideation；工作台中 worker 改用 issue 上报。
