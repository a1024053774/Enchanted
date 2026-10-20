# T-112 第二轮独立审查（2026-10-20）

STATUS: INCOMPLETE

TARGET: `/Users/luckye/Documents/Code/a2a-wt-t112`，分支 `exec/t112`，冻结候选 `5f19062f52154914123e3796fdff87caaa22fc1f`。仅审 `4bdf0721c..5f19062f5` 中的合并保真、清理放宽和焦点诊断变化，不重审第一轮已覆盖的设置实现。

合并保真、清理身份约束和结构检查均为 PASS，未确认需要作者修复的产品缺陷。前台角标失败的根因仍为 INCOMPLETE：没有发现题述“侧栏晚返回覆盖前台清零”的代码路径，但失败原件缺少焦点信息，不能把它归结为高负载等待问题，也不能用后一次绿态消除这项未知。整体结论因此保留 INCOMPLETE，不作集成决定。

EVIDENCE:

目标是确认两个父提交的已承诺行为同时保留，并核实新增清理例外的边界；非目标是实现、修复或复验全部 T-112。重大未知是失败时 Electron 是否真正取得并保持前台焦点。读取了项目地图、统一术语、intent、T-110/T-112 ticket、第一轮报告第二节及本轮相关源码、测试和原始 JSON。应用 design-integrity-review 的结构项；因涉及验收面，按 behavioral-acceptance-review 检查独立 oracle 和已知坏实现。报告按 document-writing 做 UTF-8 交付检查，没有调用其他 reviewer。

## 合并冲突逐块核对：PASS

实际使用 `LC_ALL=C` 的 Git 原文，包括：

```sh
git diff 4bdf0721c 5f19062f5 -- workbench/app workbench/src workbench/tests
git show --cc 363c4944e -- workbench/app/main.ts workbench/app/renderer.tsx workbench/tests/test_t091_pane_ipc.mjs
git diff 363c4944e^1 363c4944e -- workbench/app/main.ts workbench/app/renderer.tsx workbench/tests/test_t091_pane_ipc.mjs
git diff 363c4944e^2 363c4944e -- workbench/app/main.ts workbench/app/renderer.tsx workbench/tests/test_t091_pane_ipc.mjs
git show 22783a1ee -- workbench/tests/t108_cleanup.py workbench/tests/test_t110_cleanup.py
git show 5f19062f5 -- workbench/tests
```

| 冲突块 | 两个父提交与合并结果 |
| --- | --- |
| main 的 handler 注册块 | 相对第二父 `1267805a2`，main 只增加原 T-112 的 `a2a:execution-settings` handler。T-110 的 focus/blur 重算、双通知偏好和更新角标均原样保留；T-112 的主 frame/窗口绑定、严格四键、operator 身份、错误透出均在。 |
| renderer 的 Window 类型块 | 同时保留 `executionSettings` 和带 `notifications/dockBadges` 偏好的 `notificationSetting`。 |
| renderer 的设置 JSX 块 | 同时保留 `<ExecutionSettings />` 和 `<NotificationSettings />`。相对第二父整个 renderer 只多设置组件、类型的 import、桥类型及一个组件实例；通知展示、点击聚焦、失效及断连保留视图代码没有删除。 |
| test_t091 的 request fixture 块 | 同时接收 `nextSequence`，模拟连接成功后分配序号；保留 sidebar 的 transport/refused 两类失败注入，并加入 execution_settings 读写 fixture 与 operator 断言。 |
| test_t091 的主调用/变异调用块 | 主候选调用移到变异前，全部当前候选 exercise 调用传入 `withExecution=true`；旧 revision 仍使用各自旧合同。不存在仅执行变异却漏跑候选的路径。 |
| test_t091 的检查列表/数量块 | 精确 handler/bridge 集合各增加设置入口，数量各加一；没有放宽为子集。两父的新增业务断言都在，相对第二父没有删除业务断言。 |

第一父原先断言系统通知次数的五处被 T-110 的应用内通知、问题 ID 去重和系统 API 调用数为 0 的断言取代，符合本轮已合入的 T-110 契约，不能视为丢失功能。相对第二父的测试变化只有设置合同及相关调用参数/数量，没有削弱其通知、失效、Dock、窗口身份和布局断言。

额外核对 preload：相对第二父只增加 executionSettings 桥；notificationCenter、AppNotifications、transport、sidebar 及通知样式无差异。主进程侧栏失败时使同后台的中心失效并重新抛出原错误（main.ts:178–196）；transport 只在 connect 回调取序号，未知发送结果不重放；renderer 先应用本地 selection，再读 sidebar，只有成功读取确认任务消失才清视图。上述 T-110 路径均完整保留。

