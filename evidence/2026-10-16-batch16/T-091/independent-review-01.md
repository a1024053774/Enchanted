# T-091 独立审查 01

总体：**PASS，绑定冻结候选 e4dcb2739af449396a3c6982e9826326d64a4369。** 原始红／绿态、身份与单帧、相关回归、CLI 版本、结构检查和完成条件拒错证据均已核对，未发现确认的候选缺陷。主控 #54 补交的 18 份计时原件证实：相同 8 秒输入下，起点和候选各 9/9 次触发 deadline；结合候选 30 秒正例完成及负例预算不变，接受仅三个质量正例的预算适配。M2/M3 命中预定业务断言；M1 更早被身份绑定断言检出，原 mutation-verdict=false 保留。PASS 是本候选的独立审查结论，认领、submit、验收、集成及 ticket 关闭仍由主控走唯一门禁；本 reviewer 未执行这些动作。

候选：`e4dcb2739af449396a3c6982e9826326d64a4369`。起点：`44bbb7828459d81fab0d46069a19d3dd515a7732`。仓库：`/Users/luckye/Documents/Code/a2a-wt-t091`，分支 `exec/t091`。审查角色来自主仓库 `.project-map/roles/reviewer.md`，为 fresh-context 只读 reviewer；未读取作者会话历史，未开子 agent。

本次只写此报告、`REVIEW-OUTSIDE-01.sh`、主控 #51 新授权的 `REVIEW-OUTSIDE-02.sh`，以及 reviewer 新建的 `/private/tmp` 目录。没有改候选，没有 commit、checkout、reset、stash、push、submit 或集成，没有启动真实 Claude/Codex，没有调用模型 API、写全局配置或请求沙箱升级。OUTSIDE-01 原脚本及外置失败现场保持原样。

## 判定来源与范围

答案从以下材料重建，worker 的 RESULTS、请求和脚本仅用于定位证据：

- T-091 Acceptance：起点红态；一个窗口同任务的两个主控与一个 worker；三份真实 snapshot 与进程身份；错 task／旧 launch 拒绝；原始单帧只含隔离窗口；相关正反例不退化；独立审查与地图检查。
- `native-cli-orchestration-2026-10-10.md` 第 1、5、9、12 节：任务包含多个会话窗格，启动记录与会话环境，唯一后台数据与门禁，S1/S4 的真实路径。第 5 节明确不写 CLI 全局配置。
- 主仓库收件箱 `20261017T131813Z-ideation-answer-001.md`：并发限一个 Electron、两个主控 CLI、一个受控 worker 窗格，Codex 会话不超过三个；记录会话和 Electron 数。
- 主仓库收件箱 `20261017T133907Z-ideation-answer-001.md`：用户选“A: 锁定改到 2.1.302 并改成配置读取 (Recommended)”；路径／版本来自配置，启动实际核对 `--version`，不符报错，不改全局设置、不关自动更新、不自动改用其他版本；红态、绿态、反例分别取证，不补称 PASS；T-078 的 2.1.296 证据保持原边界。

目标是核实这一个冻结候选及完成条件的拒错能力。非目标包括实现修复、改变验收、性能收益论证、T-093 真登录和项目集成。**Ubiquitous language** 沿用 CONTEXT；下文的窗口凭据 `window_id` 是每格的后台身份，不等同于 Electron BrowserWindow 数。

## Acceptance 逐条结论

