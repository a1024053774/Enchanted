---
session_id: grilling-controller-split-user-input-20261009
status: confirmed
topic: 构思主控/执行主控拆分、用户输入数据化、问题上报面板
destination_artifact: 新的决定 ticket（从 T-049 起，写入时以目录为准）+ .project-map/specs/ 下一份 spec + 交给执行主控的就绪 build ticket；交接时同步 AGENTS.md、CONTEXT.md、intent.md 的角色表
created_at: 2026-10-09T02:46:57-04:00
updated_at: 2026-10-09T06:25:58-04:00
last_round: 5
---

> 指针状态：`.grilling/ACTIVE.md` 已于 2026-10-09 经用户同意（第 1 轮 Q5）改指向本会话。上一个会话 `synara-fork` 已 confirmed，账本原样保留。
>
> 术语更正：第 4 轮起“运行时主控”改称“执行主控”（Q13，D18）。本账本已把这个称呼统一改成“执行主控”，用户原话里的“运行时”保持原样。

## Destination

定下并写成文档三件事，不实现、不派发：A 把用户本人的输入落成数据；B 把主控拆成构思主控与执行主控两层；C 给干净上下文的 worker/reviewer 一个直达用户的问题上报接口、单独面板与批量答复，并让主控同样可见。确认后交接给执行主控：在地图里新增就绪的 ticket。

> "这次要拷问并定下两件事：A. 把"我（用户）的输入"落成数据。……B. 把主控拆成两层。"（任务书）
>
> "因为新开的 worker 也好，reviewer 也好，他们都是干净的上下文，有时会发现主控对话里发现不了的问题，这也是用干净上下文而不是子 Agent 的主要原因，这些我作为人工来说，有时这些信息夹杂在会话里我也发现不了，把这些留个接口出来？"（追加消息）
>
> "由于这些实在 worker 这些中发生的，所以主控也要能知道这些信息，这个也要设计好。"（追加消息）
>
> "构思主控是更上层的主控，负责分发任务，任务的监督由运行时执行，待全部完成停下来后再把内容返回给构思主控，然后我看构思主控就可以。"（第 1 轮 Q2 回答）
>
> "肯定要把我提的功能至少都做的能用了，我才能到 Synara 里用啊，目前都没做好，还放着延迟先不做，那我什么时候能用上"（第 3 轮回答）

背后的项目目标沿用 [intent.md](../intent.md)："让协作不依赖模型持续记住操作手册。"

## Out of scope

- 实现、派发、修改 fork 代码、触碰任何 worker 与 Herdr pane | reason: 本会话是构思主控的决策会话（任务书 C1）。例外：用户第 3 轮授权的那一条无操作测试消息（D16，已发）；用户第 4 轮授权的落地动作（D19）——写文档、提交我写的文件、发第一条 `assign` 并唤醒执行主控。
- Enchanted 的并入、消费端实现与批量标注 | reason: 用户第 1 轮 Q3："ENCHANTED 这个以后再说，批量标先不要"；M1 之后（[T-021](../.project-map/tickets/T-021-enchanted-freeze.md)、synara-fork D6）。本次只定生产端的数据合同。
- 修改门禁冻结契约（锁、fence、CAS、attempt 绑定、中断恢复） | reason: intent 约束"契约不变"；新增记录类型不得改变这些语义。
- 面板的视觉定稿 | reason: 外观由用户在实现后判断（intent、T-043 先例）。
- 细粒度权限引擎（按路径、按 ticket 的权限规则） | reason: 用户第 2 轮：权限"很难界定，也很难照顾全"；见 D13。

## Confirmed constraints

