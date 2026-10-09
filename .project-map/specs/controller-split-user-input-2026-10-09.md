# Spec：构思主控与执行主控、用户输入记录、问题上报（2026-10-09）

本 spec 是日期记录，综合 grilling 会话 [controller-split-user-input](../../.grilling/controller-split-user-input.md) 已确认的决定，不提出新问题。之后的变更走新 ticket，不改写本文。用户确认了什么、哪些是委托决定，见 [基线确认记录](controller-split-user-input-baseline-2026-10-09.md)。

## Problem

- 用户的想法、纠正、批准和回答散在各个 agent 会话与界面里，没有被当作数据保存。在 Herdr 下，主控注入的提示词和用户亲手打的字在 Codex 原生会话里同为 user 消息，没有来源字段可以区分（账本 F4）。
- 现在只有一个主控，讨论想法、做决定、拆 ticket、派发、盯进度、验收都在同一段长对话里；用户要在"构思"和"执行"之间手动搬运 prompt 与想法。
- 用干净上下文的 worker/reviewer 能发现主控对话里看不到的问题，但这些发现夹在会话里，用户自己会错过，主控也没有机械的接收与处置步骤。
- 这些功能没做好，用户就不会把日常使用挪进 Synara 工作台。用户的话："肯定要把我提的功能至少都做的能用了，我才能到 Synara 里用。"

## Solution

两个主控分上下级，一套追加式记录把三类流动连起来：

```text
用户 ⇄ 构思主控 ──assign / revise / cancel / stop──▶ 执行主控 ──派发──▶ worker / reviewer / monitor
              ◀── report / needs-decision ─────────┘                          │
用户的问题面板 ◀──────────────────── 问题上报（issue）─────────────────────────┘
```

- **构思主控**是用户日常只看的上层主控：接收想法、澄清、写决定/spec/ticket、标就绪、向执行主控分发任务、转述完成报告。
- **执行主控**监督执行：派发、盯进度、审查、验收/集成/回收（全经门禁）；没有可执行的就绪 ticket 时才停，停下前写完成报告。
- **用户输入记录**把用户本人的输入存成数据，与主控发出的提示词分开存放。
- **问题上报**让 worker/reviewer/monitor 把范围外的发现直接交给用户的面板；主控可以判断并关闭"不是问题"的，拿不准的留给用户；主控同样可见。
- **两期实现**：Herdr 期用文件、脚本、派发包装、角色卡和 Claude Code 跨会话消息；Synara 期用服务端表、MCP 工具、能力预设和任务窗口里的面板。Herdr 期做法在日常派发改走工作台时停用，不双写。

## Decisions

- [T-049 构思主控与执行主控的分工、层级与权限](../tickets/T-049-controller-roles-and-permissions.md)
- [T-050 用户输入记录：类型、存放、与人工介入的关系、过渡期](../tickets/T-050-user-input-records.md)
- [T-051 问题上报与面板：语义、处置、发送](../tickets/T-051-issue-reports-and-panel.md)
- [T-052 主控交接协议：就绪、收件箱、唤醒、完成报告、紧急停止](../tickets/T-052-controller-handoff-protocol.md)
- 沿用：[T-004 主控停止边界](../tickets/T-004-major-decision-stop-boundary.md)、[T-023 主控是角色](../tickets/T-023-controller-placement.md)、[T-044 attach 会话是普通会话加角色](../tickets/T-044-agent-driven-task-window.md)。

## 已核实的事实（2026-10-09）