| 条件 | 本 reviewer 当前结论 | 依据、已证实部分与缺口 |
| --- | --- | --- |
| 1. 起点一窗不能同时显示同任务三格 | PASS（现状红态） | 起点单 Terminal/单 section 的源码与 red-02 的三个后台 launch、进程记录、view.json 和原始 baseline-original.png 一致：后台有同任务两个主控和 worker，单个窗口只显示 worker。red-02 产品源码与起点相同；不是把任意退出 1 当红态。原 receiver 固定原生会话号的限制不作绿色身份正例。 |
| 2. 一窗同任务两主控加一 worker，身份正确 | PASS（green-02 所给边界） | 已直接读三份 snapshot/process、expected、view、独立输出流与 capture receipt，并查看三种尺寸原帧。task、角色/preset、launch、thread、attempt、原生会话及进程领导者相互对应；三格同时有可见终端区域，window_id 各异。具体身份见下一节。不是只看标题。 |
| 3. 第三格错 task／旧 launch 建窗及发凭据前拒绝 | PASS | 两份 green-02 refusal 分别是 launch_task_mismatch 和 Pane is not a current running session，windows_before/after 均为 [1]。orchestration-before-close 只有三个 window_opened，窗口关闭后恰好撤销这三个凭据。OUTSIDE-02 候选再次拒绝错 task／旧 launch，M2 删除预检后建出了第二个窗口，命中预定 third_stale_refused_before_window_and_credential 业务断言；正常收尾。 |
| 4. 原始单帧，只含隔离窗口，无拼图／顺次切换 | PASS（已给原件） | 三张绿色原帧已逐张查看；1440×900、1200×800、900×650 的 capture 均绑定 PID 88417、原生窗口 996，以 screencapture -l 996 捕获；Retina 像素分别 2880×1800、2400×1600、1800×1300。画面只含该窗口，三格同帧，布局与相应 view bounds 一致。原件及捕获链支持该结论，没有用拼图或新截图替换。 |
| 5. T-074/T-075 正反例与 T-078 主控／输入不退化 | PASS（所列合同与受控边界） | 已读 core-04 四套原方法的 8/9/18/1 结果、三种业务反例及四类 GUI -02 的 4/12/11/14 个检查，均与声明相符，正常套件 failure/error/skipped=0。产品版本对应已独立核对。补交对照在起点已复现 8 秒不足，三正例的 30 秒适配可接受，业务断言和负例期限保留；没有证明性能等价，也未重新运行供应商模型实验。 |
| 6. 独立审查通过；地图 0 problems | PASS | 本报告定稿为 PASS；M2/M3 预定真实入口变异和 M1 提前业务失败均已核对，预算依据已补齐。status 退出 0，Problems 0、Stale living docs 0；不替代后续门禁验收或集成。 |

## 已核对的原始身份与单帧

