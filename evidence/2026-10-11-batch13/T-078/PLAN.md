# T-078-1 实施计划（待执行主控审阅）

日期：2026-10-11。状态：**INCOMPLETE**，本次仅交计划，尚未实现或运行产品验收。

- 任务：T-078-1；ticket T-078，`ready_rev: 1`；派发：当前会话 `⟦主控 #19⟧`。
- worker：`s13-t078`；分支：`exec/t078`；唯一工作目录：`/Users/luckye/Documents/Code/a2a-wt-t078`。
- 起点：`14b57d22a84bcaebfa91c5051b9909b53a570fac`，读取时工作树干净。读取到的 `main` 已为 `2359a6f571d2e50b7d288a095472c85854217d72`；本轮不变基，不把这个读数当作最终集成基线。
- 规范：[T-078](../../../.project-map/tickets/T-078-controllers-in-workbench.md)、[第三阶段 spec](../../../.project-map/specs/native-cli-orchestration-2026-10-10.md) 第 5、6、9 节，沿用 [T-050](../../../.project-map/tickets/T-050-user-input-records.md)、[T-052](../../../.project-map/tickets/T-052-controller-handoff-protocol.md) 的语义与 T-074 rev 4 的决定。
- 使用技能：project-map、reality-first-engineering、evidence-first-testing、document-writing。此文件是本卡的日期记录，不建立第二套项目地图。

## 目标、边界与事实门槛

**目标**：在既有后台、门禁与 Electron 路径中接通交互输入、来源记录、主控排队与放行、库版收件箱及有凭据的紧急中断；补主控启动记录的骨架。完成条件逐项沿用 ticket，真实 Claude 验证留待另一张卡。

**非目标**：真实 Claude/Codex 模型回合、日常文件版 `scripts/inbox` 的替换、S5 面板通知、T-076 质量串、T-077 worktree 生命周期、全局配置或正式工作台数据。不会修改 `scripts/`、`acceptance/test_*.py` 断言、spec、地图或其他 ticket。

**REALITY GATE: INCOMPLETE**。代码层的实施位置已核对；终端输入来源、Claude hook 时序与夹具运行授权尚不构成通过证据。计划获准后按下面的探针顺序推进，每个行为先取得红态，再改产品。

| 状态 | 已核对事实或未知 | 依据及影响 |
| --- | --- | --- |
| observed | Electron 只读，只有 snapshot/output IPC，xterm `disableStdin: true` | `workbench/app/{renderer.tsx,preload.ts,main.ts}`；需增加窄输入接口 |
| observed | Panes 只有单个 Codex worker；已有登记、bracketed paste、300 ms 间隔、单独 CR、Stop 处理和首次 release | `workbench/src/panes.ts`；沿原路径扩展，不另起终端后台 |
| observed | SQLite 已有 `user_inputs`、`inbox_records`、`inbox_deliveries` 及禁止 UPDATE/DELETE 的触发器 | `workbench/src/gates/core.ts`；复用，不另建一套收件箱库 |
| observed | 后台没有 `wakeThread`、`interruptThread` 实现；无凭据的 inbox 调用可采用参数角色，stop 可走无 caller 分支 | `daemon.ts`、`panes.ts`、`gates/core.ts`；本卡要把凭据解析接到这些入口 |
| observed | xterm 6.0.0 的公开 `onData` 只有字符串；内部键盘/IME 与自动应答都能触发它 | 本地依赖 `typings/xterm.d.ts`、`src/common/services/CoreService.ts`、`src/browser/input/CompositionHelper.ts`；不能把所有 onData 当人类输入 |
| measured（历史，非本卡验收） | T-074 rev 4 证明了两家 CR 即忙、正常 Stop、Esc 后放行的样本 | T-074 的 RESULTS、`rev4-host.cjs`、Claude `turn-hooks.jsonl`；不外推到本产品、重启或任意竞态 |
| observed | Claude 历史 Stop 有 `session_id`、`prompt_id`，没有 Codex 的 `turn_id`；开始事件的标识不可靠 | T-074 rev 3/4；不能直接复用 Codex 的 active.nativeTurn 匹配 |
| unknown | 固定版本 xterm 的可用公共事件能否完整区分键盘、IME、粘贴和设备应答 | 探针 P1，过不了就报告，不接私有字段或猜文本来源 |
| unknown | Claude 主控的真实 hook 与本地假服务组合在本卡环境中的时序 | 探针 P2；用户答复 needs-decision `20261011T101958Z-executor-needs-decision-001` 前不运行 |

