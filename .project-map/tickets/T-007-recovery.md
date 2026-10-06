---
id: T-007
title: 服务中断后的候选与集成核对
type: build
status: closed
blocked_by: [T-006]
claimed_by:
supersedes:
---

## What to build

按 [恢复契约](../specs/recovery-2026-10-06.md) 验证真实 CLI 进程在验收、CAS 前后中断的恢复。
recovery-build 独占 coop.py / README.md；recovery-check 独占 acceptance/test_recovery_e2e.py；
主控维护规范、复核证据及集成，monitor 只读采样。测试和产品均不覆盖旧产物。

## Acceptance

- [x] 真实进程中断保留输入、候选和失败证据；恢复不会误判成功。
- [x] Git 已更新但记账中断可核对补记；引用为未知值时暂停且不覆盖。
- [x] 重放旧执行者不能提交/重复集成；保存独立端到端产物和原始命令。
- [x] 存活操作不可被重复 verify/integrate 接管；中断后按当前身份重新验收或继续同一意图。
- [x] 父版本红态与代表性坏实现反事实有效；既有 T-006 验收未回归，固定候选独立审查完成。

## Resolution

PASS，2026-10-06；候选 95cc3a25cf31f56dde85728c5798888d1e311de8。
`python3 -B acceptance/test_recovery_e2e.py` 9/9；既有 `test_coop_e2e.py` 8/8。
父版4业务红、mutant3业务红及独立审查见 [完整记录](../../evidence/2026-10-06-recovery-01/RESULTS.md)。
