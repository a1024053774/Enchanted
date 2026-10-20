# T-107 第三轮独立审查

STATUS: INCOMPLETE
TARGET: `f563fd5182feebfd16bee9063714e278536ddc6b`（实际 HEAD，exec/t107）

**第三轮 F4 修复候选尚未提交，不能确认修复通过。实际 HEAD 仍为第二轮候选，独立复验仍为 NO_GO。** 本轮没有把暂存区修复或 electron-06 的源码副本当作已提交候选；不批准集成或关闭 T-107。

## 候选身份与范围

按指定顺序读取主 checkout reviewer 角色卡、本 worktree AGENTS、T-107、T-095、RESULTS，再读取前两轮报告、修复交接、地图、CONTEXT 和 intent。未读作者会话，未开子 agent，未调用模型。预期来自任务票及本次派发，候选自带测试只作为待审证据。

开场与收尾 `git rev-parse HEAD` 均为上述完整版本，`git show -1 --format=fuller` 是第一轮 F1–F3 修复提交；`git diff f563fd518 HEAD` 为空。F4 的 paneRecovery.ts、panes.ts、sidebar.ts 及相关测试修改在暂存区，共 12 个暂存文件。第二轮报告、脚本与 electron-06 摘要另为既有未跟踪文件。本轮保持这些内容原样。已通过文本输入工具请求主控提供提交后的完整版本，截至收尾未收到答复。

目标：核对 F1–F4 与本次必审合同，并验证明显错误实现能否逃过完成条件。非目标：实现、修复、把未提交修改改作候选、补采集、启动模型或发布。唯一关键未知为第三轮应冻结的修复提交；这直接影响审查结论。

应用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review、document-writing，以及 frontend-production 的侧栏主路径工程快审。所有审查由本会话完成。Ubiquitous language：区分启动记录、原生会话、任务与 attempt；Tracer bullet 的局部旅程不替代整票七状态；Deep modules 核对查询与采集职责、共同归属模块。只写指定报告、脚本和新建 /tmp 现场；不提交、不 checkout/reset/stash/push、不申请升级、不用问题面板、不写全局配置、不操作 Herdr。模型调用和真实模型回合为 0；不要求截图。

## FINDINGS：当前 HEAD 仍有 F4 · P1

位置均指 **git show 的冻结 HEAD 原文**，不是暂存后行号：`workbench/src/sidebar.ts:33`、`:44`、`:55`；既有定位合同 `workbench/src/paneRecovery.ts:37`。

该 HEAD 仍要求 `basename(file) === pane.native_session + '.jsonl'`。恢复与采集接受 `<session>.jsonl` 后缀的 rollout 文件。根 metadata 已证明 ID 和 CLI 来源时，rollout 文件仍被记为 root=false；其问题被忽略。同一 submission 的 turn_start_signal 便可将未答问题上调为 running。

独立探针经过实际 `Panes.scan → SQLite native_record → sidebarSnapshot → agentState`，没有替换产品方法；输入为受控 PTY 身份和日志，不证明真实 CLI、模型或 OS 进程。每次提问前均为 running，提问后必须保守为 unknown；两种内容相同的文件仅改变命名：

| 输入 | 实际提问后状态 | 问题入库 | 结论 |
| --- | --- | --- | --- |
| `<session>.jsonl` | unknown | 1 | PASS |
| `rollout-2026-10-19T12-00-00-<session>.jsonl` | **running** | 1 | **NO_GO** |

正式现场 `/private/tmp/t107-review-outside-03-ko_o8ej3/review-summary.json` 保存两份观察、输入位置和命令；simple 现场为 `/private/tmp/t107-review-rollout-exuBd7`，rollout 现场为 `/private/tmp/t107-review-rollout-aXHIIF`。这是已采集的问题被错误投影，非缺依赖或初始化失败。现有 HEAD 自带 projection 和 IPC 检查先通过，仍不能拒绝 F4。

暂存修改的静态方向符合第二轮建议：在现有 paneRecovery 中提取后缀合同与 root/auxiliary/unknown 归属，恢复、采集与侧栏共同调用；未知来源不再等同辅助。但它不在本轮 HEAD，**未取得本轮冻结修复候选的绿态与变异证据**。不能据此写“F4 从根修好”。最小交接是由主控完成该修复提交并重新提供完整版本；无需 reviewer 修改候选。

## F1–F3、恢复提示与结构