- C1 | confirmed | source: 任务书 | 本会话是构思主控（首次试行）：只与用户讨论并把决定落成文档；不派发，不碰任何 worker 与 Herdr pane，不改 fork 代码。
- C2 | confirmed | source: 任务书 | 结论写进 `.grilling` 账本和新的决定 ticket，需要时写 spec；确认后交接：在地图里新增就绪的 ticket，并在给用户的总结里写明。
- C3 | confirmed | source: 任务书 | 主控派发给 worker 的提示词必须和用户本人的输入分开记录。
- C4 | confirmed | source: 任务书 | 用户输入的来源至少包括：在 worker 会话里直接打字；回答 agent 的提问（如 Codex CLI 的 queued 提问）；批准或拒绝权限；界面操作；在主控对话里说的话；以后 Enchanted 的扫描建议。输入类型不止"建议和改进"，还有指令、纠正、回答、批准、偏好、补充信息等。
- C5 | confirmed | source: 追加消息 | 干净上下文的 worker/reviewer 会话（而非子 agent）能发现主控对话里看不到的问题，且夹在会话里用户自己也可能错过；因此发现要有一个直达用户的接口。
- C6 | confirmed | source: 追加消息；第 1 轮 Q4 | 每个 worker 一个问题面板；用户可逐个回复；问题多于 1 个时可选"逐个发送"或"打包发送"，打包格式"问题 1：……用户答复：……问题 2：……用户答复：……"。"逐个批量发送"按"逐个发送"理解，用户对该理解回"可"。
- C7 | confirmed | source: 追加消息 | 问题发生在 worker 中，主控也必须能知道。
- C8 | confirmed | source: 任务书 | 一轮最多 5 个问题；用中文讨论。
- C9 | confirmed | source: 第 1 轮 Q3 | 含义（意图）的判断一律用意图识别（模型判断），不写正则、关键词或模板规则，因为太复杂且效果不好。
- C10 | confirmed | source: 第 1 轮 Q3 | v1 不做批量标注；Enchanted 相关的消费与批量标注以后再说。
- C11 | confirmed | source: 第 1 轮 Q2 | 构思主控是上层主控，负责向执行主控分发任务；执行主控负责任务的监督；全部完成并停下后把内容返回构思主控；用户通常只看构思主控。用户不要再手动在两者之间粘贴 prompt 与想法。
- C12 | confirmed | source: 第 1 轮 Q2 | 两个主控之间用"分配权限"来设计，而不是互相禁止；取代第 1 轮推荐的"构思主控不能操作运行时"。
- C13 | confirmed | source: 第 3 轮 Q2、Q17 与末段 | 本次提出的功能（A 用户输入数据、B 两层主控与 Synara 里的权限映射、C 问题上报与面板）至少都做到能用，用户才会把日常使用挪到 Synara；这些功能不能搁置延后，Synara 面板和结构底线 ① 都要做，Herdr 期那边也要设计好。
- P1 | confirmed | priority | source: 第 1 轮 Q4 项 1，C5 vs D4 | 当"用户直接看到每条上报"与"主控判断后关闭非问题"冲突时，主控判断优先；但只能追加关闭记录、不删除，拿不准的留给用户。边界已定（D9）。
- 继承（不重述）：门禁契约不变、唯一门禁入口、人工介入记录（[intent.md](../intent.md) 约束）；不保留两套路径；重新证明；同一文件只分配给一个写入者；重大决策停下问用户（[AGENTS.md](../AGENTS.md)、[T-004](../.project-map/tickets/T-004-major-decision-stop-boundary.md)）；T-044 已定：attach 会话是"普通会话加角色"，无 submit、验收、集成权限；全局规则：状态只报 PASS/INCOMPLETE/BLOCKED/NO_GO，不上调；不为哈希而哈希；测试的预期来自需求，新测试须在已知坏实现上失败。

## Decisions so far

