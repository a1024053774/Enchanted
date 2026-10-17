# T-091 独立审查请求 01

日期：2026-10-17。task `T-091`，attempt `a1`，ticket ready_rev 1。worker `s16-t091`；当前 launch `launch-71afbd1600cb451a9d9354aa7768e72b`，受管 session `d4277ace-1dde-425b-99b8-8988f1df751f`，原生 session `01a14a05-4472-70e1-af77-58414340c1ee`。模型配置 gpt-6.1-sol／xhigh，codex-cli 0.163.0；该配置不作实际供应商 tier 的证明。

请求执行主控新开干净、只读的 reviewer 会话，对本次冻结候选给出独立结论。worker 当前整票状态为 **INCOMPLETE：运行证据已齐，最终独立审查与门禁验收未完成**。本请求不代替验收、submit、integration 或 ticket 关闭。

## 冻结对象与范围

代码候选：`3db9b6def91826d5a52dd02590c559b0c4ce35a0`。最终审查对象是**包含本请求的冻结提交**，其完整 SHA 由 worker 的 `T-091 FROZEN <sha>` 交接、主控转发给 reviewer；相对代码候选只更新 RESULTS、新增本请求、core -04 两份收据及 freeze-checks-01／02.json。请先核对这个差异，再绑定最终 SHA 写审查结论。

| 版本 | 用途及证据边界 |
| --- | --- |
| `44bbb7828459d81fab0d46069a19d3dd515a7732` | 任务卡起点 main；现状红态及旧 bridge 断言的比较基准 |
| `6974c2aad1233133264b7448e1277cd19fa0b6ba` | red-02 实跑脚本；当时产品源码与起点相同 |
| `06575f5dc4f6a0d2cd264922158343952d0a0c21` | tracer-01 单格真实读回；证据提交 `3ac3edc92afdd40f31926b94d83fdba4c8c5bf65`，只证明单格 Tracer bullet |
| `5d096caa2d690fe172ba8487226e8b16cf95950a` | green-01 缺失旧 CLI 路径与回归 -01 失败现场 |
| `f20a74ada49564499691cd14cf019f8cec448db1` | green-02、window／runtime／input-failures／worker-inbox 回归 -02 的真实 PASS 候选 |
| `3db9b6def91826d5a52dd02590c559b0c4ce35a0` | core-regression-04 真实 PASS 候选，含三项正例预算适配与 CAS 分类器修正 |

主控 #25 已核对，worker 本轮也执行 git diff 确认：f20a74ada→3db9b6def 的 `workbench/src/`、`workbench/app/`、`acceptance/` 无变化。因此上述 GUI 证据与当前产品代码对应；不是把旧版本所有结论无条件沿用。[冻结前检查记录](freeze-checks-02.json) 保存这一范围的命令与结果，并分别核对 GUI 原测试／驱动及包装器 GUI 分支；[首次核对记录](freeze-checks-01.json) 保留把整个包装器误纳入未变范围的失败。原业务 acceptance 源码和门禁源码没有修改。

目标与非目标以 [任务卡](task-card-T-091-1.md)、[ticket](../../../.project-map/tickets/T-091-single-window-multi-pane.md)、[已确认界面方向](UI-DIRECTION.md) 为准。实际产品改动为：重复 --launch 的单窗口入口；main／preload 按 sender 窗口与 pane key 路由；renderer 的独立 SessionPane 与响应式三格布局；daemon 投影 preset；用户裁定 A 的主控配置／版本核对及直接调用方。沿用既有输入、输出与唯一门禁，没有改门禁、紧急停止或收件箱语义。`workbench/tests/` 的启动、驱动、收尾、采集与回归包装器改动也属于审查范围。

## Ticket Acceptance 逐条证据