| 项目 | 结论与证据边界 |
| --- | --- |
| F1 辅助 start 清根问题 | 精确文件名的反例仍被挡住，pending 不再被 start 清空；但 HEAD 的归属错误 F4 仍破坏同一底线，不能报完整修复 PASS。 |
| F2 侧栏读取写库 | 当前 HEAD 的 Panes.status 为纯快照，PTY 输出、hook、processInfo、退出负责采集。本轮独立实际 Panes/SQLite 连读两次，在未消费日志下全部表、schema、trace 和 offsets 不变。未独立重跑 daemon socket/Electron；其旧结果不代替第三轮修复候选。 |
| F3 完成条件放过写库 | 单行 store.event 变异被持久化业务断言拒绝，见下表；不是靠进程崩溃拒绝。 |
| 五条“未恢复” | 对照基线恢复路径，两个 controller 为 restore_record_unrecognized，三个受管 attempt 为 restore_managed_attempt_requires_reclaim，均为 T-096 原有拒绝。本轮未发现恢复实现被修改；五条精确提示、全页数量及只读断言保留。 |
| 是否削弱其他检查 | 阅读完整测试 diff，跨窗口、iframe、旧 key、错误任务/attempt、历史只读、关闭时序和布局断言保留；没有用“所有 alert 放行”代替恢复拒绝。当前修复暂存测试新增的归属反例尚不能记作冻结候选通过。 |

冻结完整 diff 经 design-integrity 定位器扫描（`design-locator.json`）并逐项追踪：Git catch 保留具体失败原因；刷新失败把状态改未知并显示原因；聚焦/设置失败显示错误；PTY scan 异常进入 recordFailure。三秒轮询是事实读取；changeTask 有任务切换与 agent 选择两个真实调用点。没有确认新增的无依据重试或吞错成功路径。**仍确认的结构问题是 HEAD 在 sidebar 另立过窄文件规则，与既有定位逻辑冲突，再被另一条 running 正证路径绕过。** 暂存区的共同归属模块只能算未验收的修复方向。

## 必审合同与状态分支

层级静态核对：只从 launch、attempt、成功 assign relay 与 dispatch 的 inbox_entry 关联。发送 launch 必须匹配 input 身份、项目/任务/preset、结果 from/to；歧义与跨项目不建边，合法角色边和防环检查保留。没有从标题或终端文字猜父层级；无父绑定的 worker/reviewer/monitor 在“未归属”的任务组。worker 直接派发仍无具体父 launch，完整层级 INCOMPLETE。

HEAD 的 `agentState` 按执行顺序逐分支如下：

| 条件 | 结果或影响 |
| --- | --- |
| restoration failed/pending | unrestored，机械恢复事实。 |
| lifecycle ended | ended。 |
| 缺 pane、historical、failed、interrupted、生命周期非 running | unknown。 |
| permission_wait | 标记 permission，后续未知。 |
| 同 native 的 turn_start_signal 或 pane_idle.stop | 清 permission 标记，不直接上调状态。 |
| session_meta + file | 用 ID/CLI 来源/精确 basename 设 root；最后一项过窄，F4。 |
| 已认定 root 的 task_started | 更新该文件 turn，不清问题。 |
| root 且当前 turn、metadata turn 不冲突的 request_user_input/async | pending；accepted:true 不当答案。 |
| 来源缺失，或 root 已认定但 turn 无法对应 | uncertainQuestion。 |
| origin 存在但 root=false 的问题 | 被忽略；rollout 根文件可达此错误分支。 |
| permission、pending 或 uncertainQuestion 非空 | unknown；尚无两种等待的生产正分支。 |
| idle 且无 active/writing | idle，使用现有 host 状态。 |
| root 文件多于一个 | unknown；此检查在 idle 之后。 |
| busy、active、非 writing、有 native；唯一 root turn 与 pane/active.nativeTurn 关联 | running。 |
| 同样前置条件，active.id 对应 submission 后有同 native start signal | running；F4 漏问题后被此分支上调。 |
| 其余 | unknown。 |

项目汇总为等待用户 → 等待主控 → running → 空集合或含 unknown 则 unknown → unrestored → idle → ended。项目 running 不改写单个 unknown，但会传播 F4 的错误 running。协议 event type、工具名与字段匹配是机械事实，没有新增屏幕语义关键词或正则；Git 正则仅解析 porcelain 数字。

T-095 的状态确实存在，不能说“整个项目没有等待主控信号”。`scripts/agent-status` 要求 HERDR_ENV=1、records/launches.jsonl、Codex worker/固定版本、pane/terminal/cwd/native 身份和前后读数稳定；再用 visible/detection 的面板标记与 blocked 互证。工作台 SQLite launch 与自管 PTY 没有这个 Herdr 边界，**不能直接调用该命令得到合法正例**。现有根 request_user_input 也没有回答对象字段；仅凭 worker 角色猜主控不合规。移植识别或补采集超出票中“不改采集”的范围。两种等待生产映射、七状态真实回放、回答后恢复继续 INCOMPLETE。

Git 已查范围 PASS：execFile 参数数组，porcelain v2 --branch，不依赖自然语言，GIT_OPTIONAL_LOCKS=0；真实分叉夹具与 LC_ALL=C 的 status -sb 同为领先1/落后1，无上游为 null；独立不存在目录探针返回 null 数值与具体原因。本轮所有复验 Git 子进程设 LC_ALL=C；本地上游事实不代表已 fetch。