**Ubiquitous language**：沿用“用户输入”“派发记录”“人工介入”“受管运行身份”“原生会话”；不把注入叫用户输入，不把 PTY 写成功叫 CLI 已处理。**Deep modules**：Panes 负责输入顺序与终端生命周期，门禁负责记录及权限事实，Electron 只做输入与显示；只在实际需要的边界增加接口。

## 1. 输入通路与来源

通路：Electron 的键盘／粘贴／组合输入 → preload 的限定方法 → main 校验窗口及固定 launch → 同一个后台 socket → 后台解析凭据、登记输入、串行写入 → node-pty。所有 PTY 写入（用户、注入、设备应答、Esc）都经过 Panes 中一个写入边界，不能在 renderer 或新客户端直接写终端。

1. Electron main 持有界面连接凭据，renderer 不能提交 actor、role、attempt 或任意文件路径。每条输入绑定固定的 project/task/thread/launch 与后台代次；current_attempt 变化不得把旧窗口的键送到新 worker。
2. 用户输入使用连接号与递增序号／请求号；后台按入口和凭据确定来源。原始 UTF-8 数据、输入片段顺序、控制动作、写入意图与结果追加保存。内容中即使有 `⟦主控 #…⟧` 也仍是用户输入，不能靠标记字符串抹掉它。
3. 文本为 `message`，显式放行、中断为 `action`；只按输入渠道区分，不用关键词判断含义，不从 Enter 猜测批准/拒绝。箭头、退格、组合态不冒充最终消息正文；保留原始输入片段与引用，只有能核对来源的提交才能形成相应消息记录。
4. 用户输入调用既有 `appendUserInput`；落入受管 attempt 时，同一事务产生带 `input_id` 的 `human_intervention`。主控 attach 的 attempt 为空，不因同属一个任务而误记为 worker 介入。受管输入登记失败时不写 PTY，并维持门禁原有拒绝语义；其他会话按 T-050 尽力记录，失败保留原始事件，恢复时补齐或记 gap，不能伪造成功。
5. 注入先写 `dispatch_records`，固定 dispatch id 与准确文本，再写 bracketed paste 和单独 CR；它不经过用户输入入口。注入的原生记录如另被采集，只按已登记写入的来源引用去重，不用文本相等、前缀或时间邻近猜来源。
6. 设备查询应答保持后台所有权。P1 先证明启用输入后 xterm 不会把自动应答计为用户输入，也不会让前后台重复回设备查询。只用已核对的公开输入／parser API；若必须改依赖或使用私有内部接口，先交执行主控决定。

P1：在隔离 Electron/xterm 中分别产生真实键盘事件、中文 composition、粘贴和设备查询，观察源事件、IPC、后台输入记录与 PTY 接收字节。通过条件是四者来源分清、数据完整且不重复；任何来源不明或设备应答混入用户表即失败。执行者为本 worker，沙箱外部分交主控执行，证据落 `T-078/<run>/input-origin/`。当前只写方案，不运行。

## 2. 主控窗格的启动、忙闲与排队

通过现有 attach 入口建立 `role=controller`、preset 分别为 ideation/executor 的两个会话，与 worker 同属一个任务。主控不制造假的 worker attempt；放宽单 worker 限制时只允许本票所需的两个 controller attach，不顺带开发通用多 worker 调度。

`launch_records.attempt` 当前为 NOT NULL，而 controller attach 没有受管 attempt。实施前先取“保留旧 worker 启动记录，同时允许主控自然空值”的存储红态；以局部 schema 迁移保留旧行与追加式约束，不用空字符串或虚构 attempt 绕过。迁移失败原样保留、停止，不自动重建数据库。