## 前台角标失败：归因 INCOMPLETE

失败原件 `outside-merge-t110-native-03-executor-rerun.json` 的 source_head 是 `22783a1ee`，green 在 `Foreground after reconnect clears badge` 超时，最后 badge=1。它没有 native_focus 或事件时间线。该版本与当前候选的产品 main 相同；`5f19062f5` 只增加测试诊断，没有修产品。因此失败必须保留。

`outside-merge-t110-native-03.json` 精确绑定当前候选，四个红态被相应业务断言拒绝，green、disabled 均通过。其 green 的最后一次前台动作时间线如下（UTC）：

| 时间 | 观测 |
| --- | --- |
| 18:00:30.230 | foreground 命令前：hidden=true、focused=false、focused_window=null、badge=1。 |
| 18:00:30.247 | 命令已返回：仍 hidden=true、focused=false、badge=1，只有 visible=true。 |
| 18:00:30.252 | did-become-active：focused=true、focused_window=1，但 badge 暂为 1。 |
| 18:00:30.267 | browser-window-focus：badge=0；随后 window:focus 也是 0。 |
| 18:00:30.268 | inspect：focused=true、badge=0。 |

这证明 `t108_questions_driver.mjs:91–92` 的 show/focus 调用返回不代表操作系统已完成激活。成功例从命令返回到 focus 重算约 19 毫秒；它没有证明原失败只需要多等 19 毫秒。`run_t103_picker.py:88–96` 已轮询约 20 秒，不能无证据地建议简单加长等待。

代码上，`main.ts:40–46` 的每次重算都同步读取 `BrowserWindow.getFocusedWindow()`；sidebar handler 是在 await 返回后调用该函数，而不是在请求开始时缓存焦点。只有这一处写 Dock badge。因此：若 focus 先到，后返回的 sidebar 仍读当前焦点并写 0；若 sidebar 先到，后到的 focus 事件会写 0。没有发现二者先后顺序本身能让持续有焦点的窗口保留 badge=1 的路径。即使 focus 回调时原生焦点尚未稳定，后续正常 sidebar 轮询也再次取当前焦点，而非沿用旧结果。

现有证据不能区分失败时“激活未完成或随后失焦”“原生焦点/事件状态异常”及其他平台行为。主控给出的负载约 10/5 只是相关观测，不能当因果证据。新增诊断没有 focus、重算或重试动作，但同步写日志仍会改变少量时序，成功运行也不能排除时序敏感问题。

最小后续证据是：在原前台动作失败时取得现有诊断中的 hidden、focused、focused_window、badge 及前后 focus/blur 事件。若持续 focused=true 而 badge=1，应按产品/原生事件路径处理；若未取得或未保持焦点，应检查测试动作完成条件及激活环境。不要先改产品重试或只延长超时。本轮没有运行原生 CLI/Electron，也没有把这项未知编成已确认缺陷。

## 清理放宽：PASS

`t108_cleanup.py:28–50` 在检查 E/Z 和 command 之前，逐个核对 pid、pgid、started；任何一个变化立即抛错。普通 Claude 路径只接受严格 `(数字.数字.数字)` 标题；版本安装路径还要求标题版本与原 executable 文件名相同。无关 owner、任意新 command、畸形标题均仍拒绝。ppid 变化可接受是进程被重新托管的既有语义，不替代上述三个身份字段。

每次准备 TERM/KILL 前重新观察，只对 owner 的精确 PID 发信号，不发进程组信号；E/Z 只等待，不提前宣告退出。33 例覆盖初始身份变化、TERM 后身份变化、持久运行/退出超时、观察错误透出。新例外没有给已观察到身份变化的进程发信号的路径。本结论不把既有 ps→kill 间隙宣称为原子操作。

## 原件与本轮独立运行

主控的 `outside-merge-regressions-03.json` 绑定当前候选，记录 cleanup、execution、ipc、questions、reconnect-view、window-sequence、构建及两个原生入口命令 rc=0。读取对应原件确认 PASS；本 reviewer 不冒称这些是本人重跑。T-112 原生结果含 baseline_high 的 EXPECTED_RED，factory、ui-settings、override、invalid 的 PASS；reviewer good 实际写候选而 protected 保持 unchanged，bad 放开父目录后实际越界，同一 boundary_oracle 分别 true/false。不是只看两例 status=OBSERVED。

本轮实际执行：

```sh
zsh evidence/2026-10-20-batch18/T-112/REVIEW-OUTSIDE-02.sh
```

