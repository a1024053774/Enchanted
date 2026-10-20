# T-107 第四轮独立审查

STATUS: INCOMPLETE
TARGET: `dc37cd6abd10bbb18fad282398924a1f041c34d1`（exec/t107）

**未发现新的可复现产品缺陷。** F1、F2、F3 已从原职责位置修复，第二轮 F4 也已改用既有根会话定位合同并取得旧红／新绿反事实。三个已知缺口仍真实存在：工作台还不能从现有结构化信号得到两种“等待回答”，真实 worker 派发没有保存具体父 launch，真实系统通知没有触发过。因此本候选不能报 PASS，也不能据局部通过关闭整张 T-107。

## 范围、候选与证据边界

- 按指定顺序阅读 reviewer 角色卡、AGENTS、T-107、T-095、RESULTS、前三轮独立审查、修复交接、地图、CONTEXT 和相关源码；答案来自票据及独立重建的反例，不来自作者会话。
- 完整候选先用 `git rev-parse HEAD` 核对为 `dc37cd6abd10bbb18fad282398924a1f041c34d1`，用 `git show` 和 `git diff` 阅读提交原文。其前三轮对象分别为 `3c3f2e9e1`、`f563fd518`，第三轮实际仍看到了旧 HEAD；本轮审查的是新提交，不是暂存区。
- 提交说明如实记录：作者是用户手动切换后的 Codex 会话，没有 A2A 启动绑定，由执行主控代为提交。这个披露不构成门禁或验收通过证据，但不冒充原 worker 的原生身份。
- 用户已明确“证据截图什么的都不要了，我也不会看”。本轮不生成、不要求截图；“真实入口”仍用实际 daemon、Unix socket、SQLite、trace 与 Electron runner 表示。
- 本轮没有调用模型、启动模型回合、调用子 agent、操作 Herdr、申请升级、写全局配置、checkout/reset/stash/push 或 commit。只写本报告、`REVIEW-OUTSIDE-04.sh` 和新建的 `/private/tmp` 现场。
- 环境：2026-10-19，macOS；Node v26.5.0、Python 3.9.6、Git 2.52.0。所有正式复验的 Git 子进程设 `LC_ALL=C`。模型调用和模型回合为 0。
- 应用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review、document-writing，并做 frontend-production 的侧栏主路径静态检查。

## FINDINGS

本轮没有发现新的 F1-F4 红态、IPC 越权或 Git/状态上调问题。以下三项是票据已声明、本轮再次核实的验收缺口：

1. **INCOMPLETE：两种等待没有生产状态分支。** `AgentState` 有 `waiting_user_answer` 和 `waiting_controller_answer` 枚举，但 `agentState` 没有任何生产路径返回它们；未答或来源不能核实的 `request_user_input` 保守返回 `unknown`。实际界面因此只显示“未知”，不能声称七种状态已经覆盖。
2. **INCOMPLETE：真实 worker 派发没有具体父 launch。** 层级只在能关联“认证发送 launch → 成功 assign 回执 → 实际派发目标”时建立；`daemon.ts:380 → Panes.dispatch → store.register` 的直接派发只保存目标 launch、文本和 source。没有绑定父会话的 worker/reviewer/monitor 正确进入“未归属”，但票据要求的完整主控层级尚不能验收。
3. **INCOMPLETE：真实系统通知没有触发。** 合同测试验证了只在进入 `waiting_user_answer` 时通知一次、关闭和重开后不补发旧等待，但工作台尚无可靠生产来源产生该状态。IPC Notification 是替身；主控自己的 electron-06 摘要是“转换和开关已验证、真实通知未验收”，与声明一致。

## F4：已从根修好

第二轮 F4 是 `basename(file) === <session>.jsonl` 比既有 Codex rollout 文件合同更窄：精确文件名的根问题保持未知，rollout 前缀的同一问题却被同 submission 的启动钩子上调成运行中。

候选现在把归属放在既有 `workbench/src/paneRecovery.ts`：

- `codexSessionFileName`（`:30-33`）统一接受既有 `<session>.jsonl` 后缀，rollout 前缀自然包含在内。
- `codexSessionOrigin`（`:35-46`）核对 `session_meta`、工作目录、metadata 会话 ID、文件后缀，再机械区分 `root`、已核实 `auxiliary` 和 `unknown`。
- 恢复定位 `nativeSessionFile`、实际采集 `Panes.scan`、侧栏 `agentState` 都调用这套模块，没有在 sidebar 另写一条文件名判断。
- 未经核实的来源不再被当成 auxiliary；辅助会话的 `task_started` 只更新辅助文件自己的 turn，不会清除根问题。未答问题在权限、待答或无法归属时返回 `unknown`。

