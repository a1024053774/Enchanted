---
id: T-038
title: 任务窗口与门禁状态界面
type: build
status: open
blocked_by: [T-036]
claimed_by:
supersedes:
---

## What to build

在 Synara 桌面版中按"项目 → 任务 → agent 会话"展开：一个项目下有多个任务，每个任务窗口并排显示属于它的多个 thread，并显示门禁状态（claimed、submitted、verified、accepted 及失败原因）与人工介入标记。先核实 Synara 是否已有 thread 分组；没有就由 a2a 保存任务与 thread 的归属，不改上游 thread 结构。界面对受管任务的操作只调用门禁核心。视觉沿用 Synara 主题与组件。设计见 [spec](../specs/synara-m1-2026-10-07.md) 的"层级模型""界面"。

## Acceptance

- [ ] 隔离数据目录中的桌面版截图或录屏：一个项目下至少两个任务，其中一个任务含至少两个 agent 会话（例如 worker 与 reviewer），并显示门禁状态。
- [ ] 门禁状态取自门禁核心的真实状态：经门禁 CLI 推进一个夹具任务时，界面状态随之变化（含一次失败原因）；有截图与对应 CLI 输出。
- [ ] 任务与 thread 的归属在重启后保持；上游 thread 表结构未改。
- [ ] 上游文件改动清单；`typecheck`、`lint` 通过。
- [ ] 外观由用户判断，不在本 ticket 内宣称通过。

## Resolution