原件根目录 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/green-02/`，共同 task 为 `t091-three-91e0bcc6`：

| 窗格 | launch | shell / foreground leader | 进程边界 |
| --- | --- | --- | --- |
| 构思主控 | 3f876a9e-8e87-4e20-97d6-7dfb147611ab | 88374 / 88375 | /bin/zsh → 配置的 Claude 2.1.302 |
| 执行主控 | c6215593-c80f-403d-bcc8-f8a1757251b5 | 88387 / 88388 | /bin/zsh → 配置的 Claude 2.1.302 |
| 受管 worker | d10d8a1e-0948-4b9f-b0a0-a42e558eeb70 | 88350 / 88352 | /bin/zsh → 受控 codex-receiver，非真实 Codex |

三位 leader 均是各自前台进程组的领导者，父进程对应其 shell，failed 为 null；launch/session、native_session、thread 和 worker 当前 attempt 与独立 expected 一致。关闭 UI 后仍读到同一批 agent 身份，三个输入凭据则已关闭。原件是当时的进程事实，不宣称这些 PID 今天仍存活。

逐格原始输出与 Electron received.ndjson 的本 launch 数据流对应，只有 worker 含预先固定的输出 nonce；各 window_id 的 admitted sequence 分别从 1 连续推进。1440/1200 下是上方两个主控、下方 worker；900 下三行同时可见。身份字段完整换行，只有 worker 有输入焦点边线和文字。红态原帧则只有一个 worker 终端。截图只证明同时可见；交互及身份结论另有上述后台与进程读回支持。

## 身份、路由与结构审查

`main.ts:37` 的 target 从可信 Electron event.sender.id 查窗口，再核对 sender 对象和 mainFrame，最后只查该窗口的 panes Map。六条 handler 都经此入口；没有发现 renderer 传来的 task、launch、window_id 能替换它的路由绑定。未知 key 与另一窗口的 key 均不在本窗口 Map 内。preload 仅公开冻结的 paneKeys 及六个带 key 的方法，未把 operator 或 window token 暴露给 renderer。

`main.ts:47` 起序号及发送队列属于 PaneBinding，放行期间后续输入仍可使声明过期；renderer 的 EmptyInputDeclaration 来自该格 snapshot 的 launch、window_id、interruption 与 input_generation。每个 SessionPane 的输入失败会停止该格发送；输出检查 launch 和连续 byte offset。不能把同任务三个窗格误解为三格共用同一份输入身份。

**Tracer bullet**：候选的单格和多格共享现有生产通路；没有保留第二套单格 renderer。多格选取须当前运行身份，单格仍可查看历史只读输出，是明确的不同使用条件，并非新增兼容实现。

按 design-integrity-review 检查了 main/preload/renderer、claudeLaunch、panes/daemon 及测试适配器的候选差异。**Deep modules**：SessionPane 隐藏终端生命周期，target 隐藏窗口／窗格鉴别；未发现新增平行业务 API、版本扫描、重试、静默降级或无证据的兼容路径。窗口关闭时记录未确认输入／撤销错误后销毁窗口的处理在起点已存在；候选将其逐格执行，不能称为本票新引入的异常吞噬。startController 的 probe 异常被转为明确 Refusal，没有继续启动或选择别的版本。异步 IIFE 可改成 async 方法，但当前未形成可确认的业务或结构缺陷，不作阻断发现。

结构 scanner 返回空 findings；该工具只作定位，其输出不能代替上述冻结差异与调用链审查。已查范围内无确认的新增结构缺陷；要求的 UI／进程边界及拒错证据现已核对，受控 socket、任务状态宿主和未重跑供应商模型的限制如实保留。

## CLI 配置与版本证据

配置入口是 `gates/cli.ts:165` 读取 `--manifest` 指定的 JSON。`daemon.ts` 的 controller_start 将 manifest 传给 `Panes.startController`；`claudeLaunch.ts` 要求绝对 executable 与明确的三段 version，构造预期版本字符串。没有产品内扫描安装目录、回退 PATH 或自动挑版本的逻辑。

`panes.ts:79` 起先实际执行配置 executable 的 `--version`，期限 10 秒、输出上限 64 KiB；缺路径、probe 失败与版本不符分别拒绝。比较通过后才登记 launch、创建 trace 并启动 PTY。await 后紧接同步 preset 所有权检查，可拒绝并发启动占用同一 preset。探测 argv、stdout/stderr 和观测版本进入记录。候选去掉了原先的 DISABLE_AUTOUPDATER；配置及角色环境均指向隔离 HOME，未发现全局设置写入代码。

已独立重跑实际 builder／方法的给定 IO 检查：配置路径、单次 probe、配置值改变预期、缺路径、probe 错误、版本不符、记录版本及并发 preset 唯一性均通过；删比较的变异命中“版本不符必须拒绝”。这是 L1 证据，不作真实进程或 daemon 的证明。

green-01 的缺失 2.1.296 是脚本先行 probe 的环境红态，并未走产品 controller_start，不能用来证明产品错误码；旧 builder 拒绝新配置的 red-01 只证明配置接口红态。现已核对 green-02 的真实 2.1.302 启动记录、--version argv/stdout 与两个产品拒绝。OUTSIDE-01 又补跑真实 CLI→daemon→controller_start→exec/PTY：候选的缺路径、版本不符、拒绝前不建 pane，以及两个明确配置正例全部通过；M3 删除比较后错误接受版本不符配置，命中 mismatch_refused，正常收尾。该新增实跑只运行自编译 C 程序；门禁 task 状态由测试宿主注入，不证明真实模型或门禁任务生命周期。

## 回归、预算与旧断言

已重新执行并保存逐条 argv/退出码，见 `/private/tmp/t091-review-01-umhhuu68/static-version-checks.json`：

- `git diff --exit-code f20a74ada e4dcb2739 -- workbench/src workbench/app acceptance`：退出 0、无差异。green-02 与四类 GUI -02 的产品源码仍对应候选。
- `git diff --exit-code 44bbb7828 e4dcb2739 -- workbench/src/gates acceptance`：退出 0、无差异。
- `git diff --exit-code 3db9b6def e4dcb2739 -- workbench`：退出 0、无差异。3db9b6def 到冻结仅六份证据／请求材料变化。
- f20a74ada 之后仍修改了 README、daemon_acceptance_adapter、run_daemon_acceptance 及两份测试；没有声称整个 workbench 或所有回归工具都未变。

core-04 已逐项核对 business classifier 前检、coop 8、recovery 9、run 18、CAS 1，以及 fence/CAS/lock 三个业务反例，四套正常方法 failure/error/skipped 均为 0。三种变异子运行各为退出 1、一个 assertion failure、0 error/skipped，并实际加载对应 mutant core。fence 错误接受 fence=32 而当前 fence=1 的交付；CAS 仍绑定旧 G、保留同一 C，丢失新的外部祖先，oracle 次数 1 而非 2；lock 并发命令未 operation_busy 且启动了第二次 oracle。这些是合同违反，不是环境失败。四类 GUI 原检查数分别 window 4、runtime 12、input-failures 11、worker-inbox 14，全 PASS；后面三类 cleanup_complete=true。读了子结果与原断言数据，未只读顶层 PASS，未重开已停止的 WAL 库。

**8→30 秒的判断：接受仅三个质量正例的预算适配，依据已补齐。** 改动确实放宽这三个正例的测试输入预算，且只在 `daemon_acceptance_adapter.py:486` 匹配三个具名方法、原请求为 8 秒的情况；负例、其他显式预算和产品期限未改。`test_t091_quality_run_budget.py` 的预期 30 只证明映射实现，单凭它或“起点没有计时”都不能接受；这也是此前保持 INCOMPLETE 的原因。

主控 #54 补交 `quality-timing-01/` 后，本 reviewer 读取了归档脚本、两版源码、18 次 config／child.run／原始命令和回包／停机前 readback／退出及归档记录，直接从 events 复算，未调用作者的 timing() 作为判定依据。候选采样仅在进程内删除 DaemonRun.run_args 覆盖，两边均回到各自原 RunCLI.run_args；业务方法不替换，磁盘源码不改。逐文件比较确认起点 322 个、候选 332 个相关源文件与各自 git archive 原文一致；原 acceptance/test_run_e2e.py、门禁 core、legacy_quality_driver 与依赖锁两版相同。实际 daemon host 加载的 core 路径均属于相应版本。3db9b6def 与冻结 e4dcb2739 的 workbench/acceptance 无差异，因此该对照适用于本审查候选。

每方法每版本三次，按轮次与方法交替先后顺序，18 个独立进程串行；实际 run argv 及开始／结束事件均明确 wait_seconds=8，run_id/task 逐项对应。18 个 CLI 回包均退出 1、ok=false、error=run_deadline、outcome=deadline；各原方法仍记录一个 failure、0 error/skipped、original_test_status=INCOMPLETE，没有把采样完成的 PASS 当成原正例通过。收尾及停止后归档记录完整。

| 原质量正例 | 起点：deadline／样本；事件区间（秒） | 候选：deadline／样本；事件区间（秒） |
| --- | --- | --- |
| test_run_entry_point_completes_registered_task | 3/3；8.607–10.032 | 3/3；8.776–9.600 |
| test_transient_tool_activity_keeps_same_thread_owner | 3/3；8.852–10.793 | 3/3；8.688–10.092 |
| test_matching_reclaim_guard_is_idempotent_after_automatic_success | 3/3；8.660–8.714 | 3/3；8.700–8.794 |

这足以确认：**在本机本轮受控质量场景中，8 秒不足已在起点代码上复现，不是 T-091 才新出现的失败现象。** 但这些是触发期限后的结束事件区间，不是正常完成耗时；deadline 截断了完成过程，不能凭区间重叠宣称两版性能统计等价、没有任何幅度的性能变化，或历史上所有起点运行都会失败。

可接受 30 秒还基于独立的业务证据：已复核 core-04 三个正例各自 wait_seconds=30、outcome=completed，原业务断言全过；无 submit 超时负例仍实际使用 2 秒，oracle 失败场景仍实际使用 8 秒并 fail-closed。ticket/spec 没有要求完整质量正例必须在 8 秒完成；调整的是有真实 reviewer／executor 往返的夹具等待输入，没有放宽身份、提交、验收、集成、回收的预期，也没有动态加时、重试或产品期限变更。30 秒不是由这些 deadline 样本推算出的最优阈值，不作可靠性、吞吐或性能收益主张。

原件位于 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/quality-timing-01/`；reviewer 的独立复算、源码对应和 30 秒绿态核对记录在 `/private/tmp/t091-review-final-yjd3thgf/`。新增计时脚本与 preflight 为 worker 未提交的证据补充，未修改或重新冻结候选；本 reviewer 只读它们，没有运行涉及夹具 commit/submit/integration 的采样。

