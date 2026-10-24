#!/bin/zsh
set -u

# 仅 oracle 绿态与 parent-instructions 变异；不复跑 C5，不自动重试。
# 已实用 8/16 回合；本轮预计 4、最多 4（绿态 2 + 变异 2），累计最多 12/16。
# 保持 RUN-OUTSIDE-02 的隔离权限、场景提示、全部业务样本与判据。
cd /Users/luckye/Documents/Code/a2a-wt-t163 || exit 2
run_dir=$(mktemp -d /private/tmp/t163-outside-03.XXXXXX) || exit 2
tag=${run_dir:t}
evidence=evidence/2026-10-23-batch24/T-163
budget="$evidence/model-budget.jsonl"
print -r -- "RUN_DIR=$run_dir EXPECTED_REAL_TURNS=4 MAX_REAL_TURNS=4"

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
  print -r -- 'oracle 未绿：保留失败，不自动重试，跳过需要绿态对照的旧说明变异。'
fi

print -r -- "ORACLE_EXIT=$oracle_rc MUTANT_EXIT=$mutant_rc SUMMARY_PREFIX=$evidence/$tag"
print -r -- '预期 oracle 为 PASS；变异为 NO_GO 且有业务 check 失败。两者须无 error/cleanup_errors，启动/权限/模型身份失败不算红态。'
print -r -- '请回传摘要与根回合核对；原始 fixture 保留给主控归档，不覆盖旧失败或更改判据。'
if (( oracle_rc != 0 || mutant_rc != 1 )); then
  exit 1
fi
exit 0