启动记录新增 Claude 分支，保存完整 argv、CLI 版本、预先生成的原生 session UUID、模型与强度请求、`--settings` 实际内容、角色卡正文／版本、项目提交和路径。argv 明确包含 `--session-id`、`--model`、`--effort`、`--settings`；hooks 与权限只从这次启动传入，启动凭据不进 argv 记录、日志或截图。角色卡经有登记的注入送入。CLI 退出后仍保留 zsh；`model_requested` 不冒充实际模型。认证隔离的具体启动仍受第 7 节的用户决定约束。

| 状态或事件 | 后台行为 |
| --- | --- |
| 新建、重启恢复、输入／hook 结果无法核对 | unknown，队列不自动放出；历史 PTY 不自动接管 |
| 初次就绪 | 延续明确的首次放行入口；首次启动管理动作与用户 Esc 后的放行分开记录，不能伪记用户 |
| idle、无用户草稿、无写入进行中 | 允许队首注入；同一窗格只有一个写入序列 |
| 用户开始打字／composition，尚未提交 | 持有输入占用，禁止自动文本混入草稿；不猜测退格之后是否已空，明确提交或用户确认清空／放行才释放 |
| 写入提交 CR | 在可发生下一次调度之前登记提交并记 busy；包括用户输入；粘贴内部换行不能当提交 |
| UserPromptSubmit | 保存结构化事实，不用于从 idle 推 busy，不依赖它的标识 |
| 有效 Stop | 只结束所属的一个未完成提交，再按队列顺序注入；重复或过期 Stop 不解锁新提交 |
| 主控 PermissionRequest | 记录等待，仍 busy，禁止注入；不等待不存在的“批准结束”信号 |
| Esc | 写中断字节、保留 busy 与“须用户放行”状态；即使出现迟到 Stop 也不自动排空 |
| 用户放行 | 经界面凭据记 action，绑定目标及待放行提交，清除相应占用，尝试一个队首；这次 CR 随即又 busy |

注入从 paste 到 CR 作为一个不可交错的操作；现有 300 ms 间隔期间到来的用户数据必须保留顺序，不能直接穿插。注入开始前已经存在的人工草稿使注入排队。用户输入、Stop、放行与第二条注入的交错将用显式屏障复现，不靠随机 sleep 碰运气。Esc 必须能阻止尚未写出的注入 CR；部分 paste 已进入 CLI 的情况记未完成、等待明确人工处置，不自动补回车或重试。

Claude 与 Codex 共用后台提交状态，原生身份读取保持两家各自的明确分支。Codex 继续保留会话、领导进程及回合核对，不为加 Claude 放松它。Claude 以固定 session、hook 来源、后台提交序列和单次消费记录核对 Stop；不编造 `turn_id`。迟到 Stop 无法唯一归属时保留 busy/unknown 并上报，这个边界要由 P2 验证，不能仅用接收时间较晚推出可放行。

唤醒来自已保存的收件箱条目，带主控标记和 entry id。库中的 pending/queued/写入完成/unknown 要区分：busy 时接收排队不能提前称 delivered。每条 entry 对固定目标只登记一次 dispatch；记录已有写入意图但结果不明时不自动补发。

## 3. 收件箱库表、后台客户端与权限

复用门禁的 `inbox_records` 与 `inbox_deliveries`，保留追加式触发器、单条操作锁和 ack 幂等处理。用户输入复用 `user_inputs`；启动、排队和终端写入复用 `launch_records`、`dispatch_records`、`orchestration_events`。必要的请求幂等键／投递关联随追加记录保存，不另建可变“收件箱状态”。历史状态仍由记录链推出。

新增 `workbench/bin/inbox`：只解析参数、读 body 文件并调用同一后台。支持 send、list、ack、ready；提供 refs、reply_to 等既有语义。客户端不打开 SQLite，不读取／写入文件版 inbox，也不导入本仓库的日常条目。测试强制显式指定夹具 state/project；不落到默认正式数据目录。

`ready` 按原 spec 第 5 节读取后台已绑定的夹具仓库 `.project-map/tickets/`，返回 ready=yes、字段齐全、类型 build/task/research、open、无人认领、依赖 closed/superseded 的 ticket；缺字段、重复 id、无效 rev 报不合规。它是只读 ticket 查询，不把 ticket 正文或 ready 事实复制成第二套库状态，不改 `scripts/inbox`。

