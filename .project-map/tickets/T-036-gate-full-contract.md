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
- [ ] 恢复 9 项经门禁 CLI 通过，真实中断注入只作用于测试创建的进程。
- [ ] 反例：去掉 fence 校验、或忽略 Git 回读的错误实现，会被上述验收抓住。
- [x] CLI 契约的差异（若有）逐条记录理由，不为通过而改写验收的预期答案。

## Resolution

**INCOMPLETE，待主控关闭。** fork 冻结候选 `5cae1072db94ccd1af20ef161481163484aecfe5`；交付 8/8 PASS，去掉 fence 的 mutant 被错 fence 的业务断言抓住。恢复套件 2/9 PASS、7 项在 SIGKILL 前因 execv 后的进程命令行变化被原夹具拒绝；忽略 Git 回读的 mutant 同样受夹具阻断，不能称为业务反例通过。没有改原 acceptance 或预期答案。主控需决定是否批准证据副本中的原生入口身份核对参数化；提议尚未执行。

命令、完整日志、差异、冻结版本与缺失证据见 [T-036 交付记录](../../evidence/2026-10-07-synara-batch1/T-036/RESULTS.md)。独立冻结审查与最终全仓检查在本次交接前补记，ticket 始终保持 open。
