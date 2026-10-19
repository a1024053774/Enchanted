# T-106 第二轮独立审查

STATUS: NO_GO（需修复；不代替整票收口或发布结论）

TARGET: `5036a8dc32de265dc27499028f0b938db3d1a15a`，`exec/t106`。固定比较起点为 `b0e12a88cdd601275595c85a4e177801dd58eb46`；第一轮候选为 `24cacef60f9e88103213c0bb93eecb0cb5c41cf3`。本地 main 已前移至 `37bc689fc02e4212a3f2609001869021362ff3a3`，未将其当作比较起点。

2026-10-19。第一轮 P1 在本候选中已修复；另确认一个 P2：空白标题在任何门禁调用前就被主进程拒绝，却因 IPC 抛错被 renderer 当作结果未知，锁住编辑、取消和重试。候选先通过现有检查，三个单处错误实现随后均被业务断言拒绝；旧候选也被同一提交后故障检查拒绝。额外提交前探针暴露了现有测试的缺口。真实 Electron 证据分版本核对，未把旧健康路径的 PASS 冒充本候选的新运行。地图“0 问题”仍为 INCOMPLETE，见 LIMITATIONS。

EVIDENCE:

## 范围与独立判据

- 按派发顺序读取主 checkout reviewer 角色卡、本 checkout AGENTS.md、T-106 ticket（包括简化表单裁定）、RESULTS-form.md；另读取 MAP.md、CONTEXT.md、intent.md、第一轮报告、直接调用方、原门禁、daemon、任务卡校验和相关测试。以 `git show` 读冻结原文，以 `git diff b0e12a88c 5036a8dc3` 读变更；结束时 HEAD 未变，受审 workbench 文件无工作区差异。
- 用户逐字选择："B 简化表单,不用主控 (Recommended)"。用户另说："证据截图什么的都不要了,我也不会看"。据裁定重建判据：不用模型；默认字段可见可改；只用现有门禁；确认前不持久化业务记录；拒收原因可见；取消草稿无残余；目录由主进程拥有。截图不作验收要求。
- 目标是核对 P1 根因修复、既有约束与完成条件的拒错能力；非目标是实现、修复、派 agent、整站外观/性能审查、安装或发布。没有取得 reviewer 自己的门禁 session/fence，不推断其值；按派发只交报告，不 submit、不集成。模型根回合 0。
- **Tracer bullet**：表单 → IPC → daemon 认证/解码 → 原门禁 → SQLite → 列表与按钮。**Deep modules**：校验、版本与持久化仍归门禁；UI 只解释事实与维护窗口草稿。**Ubiquitous language**：未保存、已保存、未知分别表达，不把失败响应当成持久化事实。
- 使用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review、frontend-production 的工程镜头及 document-writing。未开子 agent。适用能力轴：状态编排、异步确认、身份范围、桌面交互、JSON 文件、写库副作用。模型理解、检索/记忆、生产发布为 N/A，本票裁定不包含这些行为。

## P1：保存与注册结果分类

| 检查 | 结论与依据 |
| --- | --- |
| 门禁返回的确定提交前失败 | PASS。`workbench/app/main.ts:189` 只将有限错误按提交前拒收处理。逐一对照 `workbench/src/gates/core.ts:3281` 的卡校验、版本检查及事务，以及 `:3304` 的 create：这些错误均发生在相应业务提交前。create 的此类拒收仍返回 `persisted:true`，因为卡已经保存。未知错误不进入该白名单。但 main 自己的输入拒收没有结构化返回，见 FINDINGS 的 P2。 |
| card_save 提交后失败 | PASS。`main.ts:196` 进入 unknown，调用 `card_show(task, card_version=1)`，比较原门禁规范化后的完整卡片。匹配才承认卡已保存；读失败、未找到或内容不同都保留未知。`orchestration_failed`、`event_write_failed` 均不再被直接译成未保存。 |
| create 提交后失败 | PASS。`main.ts:206` 通过 status 核对任务号、仓库、项目号、标题、分支、卡版本、完整卡片和 ready；只有匹配才向 UI 返回注册成功。任务仍为 creating 时不能冒充成功。 |
| 未知状态的限制 | PASS。`main.ts:142`、`:165`、`:176` 分别阻止换目录、取消和重放。`renderer.tsx:329`、`:335`、`:351`、`:377` 保持未知提示，并禁止取消、Esc 取消和再次提交；已发 IPC 但 Promise 拒绝也不会重启提交按钮。主控提供的当前候选真实 GUI 原件核实了对应提示和按钮。 |
| 已核实保存但注册未完成 | PASS。卡保留；仅允许“关闭表单（保留已保存记录）”，不删库、不自动重试。读回是现有只读命令，不是第二条创建或补偿路径。 |

