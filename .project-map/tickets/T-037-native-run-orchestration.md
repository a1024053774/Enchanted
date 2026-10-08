---
id: T-037
title: 原生 run 编排与人工介入记录
type: build
status: open
blocked_by: [T-036]
claimed_by:
supersedes:
---

## What to build

把 [自动运行](../specs/supervised-run-2026-10-06.md) 的 run 编排移到门禁核心：dispatch 经 Synara 内部服务创建 worker thread（worktree 环境、baseRef 为集成头、明确模型与参数），只有当前 attempt 经 `a2a_submit` 交付才推进，verify/integrate 绑定原 attempt，回收停止并归档本 run 创建的 thread。运行时身份核对 thread、turn 与 worktree。受管 worker thread 中由人直接输入的消息记为人工介入事件。设计见 [spec](../specs/synara-m1-2026-10-07.md) 的"门禁""验证接缝"第 1 项。

## Acceptance

- [ ] `acceptance/test_run_e2e.py` 的 18 项按新运行时改写边界替身后通过，替身明确标为隔离编排证据；先在缺失实现时取得红态。
- [ ] 反例："thread 空闲或 done 而无 submit 即接受"、"忽略 expected attempt"两种错误实现在业务断言上失败。
- [ ] 交付 8 项、恢复 9 项在新候选上仍通过。
- [ ] 在受管 worker thread 中由人直接输入，产生绑定 task/attempt/thread 的人工介入事件；非受管 thread 的输入不产生。
- [ ] 改写替身与原 18 项的差异逐条记录，不改原预期答案。

## Resolution
