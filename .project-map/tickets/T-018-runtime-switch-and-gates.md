---
id: T-018
title: 运行时切换与门禁优先
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## Question

工作台与已安装的 Herdr、a2a 门禁是什么关系？

## Resolution

2026-10-06 grilling 确认（[ledger](../../.grilling/a2a-gui-client.md) 的 D7、D16、C12）。

- 工作台取代 Herdr，成为 a2a 的运行时。`coop.py` 保留全部门禁，只替换它使用的 9 个 Herdr 命令。
- 切换条件：工作台运行时上，交付、恢复、编排三套验收和一次真实 `run` 全部通过；之后删除 Herdr 路径。
- 门禁优先：受管任务的验收、集成和回收，只调用 `coop.py` 的同一入口；在受管 worker 的 pane 里直接输入，记为人工介入。
- 工作台使用独立命名空间，切换完成前与已安装的 Herdr 并存。

本决定取代首轮 intent 中"保留 Herdr"的表述。T-006～T-008 的证据只对 Herdr 运行时成立，切换后要重跑。
