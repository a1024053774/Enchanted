---
id: T-065
title: 窗口不高又开着问题面板时，会话空态的输入框要在首屏可见
type: build
status: open
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

- [ ] 红态在先：在 `e94a0efc3` 上，1280×900、开着问题面板（至少 3 条待决定问题）时，输入框不在首屏内，用例失败；保存输出与重放命令。
- [ ] 修复后，1600×1050、1280×900、以及 1280×720 三种视口，开或不开问题面板，输入框都完整在首屏内、可直接点击输入，不需要滚动。
- [ ] T-063 的反例照常通过：横幅、logo、标题、输入区两两相交面积为 0；加长中文文案也不重叠；窗口尺寸来回改变后仍成立。不能靠把文字藏掉来通过：被收起的内容要么完整可见，要么明确是按设计收起（在 RESULTS 写清哪种视口收起什么）。
- [ ] 截图作证，外观由用户判断。
- [ ] 既有套件、typecheck、lint 通过；对上游文件的改动列清单（预计仅 `ChatView.tsx` 的空态块）。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：面板宽度改变挤压会话列；问题条目很多时面板自身滚动；中文与英文文案长度不同；浏览器缩放 125%。
- 测试数据与 profile 放在哪个盘按现有约定；不需要做启动耗时对照（用户 2026-10-09："没必要测"）。
- 与 T-057 同改任务窗口时，同一文件同一时间只能有一个写入者，由执行主控串行安排。
- 授权来源：用户 2026-10-09 对"输入框要滚动才看到能否接受"答"不能"；`ready_by: ideation`，`ready_rev: 1`。

## Resolution

INCOMPLETE（机械验收与套件通过，等待一次独立审查），待主控关闭。依据 ready_rev 1 与 [执行主控决定 01](../../evidence/2026-10-09-batch11/T-065/controller-decision-01.md)，fork 候选 `9654e1c63d87f41d033a3d6093c24d2a401b347a`。上游仅改 ChatView.tsx 空态块；经批准另改 a2a IssuePanel.tsx、TaskWindow.tsx，为会话保留高度，问题列表自身滚动。红态在先；三种窗口在打开/无面板时、三种 125% device-metrics 模拟、长中文、尺寸往返、400px 窄列、15 条待决定问题与按钮完整显露/点击检查通过。相关套件及全 workspace typecheck、lint、fmt:check 通过；真实菜单缩放未证明，外观由用户判断。详见 [RESULTS](../../evidence/2026-10-09-batch11/T-065/RESULTS.md)、[重放](../../evidence/2026-10-09-batch11/T-065/REPLAY.md) 与 candidate-binding.json。
