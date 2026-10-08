---
id: T-036
title: 门禁完整契约与交付、恢复验收
type: build
status: closed
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

**PASS，仅限本 ticket 四项及输入、作用域逻辑；待主控关闭。** 最终候选 `a9cc30c395af9ffd51476a1841d80bca66568993` 经主控批准的同一副本入口重新取得交付 8/8、恢复 9/9 PASS；fence 与忽略 Git 回读的同版本 mutant 均被业务断言抓住。副本完整 diff 只有两行入口身份核对，原 acceptance 与业务预期未改；最初原脚本的拒绝注入、实现前的红态与副本对缺失实现的反事实红态均保留。最终独立行为核对与明确清单的冻结复核为 [PASS](../../evidence/2026-10-07-synara-batch1/T-036/acceptance-review-a9-pass.md)；过宽冻结声明触发的 INCOMPLETE 原样保留，没有覆盖。

首次独立审查对 `5cae1072d` 为 FAIL，发现历史 attempt 的首次回收错误拒绝；该缺陷已先取得明确红态，再修复并转绿（真实 Git/SQLite、thread 边界替身，只证明作用域逻辑）。修正候选重新取得所有上述门禁证据，不借旧结论背书。

收尾又发现空 expected attempt 被视为省略、空 thread 查询匹配未绑定本地 attempt 的边界缺陷。`26cb210a9` 上保留红态，最终候选做三行输入/查询保护并转绿；旧候选的审查与全仓通过不替最终版本背书。最终候选的类型、lint、聚焦测试与 17 项通过；最后一次全仓 PASS 绑定 `26cb210a9`，最终三行修复后没有再次运行约 33 分钟的全仓套件。

命令、完整日志、差异、冻结版本与验收边界见 [T-036 交付记录](../../evidence/2026-10-07-synara-batch1/T-036/RESULTS.md)。真实原生会话回收、run 编排和 M1 切换不在本次通过结论内。

**主控关闭（2026-10-07，Claude Code）：PASS。** 已核对：副本 diff 与 `controller-decision-01.md` 的条件一致（仍同时核对 PID、门禁 CLI 入口、state 与 task；业务断言、预期与场景数不变）；原 `acceptance/test_coop_e2e.py`、`test_recovery_e2e.py` 未改，只新增 `acceptance/entry/a2a_gates.py` 转接；原文件在转接入口下的拒绝注入记录保留。遗留：最终候选 `a9cc30c` 未重跑全仓测试（最后全仓 PASS 绑定 `26cb210a9`，其后只有三行输入保护），fmt 仍只因范围外 `.grok/` 失败；fork `a2a` 分支未 push。
