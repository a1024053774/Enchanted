---
id: T-091
title: 工作台单窗口同任务多窗格：两个主控窗格加一个 worker 窗格同屏
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

[spec](../specs/native-cli-orchestration-2026-10-10.md) 写的是"界面按项目 → 任务 → 会话展开，一个任务里有多个会话窗格"。现状（执行主控 2026-10-16 只读核对，`workbench/app/renderer.tsx:54`、`:161` 只建一个 Terminal，`workbench/app/main.ts:29` 每次只开一个 BrowserWindow）是一个窗口一个终端窗格，产品里没有同窗口多窗格。

本票做同一个 Electron 窗口里、同一任务下的多个会话窗格，至少能同时显示两个主控窗格和一个受管 worker 窗格。每个窗格独立的窗口身份、输入序号和输出流，复用现有输出与输入通路和唯一门禁，不另造业务接口；全局 IPC handler 随之调整。

## 来源与取舍

T-078 原验收有一条"Electron 截图或录屏：两个主控窗格、一个 worker 窗格同时在一个任务下"。用户 2026-10-16（逐字，会话"a2a-构思主控"，AskUserQuestion）选"拆出去：T-078 其余先收，截图项另开 UI 票 (Recommended)"，选项原文："承认单窗多窗格是产品工作，另开一张 UI 票做（spec 里本来就写“一个任务里有多个会话窗格”）。T-078 把这一项从验收里移出并在 Resolution 写明，其余项独立审查通过就可以关。这是你对验收条件的修订，要你本人确认。"

## Acceptance

- [ ] 红态：当前 `main` 上同一任务不能在一个窗口里同时显示三个窗格（读回现状）。
- [ ] 绿态：一个窗口里同一任务的两个主控窗格加一个 worker 窗格同时可辨，各自绑定正确的 task、角色与 launch；三份真实 `workbench_snapshot` 与进程身份核对，不靠标题。
- [ ] 反例：给第三个窗格绑错 task 或旧 launch，检查拒绝；不得用三张图拼接或顺次切换冒称同时显示。
- [ ] 截图或录屏用原始单帧（可附不剪辑的短视频），范围只含这个隔离窗口；Computer Use 仅限 worker 自己启动的隔离 Electron，缺屏幕录制或辅助功能权限由用户在系统设置里给。
- [ ] T-074/T-075 的正反例不退化；T-078 已有的主控窗格与输入行为不退化。
- [ ] 独立审查通过；`project_map.py status` 0 problems。

## 说明

- 构思主控建票，未标 ready；开工前先过一遍界面方向（可用 `frontend-production` 与 `same-visual-family` 两个 skill 的约束）。与 T-078 不再互相等待。
- 不改门禁、不改紧急停止或收件箱语义。

## 就绪

用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："那现在都idle了，让他继续啊，漏掉的也开工"，构思主控据此标就绪（`ready_rev: 1`）。