- D1 | confirmed | compare | origin: recommended | round 1 Q1 | 三类流动（用户输入、问题上报、主控交接）共用一个模型：每条记录有 from、to、kind、reply_to，只追加；已读、已处理、关闭也是新记录，不改旧记录；面板与两个主控的收件箱是同一批记录的视图。 | basis: C3, C5–C7 | assumes: 字段先定稳 | rejected: 三套各做各的（三处对账）
- D2 | confirmed | decide | origin: user | round 1 Q3 | 用户输入记录分两层：形态（由渠道决定，客观）= message / answer / approval·denial / choice / action；含义（推断）事后追加标注，可多标签，不改原记录；输入时不要求用户选类型；本记录只收用户本人的输入，主控、agent、自动化的提示词进派发记录。 | 用户补充：C9、C10 | assumes: v1 不产生含义标注（"接收的主控随手标"未单独问，默认不做） | rejected: (b) 输入时用户自选类型（打断、必漏标）；(c) 记录时由模型贴单层类型（事实与猜测混在一起）
- D3 | confirmed | decide | origin: recommended | round 1 Q4 项 2–5 | 问题上报：默认不阻塞（真阻塞标 blocking，置顶带徽标）；每个会话一个面板，每题有回复框（草稿自动保存）、稍后、不处理；已答多题可"逐个发送"（每题一条消息、一个 turn）或"打包发送"（每个会话一条，已答 ≥2 题默认打包，打包里带原问题）；答复送给提问的会话，会话已结束则转给执行主控处置；每条答复记为一条用户输入，reply_to 该问题。 | 与 Synara 原生异步提问格式并存（F3）
- D4 | confirmed | decide | origin: user（修改推荐） | round 1 Q4 项 1 | 主控可自行判断并关闭"不是问题"的上报：关闭是追加一条处置记录，不删除；拿不准的留在面板等用户决定。细则见 D9。
- D5 | confirmed | decide | origin: recommended | round 1 Q2 灰区 (i) | 执行主控遇到目标、验收、设计级问题：停下该 ticket，简短说明，投给构思主控展开，自己继续别的就绪 ticket，不在自己会话里 grill。说明经构思主控转给用户。
- D6 | confirmed | decide | origin: recommended | round 1 Q5 | `.grilling/ACTIVE.md` 改指向本会话（已执行）。
- D7 | confirmed | decide | origin: user（修改推荐） | round 2 Q2 灰区 (ii) | 执行主控发现新缺陷或后续工作：在已批准范围内（T-004 的自主边界）自己建 ticket 并执行，不逐项上报；只有需要用户抉择的才发构思主控；完成报告里列出自建 ticket。用户原话："不能太死，运行时发现需要我抉择的时候再发构思"。 | basis: T-004 | rejected: 推荐的"一律只上报、不自建 ticket"（太死）。
- D8 | confirmed | compare | origin: recommended | round 2 Q15 | Herdr 期构思主控与执行主控之间：收件箱文件（唯一事实）+ Claude Code 跨会话消息唤醒对方 + 订阅对方"下次空闲"通知来等完成报告，反向同理；不碰 Herdr pane；执行主控在每个动作边界也查收件箱兜底。 | assumes: U1 → 已由 D16 的测试证实（F20） | rejected: (b) 往 pane 注入文本（冒充用户输入、违反 C3、碰 pane）；(c) 只轮询（停下后不会醒）
- D9 | confirmed | decide | origin: recommended | round 2 Q16 | 问题上报的处置规则：新上报先进"待判断"；任务级由执行主控判，设计、目标、权限级由构思主控判；结果只有关闭（追加处置记录：谁、理由、依据）或转"等你决定"；主控超时没判断自动转"等你决定"（时长留给 spec）；面板默认只显示"等你决定"，"全部""已关闭"可切换，关闭项附理由、可一键重开；可关的情形：不是问题/已解决/重复/已登记为后续工作；不许自行关：标 blocking 的，涉及权限、范围、验收条件、安全、不可逆操作的，明确问用户的选择题，主控自己拿不准的；关闭随提问会话的下一条消息一并告知，不单独起 turn；只能关闭，不能替用户回答。 | basis: D4, P1, C5, R9
- D10 | confirmed | decide | origin: recommended | round 2 Q6 | 用户输入记录放工作台服务端新增的追加式表 `user_inputs`（与门禁同库、同一写入入口），覆盖受管 attempt、attach 会话、普通会话、主控会话、界面操作，可导出 JSONL 进仓库证据；`human_intervention` 保留，改为"落进受管 attempt 的那条用户输入"的派生事件，带 `input_id`，界面标记与 AGENTS 规则不变；fail-closed 只保留给受管 attempt 的输入，其余尽力记录、由 Synara 事件日志重放补齐、补不齐写 gap 记录；审批与结构化回答的来源标记点（服务端接收界面请求处盖章，或给命令加 `origin` 字段）留 spec。 | rejected: (b) 沿用 events 表（task 必填，要造假 task）；(c) 全放 a2a 仓库 JSONL（别的项目的输入不该进 a2a 仓库）
- D11 | confirmed | decide | origin: recommended | round 2 Q7 | 过渡期（Herdr 下）：执行主控发给 worker 的每段文本都走一个派发包装，自动加标记 `⟦主控 #序号⟧` 并追加进派发日志（时间、目标、全文）；worker 回收前、批次结束时，把该 worker 的原生会话文件和主控对话文件复制进该批证据（带会话 id、范围、截止点），不解析；抽取成输入记录等有消费者时再做；来源只认我们写入的标记与日志，不对内容做模式匹配；含义用意图识别（C9）。 | rejected: (a) 接受缺口；(c) 现在就写抽取脚本
- D12 | confirmed | decide | origin: recommended | round 3 Q8 | 交接：就绪是 ticket 的额外字段 `ready: yes`、`ready_by`（ideation 或 executor）、`ready_rev`（整数，每次修订加 1）；碰到 T-004 那几类一律不自标而发 `needs-decision`；标就绪后正文冻结，修订走 `revise` 并加 `ready_rev`，执行主控在证据里记下依据的 rev；收件箱 `.project-map/inbox/` 一条一个文件，字段 `id、from、to、kind、reply_to、refs`，只追加，确认也是新条目，种类 `assign、revise、cancel、stop、report、needs-decision、issue、disposition、answer、ack`；写完发跨会话消息唤醒，对方每个工作周期开头和停下之前各用小脚本列一次未确认条目；完成报告含每个 ticket 的逐字状态、证据、提交号、局限、问题上报及处置计数、自建 ticket、待用户决定的事、用户输入记录号、没做完的就绪 ticket；构思主控转述不上调，并用 `project_map.py status` 核对没有遗漏的就绪 ticket。 | basis: C11, D7, D8, F8
- D13 | confirmed | decide | origin: user（修改推荐） | round 3 Q2 | 权限三层、提示词为主：① 结构底线（不暴露的工具就是没权限；worker 只有 `a2a_submit`、`a2a_raise`，门禁全套只开给执行主控，构思主控只读）；② 提示词与角色卡（worker 的卡由派发包装自动附带；两个主控每次查收件箱时由脚本重新打印自己的卡）；③ 追加式记录。**用户改了推荐：① 也做，不是备用**，完善到差不多就把两个主控挪进 Synara。不做策略引擎，不做按路径或按 ticket 的权限。Synara 映射：执行主控 `a2a:operate`+`a2a:inbox`；构思主控 `a2a:read`+`a2a:inbox`；worker `a2a_submit`+`a2a_raise`；reviewer/monitor `a2a_raise`；角色用预设选。 | basis: I1, C11, C12, C13, F6, F19 | assumes: 能力名与工具名由 spec 定稿
- D14 | confirmed | compare | origin: recommended | round 3 Q9 | 紧急停止分层：用户随时直接动手（Herdr 里停该 pane 或 Ctrl-C，工作台里点停止），事后执行主控对账，记为用户的 `action`；对任一主控说"立刻停 X"，构思主控写 `stop` 条目并发跨会话消息（首行 `URGENT 停止 X`），执行主控在下一个工具轮次执行并回 `ack`，对执行主控说则它直接做并告知构思主控；执行主控 2 分钟没回 `ack` 且用户仍要求时，构思主控可直接对该 worker 做"停止"（只中断当前 turn，不关 pane、不回收、不验收、不集成）并记录，授权来自用户当时那句话，不是常设权限。 | rejected: (b) 无 break-glass；(c) 构思主控常设停止权
- D15 | confirmed | decide | origin: user | round 3 Q17 | 问题上报两条路都做：Herdr 期走"提示词加收件箱文件，构思主控当面板"（角色卡由派发包装附带；`issue` 条目由小脚本写；执行主控轮询判断；转"等你决定"的由构思主控列清单、用户逐条答复、构思主控按"问题 N：…用户答复：…"打包成 `answer`，经派发包装送回 worker；会话已结束交执行主控处置；Codex 自带提问照旧），日常派发改走工作台时停用；Synara 面板必须做，作为 tracer bullet。用户原话："肯定也要做啊，你不做的话我啥时候能挪到 synara 里用？只是目前还没挪，所以这边也要设计好啊"。 | rejected: (b) 不做等面板；(c) 让 Herdr 期 worker 经带范围的凭据上报（未采纳，未问细节，默认不做，漂移检查里确认）
- D16 | confirmed | decide | origin: user | round 3 Q18 | 授权构思主控向执行主控试发一条无操作确认消息，并确认执行主控是"A2A 客户端整体评估 [65a082]"。已发，已收到 ack（F20）。
- I1 | superseded by D13 | 用户第 2 轮倾向以提示词为主、不写死细粒度权限。
- D17 | confirmed | decide | origin: recommended | round 4 Q14 | 切片与顺序采纳：H1（T-053）、H2（T-054）、S1（T-055）、S2（T-056）、S3（T-057）、S4（T-058，含窄能力 `a2a:stop`）、S5（T-059）；第一波 H1 ∥ S1，第二波 H2 ∥ S2 ∥ S3，第三波 S4，第四波 S5（执行主控可更串行）；切换条件：S1–S5 全部 PASS，加用户亲自用一个真实小 ticket 跑通并说"可用"，之后构思主控才改 AGENTS.md 的"日常派发"那一条。 | basis: C13, D13, D14, D15 | assumes: 额度允许按波次推进；`a2a:stop` 的服务端前置条件能实现 | detail: spec 第 7 节
- D18 | confirmed | decide | origin: user（修改推荐） | round 4 Q13 | 术语表采纳，但把"运行时主控"改称"执行主控"；`human_input_observer`、`human_inputs`、`recordHumanInput` 等在 S2 里改名为 `user_input_*`；无前缀的"主控"在 2026-10-09 之前的文档里指执行主控。用户原话："改成执行主控吧 b 在 s2 改名"。 | rejected: 保留"运行时主控"并加定义；保留旧代码名只做对照 | detail: CONTEXT.md、T-056
- D19 | confirmed | decide | origin: user | round 4 Q19 | 落地全做，包括第 6 条：写 4 张决定 ticket、spec、基线确认记录、7 张就绪 build ticket、5 张角色卡；改 AGENTS.md、CONTEXT.md、intent.md 的角色表、MAP.md、README.md；提交我写的文件，不推送；手写第一条 `assign` 并唤醒执行主控。用户原话："Q19:全做，包括 6"。
- D20 | confirmed | decide | origin: delegated | round 4 | 通知：Herdr 期构思主控用 `PushNotification` 通知新的"等你决定"（合并）、blocking、完成报告、BLOCKED/NO_GO、需要用户在场的停止条件，不为常规进展通知；Synara 期应用不在前台时对 blocking 和新的"等你决定"发系统通知（合并），无声音，可关。 | detail: spec 第 4 节
- D21 | confirmed | decide | origin: delegated | round 4 | 隐私：用户输入与问题上报只存本机，v1 不发往模型或远端；导出显式触发；会话副本不进 git，清单进 git；消费端须先脱敏。 | detail: spec 第 3 节
- D22 | confirmed | decide | origin: delegated | round 4 | 保留：记录永久保留、追加式、v1 无删除；原生会话副本留批次证据目录，清理由用户手动；`scripts/inbox list` 在上次副本超过 7 天时提醒。
- D23 | confirmed | decide | origin: delegated | round 4 | 对话抽取：v1 只复制不抽取；将来取全部人类消息，带偏移，不选"带决定的"（选择需要意图识别，由消费端做）。
- D24 | confirmed | decide | origin: delegated | round 4 | 面板交互：草稿存本机；"稍后"1 小时；"不处理"是用户自己的 `dismiss`；已答 ≥2 题默认打包，未答的不参与。外观由用户判断。
- D25 | confirmed | decide | origin: delegated | round 4 | 来源标记点：非消息类输入在 WS RPC `dispatchCommand` 入口按枚举命令类型记录，不改命令契约；界面自动派生的命令标 `ui-derived`；发现绕过路径再提 `origin` 字段。 | basis: F22
- D26 | confirmed | decide | origin: delegated | round 4 | 判断期 15 分钟，按"无处置且超过判断期"在读取时派生，无需写入者；blocking 不进判断期。
- D27 | confirmed | decide | origin: delegated | round 4 | 面板答复去重：发送接口在派发前登记 `message_id` 与 `bundle_id`，记录器跳过已登记的。 | closes: R14
- D28 | confirmed | decide | origin: delegated | round 4 | 授权引用：`assign` 和 `revise` 里依赖用户授权的，须逐字引用用户原话并给位置；没有引用的，执行主控对 T-004 类动作按未授权处理。 | closes: R12
- D29 | confirmed | decide | origin: delegated | round 4 | 会话寻址：用 `ListAgents` 的会话名，回复用收到消息的 `from`；建议把构思主控会话改名含"构思主控"，执行主控现名保留。
- D30 | confirmed | decide | origin: delegated | round 4 | 处置动作集合：`close`、`needs-user`、`forward`、`reopen`、`snooze`、`dismiss`、`delivered`；状态名：待判断、等你决定、已转交、已关闭、稍后、已答复、已送达。
- D31 | confirmed | decide | origin: delegated | round 4 | 并行与额度：波次是建议；执行主控可串行；同一文件同一时间一个写入者。
- 注：D20–D32 已于 2026-10-09 经用户回复“同意”确认（整体同意），origin 仍记 delegated。
- D32 | confirmed | decide | origin: delegated | round 4 | 记录信封细节：字段、id 方案、文件名、`certainty` 与 `channel` 取值、会话内问题号、答复消息格式（正文截断 600 字符）、关闭告知的文字、可执行 ticket 类型（build、task、research）。 | detail: spec 第 2、4、5 节

