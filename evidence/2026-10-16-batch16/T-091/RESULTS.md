# T-091 结果记录

日期：2026-10-17。task `T-091`，attempt `a1`，worker `s16-t091`，ticket ready_rev 1。接手启动记录为 `launch-71afbd1600cb451a9d9354aa7768e72b`；下方早期运行保留原启动记录 `launch-a818e11600754e8b8ad79aab63a17f83` 的归属。整票状态：**INCOMPLETE**。三窗格基线红态和单格 Tracer bullet 真实读回已取得；三格代码已实现，真实绿态、反例、回归与最终交付审查尚未完成。

## red 与 close 系列

| 运行 | 原状态／退出码 | 事实与结论 |
| --- | --- | --- |
| red-01 | INCOMPLETE／rc 1 | observer_response_deadline；三个 observer 输出为零，未取得产品红态。后台三个窗格读回已生成，但 Electron 6599 未退出，cleanup_complete=false。原失败不改判 |
| close-01 | BLOCKED／rc 2 | 6599 卡在 ready 前，正常退出请求被拒：electron_normal_quit_request_refused |
| 主控人工处置 | 主控报告 | 执行主控核对 6599 的完整 argv、06:30:34 启动时间与 ppid 1 后，亲自发一次 SIGTERM，报告 2 秒后退出且无残留。不是 worker 或脚本动作；2 秒未经 worker 独立测量，不补造具体命令 argv 或精确时间戳 |
| close-02 | BLOCKED／rc 2 | already_absent，未发退出请求；复制前 inventory 拒绝符号链接，fixture_archive_contains_symlink |
| close-03 | PASS／rc 0 | 已核对 6599 和原 writer 不存在；仅复制已停止夹具，链接按自身保存，原件保留。71 个文件条目、2,482,692 字节、2 条链接，comparison=true。PASS 只指收尾与归档，不上调 red-01 |
| red-02 | INCOMPLETE／rc 1，**有效红态已取得** | red_observed=true，expected=3、observed=1；实际一个窗口只有 worker 终端。ready／退出均确认、cleanup_complete=true，error／archive_error 缺省为空，cleanup_errors=[]。该轮产品仍未实现三窗格，rc 1 是要求的合同失败 |

执行与原图检查来源为执行主控 #9／本对话主控 #36。worker 本轮只读核对外置 JSON、日志、原始单帧，没有重启或操作该场景。场景供应商模型回合 0、假 Messages POST 0、keys=[]、没有粘贴或放行；受管 worker 是现有受控 C receiver，不能把其 Codex 形状版本号／原生日志当成真实 Codex 模型回合。

close-03 与 red-02 都以 `6974c2aad1233133264b7448e1277cd19fa0b6ba` 的脚本运行；red-02 的产品源码与起点 `44bbb7828459d81fab0d46069a19d3dd515a7732` 相同。Node v26.5.0，Electron 43.4.1；两个 Claude CLI 固定 2.1.296，停在隔离首屏，不走真登录。完整 argv、输出、快照和进程事实见外置原件。

## red-02 的独立输入与真实读回

任务：`t091-red-c6e65649`，任务标题“T-091 同任务三窗格基线”。三个预先登记的启动身份为：

| 角色／preset（来自启动记录） | launch | 外置读回 |
| --- | --- | --- |
| controller／ideation | `295b635c-42dc-491c-a356-38359b24c1df` | ideation.snapshot.json、ideation.process.json、ideation.launch.json |
| controller／executor | `d0f2b1e2-f2cc-4269-8cb2-8c6d0c89e848` | executor.snapshot.json、executor.process.json、executor.launch.json |
| 受管 worker | `e7145a5d-ae59-457c-accb-3a6fe71fc22e` | worker.snapshot.json、worker.process.json |

基线 snapshot 尚未投影 preset；不能仅凭两个 controller 字样区分构思／执行角色，须核对对应启动记录。单帧也不代替这些身份读回。

`view.json` 和原图都显示一个 BrowserWindow 内仅一个终端格，绑定上述 worker；屏幕含 `T078_DETERMINISTIC_RECEIVER_READY`，没有两个主控格，底部保留任务门禁栏。主控已看原图；worker 本轮只读查看同一张原图，所见一致。未拼图、未把顺次切换截图当同时显示，未覆盖标签。

