# T-104 第一轮独立审查（2026-10-19）

STATUS: NO_GO

TARGET: `d54826223194b56ca057b8ab3213729c9e53a29a`，分支 `exec/t104`；起点 `cc18d93dbbcf2ee641dc92befe68e5b0609b4807`；合并提交 `edd469f6b9d2d34bedb3a9479159fbb917dc43d5`，第二父提交 `ea206484b8bcdae19fa4edd91b7553af22ff757b`。

本轮有一项已确认的记录范围不符，需修复；重启反例及完整 checkout 地图检查仍为 INCOMPLETE。没有把后两项记成产品缺陷或通过。

EVIDENCE:

## 标准、范围与证据来源

- 按派发顺序读主仓库 reviewer 角色卡、AGENTS、`git show main:.project-map/tickets/T-104-workbench-plain-shell-pane.md`、两段 RESULTS，再读本 worktree 的 MAP、CONTEXT、intent。答案来自 ticket 和本轮必审条件；作者报告及脚本只用于找到原件。
- 目标是审查项目级普通终端的语义、安全边界、合并及验收充分性；不实现、不修复、不提交、不建 worktree、不派发 agent、不调用模型、不操作问题面板。用户授权原话按派发引用：`选"A 先补功能再打包"`。
- **Tracer bullet**：沿真实入口的 UI → IPC → daemon → PTY → 登录 zsh → 关闭／重启检查。**Deep modules**：检查是否复用现有窗格、凭据、存储和门禁，是否引入浅包装或平行实现。**Ubiquitous language**：使用项目、窗格、launch、task、attempt、人工介入，普通终端的角色为 shell。
- 审查时 worktree 起初干净，HEAD 为候选。源码阅读使用 `git show`、`git diff cc18d93db d54826223`、`git diff ea206484b8 d54826223` 和 `git show --cc edd469f6b`。本轮只在 `/tmp` 副本及获准的两个交付文件写入。
- 本地原件：`/private/tmp/t104-review-01-u7yc31m9/`。candidate、baseline 均由 `git archive <revision> workbench .project-map CONTEXT.md intent.md` 提取，没有 `.git`，没有改共享 checkout。Node 为 v26.5.0。首次提取因本机 Python 不支持 `extractall(filter=...)` 失败，未用于任何结论；失败目录保留。
- 本轮没有真实启动 Electron、后台或供应商 CLI。真实边界证据来自主控已有的沙箱外原件，以下明确区分本轮运行与原件核对。

## 逐项结论

| 项目 | 结果与依据 |
| --- | --- |
| 项目归属、不绑定 attempt、不经门禁 | PASS（源码及真实归档）。`panes.ts:127` 的 shell launch 中 task、attempt、session、fence、spec_rev 均为空；真实 UI 库的两个 shell launch 也都是空 task／attempt。创建走 `startShell`，不进入 claim／submit。 |
| 事件角色、正文隐私、记录范围 | 创建／关闭的 `role: shell`、不写输入正文和 agent 输入记录有证据；“只有创建和关闭事件”不满足，见 R1。 |
| 输入不算人工介入 | PASS（shell 场景）。daemon shell 分支直接调用 `shellInput`，不进入 `recordInput`、`appendUserInput` 或派发队列。UI 归档库的 user_inputs、user_input_ingress、dispatch_records 均为 0。 |
| 登录 zsh、无模型参数、全局配置 | PASS（源码及已有真实边界证据）。固定 `/bin/zsh -l -i`，只额外注入 A2A_PROJECT，清除继承的 A2A_*、GIT_CONFIG_*、CODEX_THREAD_ID；启动记录仅保存项目环境。继承普通进程环境不等于空环境。隔离 HOME 的登录／交互配置已在真实 zsh 中读回；没有产品写全局配置的路径。 |
| 显式关闭结束进程 | PASS（已有场景）。真实 UI 原件核对 shell 71335、前台 sleep 71556、后台 sleep 71555 均退出；后台测试也有两个 sleep 的独立 ps 核对。没有据此承诺任意忽略 SIGHUP 或脱离进程树的程序都能被结束。 |
| 重启显示“已结束”、不续接 | 旧 launch 的显示和禁用输入 PASS（源码、DOM、截图）；排除“另建一个 shell”的验收充分性 INCOMPLETE，见待运行反例。候选源码的 shell 恢复分支明确 continue，不调用启动器，未发现候选自动续接。 |
| 与 agent 标识分开 | PASS（五张图及源码）。普通终端显示“普通终端 / zsh / 项目目录”，没有 attempt、人工介入提示或队列放行按钮；历史 worker 仍单独显示“受管 worker / 历史 attempt / 只读”。 |
| 受管 worker 直接输入仍记人工介入 | 静态核对 PASS；本轮真实 worker 输入复验 INCOMPLETE。shell 分支之外的 recordInput、appendUserInput、panes.userInput 和门禁派生事件路径未改；不把只读历史 worker 截图当作可输入 worker 的证据。 |
| 唯一门禁与操作锁 | PASS（差异核对）。相对合入的 main，`workbench/src/gates/` 只有 CLI 命令表变化；core 中相对 cc18 的差异仅为 T-103 的 listProjects/listTasks。锁、fence、CAS、验收、集成实现未被本票改动。 |
| 地图 0 问题 | INCOMPLETE。开始和结束均退出 1：8 个缺失问题、0 stale，均指向稀疏未检出的 findings 或旧 grilling 文件。本轮没有补文件或修改地图；完整 checkout 的候选检查仍需主控完成。 |

