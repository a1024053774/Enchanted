---
id: T-010
title: Account for descendant agent sessions and model settings
type: task
status: closed
blocked_by: [T-009]
claimed_by:
supersedes:
---

## Question

如何让开发运行的人员与模型清单覆盖 worker 内部创建的子 agent，而不只覆盖 Herdr pane？
本次复盘发现三次内部分派，两份子审查记录为 gpt-5.6-luna / max，原清单未完整覆盖。
证据：[F04](../../findings/a2a-session-retrospective-2026-10-06.zh-CN.md)、
[E12–E14 与子配置](../../evidence/2026-10-06-session-review-01/excerpts.json)。

交付边界是记录与配置检查，不扩展到多机调度或第二 CLI。先核对可用 session 关联入口，
再定义每个父子关系所需的 task/attempt、角色、请求配置、来源和结束状态。
检查应能发现“未登记子 session”与“未经说明的模型例外”；旧运行是已知缺口输入。
不得从父 pane 的 Fast UI 推导子 session 的实际 tier，也不得把 pane 回收等同于所有子任务结束。
审查角色默认模型与用户模型要求的适用关系必须明确，不能默默选择例外。

本票记录待办，不启动新 agent，不预先改变权限或模型选择。

## Resolution

2026-10-22 关闭，不执行。用户逐字：“早期的调研票关掉”。本票针对 Herdr 期第一轮运行的复盘发现；第三阶段的工作台已用启动记录、门禁检查串与原始事件覆盖相应方向，不再单独研究。