同一实际 daemon/socket/Panes/SQLite/trace 入口只改变文件名，取得如下反事实：

| 候选 | 文件名 | 提问前 | 未答根问题后 | 结果 |
| --- | --- | --- | --- | --- |
| `f563fd518` | `<session>.jsonl` | running | unknown | 旧候选此例通过 |
| `f563fd518` | `rollout-…-<session>.jsonl` | running | **running** | 旧候选 rc 1，命中 `Unanswered root question must stay unknown under either native filename` |
| `dc37cd6ab` | `<session>.jsonl` | running | unknown | PASS |
| `dc37cd6ab` | `rollout-…-<session>.jsonl` | running | unknown | PASS |

F4 的 sentinel 同时包含同一 submission 的 `turn_submitted` 后 `turn_start_signal`，所以不是只测“没有问题”的空路径；它先要求提问前确实为 running，再要求记录未答问题后保持 unknown。发送和读取前后所有表、schema、trace 与 offsets 不变。

## F1、F2、F3 与 T-096

### F1：辅助会话不能清除根问题

根问题事件只有在文件已由 `codexSessionOrigin` 核为 root、该文件当前 turn 与 pane turn 一致时才进入 pending。只有 root 文件的 `task_started` 更新 turn。已核实 auxiliary 的问题被隔离；来源缺文件、metadata、工作区、CLI 来源或正确父会话时，问题进入 `uncertainQuestion`，最终仍为未知。`request_user_input_async` 的 `accepted:true` 也不被当成回答。

本轮 `test_t107_review_regressions.py` 的 `old-identity` 为 rc 1、`fixed-identity` 为 rc 0；实际 daemon 的 `identity` 模式加入辅助 start 后仍为 unknown。F1 的根问题清除路径已关闭。

### F2：侧栏读取只读

`Panes.status()`（`workbench/src/panes.ts:995-1023`）现在只返回保存的运行时和恢复事实，不再调用 `scan`。原生采集移到已有 PTY 数据回调、hook/process 观察和退出路径（`panes.ts:552-570`），属于原先的采集职责，不是新增侧栏后门。

`sidebarSnapshot` 只读取 `store.launches()`、事件表和 `panes.status()`。独立实际 daemon/socket 夹具保留未消费原生日志，连续读取侧栏两次；`state.sqlite3`、`membership.sqlite3`、`locks/t.sqlite3` 的 schema 和全部行、trace 字节以及 `pane.offsets` 均不变，`cleanup_complete: true`。`test_t107_review_regressions.py` 中 `old-readonly` rc 1、`fixed-readonly` rc 0。

### F3：完成条件能拒绝读取时写库

完成条件现在比较所有实际 SQLite 的表、schema、trace 和读取 offsets，而不是只看 tasks 与 user_inputs。本轮三个单处变异均在候选先通过后运行：

- `sidebarSnapshot` 开头加 `store.event('sidebar_read', ...)`：投影 rc 1，命中 `Sidebar read changed persisted tables or traces`。
- 最终 unknown 改 idle：rc 1，命中 `Missing signal must remain unknown`。
- 无派发事实时按窗格标题/执行主控角色猜父会话：独立探针 rc 1，命中 `Pane title or role alone must not infer a parent`，实际父为 `exec` 而不是 `null`。

另外直接运行了作者的完整红／绿重放：

```sh
T107_DEPENDENCIES=/Users/luckye/Documents/Code/a2a/workbench/node_modules \
  python3 -B workbench/tests/test_t107_review_regressions.py \
  --source . --summary /private/tmp/t107-r4-review-regressions.json
```

rc 0，摘要 PASS，现场 `/private/tmp/t107-review-fixes-_is0mx53`，12 项全部符合预期：旧 oracle 对加一行写库仍 rc 0，新 oracle 对同一变异 rc 1，实际 daemon 对写库变异也 rc 1。该结果用于补齐 F3 的旧缺口证据，不替代本轮正式脚本。

### 五条“未恢复”不是本轮退化

