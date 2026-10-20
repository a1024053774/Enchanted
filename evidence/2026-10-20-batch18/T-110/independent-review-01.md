# T-110 第一轮独立审查

结论：**NO_GO，需修复一项 P2 缺陷**。已核实正常通知闭环与三个错误实现的拒绝；断连进入“未知”后，Dock 仍保留旧待答数量。不得把本次合同运行完成的 PASS 当成候选验收 PASS。

STATUS: FAIL
TARGET: `c5ac40c0b4cf60c30407af1a00953a297eb55005`；起点 `e3102389eda8952ea92cae4b373e14eaff898314`。

本次为干净上下文、只读 reviewer。依据 reviewer 角色卡、AGENTS.md、T-110 原文、T-108 Resolution、RESULTS.md 重建答案；使用 `git show`、`git diff` 阅读冻结候选。目标是核对 T-108 信号到通知的最小接线及反例；不实现、不修复、不接管主控，不审 T-112 的模型设置。验收要求包括：只提醒可信的等待用户回答、来源与点击目标一致、退出等待后清除、按问题去重、设置有效、不调用系统通知、不影响作答资格。主要未知是断连恢复及 Electron 的平台显示边界。

## EVIDENCE：已取得的证据

- 本地命令：`zsh evidence/2026-10-20-batch18/T-110/REVIEW-OUTSIDE-01.sh --local /private/tmp/t110-review-local-05.json`，退出 0。此处 PASS 表示审查脚本完成了预期检查；其中 `disconnect_probe.business_failure=true`，产品仍为 NO_GO。
- 冻结候选先通过 `test_t091_pane_ipc.mjs --source <私有副本>`，再运行三个单处错误实现。随后独立输入序列、`test_t108_questions.mjs`、`test_t107_sidebar.mjs` 均 PASS。T-108 包含 429 项 hook 失败案例、14 项作答生命周期。
- 私有副本通过 `git archive c5ac40c0b4cf60c30407af1a00953a297eb55005 workbench` 创建，没有新建 worktree。归档中原有的 hook 链接展开为普通文件；没有新建符号链接。合同的临时目录前缀改到该副本根目录，不改断言。三个变异每次均从原文开始。所有本轮副本已删除，仅保留结果 JSON。
- 主控提供的 `/private/tmp/t110-outside-03.json`：正常 Electron 闭环 PASS、关闭通知 PASS、隐藏通知变异被业务断言拒绝；模型和供应商调用均为 0。审查者回读了原件；13 个相关源码／测试文件与提交原文逐字一致，结果见 `/private/tmp/t110-review-search-01.json`。原件的 `source_head` 是提交前起点，因此此处依靠实际副本内容比较绑定候选，没有计算校验值。
- 上述真实入口使用 controller_start → 已安装 Claude → 本地假 API → 真实 Electron → 原 PTY，验证项目与会话的实际高亮颜色、问题 ID、单次 DOM 新增、从流程页点击通知聚焦原窗格、答复回执与后续输入、回答后清除、Dock 标签与开关。该运行由执行主控执行，审查者没有冒称自行运行。
- `python3 /Users/luckye/.agents/skills/design-integrity-review/scripts/design_integrity.py --cwd . --format json`：`findings=[]`。另做了调用链人工核对；扫描器安静不单独构成 PASS。

## FINDINGS：确认的问题

### F1 / P2：侧栏断连后，Dock 保留失去可信依据的待答角标

位置：`workbench/app/main.ts:166`，关联 `main.ts:40`、`notificationCenter.ts:29`、`notificationCenter.ts:40`、`renderer.tsx:461`。

可达过程：应用在后台，已成功观察一个等待用户回答的问题，角标为 1；随后 daemon 连接失败。`a2a:sidebar` 在 `await request(...)` 或 `!result.ok` 处退出，没有使 NotificationCenter 的 `waiting` 和 `active` 失效，也没有更新 Dock。renderer 的轮询错误路径却清空通知并把会话、项目改成“未知”。此时应用内已无可信待答状态，Dock 仍显示 1；之后前后台切换还会使用旧计数。若断连期间问题已回答或会话结束，旧角标也不能自动消失。

独立故障探针执行真实候选 main/preload 模块，只在传输边界注入 `reviewer-socket-unavailable`。先确认正常候选合同通过，再观察一次已成功显示的待答角标，令下一次 sidebar 请求拒绝，断言“Disconnected unknown state must clear Dock badge”。实际为 **1，期望为 0**，业务断言失败；不是依赖、导入或设置失败。完整输入、命令、退出码、堆栈在 `/private/tmp/t110-review-local-05.json` 的 `contracts`、`disconnect_probe` 中。

