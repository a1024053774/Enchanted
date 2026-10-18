# T-096-1 当前交付记录

2026-10-18，主控 #110／#16 派发的独立审查修复：**PASS（局部合同）；INCOMPLETE（新候选整体验收）**。上一冻结候选 `11b32303bebf276d20026a6e718719d15f5d4068` 被独立审查 01 判为 NO_GO：明确关闭最后一格后，重开又选择当前 worker。七场原生实跑证据仍成立，但没有覆盖空集边界，也不替这次产品改动背书。reviewer 的 `independent-review-01.md`、`REVIEW-OUTSIDE-01.sh` 原文一并提交；它们始终针对旧候选，脚本预期仍为 NO_GO／退出 1。

本会话身份：task T-096、attempt a1、session `f1635b4b-e7a1-4d4c-9789-94069e6de12e`、native session `01a14f20-ba1c-7362-843e-307ae25f8975`、launch `launch-a336907aa67c4d9799f9a24cb71860f7`；Codex CLI 0.163.0，gpt-6.1-sol／xhigh，启动 argv 请求 fast，实际供应 tier 未核对。合同仍为 ready_rev 1 加用户裁定 B；未沿用前一进程身份。

改动只保留已有事件流中的事实：`pane_layout` 返回该任务是否有打开／关闭布局事件，主进程只在从未保存时选择默认窗格。已保存的空集创建零个 pane key，preload 接纳空列表，renderer 使用已有空状态。没有新表、配置副本、门禁改动或 worker 自动续接。**Ubiquitous language** 沿用“窗格、启动记录、未恢复”；**Deep modules** 的配置来源与边界不变。这次是既有 **Tracer bullet** 的集合边界修复。

| 本轮证据 | 结论与范围 |
| --- | --- |
| `empty-layout-red-02.json` | 缺陷红态；产品仍为 `11b32303b`，真实 main/preload、替代 Electron／transport；退出 1，命中 `Explicitly closed final pane must stay absent when app reopens`，实际 1、预期 0。 |
| `empty-layout-green-02.json` | PASS；同一入口转绿，首次默认选择仍工作；关闭最后一格后连续重开两次仍为空；空 preload 正常、无新输入凭据，显式指定 launch 可重新打开。测试内再次读取完整旧 SHA，确认同一业务断言拒绝它。 |
| `spawn-argv-green-02.json` | PASS；真实 SQLite 重开后保存空集仍可识别，任务隔离、仅原生元数据不算布局；两个主控恢复、三个拒绝、worker 不启动及 attempt 不变仍通过。实际交给 PTY 的命令核对全部外部输入参数；M1 丢启动参数、只保留正确事件的变异被业务断言拒绝。 |
| `empty-layout-transport-01.json` | PASS；现有死／活／未知端点、PID 文件变更、活动 socket、非 socket 合同回归；仍限替代 IO 边界。 |
| `empty-reopen-cleanup-03.json`、`empty-reopen-startup-01.json` | PASS；新脚本退出未确认时不重复退出、不停止后台、不归档，移除该保护的变异被拒；原有收尾及逐屏批准合同保持。没有真实进程／GUI／模型。 |

精确复现命令（输出文件须换新名称，不能覆盖上述证据）：

```sh
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs /tmp/t096-ipc-新名称.json
node --experimental-vm-modules workbench/tests/test_t096_restore.mjs /tmp/t096-restore-新名称.json
node --experimental-vm-modules workbench/tests/test_t096_daemon_restart.mjs /tmp/t096-transport-新名称.json
python3 workbench/tests/test_t096_restart_cleanup.py /tmp/t096-cleanup-新名称.json
python3 workbench/tests/test_t096_red_startup.py /tmp/t096-startup-新名称.json
```

首跑 `empty-layout-red-01.json` 是新增首次打开场景改变凭据计数后的测试适配失败，不算缺陷红态；`empty-reopen-cleanup-01.json` 是 AST 夹具未提供新增收尾状态变量，不算产品退化。两份原始失败均保留，后续报告没有改写它们。