## 安全与合并

- `daemon.ts:130`、`:134` 的 shell_start／shell_close 均显式要求 operator。更前面的匿名、launch、window 校验分别拒绝普通调用者、agent 请求和窗口凭据越权；shell 自身也被 `Panes.authenticate` 拒绝为 agent 身份。新增的不是靠 renderer 自报角色授权的通路。
- **cwd 分层结论**：新建终端 IPC 不接受 renderer 提供的 cwd 或 project，`main.ts:117` 从当前任务的后台快照取得 repo／project，再要求绝对路径。iframe／未知窗口也须经 windowTarget。未发现通过这个 IPC 把 cwd 注入到其他目录的通路。
- **可信 operator CLI 的范围较宽**：`daemon.ts:132` 将 operator 提供的 cwd 直接传给 `startShell`；`panes.ts:119`～`:121` 只校验项目号格式、已有绝对目录和 realpath，未向门禁查询该目录是否属于项目或任务 worktree。因此持有 operator 凭据者可以传任意已有绝对目录，也可传未登记的项目号。此处不能宣称“后台保证项目目录边界”，也不是已证明的匿名／renderer 提权。若主控要求这一边界覆盖管理 CLI，应在后台核对归属；本轮不擅自扩大权限合同或替主控裁定。
- 新增窗口级 IPC 只暴露无参数 `newTerminal()`，继续使用受信窗口主 frame、每窗格 key、窗口凭据和序号；不暴露 operator 凭据、通用命令、路径参数或全局配置接口。本地实际 main/preload 模块合同通过；iframe 反例另见变异。
- `git show --cc edd469f6b` 确认冲突解决同时保留了 projects_list／tasks_list 与 shell_start／shell_close，保留 catalog 只读查询不写请求事件，以及 window 载荷脱敏。CLI 的 noTask 白名单和参数表两边均在。相对 ea206 的 T-104 差异没有改写 T-103 的 listProjects/listTasks 或目录查询语义。

## 两处现有回归夹具：独立复现

原件为 `fixtures-results.json`，共 8 次运行。命令模板为：

```sh
node <副本>/workbench/tests/test_pane_dispatch_state.ts <新输出目录>
node <副本>/workbench/tests/test_conflict_panes.ts --product <副本> --output <新输出文件>
```

| 产品源码 | 旧夹具 | 修正夹具 |
| --- | --- | --- |
| cc18d93db | 两项均退出 1 | 两项均退出 0 |
| d54826223 | 两项均退出 1 | 两项均退出 0 |

- worker-dispatch 两边旧夹具都把假 PTY PID 123 交给真实 libproc，得到 `proc_pidinfo_failed_or_short / errno 1`；修正后为该假 PTY 配套提供假进程树。真实版本查询 exec 路径仍保留。该旧失败不是 T-104 引入的退化，也不计作 T-104 产品红态。
- conflict-panes 两边旧夹具均在 `new_attempt_binds_only_its_own_rollout` 报 `restore_argv_missing`；修正仅把 argv 从单独可执行路径补为 `['/fixture/codex', '-a', 'never']`。
- 逐行差异确认：没有删、改、放宽既有断言。原来的辅助进程、领导者更换、native session 选择、队列持久化先于写入等检查仍执行。夹具边界不能代替真实 PTY，但这两处修改本身没有削弱它们原来负责的隔离合同。

