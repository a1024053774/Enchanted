# T-110 第二轮独立审查

结论：**产品范围 PASS，未确认新的可达缺陷；票的完整验收仍为 INCOMPLETE。** 第一轮 F1 已由当前候选的真实入口红／绿证据关闭。唯一保留的票级缺口是：指定稀疏 checkout 的地图检查仍为 8 problems、0 stale，不能写成该目录已达到 0 问题。完整 main checkout 的检查为 0 problems、0 stale，详见下文。

STATUS: INCOMPLETE
TARGET: `aea89b9d51f7eab67d3ad4760e727ba4a275b16e`；分支 `exec/t110`；基线 `e3102389eda8952ea92cae4b373e14eaff898314`。第一轮对象为 `c5ac40c0b4cf60c30407af1a00953a297eb55005`。

本次为新的只读 reviewer 会话，无作者会话历史。按指定顺序阅读 reviewer 角色卡、AGENTS.md、T-110、T-108 Resolution、RESULTS.md，再用 `git show` 与 `git diff` 核对冻结候选及修复链。目标是检查可信提问到提醒的接线、断连恢复、作答传输和测试清理；不实现、不修复、不审 T-112 的模型／强度设计。验收答案来自 T-110 和 T-108 已有契约，作者新增测试只作为待核实的证据。主要未知是平台权限下的 Dock 视觉显示和稀疏检出的地图完整性。

## EVIDENCE：命令与结果

本轮自行运行：

```sh
zsh evidence/2026-10-20-batch18/T-110/REVIEW-OUTSIDE-02.sh --local /private/tmp/t110-review02-local-02.json
```

退出 0，审查脚本执行状态 PASS。该结果不是整张票已验收的替代。JSON 保存完整命令、退出码、stdout／stderr、各合同结果、变异文本和主控原件。

| 检查 | 结果 |
| --- | --- |
| 未变异候选 main／preload IPC 合同 | PASS，32 项 checks；先跑好候选，再跑三个变异 |
| 三个单处错误实现 | 均被业务断言拒绝，见 COUNTEREXAMPLE |
| 独立新项目／会话／问题 ID 序列 | PASS，来源映射、状态过滤、失效、去重、移除／结束及两个开关 |
| `test_t108_questions.mjs` | PASS；15 项主检查、429 项 hook 失败案例、14 项作答生命周期 |
| `test_t107_sidebar.mjs` | PASS，12 项 |
| `test_t110_window_sequence.mjs` | PASS，6 项；同入口拒绝修前 `4a6d6bb9e` |
| `test_t110_reconnect_view.mjs` | PASS，5 项 |
| `test_t110_snapshot.mjs` | PASS，5 项 |
| `test_t110_cleanup.py` | PASS，19 项；同入口拒绝修前 `92bc88208` |
| 冻结 diff 的 `git diff --check e3102389e aea89b9d5` | PASS |

副本用 `git archive aea89b9d51f7eab67d3ad4760e727ba4a275b16e workbench` 创建，没有 worktree 或私有 `.git`。归档内原有 hook 链接展开成普通文件；依赖复制成普通文件，没有创建链接。只在私有副本调整合同夹具路径和历史版本读取的 cwd，不改期望或断言。两个本轮私有副本均已删除，只留结果 JSON。

### 已回读、绑定当前候选的真实入口原件

`/private/tmp/t110-outside-08.json` 的 `source_head` 为本次完整候选，`source_changes=[]`。本轮将其保留的副本中 `workbench/app/`、`src/`、`tests/` 下 **466 个文件**与 `git show <候选>:<路径>` 原文逐字比较：全部相同，无缺失。没有计算校验值。该原件由执行主控在沙箱外运行，本审查没有冒称自行启动 Electron。

- 四个红态都命中业务拒绝：隐藏通知、断连角标保留 1、断连重载丢所选项目、重连作答因 `invalid_window_sequence` 被拒。均无窗口、daemon 或 CLI 清理错误。
- green PASS，16 项检查，包括实际高亮颜色、问题 ID、单次 DOM 新增、从流程页点击聚焦原窗格、刷新／重载／socket 断连恢复后的去重、Dock 标签、原 PTY 作答、首个最终回执和后续输入。
- disabled PASS，11 项检查；关闭期间不出现提醒，重新打开不补发，作答仍通过原入口。
- 入口为 `controller_start` → 已安装 Claude 2.1.304 → 本地假 API → 真实 Electron 43.4.1 → 原 PTY；模型与供应商调用均为 0，无截图。

