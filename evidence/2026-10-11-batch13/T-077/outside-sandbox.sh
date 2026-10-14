#!/bin/bash
set -euo pipefail

# 执行主控运行。只有 real-01 / real-02 启动真实 Codex，须逐次明确批准。
# 运行命令：
# bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh red-01
# 同名输出已存在时拒绝，不能覆盖原始失败。后续阶段另行批准/交回。
if [[ "$#" != 1 ]]; then
  echo 'usage: outside-sandbox.sh red-01|check-01|check-02|check-03|check-04|cards-03|conflict-red-01|conflict-green-01|rebase-01|rebase-fix-02|real-01|real-02|relay-check-01|relay-check-02|relay-regression-01|real-recheck-01|real-recheck-02|r3-plan-check-01|real-r3-launch-01|real-r3-launch-02|controlled-trailer-proofs-01|rebase-final-01' >&2
  exit 2
fi
cd /Users/luckye/Documents/Code/a2a-wt-t077
# 主控 #96 / answer 20261014T011612Z：不再允许新的真实模型回合。
case "$1" in
  real-01|real-02|real-recheck-01|real-recheck-02|real-r3-launch-01|real-r3-launch-02)
    echo 'NO_GO: T-077 real model runs are closed by answer 20261014T011612Z-ideation-answer-001' >&2
    exit 1
    ;;
esac
case "$1" in
red-01)
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase baseline \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-red-01
  ;;
check-01)
# 首批 12 项候选检查。R8 尚未实现，明确不把它算成绿态。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase candidate \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-green-01 \
  --case test_worker_name \
  --case test_clean_revoke \
  --case test_clean_revise \
  --case test_verification_name \
  --case test_completed_verification_cleanup \
  --case test_overlap_without_reason \
  --case test_dirty_revoke_keeps_scene_and_reports \
  --case test_unknown_cleanup_keeps_scene_and_reports \
  --case test_dirty_integration_reports_without_mutation \
  --case test_integrated_run_cleanup \
  --case test_timeout_cleanup_retains_unsubmitted_commit \
  --case test_rejected_run_cleanup
# 从已经确认的 red-01 源码归档重建起点；逐文件与 git show 起点比对，
# 不移动、切换或重置任何 checkout。baseline 只运行指定的手工 claim 场景。
t077_baseline_product=$(python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/prepare_s3_baseline.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/baseline-red-02.json)
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase baseline --baseline-product "$t077_baseline_product" \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-red-02 \
  --case test_r8_stops_at_fourth_cas_miss
  ;;
check-02)
# 核对 R8 一次竞争、第四次停止与计数重放；不把其他未实现范围算通过。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase candidate \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-green-02 \
  --case test_r8_revalidates_on_new_head \
  --case test_r8_stops_at_fourth_cas_miss
# 其余白名单项先在起点取得独立红态，再改原验收方法。
t077_baseline_product=$(python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/prepare_s3_baseline.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/baseline-red-03.json)
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase baseline --baseline-product "$t077_baseline_product" \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-red-03 \
  --case test_r8_stops_at_fourth_cas_miss \
  --case test_r8_missing_trailer_is_not_recorded_twice \
  --case test_superseded_run_retains_only_new_workspace \
  --case test_historical_cleanup_leaves_current_and_foreign_untouched \
  --case test_cas_write_race_revalidates
  ;;
check-03)
# 与 red-03 相同的四项补充信号，先取得候选绿态。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase candidate \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-green-03 \
  --case test_r8_missing_trailer_is_not_recorded_twice \
  --case test_superseded_run_retains_only_new_workspace \
  --case test_historical_cleanup_leaves_current_and_foreign_untouched \
  --case test_cas_write_race_revalidates
# 完整原方法：8/9/18、实际 CAS 竞争补充、T-075 任务卡正反例。
# 任一阶段失败即停；不能把未运行的后续阶段列为通过。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite coop --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-01-coop
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite recovery --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-01-recovery
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite run --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-01-run
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite cas --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-01-cas
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite cards --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-01-cards
  ;;
check-04)
# check-03 的第二个 wrapper 被 release-all 按清理语义 abort，产品正确拒收。
# 修正夹具后先重建同一 W11 起点红态，再验证候选；不改产品或业务断言。
t077_baseline_product=$(python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/prepare_s3_baseline.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/baseline-red-04.json)
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase baseline --baseline-product "$t077_baseline_product" \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-red-04 \
  --case test_cas_write_race_revalidates
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase candidate \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-green-04 \
  --case test_cas_write_race_revalidates
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite coop --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-02-coop
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite recovery --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-02-recovery
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite run --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-02-run
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite cas --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-02-cas
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite cards --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-02-cards
  ;;
cards-03)
# 主控 #43：只复验 cards 收证据修复，不重跑已通过的 8/9/18/CAS。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --suite cards --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-regression-03-cards
  ;;