## 真实红／绿原件与截图

- 检查了 backend-03、merge-01、ui-01 的摘要及外置盘 UI 库、事件、driver、源码快照；不只读取 RESULTS 的结论。
- ui-01 的 15 个 source-snapshot 文件与候选逐字节一致，覆盖 main/preload/renderer/style、panes/daemon/store/cli、README 和本次测试；不因 run.json 的 HEAD 仍是合并提交而假定它代表另一个候选。
- ui-01-backend 的 known-bad 原件中，36 个 src 文件均与 cc18 对应；它在 CLI 参数解析处以 `Unknown option '--cwd'` 失败，这是新功能缺失的合同红态，不是 daemon 已收到并拒绝该命令的证明。UI 红态另在 T-103 后的 picker 基线上确认无按钮、无桥接名、无主进程 handler。
- ui-01-backend 的 privacy-mutant 原件中，36 个 src 文件相对候选只有 daemon 的 `input: eventInput(envelope.input)` 恢复为 `input: envelope.input`。场景完成真实输入与重启后，在 privacy 检查处报“shell 输入内容泄漏进事件流”，cleanup_complete 为 true。该坏实现确实被正文隐私断言抓住。
- 五张原图均已目视检查：red-no-terminal 无入口；green-terminal 有独立 nonce、正确中文空格 cwd、LOGIN=on、RC=loaded，并与历史 worker 分开；green-closed 移除了普通终端；green-project-shell 显示项目终端仍运行；green-ended 显示旧终端“已结束”、只读、进入按钮禁用。
- 截图支持显示结论。进程退出、记录表为空、无输入正文来自独立 ps、只读 SQLite 查询和事件流，不能由截图替代；截图也不能单独证明跨项目往返或没有额外新进程。

FINDINGS:

### R1 [P2] shell 的逐次输入元数据仍写入事件流，超出本轮要求的记录范围

位置：`workbench/src/daemon.ts:176`；通用请求日志还位于 `:437` 与 `:448`。shell 的分流发生在 `:181`，晚于 `window_request_admitted` 的追加。

本轮必审条件逐字为“事件流只有创建和关闭事件，角色为 shell，不记录输入内容”。候选虽删去正文，仍对 shell 的每个 window_input／composition／observation 记录请求元数据。实际 UI 库中 launch `e352c175-6bc1-4957-aa3f-06c4bce7c308` 有 4 条 `window_request_admitted`；seq 42 的记录明确包含 `command: window_input`、时间、序号和 request_id。该 launch 还含 window_opened、pane_layout_opened、pane_stop_intent、shell_exit_confirmed、window_closed 等事件。没有把元数据误报为密码正文泄漏。

这是源码和真实归档共同确认的合同不符。现有测试只排除正文 nonce 和少数 agent 事件，允许该候选通过；因此这些绿态不能证明“只有创建和关闭事件”。

最小修复方向：在 daemon 的事件采集层按已绑定 launch 的 shell 角色控制记录范围，保留内存中的凭据、序号与防重放检查；不要削弱 agent 的专用用户输入、人工介入或门禁事实记录。对创建／关闭之外的布局与进程诊断是否保留，须由主控明确对照本轮“只有”的要求处理，不能由 reviewer 默认为例外。增加一个以要求为准的事件类型检查，至少必须拒绝逐次 shell 输入的 window_request_admitted。

COUNTEREXAMPLE:

## 本轮变异

先在 `/tmp` 的候选上运行原 `test_t091_pane_ipc.mjs --contract shell`，退出 0。为避免该脚本内置变异自检先失败而掩盖当前变异的业务断言，另建 `ipc-direct.mjs`：保留同一 exercise 函数、独立夹具、所有业务断言和 main/preload VM 边界，直接运行候选 exercise；仅去掉外围旧版本与内置变异的自检流程。direct 好候选也先退出 0。

复现命令（从本仓库运行，以便只读 git show 获取旧合同）：

```sh
node --experimental-vm-modules /private/tmp/t104-review-01-u7yc31m9/ipc-direct.mjs /tmp/未使用的结果.json --source /private/tmp/t104-review-01-u7yc31m9/candidate --contract shell
```