| 事实 | 来源 |
| --- | --- |
| 现有 `human_intervention` 只记"thread 属于某 attempt 且 `dispatchOrigin=user` 的 `thread.message-sent`"；写入门禁 `events` 表（`task` 必填），`human_inputs(event_id)` 去重；记录器失败时变更命令被拒；它按 `attempts` 查 thread，不查 `attachments` | fork `a2a` 分支 `90e38b6`，`packages/a2a-gates/src/core.ts` 的 `recordHumanInput` |
| `dispatchOrigin` 是消息上的可选字段，缺省为 `user`；门禁 dispatch/attach 投递的提示词为 `agent`，自动化为 `automation`；门禁自己发的命令 `commandId` 以 `a2a:` 开头 | fork `decider.ts`、`apps/server/src/a2a/service.ts` |
| 审批与结构化提问的答复是独立命令 `thread.approval.respond`、`thread.user-input.respond`，只有 commandId、threadId、requestId、决定或答案、时间，没有来源字段；界面经 WS RPC `orchestration.dispatchCommand` 发出它们，以及停止、中断 | fork `packages/contracts/src/orchestration.ts`，`apps/server/src/wsRpc.ts`，`apps/web/src/components/chat/respondToThreadApproval.ts` 等 |
| Synara 已有"异步提问"：Codex 助手消息附 `questions: [{title, options?}]`，用户答复是普通用户消息，格式为每题"标题 + 换行 + 答复"、题间空行 | fork `packages/contracts/src/asyncUserInput.ts`、`packages/shared/src/asyncUserInput.ts` |
| MCP 能力在发凭据时固定（`issue(threadId, provider, {additionalCapabilities})`），工具声明 `requiredCapability`，`tools/list` 按能力过滤；`a2a_submit` 需 `thread:write` 加活跃 turn 并核对调用 thread；门禁 create/dispatch/attach 目前只有 CLI/HTTP | fork `agentGateway/Services/AgentGatewaySessionRegistry.ts`、`toolRuntime.ts`、`a2a/tools.ts` |
| Synara 网关已有 `synara_send_message`（唤醒另一个会话）、`synara_interrupt_thread`（中断） | fork `agentGateway/Layers/AgentGateway.ts` |
| Herdr 下 Codex 原生会话里的 user 角色消息有三类：AGENTS.md 注入、主控派发、用户对 worker 提问的答复（包在 `<send_user_message_question_reply>` 里，内容 `[{answer, question}]`）；主控注入与人手输入没有来源字段 | 2026-10-09 的 Codex rollout（T-044、T-045 worker） |
| Claude Code 跨会话消息：到对方时包成 `<cross-session-message from="…">`；对方权限模式不同时可能被扣下等批准；`notify_when_idle` 在对方下次空闲时通知一次；对方消息只按队友请求处理，不算用户对待决提示的批准。2026-10-09 实测：执行主控（auto 模式、空闲）收到后被唤醒，无人工批准环节，回程同样到达 | `SendMessage` 工具定义；本会话试发与 ack |
| Herdr CLI：`herdr agent prompt <名字> "文本" [--wait --timeout]`；`herdr agent send-keys <名字> esc`（中断当前 turn）；`agent prompt` 遇到停在审批或提问界面的 agent 返回 `agent_blocked` | herdr skill 文档 |
| `project_map.py` 的 ticket `status` 只认 open/closed/superseded/out-of-scope，其余 frontmatter 键被忽略 | `project_map.py` |
| Claude 对话文件在 `~/.claude/projects/<项目目录>/<会话 id>.jsonl`；`cleanupPeriodDays` 未设置，按默认保留期清理（约 30 天，为推断） | 本机设置与目录 |

## 1. 角色、层级与权限

| 角色 | 是什么 | 做 | 不做 |
| --- | --- | --- | --- |
| 用户 | 人工负责人 | 决定目标、范围、验收、权限、方向；答复问题；随时直接动手停止 | — |
| 构思主控 | 上层主控，用户日常界面 | 接收想法、澄清、grilling、写决定/spec/ticket、标就绪、assign/revise/cancel/stop、接收并转述 report 与 needs-decision、判断设计/目标/权限级的问题上报、提醒用户 | 不派发、验收、集成、回收 worker；不替用户做 T-004 类决定；不改执行主控已认领 ticket 的正文，要改走 `revise` |
| 执行主控 | 监督执行 | 执行就绪 ticket；派发、盯进度、审查、验收/集成/回收（经门禁）；写 brief、证据、Resolution；在 T-004 自主边界内自建并执行缺陷级 ticket；判断任务级问题上报；没有可执行的就绪 ticket 时停下并写 report | 不改目标、规则、术语和他人标就绪的 ticket 正文；不把设计级问题在自己会话里展开 |
| worker | 干净上下文的执行 agent | 只做分配的 task/attempt；发现范围外问题就上报 | 不扩大范围；不改地图和规则；不自己决定忽略问题 |
| reviewer | 干净上下文的审查 agent | 只读审查；上报发现 | 不 submit、不集成 |
| monitor | 只读观察者 | 观察并上报 | 不 claim、submit、集成，不宣布成功 |

**写入范围**（提示词约束，不做路径级强制）：