原始单帧只留外置盘：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-02/baseline-original.png`。指针为 [red-02.single-frame.pointer.json](red-02.single-frame.pointer.json)，原件 213,422 字节，2880×1800；对应逻辑窗口 1440×900、Electron PID 64741、CoreGraphics 窗口号 10448。实际捕获命令是 `/usr/sbin/screencapture -x -o -l 10448 <外置原图路径>`；完整 argv 保存在 capture.json。仓库不复制 PNG、原始二进制、SQLite 或整个 fixtures。

## 原件位置与重放条件

统一外置根：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/`。

- `red-01/`、`red-01-close-01/`、`red-01-close-02/`：失败原件不覆盖。
- `red-01-close-03/fixture/`：原 red-01 夹具的停止后副本；清单 [red-01-close-03.archive.json](red-01-close-03.archive.json)，原目录 `/private/tmp/t078-2-t091-red-05cht89k` 保留。
- `red-02/fixture/`：172 个文件条目、5,222,955 字节、2 条链接，comparison=true；清单 [red-02.archive.json](red-02.archive.json)，原目录 `/private/tmp/t078-2-t091-red-bh38vd4j` 保留。
- `red-02/`：三份 snapshot、process、first-screen，expected.json、view.json、capture.json、observer 日志与完整命令原始输出。链接清单同时标记原夹具／归档目录外目标，链接不跟随、绝对目标不重写。

主控日志位于 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/` 下的 `t091-close03.log`、`t091-red-02.log`，早期失败另见相应 red／close 日志。

本轮执行入口及参数为：

```sh
python3 -B evidence/2026-10-16-batch16/T-091/close_red01.py --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-01-close-03 --label red-01-close-03 --approval-ref '<本轮主控批准，逐字值见 run.json>'
python3 -B evidence/2026-10-16-batch16/T-091/run_red.py --source /Users/luckye/Documents/Code/a2a-wt-t091 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-02 --label red-02 --approval-ref '<本轮主控批准，逐字值见 run.json>'
```

这是已执行命令的可读形式，输出标签均已使用。重放须使用冻结版本和新标签／新批准；后续产品实现会使当前 worktree 不再满足 red 脚本的基线检查，不能直接把修改后的源码冒作基线重放。完整原始脚本 argv 与批准引用保留在各 run.json。

## 实现顺序与当前边界

下一步为单格 **Tracer bullet**：同一生产入口经 sender 窗口及 pane key 查询快照、读输出、发输入和放行；不保留旧单格 IPC 实现。单格真实读回交执行主控跑通后，再扩到已确认的上方双主控／下方全宽 worker；窗宽小于 1000px 时三行，160×45 网格与独立滚动保持不变。

绿态、错 task／旧 launch 反例、T-074／T-075 正反例及 T-078 输入回归均为 **INCOMPLETE**，不得用本轮红态或旧候选通过结论替代。仍只在隔离场景验证，所有 Electron／daemon／PTY／ps／截图实跑交执行主控，不在 worker 沙箱外执行。

## 单格实现候选（待实跑）

单格已迁到 sender 窗口／pane key 的唯一生产通路，六条 IPC 进程内单次注册；preset 是 daemon 唯一新增投影。完整身份、实际焦点标识、原输入序号／放行声明与 160×45 网格保留；未扩三格。

本地 `pane-ipc-unit-01.json` 的八项 main／preload 边界检查为 PASS；未知 key 的旧 API 被已知坏版本反例拒绝。`driver-selection-unit-01.json` 在给定观察值上验证显式选择、角色／快照绑定、未知／歧义拒绝，旧驱动不拒绝歧义而失败。这些是 VM／给定边界证据，不是 GUI 或后台实跑。脚本语法、TS／TSX 内存转换通过；没有在 worker 中完整构建、启动 Electron 或后台。

待主控核对并运行 [TRACER-RUN.md](TRACER-RUN.md) 的 tracer-01；原图仍只留外置盘。按已确认顺序，取得真实单格读回后再扩三格并重跑新候选的绿态、反例和回归。[REGRESSION-PLAN.md](REGRESSION-PLAN.md) 给出现有 CLI 全命令，并列出旧验收材料／包装器问题，不把它们隐去或记为通过。

基线结果及指针已先提交为 `8df399ca76bedd327364d94ed9cdb4c36f1205cc`，随后单格生产路径与实跑脚本提交为 `7e1c68ad432f281e05c2ac58c1fc3fe2fe079d86`。新开的只读审查会话 `/root/tracer_acceptance_audit` 使用 gpt-6.1-sol／xhigh，按 behavioral-acceptance-review 检查该冻结代码候选；结果为 **INCOMPLETE**，没有确定可达的违规发现，但缺少真实 Electron／PTY 边界证据，不能作 PASS 或全票交付结论。原文见 [tracer-acceptance-audit-01.md](tracer-acceptance-audit-01.md)。审查未改文件，也未启动服务或 GUI。

交接前再次执行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`，rc 0，Problems (0)、Stale living docs (0)；`git diff --check` rc 0。本次三份审查／交接文档回读均为 UTF-8、无 BOM、无替换字符，未改变既有 LF 换行。

