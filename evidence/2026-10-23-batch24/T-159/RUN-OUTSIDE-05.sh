#!/bin/zsh
set -u

cd /Users/luckye/Documents/Code/a2a-wt-t159 || exit 1
git diff --quiet HEAD -- workbench || { print -r -- 'INCOMPLETE: workbench has uncommitted changes'; exit 1; }
result_dir=$(mktemp -d evidence/2026-10-23-batch24/T-159/outside-05-XXXXXXXX) || exit 1
export PYTHONPYCACHEPREFIX=/private/tmp/t159-outside-pycache
print -r -- "RESULT_DIR=$result_dir"
git rev-parse HEAD > "$result_dir/candidate.txt"

# Dispatch #60: rerun only green after fixing the positive control's overwritten baseline.
python3 workbench/tests/test_t159_split_e2e.py --summary "$result_dir/green.json" > "$result_dir/green.log" 2>&1
green_exit=$?
print -r -- "green=$green_exit" > "$result_dir/exits.txt"

python3 - "$result_dir" "$green_exit" <<'PY'
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
path = root / 'green.json'
assert path.is_file(), 'INCOMPLETE: no green summary; inspect green.log'
value = json.loads(path.read_text(encoding='utf-8'))
assert sys.argv[2] == '0' and value['status'] == 'PASS' and not value.get('cleanup_errors'), value
assert value['code_version'] == (root / 'candidate.txt').read_text(encoding='utf-8').strip(), value
required = {'task_right_keeps_worker', 'task_down_keeps_worker', 'task_right_geometry', 'task_down_geometry',
            'task_right_ordinary_root_terminal', 'task_down_ordinary_root_terminal',
            'task_right_catalog_not_worker', 'task_down_catalog_not_worker',
            'task_right_no_intervention', 'task_down_no_intervention',
            'task_right_worker_unchanged', 'task_down_worker_unchanged',
            'task_right_actual_pwd', 'task_down_actual_pwd', 'task_explicit_terminals_restored',
            'task_restores_down_geometry', 'close_discussion_preserves_worker',
            'task_return_only_explicit_terminals', 'single_worker_excludes_discussion_terminals',
            'project_controller_right_keeps_original', 'intervention_observer_positive_control', 'zero_model_requests'}
checks = value['checks']
assert all(c['passed'] for c in checks) and required <= {c['name'] for c in checks if c['passed']}, value
print('PASS: real Electron green completed, including the live intervention positive control')
print('Preserve fixture and return result directory:', root)
PY
oracle_exit=$?
print -r -- "oracle=$oracle_exit" >> "$result_dir/exits.txt"
exit "$oracle_exit"