`/private/tmp/t110-receipt-compare-01.json` 的整体 PASS 表示对照脚本满足预期，**不表示父版作答成功**。其中 `parent_answer_receipt=FAILED_INVALID_WINDOW_SEQUENCE`；e1 父版到达同一作答入口后超时，事件明确记录 `invalid_window_sequence`；修后版本的最终回执为 `ok:true`。两侧使用相同的显式刷新／重载动作。该原件绑定 `92bc88208`；与最终候选比较，产品源码相同，差别限清理辅助函数、新增清理合同及 runner，不能用它单独证明最终清理修复。最终清理由第八轮原件和本轮 19 项合同证明。

第一轮 F1 的完成依据是第八轮同场景：旧候选断连后角标为 1 被拒；当前候选断连后 UI 未知、通知消失、角标为 0，前后台切换不复活旧计数，恢复同一问题不补发，随后原窗格作答成功。

## FINDINGS：必审项结论

未确认需要修复的产品缺陷。

| 项目 | 结论与依据 |
| --- | --- |
| 信号与可信度 | PASS。`src/sidebar.ts:120` 先调用已有 `agentState` → `questionState` → `currentTurnTrust`；只有获准 `waiting_user_answer` 才取当前 active submission 的问题 ID。`notificationCenter.ts:27` 只消费该状态和 ID，不读终端文字、不做第二套可信度判断。未知、其他权限等待、等待主控、运行和空闲均不提醒。 |
| 高亮、通知与点击 | PASS。真实入口同时核对项目／会话高亮与通知，点击复用 `selectAgent`，切回终端并聚焦该 launch 的 pane。点击本身不作答、不写 PTY、不发输入凭据。 |
| 回答、取消、结束清除 | PASS。每次成功快照按 pending ID 删除 active；取消／移除／结束由独立输入与 T-108 合同覆盖，真实回答后的通知与高亮清除由第八轮覆盖。失败快照由主进程使同状态目录的通知中心失效，并重算角标。 |
| 同问题只一次 | PASS。主进程 `seen` 按问题 ID 保存，renderer 刷新／重渲染不重建它。断连清空 active／waiting，保留 seen；恢复只恢复可信待答计数，不重发旧通知。第八轮实跑刷新、重载、断连、重连组合。进程退出后的永久去重不在票的要求中，也未宣称已实现。 |
| 设置 | PASS。通知和 Dock 是独立 boolean 设置，保存在既有设置文件中；关闭通知清空 active，关闭 Dock 立即清空标签。关闭期间观察到的问题不会在重新打开时补发。设置页新增独立 `NotificationSettings` 区块，未改模型／强度部分。 |
| IPC 安全 | PASS。仍为 22 个 handler、23 个 bridge 名称，没有新通用执行接口。已有设置接口只增加 `notifications`／`dockBadges` 枚举；boolean、非法枚举、未知窗口及 iframe 均拒绝。`windowTarget` 的 sender／主 frame 检查不变。 |
| 作答资格 | PASS。`main.ts:419` → `target` → `sendWindowCommand` → daemon `window_answer` → `Panes.answerQuestion` 原链保留。可信度、问题 pending、原 session／submission／turn、input generation、当前 attempt／fence、每次写入前的检查均不依赖通知是否可见。关通知仍可正常作答，重复作答被拒。 |
| 合同只增不减 | PASS。原窗格身份、跨窗口／iframe、历史只读、空布局、关闭／创建竞态和作答检查均保留。旧“系统通知产生一次”的通知专属期望按用户决定替换为 app 内提醒及禁止系统通知；没有借此删除安全检查。 |

### 5b：92bc88208 的传输范围

PASS。`main.ts:120` 不再在排队时消耗序号；唯一新增的 transport 回调在 `src/transport.ts:31` 的 socket `connect` 之后、实际 `write` 之前执行。连接未成功的命令以原错误失败，未发送、未保存待重发内容，不消耗序号。连接已成功、结果未知的命令仍消耗序号；没有回退、复用或自动重发。命令请求 ID 逐次独立生成。

