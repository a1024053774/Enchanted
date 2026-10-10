---
id: T-065
title: 窗口不高又开着问题面板时，会话空态的输入框要在首屏可见
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

[T-063](T-063-reopen-stall-and-empty-state-overlap.md) 修好了空态文字与 logo 的重叠，做法是让空态按正常流排布、放不下时整体滚动（fork `e94a0efc3`）。副作用：1280×900 且开着问题上报面板时，输入框被挤到首屏以下，要滚动才看得到（`evidence/2026-10-09-batch11/T-063/` 的 `green07-resume-1280x900*`、`green11-pinned-resume-*`）。用户看过后不接受（逐字："不能"）。

改成：空间不够时，先收起或缩小次要内容（导入横幅、logo、标题），输入框始终在首屏可见；同时不再出现 T-063 修掉的重叠。

## Acceptance

- [x] 红态在先：在 `e94a0efc3` 上，1280×900、开着问题面板（至少 3 条待决定问题）时，输入框不在首屏内，用例失败；保存输出与重放命令。
- [x] 修复后，1600×1050、1280×900、以及 1280×720 三种视口，开或不开问题面板，输入框都完整在首屏内、可直接点击输入，不需要滚动。
- [x] T-063 的反例照常通过：横幅、logo、标题、输入区两两相交面积为 0；加长中文文案也不重叠；窗口尺寸来回改变后仍成立。不能靠把文字藏掉来通过：被收起的内容要么完整可见，要么明确是按设计收起（在 RESULTS 写清哪种视口收起什么）。
- [x] 截图作证，外观由用户判断。
- [x] 既有套件、typecheck、lint 通过；对上游文件的改动列清单（预计仅 `ChatView.tsx` 的空态块）。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：面板宽度改变挤压会话列；问题条目很多时面板自身滚动；中文与英文文案长度不同；浏览器缩放 125%。
- 测试数据与 profile 放在哪个盘按现有约定；不需要做启动耗时对照（用户 2026-10-09："没必要测"）。
- 与 T-057 同改任务窗口时，同一文件同一时间只能有一个写入者，由执行主控串行安排。
- 授权来源：用户 2026-10-09 对"输入框要滚动才看到能否接受"答"不能"；`ready_by: ideation`，`ready_rev: 1`。

## Resolution

INCOMPLETE，待主控关闭。依据 ready_rev 1 与 [执行主控决定 01](../../evidence/2026-10-09-batch11/T-065/controller-decision-01.md)。一次独立审查对冻结候选 fork 9654e1c63 / a2a e18fead 返回 FAIL（P1：窄列空态工具栏文字/按钮相交）。已修复为换行并保留分支最小内容宽度，交付 fork `7a3a13249e562bf2d7f9ff4cb024f39b13d62434`；按 brief 没有自行追审，由执行主控审 [修复 diff](../../evidence/2026-10-09-batch11/T-065/review-repair.diff.patch)。

修复版的三种窗口开/无面板、三种 125% device-metrics 模拟、加长中文、resize 往返、400px 窄列、15 条待决定问题及回复框/按钮完整可达均通过；可见工具栏按钮面积为 0，已审坏版本被同一 oracle 因业务相交拒绝。相关单元 35/35，浏览器选中 5/5（208 项过滤未跑），全 workspace typecheck、lint、fmt:check 通过。上游只改 ChatView.tsx 空态布局及控件组装；经批准另改 a2a IssuePanel.tsx、TaskWindow.tsx。真实菜单缩放未证明，外观由用户判断。详见 [RESULTS](../../evidence/2026-10-09-batch11/T-065/RESULTS.md)、[重放](../../evidence/2026-10-09-batch11/T-065/REPLAY.md)、candidate-binding.json 和独立审查原始 FAIL。

**执行主控关闭（2026-10-10）：PASS（独立审查 FAIL 后的修复由执行主控自审）。** 依据 ready_rev 1（用户原话"不能"）与主控决定 01（`T-065/controller-decision-01.md`）。worker `s11-t065` 交付 fork `95d525c56`/`9654e1c63`/`7a3a13249`（上游 `ChatView.tsx` 空态块；a2a `IssuePanel.tsx` 允许收缩、`TaskWindow.tsx` 为会话保留至少 192 CSS px），a2a 证据 `e18fead`（冻结）/`7e644fe`/`e0dde55`。红态：`e94a0efc3` 上 1280×900、3 条问题时输入区在首屏外。绿态：1600×1050、1280×900、1280×720 及三者的 125% 模拟，开/不开面板，输入区都完整在首屏、可点击输入；横幅/logo/标题按剩余空间整块收起（规则与各视口收起内容见 RESULTS），空间充足时不收；6 对相交面积 0；15 条问题时面板内滚动、首末题按钮可完整显露。独立审查一次 FAIL（P1：400px 窄列与两个 125% 小尺寸下工具栏按钮相交）；修复仅两处 class（工具栏 `flex-nowrap`→`flex-wrap`，分支 slot `min-w-0`→`min-w-fit`），已审冻结版被同一 oracle 拒绝（相交 2664.6/127.6/556.2 px²），修复版三组矩阵全为 0。主控自审修复 diff：只作用于空态的项目/分支托盘，分支工具栏不显示时 slot 为空、不占宽，不影响已有会话；并审阅 `toolbar-final01-ui-1280x900-open.png`，输入区在首屏。相关单元 35/35、浏览器选中 5/5、typecheck、lint（0 errors）、fmt:check 通过。局限：125% 为 device-metrics 模拟，非真实菜单缩放；外观由用户判断。worker 的 blocking 上报 `20261010T054058Z-worker:T-065-issue-001` 已作答并转交用户关闭。
