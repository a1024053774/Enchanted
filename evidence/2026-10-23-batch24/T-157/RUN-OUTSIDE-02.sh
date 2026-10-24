#!/bin/zsh
set -u

# Backend checkpoint only; renderer is still owned by T-159.
# Real Electron/daemon/CLI; local scripted Messages, zero vendor model turns.
task_root="${0:A:h:h:h:h}"
run_dir="$(mktemp -d /private/tmp/t157-outside-02.XXXXXX)" || exit 2
print -r -- "RUN_DIR=$run_dir"
cd "$task_root" || exit 2
run_probe() {
  local run_name="$1"
  shift
  python3 -B "$@" --summary "$run_dir/$run_name.json" > "$run_dir/$run_name.log" 2>&1
  local run_code=$?
  print -r -- "$run_name TEST_EXIT=$run_code SUMMARY=$run_dir/$run_name.json"
}
run_probe baseline workbench/tests/test_t157_stop_input_e2e.py --revision ef99842b35e17c4cd69e1e58d5afca0689bf88b1
run_probe candidate workbench/tests/test_t157_stop_input_e2e.py
run_probe reject-broken-caller workbench/tests/test_t157_stop_input_e2e.py --mutant submit-never-active
run_probe review-regression workbench/tests/test_t160_review_recovery_e2e.py
run_probe controller-regression workbench/tests/test_t133_t107_terminal_controller_e2e.py

python3 - "$run_dir" <<'PY'
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
checks = []
for name in ['baseline', 'candidate', 'reject-broken-caller', 'review-regression', 'controller-regression']:
    path = root / (name + '.json')
    if not path.is_file():
        checks.append(dict(name=name, passed=False, reason='summary absent'))
        continue
    report = json.loads(path.read_text(encoding='utf-8'))
    if name == 'baseline':
        passed = report.get('red_reproduced') is True and report.get('status') == 'INCOMPLETE' and not report.get('errors')
    elif name == 'reject-broken-caller':
        failed = [c for c in report.get('checks', []) if c.get('name') == 'original_stop_submit_accepted' and c.get('passed') is False]
        passed = bool(failed) and report.get('status') == 'INCOMPLETE' and not report.get('errors')
    else:
        passed = report.get('status') == 'PASS' and not report.get('errors')
    checks.append(dict(name=name, passed=passed, summary=str(path), status=report.get('status'), errors=report.get('errors')))
result = dict(status='PASS' if all(c['passed'] for c in checks) else 'INCOMPLETE', checks=checks,
              scope='Stop/input backend checkpoint; genuine-native-new-turn Electron/UI counterexample still pending', vendor_model_turns=0)
with (root / 'RESULT.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
PY
