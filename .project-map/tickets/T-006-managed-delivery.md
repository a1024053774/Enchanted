---
id: T-006
title: 受管理候选从 Herdr 分派到独立验收
type: build
status: closed
blocked_by: [T-005]
claimed_by:
supersedes:
---

## What to build

按 [冻结执行规格](../specs/managed-delivery-2026-10-06.md) 实现第一个 Tracer bullet。
controller 持有治理与集成职责；a2a-build 拥有 coop.py 与运行说明；
a2a-check 拥有 acceptance/test_coop_e2e.py；monitor 只读观察。
实现者和验收者共享契约，不共享实现答案；各自不覆盖他人的文件。

## Acceptance

- [x] 多子进程竞争只产生一个有效 attempt；程序生成身份并准备独立工作区。
- [x] 旧 attempt/session/fence/spec 和未验收交付被拒绝，集成引用不变。
- [x] 外部坏候选失败、合法候选通过；验收绑定冻结代码和 oracle，记录原始输出。
- [x] 验收后基线变化拒绝，合法结果以 CAS 恰好推进本地引用一次。
- [x] 真实 Herdr/Codex 任务经程序分派、提交、独立验收与集成，worker pane 正确回收。
- [x] 代表性门禁 mutant 被独立验收拒绝；只读行为审查没有未解决核心缺陷。
- [x] 保存 exact command、输入输出、退出码、运行产物与候选 commit；living docs 无 stale。

## Resolution

PASS，2026-10-06。实现 commit 5ab42ffe1c49770ed83f19a4a40e3fd8653ccbf1；
最终验收候选 033631dd84e020591e6879c48ebdfe6d11a4ce9e。完整命令、边界、原始产物
见 [RESULTS.md](../../evidence/2026-10-06-managed-01/RESULTS.md)。
`python3 -B acceptance/test_coop_e2e.py` 为 8/8；真实 Herdr/Codex live-02 交付和集成通过；
两项 gate mutant 与一项 oracle 上界反事实有效，初审 P2 在一次定向复核后关闭。
主控/实现/验收/monitor/reviewer 分工完成，本项目额外 pane 全部回收。
