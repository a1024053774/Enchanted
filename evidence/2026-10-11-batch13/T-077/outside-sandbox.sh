#!/bin/bash
set -euo pipefail

# 执行主控运行。不启动真实 Codex，不安装 hook。
# 运行命令：
# bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh red-01
# 同名输出已存在时拒绝，不能覆盖原始失败。后续阶段另行批准/交回。
if [[ "$#" != 1 ]]; then
  echo 'usage: outside-sandbox.sh red-01|check-01|check-02|check-03|check-04|cards-03|conflict-red-01|conflict-green-01' >&2
  exit 2
fi
cd /Users/luckye/Documents/Code/a2a-wt-t077
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
*)
  echo 'usage: outside-sandbox.sh red-01|check-01|check-02|check-03|check-04|cards-03|conflict-red-01|conflict-green-01' >&2
  exit 2
  ;;
esac

# 真实场景尚未准备，不在本轮执行。准备时按决定 01 使用产品生成的完整 argv
# （实际路径/launch 参数在真实运行前固定并再次交回）：
# Codex 0.162.1；--no-daemon --no-alt-screen -C <本次隔离worktree>
# -a never --sandbox workspace-write -m gpt-6.1-sol
# -c model_reasoning_effort="xhigh" -c service_tier="fast"
# -c check_for_update_on_startup=false -c tui.notifications=false
# -c sandbox_workspace_write.network_access=false -c features.network_proxy=false
# -c hooks.UserPromptSubmit=<该launch的signal命令>
# -c hooks.Stop=<该launch的signal命令>
# -c hooks.PermissionRequest=<该launch的signal命令>
# --dangerously-bypass-hook-trust
# Git prepare-commit-msg 仅经 GIT_CONFIG_* 每会话环境指定现有目录。
# 上述占位记录不是可执行真实入口；完整 argv 未填定前不运行真实 Codex。
