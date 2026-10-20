# T-107 第二轮独立审查

**NO_GO，需修复。** 冻结候选：`f563fd5182feebfd16bee9063714e278536ddc6b`，分支 `exec/t107`。

F2 的查询／采集职责已分开，F3 的主动写库变异已被拒绝；F1 的简化辅助会话反例能够通过新检查，但根会话归属仍有可达错误：使用采集器支持的 `rollout-…<session>.jsonl` 文件名时，根问题会被忽略，并被启动钩子上调为“运行中”。因此不能批准此候选集成或关闭整票。两种等待、完整 worker 父层级和真实系统通知仍为 INCOMPLETE。

## 范围、依据与独立性

- 按派发顺序读取 reviewer 角色卡、AGENTS、T-107、T-095、RESULTS，随后读取第一轮报告与修复交接。未读取作者会话，未开子 agent。
- 用 `git show` 和 `git diff 0967cd465 HEAD` 阅读完整候选，用 `git diff 3c3f2e9e1 HEAD` 定向复核修复。审查期间 HEAD 未变。
- 目标：验证 F1／F2／F3、保存事实建立的层级、未知状态、Git、通知与 IPC。非目标：实现修复、补采集方式、运行模型、发布。验收预期来自 T-107 与本次派发，不以候选测试的绿色结论作为答案。
- Ubiquitous language：启动记录、原生会话、派发记录、任务与 attempt 分别核对。Tracer bullet 的局部通过不能替代整票七状态与完整层级；Deep modules 重点核对采集与查询职责，以及根会话身份的归属。
- 应用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review、frontend-production（限定侧栏主旅程的工程快审）和 document-writing。所有审查由本会话完成。
- 只写指定报告、`REVIEW-OUTSIDE-02.sh` 和新建的 `/private/tmp` 目录；没有提交、切换、重置、暂存、push、调用模型、操作 Herdr、写全局配置、申请升级或使用问题面板。模型调用与真实模型回合均为 0；按用户裁定不要求截图。
- 当前提交说明如实披露用户手动切换后的 Codex 身份、无 A2A 启动绑定与执行主控代提交，没有伪造 worker 尾注；这项披露本身不代表门禁交付已通过。

## 确认问题：F4 · P1，根 rollout 问题被忽略后错误显示运行中

位置：`workbench/src/sidebar.ts:33`、`:44`、`:55`。相关入口：`workbench/src/panes.ts:671`；既有文件定位合同：`workbench/src/paneRecovery.ts:37`。

新增的根来源判断要求 `basename(file) === pane.native_session + '.jsonl'`。现有采集器和恢复定位使用文件名以 `<session>.jsonl` 结尾的合同，支持 `rollout-…<session>.jsonl`；仓库既有 native final-read、hook 与 worker delivery 场景也使用 rollout 命名。

当 metadata 已证明 `source === 'cli'` 且 `id` 与 pane 根原生会话一致，但文件有 rollout 前缀时，`files` 仍保存该文件，只把 `root` 置为 false。随后根 `request_user_input` 既不进入 pending，也不进入 uncertainQuestion：`:44` 的 `!origin || origin.root` 为 false。若当前 submission 之后存在同 native session 的 `turn_start_signal`，`:55–57` 便返回 running；该钩子不是问题已答复的证据。

本轮独立受控探针经过实际 `Panes.scan → SQLite native_record → sidebarSnapshot → agentState`，未调用模型，没有替换这些产品方法。PTY 对象与空项目目录是受控输入；这项探针不证明 CLI、OS 进程、daemon socket 或 GUI 行为。预期由票据给定：无法区分回答对象的问题应为未知，不能显示运行中。

| 同一会话内容，仅改变文件名 | 问题出现前 | 问题出现后 | SQLite 问题条数 | 预期 |
| --- | --- | --- | --- | --- |
| `<session>.jsonl` | running | unknown | 1 | unknown |
| `rollout-2026-10-19T12-00-00-<session>.jsonl` | running | **running** | 1 | **unknown** |

两条路径的 `pane.turn` 与 `active.nativeTurn` 均保持 root-turn，没有回答事件，也没有辅助会话。失败不是未采集、环境错误或缺依赖。新候选自己的 projection 与 IPC 检查在该探针前均 rc 0，说明现有检查仍不足以拒绝这个明显错误实现。

最小修复方向：在现有根原生会话归属层统一文件与 metadata 核对，遵守既有 rollout 文件合同；不能把“未满足过窄文件名条件”当成“已确认是辅助会话”。未核实来源必须保守为未知。保留已修复的辅助会话隔离与零写入，不增加猜测分支。

防复发检查：在侧栏状态完成条件中加入上述文件名变换的 sentinel，并包含“同一 submission 启动钩子 + 未答根问题”。要求当前候选先失败、修复候选再通过，且复跑真实 daemon／Electron 入口。只测 `<session>.jsonl` 的根归属不能承担此合同。

