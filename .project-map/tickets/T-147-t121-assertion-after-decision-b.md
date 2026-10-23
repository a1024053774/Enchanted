---
id: T-147
title: T-121 受保护断言随裁定 B 更新：关闭的主控留在侧栏并标已结束
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

缺陷级（执行主控自建，T-004 范围内）。T-146-3 按用户裁定 B（20261023T125315Z ideation answer 问题 3）保留已结束的主控条目，与受保护的 `workbench/tests/test_t121_role_request_e2e.py:515` `sidebar_drops_closed_controller`（关闭终端后侧栏 agents 里没有该主控）冲突：main fd4d9ac13 上 T-121 失败，T-146-3 前 045e8cfb1 通过（`evidence/2026-10-23-batch23/merge-1/run-20261023T151510Z/NOTE.md`）。

用户 2026-10-23 在执行主控会话选择题逐字选“保留并标已结束 (Recommended)”（inbox 20261023T153252Z-executor-report-001）：改该断言为关闭后该主控仍在侧栏、状态已结束、身份已释放；其余断言不动，产品代码不改。

## Acceptance

- [ ] main 上 T-121 全绿；该断言在关闭后检查条目存在、state 为 ended，且身份已被拒（原 closed_terminal_identity_refused 保留）。
- [ ] 反例：侧栏把关闭的主控删掉（T-146-3 前的行为）或仍标运行中，新断言都失败。
- [ ] 其余 T-121 检查名、断言、超时不变。

## 不做

不改 sidebar.ts 或其他产品代码；不改其他验收文件。

## Resolution
