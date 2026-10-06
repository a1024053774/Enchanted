---
id: T-006
title: 受管理候选从 Herdr 分派到独立验收
type: build
status: open
blocked_by: [T-005]
claimed_by: a2a-build
supersedes:
---

## What to build

按 [冻结执行规格](../specs/managed-delivery-2026-10-06.md) 实现第一个 Tracer bullet。
controller 持有治理与集成职责；a2a-build 拥有 coop.py 与运行说明；
a2a-check 拥有 acceptance/test_coop_e2e.py；monitor 只读观察。
实现者和验收者共享契约，不共享实现答案；各自不覆盖他人的文件。

## Acceptance

- [ ] 多子进程竞争只产生一个有效 attempt；程序生成身份并准备独立工作区。
- [ ] 旧 attempt/session/fence/spec 和未验收交付被拒绝，集成引用不变。
- [ ] 外部坏候选失败、合法候选通过；验收绑定冻结代码和 oracle，记录原始输出。
- [ ] 验收后基线变化拒绝，合法结果以 CAS 恰好推进本地引用一次。
- [ ] 真实 Herdr/Codex 任务经程序分派、提交、独立验收与集成，worker pane 正确回收。
- [ ] 代表性门禁 mutant 被独立验收拒绝；只读行为审查没有未解决核心缺陷。
- [ ] 保存 exact command、输入输出、退出码、运行产物与候选 commit；living docs 无 stale。

## Resolution

待执行。