| 认证后的角色 | 本卡所需写权限 |
| --- | --- |
| ideation | assign/revise/cancel/stop → executor；按既有约束处置问题／转述 answer；ack 自己收到的条目 |
| executor | report/needs-decision → ideation；按既有约束处置问题；ack 自己收到的条目；执行受管任务操作仍经门禁 |
| worker/reviewer/monitor | issue → triage，地址绑定自己的 thread；ack 仅本人收到的条目；不能写 assign/report 或冒充主控 |
| user | 由界面凭据产生用户动作、stop 和既有用户处置；不能由普通角色参数取得 |
| system/triage | system 只作后台内部来源；triage 是路由目标，均不是客户端可自领的身份 |

新权限限制落在已有角色及门禁方向检查处，不增加可配置策略引擎。`--from`／`--role` 若为沿用命令格式而存在，也不能选择实际调用者；冲突参数在权限判断前被实际凭据覆盖或拒绝，审计中 actor 总是实际角色。`list` 的读范围由凭据限制；`ready` 不允许任意绝对路径越过已绑定项目。

## 4. 紧急停止与凭据来源

后台为每个 launch 签发随机会话凭据，绑定 role/preset、project/task/thread、launch、后台代次与有效生命周期。各 CLI 仅在本会话环境中得到自己的凭据；Electron main 得到独立的用户连接凭据，preload/renderer 看不到它。凭据签发通过后台启动者的受控初始化通道完成，不能提供无认证“领取 ideation/user 凭据”的 socket 命令。重启后旧凭据失效。

`daemon.ts` 在调用门禁前解析实际 caller；既有 worker token 路径纳入同一校验。普通输入、inbox、release、interrupt 不接受无凭据降级成 user/executor；既有管理 CLI 的必要调用绑定启动者凭据，测试适配器也显式传递这个事实，不通过改业务断言保留匿名放行。参数和 `A2A_ROLE` 本身都不构成凭据。这里保证应用内来源；不宣称能对抗任意读取同一用户进程内存／环境的 OS 级对手。

1. 正常流程：构思主控按用户原话写 stop（引用 `input:<id>` 及固定 thread/attempt），保存条目后唤醒执行主控。执行主控在下一个工具轮次经同一门禁中断目标，然后回 ack；不能由系统伪造执行主控已读取／已执行。
2. 执行主控收到用户直接停止指令也走凭据及固定目标校验，记录真实 executor 和授权输入引用。用户直接操作由 user 连接记 action。不中断同任务的其他会话。
3. 超过 120,000 ms、没有执行主控 ack、且用户仍要求时，ideation 可调用窄 stop 接口；既有 `> 120_000` 边界保留。用户仍要求是当次授权条件，保存其输入引用，由主控判断，不用正文关键词自动推出，也不设置两分钟后自动中断的定时器。
4. 门禁核对 stop 条目、调用角色、目标归属、生命周期、前台进程身份、task/attempt 绑定；在原 task 锁和 inbox 锁内重新查 ack，避免检查后出现 ack 的竞态。运行时只向核对后的 PTY 写 Esc 中断当前回合，既不关窗格、不 kill shell，也不 reclaim/verify/integrate。
5. 记录 `interrupt_intent` 与写入结果，保存 actor、调用 launch、stop id、授权输入和目标。写入结果不明保留 unknown，不重试；实际退出／中断证据单列，不能把请求成功当回合已结束。

反例必须覆盖：无凭据、坏 token、过期 launch、worker 伪造 ideation 参数、ideation 伪造 user 参数、提前停止、已有 ack、目标不符、原 attempt 被替换、ack/stop 竞争。正确 ideation 凭据带假 actor 参数时，停止记录仍为 ideation；错误角色即使参数正确也无 PTY 字节。

## 5. ticket 失败方式逐条处理