## Facts

- F1 | observed | 2026-10-09，fork `a2a` 分支 `90e38b6`，`packages/a2a-gates/src/core.ts` `recordHumanInput` | 现有 `human_intervention` 只记"thread 属于某 attempt 且 `dispatchOrigin=user` 的 `thread.message-sent`"，写入门禁 `events` 表（`task` 必填），`human_inputs(event_id)` 去重；记录器失败时所有变更命令拒绝（`human_input_observer_failed`）。它按 `attempts` 查 thread，不查 `attachments`，所以用户对 reviewer/monitor 等 attach 会话说的话不会被记录。
- F2 | observed | fork `packages/contracts/src/orchestration.ts:1786-1802` | `thread.approval.respond`、`thread.user-input.respond` 是独立命令，不走 `thread.message-sent`，现有记录器不覆盖；界面操作（停止、中断等）同理（后者是推断：未逐个核对命令）。
- F3 | observed | fork `packages/contracts/src/asyncUserInput.ts`、`packages/shared/src/asyncUserInput.ts`、`apps/server/src/provider/Layers/CodexAdapter.ts:970` | Synara 已有"异步提问"：Codex 助手消息附 `questions: [{title, options?}]`，没有待回复的 RPC，用户答复是普通用户消息，格式为每题 `标题\n答复`、题间空行。
- F4 | observed | 2026-10-09，Codex rollout `…01a11ef0-808d-7613-b979-10e06dfd7aec.jsonl:103`（T-045 worker）；同日 T-044 worker rollout | Herdr 下 Codex 的 user 角色消息分三类：AGENTS.md 注入；主控派发（如"读并执行 …/brief-T-045.md"、"主控决定见 …"）；用户对 worker 提问的答复（包在 `<send_user_message_question_reply>` 里，内容 `[{answer, question}]`）。主控注入与人手输入没有来源字段可区分。
- F5 | observed | fork `service.ts:140,177` | Synara 里 dispatch/attach 投递的提示词 `dispatchOrigin: "agent"`；自动化为 `automation`；用户输入为 `user`。原生运行时里两者已可区分，Herdr 下不行。
- F6 | observed | fork `apps/server/src/agentGateway/toolRuntime.ts`、`Services/AgentGatewaySessionRegistry.ts` | MCP 能力在发凭据时固定（`issue(threadId, provider, {additionalCapabilities})`，授予或撤销会重启会话）；现有能力名 `thread:read/write`、`automation:write`、`diagnostics:read`、`browser/device/computer:control`；工具声明 `requiredCapability`，catalog 按能力过滤；`a2a_submit` 需 `thread:write` 加活跃 turn 并核对调用 thread。create/dispatch/attach 目前只有 CLI/HTTP（owner 凭据），T-044 明确"主控 MCP 工具等主控迁入 Synara 时再开放"。
- F7 | observed | [Enchanted spec §4](../../Enchanted/spec.md)、AGENTS.md | Enchanted 的证据模型 `origin ∈ {human, assistant, tool, system, injected, unknown}`，只有 human 支撑纠正信号；建议只能 Preview/Export，没有 Apply；效果主张需要 holdout。（消费端本次不做，见 Out of scope。）
- F8 | observed | `project_map.py` | ticket 的 `status` 只认 open/closed/superseded/out-of-scope，其余 frontmatter 键被忽略不报错；"就绪"只能是额外字段，不能是 status。MAP.md 预算 150 行。
- F9 | observed | 环境变量与 `evidence/2026-10-09-batch5/controller-poll.log`，2026-10-09 | 本会话（构思主控）运行在 Herdr pane `wF:p1A`；执行主控是另一个 Claude Code 会话（pane `wF:pM`），经 `herdr agent start …` 派发 Codex worker，约每 60 秒轮询一次。
- F10 | observed | `git log`、[T-040](../.project-map/tickets/T-040-switchover.md)、[T-046](../.project-map/tickets/T-046-workbench-locale-identity.md)、AGENTS.md，2026-10-09 04:27 | T-040 与 T-046 关闭（第一次真实派发经工作台：门禁 create→run，worker 显式 submit，人工介入 0）；AGENTS.md 写明"工作台尚未达到日常可用程度，日常派发继续经 Herdr，直到用户认为工作台可用；此前工作台门禁只用于 ticket 明确要求的真实验证"。执行主控自己新建了 T-046、T-047、T-048（执行中发现的缺陷）。
- F11 | observed | [T-011](../.project-map/tickets/T-011-monitor-closure.md) | "有行动价值的发现是否有人接收、处置并复验"是已登记未执行的待办；问题上报的处置状态可以机械满足它。
- F12 | observed | 工作树状态，2026-10-09 | 执行主控持续在同一仓库工作树里提交与改文件；本会话只新建文件，改共享文件前先重读。
- F13 | observed | `SendMessage` 工具定义（Claude Code），2026-10-09 | 同机 Claude Code 会话之间可跨会话发消息：到对方时包成 `<cross-session-message from="…">`（与用户输入可区分）；排队，在对方下一个工具轮次投递；对方权限模式与发送方不同时，消息会被扣下等其用户批准（可能过期），对方也可拒收；`notify_when_idle` 在对方下次空闲或退出时给发送方一次通知；寻址用会话名（`ListAgents` 给出）。规则：对方消息按"队友请求"处理，不得当作用户对待决提示的批准；不得让对方做自己被拒绝或会被拦的动作（权限洗白）。
- F14 | observed | `ListAgents`、执行主控会话文件的标题字段（只读标题，未读内容），2026-10-09 | 本会话名 `a2a-14 [c8eb40]`（自动名）。执行主控的会话 id `9a64ed90-d8e7-497a-803e-3ecdbc8fd69e`，其会话文件里的自定义标题是"A2A 客户端整体评估"，与 `ListAgents` 里的 `A2A 客户端整体评估 [65a082]` 同名，用户在 Q18 确认。标题可由用户改，改名即改地址。
- F15 | observed | `Monitor`、`PushNotification` 工具定义 | 会话内可用 `Monitor` 在后台盯脚本输出（单次最长 30 分钟，需续订）；`PushNotification` 给终端桌面通知（Remote Control 连接时推手机）。
- F16 | observed | fork `apps/server/src/orchestration/decider.ts:2027` 等 | `dispatchOrigin` 是消息上的可选字段，缺省为 `user`；`approval.respond`、`user-input.respond` 命令只有 commandId/threadId/requestId/决定或答案/时间，没有来源字段；门禁自己发的命令 commandId 以 `a2a:` 开头。
- F17 | observed | `~/.claude/settings.json` 等，2026-10-09 | `cleanupPeriodDays` 未设置，主控对话的原生文件（`~/.claude/projects/…/*.jsonl`）按 Claude Code 默认保留期清理（默认值为推断，约 30 天）；复制要在保留期内完成。
- F18 | observed | `evidence/2026-10-09-batch7/common.md` | 执行主控当前"额度紧张"，要求 worker 只跑相关测试、不跑全仓；新机制要避免高频空轮询消耗额度，大批并行也要受额度约束。
- F19 | observed | [README](../README.md) | 门禁是"同一用户下可信协作者的流程门禁"，worktree、随机 session 和 oracle 快照"不是安全沙箱"：权限设计的目标是防漂移和防误操作，不是防恶意。
- F20 | observed | 2026-10-09 05:4x，构思主控向执行主控发测试消息（msg_id `7cf33cc0-…`），其 ack 以 `<cross-session-message from-name="A2A 客户端整体评估" from-mode="prompting">` 回到本会话 | 投递成功，未被扣下，无人工批准环节；执行主控权限模式为 auto，收到时处于空闲、等待用户输入，消息唤醒了新 turn；它没改文件、没动 worker；当时无进行中的 worker，T-040～T-048 已关闭，在等就绪 ticket。回程方向（执行→构思）同样到达。未测：对方正在长工具调用时的延迟（文档称下一个工具轮次投递）、两端权限模式的其他组合。
- F21 | observed | fork `apps/server/src/agentGateway/Layers/AgentGateway.ts` | Synara 已有网关工具 `synara_create_thread(s)`、`synara_send_message`、`synara_interrupt_thread`、`synara_set_thread_*`、`synara_hub_*`：在 Synara 里唤醒另一个会话可用 `synara_send_message`，停止可用 `synara_interrupt_thread`；`a2a:inbox` 工具可在服务端内部完成"写条目并唤醒目标角色会话"，两个主控不必为此拥有通用的 `thread:write`。
- U1 | resolved by F20 | 跨会话消息在 auto 模式的执行主控与本会话之间可用，空闲会话会被唤醒。其余组合未测，留作实现期的观察项。
- F22 | observed | fork `apps/server/src/wsRpc.ts:1322`、`apps/web/src/components/chat/respondToThreadApproval.ts` 等 | 界面经 WS RPC `orchestration.dispatchCommand` 发审批、结构化回答、停止、中断；另有界面自动派生的停止与中断（`RunningChatsQuitCoordinator.tsx`、`useTemporaryThreadLifecycle.ts`）；服务端内部、门禁、自动化的命令不经此入口。
- F23 | observed | herdr skill 文档 | `herdr agent prompt <名字> "文本" [--wait]`；`herdr agent send-keys <名字> esc|ctrl+c`；`agent prompt` 遇到停在审批或提问界面的 agent 返回 `agent_blocked`。只读了文档，没执行。
- F24 | observed | `project_map.py status`，落地后 | 0 个 problems、0 个 stale living docs。README.md 第 7 行"首次日常派发由 T-040 的其余部分交付"已过期（非本次改动，已在第一条 assign 里转给执行主控）。