- 构思主控写：`intent.md`、AGENTS.md 的规则、CONTEXT.md 的术语、MAP.md 的目的地/决定/范围、decide/compare 类 ticket、spec、build ticket 的正文与就绪字段、`.project-map/roles/`、自己发出的收件箱条目。
- 执行主控写：brief、证据、运行记录、就绪 ticket 的认领/验收勾选/Resolution/关闭、自建 ticket、实现后 living doc 的事实性漂移（路径、命令、已删除项，并在 report 里列出）、MAP.md 的 fog 追加、自己发出的收件箱条目。规则、术语、决定、目的地只由构思主控改，且须用户接受。

**停止边界**：沿用 [T-004](../tickets/T-004-major-decision-stop-boundary.md)。执行主控停下后，经构思主控向用户说明证据和最小选项；构思主控收到后用 `PushNotification` 提醒用户（规则见第 4 节通知）。

**权限三层**：

1. 结构底线：不暴露的工具就是没权限。worker 只有 `a2a_submit` 与 `a2a_raise`；门禁全套命令只开给执行主控；构思主控只读。Herdr 期靠"只放行派发包装"的权限规则建议（[T-054](../tickets/T-054-dispatch-wrapper-and-session-copy.md)，用户批准后应用）；Synara 期用能力预设。
2. 提示词与角色卡：每个角色一张短卡（`.project-map/roles/`）。worker 的卡由派发包装附带；两个主控每次用 `scripts/inbox list` 查收件箱时，脚本先把自己的卡再打印一遍，不靠模型记得。
3. 追加式记录：分发、修订、停止、处置、代改都有记录，可事后核对。

不做策略引擎，不做按路径或按 ticket 的权限。门禁本身是"同一用户下可信协作者的流程门禁，不是安全沙箱"（README），权限设计的目标是防漂移和防误操作。

**Synara 期的能力预设**（名字以 [T-058](../tickets/T-058-server-inbox-capabilities-wake.md) 的 RESULTS 为准）：

| 角色 | 能力 |
| --- | --- |
| 执行主控 | `a2a:operate`（门禁全套命令的 MCP 工具）、`a2a:inbox` |
| 构思主控 | `a2a:read`（只读门禁状态、事件、问题上报）、`a2a:inbox`、`a2a:stop`（窄：只中断，见第 5 节） |
| worker | `a2a_submit`、`a2a_raise` |
| reviewer / monitor | `a2a_raise` |

角色在 attach 或创建会话时用预设选择，不提供自由编辑权限的界面。写条目时的唤醒由服务端内部完成，两个主控不需要通用的 `thread:write`。

## 2. 共用记录（信封）

用户输入、问题上报、主控交接共用一套字段，只追加；已读、已处理、关闭、确认都是新记录，不改旧记录。

| 字段 | 含义 |
| --- | --- |
| `id` | 稳定、不依赖内容。Herdr 期是文件名主干 `<UTC 紧凑时间>-<from>-<kind>-<序号>`；服务端是随机 UUID |
| `kind` | 记录种类，见第 5 节 |
| `from` / `to` | `user`、`ideation`、`executor`、`worker:<名字或 thread id>`、`reviewer:<…>`、`monitor:<…>`、`system`；问题上报的 `to` 可以是虚拟地址 `triage` |
| `reply_to` | 它回答、确认或处置的那条记录的 id |
| `refs` | 带类型的引用：`ticket:`、`task:`、`attempt:`、`thread:`、`turn:`、`message:`、`request:`、`input:`、`issue:`、`file:`、`commit:` |
| `created_at` | ISO 8601，带时区偏移 |
| `body` | 正文，自由文本 |
| `schema` | 整数，现为 1 |

某条记录的"当前状态"从指向它的记录链推出，不存可变字段。用户输入另有自己的字段，见第 3 节。

## 3. 用户输入记录

**记什么**：用户本人的输入。主控、agent、自动化发出的提示词是派发记录，永不进用户输入记录。

**两层类型**：

- **形态**（客观，由渠道决定，不靠模型猜）：

  | form | 渠道 | 内容 |
  | --- | --- | --- |
  | `message` | 在任何会话里打的自由文本 | 文本 |
  | `answer` | 对 agent 提问的答复：Codex 异步提问、结构化提问、问题上报的答复 | 问题与答复，`reply_to` |
  | `approval` / `denial` | 权限批准或拒绝 | 请求 id、决定 |
  | `choice` | 在界面选了某个选项 | 选项 |
  | `action` | 界面操作：停止、中断、重试、归档 | 命令类型、目标 |