conflict-red-01)
# 只验证起点缺失的冲突流程；替换原生会话边界，不启动真实 CLI。
# 源码从已确认的 red-01 冻结快照重建，逐文件核对起点 14b57d22。
t077_baseline_product=$(python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/prepare_s3_baseline.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/baseline-conflict-red-01.json)
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase baseline --baseline-product "$t077_baseline_product" \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-conflict-red-01 \
  --case test_conflict_active_worker_reworks_and_integrates \
  --case test_conflict_ended_session_gets_new_attempt \
  --case test_conflict_unknown_session_preserves_scene_and_reports \
  --case test_conflict_unknown_delivery_does_not_resend \
  --case test_merge_command_error_is_not_text_conflict \
  --case test_conflict_rework_still_rejects_forbidden_path \
  --case test_conflict_rework_still_rejects_foreign_trailer
  ;;
conflict-green-01)
# 主控 #47 已确认同一七项起点业务红态。只运行本批冲突候选，真实用量 0。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase candidate \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-conflict-green-01 \
  --case test_conflict_active_worker_reworks_and_integrates \
  --case test_conflict_ended_session_gets_new_attempt \
  --case test_conflict_unknown_session_preserves_scene_and_reports \
  --case test_conflict_unknown_delivery_does_not_resend \
  --case test_merge_command_error_is_not_text_conflict \
  --case test_conflict_rework_still_rejects_forbidden_path \
  --case test_conflict_rework_still_rejects_foreign_trailer
# 两份旧窗格探针只补 session_meta.cwd；原断言不变，复验实际受影响的边界。
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_native_final_read.ts \
  /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-conflict-native-final-01
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_pane_dispatch_state.ts \
  /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-conflict-dispatch-state-01
  ;;
rebase-01)
# 主控 #54：同一提交一次复验。只允许证据目录变化；不运行真实 Codex。
t077_require_rebased_candidate() {
  [[ "$(git -C /Users/luckye/Documents/Code/a2a-wt-t077 rev-parse HEAD)" == '446f25c3de00925dfcc2f1c3f1375713676e166b' ]]
  [[ "$(git -C /Users/luckye/Documents/Code/a2a-wt-t077 rev-parse HEAD^)" == '457e02a867bfdc5d8b06a9d14214eb7a429c48c2' ]]
  git -C /Users/luckye/Documents/Code/a2a-wt-t077 diff --exit-code HEAD -- workbench acceptance fixtures/pagination
  [[ -z "$(git -C /Users/luckye/Documents/Code/a2a-wt-t077 ls-files --others --exclude-standard -- workbench/src workbench/hooks workbench/tests acceptance fixtures/pagination)" ]]
}
t077_require_rebased_candidate
# 25 项全部运行，已包含冲突 7 项，不再重复运行冲突子集。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase candidate \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-contracts
t077_require_rebased_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --suite coop \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-coop
t077_require_rebased_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --suite recovery \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-recovery
t077_require_rebased_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --suite run \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-run
t077_require_rebased_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --suite cas \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-cas
t077_require_rebased_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --suite cards \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-cards
t077_require_rebased_candidate
# 直接受合流影响的窗格、稳定原生身份和停机边界；均为零模型回合。
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_conflict_panes.ts \
  --product /Users/luckye/Documents/Code/a2a-wt-t077 \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-panes.json
t077_require_rebased_candidate
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_native_final_read.ts \
  /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-native-final
t077_require_rebased_candidate
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_pane_dispatch_state.ts \
  /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-dispatch-state
t077_require_rebased_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_multiturn_identity_e2e.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t077 --case all \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-identity
t077_require_rebased_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_startup_shutdown_e2e.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t077 \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-01-shutdown
t077_require_rebased_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/summarize-rebase-01.py
  ;;
rebase-fix-02)
# 主控 #58：真实归档已证明 cwd 等于 -C，只修夹具元数据，复验三个受影响组。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/check-shutdown-fixture-repair.py \
  --mode prepare --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-fix-02
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_startup_shutdown_e2e.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t077 \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-fix-02/shutdown
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_multiturn_identity_e2e.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t077 --case all \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-fix-02/identity
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_conflict_panes.ts \
  --product /Users/luckye/Documents/Code/a2a-wt-t077 \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-fix-02/panes.json
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/check-shutdown-fixture-repair.py \
  --mode collect --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-rebase-fix-02
  ;;
relay-check-01)
# 主控 #66：真实预算 4/4，下面只有受控 PTY；无真实 Codex、凭据或新增模型回合。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-relay-check.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-check-01
  ;;
relay-check-02)
# 主控 #72：只修取 launch 的路径与 pane_* 夹具参数，不改业务断言。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-relay-check.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-check-02
  ;;
relay-regression-01)
# 主控 #73：固定 relay 修复提交，一次完成脚本验收；不准备或启动真实 Codex。
t077_require_relay_candidate() {
  [[ "$(git -C /Users/luckye/Documents/Code/a2a-wt-t077 rev-parse HEAD)" == 'da44c6733f5046f7c645028352859a80070f15b9' ]]
  [[ "$(git -C /Users/luckye/Documents/Code/a2a-wt-t077 rev-parse HEAD^)" == '93094e7be82c21448c460436c360ffb0f75a3412' ]]
  git -C /Users/luckye/Documents/Code/a2a-wt-t077 diff --exit-code HEAD -- workbench acceptance fixtures/pagination
  [[ -z "$(git -C /Users/luckye/Documents/Code/a2a-wt-t077 ls-files --others --exclude-standard -- workbench/src workbench/hooks workbench/tests acceptance fixtures/pagination)" ]]
}
t077_require_relay_candidate
# 25 项全部运行，已包含冲突 7 项，不再重复运行冲突子集。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_worktree_lifecycle_e2e.py \
  --phase candidate \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-contracts