## Frontier

- （无。）

## Blocked

- （无。）

## Not yet specified

- （无。原有雾区已由委托决定 D20–D25 处理，或移入 Out of scope；含义标注、抽取、Enchanted 消费以后再说，见 Out of scope。）

## Risks and conflicts

- R1 | open（缓解见 D11） | owner: T-054 | affects: C4 | 过渡期缺口：Herdr 下 worker 的人手输入与主控注入的提示词在原生会话中不可区分（F4）。包装被绕过时来源降级为"用户或未知"，不会误标成主控；T-054 另给出只放行包装的权限规则建议，待用户批准。
- R2 | resolved | affects: C2 | 并发写：落地只提交我写的文件；`acceptance/workbench_identity_oracle.py` 的未提交修改不是我的，已转给执行主控。
- R4 | open（缓解） | owner: 两个主控 | affects: C11 | 执行主控是长会话，可能忘记规则或没做完就停（F01 类）；缓解：脚本每次重新打印角色卡，完成报告后构思主控用 `project_map.py status` 与 `scripts/inbox ready` 核对。
- R5 | resolved by D18 | 术语冲突随改称"执行主控"消失；无前缀"主控"的归属已写进 CONTEXT.md。
- R9 | mitigated by D9 | affects: C5, D4 | 主控判断后关闭上报有误关真问题的风险；靠关闭可见、可重开、通知提问会话、几类不许自行关来约束。"不许自行关"里除 blocking 外的类别需要语义判断，无法机械强制，靠提示词加可见性兜底（C9）。
- R10 | resolved by D12 | "就绪"拆成两种授权来源（构思主控标的；执行主控在 T-004 自主边界内自建的）。
- R11 | mitigated by D13 | "靠提示词"与核心目标"不依赖模型持续记住"的张力：角色卡由脚本重新打印、追加式记录、结构底线 ① 三层缓解。
- R12 | resolved by D28 | 委托不等于用户批准：授权须逐字引用。
- R13 | open | owner: 执行主控 | affects: C13 | 额度（F18）与并行度：T-053～T-059 体量不小，执行主控可能要串行，这影响"何时能用"。
- R14 | mitigated by D27 | owner: T-055 | 重复计数：面板发送接口在派发前登记 `message_id`，记录器跳过已登记的；T-055 要有"同一答复只产生一组记录"的验收。
- R15 | resolved | owner: 用户 | affects: D20–D32 | 委托决定用户当时没有逐条看过；用户随后回复“同意”（整体同意，非逐条），见基线确认记录的补记。理由与推翻成本仍有效，可随时推翻。
- R16 | resolved | owner: 用户 | affects: D8, D29 | 本会话（构思主控）原名是自动名 `a2a-14`；用户已改名为 `a2a-构思主控`（2026-10-09）。