| 单处错误实现 | 运行及结果 |
| --- | --- |
| M1：main 新建终端把 cwd 从 current.task.repo 改为 `/private/tmp` | 原完整合同及 direct 合同均退出 1；业务断言为 `Terminal cwd must come from the selected task`。没有把编译失败或依赖错误当成有效拒绝。 |
| M2：main 的 windowTarget 仅删除 senderFrame 与 mainFrame 的比较 | direct 合同退出 1，在 iframe 必须被拒的 `assert.rejects` 报 `Missing expected rejection`。完整脚本先在其内置变异自检处失败，该第一次结果也保留，但不单独用它证明 iframe 业务断言。 |
| M3：recover 的 shell 分支单独加一行 `this.startShell(record.project, record.worktree)` | 已在本轮 `/tmp` 下的 `mutant-restart` 副本构造，尚未运行真实后台。该变异另起新 launch，保留旧 launch 的 ended 状态；现有后台测试只检查旧 launch 和打开集第一项，疑似会漏掉。当前不宣称它已存活或已被抓住。 |

详细命令、退出码及错误在 `ipc-direct-results.json`、`ipc-mutations.json`、各 `*-direct.json` 与日志中；原件不覆盖。M3 的实际路径为 `/private/tmp/t104-review-01-u7yc31m9/mutant-restart`。

待主控执行：

```sh
bash evidence/2026-10-19-batch17/T-104/REVIEW-OUTSIDE-01.sh review-outside-01
```

该脚本重新 git archive 冻结候选，复制 node-pty 后只改测试副本 spawn-helper 的 755 执行位；不修改依赖原件。先跑好候选的完整后台验收，再跑同一测试对 M3，且独立查库确认第一次 daemon_stopped 后是否实际出现新的 shell_created。好候选必须先过；环境失败不计为抓住坏实现；若坏行为发生而测试仍 PASS，脚本报告 NO_GO。脚本不需要 Electron；如后续追加界面复验，仍须使用内置盘 Electron。脚本已通过 bash 语法与内嵌 Python AST 检查，本轮未执行它。

LIMITATIONS:

- R1 已足以拒绝本轮按给定必审条件给出 PASS；正文隐私、受管记录及进程场景的局部通过不抹去该发现。
- M3 仍待主控沙箱外运行；没有通过静态推断冒称验收已漏检。UI 测试也主要确认旧 launch 显示结束，尚无本轮实际变异结论。
- 未新跑真实可输入 worker 的“直接输入 → user_input → human_intervention”旅程；backend-03 的 controller-window 隔离验证与只读历史 worker 截图不提供这项真实边界证据。源码路径未改这一结论与运行证明分开报告。
- shell_close 会观察子进程并拒绝无法确认的退出，本轮仅核对已有正常 sleep 场景，没有运行忽略 SIGHUP、自然 shell 退出后遗留子进程或 daemon 突然死亡的场景；不据未运行场景新增已确认缺陷。
- 地图 0 问题要求尚未在完整候选 checkout 取得；稀疏 worktree 的 8 个问题不能记成 0，也不要求本只读 reviewer 修地图。

RULE:

本轮没有证据证明 R1 是项目已出现过的同类缺陷，不新增治理规则。可机械补强的检查应放在当前普通终端真实入口验收中：检查输入前后的事件类型范围；重启前后比较全部 shell launch／shell_created，不能只检查旧 launch 的状态。保留现有 nonce、拒绝路径、只读 SQLite 与独立进程证据。

## 结构完整性检查

按 design-integrity-review 路由，接受面已变化，主体使用 behavioral-acceptance-review；结构标记仍逐个检查。scanner 对干净工作树返回空 findings，只是定位结果，不作为候选通过证明。

检查了新增 recover catch、trace／退出记录失败处理、terminate／confirmShellExit 的等待与观察。异常会追加诊断或设置失败／unknown；退出轮询属于该层负责的关闭核对，没有新增自动启动 fallback、兼容双写、平行门禁或第二套输入记录器。nullable 迁移保留旧数据与追加式 trigger，真实后台合同也核对旧行不变且 update 被拒。新增 requireShellPane 是 IPC 身份边界的校验，未发现需要另造抽象的理由。除 R1 的采集分流过晚外，没有确认其他结构捷径；这些结论不外推到未运行的异常进程场景。

本轮交付只含本报告及 REVIEW-OUTSIDE-01.sh。没有 commit、checkout、reset、stash、push、模型调用或全局配置写入。

T-104 REVIEW NO_GO