本轮实际 main 队列加实际 transport 的合同注入两次连接失败，再作答，观察发送序号从 1 开始；未知发送只出现一次，拒绝响应继续消耗已发送序号；后续正常发送序号为 `[1,2,3,4,5,6]`，请求 ID 不重复。pending release 允许后续输入使声明失效，但拒绝重复 release，原有并发语义未改。真实入口也明确用原 pane 的 resize 在断连期间取得 ENOENT，恢复后首个答复最终回执成功。

daemon 未在本票改动。`daemon.ts:223` 仍要求安全整数且严格等于 `window.sequence + 1`，随后独立拒绝复用的 request ID；两个标识在任何 await 前消耗。未知发送若没有被 daemon 接纳，后续命令可以安全拒绝，客户端不会为恢复可用性重置序号；本轮没有宣称未知结果下可无条件继续。

4a6d6bb9e 只改变 renderer 初始化顺序：先恢复主进程已绑定的 selection，再读取可能失败的 catalog；没有恢复 renderer 自造的 launch、attempt 或凭据。成功确认任务移除后仍清空选择。本地合同核对 task／paneKeys／layout／names 保留与移除；当前 pane 准入仍经 `requireCurrentPane`，旧会话的临时查看仍为 `viewOnly`，daemon 写入仍核对 current attempt／session／fence。保留本地视图不会把旧 attempt 升格为可写当前目标。真实跨 attempt 换代未在本轮另注入；上述准入源码未改，原拒绝合同保留。

### 5c：aea89b9d5 的清理范围

PASS。`tests/t108_cleanup.py:26` 的每次观察都先比较 pid、pgid、启动时间。仅这三个字段相同、stat 包含 E 或 Z 时允许 command 缩短，且该轮不发 SIGTERM／SIGKILL；进程必须实际消失才报告退出。普通存活态仍要求 command 完全相同。E/Z 后变成不同身份，或回到 command 不同的存活态，均拒绝；持续退出态在期限内不消失仍失败。

19 项合同覆盖 E/Z、TERM 后退出、三种身份字段变化、等待途中替换、恢复存活态、存活 command 不符、观察失败、超时与信号升级。它是 supplied ps／clock／signal 边界的证据；第八轮补足真实 CLI 清理证据。该修复没有许可向身份变化的 PID 发信号。

### 6：结构审查

PASS，未确认结构捷径。另对 `e3102389e..aea89b9d5` 的冻结 diff 调用技能扫描器的 `scan_unified_diff`，定位结果保存 `/private/tmp/t110-review02-structure-01.json`：生产代码仅三个异常边界 marker（main 172，renderer 461、577）。工作区扫描另标到本次审查脚本的异常记录／清理分支，不能拿工作区扫描代替候选扫描。

逐项核对：main 的 catch 由该层负责撤销失效快照带来的通知事实，随后重新抛出原错误；renderer 保留错误并显示未知；设置保存错误可见。均未伪造成功、吞掉错误或重试。NotificationCenter 承担去重、待答集合和设置，是有实际状态职责的 **Deep modules** 边界。跨 UI／IPC／daemon／PTY 的 **Tracer bullet** 沿用并复验 T-108 真入口；**Ubiquitous language** 沿用“等待用户回答”和问题 ID。没有兼容 API、双写或平行作答路径。未改 panes.ts、CLI 启动参数和模型设置；两个新增范围各落在传输层与测试清理层的根因位置。

## 系统通知与 Dock 权限

本轮自行在冻结候选副本检索，完整命令与输出在 local-02 JSON。以下展示相对路径形式：

```sh
rg -n 'new\s+(window\.)?Notification\b|Notification\.(isSupported|requestPermission)|\bNotification\s*[,}]|requestAuthorization|NSUserNotificationCenter|UNUserNotificationCenter|showNotification|registerForAPNSNotifications' workbench/app workbench/src workbench/hooks
```

结果：0 匹配，退出 1。

```sh
rg -n 'setPermissionRequestHandler|setPermissionCheckHandler|pushNotifications|setBadge|Notification' workbench/app workbench/src workbench/hooks
```

结果：退出 0，只有本地 NotificationCenter／通知组件／状态命名及 `main.ts:46` 的 `app.dock.setBadge(...)`。没有 Electron Notification、Web Notification、APNS、通知授权请求或 permission handler。T-108 的 CLI hook 事件名不等于系统通知 API。