- **含义**（推断，事后追加标注，可多标签，不改原记录）：建议·改进、指令、纠正、偏好、补充信息、决定、验收、提问、其他。含义判断一律用意图识别，不写正则、关键词或模板规则。v1 不产生含义标注，也不做批量标注。标注是另外的追加记录（输入 id、标签、标注者、版本、时间），用户可覆盖。

**字段**：`id`、`form`、`text` 或结构化内容、`target`（`project`、`task`、`attempt`、`thread`、`turn`、`message`、`request`）、`channel`（`thread-message`、`ui-command`、`issue-panel`、`herdr-pane`、`controller-conversation`）、`reply_to`、`source_ref`（域事件 id 与序号，或原生会话文件与字节范围）、`certainty`、`created_at`、`schema`。

`certainty`：`observed` 是服务端在输入到达时依据权威事件或 RPC 入口记下的；`derived` 是事后按确定性规则从原生会话文件重建的；`relayed` 是主控从对话里逐字抄下的。

**关联**：只存稳定的键。后续结果——门禁事件、提交、验收——靠这些键关联，不存进输入记录。

**存放（Synara 期）**：工作台服务端新增追加式表 `user_inputs`，与门禁同库、同一写入入口，覆盖受管 attempt、attach 会话、普通会话、主控会话、界面操作；可导出 JSONL。

**与人工介入的关系**：`human_intervention` 保留，改为"落进受管 attempt 的那条用户输入"的派生事件，带 `input_id`，与输入记录在同一事务里写。界面标记与 AGENTS.md"受管 worker 里直接输入记为人工介入"的规则不变。

**fail-closed 范围**：只有受管 attempt 的输入记录失败时，才沿用现有行为——所有变更命令被拒。其余范围尽力记录：失败不阻断业务，恢复后由 Synara 事件日志重放补齐，补不齐的写一条 `form: gap` 的记录，标明序号范围与原因。重放不重复。

**观测点**：

1. 消息类输入沿用对域事件的订阅（`thread.message-sent` 且 `dispatchOrigin=user`），启动时重放。
2. 非消息类输入（审批、结构化回答、停止、中断、重试、归档）在 WS RPC `orchestration.dispatchCommand` 入口按枚举的命令类型记录。服务端内部、门禁、自动化和网关发出的命令不经此入口，因而不会被记成用户输入。不改命令契约。
3. 界面自己派生的命令（退出应用时的批量中断、临时线程清理）从入口记录时标 `channel: ui-derived`，不算用户的明确决定。
4. 如果发现界面有绕过该入口的路径，再提给核心加 `origin` 字段；不预先做。

**去重**：问题上报面板发出的答复在线程里是一条 `dispatchOrigin=user` 的消息。面板的发送接口在派发之前把 `message_id` 与 `bundle_id` 登记进门禁库；记录器遇到已登记的 `message_id` 不再记 `message` 输入，只为受管 attempt 生成指向这些 `answer` 输入的 `human_intervention`。

**Herdr 期**（日常派发改走工作台时停用）：

- 发给 worker 的每段文本经 `scripts/dispatch`：加标记 `⟦主控 #序号⟧`，对该 agent 在本批的第一条提示词附角色卡，把时间、目标、角色、全文和 Herdr 退出码追加进 `evidence/<批次>/dispatch.jsonl`。来源只认这个标记与日志，不对内容做模式匹配；包装被绕过时，来源降级为"用户或未知"，不会误标成主控。
- worker 回收前、批次结束时，`scripts/session-copy` 把 worker 的 Codex 原生会话文件和两个主控的 Claude 对话文件中上次复制之后新增的字节段复制进 `evidence/<批次>/sessions/`，写清单（会话 id、来源路径、起止字节、截止时间、大小）。只复制，不解析。副本不进 git，清单进 git。
- 用户在主控对话里说的话留在 Claude 原生会话文件里；构思主控写 `answer` 条目时逐字抄下用户的话，标 `certainty: relayed`。
- 抽取成输入记录等有消费者时再做；抽取时取全部人类消息（带偏移），不选"带决定的"，因为选择需要意图识别，应由消费端做。
- `scripts/inbox list` 在上次会话副本超过 7 天时打印一行提醒，提防默认保留期的清理。

