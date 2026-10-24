#!/bin/zsh
set -u

cd /Users/luckye/Documents/Code/a2a-wt-t159 || exit 1
result_dir=$(mktemp -d evidence/2026-10-23-batch24/T-159/outside-01-XXXXXXXX) || exit 1
export PYTHONPYCACHEPREFIX=/private/tmp/t159-outside-pycache
print -r -- "RESULT_DIR=$result_dir"

# Run the unchanged product first. A setup failure is not defect evidence.
python3 workbench/tests/test_t159_split_e2e.py \
  --revision c01742804961214ed025b6c9fb9924a1ea49ee2d \
  --summary "$result_dir/red.json" > "$result_dir/red.log" 2>&1
red_exit=$?
python3 - "$result_dir/red.json" "$red_exit" <<'PY'
import json
from pathlib import Path
import sys
path = Path(sys.argv[1])
assert path.is_file(), 'INCOMPLETE: no summary; inspect red.log'
value = json.loads(path.read_text(encoding='utf-8'))
observed = value.get('observed', {}).get('right', {})
panes = observed.get('panes', [])
assert sys.argv[2] == '1', value
assert value.get('error', '').startswith('AssertionError: task_right_explains_before_action:'), value
assert len(panes) == 1 and panes[0]['role'] == 'shell', value
assert panes[0]['launch'] != value['observed']['worker'], value
assert not value.get('cleanup_errors'), value
print('PASS: defect-specific red state; original worker replaced by one project shell')
print('Preserved fixture:', value['fixture'])
PY
oracle_exit=$?
if (( oracle_exit != 0 )); then
  print -r -- "INCOMPLETE: red state not established. Preserve $result_dir and return its path."
  exit "$oracle_exit"
fi

# Existing checks for the directly affected T-139 view model; zero model calls.
node --experimental-vm-modules workbench/tests/test_t139_selection.mjs "$result_dir/selection.json" > "$result_dir/selection.log" 2>&1
selection_exit=$?
node --experimental-vm-modules workbench/tests/test_t139_layout_store.mjs "$result_dir/layout-store.json" > "$result_dir/layout-store.log" 2>&1
layout_exit=$?
node workbench/tests/test_t139_terminal_catalog.mjs "$result_dir/terminal-catalog.json" > "$result_dir/terminal-catalog.log" 2>&1
catalog_exit=$?
print -r -- "red_oracle=$oracle_exit selection=$selection_exit layout=$layout_exit catalog=$catalog_exit" > "$result_dir/exits.txt"
print -r -- "Return $result_dir (including red.json, screenshots and exits.txt)."
if (( selection_exit || layout_exit || catalog_exit )); then
  print -r -- "INCOMPLETE: existing view-model checks failed; preserve their baseline results."
  exit 1
fi
print -r -- 'PASS: red state established; product fix remains pending.'