**旧 bridge 断言修订：静态及隔离反事实 PASS。** 起点原 preload 已公开 snapshot、output、input、beginComposition、releaseQueue、observeFocus，原测试却只允许 output/snapshot。本 reviewer 用起点原文重新执行旧断言，确实失败；收据在 `/private/tmp/t091-review-01-umhhuu68/baseline-bridge-replay.json`。候选 `test_electron_e2e.py:174` 精确枚举七项接口，新增项仅 paneKeys，并继续单独要求 Node 为 undefined；不是改成数量或子集检查。起点探针的 node 字段由 VM 提供，不能证明真实 Electron 的 Node 隔离；也没有执行完整起点 window suite。现已读 window-regression-02 的真实 electron_real_window 检查及原断言数据，候选隔离检查通过。

## 完成条件与变异检查

用 `git archive e4dcb2739` 解包到 `/private/tmp/t091-review-01-umhhuu68/candidate`，未建 worktree。先运行候选，再在三个独立副本各改一处。预期来自 ticket 的身份／选取约束和用户的版本裁定。原始 stdout/stderr、JSON 和精确替换保存在同目录 `mutations.json` 及相应文件，未覆盖旧结果。

候选命令均退出 0：`node --experimental-vm-modules <candidate>/workbench/tests/test_t091_{pane_ipc,claude_version,start}.mjs <新报告路径>`。这三项边界均由 VM／测试提供，属于逻辑证据。

