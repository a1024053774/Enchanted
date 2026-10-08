---
id: T-039
title: 真实 Codex 闭环
type: build
status: open
blocked_by: [T-037]
claimed_by:
supersedes:
---

## What to build

真实 Codex（经 app-server）在 Synara thread 中完成分页夹具：门禁派发 → worker 提交并调用 `a2a_submit` → 独立 oracle → CAS 集成 → 回收。使用隔离 Synara 数据目录与隔离 CODEX_HOME（AGENTS.md 规则）。见 [spec](../specs/synara-m1-2026-10-07.md)"验证接缝"第 2 项。

## Acceptance

- [ ] 一次真实 run 经完整入口 accepted，集成引用读回为 worker 提交；追加式运行记录含精确 argv、版本、task/attempt/thread、原始外部结果。
- [ ] 隔离 home 在结束后删除；用户 Herdr、Codex 配置与 Synara 数据不变。
- [ ] 无人值守期间若出现权限对话，停下保存现场，不作为通过。

## Resolution