## 第一轮三项与恢复提示

| 项目 | 本轮判断 | 证据与边界 |
| --- | --- | --- |
| F1 辅助 start 清掉根问题 | **未从根上修好，NO_GO** | 不再 pending.clear；新检查要求根 metadata／文件／turn，辅助和缺来源 start 不解除问题。这一简化反例已通过，但新增文件名判断造成 F4，真实可用文件形态仍可错误上调。 |
| F2 侧栏读取写库 | 已查范围 PASS | `Panes.status()` 移除 scan；采集放到已有 PTY 数据回调，hook、processInfo、退出等采集路径保留。本轮实际 Panes／SQLite 探针在未消费日志存在时连续读两次，所有表、schema、trace 与 offsets 原值相同。实际 daemon／Electron 的证据来自主控 electron-05；本轮未独立重跑这些进程入口。 |
| F3 完成条件放过主动写库 | 指定变异 PASS | 当前 projection 的读取前后比较覆盖每个 SQLite 表、schema 和 trace。单行 store.event 变异 rc 1，命中专属业务断言。真实 runner 同时串入 daemon 未消费日志只读检查及 Electron sidebar IPC 原值比较；本轮外部重跑待执行，不能外推为所有副作用均已覆盖。 |
| 五条“未恢复”提示 | 原有 T-096 拒绝，不是本次恢复退化 | 两个 controller 缺少可恢复合同，原本就拒绝 restore_record_unrecognized；三个受管 attempt 原本就拒绝 restore_managed_attempt_requires_reclaim。对照基线的 recover／requireFakeControllerRestore 与候选，这些拒绝路径未改。原 renderer 的诊断映射也保留。 |

修复没有删除或放宽 IPC 的跨窗口、iframe、旧 key、错误任务／attempt、只读审查员、关闭时序与布局断言。running 正例增加根来源事实，同时新增缺来源必须未知的反例。原 GUI 的“全页无 alert”断言被五个刻意不可恢复夹具违反；改成等待五个指定 launch 全部加载，逐窗格要求确切的一条恢复拒绝和只读输入，并要求全页 alert 恰好等于五条预期，能拒绝额外连接错误。这是修正错误 oracle，不是把所有 alert 放行。

已读取主控 `restoration-oracle-summary.json`：缺窗格、错提示、缺提示、可写历史、额外连接错误、缺全页提示六种反例均被拒。该文件是既有证据，本轮没有将其冒称独立运行。`electron-05-summary.json` 的六项局部检查 PASS、cleanup_complete true、总状态 INCOMPLETE，与派发描述一致；其中状态只覆盖三种历史状态，不证明七状态来源。

## 必审项

| 项目 | 判断 |
| --- | --- |
| 层级来自保存事实 | 已查范围 PASS；完整层级 INCOMPLETE。SQL 关联目标 dispatch 的 inbox_entry、成功 relay result、认证发送 launch；核对 input 的 launch／project／task／preset、结果 from／to 及同项目，歧义不建边，再限制合法角色边并防环。未读取窗格标题或终端文字推断父子。任务与 attempt 来自启动记录。没有可信父 launch 的 worker／reviewer／monitor 在“未归属”的任务下。 |
| 状态未知与语义识别 | NO_GO，F4。精确协议工具名、event type 与 JSON 字段匹配属于机械事实；没有用正则或关键词猜提问语义。Git 数字正则只解析 porcelain 协议字段。 |
| 两种等待来源 | INCOMPLETE。状态枚举、图标和汇总已定义，但 agentState 没有返回这两个状态的生产分支；现有问答信号只能保守未知。不能把七种枚举写成七状态验收通过。T-095 的条件见下文。 |
| Git | 已查范围 PASS。使用 execFile 参数数组运行 `git status --porcelain=v2 --branch`，不解析本地化普通输出；GIT_OPTIONAL_LOCKS=0。真实分叉夹具领先 1／落后 1，与 LC_ALL=C 的 status -sb 一致；无上游是 null，失败返回 null 和具体原因。本轮不存在目录反例也通过。没有网络 fetch，数值是现存本地上游引用的事实。 |
| 通知 | 合同局部 PASS；真实触发 INCOMPLETE。只在进入 waiting_user_answer 时，按 state 路径／launch 去重；重复读取不通知，运行／空闲／等待主控不通知。关闭期间仍更新已观察状态，重新启用不补发旧等待，离开再进入会再次通知。设置写入该窗口 userData；主控 electron-05 已验证关窗重开保留。生产等待分支目前不可达，没有真实系统通知证据。 |
| IPC 与攻击面 | 已查范围 PASS。显式增加 sidebar、selectAgent、notificationSetting 三个 bridge／handler；均先 windowTarget 核对注册窗口、webContents 和 main frame。launch 类型、catalog 所属 task、snapshot task／launch／role 均校验。新接口没有任意文件路径或任意命令参数。daemon 新增匿名只读目录命令，与原 projects／tasks 读取边界一致，socket 权限边界保留。 |
| 历史视图与输入权限 | 已查范围 PASS。临时 viewOnly 不发输入凭据，不进入保存布局，关闭不写 pane_layout_close；原保存窗格的准入合同保留。main／preload 合同本轮 rc 0，20 handler／21 bridge，未知 launch、伪造 foreign task、iframe 与未知窗口被拒。 |
| 前端限定快审 | 静态核对项目列表、未归属分组、中文角色／状态、图例、选中与等待样式、失败后未知和真实创建入口复用。真实窄窗、聚焦与设置旅程只引用主控 electron-05。没有独立 GUI、读屏、200% 缩放或长文本压力证据，不宣布完整前端验收通过。 |