**隐私与保留**：用户输入与问题上报只存本机，v1 不发往任何模型或远端，导出由用户或构思主控显式触发，是否提交由提交者判断。会话副本不进 git。记录永久保留、追加式、v1 无删除；原生会话副本留在批次证据目录，清理由用户手动。将来任何把输入发往模型或远端的消费者，必须先做脱敏，这是消费端的前置条件。

**使用**：v1 不跑任何自动分析。数据供：构思主控交接时逐字引用用户原话；事后复盘；将来 Enchanted 与改进分析（以后再说，前置条件是脱敏、权威的来源标记、记录不可变）。

## 4. 问题上报

**接口**：worker、reviewer、monitor 经 MCP 工具 `a2a_raise` 上报（Herdr 期用 `scripts/inbox send --kind issue`）：

| 参数 | 含义 |
| --- | --- |
| `title` | 标题，必填 |
| `body` | 正文，可空 |
| `blocking` | 默认否；真要等用户才能继续的才标 |
| `refs` | 可选引用，如文件与行号 |

返回会话内问题号（从 1 起）与 id。身份取自凭据，不取自参数；需要活跃 turn；不改变任何门禁业务状态。

**状态**（从记录链推出，不存可变字段）：

| 状态 | 条件 |
| --- | --- |
| 待判断 | 没有处置、未标 blocking、距上报不足判断期 |
| 等你决定 | 标 blocking；或最近一次处置是 `needs-user` 或 `reopen`；或没有处置且超过判断期 |
| 已转交 | 最近一次处置是 `forward`（交构思主控判断；判断期从转交时重新计） |
| 已关闭 | 最近一次处置是 `close` 或 `dismiss` |
| 稍后 | 最近一次处置是 `snooze` 且未到时间；到时回到"等你决定" |
| 已答复 | 有 `answer` 且尚无 `delivered` 处置 |
| 已送达 | 答复已送出（`delivered` 处置） |

判断期 15 分钟。超时按"无处置且超过判断期"在读取时派生，不需要写入者。

**处置动作**（`disposition` 记录的 `action`）：`close`（必须带理由与依据）、`needs-user`、`forward`、`reopen`、`snooze`（1 小时）、`dismiss`（仅用户）、`delivered`。

**判断规则**：

- 任务级由执行主控判；设计、目标、权限级由构思主控判；判不了的转"等你决定"。
- 可关的情形：不是问题、已解决、重复、已登记为后续工作。每次关闭追加一条处置记录，写明谁、理由、依据；原条目不删不改。
- 不许自行关，直接进"等你决定"：标 `blocking` 的；涉及权限、范围、验收条件、安全、不可逆操作的；明确问用户的选择题；主控自己拿不准的。服务端只强制其中 `blocking` 一项，其余靠角色卡，不做内容判断。
- 主控只能关闭，不能替用户回答。
- 关闭不单独起 turn：告知随提问会话的下一条消息一并送出，格式：`（另：你上报的问题 <n> 已被关闭，理由：<理由>。如不同意，请重新上报并补充证据。）`，只附一次。

**面板**：

- 每个会话一个，位于任务窗口里该会话旁；任务层另有汇总视图。
- 默认只显示"等你决定"；可切到"全部"和"已关闭"；关闭项显示理由与依据，可一键重开；blocking 置顶。
- 每题有回复框，草稿存本机（不进服务端记录），刷新或重启后还在，发送后清除。
- "稍后"：1 小时内不计入徽标与提醒，之后自动回来。"不处理"：用户自己的关闭处置（`dismiss`），进"已关闭"，可重开。
- 会话旁与项目侧栏有"等你决定"计数徽标。
- 外观由用户判断。

**发送**：已答多题时可选"逐个发送"（每题一条消息、一个 turn）或"打包发送"（每个会话一条消息）；已答 ≥2 题默认打包；未答的不参与。答复送给提问的会话；会话已结束则不送达，答复照记，并对执行主控产生一条 `forward`（理由 `session-ended`）。

**消息格式**（逐字，单条与打包同一格式；题间一个空行，无头无尾）：

```text
问题 <n>：<标题>
<正文>
用户答复：<答复>
```