T-107 的真实 Electron 夹具刻意包含五个不能自动续接的 launch。逐窗格提示恰为两个“未恢复：restore_record_unrecognized”和三个“受管 worker 未续接；请由执行主控按中断恢复流程回收后重新认领”。它们分别来自既有 `restore_record_unrecognized` 与 `restore_managed_attempt_requires_reclaim`，与提交起点 `0967cd4` 的恢复代码一致；本候选在 `panes.ts` 的差异只有采集位置、根归属与 `status()` 去 scan，没有修改 recover/restore 判定。

本轮 `test_t096_restore.mjs` rc 0 / PASS，原正常登录、显式 fake profile、argv 全字段、零 PTY、历史和已知坏实现拒绝都保留。五个焦点视图均为只读，并各自显示准确提示；没有用“所有恢复错误放行”削弱检查。

## 必审项

### (1) 层级只来自保存事实

`sidebarSnapshot` 只关联：

1. `dispatch_records` 的实际派发目标；
2. `relay_requests` 中认证发送 launch 的 assign 输入；
3. `relay_results` 的成功 `ok:true`、`kind:"assign"`、`from/to`；
4. 启动记录中的 role、preset、project、task、attempt。

父与子必须同项目、同任务、preset 相符；收件人以控制器 preset 或 `role:thread` 表示。同一子有多个合法 sender 时归零，非法角色边和环也归零。没有从窗格标题、终端正文、角色地址或普通回复推断关系。

独立探针给两个 launch 相同伪标题“执行主控”，但没有派发事实，`worker.parent === null`；按标题猜父的变异被拒。无具体父 launch 的 worker/reviewer/monitor 进入“未归属”的任务组，不硬挂到执行主控。局部关系能正确显示，完整 worker 父子仍因采集接口没有父 launch 而为 INCOMPLETE。

### (2) 状态映射逐分支

`workbench/src/sidebar.ts:17-57` 按执行顺序：

| 条件 | 结果 | 核对 |
| --- | --- | --- |
| restoration `failed` / `pending` | 未恢复 | T-096 恢复事实优先。 |
| lifecycle `ended` | 已结束 | 生命周期事实。 |
| 无 pane、historical、failed、interrupted、lifecycle 非 running | 未知 | 不上调。 |
| `permission_wait` | 后续未知 | 同 native 的 start/idle stop 只清标记，不直接上调状态。 |
| root 文件 `task_started` | 更新该 root 文件的 turn | auxiliary 和 unknown 的 start 不清问题、不更新根 turn。 |
| root 且当前 turn 相关的 `request_user_input(_async)` | pending | 协议 event type、工具名、call_id、turn 是结构化事实；`accepted:true` 不算回答。 |
| 问题来源未知、文件/工作区/回合不能核实 | `uncertainQuestion` | 最终未知。 |
| 已核实 auxiliary 的问题 | 隔离 | 不影响根。 |
| permission、pending 或 uncertainQuestion | 未知 | 当前无法在这里合法区分两种等待。 |
| idle 且无 active、无 writing | 空闲 | 使用现有 host 状态。 |
| root 文件多于一个 | 未知 | 不任选其一。 |
| busy、active、非 writing、有 native，且唯一 root turn 与 pane/active.nativeTurn 关联 | 运行中 | 需要正向执行证据。 |
| 同上，但只靠 submission 之后的同 native start signal | 运行中 | start 必须晚于该 submission；旧 start 不算。 |
| 其余 | 未知 | 最终保守值。 |

没有用正则或自然语言关键词判断“用户/主控/正在思考”。唯一的正则只解析结构化 Git porcelain 数值或校验恢复 ID，不参与语义分类。未知到 idle 的单点变异被拒。

项目汇总顺序是：等待用户回答 → 等待主控回答 → 运行中 → 空集合或含未知则未知 → 未恢复 → 有空闲则空闲 → 已结束。项目行有另一个真实 running 会话时可汇总为运行中，但不会改写单个未知 agent；没有等待/运行的正证据时不能被上调。

### (3) 作者声明的缺口属实，T-095 不能直接接上

现有生产 `agentState` 没有任何分支返回 `waiting_user_answer` 或 `waiting_controller_answer`。根会话的结构化 `request_user_input` 只能说明“有未解决问题”，没有回答对象字段；仅凭 root/worker 角色猜“问用户/问主控”不符合票据。当前因此显示未知，缺口属实。

T-095 的 `scripts/agent-status` 确实实现了 Herdr 期的 `waiting_controller_answer`，但不能直接用于工作台自管 PTY：