### 状态映射逐分支

入口 `workbench/src/sidebar.ts:17`，按执行顺序：

| 条件／动作 | 返回或影响 | 核对结果 |
| --- | --- | --- |
| restoration failed／pending | unrestored | 使用机械恢复事实，优先于 ended。 |
| lifecycle ended | ended | 使用生命周期事实。 |
| 缺 pane、historical、failed、interrupted、生命周期非 running | unknown | 不上调。 |
| permission_wait | permission=true | 后续保守未知。 |
| 同 native session 的 turn_start_signal，或同 native session 的 pane_idle.stop | permission=false | 不因辅助或未知身份事件解除标记；本身不直接返回运行中。 |
| session_meta + file | 保存 root 与 turn | source／id 合同正确，但文件名判断过窄，见 F4。 |
| 已认定 root 的 task_started | 更新该文件 turn | 不清问题；辅助 start 不更新根归属。 |
| root 且当前 turn、metadata turn 不冲突的 request_user_input／async | 加入 pending | 不把 async accepted:true 当答案。 |
| 问题来源不存在，或是已认定 root 但 turn 无法关联 | uncertainQuestion=true | 保守未知。 |
| 存在 origin 且 root=false 的问题 | 忽略 | 真实 rollout 根也会误入此分支，F4。不能据此证明是辅助。 |
| permission、pending 或 uncertainQuestion 非空 | unknown | 没有在此区分两种等待；没有可靠答案解析，后续仍可能保守未知。 |
| pane.state idle，且无 active／writing | idle | 来自现有 host 状态；该状态的建立／解除语义未在本票改写。 |
| root 文件多于一个 | unknown | 不把歧义上调。此检查在 idle 分支之后，不声称它覆盖 idle。 |
| busy、active、非 writing、有 native，唯一 root turn 与 active.nativeTurn／pane.turn 关联 | running | 正向来源事实；无法识别 rollout 文件时不走此正例。 |
| 相同 busy 前置条件，active.id 匹配 turn_submitted，其后有同 native session 的 turn_start_signal | running | 旧提交之前的 start 不算正证；但当根问题被 F4 忽略后，该分支会错误上调。 |
| 其余 | unknown | 最终未知改 idle 的变异被拒。 |

项目汇总顺序：等待用户回答 → 等待主控回答 → 运行中 → 空集合／含未知则未知 → 未恢复 → 有空闲则空闲 → 已结束。一个已确认 running 的会话可使项目汇总 running，单个未知会话不会因此被改写。当前 F4 的错误 running 会传播至项目汇总。

### 作者缺口与 T-095 能否直接用

“整个项目没有等待主控回答信号”不成立；T-095 已实现 Herdr worker 的该状态。准确缺口是：工作台自管 PTY 尚没有可直接使用的同等身份与观测边界。

`scripts/agent-status:192` 要求 HERDR_ENV=1，从 `records/launches.jsonl` 获取启动身份，限定 Codex worker／CLI 版本；核对 pane、terminal、cwd、原生会话与前后读数稳定，再读取 visible／detection 两份 Herdr 屏幕。只有两边机械面板标记与 Herdr blocked 互证才返回 waiting_controller_answer。工作台的 SQLite launch 与自管 PTY 没有这些 Herdr 身份；直接把工作台 launch 传进去不能得到合法正例。移植识别或补采集属于票据明确排除的采集方式变更，不能在本审查里补做。

现有 root request_user_input 工具名没有区分“问用户”还是“问主控”；不能单凭角色或工具名补猜。候选必须在未解决前保持未知，F4 正是违反了这条底线。T-095 的“已回答”与“跳过”仍有回落到 unknown 的已知限制，也不能据其存在推定工作台已覆盖回答恢复。

worker 直接派发路径 `daemon.ts:380 → Panes.dispatch → store.register` 保存目标 launch、文本和来源，没有具体父 launch；inbox 的 sender 地址也不是唯一会话身份。仅能成功关联 relay assign 的情况下建立父边，所以完整 worker 父层级缺口属实。真实系统通知未触发的声明也与现有证据一致。