- `<n>` 是该问题在会话内的编号，不是它在这一包里的位置。
- `<正文>` 最多 600 个字符，超出处以"…"结尾；正文为空时整行省略。
- 答复按输入原样发送，只去掉末尾空白。

例（预期串，供验收手写核对）：

```text
问题 1：oracle 漏了空页
分页夹具没有覆盖最后一页为空的情况。
用户答复：补上，并在 RESULTS 里写明。

问题 3：README 的构建命令已过期
用户答复：不用管，T-050 会重写。
```

**记录**：每条答复记为一条 `answer` 用户输入，`reply_to` 该问题；同一包共享 `bundle_id`，并记下送达消息的 id；逐个发送时每题各一条消息。

**通知**：

- Herdr 期：构思主控用 `PushNotification`（不超过 200 字，动作在前）通知：新的"等你决定"问题上报（同一批合并为一条）、blocking 的问题上报、完成报告、BLOCKED 或 NO_GO、需要用户在场的停止条件（登录、付款、系统授权）。不为常规进展通知。
- Synara 期：应用不在前台时，对 blocking 和新的"等你决定"发系统通知（同一批合并），不发声音，设置里可关。

**主控可见**：上报与处置都是追加记录，进门禁事件，执行主控轮询可见；需要用户的由构思主控列清单；完成报告里有计数与待决定项。

**Herdr 期**：同一协议，提示词加收件箱文件。worker 的角色卡要求"发现范围外的问题就用 `scripts/inbox send --kind issue` 上报，不自己决定忽略"；执行主控在轮询里看到就按上面的规则判断；转"等你决定"的由构思主控当面板，列清单给用户逐条答复，按上面的格式打包成一条 `answer` 写给执行主控，由执行主控经 `scripts/dispatch` 送回该 worker。Codex 自带的提问（`send_user_message`）照旧直达用户的 pane。

## 5. 主控交接协议

**就绪**：ticket 的额外字段。

| 字段 | 含义 |
| --- | --- |
| `ready: yes` | 已获执行授权 |
| `ready_by` | `ideation`（用户已决定的工作，验收条件写清，依赖已关闭，由构思主控标）或 `executor`（T-004 自主边界内的缺陷级后续，执行主控自建，建成即就绪） |
| `ready_rev` | 整数，每次修订加 1 |

可执行的 ticket 类型是 build、task、research；decide、compare、prototype 与用户一起解决，不由执行主控执行。`scripts/inbox ready` 列出满足下面全部条件的 ticket：`ready: yes`，三个字段齐全，类型可执行，`status: open`，无人认领，`blocked_by` 里每一项都是 closed 或 superseded。字段缺失的列为不合规，不算就绪。碰到 T-004 那几类（目标、范围、验收、权限、不可逆外部效果、方向取舍、预算与风险）一律不自标，发 `needs-decision`。

**冻结与修订**：标就绪后正文冻结。要改，构思主控改完把 `ready_rev` 加 1 并发 `revise`。执行主控在证据里记下自己依据的 `ready_rev`（交付绑定规格版本）；旧 rev 上进行中的 worker 由它决定继续还是重来。

**收件箱（Herdr 期）**：`.project-map/inbox/` 下一条一个文件，文件名 `<UTC 紧凑时间>-<from>-<kind>-<序号>.md`，用 `O_EXCL` 创建、原子写入。front matter 为 `id、from、to、kind、reply_to、refs、created_at、schema`，正文自由。只追加，不改不删。一条条目对某角色"未确认"，当且仅当没有 `kind: ack`、`from` 为该角色、`reply_to` 指向它的条目。

| kind | 方向 | 含义 |
| --- | --- | --- |
| `assign` | 构思 → 执行 | 本批就绪 ticket（`refs`）、交接说明、`## 授权` 一节 |
| `revise` | 构思 → 执行 | 某 ticket 改了，新的 `ready_rev` |
| `cancel` | 构思 → 执行 | 取消某些 ticket 或整批，写明原因 |
| `stop` | 用户/构思 → 执行 | 紧急停止，首行 `URGENT 停止 <目标>`，`refs` 指向 worker 或 attempt |
| `report` | 执行 → 构思 | 完成报告 |
| `needs-decision` | 执行 → 构思 | 需要用户抉择：问题、选项、证据、最小选择 |
| `issue` | worker/reviewer/monitor → `triage` | 问题上报 |
| `disposition` | 执行/构思/用户/系统 | 对某条 `issue` 的处置 |
| `answer` | 构思 → 执行（用户的答复，由构思主控逐字抄录） | 要投递给提问会话的原文，`refs` 带 issue 和 worker，带 `bundle_id`；执行主控投递后写 `delivered` 处置并 `ack` |
| `ack` | 任一方 → 发送方 | 确认收到或已执行，可附结果 |