- 要求 `HERDR_ENV=1`，从 `records/launches.jsonl` 取 Herdr launch 身份；
- 限定 Herdr pane、terminal、cwd、原生会话和前后读数稳定；
- 读取 visible/detection 两份 Herdr 屏幕，并要求机械面板标记与 Herdr `blocked` 互证；
- 工作台使用自己的 SQLite launch 和不调用 Herdr 的 PTY，没有这些身份与读屏边界。

准确说法不是“项目没有等待主控信号”，而是“Herdr 期有该信号，工作台尚未采集可直接互证的同等事实”。移植或补采集超出 T-107“不改采集方式”的范围。

### (4) Git 事实

`gitFacts` 使用参数数组执行：

```sh
git -C <repo> status --porcelain=v2 --branch --untracked-files=no
```

并设 `GIT_OPTIONAL_LOCKS=0`。分支、上游、ahead、behind 只读 porcelain v2 固定字段，不受显示语言影响。真实分叉夹具与 `LC_ALL=C git status -sb` 一致为 ahead 1 / behind 1；无上游保留 null，不编造 0。

独立不存在目录探针返回 `branch/upstream/ahead/behind = null`，同时保留具体 `无法读取 Git：…fatal: cannot change to…` 原因，没有猜成零或空闲。仓库自身本次 `LC_ALL=C git status -sb -uno` 与 porcelain v2 都为 `exec/t107`。这里只核对本地 upstream ref，不声称已经 fetch。

### (5) 通知

主进程只在每个 agent 从非 `waiting_user_answer` 进入该状态时发一次；同一状态重复轮询不重复发，`running`、`idle`、`waiting_controller_answer` 不通知。通知关闭期间仍更新观察状态，重新打开时不补发“打开前已经存在”的旧等待；之后离开再进入才再次通知。

设置保存在本窗口 `userData/sidebar-settings.json`，重开保留。IPC 合同对通知单次转换、关闭、重开和后续再进入均有断言。真实 OS 通知没有触发，electron-06 也只验证设置重开保留；此项仍是 INCOMPLETE。

### (6) IPC 安全与只读合同

新增名称只有 `a2a:sidebar`、`a2a:select-agent`、`a2a:notification-setting`，preload 对应三个显式方法，没有任意 channel、命令或路径参数。三个 handler 都先经 `windowTarget` 校验注册的 `BrowserWindow`、`webContents` 和 mainFrame；iframe、未知窗口和跨窗口 key 被拒。

- `sidebar` 无参数，只调用既有的只读 `sidebar_snapshot`；通知设置读取不是业务数据库写入。
- `select-agent` 只接受 launch 字符串，取 snapshot 后再核对 catalog 中 project/task/launch/role，并核对目标 task 的 launch。历史/结束视图创建为 `viewOnly` 临时窗格，不领取输入凭据、不保存布局，关闭也不发 `pane_layout_close`。
- `notification-setting` 只接受可选 boolean，写入本窗口 user-data 的固定文件，不接受路径。
- 未知 launch、错误任务、跨项目、历史页面领输入凭据和保存布局的拒绝都保留。

合同从 17 handler / 18 bridge 扩到 20 / 21，旧名称和旧拒绝检查没有删减。新增接口扩大了三个小接口的本地 IPC 面，但没有打开任意门禁命令、任意仓库路径或 renderer 可见凭据。`sidebar_snapshot` 走既有匿名只读 socket 边界；实际读侧全表零写入。

### (7) design-integrity-review

对冻结工作树运行：

```sh
python3 /Users/luckye/.agents/skills/design-integrity-review/scripts/design_integrity.py \
  --cwd . --format json
```

结果 `{"root":"/Users/luckye/Documents/Code/a2a-wt-t107","findings":[]}`。定位器不是通过证明，因此继续逐项追踪了本提交的异常边界和职责：

- F4 没有新增兼容 shim，而是回收 sidebar 的平行判断到既有 `paneRecovery`；恢复、采集、显示共用同一个归属定义。
- F2 没有新增“只读版 scan”或 fallback，而是把采集放回 PTY/hook/process/exit 的既有所有权，`status()` 变成纯快照。
- Git、focus、设置和采集错误均保留具体错误或转成未知；没有吞掉错误后报成功。
- 三秒刷新是事实轮询，不是写操作重试；没有新增门禁旁路、双写、无依据 retry 或第二套状态 API。

本轮没有确认新的结构缺陷。