## 本轮运行与变异

环境：2026-10-19，macOS；Node v26.5.0、Python 3.9.6；所有复验 Git 调用设 LC_ALL=C。正式命令：

```sh
bash evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-02.sh local
```

正式现场：`/private/tmp/t107-review-outside-02-aj18dnl3`。候选和三个变异均由 `git archive` 创建，没有建立 worktree。完整 argv、stdout／stderr、JSON、变异源码和独立探针保留在该目录；两个根日志现场路径记录在 review-summary.json。初次现场 `/private/tmp/t107-review-outside-02-pzgfdz1a` 同样保留；正式重跑增加独立未消费日志零写入断言，没有覆盖初次输出。

| 检查 | 本轮结果 |
| --- | --- |
| 冻结候选 projection，真实 Git／SQLite | rc 0 / PASS |
| 冻结候选 main／preload IPC，含历史坏版本与内置变异 | rc 0 / PASS |
| 单处错误实现：最终未知改为空闲 | rc 1；命中 Missing signal must remain unknown |
| 单处错误实现：没有派发证据时按 executor/title 猜父会话 | rc 1；命中 Role-only parent must be rejected |
| 单处错误实现：侧栏开头主动 store.event | rc 1；命中 Sidebar read changed persisted tables or traces |
| 独立实际 Panes／SQLite，未消费日志下连续两次读取 | PASS；所有表／schema／trace 及 offsets 原值不变 |
| 独立根 rollout sentinel | **NO_GO**；同内容改文件名后，未答根问题被显示成 running |
| 独立 Git 读取失败 | PASS；分支与数值为 null，具体错误保留 |

脚本最终 rc **1** 表示已确认业务 NO_GO；探针自身 rc 0 是为了完整保存两种观察，不代表状态合同通过。三个变异都在候选先通过之后运行，并因指定业务断言失败；没有用崩溃、缺依赖或初始化失败冒充拒绝。

真实入口复验命令已写入指定新脚本，固定当前完整提交：

```sh
bash evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-02.sh electron
```

本轮未运行 electron 模式，未申请升级。此模式在内置盘 Electron 43.4.1 上执行冻结候选旅程，并运行旧候选 F1／F2 反事实与主动写库变异的完成条件。写库变异可在 runner 的实际 daemon 前置只读检查被拒，因此不把它称为“变异已走到 Electron UI”。即使候选 GUI 局部旅程通过，已复现的 F4 仍使脚本最终 NO_GO。所有新输出仅在新建 `/private/tmp` 目录，不覆盖 electron-05 或第一轮脚本。

## 结构审查、边界与收尾

对冻结完整 diff 运行 design-integrity 定位器，结果保存在正式现场 `design-locator.json`，再逐项追踪：Git catch 返回明确读取失败；侧栏刷新失败显示未知及原因；聚焦／设置失败显示错误；新增 PTY scan 异常进入 recordFailure，不吞成成功。三秒轮询是读取事实，不是写操作自动重试。changeTask 有 selectTask 与 selectAgent 两个真实调用点，旧 projects／tasks IPC 属于既有公开合同，原合同断言保留。

查询／采集分离解决了 F2 的职责问题；没有新增双写门禁、兼容实现或无依据重试。已确认的结构风险是 F4：在 sidebar 重新制定了一条与现有根文件定位合同冲突的身份规则，再由另一条 running 证据路径绕过了问题未知。这应在根归属层修复，不用增加 catch／fallback 包住。

行为能力覆盖范围：launch／原生身份、状态编排、IPC、Git／SQLite／trace 文件读取与通知合同。模型理解、真实模型问答、真实系统通知、生产发布、长期性能不在本轮通过主张内。当前保守问题记录也没有可靠答案解析，不能声称回答后七状态转换已验收。

地图开场与收尾均 rc 1：相同的 8 个稀疏 checkout 路径缺失，0 stale，不能写成 0 问题。收尾原文保存在正式现场 `closing-project-map-status.txt`。shell 语法、内嵌 Python 3.9 语法、UTF-8 无 BOM／无替换字符／无行末空白及 diff 检查 PASS；工作树仅新增本次允许的报告和脚本，HEAD 仍为冻结候选。另有既有 intent 构建约束仍写外置盘，与本次明确内置盘裁定不一致；此处只上报执行主控，不改范围外文档。

交接：修复 F4 并补当前候选的红态／绿态反事实，再对变更范围复验；保留 F2／F3 的全表只读检查及三个已拒绝变异。两种等待、完整 worker 父层级和真实通知继续交主控处理，不能由 reviewer 把 INCOMPLETE 上调为 PASS。

T-107 REVIEW NO_GO
