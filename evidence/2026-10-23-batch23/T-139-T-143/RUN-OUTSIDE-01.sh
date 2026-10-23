#!/bin/zsh
set -u
cd /Users/luckye/Documents/Code/a2a-wt-t139-t143 || exit 2
run_dir=$(mktemp -d "$PWD/evidence/2026-10-23-batch23/T-139-T-143/outside-XXXXXXXX") || exit 2
export PYTHONPYCACHEPREFIX=/private/tmp/a2a-t139-pycache
test_file=workbench/tests/test_t139_t143_views_perf_e2e.py
failed=0
node --experimental-vm-modules workbench/tests/test_t139_selection.mjs "$run_dir/selection.json" > "$run_dir/selection.log" 2>&1 || failed=1
node --experimental-vm-modules workbench/tests/test_t139_layout_store.mjs "$run_dir/layout-store.json" > "$run_dir/layout-store.log" 2>&1 || failed=1

# Expected red must be a business assertion, with usable real Electron metrics.
python3 "$test_file" --revision ebbae7bd0 --summary "$run_dir/baseline.json" > "$run_dir/baseline.log" 2>&1
python3 - "$run_dir/baseline.json" <<'PY'
import json, sys
r=json.load(open(sys.argv[1]))
assert r['status']=='NO_GO' and 'task_A_only_its_agents' in r['failures'], r
assert r['metrics']['scroll_fps_median']>0 and r['metrics']['switch_ms_median']>0, r
print('PASS: expected baseline red, with metrics')
PY
if (( $? != 0 )); then
  print "INCOMPLETE：基线未取得；请回传 $run_dir，不运行性能改动。"
  exit 1
fi

# One variable at a time, against the same baseline and same command/fixture.
# These test-only copies do not change production or install dependencies.
for experiment in screen-reader-off poll-16ms; do
  python3 "$test_file" --revision ebbae7bd0 --experiment "$experiment" --summary "$run_dir/experiment-$experiment.json" > "$run_dir/experiment-$experiment.log" 2>&1
done

python3 "$test_file" --summary "$run_dir/t139-candidate.json" > "$run_dir/t139-candidate.log" 2>&1 || failed=1
for mutant in task-includes-project-terminal duplicate-replay; do
  python3 "$test_file" --mutant "$mutant" --summary "$run_dir/mutant-$mutant.json" > "$run_dir/mutant-$mutant.log" 2>&1
  python3 - "$run_dir/mutant-$mutant.json" "$mutant" <<'PY'
import json, sys
r=json.load(open(sys.argv[1]))
expected={'task-includes-project-terminal':'task_A_only_its_agents','duplicate-replay':'numbered_output_once_before_switch'}[sys.argv[2]]
assert r['status']=='NO_GO' and expected in r['failures'], r
PY
  if (( $? != 0 )); then failed=1; fi
done

node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs "$run_dir/t091.json" > "$run_dir/t091.log" 2>&1 || failed=1
python3 workbench/tests/test_t107_live_sidebar_e2e.py --summary "$run_dir/t107.json" > "$run_dir/t107.log" 2>&1 || failed=1
python3 workbench/tests/test_t133_t107_terminal_controller_e2e.py --summary "$run_dir/t133-t107.json" > "$run_dir/t133-t107.log" 2>&1 || failed=1
print "结果目录：$run_dir"
print 'T-143 仍需 worker 根据数字选择保留项、实现第四项试验，再跑同一联合 e2e；本脚本不是最终验收。'
exit "$failed"