通知合同局部 PASS：只在 waiting_user_answer 转入时通知一次，按 state 路径/launch 去重；普通运行/空闲/主控等待不通知，关闭仍更新观察状态，重开不补发旧等待，离开再进入再发一次。IPC 测试的 Electron Notification 是替身；设置为本窗口 userData 文件。electron-06 摘要有重开保留检查，但未绑定新的修复提交。本轮没触发真实系统通知，仍 INCOMPLETE。

IPC 已查范围 PASS：显式新增 sidebar/selectAgent/notificationSetting，windowTarget 核对注册 window、webContents 和 mainFrame；选择会话再核对 catalog 所属 task、snapshot task/launch/role。没有任意命令或任意路径参数。匿名 sidebar_snapshot 与原目录读取同属 socket 边界。临时 viewOnly 不发输入凭据、不保存布局，关闭不写 pane_layout_close；未放宽已有保存窗格准入。合同从17 handler/18 bridge扩至20/21，旧拒绝断言保留。侧栏读取本身只读，设置接口是显式设置写入。

前端仅静态快审：项目入口复用 T-106、中文状态/图例、未归属、选中/等待样式、刷新失败未知和错误原因可见。未独立走 GUI、读屏、200%缩放、长文本与长期性能，不声明完整前端验收。electron-06 的六项局部 PASS、cleanup_complete=true、总状态 INCOMPLETE 仅为主控已运行记录，不能用于本轮不存在的新提交。

## EVIDENCE 与 COUNTEREXAMPLE

命令：

```sh
bash evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-03.sh local
```

现场：`/private/tmp/t107-review-outside-03-ko_o8ej3`。通过 git archive 新建候选和三个单处变异副本，没有 worktree；stdout/stderr、完整 argv、摘要、源码、独立探针均保留。预期来自 T-107，而非复制产品输出。

| 检查 | rc / 观察 |
| --- | --- |
| 当前 HEAD projection，真实 Git/SQLite、受控 pane 状态 | 0 |
| 当前 HEAD main/preload IPC，含历史坏版本与内置反例 | 0 |
| 最终 unknown 改 idle | 1；Missing signal must remain unknown |
| 无派发事实时按 executor/title 猜父层级 | 1；Role-only parent must be rejected；此变异同时依赖角色与默认标题，不等于证明任意标题推断均被覆盖。 |
| sidebar 开头加一行 store.event | 1；Sidebar read changed persisted tables or traces |
| 独立未消费日志读两次 | 全表/schema/trace/offsets 不变。 |
| 独立文件名变换 sentinel | rollout 未答问题仍为 running，NO_GO。 |
| 独立 Git 读取失败 | null 事实与具体错误，PASS。 |

脚本整体 rc 1 为当前 HEAD 的明确业务拒绝；探针 rc 0 为保存两种观察，不能解释为 sentinel 通过。三个变异均在候选原检查通过后运行，并命中指定业务断言。

指定新脚本还提供 `electron` 模式：固定当前完整 HEAD、内置盘 Electron 43.4.1、Python 3.9 可解析、LC_ALL=C、隔离源码与状态目录；保留旧 F1/F2/F3 反事实与实际 GUI 旅程、写库变异拒绝，以及本轮独立 rollout sentinel。本轮未运行该模式，未申请升级。脚本起始核对 HEAD；若主控已提交新修复则拒绝运行，避免脚本自动接管未经冻结的新候选。**它只绑定本次实际旧 HEAD，不能用于宣称新提交通过；应在提供新 commit 后由新审查更新。**

## LIMITATIONS、RULE 与收尾

本轮核心缺口是候选身份：要求第三轮修复审查，但 HEAD 仍是第二轮已拒版本。没有把暂存修复运行结果补称为已提交版本证据。整票另有七状态、完整 worker 父层级、真实通知缺口。

防复发应把 rollout 命名变换 sentinel 与同 submission start hook 纳入完成条件，并在冻结修复候选的实际 daemon/Electron 入口重跑；继续保留辅助隔离、未知来源与全表只读断言。新候选须先通过，再确认未知改空闲、猜层级和读取写库单处变异仍被拒。不能用旧候选的绿色检查替新修复背书。

project_map 原始运行因共享 Git 配置 core.bare=true 无法识别 worktree，报12项；不修改配置，仅给只读 status 进程传 GIT_WORK_TREE 后为既有8个稀疏缺路径问题、0 stale，rc 1。收尾原文在现场 closing-project-map-status.txt，不能报告0问题。既有 intent 构建约束与当前 AGENTS 内置盘裁定不一致，此处只报告，不改范围外文档。

报告与脚本以 UTF-8 保存；语法、编码和 diff 检查结果见收尾工具记录。需要主控先提交 F4 修复并提供完整版本，再进行第三轮冻结候选复审。

T-107 REVIEW INCOMPLETE
