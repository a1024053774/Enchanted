---
id: T-086
title: 缺陷：T-084 后测试夹具仍写非启动记录的尾注（T-077 lifecycle 冲突两案失败）
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

T-084（main `c8d4e5d6`）起，受管 attempt 的提交尾注 Launch/Tool/Model/Effort 必须与启动记录一致（仅 Model 可写字面量 unknown）。`workbench/tests/test_worktree_lifecycle_e2e.py` 的 `commit_worker`（约 626–640 行）仍写 `Model: fixture`、`Launch: <thread_id>`、`Tool: Codex 0.162.1`，导致 T-077 生命周期冲突套件 `CONFLICT-ACTIVE-WRITEBACK`、`CONFLICT-ENDED-NEW-ATTEMPT` 两案 verify 返回 `trailer_identity_mismatch`（T-081 回归 `evidence/2026-10-14-batch14/T-081/6e-regress-rest-02/t077-lifecycle-conflicts/run.json`）。T-084 回归只覆盖该文件 3 个用例，漏掉了冲突用例。

修法：测试夹具的尾注取自该 attempt 的启动记录（门禁 `attempt.delivery` 或受控宿主 `worker-creations.jsonl` 的同一记录），不改门禁规则，不放宽比对。清点 `workbench/tests/`、`acceptance/` 中所有写 A2A 尾注的测试，逐个确认在新规则下仍按原意通过或被拒。

## Acceptance

- [x] 红态：在当前 `main` 上经真实入口复现两案 `trailer_identity_mismatch`（可引用 T-081 回归原件并重跑一次）。
- [x] 修复后 T-077 lifecycle 冲突套件全过；所有写尾注的测试文件清单与各自回归结果列出，失败 0（既有、与本票无关的失败须在基线上证明并单列）。
- [x] 期望值来自启动记录本身，不读门禁通过输出；不调用真实模型；`project_map.py status` 0 problems。

## 说明

- 来源：T-081 6e 回归发现（Grok 会话 wF:p30）。属 T-084 遗留的测试回归，执行主控按 T-004 边界自建（`ready_by: executor`）。
- 写入范围：`workbench/tests/`、`acceptance/` 中写尾注的测试夹具与本票证据；不改 `workbench/src/`。与 T-081 错开：T-081 不改这些文件，待本票合入后变基重跑。

## Resolution

**2026-10-15：执行主控验收 PASS，关闭。** 合入 main `e38b87cb1`（变基后实现 `8bce61b87`、`1185402cd`；审查 02 冻结候选 `c9e431aa`，变基前后 workbench/acceptance/scripts diff 为 0）。受控冲突宿主为每个 attempt 写与任务卡、thread_id、固定常量都不同的启动记录，`runtime_identity.launch` 取记录 id；`commit_worker` 按 attempt 读 `worker-creations.jsonl` 写尾注。证据 `evidence/2026-10-15-batch15/T-086/`：基线两案 `trailer_identity_mismatch`（rework-red-01），候选两案与冲突七案 PASS；变异 M1–M4 在 verify 失败（作者 rework-m1..m4 与审查 02 各自副本），M5 两案走不到 delivery 分支（未造路径）；tracer 13 案、widen wide 单跑 15 案、review-red 3 案 PASS。独立审查 01 NO_GO（完成条件不够格、清单漏 tracer/widen、run_worker_delivery 期望）→ 返工 → 审查 02 PASS。
- `run_worker_delivery.py` 按用户决定"只改脚本期望"（answer `20261015T131159Z-ideation-answer-001`）改为取当前回合 turn_context 的 model/effort 并等于 delivery；该脚本复制 auth、调真实模型，**未运行**，不算通过。`run_t076_real.py`、`run_t076_quality_real.py`、`run_pane_lifecycle.py`、`run_t076_red.py` 同样只做静态核对。
- 既有、与本票无关：widen wide 与 tracer 并发时 `widen_score_after_cas` 5 秒等待超时，基线并发同样复现、单跑通过；`test_task_cards_e2e.py` 直接入口不启动 daemon 的 49 个失败为基线既有。
- worker 为用户指定的 Grok 会话 wF:p3Z（无 A2A 启动记录，提交由执行主控代做、无 worker 尾注；打分因无启动记录不适用）。证据 120 MB，无单文件 >5 MB。