## Handoff

已确认。依据：用户第 4 轮的答复"Q14:采纳""Q13: 改成执行主控吧 b 在 s2 改名""Q19:全做，包括 6"，以及"现在未决定的部分也来决定一下，然后这个漂移检查也落成文档"。用户没有逐字回复"确认"；委托决定 D20–D32 用户当时没有逐条看过（R15）；之后用户回复“同意”（整体同意，非逐条），见基线确认记录的补记。

正本（canonical artifact）：

- [spec](../.project-map/specs/controller-split-user-input-2026-10-09.md)：数据模型、状态机、格式、权限表、两期实现、切片与切换条件。
- [基线确认记录](../.project-map/specs/controller-split-user-input-baseline-2026-10-09.md)：漂移检查落成的文档——用户自己定的、照推荐采纳的（带假设）、委托决定（带理由与推翻成本）。
- 决定 ticket [T-049](../.project-map/tickets/T-049-controller-roles-and-permissions.md)～[T-052](../.project-map/tickets/T-052-controller-handoff-protocol.md)（已关闭）。
- 就绪 build ticket [T-053](../.project-map/tickets/T-053-inbox-script-and-role-cards.md)～[T-059](../.project-map/tickets/T-059-controllers-in-workbench.md)（`ready_by: ideation`，`ready_rev: 1`）。
- 同步更新：AGENTS.md（新增"构思主控与执行主控"一节、切换条件、停下并问用户的路径）、CONTEXT.md（术语）、intent.md（角色表）、MAP.md（决定索引、spec 链接）、README.md（一行入口）。
- 角色卡 5 张：`.project-map/roles/`。第一条 `assign`：`.project-map/inbox/20261009T102412Z-ideation-assign-001.md`。