真实 Electron 新边界**未运行**，交主控的入口为 `RUN-EMPTY-LAYOUT.sh`，完整启动与按键预算写在脚本开头；它复用 `run_restart.py --check-empty-reopen`，三格原生读回后关闭全部窗格，正常退出并用第三个串行 Electron 重开，检查空 DOM／pane key／保存集、无新窗格或凭据事件、完整 task 不变。原生 CLI 仍按原流程逐屏批准，模型预算 0。具体命令见 `RUN-RESTART.md` 新增说明。此脚本的真实 Electron／daemon／CLI 路径、标准构建以及新候选独立审查、门禁 submit／验收／集成均未执行，整票保持 INCOMPLETE。

`empty-layout-static-01.json`：静态与路径核对 PASS，Node v26.5.0、Python 3.9.6；TS／Python／shell 语法、UTF-8／LF、diff 检查通过；项目地图为 0 problems、0 stale living docs。未改地图、ticket、角色卡、全局配置或 gates。冻结版本由包含本轮证据的提交及本会话自动生成的九项尾注标识，完整 SHA 在交付末行。

以下保留上一冻结候选的历史交付记录及七场实跑结论：

**PASS（本票实跑）**：七个最终场景全部通过，全部 cleanup true、fake API POST 0、模型回合 0。候选按主控 #107／#15 要求冻结，等待独立审查；门禁 submit、验收与集成尚未完成，不把实跑 PASS 当作门禁结论。审查入口见 `REVIEW-REQUEST-T096-01.md`。

当前范围以主控 #89 转达和 main `8cf91b26e` 的 T-096“裁定”节为准：只恢复两个主控；worker 保留为“未恢复”，不启动 CLI、不重绑定、不改 attempt。不修改 `workbench/src/gates/`。主控 #88 允许先完成不依赖门禁裁定的路径。

主控没有跨重启的固定 PID 绑定：`Panes.controllerLaunch()` 返回的身份不含 PID；`caller()` 在单次请求内固定当次 leader（`panes.ts` 的 controller 分支），daemon 的 `assertCurrent()` 核对当次前台进程；`core.ts:340` 的 `registerController()` 只核对 task/project/spec_rev。worker 的旧 PID 绑定留在 `core.ts:2485`，没有改动。

最终场景结论（主控 #107／#15 确认，2026-10-18）：

| 场景 | 结论 | 独立读回重点 | 收尾 |
| --- | --- | --- | --- |
| red-b-05 | PASS，识别到 main 的真实红态 | main 遗留死端点阻断第二轮启动，行为为 NO_GO；不是产品恢复成功 | cleanup true、归档比较通过 |
| tracer-b-05 | PASS，15 项 | 单主控原 session 的真实历史 nonce、内核 argv 全字段、绑定和显式关闭集 | cleanup true、归档比较通过 |
| three-b-01 | PASS，26 项 | 两主控原历史恢复；worker 只读“未恢复”；完整 gate task／attempt 前后相等 | cleanup true、归档比较通过 |
| no-argv-b-02 | PASS，9 项 | 缺 argv 明确拒绝，真实窗口保留“未恢复”，没有成功事件 | cleanup true、归档比较通过 |
| version-b-02 | PASS，9 项 | 版本不符明确拒绝，真实窗口保留“未恢复”，正常退出及已保存窗格集读回 | cleanup true、归档比较通过 |
| no-session-b-01 | PASS，9 项 | 缺 session 明确拒绝，保留现场，不新建会话 | cleanup true、归档比较通过 |
| isolation-b-01 | PASS，20 项 | 一个主控拒绝恢复不影响另一主控；失败窗格无成功事件，worker attempt 不变 | cleanup true、归档比较通过 |

初始化按键全部由执行主控逐屏读取原始屏幕后明确批准：每个主控 profile 六键，加一次空队列就绪放行。主控 #104／#14 与 #107／#15 确认批准来源；每屏材料与批准回执在各场外置盘 `startup-screens/`，daemon 事件和 run.json 保存实际按键序列。red-b-05 不发初始化键。所有最终场景的 fake API 原始请求记录均无 POST，恢复不提交模型提示词，模型回合为 0；未做真实登录或写用户全局配置。

`cleanup-version-b-01.run.json` **PASS**：核对固定身份后仅一次 daemon_stop，79664 已退出，651 文件／207,761,842 字节归档比较通过；私密 operator-1／2 只从副本排除，原件保留。`version-b-02.archive.json` 为 652 文件／177,406,492 字节，comparison true。新四份 run／清理／归档产物一并提交。no-argv-b-01、version-b-01 及更早失败的原始摘要、原件和诊断保持原样；补做清理不把失败摘要改记 PASS。