| 变异 | 单处错误 | 相同逻辑入口结果 | 真实入口现状 |
| --- | --- | --- | --- |
| M1 | main target 忽略 key，总取 Map 第一格 | 退出 1；`Unregistered pane key was accepted` | OUTSIDE-02 退出 1，实际先失败于 same_window_three_launches。预检仍读三份不同 launch，但三个 keyed snapshot 都被错误路由到 ideation，只签发一个凭据，真实命中“各格绑定正确 launch”的既有业务断言。unknown_key_refused 未到达；原 mutation-verdict=false 保留，不能改称预定断言通过。 |
| M2 | 删除多格选取时 requireCurrentPane 调用 | 退出 1；错误第三格的 `assert.rejects` 失败 | PASS（命中预定拒错断言）：OUTSIDE-02 候选先通过八项；M2 前五项通过，旧 launch 选择却创建了第二个 BrowserWindow，third_stale_refused_before_window_and_credential 失败。mutation-verdict=true，cleanup_confirmed=true；不是环境失败。 |
| M3 | 删除版本比较条件 | 退出 1；`Configured version mismatch must be rejected` | PASS（变异被拒错检查检出）：OUTSIDE-01 候选版本入口先退出 0；M3 版本不符请求错误返回退出 0，随后 reviewer 的 mismatch_refused 断言失败，子运行退出 1，cleanup_confirmed=true。不是环境失败。 |

