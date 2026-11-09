---
id: T-272
title: 记录页任务筛选显示任务简介
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## 来由

用户 2026-11-09 截图后提出（逐字）：“第三:这里面的 最好也显示一下任务简介”（截图为记录页的任务下拉框，只有任务编号）。

## 要做的

门禁的 `tasks_list` 多返回任务卡的目标 `goal`；记录页任务筛选的每一项写成“编号　目标第一句”（超长截断）；任务条按钮的悬停提示也带上目标。读不到时只显示编号，筛选照常可用。

## Acceptance

- [ ] 筛选项文字含编号与目标第一句；没有目标的任务只显示编号。
- [ ] 筛选结果与改动前一致。