用户询问用预置 hasCompletedOnboarding 和隔离目录信任状态绕过 Claude 初始化屏，主控已明确另交构思主控处理；本票不实现，也不把这条未决定路径计入本次验收。

2026-10-18 主控 #104／#14 的原生验收结果与 version 收尾：

| 场景 | 原摘要 | 检查项 | 收尾／归档 |
| --- | --- | --- | --- |
| red-b-05 | PASS | 4 | true；84 文件／3,920,891 字节 |
| tracer-b-05 | PASS | 15，含 ideation_native_history_visible | true；650 文件／285,439,776 字节 |
| three-b-01 | PASS | 26，含两主控原生历史、worker 未恢复 | true；1,236 文件／568,770,930 字节 |
| no-argv-b-01 | INCOMPLETE | 初始化未完成，不算 argv 反例 | true；45 文件／1,424,491 字节 |
| no-argv-b-02 | PASS | 9 | true；653 文件／287,513,046 字节 |
| no-session-b-01 | PASS | 9 | true；649 文件／199,808,749 字节 |
| isolation-b-01 | PASS | 20 | true；1,239 文件／572,856,163 字节 |
| version-b-01 | INCOMPLETE | 8 项业务检查全部 PASS | false；原现场保留，待固定收尾 |

以上全部 fake POST 0；七份归档 comparison 均 true，原件保留，run.json 和 archive.json 一并提交。no-argv 首场的按键被拒绝由主控报告为操作者过早截屏；保留原失败，不改记通过，使用 -02 的独立重跑证明 argv 反例。原始 three／isolation 的完整 gate-before／gate-after task（包括 current_attempt 的身份、state、runtime_identity）逐字段相等。

version 第二个 Electron 79678 的最后两次已保存 ps 与 journal 的 PID／lstart／command 完全相等；全部业务检查在退出前完成。window-2/stages.jsonl 记录正常 ready、读回、will_quit／quit，退出码 0，无 fatal；因此不支持“版本不符导致提前退出”。正常退出 helper 的请求前／请求后均会核对身份，但旧版没有保存拒绝那一次 ps 或已接受的退出请求回执，无法严格证明没有 PID 复用。现有证据支持退出过程核对竞态，具体缺失处保留为未知。原始 stderr 也有只读未恢复窗格的 focus-observation 拒绝，未发现它触发 Electron fatal／退出的证据，本轮不据此修改产品。

修复仅在已接受 NSRunningApplication.terminate 后遇到精确的身份核对错误时，等待本 runner 的 Popen 子进程退出并独立确认 PID 不存在，最多 3 秒；不重发请求、不收留复用 PID。请求前拒绝、未接受、持续存活、超时、其他错误仍交回；非零退出保留诊断。摘要新增 electron_quit_events，报错时也保存阶段回执。`version-cleanup-contract-03.json` **PASS**：实际旧 normal_quit 循环在替代 AppKit／ps 边界下重现，旧 `f2b96001d` 被接受退出后误拒绝的反例拒绝；固定收尾入口的身份、完整 argv、活 Electron／未知夹具写入者、子进程、二次核对、停止回执丢失、私密排除与原件保留均核对，跳过身份比较的变异被拒绝。既有收尾和 argv 语法回归 `restart-cleanup-version-01.json`、`runner-materials-version-01.json` 均 PASS；不作真实 AppKit 或固定夹具已收尾的证明。

2026-10-18 主控 #99／#13 的真实进程树结果读回：

- `process-tree-red-02.run.json`：旧候选 `da6a095fc` 的四场均 INCOMPLETE，测试自身 cleanup 全为 true。原始 `zombie` 场景实际读到 Z，kill 抛身份变化拒绝；另外三场的候选 finally 在死端点归档处失败。这是所需缺陷红态，原失败摘要不改记 PASS。
- `process-tree-green-01.run.json` **PASS**：候选与 harness 均对应 `4c49db73b`，父死子随退出、Z 状态后回收、提前退出和存活 exec 替代四场均 PASS；每场 runner_cleanup／独立 cleanup 均 true、handoff null。原始 JSON 核对：三个自然退出的子进程均未收到信号；Z 场景记录 exited_without_signal；存活替代命令记录 identity_changed 且未收到信号。没有供应商 CLI／模型／Electron；适用范围为 runner 的真实进程 kill／finally。
- `archive-red-b-04.run.json` **PASS**：83 文件／3,921,101 字节，comparison true，死 socket／私密 operator 文件明确排除，原件保留；清单为 `red-b-04-archive-red-b-04.archive.json`。旧 red-b-04.run.json 保持 INCOMPLETE。
- 上述四份主控产物一并提交。本轮只读核对原始记录、更新运行说明，runner 与产品代码不变；没有重跑已经通过的演练。red-b-05／tracer-b-05 的 label、外置盘 output 和 context 路径见 `RUN-RESTART.md`，逐屏批准与严格 nonce／argv／0 POST 断言不变。