## tracer-01 真实单格读回

状态 **PASS／rc 0**，仅指单格 Tracer bullet。执行来源为主控 #11／本对话 #40，冻结源码 `06575f5dc4f6a0d2cd264922158343952d0a0c21`；worker 只读核对外置 run.json、capture.json 与仓库摘要，没有重新启动场景。trace_passed、cleanup_complete、archive_complete 均为 true；fake_posts=0、供应商模型回合 0、真实供应商 CLI 启动 0，error／post_close_error／archive_error 为空、cleanup_errors=[]。此次仅测试夹具粘贴，无 Enter／Esc；自动测试字节不作真实用户历史。

task `t091-tracer-f18b846b`，launch `3d4a9a80-39f7-408f-bcd0-d0b98ed11df7`，pane key `f451023c-869d-4114-a902-e601eb59c1d8`，window_id `329412db-a3cd-4d4f-b2a2-c8f3121492bc`。真实读回确认六个未知 key 拒绝、输出 nonce 与原 trace 一致、正确窗格收到精确 bracketed paste 字节、输入记录和人工介入相符、独立序号为 1～4、没有 Enter／队列派发；关闭界面后凭据撤销，同一 receiver 仍存活，再停止后台。

主控查看原始单帧，报告完整 role／task／launch／attempt、蓝色边线和“正在输入”可见，终端有 READY 与 T091_OUTPUT nonce，底部为共享门禁栏；截图只有一格，不作三格绿态。原图只在外置盘，指针 [tracer-01.single-frame.pointer.json](tracer-01.single-frame.pointer.json)：246,886 字节、2880×1800、PID 91515、窗口号 10793。全部原件根为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/tracer-01/`；夹具副本 157 文件、3,084,805 字节，comparison=true、原件保留。摘要 [tracer-01.run.json](tracer-01.run.json)，清单 [tracer-01.archive.json](tracer-01.archive.json)。日志为主控 scratchpad 的 `t091-tracer-01.log`。

单格真实读回门槛已满足，开始沿同一生产路径扩三格；整票仍为 **INCOMPLETE**。此前只读审查的 INCOMPLETE 原报告保留，不能补称其当时已取得运行证据。

## 三格实现候选与回归脚本

tracer-01 的结果及指针先提交为 `3ac3edc92`，随后才扩三格。生产启动器与 main 均支持重复 --launch；main 先核对各 launch 的 task、role／preset、运行状态与当前 worker attempt，再按构思主控／执行主控／worker 排序，建一个 BrowserWindow。错误 task、旧 attempt 或重复 launch 在建窗／签发凭据前拒绝；单格历史查看仍只读。renderer 只有一套 SessionPane 实现，每格各持终端、decoder、offset、错误、输入占用和放行声明；共用任务外壳和当前任务门禁栏。160×45 不变，各格独立滚动；小于 1000px 三行，实际 textarea 焦点才显示蓝线和“正在输入”。daemon 本票仍仅新增 preset 投影，门禁未改。

本地检查命令及结果（均不启动 Electron、后台、PTY，不运行 ps 或截图）：

| 命令 | 结果与范围 |
| --- | --- |
| `python3 -B evidence/2026-10-16-batch16/T-091/check_baseline_bridge.py evidence/2026-10-16-batch16/T-091/baseline-bridge-assertion-01.json` | rc 0，起点 44bbb7828 的原 preload 和原断言实际单独执行；原断言 FAIL：已公开六方法，却只允许 output／snapshot。没有运行完整旧 window suite |
| `node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-16-batch16/T-091/pane-ipc-unit-04.json` | rc 0、11 项 PASS；真实 main／preload 模块，给定外部边界；单格 7e1c68 因只有一 key 而被三格数量断言拒绝，6974c2 因接受未知 key 被拒；含三格独立凭据、序号、输出、声明和建窗前拒绝 |
| `node --experimental-vm-modules workbench/tests/test_t091_start.mjs evidence/2026-10-16-batch16/T-091/launcher-unit-01.json` | rc 0、2 项 PASS；起点丢失前两份重复 --launch，被断言拒绝；未真正 spawn Electron |
| `node workbench/tests/test_t091_driver_selection.mjs evidence/2026-10-16-batch16/T-091/driver-selection-unit-02.json` | rc 0、5 项 PASS；给定三格观察值，按 key／launch 选择，拒绝歧义；不是实际三格 DOM |
| `node workbench/tests/test_t078_window_binding.mjs evidence/2026-10-16-batch16/T-091/t078-window-binding-01` | rc 0、13 项 PASS；使用主控恢复的原 snapshot，未修改原件；仅生产谓词／驱动分支，外部边界由测试提供 |
| `python3 -B workbench/tests/test_t091_client_cleanup.py evidence/2026-10-16-batch16/T-091/client-cleanup-unit-01.json` | rc 0、4 项 PASS；旧客户端对 unready 执行关闭／强杀，被已知坏断言拒绝；不是 AppKit 或真实退出证明 |
| Node --check、Vite transformWithOxc 内存转换、Python compile | 已跑部分通过；最终脚本预检记录随冻结候选保存，无完整构建或目标进程启动 |

`pane-ipc-unit-02.json` 保留一次实现中的失败：多格身份校验误放入普通输入回执处，正常输入返回不含快照而报 mismatch；校验移回 snapshot 后 unit-03／04 通过。`three-script-preflight-01.json` 保留一次 Python comprehension 中 walrus 的编译错误；改为先读取观察值再迭代后 preflight-02 通过。没有覆盖失败文件或将它们改判 PASS。

主控 #11／本对话 #40 确认旧 bridge 断言不受 T-080 保护，并授权先留起点结果再修正；已按上述结果把预期精确列为 beginComposition、input、observeFocus、output、paneKeys、releaseQueue、snapshot，不用宽松数量比较。复核真实窗口入口还发现隔离 bootstrap 凭据未配置、旧客户端失败时自动强杀且后台／归档仍可能继续；已仅修正测试的凭据与生命周期收尾，不改其业务 oracle。当前 receiver／GUI 回归按新批准逐场运行，不沿用 T-078 的批准。

主控执行材料见 [THREE-PANES-RUN.md](THREE-PANES-RUN.md)。`run_three_panes.py` 提供三格同屏、三份快照／进程、输出归属、worker 输入收据链、错 task／旧 launch 拒绝及三种尺寸原始帧；`run_regression.py` 分 core／window／runtime／input-failures／worker-inbox，继续调用原业务断言。T-074 的固定注入合同由原 runtime 场景在当前生产路径回归，不声称重跑供应商模型实验。所有实跑、实际截图和独立最终验收仍 **INCOMPLETE**，本轮没有启动这些场景。

## 重启后新会话接手

当前受管 session 为 `d4277ace-1dde-425b-99b8-8988f1df751f`，原生会话为 `01a14a05-4472-70e1-af77-58414340c1ee`，launch 为 `launch-71afbd1600cb451a9d9354aa7768e72b`。这些值来自本会话环境，提交尾注由现有钩子生成；未沿用旧会话进程身份。起点 HEAD `3ac3edc92afdd40f31926b94d83fdba4c8c5bf65` 的未提交三格工作全部保留并核对。

本次本地检查为 **PASS**，范围仅为给定外部边界的逻辑、静态转换与材料读回。实际 Electron、daemon、PTY、原生 agent、ps、截图启动／执行均为 0，模型回合 0；没有复制 auth 或写外置盘，没有运行下方主控专用脚本。

```sh
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-16-batch16/T-091/pane-ipc-takeover-01.json
node --experimental-vm-modules workbench/tests/test_t091_start.mjs evidence/2026-10-16-batch16/T-091/launcher-takeover-01.json
node workbench/tests/test_t091_driver_selection.mjs evidence/2026-10-16-batch16/T-091/driver-selection-takeover-01.json
python3 -B workbench/tests/test_t091_client_cleanup.py evidence/2026-10-16-batch16/T-091/client-cleanup-takeover-01.json
python3 -B workbench/tests/test_t091_run_budgets.py evidence/2026-10-16-batch16/T-091/run-budgets-green-02.json
node workbench/tests/test_t078_window_binding.mjs evidence/2026-10-16-batch16/T-091/t078-window-binding-takeover-01
python3 -B evidence/2026-10-16-batch16/T-091/test_red_cleanup.py --output evidence/2026-10-16-batch16/T-091/observer-cleanup-takeover-01.json
```

以上输出均已存在，重放须换新文件名。结果分别为 11、2、5、4、两种客户端、13、6 项 PASS。三格数量、独立身份／序号与输出、错 task／旧 launch、重复 launch、旧启动器丢弃重复参数、未知／歧义选择等，均有拒绝已知坏实现的反事实记录。`product-parse-takeover-01.json` 的 TS／TSX 内存转换与 MJS 语法检查、`script-parse-takeover-01.json` 的 Python compile 通过，未完整构建。

根据主控转达的资源约束，本次为两种实际客户端增加探测额度：三格脚本 120 次 RPC（最多 360 次读屏），GUI 回归 400 次（最多 1200 次读屏）；驱动记录实际读屏数。stdout 分别在 32／64 MiB 时停止下一次探测，允许一份在途回复跨过阈值。正常关闭不消耗 GUI 探测额度；额度耗尽仍进入原归属核对／关闭／停机／归档流程，不增加强杀。完整输出直接落外置文件，Terminal 只收到一行短摘要。限额检查的首次红态保存在 `run-budgets-red-01.json`，修正后 `run-budgets-green-02.json` PASS，固定坏版本为 `3ac3edc92`；不声称这些逻辑检查证明了真实内存占用或 macOS 收尾能力。

三格场景的新真实 Codex CLI 启动为 0；两个真实 Claude 主控与一个受控 receiver 同时存在，反例的另两个 receiver 先退出再启动下一个，Electron 最多一个。run.json 记录启动尝试、峰值 receiver、实际窗数、读屏、截图与 stdout 字节数。Herdr 中已存在的 Codex 会话总数由主控逐场核对，不从 worker 的局部夹具推断。

**core 回归材料缺件，仍 INCOMPLETE。** 原运行器固定读取的四份受控文件未进入本稀疏 checkout，清单在 `core-materials-takeover-01.json`。它们在 HEAD 中存在：分页 CONTRACT／pager 两份，以及 T-076/card-2 的 controller-decision-03／legacy-acceptance-hunks 两份。worker 只读运行 `prepare_core_materials.py --source /Users/luckye/Documents/Code/a2a-wt-t091`，rc 1，未恢复或改写原件。主控专用 `--restore` 仅写回缺失的 HEAD 原字节，拒绝已有内容不符或链接路径；core wrapper 在启动业务测试前先拒绝缺件。完整命令见 THREE-PANES-RUN。此缺件不是产品红态，不能算回归通过。

bridge 断言修订沿用主控裁定：起点原断言只允许 output／snapshot，但起点 preload 实际已有六个公开方法，原断言单独执行 FAIL。新预期逐项为 beginComposition、input、observeFocus、output、paneKeys、releaseQueue、snapshot，另要求 renderer 无 Node；没有运行起点完整 window suite。主控恢复的 p1-materials-09 原 snapshot 未改，当前 13 项绑定检查仍 PASS。

交付边界仍是脚本准备完成，等待主控依次实跑三格绿态／拒绝反例与五类回归；真实结果和最终门禁验收不能以本地 PASS 替代。

### 冻结审查与收尾判定修正

三格候选先冻结为 `03b80c4d86feb20140d0df630ae100db40d68ecf`；提交九项尾注已核对，均使用新会话身份，工具为 codex-cli 0.163.0。新开的只读工具子会话按 behavioral-acceptance-review 审查此冻结候选，结论 **FAIL**，原报告 [three-pane-acceptance-audit-01.md](three-pane-acceptance-audit-01.md) 保留。审查没有启动真实 reviewer CLI 或场景，不作为最终门禁独立终审。

该审查复现了隔离 operator 凭据删除失败仍被判 PASS 的 P2。修正只把 `cleanup_complete` 的设置移到删除成功后，并在最终 PASS 条件要求 `cleanup_errors` 为空。`test_t091_cleanup_verdict.py` 执行 runner 实际 AST 的收尾段与最终判定，文件系统故障由独立输入注入；固定坏候选 03b80c4 被拒，当前删除失败为 INCOMPLETE／cleanup_complete=false，正常收尾仍 PASS，已有收尾错误不能 PASS。

```sh
python3 -B workbench/tests/test_t091_cleanup_verdict.py evidence/2026-10-16-batch16/T-091/cleanup-verdict-green-02.json
```

该检查三项 **PASS**；它是纯逻辑故障注入，不是实际 macOS 删除／退出证据。`cleanup-verdict-red-01.json` 保留产品判定缺陷；`cleanup-verdict-green-01.json` 保留一次检查夹具错误：给定 call 未接收实际入口的位置参数，修正检查边界的签名后 green-02 通过，不改生产业务预期。最终脚本尚无新的独立通过结论，仍待主控实跑和最终只读审查。