Node `v26.5.0`，`/usr/bin/python3` 为 `3.9.6`，Git 环境 `LC_ALL=C`。脚本从固定候选 git archive 创建 `/private/tmp/t112-review02-6a08cqpz/candidate`，拒绝链接和特殊文件，不依赖 rg，不复制依赖。脚本保留完整 argv、退出码和结果输出，已加入候选与验收文件变化拒绝检查。

| 本轮检查 | 结果 |
| --- | --- |
| 实际 main/preload 的 T-091 全合同 | rc=0，PASS。包含设置输入、窗口/iframe、通知失效、角标与既有已知坏实现检查。 |
| 实际 main 队列与 transport 的 window-sequence 合同 | rc=0，PASS；连接前失败不耗序号、未知发送不重放、release 并发及 request ID 均覆盖。 |
| 实际 renderer refresh 的 reconnect-view 合同 | rc=0，PASS；断连保留原 selection/layout/names，成功确认删除仍清除。 |
| 清理合同 | rc=0，PASS，33 例；两份旧实现均被对应断言拒绝。 |

以上是提供 Electron/socket/ps/clock 边界的合同证据，不能代替原生焦点边界。精确子命令可由脚本重建；例如 `node --experimental-vm-modules <仓库>/workbench/tests/test_t091_pane_ipc.mjs <临时根>/ipc-good.json --source <临时根>/candidate`。本轮所有私有副本和输出在脚本 finally 中删除，`fixture_removed=true`；结果摘要保存在本报告，先前原件未动。

COUNTEREXAMPLE:

两个变异均只修改临时副本的一处；使用相同业务检查，不因缺依赖、语法或启动失败被拒：

| 变异 | 实际命令与结果 |
| --- | --- |
| 丢掉前台事件重算 | 从 main 删除 `app.on('browser-window-focus', updateDockBadge)`；同一 T-091 命令，输出改为 `lost-focus-recompute.json`。rc=1，命中 `Foreground clears Dock badge`，实际 1、期望 0。 |
| 丢掉启动时间身份核对 | 从 cleanup 的身份字段列表删 started；`/usr/bin/python3 -B -c <脚本内 probe> <仓库>/workbench/tests/test_t110_cleanup.py <临时根>/candidate/workbench/tests/t108_cleanup.py`。rc=1，命中 `reused_started_live_claude_title` 的 Unexpected cleanup signals；模拟边界记录了本应为零的 TERM/KILL。没有真实发信号。 |

FINDINGS:

无确认的 P0/P1/P2 产品或结构缺陷。焦点失败的归因缺口见上，不将它升级为已确认竞态，也不判作已解释的测试偶发。

结构检查 PASS：NotificationCenter 用小接口隐藏问题去重、待答集合、失效和偏好存储，符合 Deep modules 的用途；沿用同一侧栏可信状态与已有设置文件，没有另一套分类器或双写。transport 的 nextSequence 回调把分配放到实际发送边界，不新增重试、兼容路径或第二套发送 API。sidebar catch 清除失效状态后重新抛错，没有吞异常。新增清理标题例外严格位于测试进程身份检查内，没有放宽产品启动权限；诊断读取失败把结果置 INCOMPLETE，没有静默跳过证据。

Tracer bullet 的 UI→IPC→后台→设置→原生派发已有本候选原件，本轮没有用合同测试重新冒称端到端通过。Ubiquitous language 沿用角色设置、启动记录、窗格、问题身份与候选副本。

LIMITATIONS:

- 尚未取得一次带焦点时间线的失败运行；原失败不能从后来成功的时间线反推。没有重复模型、原生 CLI 或 GUI 运行，没有申请升级。
- session 开始和结束的 project_map status 都是 8 个既有缺失项、0 stale，和第一轮一致；未改地图、术语或缺失文件，也不据此声称全票地图验收通过。它不属于本轮合并产品缺陷。
- `git diff --check 4bdf0721c 5f19062f5 -- workbench/app workbench/src workbench/tests` rc=0。开始与结束 HEAD 相同，产品 tracked 文件没有脏改；既有未跟踪的 `outside-merge-*-03.json` 保留。本轮仓库只新写本报告及复跑脚本，未 commit、push、submit、集成、操作问题面板或写全局配置。

RULE:

无需新增治理规则。T-091 的前台角标断言和清理合同的 changed-started 反例已分别拒绝本轮两个错误实现；原生失败保留现有 timeline 观测即可补齐归因证据。

T-112 REVIEW INCOMPLETE
