#!/bin/zsh
set -u

cd /Users/luckye/Documents/Code/a2a-wt-t159 || exit 1
git diff --quiet HEAD -- workbench || { print -r -- 'INCOMPLETE: workbench has uncommitted changes'; exit 1; }
result_dir=$(mktemp -d evidence/2026-10-23-batch24/T-159/outside-04-XXXXXXXX) || exit 1
export PYTHONPYCACHEPREFIX=/private/tmp/t159-outside-pycache
print -r -- "RESULT_DIR=$result_dir"
git rev-parse HEAD > "$result_dir/candidate.txt"

# Dispatch #54 explicitly permits reuse of this real Electron pre-fix observation.
python3 - <<'PY' > "$result_dir/reused-red.txt" 2>&1
import json
from pathlib import Path
path = Path('evidence/2026-10-23-batch24/T-159/outside-01-dJtqcETt/red.json')
red = json.loads(path.read_text(encoding='utf-8'))
assert red['code_version'] == 'c01742804961214ed025b6c9fb9924a1ea49ee2d'
panes = red['observed']['right']['panes']
assert len(panes) == 1 and panes[0]['role'] == 'shell' and panes[0]['launch'] != red['observed']['worker']
assert red['observed']['right']['selection']['task'] is None and not red.get('cleanup_errors')
print('PASS: reused real Electron replacement red state:', path)
print('Original assertion belonged to the withdrawn disabled-menu contract; this reuse proves the observed worker replacement only.')
PY
red_exit=$?
if (( red_exit )); then print -r -- "INCOMPLETE: inspect $result_dir/reused-red.txt"; exit "$red_exit"; fi

python3 workbench/tests/test_t159_split_e2e.py --summary "$result_dir/green.json" > "$result_dir/green.log" 2>&1
green_exit=$?
python3 workbench/tests/test_t159_split_e2e.py --mutant replace-worker --summary "$result_dir/mutant-replace.json" > "$result_dir/mutant-replace.log" 2>&1
replace_exit=$?
python3 workbench/tests/test_t159_split_e2e.py --mutant shell-input-to-worker --summary "$result_dir/mutant-intervention.json" > "$result_dir/mutant-intervention.log" 2>&1
intervention_exit=$?

node --experimental-vm-modules workbench/tests/test_t139_selection.mjs "$result_dir/selection.json" > "$result_dir/selection.log" 2>&1
selection_exit=$?
node --experimental-vm-modules workbench/tests/test_t139_layout_store.mjs "$result_dir/layout-store.json" > "$result_dir/layout-store.log" 2>&1
layout_exit=$?
node workbench/tests/test_t139_terminal_catalog.mjs "$result_dir/terminal-catalog.json" > "$result_dir/terminal-catalog.log" 2>&1
catalog_exit=$?
# Real Claude CLI with the existing isolated local scripted Messages endpoint; no vendor model calls.
python3 workbench/tests/test_t139_t143_views_perf_e2e.py --summary "$result_dir/t139-t143.json" > "$result_dir/t139-t143.log" 2>&1
perf_exit=$?
print -r -- "red=$red_exit green=$green_exit replace=$replace_exit intervention=$intervention_exit selection=$selection_exit layout=$layout_exit catalog=$catalog_exit t139_t143=$perf_exit" > "$result_dir/exits.txt"

python3 - "$result_dir" "$green_exit" "$replace_exit" "$intervention_exit" "$selection_exit" "$layout_exit" "$catalog_exit" "$perf_exit" <<'PY'
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
green, replace, intervention, selection, layout, catalog, perf = map(int, sys.argv[2:])
revision = (root / 'candidate.txt').read_text(encoding='utf-8').strip()
def read(name):
    path = root / (name + '.json')
    assert path.is_file(), 'INCOMPLETE: missing ' + str(path)
    value = json.loads(path.read_text(encoding='utf-8'))
    assert not value.get('cleanup_errors'), value
    if 'code_version' in value: assert value['code_version'] == revision, value
    return value
candidate = read('green')
assert green == 0 and candidate['status'] == 'PASS', candidate
required = {'task_right_keeps_worker', 'task_down_keeps_worker', 'task_right_geometry', 'task_down_geometry',
            'task_right_ordinary_root_terminal', 'task_down_ordinary_root_terminal',
            'task_right_catalog_not_worker', 'task_down_catalog_not_worker',
            'task_right_no_intervention', 'task_down_no_intervention',
            'task_right_worker_unchanged', 'task_down_worker_unchanged',
            'task_right_actual_pwd', 'task_down_actual_pwd',
            'task_explicit_terminals_restored', 'task_restores_down_geometry', 'close_discussion_preserves_worker',
            'task_return_only_explicit_terminals', 'single_worker_excludes_discussion_terminals',
            'project_controller_right_keeps_original', 'intervention_observer_positive_control', 'zero_model_requests'}
checks = candidate['checks']
assert required <= {c['name'] for c in checks if c['passed']} and all(c['passed'] for c in checks), candidate
bad = read('mutant-replace')
assert replace == 1 and bad.get('error', '').startswith('AssertionError: task_right_keeps_worker:'), bad
panes = bad.get('observed', {}).get('right', {}).get('panes', [])
assert len(panes) == 1 and panes[0]['role'] == 'shell' and panes[0]['launch'] != bad['observed']['worker'], bad
bad = read('mutant-intervention')
assert intervention == 1 and bad.get('error', '').startswith('AssertionError: task_right_no_intervention:'), bad
assert any(c['name'] == 'task_right_catalog_not_worker' and c['passed'] for c in bad['checks']), bad
for name, code in [('selection', selection), ('layout-store', layout), ('terminal-catalog', catalog), ('t139-t143', perf)]:
    value = read(name)
    assert code == 0 and value['status'] == 'PASS' and not value.get('failures'), value
print('PASS: task discussion split, worker isolation, both mutations rejected, T-139/T-143 regressions')
print('Preserve fixtures and return result directory:', root)
PY
oracle_exit=$?
print -r -- "oracle=$oracle_exit" >> "$result_dir/exits.txt"
exit "$oracle_exit"