t077_require_relay_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --suite coop \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-coop
t077_require_relay_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --suite recovery \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-recovery
t077_require_relay_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --suite run \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-run
t077_require_relay_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --suite cas \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-cas
t077_require_relay_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/run_s3_regression.py \
  --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --suite cards \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-cards
t077_require_relay_candidate
# 完成条件的窗格、原生记录、身份与停机边界；均为零模型回合。
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_conflict_panes.ts \
  --product /Users/luckye/Documents/Code/a2a-wt-t077 \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-panes.json
t077_require_relay_candidate
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_native_final_read.ts \
  /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-native-final
t077_require_relay_candidate
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_pane_dispatch_state.ts \
  /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-dispatch-state
t077_require_relay_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_multiturn_identity_e2e.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t077 --case all \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-identity
t077_require_relay_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_startup_shutdown_e2e.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t077 \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-shutdown
t077_require_relay_candidate
# relay 的交付闭环、正反例和本次指定的全库去重变异体。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_relay_conflict_e2e.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t077 \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-relay-conflict
t077_require_relay_candidate
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_relay_scope.ts \
  /Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/relay.ts \
  /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-relay-scope
t077_require_relay_candidate
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_relay_core.ts \
  /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-relay-core
t077_require_relay_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_relay_cli.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-relay-cli
t077_require_relay_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/check-relay-mutants.py \
  --mutant global-lookup \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-relay-mutant
t077_require_relay_candidate
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/summarize-relay-regression-01.py
  ;;
real-recheck-01)
# 用户额外预算 20261012T015257Z-ideation-answer-001；本次 launch 另须主控明确审批。
: "${T077_REAL_APPROVAL:?必须填写第二实例第一次启动的主控批准引用}"
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-real-conflict-02.py \
  --phase 1 --approval-ref "$T077_REAL_APPROVAL"
  ;;
real-recheck-02)
: "${T077_REAL_APPROVAL:?必须填写第二实例第二次启动的主控批准引用}"
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-real-conflict-02.py \
  --phase 2 --approval-ref "$T077_REAL_APPROVAL"
  ;;
r3-plan-check-01)
# 主控 #83：只核对显式 default 的准备材料，不启动真实 CLI。
node /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/check-real-launch-offline-03.ts \
  /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/real-plan-03.json \
  /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/r3-plan-check-01.json
  ;;
real-r3-launch-01)
# 主控 #85：预算已批；Launch 1 本身仍须逐次审批，不自动运行 Launch 2。
: "${T077_REAL_APPROVAL:?必须填写 r3 Launch 1 本次主控批准引用}"
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-real-conflict-03.py \
  --phase 1 --approval-ref "$T077_REAL_APPROVAL"
  ;;
real-r3-launch-02)
: "${T077_REAL_APPROVAL:?必须填写 r3 Launch 2 本次主控批准引用}"
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-real-conflict-03.py \
  --phase 2 --approval-ref "$T077_REAL_APPROVAL"
  ;;
rebase-final-01)
# 主控 #108：冻结 c3eb705c；受控变体先红、候选联合检查及完整回归；真实模型 0。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-rebase-final-01.py
  ;;
controlled-trailer-proofs-01)
# 真实 CLI/Git/门禁，受控原生运行时；先杀死放过额外尾注的变体，再跑两条候选证明。
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-controlled-trailer-proofs.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-controlled-trailer-proofs-01
  ;;
real-01)
: "${T077_REAL_APPROVAL:?必须填写本次真实启动的执行主控批准引用}"
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-real-conflict.py \
  --phase 1 --approval-ref "$T077_REAL_APPROVAL"
  ;;
real-02)
: "${T077_REAL_APPROVAL:?必须填写第二次真实启动的执行主控批准引用}"
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-real-conflict.py \
  --phase 2 --approval-ref "$T077_REAL_APPROVAL"
  ;;
*)
  echo 'usage: outside-sandbox.sh red-01|check-01|check-02|check-03|check-04|cards-03|conflict-red-01|conflict-green-01|rebase-01|rebase-fix-02|real-01|real-02|relay-check-01|relay-check-02|relay-regression-01|real-recheck-01|real-recheck-02|r3-plan-check-01|real-r3-launch-01|real-r3-launch-02|controlled-trailer-proofs-01|rebase-final-01' >&2
  exit 2
  ;;
esac

# 两次启动的完整 argv / shell argv / hook 命令已固定在同目录 real-plan-01.json，
# 人工核对版见 REAL-APPROVAL-01.md。第一次结束在第二次审批之前；不自动连跑。