## 复验命令、变异与主控原件

正式复验脚本是 `evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-04.sh`，固定候选 `dc37cd6abd10bbb18fad282398924a1f041c34d1`。它从 `git archive` 建一次性副本，不建 worktree；若 HEAD 改变则拒绝，避免自动接管新提交。

命令：

```sh
bash evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-04.sh local
```

正式现场：`/private/tmp/t107-review-outside-04-tumqofpn`，摘要：`review-summary.json`。脚本最终 rc **2** 表示实现了的局部切片通过但整票 `INCOMPLETE`，不是环境失败。

| 检查 | rc / 观察 |
| --- | --- |
| 候选 projection，真实 Git/SQLite、未知/层级/汇总 | 0 / PASS |
| 候选 main/preload IPC，20 handler / 21 bridge，历史坏侧栏拒绝 | 0 / PASS |
| 实际 daemon `readonly` | 0 / PASS；未消费日志下连续读取零写入 |
| 实际 daemon `identity` | 0 / PASS；辅助 start 不清根问题 |
| 实际 daemon `filename` / `rollout` | 均 0 / PASS；提问前 running，未答问题后 unknown |
| 候选单点反例测试 | 0 / PASS |
| T-096 恢复合同 | 0 / PASS；五条精确拒绝保留 |
| 旧 F4 精确名 | 0；提问前后符合预期 |
| 旧 F4 rollout 前缀 | 1；business assertion 指出仍为 running |
| 不存在目录的 Git 事实 | 0；null 数值与具体原因 |
| 标题猜父独立探针 | 0；没有派发事实时 parent=null |
| 变异 unknown→idle | 1；`Missing signal must remain unknown` |
| 变异按标题猜父 | 1；`Pane title or role alone must not infer a parent` |
| 变异侧栏读取写库 | 1；`Sidebar read changed persisted tables or traces`，新增 `sidebar_read` 行被捕获 |

三个变异都在候选本身先通过后运行，并由业务断言拒绝；没有把崩溃、缺依赖或初始化失败当作拒绝。

脚本还提供沙箱外模式：

```sh
bash evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-04.sh electron
```

它使用内置盘 Electron 43.4.1、隔离源码和状态目录，先运行冻结候选的真实 Electron 旅程，再运行读取写库变异并要求业务断言失败；全部输出进新的 `/private/tmp` 目录，不截图、不调用模型、不操作 Herdr。

**本轮没有在 reviewer 沙箱内运行 electron 模式，未申请升级。** 主控提供的 `electron-06-summary.json` 记录 implemented slice PASS、六项局部检查 PASS、总状态 INCOMPLETE、`cleanup_complete: true`、`model_calls: 0`，三条 limitations 与上述三个缺口一致。这是主控已运行原件，不是本轮 reviewer 独立 GUI 通过，也不把整票 INCOMPLETE 上调。

## 收尾限制

- 本轮没有独立运行真实 Electron；只能引用主控 electron-06 摘要，等待主控运行新的 `REVIEW-OUTSIDE-04.sh electron` 才能取得本候选的 reviewer 脚本真实入口原件。
- 无真实模型信号证明两种等待；无真实 worker 父 launch 绑定；无真实 OS 通知。三项均属于整票验收缺口。
- 真实 CLI 长时运行、读屏、200% 缩放和长期性能不在本轮通过主张内；截图按用户裁定不要求。
- `git diff --check` rc 0。复验脚本 `bash -n` rc 0，UTF-8 无 BOM、无替换字符、无行末空白。工作树只新增指定报告和脚本，HEAD 仍为冻结候选。
- 开场/收尾 `project_map.py status --root .` 均 rc 1，仍是同样的 8 个稀疏 checkout 缺文件链接，stale living docs 为 0；不能写成“0 问题”，本轮未改地图。地图中的既有 intent 构建约束仍保留外置盘旧文案，与当前 AGENTS 的内置盘裁定不一致；这里只报告执行主控，不改范围外文档。

防复发检查已经落在完成条件中：rollout 文件名变换与同 submission 启动钩子必须保持 unknown；辅助会话和未知来源不能释放根问题；侧栏读取比较全部持久化表、schema、trace 和 offsets；未知改空闲、标题猜层级、读取写库三个单点变异必须由业务断言拒绝。后续修复三个声明缺口时，应对新候选重新取红绿，不用本轮的局部 PASS 替新实现背书。

T-107 REVIEW INCOMPLETE
