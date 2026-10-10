---
id: T-031
title: a2a 门禁在 Synara 中原生实现
type: decide
status: superseded
blocked_by: []
claimed_by:
supersedes: T-018
---

## Question

a2a 门禁今后在哪里实现，旧实现怎么处理？

## Resolution

2026-10-07 grilling 确认（[ledger](../../.grilling/synara-fork.md) 的 D5、D9）。用户原话："我建议选B，你觉得呢？这是为长远考虑，最好原生。"

- 门禁在 Synara 服务端用 TypeScript 原生重写，做成独立 package，提供外部可调用的唯一门禁入口。
- 契约不变：照搬受管交付、恢复、自动运行三份冻结规格的锁、fence、CAS、attempt 绑定与中断恢复语义。
- 重新证明：交付 8、恢复 9、编排 18 项场景移植后经门禁入口重新取得红态、绿态与反例；旧通过结论不背书。
- `coop.py` 与 Muster 引擎冻结为参考实现；新门禁通过同样验收后删除 Muster，不保留两套路径。新门禁就绪前由 `coop.py` 的 CLI 担任门禁入口。

取代 T-018（工作台取代 Herdr，`coop.py` 改接 Muster）。被否决：保留 `coop.py` 为唯一门禁实现、只把运行时改接 Synara。

2026-10-10 由 [T-070](T-070-gates-task-cards-quality.md) 取代：门禁从 fork 抽进工作台的编排后台。
