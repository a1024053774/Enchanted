#!/bin/zsh
set -u

cd /Users/luckye/Documents/Code/a2a-wt-t159 || exit 1
git diff --quiet HEAD -- workbench || { print -r -- 'INCOMPLETE: workbench has uncommitted changes'; exit 1; }
result_dir=$(mktemp -d evidence/2026-10-23-batch24/T-159/outside-03-XXXXXXXX) || exit 1
export PYTHONPYCACHEPREFIX=/private/tmp/t159-outside-pycache
print -r -- "RESULT_DIR=$result_dir"
git rev-parse HEAD > "$result_dir/candidate.txt"

python3 workbench/tests/test_t159_split_e2e.py --summary "$result_dir/green.json" > "$result_dir/green.log" 2>&1
green_exit=$?
python3 workbench/tests/test_t159_split_e2e.py --mutant old-task-split --summary "$result_dir/mutant-old.json" > "$result_dir/mutant-old.log" 2>&1
old_exit=$?
python3 workbench/tests/test_t159_split_e2e.py --mutant missing-split-guard --summary "$result_dir/mutant-guard.json" > "$result_dir/mutant-guard.log" 2>&1
guard_exit=$?
print -r -- "green=$green_exit old_mutant=$old_exit guard_mutant=$guard_exit" > "$result_dir/exits.txt"

# Require the new real controller scene and the original defect-specific mutation failures.
python3 - "$result_dir" "$green_exit" "$old_exit" "$guard_exit" <<'PY'
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
green, old, guard = map(int, sys.argv[2:])
def read(name):
    path = root / (name + '.json')
    assert path.is_file(), 'INCOMPLETE: missing ' + str(path)
    value = json.loads(path.read_text(encoding='utf-8'))
    assert not value.get('cleanup_errors'), value
    assert value['code_version'] == (root / 'candidate.txt').read_text(encoding='utf-8').strip(), value
    return value
candidate = read('green')
assert green == 0 and candidate['status'] == 'PASS', candidate
required = {'task_right_explains_before_action', 'task_down_explains_before_action',
            'task_right_ipc_refused_with_explanation', 'task_down_ipc_refused_with_explanation',
            'shell_right_geometry', 'shell_down_geometry', 'task_return_excludes_project_terminals',
            'single_agent_only_itself', 'zero_model_requests', 'project_controller_approved',
            'project_controller_view_is_project_scoped', 'project_controller_right_split_enabled',
            'project_controller_right_keeps_original', 'project_controller_right_geometry',
            'project_controller_role_preserved'}
checks = candidate['checks']
assert required <= {c['name'] for c in checks if c['passed']} and all(c['passed'] for c in checks), candidate
bad = read('mutant-old')
assert old == 1 and bad.get('error', '').startswith('AssertionError: task_right_explains_before_action:'), bad
panes = bad.get('observed', {}).get('right', {}).get('panes', [])
assert len(panes) == 1 and panes[0]['role'] == 'shell' and panes[0]['launch'] != bad['observed']['worker'], bad
bad = read('mutant-guard')
assert guard == 1 and bad.get('error', '').startswith('AssertionError: task_right_ipc_refused_with_explanation:'), bad
assert any(c['name'] == 'task_right_explains_before_action' and c['passed'] for c in bad['checks']), bad
print('PASS: real Electron project-controller split retained the original pane; both original mutations rejected')
print('Preserve fixtures and return result directory:', root)
PY
oracle_exit=$?
print -r -- "oracle=$oracle_exit" >> "$result_dir/exits.txt"
exit "$oracle_exit"