下一步与负责人：

- 执行主控按第一条 `assign` 执行 T-053～T-059（波次见 spec 第 7 节）；没有可执行的就绪 ticket 时才停，写 `report` 并唤醒构思主控。
- 构思主控（本会话或之后的会话）收到 `report` 或 `needs-decision` 后转述给用户，状态逐字；每次开工先看 `.project-map/inbox/`。
- 用户：复核 D20–D32；给构思主控会话改名含"构思主控"；T-054 完成后批准或拒绝权限规则建议；全部切片完成后亲自试用，并判断是否"可用"。

限制：所有实现尚未开始；跨会话消息只测了"构思 → 执行（auto 模式、空闲）"和回程；"执行主控正在长工具调用时的延迟"和其他权限模式组合未测；委托决定已由用户整体同意，但不是逐条确认。本账本不记录实现进度。

## Changelog

- Round 0（2026-10-09）：读 AGENTS、CONTEXT、intent、MAP、ACTIVE、synara-fork、T-037 的人工介入设计、T-021、T-023、T-040、T-044、Enchanted 的 AGENTS/spec；核实 F1–F12；建账本；提出 Q1–Q5。
- Round 1 答复（2026-10-09）：Q1 选 A（D1）。Q2 用户否掉"构思主控不能操作运行时"，改为上下级与分配权限（C11、C12），灰区 (i) 通过（D5），(ii)(iii) 交我按此设计，整体 Q2 回到 frontier。Q3 选 A 并加条件（D2、C9、C10）。Q4 项 1 改为主控可判断并关闭（D4、P1），项 2–5 通过（D3）。Q5 同意（D6），已改 ACTIVE.md。
- Round 2（2026-10-09，用量重置后）：重读账本；核对停顿期间仓库变化（F10）；核实 F13–F18；合并原 Q11 进 Q16；原 Q12 因"Enchanted 以后再说"移入 fog；提出 Q2（修订）、Q15、Q16、Q6、Q7。
- Round 2 答复：Q15 选 a（D8）、Q16 全部采纳（D9）、Q6 选 a（D10）、Q7 选 b（D11）。Q2 灰区 (ii) 改为"不能太死"（D7）；用户对权限写死提出疑问并要我权衡（I1）。
- Round 3：核实执行主控的会话标题（F14）；Q10 并入 Q2；新增 Q17、Q18；提出 Q2（第三版）、Q8、Q17、Q9、Q18。
- Round 3 答复：Q2 采纳三层且 ① 也做（D13、C13），Q8 采纳（D12），Q17 两条路都做（D15），Q9 选 A（D14），Q18 确认（D16）。用户补充切换条件（C13）。已发测试消息并收到 ack（F20，U1 已解）。
- Round 4：核实 F21（Synara 网关已有 send_message、interrupt_thread，a2a:inbox 可在服务端内部唤醒）；把 R3 并入 D10、R6–R8 并入 D16/F20、新增 R12–R14；提出 Q13、Q14、Q19，并在同一条消息里给出漂移检查与最终确认。
- Round 4 答复（2026-10-09）：Q14 采纳（D17）；Q13 改称"执行主控"并在 S2 改名（D18）；Q19 全做含第 6 条（D19）；用户要求把未决定的部分决定下来（D20–D32，origin: delegated）并把漂移检查落成文档。
- 落地（2026-10-09）：写 T-049～T-052（已关闭）、T-053～T-059（就绪）、spec、基线确认记录、5 张角色卡；改 AGENTS.md、CONTEXT.md、intent.md、MAP.md、README.md；`project_map.py status` 0 problems / 0 stale；账本标 confirmed。
- Round 5 答复（2026-10-09，落地之后）：用户回复“需要我做的：1.同意 2.已改名 3.还 没看到 504 在执行”。D20–D32 经用户同意（R15 关闭）；构思主控会话已改名 `a2a-构思主控`（R16 关闭）；T-054 尚未开工，按计划在第二波（“504”按 T-054 理解）。
- 落地之后（2026-10-09）：用户授权构思主控自行提交自己写的文件（回复“可以”）：只提交自己写的，不推送，不碰别人的未提交修改；已写进角色卡 `.project-map/roles/ideation.md`。同日用户对 T-055 的 `a2a_raise` 免确认选 A，并让构思主控开 T-060；记录在 inbox 的 revise-001 与 T-055、T-060，不属于本会话的决定。
- 落地之后（2026-10-10 UTC）：用户回复“062选B，两条范围外的界面问题都做，三条block我同意，057通知我建议走软件内通知，需要我接管的通知另外走系统。同意推送，权限规则放在用户级设置，默认按我说的来，然后设置里也可以自己选。”构思主控：T-062 revise 到 ready_rev 2；开 T-063；替用户记三条 blocking 与两条界面 issue 的 close；授权执行主控推送；把 T-054 的权限建议合并进用户级 `~/.claude/settings.json`。T-057 的通知新设计待两点答复后再 revise。均为执行期决定，不属于本会话的决定。
- 纠正（2026-10-09）：用户指出“权限规则放在用户级设置”指 Synara 软件层面，不是 Claude Code / Codex。构思主控误把 T-054 的权限建议合并进 `~/.claude/settings.json`，导致用户其他项目（sitecraft-ai 的任务主控）的 herdr 命令被拒；已删除该段并告知执行主控。T-054 建议文件不再应用到任何 Claude Code / Codex 配置。同时用户对 T-057 真实系统通知选 A。
