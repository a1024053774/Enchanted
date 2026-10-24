#!/bin/zsh
set -u

# 候选绿态、同配置旧说明变异、T-158 说明回归。无自动重试。
# 既有实际 4/16 回合；本轮两绿态加 oracle 变异最多预留 6，累计不超过 10/16。
# C5 受管 worker 仍用本地脚本化 API；真实供应商调用仅来自三个主控会话。
# 夹具主控在临时 HOME 中允许 Bash，避免修前有限前缀误拦正常多行命令；产品权限不变。
cd /Users/luckye/Documents/Code/a2a-wt-t163 || exit 2
run_dir=$(mktemp -d /private/tmp/t163-outside-02.XXXXXX) || exit 2
tag=${run_dir:t}
evidence=evidence/2026-10-23-batch24/T-163
budget="$evidence/model-budget.jsonl"
print -r -- "RUN_DIR=$run_dir"

python3 workbench/tests/test_t163_controller_e2e.py --scenario c5 \
  --budget "$budget" --summary "$evidence/$tag-c5-green.json" > "$run_dir/c5.log" 2>&1
c5_rc=$?
cat "$run_dir/c5.log"

python3 workbench/tests/test_t163_controller_e2e.py --scenario oracle \
  --budget "$budget" --summary "$evidence/$tag-oracle-green.json" > "$run_dir/oracle.log" 2>&1
oracle_rc=$?
cat "$run_dir/oracle.log"

mutant_rc=125
if (( oracle_rc == 0 )); then
  python3 workbench/tests/test_t163_controller_e2e.py --scenario oracle --mutant parent-instructions \
    --budget "$budget" --summary "$evidence/$tag-oracle-parent-mutant.json" > "$run_dir/mutant.log" 2>&1
  mutant_rc=$?
  cat "$run_dir/mutant.log"
else
  print -r -- 'oracle 未绿：保留失败，不重试；跳过需要绿态对照的旧说明变异。'
fi

python3 workbench/tests/test_t158_revise_retry_e2e.py --check instructions \
  --summary "$evidence/$tag-t158-instructions.json" > "$run_dir/t158.log" 2>&1
regression_rc=$?
print -r -- "C5_EXIT=$c5_rc ORACLE_EXIT=$oracle_rc MUTANT_EXIT=$mutant_rc T158_EXIT=$regression_rc"
print -r -- "SUMMARY_PREFIX=$evidence/$tag"
print -r -- 'C5 自动状态仍为 INCOMPLETE，须主控读实际卡和原生记录：完整要求、派发前逐项核对、两 worker 确实派发、没有越过用户停点。修前遗漏未复现，不补称红态。'
print -r -- 'oracle 要求 PASS 且无 error/cleanup_errors；变异须 NO_GO 且至少一项业务 check 失败，无环境错误。变异偶然通过则如实记录，不自动复跑。'
print -r -- '请回传所有摘要和 C5 独立判断；fixture 原件保留，后续由主控按 T-088 归档。'
if (( oracle_rc != 0 || mutant_rc != 1 || regression_rc != 0 )); then
  exit 1
fi
# Zero means the automated commands have expected exits, not that C5 semantic review passed.
exit 0