本轮重新核对已安装 Electron 43.4.1 的 `electron.d.ts:8098` 及 [官方 Dock 文档](https://www.electronjs.org/docs/latest/api/dock#docksetbadgetext-macos)：文档明确提醒角标生效需要应用已有通知显示权限，**类型文档不能证明“显示角标无需权限”**。

“调用不会主动申请权限”由实现核实：[v43.4.1 API 绑定](https://github.com/electron/electron/blob/v43.4.1/shell/browser/api/electron_api_app.cc#L1627) 将 setBadge 直接绑定到 DockSetBadgeText；[macOS 实现](https://github.com/electron/electron/blob/v43.4.1/shell/browser/browser_mac.mm#L464) 仅设置 NSDockTile 的 badgeLabel，没有授权调用。这支持本固定版本不主动请求通知权限。真实入口的 getBadge 证明标签值，不证明所有 macOS 权限状态下的视觉显示；本轮没有修改权限或系统设置。

## COUNTEREXAMPLE：三个独立单处变异

均在新建的一次性 git archive 副本中，每次从候选原文开始，使用同一 `test_t091_pane_ipc.mjs --source <副本>`，未更改断言。

| 变异 | 单处修改 | 拒绝结果 |
| --- | --- | --- |
| unknown-notifies | pending 条件把 unknown 也收进来 | 退出 1；第 326 行未知状态 Dock 应为 0，实际 1。先前 ID 去重掩盖了重复通知，错误计数仍被拒绝。 |
| answer-keeps-notice | 退出 pending 后的删除条件改为 false | 退出 1；`Other states do not notify`，应为 0，实际 1。捕获离开待答后残留提醒。 |
| switch-ignored | `const enabled = this.setting()` 改为 true | 退出 1；`Enabling while already waiting is not a new question`，应为 0，实际 1。关闭期间偷偷保存的通知被拒绝。 |

不是依赖失败、导入失败或空集合冒充业务红态。首轮本地结果 `/private/tmp/t110-review02-local-01.json` 保留：好候选已过，unknown 变异也确实触发第 326 行断言，但审查脚本最初匹配了不存在的文案，故脚本判读为 INCOMPLETE。修正判读后另写 local-02，没有覆盖 01，也没有改产品或测试期望。

## LIMITATIONS：未执行与交接

- 本 reviewer 没有启动 GUI、申请升级或调用模型。当前候选的真实入口证据来自已核对并逐文件绑定的第八轮原件。新增真实 Electron 变异（回答后残留、忽略开关）在 `REVIEW-OUTSIDE-02.sh` 默认模式中，**尚未执行**；本轮三个必需变异已在实际 main／preload 边界合同被拒，不能把未执行的 Electron 变异写成通过。
- 外跑脚本的 shell 与内嵌 Python 3.9.6 语法已检查。主控若执行额外真实变异，可用新的路径：

  ```sh
  zsh evidence/2026-10-20-batch18/T-110/REVIEW-OUTSIDE-02.sh /private/tmp/t110-review02-outside-01.json
  ```

  默认模式先跑未变异候选和禁用场景，再跑两个错误实现；sticky 场景只省略断连步骤，避免去重清空遮蔽“回答后残留”，作答和清除断言保留。用内置盘 Electron、Python 3.9、`LC_ALL=C`；清掉 Git 目录环境变量；spawn-helper 执行位只改私有副本。私有根路径满足 `/private/tmp/t078-2-` 校验，结束删除本次副本，仅留结果 JSON。
- 开始与收尾对指定稀疏目录运行 `project_map.py status --root .` 都是退出 1，8 problems、0 stale；缺 findings／grilling 链接与文件。另自行只读运行 `status --root /Users/luckye/Documents/Code/a2a`，退出 0，0 problems、0 stale；其 HEAD 为基线 e3102389e。MAP、tickets、CONTEXT、intent、AGENTS、findings、grilling 在基线与候选之间无差异；新增 inbox 不改变此结论。但这不等于候选在完整 checkout 的 status 已执行。结果与精确命令在 `/private/tmp/t110-review02-map-01.json`，交执行主控处理票级验收，不由 reviewer 补文件或改地图。
- 检查期间冻结候选未变化；最终工作区只新增本报告与 REVIEW-OUTSIDE-02.sh。没有 commit、checkout、reset、stash、push、主仓库 Git 写操作、全局配置、问题面板或子 agent。

## RULE

第一轮 F1 所需的真实断连检查已经进入当前入口，且第八轮取得旧坏候选红态与当前候选绿态。本轮未发现新的重复缺陷类别，不另加治理规则。

T-110 REVIEW INCOMPLETE
