---
id: T-147
title: T-121 受保护断言随裁定 B 更新：关闭的主控留在侧栏并标已结束
type: build
status: closed
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

- [x] main 上 T-121 全绿；该断言在关闭后检查条目存在、state 为 ended，且身份已被拒（原 closed_terminal_identity_refused 保留）。
- [x] 反例：侧栏把关闭的主控删掉（T-146-3 前的行为）或仍标运行中，新断言都失败。
- [x] 其余 T-121 检查名、断言、超时不变。

## 不做

不改 sidebar.ts 或其他产品代码；不改其他验收文件。

## Resolution

2026-10-23 关闭，PASS。

- 改动：`aa1a83aa0`，只改 `workbench/tests/test_t121_role_request_e2e.py:515`：关闭终端后侧栏里该主控的状态列表必须正好是 `['ended']`；`closed_terminal_identity_refused` 等其余检查与超时未动，产品代码未改。合并 `84860f257`。
- 验收（执行主控沙箱外，`evidence/2026-10-23-batch23/T-147/outside-20261023T153955Z-dr9uZR`）：候选上 T-121 全绿；`--revision 045e8cfb1`（关闭主控从侧栏消失的旧行为）在新断言失败。
- 独立审查：agy gemini-3.8-flash-high，PASS。P2：worktree 起点是 2e36efb7c 而不是含 ticket 的 fda7d194d（执行主控先取起点再提交 ticket），用 git merge 合入不受影响；P2：RUN-OUTSIDE-01.sh 写死 worktree 路径；P3：检查名沿用旧字面，按卡不改。
- 起因记录：合并回归 01–04 没有收 T-121，T-146-3 合入时没拦住，是执行主控的疏漏；之后的回归脚本加入 T-121。

