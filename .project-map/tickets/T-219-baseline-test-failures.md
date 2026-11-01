---
id: T-219
title: 既有测试在基线上失败：终端状态、紧急中断、旧恢复与 Electron 夹具、跨项目开终端
type: research
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## Question

T-216 的 worker 跑回归时发现下面几项失败。它在改动前的基线 `cac1880f0` 上用 `--revision` 或源码快照重跑，结果同样失败，所以失败与 T-216 无关。逐项查明：是测试过时（比如它覆盖的做法已于 2026-10-27 随 Herdr 停用），还是产品回归。

1. `workbench/tests/test_t133_t107_terminal_controller_e2e.py` 里的 T-176 检查 `home_terminal_header_known` 失败。证据：`a2a-worktrees/T-216-evidence/regression-t133-baseline-01.json`。
2. `workbench/tests/test_t078_inbox_domain.ts` 的 `executor_honors_stop_immediately`、`late_stop_actor_comes_from_caller` 两项为 INCOMPLETE。证据：`a2a-worktrees/T-216-evidence/regression-domain-baseline-02.log`。
3. `workbench/tests/test_t078_pane_runtime.ts` 的 `interrupt_only_esc_not_reclaim` 断言失败。证据：`a2a-worktrees/T-216-evidence/regression-pane-baseline-01.log`。
4. `workbench/tests/test_t078_a13_rehearsal.ts` 的第一条 UPS 被 `question_origin_unverified` 拒绝，还没在基线上重跑，所以原因未知。

T-212 跑回归时，又在父版本 `4cb88bba7` 上复现了以下失败（worker 用 `git archive` 副本复跑，主控用 `--revision` 复跑）：

5. `test_t184_unwired_cli_e2e.py` 的 `shim_claude_state_known` 读到 unknown。证据：`a2a-worktrees/T-212-evidence/parent-t184-01.json`。
6. `test_t195_native_link_e2e.py` 的 `managed_codex_unsearchable_day_grey` 失败。证据：`a2a-worktrees/T-212-evidence/parent-t195-01.json`。
7. `test_daemon_recovery_e2e.py` 的 5 个测试都在 `card_save` 阶段报 `unknown_task`。证据：`a2a-worktrees/T-212-evidence/parent-recovery-01.json`。
8. `test_electron_e2e.py` 在窗口测试前的 `card_save` 夹具准备阶段报 `unknown_task`。证据：`a2a-worktrees/T-212-evidence/parent-electron-01.json`。
9. `test_t142_terminal_open_e2e.py` 的 `approved_foreign_project_refused`：demo 项目的主控在另一个已打开项目里开终端，没有被拒。证据：`a2a-worktrees/T-212-controller/t142-parent-02.json`。T-189/T-193 决定主控可以跨已打开项目工作，这条断言可能已经过时，要先核对。

第 7、8 项在 [hc 运行时规格](../specs/hc-runtime-2026-10-31.md)里列为后续切片的真实入口，必须在受管窗格切片之前修好。

T-216 关闭时，这些证据会随它归档进 `evidence/2026-10-31-batch29/T-216/`；T-212 的证据随 T-212 归档进 `evidence/2026-10-31-batch29/T-212/`。第 1 项的终端状态，在 hc 运行时的“状态统一取 hc 事件”切片里可能有不同的结论，先查明原因再决定放到哪里处理。

## Resolution

2026-10-31 关闭。九项都在给定基线上复现到票面失败点，逐项查明：八项是测试过时，按现行契约修订；第 6 项是产品缺陷。

- 测试过时、已修订（各附修前红态、绿态和变异反例）：
  - 第 1 项：T-191，没有前台 CLI 的普通终端显示空闲；
  - 第 2、3 项：T-124，provider 取自 attempt 的任务卡快照；T-187，按启动记录的 `cli` 判定；
  - 第 4 项：T-108，hook 必须带 `cwd`、`transcript_path`；
  - 第 5 项：T-191，Claude/Codex 在角色获批前为未知；
  - 第 7 项：T-123 任务 id 带项目、T-141 原生 idle、T-203 `review_submit`、T-096 活所有者拒绝重启，五场全过；
  - 第 8 项：T-123；
  - 第 9 项：T-189/T-193，主控可在任一已打开项目开终端。
- 第 6 项交 [T-221](T-221-dst-day-scan.md)：夏令时回拨当天，按天扫描 Codex 记录的循环漏掉次日。
- 第 7、8 项现已能当后续受管窗格切片的真实入口；换到 hc 后要重新取得红绿态，不复用本票结果。
- 第二轮对照：共享夹具的 23 个非历史调用者在基线和候选上各跑一次，没有“基线过、候选不过”的。另有 17 个旧套件两边都失败，与本票无关，登记为 [T-222](T-222-legacy-gate-suites-broken.md)。
- `workbench/tests/HISTORICAL.md`：`controlled_quality_pty.ts` 移入“已迁移到现行契约”，写明各直接导入方的实际复验范围。
- 边界偏差：worker 初轮漏设 `TMPDIR`，UI 构建在系统临时目录留下 4 个构建槽。主控删除了这 4 个槽，并接受该轮证据。

提交：worktree `5d1d9b6fc`，main `4fa0d4ca4`。主控独立重跑 10 个入口，结果全部符合预期。证据在 [evidence/2026-10-31-batch29/T-219/](../../evidence/2026-10-31-batch29/T-219/RESULTS.md)，整份目录与 110 个现场已归档到外置盘，清单在同目录的 `archive/` 下。
