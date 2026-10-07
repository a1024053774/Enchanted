---
id: T-036
title: 门禁完整契约与交付、恢复验收
type: build
status: open
blocked_by: [T-035]
claimed_by:
supersedes:
---

## What to build

把门禁补全到与三份冻结规格一致：attempt/session/fence/spec_rev 身份、submit 全部校验、操作锁与竞争返回、revoke/revise、中断验收与 CAS 前后的恢复、`needs_reconciliation`。门禁 CLI 对与运行时无关的命令保持 `coop.py` 的命令与 JSON 契约，使现有交付与恢复脚本只替换入口即可重跑。设计见 [spec](../specs/synara-m1-2026-10-07.md) 的"门禁"与"验证接缝"。

## Acceptance

- [ ] 交付 8 项经门禁 CLI 通过，先在缺失实现时取得红态。
- [ ] 恢复 9 项经门禁 CLI 通过，真实中断注入只作用于测试创建的进程。
- [ ] 反例：去掉 fence 校验、或忽略 Git 回读的错误实现，会被上述验收抓住。
- [ ] CLI 契约的差异（若有）逐条记录理由，不为通过而改写验收的预期答案。

## Resolution

未执行。
