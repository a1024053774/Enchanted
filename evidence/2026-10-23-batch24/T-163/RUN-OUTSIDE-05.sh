#!/bin/zsh
set -u

# 执行主控 #55：用户“B 继续改说明”，追加至多两轮、共 8 回合，累计上限 20。
# 追加第一轮仅 oracle 绿态 + parent-instructions 变异，预计最多 4 回合，累计最多 16/20。
# 绿态失败跳过变异，不自动重试；不改场景提示、oracle 样本或原判据。
cd /Users/luckye/Documents/Code/a2a-wt-t163 || exit 2
run_dir=$(mktemp -d /private/tmp/t163-outside-05.XXXXXX) || exit 2
tag=${run_dir:t}
evidence=evidence/2026-10-23-batch24/T-163
budget="$evidence/model-budget.jsonl"

python3 - "$budget" "$evidence/RUN-OUTSIDE-05-started.json" "$run_dir" <<'PY'
import json, sys
from pathlib import Path
ledger, marker, run_dir = map(Path, sys.argv[1:])
rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()]
reserved = sum(row['reserved_turns'] for row in rows)
assert reserved == 12, '第五轮须从已核对的 12 回合继续；停止交主控核对，不重置账本'
assert any(row.get('event') == 'authorization-extension-01' for row in rows), '缺少当前追加授权记录'
with marker.open('x', encoding='utf-8') as stream:
    json.dump(dict(run_dir=str(run_dir), reserved_before=reserved, maximum_new_turns=4,
                   extension_round=1, maximum_extension_rounds=2, maximum_extension_turns=8,
                   maximum_cumulative_turns=20, authority='执行主控 #55，用户 B 继续改说明'), stream, ensure_ascii=False, indent=2)
    stream.write('\n')
PY
preflight_rc=$?
if (( preflight_rc != 0 )); then
  exit 2
fi
print -r -- "RUN_DIR=$run_dir EXPECTED_REAL_TURNS=4 MAX_CUMULATIVE_REAL_TURNS=20"

python3 workbench/tests/test_t163_controller_e2e.py --scenario oracle --budget-limit 20 \
  --budget "$budget" --summary "$evidence/$tag-oracle-green.json" > "$run_dir/oracle.log" 2>&1
oracle_rc=$?
cat "$run_dir/oracle.log"

mutant_rc=125
if (( oracle_rc == 0 )); then
  python3 workbench/tests/test_t163_controller_e2e.py --scenario oracle --mutant parent-instructions --budget-limit 20 \
    --budget "$budget" --summary "$evidence/$tag-oracle-parent-mutant.json" > "$run_dir/mutant.log" 2>&1
  mutant_rc=$?
  cat "$run_dir/mutant.log"
else
  print -r -- 'oracle 未绿，保留失败、跳过变异；本轮不自动重试。还剩最多一个追加轮次，交回 worker 读原生记录。'
fi

print -r -- "ORACLE_EXIT=$oracle_rc MUTANT_EXIT=$mutant_rc SUMMARY_PREFIX=$evidence/$tag"
print -r -- '严格 oracle 与旧判据不变：绿态应 PASS；变异应 NO_GO 且有业务失败。环境/身份/清理错误不算红态。'
print -r -- '请回传摘要、实际回合数和原生记录位置；新 fixture 原件仍按 T-088 由主控归档。'
if (( oracle_rc != 0 || mutant_rc != 1 )); then
  exit 1
fi
exit 0