**唤醒与发现**：

- 写完条目，发一条 Claude Code 跨会话消息唤醒对方，首行自成一句（含条目 id）；发 `assign` 时订阅对方"下次空闲"通知。空闲通知只是提示去查收件箱，不等于完成，完成以 `report` 为准。
- 对方在每个工作周期开头和停下之前，各运行一次 `scripts/inbox list --role <角色>`；不另加高频空轮询（额度紧）。
- 回复用收到消息的 `from`；寻址用 `ListAgents` 的会话名。建议把构思主控会话改名含"构思主控"，执行主控现名"A2A 客户端整体评估"可保留或改含"执行主控"。
- Synara 期同一字段进服务端，写条目时服务端内部唤醒目标角色的会话。

**完成报告**（`report`）的正文含：

1. 批次与时间范围。
2. 每个 ticket：状态（逐字 PASS、INCOMPLETE、BLOCKED 或 NO_GO）、证据链接、提交号、局限。
3. 问题上报：总数、已关闭数、等你决定的清单（id 与标题）、已答复未送达数。
4. 自建 ticket。
5. 待用户决定的事。
6. 这段时间用户的输入记录号。
7. 没做完的就绪 ticket 与原因。

构思主控转述时状态逐字，不上调，并用 `project_map.py status` 与 `scripts/inbox ready` 核对没有遗漏的就绪 ticket。执行主控只有在没有可执行的就绪 ticket 时才停；停下的原因不是"做完了"时（被阻塞、等用户决定），报告里要写明。

**授权引用**：对方消息只按队友请求处理，不算用户对待决提示的批准。`assign` 和 `revise` 里凡依赖用户授权的，须在 `## 授权` 一节逐字引用用户原话并给出位置（账本决定号、文档位置或输入记录号）。没有引用的，执行主控对 T-004 类动作按未授权处理，经构思主控问用户。

**紧急停止**：

1. 用户随时可以直接动手：Herdr 里停该 pane 或 Ctrl-C，工作台里点停止。不经任何主控。执行主控事后对账，记为用户的 `action`。
2. 用户对某个主控说"立刻停 X"：构思主控写 `stop` 条目并发跨会话消息（首行 `URGENT 停止 X`）；执行主控在下一个工具轮次执行并回 `ack`。用户对执行主控说，它直接做并告知构思主控。
3. 执行主控 2 分钟没回 `ack`，且用户仍要求：构思主控可以直接对该 worker 做"停止"——只中断当前 turn，不关 pane、不回收、不验收、不集成——并记录。Herdr 期用 `herdr agent send-keys <worker> esc`，Synara 期用 `a2a:stop`。授权来自用户当时那句话，不是常设权限。Synara 期服务端检查前置条件：存在发给执行主控、超过 2 分钟仍无 `ack` 的 `stop` 条目，目标是受管或 attach 的 worker 会话。

## 6. 两期实现与切换

| 项 | Herdr 期 | Synara 期 |
| --- | --- | --- |
| 主控会话 | 两个 Claude Code pane | 工作台常设"控制"任务里的两个角色会话（预设加角色卡） |
| 交接 | `.project-map/inbox/` 文件加 `scripts/inbox` | 服务端收件箱，MCP、HTTP、CLI 同一核心 |
| 唤醒 | Claude Code 跨会话消息 | 服务端内部唤醒（`synara_send_message` 的内部等价） |
| 派发 | `scripts/dispatch` 包装 `herdr agent prompt` | 门禁 dispatch，`dispatchOrigin=agent` |
| 用户输入 | 原生会话副本加派发日志，抽取以后做 | `user_inputs` 表，实时记录 |
| 问题上报 | worker 写 `issue` 条目，构思主控当面板 | `a2a_raise` 加任务窗口面板 |
| 权限 | 规则、角色卡、只放行包装的规则建议 | 能力预设 |
| 紧急停止 | 用户直接停；`stop` 条目；限时 break-glass | 停止按钮；`stop` 条目；`a2a:stop` |

