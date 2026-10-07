---
id: T-032
title: 修订后的 M1 与层级要求
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes: T-016
---

## Question

基于 Synara 的 M1 做到什么算完成？

## Resolution

2026-10-07 grilling 确认（[ledger](../../.grilling/synara-fork.md) 的 D6、D7、D10）。层级原话："反正就是要项目 任务 agent 这样的层级展开，一个项目里可以有多个任务窗口，一个任务窗口里可以有多个agent"。

M1 六项（详见 [intent.md](../../intent.md)）：fork 能跑起来（含缓存测量与上游合并演练）；项目 → 任务 → agent 会话层级（缺则在 fork 中补模块，"任务窗口"指应用内区域）；原生门禁与移植场景；一次真实闭环；界面显示门禁状态；切换后删除 Muster 与 `coop.py` 运行路径。

不在 M1：Enchanted 功能（门禁接入后再并入，方式待重叠调研）、Windows/Linux、每个项目一个系统窗口。T-025、T-028 以 out-of-scope 关闭，spec `workbench-m1-2026-10-06.md` 成为被取代方案的日期记录。取代 T-016。