2026-10-18 主控 #95／#96 的实跑与进程树交接：

- `archive-red-b-03.run.json` **PASS**：85 文件／3,921,951 字节，comparison true，排除死 socket 与私密 operator 文件，原件保留。该摘要及 `red-b-03-archive-red-b-03.archive.json` 一并提交；原 red-b-03.run.json 的 INCOMPLETE 不变。
- red-b-04 的 command-34：shell 53458 的 lstart 与登记相同，但 command 由完整 zsh 启动命令变成 `(zsh)`；command-39 已为空 rc 1。此前只发出了四个 Electron 进程和 daemon 53370 的 kill，未对该 shell 发信号。旧 ps 未请求 stat，故不能把 `(zsh)` 直接认定为僵尸；这次失败属于 runner 身份核对把退出过程当作身份更换，未到第二轮后台启动。七 PID 最终退出的事实来自主控事后读回，本 worker 未在沙箱外探测。
- 修复：同启动时间的 command 变化不会被规范化或获准发信号，只限时等待最多 3 秒，观察到 PID 不存在才继续；持续存在或启动时间变化仍拒绝。确认旧 epoch 全部写入者退出后，finally 可核对故障注入留下的死端点并归档，保留原件、私密文件与原失败状态。没有 crash intent、新 epoch 存在、身份未知或活动端点均不接纳。
- `process-probe-exit-01.json`、`restart-cleanup-exit-01.json`、`archive-04-contract-01.json`、`red-startup-exit-01.json` **PASS**：均限替代进程／socket 边界。旧 `da6a095fc` 被同启动时间 command 变更后退出、故障中断后的死端点收尾反例拒绝；存活替代命令不得收到信号，nonce 断言仍严格。
- `test_t096_process_tree.py` 是待主控执行的真实 Python 父子树演练，覆盖父死子随 EOF 退出、实际 Z 状态后由父回收、kill 前已退出，以及持续存活的 exec 替代反例。它执行候选实际 kill 和完整 finally，并单独记录测试自身的独立收尾；进程／信号边界不用替身。真实演练当前 **INCOMPLETE**，不是上述局部 PASS 的结论。
- 本 worker 的 `process-tree-red-01.json` 在首次 ps 被沙箱拒绝：这是环境失败，不算已知坏候选的行为红态。已发送私有 shutdown 并等父进程返回；后续 ps 同样被拒绝，原记录保留 cleanup false 和 PID 56541／56543 的交接。升级申请被主控拒绝，未运行，本 worker 不再申请升级。只读核对这些 PID、红态／绿态完整命令、输出路径与 red-b-04 归档命令见 [RUN-PROCESS-TREE.md](RUN-PROCESS-TREE.md)。后续进程树证据先通过，再安排原生场景。


2026-10-18 主控 #93 的实跑、原件诊断与最小探针：