**切换**：Herdr 期做法在日常派发改走工作台时停用——`.project-map/inbox/` 冻结为历史记录，不迁移，不双写；`scripts/inbox`、`scripts/dispatch`、`scripts/session-copy` 在切换 ticket 里删除；角色卡保留，改作预设会话的首条消息；`ready` 字段保留（地图是文件）。切换的时间点由用户判断，条件见第 7 节。

## 7. 切片、顺序与切换条件

| 代号 | ticket | 依赖 | 交付 |
| --- | --- | --- | --- |
| H1 | [T-053](../tickets/T-053-inbox-script-and-role-cards.md) | — | `scripts/inbox` |
| H2 | [T-054](../tickets/T-054-dispatch-wrapper-and-session-copy.md) | — | 派发包装、派发日志、会话副本 |
| S1 | [T-055](../tickets/T-055-issue-report-tracer-bullet.md) | — | 问题上报最薄一刀 |
| S2 | [T-056](../tickets/T-056-user-input-coverage.md) | S1 | 用户输入覆盖全部范围，观察器改名 |
| S3 | [T-057](../tickets/T-057-issue-panel-completion.md) | S1 | 面板完整化 |
| S4 | [T-058](../tickets/T-058-server-inbox-capabilities-wake.md) | S1 | 服务端收件箱、能力预设、唤醒 |
| S5 | [T-059](../tickets/T-059-controllers-in-workbench.md) | S2, S3, S4 | 两个主控进入工作台，端到端 |

- **顺序**（建议，执行主控可以更串行）：第一波 H1 与 S1 并行（H2 也不依赖它们）；第二波 H2 ∥ S2 ∥ S3，改同一文件的串行；第三波 S4；第四波 S5。额度紧，改同一批文件的 S2、S3、S4 同一时间只能有一个写入者。
- **里程碑**：H1 与 H2 完成后，Herdr 期这套就能日常用，不必等 Synara。S1 完成后，用户第一次在工作台里看到面板。
- **开工前重读**：S2～S5 开工前先对照已关闭切片的实际结果重读本 spec；发现不符，停下发 `needs-decision`，不绕开，也不改写本 spec（走新 ticket）。
- **切换条件**（用户的话："肯定要把我提的功能至少都做的能用了，我才能到 Synara 里用"）：S1～S5 全部 PASS，加用户亲自用一个真实小 ticket 跑通——两个主控在工作台里，面板里至少收发两条问题并打包发送一次——并说"可用"。之后构思主控才改 AGENTS.md 里"日常派发"那一条。

## 8. 默认值

| 名称 | 值 |
| --- | --- |
| 问题上报判断期 | 15 分钟 |
| "稍后" | 1 小时 |
| 答复消息里正文截断 | 600 字符 |
| `stop` 条目无 `ack` 后 break-glass | 2 分钟 |
| 会话副本提醒 | 7 天 |
| Herdr 期执行主控轮询 | 沿用现状，约每 60 秒 |

这些值是委托决定（见基线确认记录），试用后可调，改动走新 ticket。

## Test seam

- **Herdr 期**：真实命令行入口（`scripts/inbox`、`scripts/dispatch`、`scripts/session-copy`）加真实文件系统；对 `herdr` 使用明确标注为替身的命令，并在下一次真实派发中取得真实入口证据。
- **Synara 期**：真实服务端（隔离数据目录），经 MCP、HTTP、CLI 与 WS RPC；任务窗口的面板在 dev Chrome 里取证，Electron 可达时补；每个切片一次真实 Codex worker（隔离 `CODEX_HOME`，最少 turn）；S5 加两个真实 Claude 会话和用户亲自试用。
- 预期结果来自需求，不从实现输出复制；新测试须在已知坏实现（父修订、撤销修复、mutant）上失败；失败原样保留。

## Out of scope

- Enchanted 的并入、消费端、批量标注，以及含义标注的实现（用户："ENCHANTED 这个以后再说，批量标先不要"）。
- 修改门禁冻结契约（锁、fence、CAS、attempt 绑定、中断恢复）。
- 面板的视觉定稿（外观由用户在实现后判断）。
- 细粒度权限引擎。
- 决定日常派发何时改走工作台（由用户判断，条件见第 7 节）。
- 抽取原生会话成用户输入记录（等有消费者时再做）。
