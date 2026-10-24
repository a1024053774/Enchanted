#!/bin/zsh
set -u

# 最后一轮：只有 oracle 绿态 + parent-instructions 变异，最多 4 回合，累计最多 14/16。
# 若未绿，停下报告残余失败，不重试、不再改说明、不改判据。
cd /Users/luckye/Documents/Code/a2a-wt-t163 || exit 2
run_dir=$(mktemp -d /private/tmp/t163-outside-04.XXXXXX) || exit 2
tag=${run_dir:t}
evidence=evidence/2026-10-23-batch24/T-163
budget="$evidence/model-budget.jsonl"

# Claim this one authorized round before any model starts. A repeated script invocation is refused.
python3 - "$budget" "$evidence/RUN-OUTSIDE-04-started.json" "$run_dir" <<'PY'
import json, sys
from pathlib import Path
ledger, marker, run_dir = map(Path, sys.argv[1:])
reserved = sum(json.loads(line)['reserved_turns'] for line in ledger.read_text(encoding='utf-8').splitlines())
assert reserved <= 10, '现有预留会使本轮超过累计 14 回合；停止，交主控核对'
with marker.open('x', encoding='utf-8') as stream:
    json.dump(dict(run_dir=str(run_dir), reserved_before=reserved, maximum_new_turns=4,
                   maximum_cumulative_turns=14, authority='执行主控 #50，最后一轮'), stream, ensure_ascii=False, indent=2)
    stream.write('\n')
PY
preflight_rc=$?
if (( preflight_rc != 0 )); then
  exit 2
fi
print -r -- "RUN_DIR=$run_dir MAX_REAL_TURNS=4 MAX_CUMULATIVE_REAL_TURNS=14"

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
  print -r -- '最后一轮 oracle 仍未绿：跳过变异，停止。不再修改说明，不自动重试，交主控转构思主控决定。'
fi

print -r -- "ORACLE_EXIT=$oracle_rc MUTANT_EXIT=$mutant_rc SUMMARY_PREFIX=$evidence/$tag"
print -r -- '期望 oracle PASS；变异 NO_GO 且有业务失败，均无 error/cleanup_errors。若环境失败，仍如实记 INCOMPLETE。'
print -r -- '请回传所有摘要与实际根回合数；保留 fixture 原件，交主控归档。'
if (( oracle_rc != 0 || mutant_rc != 1 )); then
  exit 1
fi
exit 0