| 失败方式 | 处理与独立观察 |
| --- | --- |
| 用户与注入同时输入 | 单窗格串行写入；人工草稿占用；paste/CR 期间屏障。观察 PTY 原始接收顺序、用户表、dispatch 和介入引用，三者不得混写或漏写 |
| 中文输入法组合输入 | 沿 xterm 原生组合输入，不把 keydown 拼为文本；观察 compositionstart/update/end、最终 IPC 与 UTF-8 字节；合成事件仅证明代码路径，真实 macOS 输入法未实测时明确 INCOMPLETE |
| 粘贴大段文字 | 保留中文、多行、标记字符；bracketed paste 内换行不启动多个提交。覆盖接近传输上限与超限，必须完整接受或在写入前明确拒绝，不能截断；不把拆块当多条用户消息 |
| 窗口关闭期间输入 | 关闭只结束视图；后台继续运行和排队。关闭前已接收的请求按请求号留结果，未被后台接收的不宣称送达；重开只读回结果，不重发未确认输入；旧连接不能再写 |
| 后台重启忙闲未知 | 延续历史窗格查询与 unknown；不复活 PTY、旧凭据或未完成投递；派发记录保留，未知写入不自动重放 |
| 同一唤醒重复送达 | entry id + 固定目标关联一个 dispatch；并发 send/ack/重复调用只返回已有结果，不能二次 paste；崩溃留下 pending 只能报 unknown，不能当重试许可 |

额外守住：记录器失败时受管输入不入 PTY；设备应答不算用户输入；旧 Stop 不放出新回合队列；主控 PermissionRequest 不能按 worker 的“不应弹确认”规则判为同一种故障。

## 6. 红态、反例与验收顺序

首个 **Tracer bullet**：同一夹具任务中，Electron 向固定窗格输入一句中文 → 后台鉴权与记录 → 真实 node-pty 中的确定性接收器收字节 → 独立 SQLite 读回用户输入；再在同一窗格注入另一句，验证它只进入派发记录。随后扩展两个主控、受管 worker、report 唤醒和紧急停止。不会先完成所有表与 API，再补真实输入路径。

每个新行为的红态是“新增合同尚未实现”，不是宣称旧版本违反当时的只读契约。先写来自 ticket/spec 的独立期望与测试输入，固定在起点跑失败，再改相关产品。起点缺新入口时保留明确的契约拒绝；导入失败、fixture 初始化失败、EPERM 不算行为红态。若新入口挡住后续断言，再对候选做去掉关键保护的单点变异，证明深层断言会失败。

| 验收对应 | 红态与绿态读取 | 必须拒绝的反例／变异 |
| --- | --- | --- |
| A1：两个主控＋worker，同一任务 | CLI attach/dispatch、启动记录、Electron 三窗格截图及 PTY 接收文件；起点无 controller runtime/多窗格 | 错任务 launch、历史 launch 输入、复用原生会话；启动记录漏参数或角色卡 |
| A2：输入与介入 | 从界面输入固定中文、多行内容，数据库独立读回；后台注入同文本仍不能算用户输入 | 来源按正文标记猜测；注入混入 user_inputs；漏 `human_intervention`；记录失败后仍写字节 |
| A3：report 唤醒／排队／Esc 放行 | 空闲立即写；用户 CR 到 hook 之间触发注入不写；Stop 后写；Esc 后只在真实用户 action 后写 | 去掉 CR 即忙、去掉 Esc 锁、用旧 Stop 放行、队列写前未登记、重复 entry 二次写 |
| A4：send/list/ack/ready | 库客户端 → 后台 → SQL 读回；ready 使用固定 fixture ticket 集合与独立预期列表 | worker assign；伪造 from；ack 非本人条目；不合规 ready；跨项目读取；UPDATE/DELETE 被拒 |
| A5：stop→ack／逾时中断／actor | 正常中断、ack；另一个条目等待真实两分钟后再显式请求中断；PTY Esc、存活 shell、事件和 Git 引用读回 | 提前／已有 ack／错误目标／错误凭据；写假 actor；中断暗中关闭 pane 或推进门禁 |
| A6：配置与授权隔离 | 固定 argv/settings 的静态及夹具读回；本次不启动真实 Claude | 任何读取或写入用户全局配置的路径、真实认证或未授权模型请求 |
| A7：回归 | 8/9/18 经后台入口，既有 T-075 非模型正反例按相关运行器复跑 | fence/CAS/锁反例必须仍在业务断言失败；不改 acceptance 断言，不用旧 PASS 背书 |