这违反本轮“未知不提醒”及后台角标显示当前待答数量的要求。根因在主进程对侧栏事实有效期的管理，renderer 单独清空通知不足以撤销主进程保存的提示状态。

最小修复方向：侧栏读取失败时，使对应状态目录的当前通知与待答计数失效，重算 Dock，同时保留问题的去重记录，并继续向调用方报告原始读取失败；不要伪造成功快照或添加自动重试。恢复后同一问题不得重新提醒。审查者未实施该修复。

已把真实 socket 断连、恢复及 DOM/Dock 断言加入 `REVIEW-OUTSIDE-01.sh`；该真实 Electron 探针尚未执行。本项当前证据层为实际 main/preload 模块加受控传输边界，不能写成已完成真实断连复验。

## 必审项逐项结论

| 项目 | 结论与依据 |
| --- | --- |
| 信号与可信度 | PASS。`sidebar.ts:120` 先经原 `agentState` → `questionState` → `currentTurnTrust`；只有获准的 `waiting_user_answer` 才附带同 submission 的问题 ID。NotificationCenter 不读终端文字、不做第二个可信度分类。未知、权限等待、等待主控回答及普通状态不进入正常提醒集合。 |
| 同时出现、高亮与点击 | PASS（主控真实入口原件，经本轮核对）。CSS 选择器优先级已修；通知点击仅复用 `selectAgent`，切回终端页并请求对应 pane 聚焦。 |
| 回答、取消、结束清除 | 正常状态投影 PASS；真实回答清除 PASS。取消／会话移除、结束由独立输入序列验证。断连的角标失效有 F1，不能整体 PASS。 |
| 同问题一次 | 正常轮询与重渲染 PASS；按问题 ID 去重，旧 ID 离开再回放不补发，新 ID 可提醒，关闭后不补发。`seen` 在主进程，普通 renderer 重载不会重建它。真正的刷新、renderer 重载与断连恢复组合尚未独立跑 Electron，保留 INCOMPLETE，已列入外部脚本。未要求进程退出后跨重启永久去重。 |
| 通知与 Dock 开关 | 正常场景 PASS。两个设置独立保存，关闭通知清空 active，关闭 Dock 立即清空标签；关闭期间观察到的问题不在重新开启后补发。 |
| IPC 与作答资格 | PASS。handler／bridge 名称仍为 22／23；仅扩展已有设置接口的枚举参数，限制 boolean 与 `notifications`／`dockBadges`。`windowTarget` 的发送者与主 frame 资格不变。点击通知不能调用 answer 或向 PTY 写入；`a2a:answer` → `target` → `window_answer` → `Panes.answerQuestion` 原有当前 attempt、身份、问题状态及每次写入的信任检查不变。 |
| 合同保留 | PASS。原窗格 key、跨窗口／iframe、只读、历史窗格、布局、凭据和作答检查未删减；旧“必须产生系统通知”的通知专属期望，按 T-110 改为应用内通知和禁止系统通知的合同，并增加反例。没有以此删除安全检查。 |
| 结构与范围 | 除 F1 外未确认其他结构问题。新增模块集中保存设置、待答与去重状态，界面只接收结果；没有新增重试、兼容入口或平行作答 API。NotificationCenter 是承担实际状态管理的 Deep modules 边界。Tracer bullet 沿用 T-108 的真实入口；Ubiquitous language 沿用“等待用户回答”“问题 ID”。设置页只加独立组件与少量接线，没有改 panes.ts、CLI 启动参数或模型／强度设置。 |

## 系统通知与 Dock 权限核实

本轮自行执行的精确检索，命令与原始 stdout、stderr、退出码保存在 `/private/tmp/t110-review-search-01.json`：

```sh
rg -n 'new\s+(window\.)?Notification\b|Notification\.(isSupported|requestPermission)|\bNotification\s*[,}]|requestAuthorization|NSUserNotificationCenter|UNUserNotificationCenter|showNotification|registerForAPNSNotifications' workbench/app workbench/src workbench/hooks
```

结果：**0 个匹配，rg 退出 1**。补充检索：

```sh
rg -n 'setPermissionRequestHandler|setPermissionCheckHandler|pushNotifications|setBadge|Notification' workbench/app workbench/src workbench/hooks
```

结果：仅有本地 NotificationCenter／组件／状态的命名及 `main.ts:46` 的 `app.dock.setBadge(...)`；没有 Electron Notification、Web Notification、APNS 或通知权限请求调用。T-108 的原生 hook 事件名不等同于操作系统通知 API。

