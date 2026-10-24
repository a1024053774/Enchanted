#!/bin/zsh
set -u

# 执行主控 #55/#57 授权的追加第二轮、最后一轮；只做 oracle 绿态与旧说明变异。
# 当前实际 14/20；预计最多新增 4，累计最多 18/20。未绿则新增 2 并跳过变异。
# 不自动重试；结果回来按用户授权的 A 口径收尾，不再修改说明或询问。
cd /Users/luckye/Documents/Code/a2a-wt-t163 || exit 2
run_dir=$(mktemp -d /private/tmp/t163-outside-06.XXXXXX) || exit 2
tag=${run_dir:t}
evidence=evidence/2026-10-23-batch24/T-163
budget="$evidence/model-budget.jsonl"

python3 - "$budget" "$evidence/RUN-OUTSIDE-05-started.json" "$evidence/RUN-OUTSIDE-06-started.json" "$run_dir" <<'PY'
import json, sys
from pathlib import Path
ledger, previous, marker, run_dir = map(Path, sys.argv[1:])
rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()]
reserved = sum(row['reserved_turns'] for row in rows)
assert reserved == 14, '最后一轮须从已核对的 14 回合继续；不重置账本或自动重试'
assert previous.is_file(), '缺少追加第一轮启动记录'
assert any(row.get('event') == 'outside-05-observed' for row in rows), '缺少第五轮实际回合核对'
assert any(row.get('event') == 'authorization-extension-01' for row in rows), '缺少追加授权'
with marker.open('x', encoding='utf-8') as stream:
    json.dump(dict(run_dir=str(run_dir), reserved_before=reserved, maximum_new_turns=4,
                   extension_round=2, maximum_extension_rounds=2, maximum_extension_turns=8,
                   maximum_cumulative_turns=20, authority='执行主控 #55/#57，追加最后一轮'), stream, ensure_ascii=False, indent=2)
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
  print -r -- '严格 oracle 未绿，跳过变异。最后一轮结束，不再改说明、不重试；交回 worker 按 A 口径如实核对并 DELIVERED。'
fi

print -r -- "ORACLE_EXIT=$oracle_rc MUTANT_EXIT=$mutant_rc SUMMARY_PREFIX=$evidence/$tag"
print -r -- '严格 oracle 与判据未改；原始 NO_GO 不覆盖。A 口径另行报告失败项是否增加、错数字/缺项/反向购买是否拒绝，残余记 M02，整体否定交独立审查。'
print -r -- '请回传所有摘要、原生记录位置和实际根回合；环境错误如实报 INCOMPLETE，新 fixture 按 T-088 归档。'
if (( oracle_rc != 0 || mutant_rc != 1 )); then
  exit 1
fi
exit 0