原门禁 `core.ts:3300` 提交卡版本后，daemon `:503` 仍可能因写结果事件失败而返回一般错误；本次修复针对这一事实做分类，没有修改 daemon 的错误合同或弱化门禁。只读核实失败的原因与原始失败 details 一起保留。

## 其余必审项

| 项目 | 结论与证据 |
| --- | --- |
| 唯一创建路径 | PASS。目录选定后 `main.ts:153` 调 card_template；确认后 `:225`、`:232`、`:236` 依次调 card_validate、card_save（expected_version 0）、create，均用主进程 operator 身份。相对起点的产品 diff 只有 app 和 README；未改 gates、daemon、schema 或校验规则，未直接写库。新增 card_show/status 只读核实，不产生任务。 |
| 项目随首个任务隐含 | PASS。既有 `A2AGates.listProjects()`（core.ts:325）从 tasks 的 project_id 投影项目；create 原本接收 project/repo/title。这是现有最小方式，没有独立项目表或新门禁命令。renderer.tsx:359 和 README“任务卡与交付”“日常启动”明确说明成功后才出现项目，不支持独立空项目。 |
| 确认前、拒收与取消 | 普通草稿路径 PASS。确认前只有 card_template 和窗口草稿；取消不调保存/注册。已有真实 Electron 健康路径核实了缺字段、非 argv、不可执行命令的可见拒收，以及取消前后 tasks、task_card_versions、task_card_snapshots、attempts、launch_records 五表零增长。本候选原拒收/取消断言复跑通过；提交后的状态另按上表处理，不把保留记录称为“取消无残余”。 |
| 目录信任边界 | PASS。三个新 handler 都经 windowTarget 校验 sender 对象与 mainFrame。选择目录拒绝额外参数，主进程 dialog → realpath → Git 根目录检查，repo 只存窗口上下文。提交严格限制五个字符串字段并拒绝额外 repo；create 只取 draft.repo。未知窗口、iframe、跨窗口草稿、renderer 路径注入反例通过。 |
| 完成条件、标题与目标 | 已查范围 PASS。新生产代码没有 shell 拼接：Git 读查询使用 execFile argv；临时卡路径由主进程 mkdtemp 固定生成；标题是门禁数据，目标进 JSON，UI 以文本呈现。原 commandArgv 只核对并解析可执行文件，不执行完成条件。真实入口原件有未执行标记；补充实际门禁探针使用含 `$(touch ...)`、`../../escape`、标签文本的不同标题/目标，保存正确且无标题命令标记。 |
| IPC 合同 | PASS。新增的是三个受约束的创建动作，没有通用命令、任意路径或执行桥接。17 个 handler / 18 个 bridge 名称显式核对；旧 key、iframe、跨窗口、历史 worker、凭据/序号、关闭恢复、旧版本与原变异断言保留。与第一轮相比，原创建/IPC/窗格测试源未改，复跑通过。 |
| 默认值 | 已查范围 PASS。非目标、allow=["."]、deny=[".git/"]、oracle_paths=["tests/"]、M、Codex/gpt-6.1-sol/xhigh，以及 source/base_commit/writer 的 null 均可见可改；分支预填当前分支，可改。整库范围偏宽，但明示且可改；验收路径依赖仓库实际情况，UI/README 已提醒，未宣称默认值适用所有仓库。当前候选真实 GUI 故障运行保留默认卡，仅填写项目、标题、目标和命令后成功注册，证明无需手工补其余 JSON 字段。 |
| 最少输入 | **只填名字和目标不能完成**：完成条件命令为空且 required（renderer.tsx:310、:371）。这与 ticket 最新裁定明确列出“标题、目标、完成条件命令”一致，旧的“两项输入”不能继续当作现合同或完成报告的承诺。新外部脚本显式检查这一点。 |
| design-integrity-review | NO_GO。只读核实后的成功有完整持久化事实支持，也没有 fallback 写入、重试、兼容分支、平行 API、策略引擎或另建存储。但 renderer 把主进程已确定的提交前输入拒收与不确定的 transport 失败合并，越过了 main 对提交阶段的事实所有权，见 P2。扫描器只定位当前未跟踪的第一轮复验脚本 catch，未将其当作候选缺陷，也未用扫描结果代替冻结 diff 审查。 |

## 本轮运行与原件

一次性源码均来自 `git archive`，未建 worktree。根目录 `/private/tmp/t106-review02-_vct1jzk`；Node `v26.5.0`。候选先运行如下检查，全部退出 0：

