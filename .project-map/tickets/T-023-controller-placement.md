---
id: T-023
title: 主控放在项目级还是任务级
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## Question

工作台里的主控 agent 放在项目级（一个项目一个主控，跨任务派 worker），还是任务级（每个任务页一个主控）？

这决定主控 pane 放在哪里、它能看到和派发的范围，以及 M1 中"主控在任务页中真实跑一次 `run`"如何落地。

## Resolution

2026-10-06，用户决定主控不区分项目级和任务级，参照 Herdr 的做法（"主控其实不太分，既可以操作项目级，也可以操作每个任务级"）。

主控是一个角色，不绑定层级：它可以在任意 pane 中运行，经控制接口按 ID 操作项目级对象（项目窗口、任务页）和任务级对象（pane、agent）。这与 Herdr 中 agent 用 CLI 或 socket 操作 workspace、tab、pane 的方式一致。门禁和停止边界仍按 AGENTS.md 执行。