以下 PASS 是相应运行证据的状态；第六项仍待本次独立审查。完整历史在 [RESULTS.md](RESULTS.md)。外置根统一为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/`，下表中的运行目录均位于该根下。

| Ticket 条件 | 当前证据与核对入口 | 边界／状态 |
| --- | --- | --- |
| 1. 起点 main 不能在一个窗口同时显示同任务三格 | [red-02.run.json](red-02.run.json)、[归档清单](red-02.archive.json)、[原帧指针](red-02.single-frame.pointer.json)；外置 `red-02/expected.json`、三个 snapshot／process、view.json、baseline-original.png | 有效红态：后台有三份启动身份，实际一个 BrowserWindow 只有 worker 格，expected=3、observed=1、red_observed=true。原顶层 INCOMPLETE／rc 1 是合同预期失败，保持原值 |
| 2. 一窗同任务两主控和一 worker，各自正确绑定 task／角色／launch，三份真实快照与进程核对 | [green-02.run.json](green-02.run.json)、[只读对账](green-02-readback.json)、[归档清单](green-02.archive.json)；外置 `green-02/expected.json`、ideation／executor／worker 的 snapshot.json、process.json、两个 launch.json、三个 view JSON | PASS。任务 `t091-three-91e0bcc6`；构思、执行、worker launch 分别为 `3f876a9e-8e87-4e20-97d6-7dfb147611ab`、`c6215593-c80f-403d-bcc8-f8a1757251b5`、`d10d8a1e-0948-4b9f-b0a0-a42e558eeb70`。三份 window_id、输出流、输入序号独立；不是凭标题判断 |
| 3. 第三格错 task 或旧 launch 被拒，不用拼图或顺次切换冒称同屏 | 外置 `green-02/wrong-task.refusal.json`、old-launch.refusal.json、old.snapshot.json、原始 view／capture；同一 run 的检查与输出／输入 oracle | PASS。错 task 为 `launch_task_mismatch`；同任务历史 attempt 的旧 launch 为 `Pane is not a current running session`，两者均未建新窗口或签发新凭据。当前三格来自同一 BrowserWindow |
| 4. 只截隔离窗口的原始单帧 | 外置 `green-02/green-original.png`、green-1200x800-original.png、green-900x650-original.png 及各自 `.capture.json`；red／tracer 原帧另有仓库指针 | PASS。三张不同尺寸原始单帧，捕获 argv／窗口归属保留，未裁切拼接。主控 #21 看过 1440×900 和 900×650 原帧，确认身份完整、只有 worker 格有焦点；worker 此轮只读对账 JSON，不冒称另做屏幕观察 |
| 5. T-074／T-075 正反例与 T-078 主控／输入行为不退化 | 四类 GUI -02 和 core -04，详见下表；[pane-ipc-takeover-01.json](pane-ipc-takeover-01.json)、[t078-controller-window-01/results.json](t078-controller-window-01/results.json) 为补充给定边界证据 | PASS（所列回归）。runtime 覆盖固定注入、lateStop／Esc／release 等已有合同；core 覆盖原门禁正例与 fence／CAS／lock 业务反例。没有重跑 T-074 供应商模型实验，不将局部逻辑检查称为真实 CLI 回归 |
| 6. 独立审查通过；project_map.py status 0 problems | 本请求待主控派发；[冻结前检查记录](freeze-checks-02.json) 保存 status 输出 | INCOMPLETE：独立审查未运行。ticket 保持 open，worker 未勾验收框；既有工具审查不代替本次最终审查 |

## 真实回归与分类器证据

| 实跑 | 结果／入口 |
| --- | --- |
| window-regression-02 | PASS／rc 0，4 项；[run](window-regression-02.run.json)、[archive](window-regression-02.archive.json) |
| runtime-regression-02 | PASS／rc 0，12 项；[run](runtime-regression-02.run.json)、[archive](runtime-regression-02.archive.json) |
| input-failures-regression-02 | PASS／rc 0，11 项；[run](input-failures-regression-02.run.json)、[archive](input-failures-regression-02.archive.json) |
| worker-inbox-regression-02 | PASS／rc 0，14 项；[run](worker-inbox-regression-02.run.json)、[archive](worker-inbox-regression-02.archive.json) |
| core-regression-04 | PASS／rc 0，共八项：business_classifier_preflight，coop／recovery／run／cas 原套件（8／9／18／1 原方法，全部零 failure/error/skipped），fence／CAS／lock 业务反例；[run](core-regression-04.run.json)、[archive](core-regression-04.archive.json) |

每个外置同名目录保留完整命令、stdout／stderr、原断言输出、停机前读回及原夹具副本。core -04 三个变异子运行均加载指定的变异 core，实际一个原测试失败、0 error/skipped，最终由各自 `<name>.business-counterexample.json` 分类通过；变异子运行本身仍是 INCOMPLETE／exit 1。四组正常套件的最终状态看子目录 `run.json`；`test-result.json` 是最终判定前的阶段快照，不单读其初始化 status。

core -03 的 CAS 已实际触发三项业务违反，旧分类器查找过期 claim 导致漏判，lock 未执行，原顶层仍 INCOMPLETE。新分类器依照原 CAS 合同及 T-078 补判条件，要求同一原方法、指定 core、零 error/skipped、新 G 未绑定且 C 未变、外部祖先丢失、oracle 未重验同时成立；不能仅凭 rc 1 通过。core -04 的六个 CAS contract_checks 全 true。补充反事实为 [cas-classifier-green-04d.json](cas-classifier-green-04d.json)：16 组独立输入，拒绝旧分类器及“任意失败即通过”的削弱变异；该检查已接入 core 的自动前置检查。详情和原失败索引见 [core-regression-03-diagnosis.json](core-regression-03-diagnosis.json)。未改原 CAS 断言。

回归 -01 中 core 是旧方法名审计过时，window 是驱动把整页文本覆盖为单格文本，另外三类是停止后重开 WAL 库采集失败；修正位于包装器／驱动／采集层。统一采用原测试已有的停机前读回文件，没有增加 immutable fallback。window 额外保存同源事件读回；除下一节说明的旧 bridge 断言修订外，原业务预期没有为通过回归而放宽。旧 -01 记录完整保留，详见 [regression-01-diagnosis.json](regression-01-diagnosis.json) 和 RESULTS。

## 用户裁定 A：主控 CLI 配置与版本核对

授权来源为收件箱 `20261017T133907Z-ideation-answer-001`，执行主控 #18 逐字转达：

> 主控 CLI 版本不再写死路径，从配置值读取；启动时实际跑一次 --version 核对，不符就报错；配置值先设 2.1.302；T-078 的证据仍绑定 2.1.296，在 T-091 Resolution 里写明。不动用户全局设置、不关自动更新。这是产品行为改动，须有红态（锁定版本缺失时起不来）、绿态与反例（版本不符被拒），不得补称为 PASS；自动更新以后再删版本时应是清楚的报错而非静默起不来。

实现入口为 `workbench/src/claudeLaunch.ts`、`panes.ts` 的 startController 及 daemon 的直接调用方：读取每次启动 manifest 的明确 executable／version；先在对应角色的隔离环境实际执行一次 --version，期限 10 秒、输出上限 64 KiB，通过后才登记 launch 并启动 PTY。实际 argv／版本／stdout／stderr 保存于启动证据。错误码分别为 `controller_executable_missing`、`controller_version_probe_failed`、`controller_version_mismatch`。不扫描版本、不 fallback、不改全局配置、不关闭自动更新；等待探测后再同步核对 preset 所有权。

| 要求 | 证据与实际边界 |
| --- | --- |
| 红态：锁定旧版本缺失时起不来 | [green-01.run.json](green-01.run.json)、[archive](green-01.archive.json)，旧候选 5d096caa2 的脚本实际调用缺失的 2.1.296 --version，FileNotFoundError，Electron／主控启动均 0。这是建窗前的脚本／环境红态，尚未调用产品 controller_start，不能称其证明了产品错误码；[claude-version-red-01.json](claude-version-red-01.json) 另证明旧硬编码产品拒绝新配置，是给定 IO 边界的红态 |
| 绿态：明确配置 2.1.302，核对通过，主控启动 | green-02 PASS。脚本开始的真实 --version 以及两个主控在产品 startController 中的各自探测成功；真实 CLI 两个均为 2.1.302，原始输出在 run／launch 记录，三份身份读回见上表 |
| 反例：路径不存在 | 外置 `green-02/missing-cli.refusal.json`，真实产品入口返回 `controller_executable_missing`，没有新增 pane_started；不换用其他已装版本 |
| 反例：实际输出与配置不符 | 外置 `green-02/version-mismatch.refusal.json`，真实产品入口返回 `controller_version_mismatch`，没有新增 pane_started |
| 删除 --version 核对的变异必须被拒 | [claude-version-green-04.json](claude-version-green-04.json)，8 项 PASS；检查执行真实 builder／启动方法，删除生产版本比较条件的变异被“版本不符必须拒绝”断言拒绝。IO 由测试提供，未额外启动真实变异 CLI，不把此逻辑变异冒称现场实跑 |

T-078 历史纯配置夹具仅补显式 version=2.1.296 以满足新接口，原预期不改。**T-078 已有实跑证据和 red-02 仍绑定 2.1.296 及各自代码版本；green-02 使用 2.1.302。** 该区别已写入 T-091 Resolution；没有回改旧证据或把新结果补到旧版本上。

## 三个质量正例：8 秒改为 30 秒的依据与边界

core -02 在原正常完成方法缺少最终提交 ref 处失败。停机前事件显示配置 wait_seconds=8，run_started→run_finished 9.266 秒时以 waiting_executor／run_deadline 结束，随后才发生 review_reclaimed／integrated；事后 task accepted 不能补判原 run 自动回收成功。[core-regression-02-diagnosis.json](core-regression-02-diagnosis.json) 保留原失败。

最小变更仅在 `DaemonRun.run_args` 为以下三个走完整质量串、原请求为 8 秒的正例显式配置 30 秒，并记录 `quality_run_wait_budget` 的原值、实际值与理由：

- `test_run_entry_point_completes_registered_task`
- `test_transient_tool_activity_keeps_same_thread_owner`
- `test_matching_reclaim_guard_is_idempotent_after_automatic_success`

未 submit 超时负例仍 2 秒，oracle 失败仍 8 秒，重复 run 原 30 秒及其他显式预算保留；没有重试、动态延长或产品期限改动。原 acceptance 源码未改。[quality-run-budget-green-03.json](quality-run-budget-green-03.json) 的七组配置检查拒绝旧适配器，也拒绝把所有预算都改成 30 秒的变异；core -04 最终实际跑完 18 个原方法。

**没有起点 main 上同一方法的计时证据，不能断言起点也会超时。** 起点 44bbb7828→f20a74ada 的 gates/core、legacy_quality_driver、test_run_e2e、daemon_acceptance_adapter 源码相同，仅能说明质量串和旧预算已存在。候选 core -03 用 30 秒完成，run 事件区间 15.131 秒；与 core -02 的 9.266 秒都不是完整方法耗时，也不是起点对照。边界见 [baseline-timing-evidence-04.json](baseline-timing-evidence-04.json)（INCOMPLETE，baseline_same_method_executed=false）。这里不主张 T-091 导致性能回退，也不主张性能改善。

## test_electron_e2e 旧断言为何修改

主控 #11／本对话 #40 裁定：原 `test_electron_e2e.py:170` 是 T-078 后过时且不受 T-080 保护的断言，允许先在起点留证，再按真实接口精确修正。[baseline-bridge-assertion-01.json](baseline-bridge-assertion-01.json) 使用起点 44bbb7828 的原 preload 与原断言实际单独执行，原断言 FAIL：它只允许 output／snapshot，原 preload 已公开 snapshot、output、input、beginComposition、releaseQueue、observeFocus 六个方法。该探针没有运行完整起点 window suite。

当前断言要求排序后的接口**精确等于** beginComposition、input、observeFocus、output、paneKeys、releaseQueue、snapshot，并继续要求 renderer 的 Node 为 undefined；paneKeys 是 T-091 新增的窗格选择入口。没有改成宽松数量比较或跳过检查。当前完整真实 window-regression-02 的四项原检查已 PASS；本次预算和分类器改动后产品／窗口代码未变。

## 收尾、证据归属与已知限制

green-02：Electron 1、真实 Claude 主控 CLI 2、受控 receiver 共 3 个串行且峰值 1、读屏 30 次、截图 3 张；真实 Codex CLI 启动 0、供应商模型回合 0、假 Messages POST 0。没有复制 auth、没有向供应商发模型请求。receiver 只提供确定的终端／身份／输入收据边界，不能代表真实 Codex 推理、登录或 supplier tier。主控负责场景外已有 Codex 会话总数的逐场核对，worker 不以局部夹具数量推断全机总数。

green-02 的 cleanup_complete／archive_complete 都 true，关闭窗口后原 agent 仍存活，再停后台；GUI 四类 -02 均 archive_complete=true；core -04 无 Electron／供应商 CLI／读屏／截图，archive_complete=true。输出与读屏有脚本额度，完整输出落文件，不灌入 Terminal。core -04 九份夹具共 3,623 文件条目、255,327,757 字节、三条链接，逐份 comparison=true，原目录保留。大块证据只在外置盘，仓库为摘要／清单；具体重放命令在对应 run.json、[THREE-PANES-RUN.md](THREE-PANES-RUN.md) 和 [REGRESSION-PLAN.md](REGRESSION-PLAN.md)，重放必须使用新输出标签与主控批准。

系统 IME 不在本票范围；合成 composition 检查不能证明系统 IME。真登录为 T-093，未纳入本次验收。没有可靠性、吞吐、成本或内存改善的独立对照实验。T-078 旧证据版本边界和起点计时缺口如上，不补称 PASS。

red-01／close 系列、green-01、回归 -01／core -02／core -03 的失败原件保留。先前 [three-pane-acceptance-audit-01.md](three-pane-acceptance-audit-01.md) 为 FAIL（收尾标志缺陷，后已修正并留反事实），[version-wrapper-acceptance-audit-02.md](version-wrapper-acceptance-audit-02.md) 为当时证据不足的 INCOMPLETE；两者都不是本次最终独立审查 PASS。

请 reviewer 只读审查最终冻结 SHA 的代码、验收面改动和原始证据，重点核对三格身份／输入隔离、版本探测确实先于登记／PTY、原断言未被绕过、变异确实命中业务及收尾条件。若需要新增运行，先由执行主控安排新标签和既定资源范围；不要操作用户应用、全局设置或其他会话。请将审查结论绑定最终 SHA，逐项报告 PASS／INCOMPLETE／BLOCKED／NO_GO；worker 冻结后不再改动，后续由主控走独立审查和唯一门禁。