每个真实入口均先确认候选通过，再运行错误副本。按运行前的严格分类规则，只有退出 1、命中预定业务断言且收尾确认才记为 true：M2/M3 满足，已达到至少两项；M1 原 false 不改。本 reviewer 另确认 M1 属于更早的业务拒错，证据来自运行前已存在的三格身份断言及原始 transport，非事后新造 oracle；不把这一观察替换成其预定未知 key 断言的实跑结果。依赖缺失、构建失败、硬超时、测试宿主错误均不算拒错证据。真实 UI 变异不是全套真实 daemon/PTY 场景，不能把其边界合并冒称端到端全部真实；原 green-02 另提供已核对的完整依赖边界。

## OUTSIDE-01 超时诊断与 OUTSIDE-02

OUTSIDE-01 输出根为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/review-outside-01-20261017T160603Z/`。归档核对退出 0，版本候选退出 0，M3 子运行退出 1 且 mutation-verdict 为 true，候选 UI 标准构建退出 0。candidate-ui 45.943 秒后退出 124，之后没有运行 M1/M2；summary 保持 INCOMPLETE。主控 #51 报告无残留 Electron/daemon，本 reviewer 未另做实时进程查询。

**根因在 reviewer 脚本。** candidate-ui-results/transport.ndjson 仅有 worker、executor、ideation 三次预检 snapshot，无 window_open；hard-timeout.json 的 checks=[]；stdout/stderr 为空。按冻结 main 的实际控制流，三次预检通过后，会先设置路径，再等待 app.whenReady，尚未执行 BrowserWindow 构造。审查脚本却在 ESM 入口顶层 await run，令入口模块直到 run 完成才完成求值。Electron 43.4.1 的 [default_app/main.ts](https://github.com/electron/electron/blob/v43.4.1/default_app/main.ts) 等待应用模块 import；[lib/browser/init.ts](https://github.com/electron/electron/blob/v43.4.1/lib/browser/init.ts) 在入口 import 完成后才调用 appCodeLoaded。这与 main 等 ready 形成等待环。候选自己的 CLI 入口则调用 run(...).catch(...)，没有顶层 await；已有 green-02 及四类 GUI 回归也不是这个阻塞的启动方式。不能把本次脚本错误归到候选。

OUTSIDE-02 只修 reviewer 生命周期：用未等待的 async main() 启动测试，使入口模块完成求值；Electron 路径先同步设为隔离目录；记录 entry_evaluation_complete、app_ready、whenReady、建窗、加载和 run 阶段。八项业务断言以及 45 秒应用内／65 秒外部硬期限均不改，没有用加时掩盖卡住。现已在实际阶段日志中观察到 entry_evaluation_complete→app_ready→when_ready_resolved→browser_window_created→product_run_completed，候选运行 1.558 秒退出 0，证实了脚本修正后的绿态。

实跑输出为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/review-outside-02-20261017T161531Z/`。候选、M1、M2 的标准构建均退出 0；各副本来自同一冻结 SHA，逐文件比较 app/src 的 35 个文件确认候选未变、M1/M2 各只改 main.ts 指定一处，记录在 `/private/tmp/t091-review-52-zie3sji0/source-comparison.json`。候选退出 0，八项检查全 true：三格 launch 正确、凭据各异、未知 key 拒绝、序号和输入目标各异、放行声明各异、旧 launch／错 task 建窗前拒绝、另一窗口 key 拒绝。原始 snapshots、transport 中三个 window_id 的输入 sequence=1 与放行 sequence=2 逐格对应。