两分钟临界值 120,000 与 120,001 ms 的孤立检查可用现有 `A2AGates` 时钟注入；它补充、不能替代真实后台的逾时流程。该孤立检查的失败方式预先列为：比较符错误、客户端时间冒充服务端时间、ack 竞态、目标更换、actor 参数覆盖凭据。

预定新增 `workbench/tests/test_controllers_e2e.py`（具体文件名可随实现最小调整），从 `--source`、`--output` 显式选版本与未存在的证据目录；各场景有固定编号，可在旧版本和候选重放同一输入。计划命令形式如下，**这些测试文件尚未创建，命令未运行**：

```sh
python3 /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/test_controllers_e2e.py --source /tmp/a2a-t078-baseline --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/red-01 --case all
python3 /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/test_controllers_e2e.py --source /Users/luckye/Documents/Code/a2a-wt-t078 --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/green-01 --case all
```

起点从固定提交只读导出到本卡的临时夹具，测试使用相同驱动而非拷贝候选产品修复。现有 `run_daemon_acceptance.py` 默认输出 T-075/card-5 且含旧任务身份；本卡不能直接用默认路径。实施时仅给 `workbench/tests/` 的运行器增加显式输出目录与证据身份参数，或复用其适配器由本卡驱动保存结果，原 8/9/18 业务断言保持原样。

运行产物至少含：完整命令及 cwd、退出码、stdout/stderr、代码版本、CLI/依赖版本、夹具输入、真实 PTY 接收内容、数据库只读查询、截图、hook 原文及来源层级。自动键入标为“测试模拟用户输入”，不说用户本人实际键入过。故障现场按新 run 目录保留，探针错误与协议／产品错误分开；后两者及需修改业务断言的情况停交执行主控。

## 7. 不消耗模型的 Claude 夹具方案（待用户决定，不运行）

首选 needs-decision 中的 A：固定真实 Claude Code CLI，在本卡 `/tmp` 隔离配置与 HOME 下，通过每会话 `ANTHROPIC_BASE_URL` 接入仅监听 loopback 的确定性 Messages API 服务，使用无真实权限的夹具 key，不读取、复制或使用用户凭据。hooks 由真实 CLI 发出，输入经过真实 zsh/node-pty。预置响应包含普通文本、延迟完成、工具权限请求与中断窗口；用屏障控制交错，不由模型随机决定何时停。

本地假服务所需请求格式与流式事件在获准后先核对固定 CLI 版本和既有 T-064 夹具，再做最小启动探针；本计划不假定当前版本能无登录启动。记录 HTTP 请求去向、CLI argv、配置目录、原生会话与 hook 原文；遇到认证／信任／更新提示不按 Enter、不改全局配置。若需要实际外部请求，立即停报。

P2 最小探针：一个 Claude 主控窗格、两条带唯一测试编号的输入、一个延迟完成屏障、一次 Esc；验证 CR 后立即 busy、Stop 可对应唯一提交、重复／迟到 hook 不解锁、Esc 后用户放行才送达。成功才扩展双主控 report/ack；失败不靠伪造 `turn_id`、屏幕字样、超时自动放行或重试补救。负责人为本 worker，执行由主控持本卡沙箱外脚本完成，产物落 `T-078/<run>/claude-fixture/`。

备选是确定性终端接收器＋重放 T-074 的 hook 协议样本。它只能证明后台／UI 状态规则与字节通路，不能证明真实 Claude CLI 发出这些事件；不得用这个备选补称 A1/A3 的真实 Claude 已通过。**包括备选在内，本节方案在用户答复前只写计划，不运行。** 若本卡获准先实施其他部分，Claude 相关证据保持“待真实 Claude 复核”。

本卡不运行真实模型；若用户选 B/C，真实模型部分仍由执行主控另开卡。本卡 RESULTS 将分别列后台规则、真实 CLI＋假 API、真实模型三种证据，缺哪层就保留哪层的 INCOMPLETE，不把历史 T-074 授权延用到本卡。

## 8. 沙箱外项目、检查点与交付