```sh
R=/private/tmp/t106-review02-_vct1jzk
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t106_creation.mjs" "$R/results/candidate-creation.json" "$R/candidate/workbench/app/main.ts"
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t091_pane_ipc.mjs" "$R/results/candidate-pane.json" --source "$R/candidate"
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t105_panes.mjs"
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t106_postcommit.mjs" "$R/results/candidate-postcommit.json" "$R/candidate"
```

前两项及窗格检查是实际 main/preload 加边界夹具，不是 GUI 或真实 socket 证明。提交后检查使用实际 main、daemon 认证/解码/处理、门禁与 SQLite；仅提供 Electron、PTY、socket 监听边界。触发器只阻断指定事件，SQL 五表计数独立确认提交事实，写命令均未重放。七场均 PASS：save-result、save-event-failure、save-readback-failure、save-before-write、save-conflicting-record、create-result、create-readback-failure。

另在 `/tmp` 的观察脚本添加三场独立边界，不改候选生产代码：

```sh
node --experimental-vm-modules "$R/probe-extra.mjs" "$R/results/extra-boundaries.json" "$R/candidate"
```

退出 0，三场 PASS：

- 保存已实际提交后，丢失响应并让 transport Promise 拒绝：card_show 核实已保存，禁止重放。
- create 已实际提交后同样丢失响应：status 核实完整 ready 任务，成功返回同一任务。
- SQL 触发器拒绝门禁的 created 事件，使先前 create_intent 已提交而 ready 事务回滚：独立 SQL 核实任务为 creating，结果保持 unknown，取消、重试和换目录均拒绝。

完整结果见临时目录 `results/index.json`、各 JSON、`probe-extra.mjs`、`mutations.json`。候选绿态的实际库夹具由原 runner 清理；旧候选和变异的红态实际库夹具分别保留在 `/private/tmp/t106-postcommit-4nDfgh`、`/private/tmp/t106-postcommit-7AmV7K`，未覆盖失败。首次解包脚本用了当前 Python 3.9 不支持的 tarfile filter 参数，已改为系统 tar；该设置失败没有算作产品红态。

FINDINGS:

### [P2] 确定发生在提交前的输入拒收，被当作结果未知锁住表单

位置：`workbench/app/main.ts:179` 与 `workbench/app/renderer.tsx:341`、`:351`、`:377`。

触发：正常选择仓库并填写有效项目号、目标、完成条件，标题输入三个空格后确认。标题 input 只有 required/maxLength，没有拒绝纯空白的 pattern；非空字符串即使全为空格，native required 检查也不会阻止提交。main 的 `!input.title.trim()` 在生成临时卡、调用任何门禁前执行，直接抛 `Invalid creation fields`。

实际 main 探针运行：

```sh
node --experimental-vm-modules "$R/probe-preflight.mjs" "$R/results/preflight-refusal.json" "$R/candidate/workbench/app/main.ts"
```

退出 1，业务断言为“确定提交前的拒收应保留可编辑、可取消草稿”。实际原件：

```json
{"input_title":"   ","rejection":"Error: Invalid creation fields","new_commands":[],"saved_count":0,"task_count":0}
```

这份探针执行实际 main handler；transport/Electron 为边界夹具，结果确认没有保存或创建调用。它不是 GUI 运行。后续 UI 行为由冻结源码直接确定：renderer 在调用 IPC 前无条件令 submitted=true，catch 收到上述异常后设置 persisted='unknown'，继而禁用 fieldset、取消和确认；Esc 也不能取消。main 的草稿实际仍为未保存，但 renderer 已没有可用的修正/取消入口。该 UI 路径已写入外部脚本，真实 GUI 复验本轮未运行。

预期：这类已知发生在提交前的业务输入错误应显示原因并允许用户修改或取消；通信丢失仍保持未知，不得通过重新启用所有异常的按钮来修它。影响是普通输入错误会把创建表单锁住，用户只能关闭窗口后重新开始；不是持久化数据损坏，因此列 P2。

最小修正方向：由 main 的提交入口把自身已知的提交前拒收结构化返回为失败且 persisted:false，renderer 沿已有结构化结果处理；保持未识别 IPC/transport 异常的 unknown 保护。不要在 renderer 解析异常文案猜阶段，也不要只补一个标题 pattern 而保留提交前失败合同缺口。现有提交后 P1 的只读核实与禁止重放必须继续通过。

COUNTEREXAMPLE:

三份变异各从候选 archive 原文解包，只改一个生产位置；候选测试和期待值保持不变。

```sh
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t106_postcommit.mjs" "$R/results/mutant-postcommit.json" "$R/mutant-postcommit"
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t106_creation.mjs" "$R/results/mutant-renderer-repo.json" "$R/mutant-renderer-repo/workbench/app/main.ts"
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t106_creation.mjs" "$R/results/mutant-silent-refusal.json" "$R/mutant-silent-refusal/workbench/app/main.ts"
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t106_postcommit.mjs" "$R/results/knownbad-postcommit.json" "$R/knownbad"
```