M1 退出 1，result.json 的 AssertionError 为 same_window_three_launches，checks 只到这项且为 false。transport 显示建窗前确实读过三份不同 launch，建窗后的 keyed snapshot 却全部选择 ideation，只 window_open 一次；因此是被忽略 key 引起的真实身份错绑，不是依赖或宿主失败。但它没到预定 unknown_key_refused，mutation-verdict=false 与 summary 总退出 1 均原样保留，不回改为 PASS。

M2 退出 1，前五项通过，AssertionError 精确为预定 third_stale_refused_before_window_and_credential；阶段日志在旧 launch 的预检请求之后出现第二个 BrowserWindow，表明拒绝没有发生在建窗前。mutation-verdict=true。M2 此次在旧 launch 处已停，变异上的错 task 子例未执行；错 task 的正常候选和 green-02 反例已有独立证据。

三个子运行 cleanup_confirmed=true，after-processes 均为 remaining=[]、exit_confirmed=true；主控 #52 同时报告没有残留 Electron/daemon。OUTSIDE-02 实际三个 Electron 串行、峰值一个，无 daemon、PTY、真实 CLI 或模型调用。结果总退出 1 是 M1 的严格断言名分类不匹配，不能解读为候选失败。M2/M3 已给出两项符合预定规则的真实入口反事实，不为“清理总退出码”而重跑或改写旧收据。

## 审查结论与交接

审查定稿为 PASS，无确认的候选产品缺陷，无剩余的本次审查补证项。reviewer 的启动等待环已修正并取得真实绿态；M1/M2/M3 原件与分类已核实，M1 未命中预定断言的边界如上保留。8→30 秒依据已由起点／候选同输入对照及现有 30 秒业务绿态补齐，接受范围仅限三个质量正例的夹具预算。

OUTSIDE-01 实际启动一个 Electron；版本正例峰值两个受控 C/PTY，M3 另一次串行运行。OUTSIDE-02 实际启动三个串行 Electron，无 daemon/PTY；两轮合计四次 Electron 启动，峰值一个，真实 Claude/Codex/模型调用均零，新增 agent 会话零。当前 reviewer 本身是一份 Codex 会话，未创建其他会话；不据此推断机器上其他会话的总数。

主控另行运行的 quality-timing-01 为 18 个串行单方法采样进程，每个使用独立夹具和受控 worker/reviewer；Electron、真实 CLI、供应商模型调用和新增 Codex 会话均为 0，退出／凭据清理及归档记录已读。本 reviewer 没有启动这些进程。采样完成的 PASS 与 18 个原正例的 deadline 失败分别保留。

OUTSIDE-01 将原始截图原样复制到 `/private/tmp/t091-outside-01-nxac2w44/original-frames`，本 reviewer 已逐张查看；没有裁切、改图、拼接或重新截图。OUTSIDE-02 的 summary、三个 result、mutation-verdict、stages、transport、oracle、snapshots、构建／运行命令和收尾记录已逐项读取。两轮 raw 结果均保留，尤其不把 script summary 的 INCOMPLETE 改写成 PASS。quality-timing-01 的 18 份原件独立复核记录另存，不回改既有 deadline 或旧报告收据。

报告及脚本已按 UTF-8 无 BOM 保存并回读；候选范围未改。OUTSIDE-01 前的收口记录在 `/private/tmp/t091-review-01-umhhuu68/close-checks.json`，OUTSIDE-02 交接记录在 `/private/tmp/t091-review-02-ldhrox6z/close-checks.json`；主控 #52 的阶段定稿检查保存在 `/private/tmp/t091-review-52-zie3sji0/close-checks.json`，本次最终收口检查在 `/private/tmp/t091-review-final-yjd3thgf/close-checks.json`。status 退出 0、Problems 0、Stale living docs 0，HEAD 仍是冻结 SHA。保留 worker 新增的未提交计时脚本／preflight，本 reviewer 未改动它们；没有执行所禁止的动作。

T-091 REVIEW PASS
