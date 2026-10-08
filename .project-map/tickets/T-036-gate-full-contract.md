---
id: T-036
title: 门禁完整契约与交付、恢复验收
type: build
status: open
blocked_by: [T-035]
claimed_by: Codex T-036 worker
supersedes:
---

## What to build

把门禁补全到与三份冻结规格一致：attempt/session/fence/spec_rev 身份、submit 全部校验、操作锁与竞争返回、revoke/revise、中断验收与 CAS 前后的恢复、`needs_reconciliation`。门禁 CLI 对与运行时无关的命令保持 `coop.py` 的命令与 JSON 契约，使现有交付与恢复脚本只替换入口即可重跑。设计见 [spec](../specs/synara-m1-2026-10-07.md) 的"门禁"与"验证接缝"。

## Acceptance

- [x] 交付 8 项经门禁 CLI 通过，先在缺失实现时取得红态。
- [x] 恢复 9 项经门禁 CLI 通过，真实中断注入只作用于测试创建的进程。
- [x] 反例：去掉 fence 校验、或忽略 Git 回读的错误实现，会被上述验收抓住。
- [x] CLI 契约的差异（若有）逐条记录理由，不为通过而改写验收的预期答案。

## Resolution

**INCOMPLETE，仅余针对性独立复核与收尾；待主控关闭。** fork 修正候选 `26cb210a99fc74a43ef341278c6ef4e19ab0565e` 经主控批准的同一副本入口取得交付 8/8、恢复 9/9 PASS；fence 与忽略 Git 回读的同版本 mutant 均被业务断言抓住。副本完整 diff 只有两行入口身份核对，原 acceptance 与业务预期未改；最初原脚本的拒绝注入、实现前的红态与副本对缺失实现的反事实红态均保留。

首次独立审查对 `5cae1072d` 为 FAIL，发现历史 attempt 的首次回收错误拒绝；该缺陷已先取得明确红态，再修复并转绿（真实 Git/SQLite、thread 边界替身，只证明作用域逻辑）。修正候选重新取得所有上述门禁证据，不借旧结论背书。

命令、完整日志、差异、冻结版本与缺失证据见 [T-036 交付记录](../../evidence/2026-10-07-synara-batch1/T-036/RESULTS.md)。修复范围的针对性只读复核在交接前补记，ticket 始终保持 open。