计划批准后分阶段准备 `evidence/2026-10-11-batch13/T-078/outside-sandbox.sh`，所有源码、证据和脚本路径使用本 worktree 绝对路径，每次执行写入新的 run 目录。以下项目由执行主控运行，本 worker 不申请提权：

- Unix socket 后台与真实 PTY 的红态／绿态、`ps` 前台身份观察、自建进程中断／重启与清理。
- Electron 标准构建与启动、窗口输入及截图；构建槽、Vite 缓存、Electron 依赖缓存只用已挂载 `/Volumes/WD-Elements`，不安装依赖、不改共享输出链接。
- 第 7 节获准后的真实 CLI＋本地假服务；独立后台均 detached/start_new_session，只清理本卡创建并核对身份的进程与文件。
- 8/9/18、T-075 相关无模型回归、变异体、变基后复验。

每个需要外部运行的检查点完成脚本与可审阅输入后，回复 `T-078 OUTSIDE-SANDBOX READY` 并停下，由主控执行。预期红态需按事先列明的契约失败判读；未预期的产品／协议失败先停报，禁止顺手改断言。

候选完成时按任务卡做一次 fresh-context 只读独立审查，提交范围限定本卡文件与候选版本；届时使用 behavioral-acceptance-review 的证据审查流程，结构性风险纳入同次审查，不在计划阶段派生实现 agent。发现问题先保留新的红态；修复 diff 交执行主控审。审查会话只读，不 submit、不集成。

最终才更新本 ticket 的 Resolution，保持 open、写“待主控关闭”；中文 RESULTS 对 A1～A7 和六项失败方式逐条报告状态，记录未运行的真实 CLI／真实模型／真实输入法检查。提交带项目规定尾注，git add、git commit 各单独执行，不 push。

提交前检查 `find /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078 -size +5M`；超限原始数据压缩或按批准路径归档，保留摘要和重放命令。完成前再次运行 project-map status，若需要改地图 Verified 则交唯一写入者执行主控处理。

## 9. 与 T-076-1、T-077 的接点及变基

| 文件 | 本卡拟改 | 必须保留的并行意图 |
| --- | --- | --- |
| `workbench/src/daemon.ts` | caller 凭据解析、输入/主控命令、inbox 路由、多窗格 snapshot | T-076 的 Stop relay、多回合身份与回执；T-077 的门禁路由，不能为匿名测试旁路鉴权 |
| `workbench/src/panes.ts` | controller attach/Claude 启动、单一输入顺序、用户放行、wake/interrupt | T-076 的会话与回合分离、模型尾注、fresh reviewer；T-077 冲突回写仍走相同登记通道 |
| `workbench/src/gates/core.ts` | 既有用户输入/收件箱/stop 的最小接线，投递排队结果与真实 caller | T-076 质量串／打分／身份与一致性检查，T-077 worktree/CAS/清理；不重写整文件或迁移门禁存储 |
| `workbench/src/gates/cli.ts`、contracts、store、README | 必要命令及状态契约、追加记录、文档同步 | 共用字段不改旧语义；新表只追加；两份文档改动合并保留事实与限制 |
| `workbench/app/*`、新 `workbench/bin/inbox`、本卡测试与证据 | 输入与三个窗格、库客户端及本卡验收 | 尽量把本卡独有逻辑留在这些位置，不改其他批次证据 |

旧 membership/preset 另库及 attachment 事件一致性已有 T-076 负责，本卡不自行迁库；如主控 attach 依赖的缺口无法在当前合同内接通，记录最小阻塞点交主控，不复制第二套成员表绕过它。

交付前在本分支执行 `git -C /Users/luckye/Documents/Code/a2a-wt-t078 rebase main`。只合并双方意图；碰到权限／验收含义冲突先报告，不用删除对方行为消冲突。变基后的代码重新跑本卡完成条件、8/9/18 与相关 T-075 正反例，记录新的完整代码版本；旧候选的通过结论不能替代。不得触碰主 checkout。

本轮收尾：只保存 PLAN 与计划检查证据；不改产品、ticket Resolution 或验收断言，不运行 Claude 夹具。回复 **T-078 PLAN READY** 后按任务卡明确要求停下，等待执行主控。