作者引用的类型文档需要纠正解释：本机 `workbench/node_modules/electron/electron.d.ts:8098` 和 [Electron Dock 官方文档](https://www.electronjs.org/docs/latest/api/dock#docksetbadgetext-macos) 都说明角标生效需要通知权限。**它们不能证明“显示角标不需要权限”。**

“不主动请求权限”是另一个命题。本轮核对 [Electron 43.4.1 的 API 绑定](https://github.com/electron/electron/blob/v43.4.1/shell/browser/api/electron_api_app.cc#L1627) 和 [macOS 实现](https://github.com/electron/electron/blob/v43.4.1/shell/browser/browser_mac.mm#L464)：`app.dock.setBadge` 调到 `DockSetBadgeText`，直接设置 NSDockTile 的 badgeLabel，该路径没有请求授权。这支持当前固定版本不会主动弹出通知授权请求；不能扩张成所有 macOS 权限状态下角标一定可见。现有真实入口用 `app.dock.getBadge()` 回读标签，证明标签值，不足以独立证明拒绝权限时 Dock 的视觉显示。没有请求权限或修改系统设置。

## COUNTEREXAMPLE：错误实现与拒绝结果

三个变异均只改 `notificationCenter.ts` 一处，先通过未变异候选，再依次跑相同的 `test_t091_pane_ipc.mjs`。完整命令、修改前后文本、错误与退出码均在 `/private/tmp/t110-review-local-05.json`：

| 变异 | 单处错误 | 拒绝结果 |
| --- | --- | --- |
| unknown-notifies | pending 条件把 `unknown` 也收进来 | 退出 1；合同第 322 行未知状态下 Dock 应为 0，实际 1。通知本身因已有 ID 去重没有再出现，但错误的未知计数仍被拒绝。 |
| answer-keeps-notice | 把退出 pending 后的删除条件改为 false | 退出 1；`Other states do not notify`，通知应为 0，实际 1。真实回答后的同类错误另列入外部 Electron 变异。 |
| switch-ignored | `const enabled = this.setting()` 改为 true | 退出 1；关闭期间的新问题被偷偷保留，重新开启时 `Enabling while already waiting is not a new question` 应为 0，实际 1。 |

另外，独立序列用未出现在作者固定场景中的项目、会话与问题 ID，核对来源映射、不同 ID、移除／结束、旧 ID 回放和两个开关。它是纯逻辑证据，不冒充 daemon 重连。主控提供的隐藏通知变异在真实入口也被拒绝。

## LIMITATIONS：未完成与异常现场

- 新增刷新、renderer 重载、真实 socket 断连恢复，以及“回答后保留通知”变异的 Electron 复验未运行。当前权限要求 GUI 经升级执行，而本轮明确禁止申请升级，因此只交付外部脚本，没有启动 GUI，也没有请求权限。执行主控可运行：

  ```sh
  zsh evidence/2026-10-20-batch18/T-110/REVIEW-OUTSIDE-01.sh /private/tmp/t110-review-outside-01.json
  ```

  脚本固定候选，用内置盘 Electron、Python 3.9、`LC_ALL=C`，清空 Git 目录环境变量，只在私有依赖副本修改 spawn-helper 执行位；没有模型调用、截图、全局配置写入或主仓库 Git 写操作。外部模式的新增驱动与场景只通过 shell、Python 和 JavaScript 语法检查，未宣称运行通过。
- 地图启动及收尾检查均为 **8 problems、0 stale**；是该稀疏 checkout 缺 findings／grilling 文件与链接。T-110 的“status 0 问题”仍为 INCOMPLETE，需在完整 checkout 核对。本轮未改地图或扩大写入范围。
- `/private/tmp/t110-review-local-01.json` 保留了归档含历史 hook 链接而被脚本拒绝的准备失败；02 保留了未知变异确实业务失败、但脚本最初匹配了错误断言文案的判读失败；03 保留了私有副本尚未复制依赖导致缺 effect 的准备失败。04 为完整本地合同通过；05 新增并保存了 F1。早期失败没有算作产品红态，也未被覆盖。
- 真实入口原件 01 的 CSS 问题与 02 的磁盘不足没有被本轮通过结论抹去；03 是修后证据。本轮没有重写作者 RESULTS.md。
- 未发现需要额外上报的范围外新问题；既有稀疏检出缺口只在本报告记录，遵照派发要求未使用问题面板。没有提交、切换分支、reset、stash、push 或子 agent。

## RULE：能捕获该问题的检查

在现有真实 Electron 通知入口中加入“已显示可信问题 → 断开该夹具的 daemon socket → UI 明确未知且 Dock 为 0 → 恢复同一问题不重复提醒”的检查。作者现有 suite 只覆盖成功快照中的 unknown，未覆盖读取失败使主进程旧计数失效；本轮故障探针已给出这条缺失检查。暂未确认这是项目既有的重复缺陷类别，不新增治理规则。

T-110 REVIEW NO_GO