| 单处错误实现 | 结果 |
| --- | --- |
| mutant-postcommit：向 card_save 的提交前错误白名单加入 orchestration_failed，复现 P1 | 退出 1。四场在 test_t106_postcommit.mjs:103 的“必须只读核实”断言失败；实际已落库卡仍被返回 persisted:false。不是导入或夹具失败。 |
| mutant-renderer-repo：create 的 repo 从 draft.repo 改取 renderer 的 input.project 字符串 | 退出 1。实际 main 向 transport 提供错误目录，夹具的主进程所选目录断言拒绝；继而在 test_t106_creation.mjs:115 的本应成功提交断言失败。 |
| mutant-silent-refusal：card_validate 拒收改返 ok:true 且丢弃错误 | 退出 1。在 test_t106_creation.mjs:101 拒收应为 false 的业务断言失败。 |
| 未修改的旧候选 24cacef60 | 退出 1。七场均在只读核实断言失败；保存后失败与 create 后失败都被拒绝。 |

创建测试失败 JSON 的 status 仍为其原有 INCOMPLETE 格式；这里依具体业务断言和退出码判定“错误实现已拒绝”，未篡改 JSON 标签。oracle 来自裁定的确认边界、目录归属、拒收可见性与提交事实，不以候选自报或某个 status 字符串当成功证据。

LIMITATIONS:

- 已读取主控原件 `form-electron-01.json`：PASS，绑定旧候选 24cacef60、candidate_diff 为空，两次原生目录选择、真实空库/拒收/取消/注册/CLI 整记录及快照对照、模型回合 0、清理完成。本 reviewer 未亲眼观察该次操作；其健康路径不独自证明本次 P1 修复。
- 已读取主控原件 `postcommit-electron-01.json` 及 runner/driver：PASS，绑定当前候选 5036a8dc3、candidate_diff 为空、模型回合 0、清理完成。包含旧 GUI 红态与当前候选五种真实 GUI 故障，核对按钮、错误、五表计数和写命令一次调用；当前候选 create-result 已注册并显示列表。这是本候选真实入口的现有证据。该 runner 固定 driver 的主进程目录选择结果，未冒充新原生对话框证明；目录选择生产逻辑相对第一轮未变。
- 新增 `REVIEW-OUTSIDE-02.sh`，**本轮未执行**。执行主控可运行 `bash evidence/2026-10-19-batch17/T-106/REVIEW-OUTSIDE-02.sh`：固定 archive 本候选及旧候选，真实 GUI 补查默认卡的正常注册、缺命令/格式拒收/取消、标题目标 sentinel、路径注入及空白标题的提交前拒收，再复跑 GUI 提交后故障。当前候选预期在空白标题检查处 NO_GO 并停止；这不是已执行结果。无须人手操作对话框；新 summary 和故障原件留在新 `/private/tmp/t106-review-outside02-*`。脚本已通过 bash -n、内嵌 Python 3.9 AST/compile、UTF-8 无 BOM/LF 回读；这些静态检查不计作 GUI PASS。
- `project_map.py status --root .` 起止均退出 1：8 个稀疏 checkout 缺文件/断链诊断，stale living docs 0。`git ls-tree` 确认缺失的 findings 与 grilling 文件存在于候选 Git 对象。结果保存在临时目录 `results/project-map-final.txt`；本 checkout 的“0 问题”仍为 **INCOMPLETE**，本审查不替该票此完成条件签 PASS，不修改地图或补齐 sparse 文件。
- 本轮没有重跑截图、全站键盘/读屏、布局压力或性能测量，没有构建/安装应用，没有运行 agent/model CLI，没有变更用户全局配置。未申请升级、未使用问题面板、未调用 Herdr、未 commit/checkout/reset/stash/push。
- `git diff --check b0e12a88c 5036a8dc3` 通过。仅新增本报告与指定复验脚本；第一轮报告、脚本、两份主控 GUI 原件及原有未跟踪文件均保持原样。

RULE:

- 第一轮与本轮都涉及“失败”与“持久化事实”的混淆。本轮应在创建验收补上“非空但全空白标题 → main 提交前拒收 → 可编辑且可取消 → 修正后成功”的真实入口检查，并核对五表无增长；REVIEW-OUTSIDE-02.sh 已列出该场景。现有 test_t106_postcommit.mjs 的提交后触发器、只读核实与禁止重放/取消断言继续运行，避免修 P2 时重引 P1。不用新增提示词规则代替机械检查。

T-106 REVIEW NO_GO