- `archive-failed-02.run.json` **PASS**：red-b-02 83 文件／3,921,063 字节，tracer-b-02 82 文件／2,898,979 字节；只读归档、comparison true，明确排除死 socket 与 operator 私密文件。两份 `*-archive-failed-02.archive.json` 和现有摘要一起提交。
- `diagnosis-03.json` 保存原件诊断。red-b-03 的 command-47 返回 `ok:false, error:daemon_call_failed, details:"Error: socket exists; query its owner, do not replace it"`；未创建 operator-2 或第二轮收据，原 daemon.pid 仍指向 26509。调用在 main 的 transport 检查 socket 存在处，早于新凭据／进程创建，是本票重启路径应修的真实红态。主控事后确认七 PID 退出，本 worker 未执行实时 PID／socket 探测。
- red-b-03 的实际 argv 再次未带旧可选 `--expect-red`；旧 runner 因而按恢复成功场景运行，先前预清理端点的另一分支还会掩盖此缺陷。现在改成必填 `--expect red|restore`，不预清理端点。只有显式 red 模式、已观察到的精确拒绝、无新凭据、全部原 PID 退出以及 socket 确认死亡才接纳该红态；观测行为记 NO_GO，探针自身成功为 PASS，未知启动失败不接纳。
- tracer-b-03 实际到达 epoch 2，实际 PID、task／role／launch、原记录与内核 argv 核对 PASS，cleanup true、fake POST 0。`ideation.resumed-view.json` 中仍显示 `Choose the text style...`；隔离 `.claude.json` 的 hasCompletedOnboarding／theme 未设置，debug 明确记录 workspace trust not accepted。第二轮约 9 秒的窗口读回末尾仍是主题引导阶段；不能把缺 nonce 归为单纯读屏太早，也不能据此判定原生 JSONL 语法或 --resume 目标错了。
- 官方 [CLI 参考](https://code.claude.com/docs/en/cli-reference) 说明 --resume 按 ID 恢复；实际 2.1.302 是否载入本夹具仍须原生内容读回证明。当前不改变合成历史格式、不扩大 nonce 等待、不放宽 nonce 断言。
- REALITY GATE: INCOMPLETE。GOAL：证明已初始化的隔离 CLI 用原参数恢复原历史；NON-GOALS：不真实登录、不写全局配置、不伪造 onboarding/trust 状态、不改门禁。OBSERVED：theme 引导尚未完成；UNKNOWN：引导完成后此 JSONL 是否被 CLI 接纳、历史如何显示。PROBE：执行主控运行 tracer-b-04，经现有逐屏批准入口完成初始化；继续同一 nonce／实际 argv／0 POST 断言。任何新引导拒绝或无 nonce 保存原件并停止该候选；OWNER：执行主控实跑，本 worker 提供脚本。DECISION CONSEQUENCE：先补最小原生探针，不以假想格式修复替代实际证据。
- 新 `startup_controls.py` 绑定 launch／session／目录／原始屏幕和批准依据，沿用 pane_screen_key。trust 后须另读原生就绪屏并批准一次空队列 pane_release，避免按键刚送达即杀后台。runner 限时等待 trust-Enter 及其后的 initial_release，不自行按键；两个事件只是测试前置条件，不是恢复结论。过程文件在外置盘，每屏批准新建，不复用其他场景。
- `red-startup-contract-06.json` **PASS**：替代边界验证精确红态与未知失败隔离、预期必填、基线端点不被预清理、批准模板不产生动作、单次绑定按键、空队列就绪放行、等待期限／零模型预算、主题屏不能替代历史；把 nonce 断言改为恒真或原候选不接纳真实红态均被拒绝。`-02` 的 source 变量缺失为局部夹具适配失败，保留记录。
- `restart-cleanup-contract-09.json` **PASS**：已验证红态可确认退出并归档、保留死端点／私密源文件；不把未知启动当作已退出。`archive-03-contract-04.json` **PASS**：固定 red-b-03 只读归档入口、失败交接对象与既有 -02 用例保持约束；`runner-materials-startup-02.json` **PASS**。archive 局部 `-03` 的存活 PID 替身仍写死 -02 PID，属于测试适配失败，已修正并保留失败记录。均未执行真实 `-04` 或旧 red-b-03 归档。

2026-10-18 主控 #91 的实跑、原件核对与退出探针修复：

- `cleanup-failed-01.run.json` **PASS**：两场 `-01` 的六个 PID 已由主控确认退出，两个夹具已复制并比较。`red-b-01-cleanup-failed-01.archive.json` 为 78 文件／3,129,075 字节，`tracer-b-01-cleanup-failed-01.archive.json` 为 75 文件／3,080,910 字节，comparison 均为 true；这些现有记录一起提交，不改旧失败摘要。
- 原件核对见 `phase-readback-02.json`：两场均只有 epoch 1 的 daemon 启动收据、一次 controller_start、`window-1` 与 `before-view.json`；没有 `daemon-start-2.json`、`window-2`、`after-view.json` 或 `gate-after.json`。异常调用点为 `for owner in owned: kill(owner)`，位于第二轮后台启动之前。因此两场都**没有到达重启读回**，不能记作红态／绿态通过；仅初始真实 Claude argv 核对 PASS，fake POST 均为 0。
- `red-b-02.run.json` 的主异常 PID 为 15840，`tracer-b-02.run.json` 为 16098。调用链显示 alive 先执行一次 ps，再由 process_identity 立即执行第二次 ps；第二次遇进程消失时抛 rc 1。主控事后核对 14 个 PID 都已退出；原目录仍有死端点，故 finally 报 endpoint remains、cleanup false。本 worker 只读核对这些原件，未运行实际 ps 或归档。
- 修复为当前 runner 和 `-02` 归档命令共用的 `probe_process`：每次只用一个 ps 结果，rc 1 且 stdout／stderr 都为空才判退出；其余错误照旧。alive 不再做重复查询，发信号前刚好退出的 ProcessLookupError 明确记入退出回执；权限错误和身份变化不吞掉。
- `process-probe-contract-01.json` **PASS**：替代 ps／信号边界，覆盖空 rc 1、带输出 rc 1、其他返回码、坏格式、单次读回、信号前退出、权限错误和 PID 变化；上一候选 `958ede25f` 被退出竞态反例拒绝。
- `archive_failed_02.py` 只读核对固定两个 `-02` 夹具、14 个 PID 和端点状态；不启动或停止 agent、不改源目录。明确排除死 IPC socket 与 operator 私密凭据，保留其原件，复制其余部分并比较数量／字节／路径。清单列明排除项及比较范围，不把过滤后的副本称为完整原树。
- `archive-02-contract-01.json` **PASS**：真实临时文件、复制和 symlink，替代 PID／socket 探针；存活 PID、活动／未知端点及后续 epoch 均拒绝，源文件／旧摘要原样保留，私密和 IPC 不进入副本；独立已知文件数／字节数核对通过，绕过排除项的变异被拒绝。未操作真实两场 `-02` 目录。
- 既有收尾、固定 `-01` 收尾入口和 argv 解析局部回归分别为 `restart-cleanup-contract-07.json`、`fixed-cleanup-contract-04.json`、`runner-materials-probe-01.json`，均 PASS，仍限替代进程边界。下一次使用 `red-b-03`／`tracer-b-03`，命令见 `RUN-RESTART.md`。

2026-10-18 主控 #90 的实跑与脚本修复：

- 两场原始摘要为 `red-b-01.run.json`、`tracer-b-01.run.json`，完整日志在各自外置盘目录。真实初始 Claude argv 核对通过，fake POST 均为 0；两场都未走到重启后的验收断言，不能当作合同红态或绿态。
- 已确认脚本缺陷：`process.stdout.read()` 在非阻塞模式可能为 None；计划内杀掉 Electron 后旧 Observer.close 拒绝非零退出；旧 finally 在布局查询／Observer 收尾出错后跳过 daemon_stop。原摘要中的 cleanup_error 分别是 caller_identity_required、observer_exit_nonzero。另：red-b-01 的实际 argv 未含 `--expect-red`，重跑命令明确带上该参数。
- 修复集中在本票脚本和测试，没有改产品 src/app/gates。`restart_cleanup.py` 由 runner 和固定收尾脚本共用，负责非阻塞输出、退出证明、私有 operator 请求及顺序收尾；失败诊断被保留，不作无声 fallback 或重放停止请求。
- `cleanup_failed_01.py` 只处理主控列出的两个夹具／六个 PID。先核对全部身份，再各用原 operator 凭据执行 daemon_stop；不强杀、不新开 attempt，确认退出才归档，原件和旧失败摘要保留。旧运行缺历史精确 lstart 的限制已写进脚本、preflight 和运行说明。
- `restart-cleanup-contract-06.json` **PASS**：以 `10c0168db` 为反事实，两个真实报告的缺陷均在替代进程边界重现；当前 runner 的实际 AST 及共用收尾函数通过 None／部分输出、计划内非零退出、布局诊断、身份变化、停止回执丢失、活写入者、归档失败和私有凭据等检查。没有执行真实残留收尾。
- `fixed-cleanup-contract-03.json` **PASS**：固定收尾脚本真实入口在替代进程／socket／归档边界下，只有两场／六 PID、第二场不符时零 stop、停止前 PID 变更拒绝、退出先于归档、凭据不进归档、原失败摘要不变。删掉最后身份复核的变异被业务断言拒绝。
- `restart-cleanup-contract-01.json` 的局部夹具缺 cleanup_complete 字段属于测试适配失败，原件保留；后续报告不覆盖它。

本次局部证据：

- `decision-b-contract-02.json` **PASS**：真实 SQLite／原生文件，替代进程边界；两个有效主控恢复、三个失败各自保留、worker 无新 PTY、attempt 原字节不变、argv 全字段、原启动记录不变、关闭集与位置、0 次输入写入。上一 WIP `a8fbc72bd` 被“worker 必须未恢复”断言拒绝。
- `layout-ipc-contract-02.json` **PASS**：真实 main/preload 模块，替代 Electron/transport；退出应用保留打开集、显式关闭只删一个、重开沿用位置、失败 worker 无输入凭据。关闭却不移除保存集的变异被业务断言拒绝。
- `daemon-restart-contract-b-02.json` **PASS**：真实 transport 模块，替代 IO 边界；死进程加拒绝连接的旧端点允许重启，活进程、未知 owner、活 socket、非 socket、异步期间更换 PID 均不删除端点、不发凭据。起点 `3c9016d02` 的死端点重启被业务断言拒绝。`-01` 的 VM 缺 URL 属测试边界适配失败，原件保留。
- `runner-materials-01.json` **PASS**：脚本语法、原生 argv 缓冲解析；空参数、空格、引号、Unicode 与换行保留，环境不进入 argv。未调用 macOS sysctl，不作实际进程证据。

`run_restart.py` 已按裁定 B 重写：真实配置 Claude 2.1.302、真实 daemon／Electron；只有三格夹具中的 worker 使用受控 C receiver。原生续接的 argv 从 macOS sysctl 独立读取；实际终端还须显示历史 nonce。历史由脚本在停止的隔离目录中预置，明确为合成夹具，不冒称模型生成或 CLI 自行保存。遇初始化／信任／权限屏不自动确认，读回不成立就 INCOMPLETE。详见 `RUN-RESTART.md`。

`static-checks-b-01.json` 的语法、编码、修改范围和项目地图检查 **PASS**（0 problems、0 stale living docs）。Claude 启动版本与 driver 选择局部回归分别见 `t091-version-regression-b-01.json`、`driver-selection-b-01.json`，均 PASS，适用范围仍为替代边界。

尚未完成：独立审查、门禁 submit／验收／集成；本票实跑及故障现场清理已完成。原门禁重绑定阻塞已由裁定 B 移出本票；不再等待它实施。下文各日期段保留当时的阶段状态，最终结论以上方七场表为准。

下列为第一轮 WIP 的原始局部证据，保留其适用范围：

身份：s16-t096；T-096 / a1；执行器 gpt-6.1-sol / xhigh；派发来源 launch-14dcc6be543a483ab0b03021f573d028；起点 main 3c9016d02；合同 ready_rev 1。CLI 实际供应 tier 未核对。

Ubiquitous language 沿用 CONTEXT.md 的启动记录、原生会话、attempt 与窗格。Deep modules：恢复的 argv 与原生会话核对由 `paneRecovery.ts` 承担，启动配置仍只读原启动记录；窗格集是同库现有事件流的投影，没有第二套 profile。

已有证据（均为局部合同，不是后台或 GUI 验收）：

- `contract-red-01.json`：修复前 recover 重启数为 0，命中应为 1 的业务断言。真实 SQLite，替代进程边界；模型回合 0。
- `contract-tracer-green-02.json`：同一合同转绿，核对前台身份确认、原启动记录不变，以及非 session 选择器的 argv 字段保留。
- `t091-ipc-regression-01.json`：新 layout 命令未被旧 VM 边界识别，属于测试适配失败，保留。
- `t091-ipc-regression-02.json`：只增加 operator layout 命令边界后，原 pane-key、窗口隔离、序列号、输出路由、历史 attempt、错误绑定等断言通过；两个已知坏版本仍被原业务断言拒绝。
- `t091-version-regression-01.json`：原 Claude 启动版本合同及版本校验变异检查通过。

第一轮的阻塞正文保留在 `ISSUE-worker-runtime-rebinding.md`，作为日期记录；当前裁定不恢复 worker，因此不再把它作为本候选的推进阻塞。首轮脚本未运行；当前运行步骤以 `RUN-RESTART.md` 为准。
