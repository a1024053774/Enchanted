#!/bin/zsh
set -u

# Product queued-turn correction: rerun all 10 cases from 03 plus all 3 from 04.
# The second positive is a separate planned case with fresh state/sentinel, not a retry.
# Real daemon, PTY, Claude CLI and Electron; the model backend is local scripted Messages.
task_root="${0:A:h:h:h:h}"
run_dir="$(mktemp -d /private/tmp/t157-outside-05.XXXXXX)" || exit 2
print -r -- "RUN_DIR=$run_dir"
cd "$task_root" || exit 2
git rev-parse HEAD > "$run_dir/candidate.txt"
run_probe() {
  local run_name="$1"
  shift
  python3 -B "$@" --summary "$run_dir/$run_name.json" > "$run_dir/$run_name.log" 2>&1
  local run_code=$?
  print -r -- "$run_name TEST_EXIT=$run_code SUMMARY=$run_dir/$run_name.json"
}
run_probe stop-input-positive workbench/tests/test_t157_stop_input_e2e.py
run_probe stale-baseline workbench/tests/test_t157_stale_turn_e2e.py --revision c6725344ae81dce51656b2e44d1035a247df6604
run_probe stale-recover workbench/tests/test_t157_stale_turn_e2e.py
run_probe stale-expired workbench/tests/test_t157_stale_turn_e2e.py --scenario expired
run_probe mutant-old-stop workbench/tests/test_t157_stale_turn_e2e.py --mutant execute-old-stop
run_probe mutant-no-reason workbench/tests/test_t157_stale_turn_e2e.py --mutant hide-reason
run_probe mutant-no-recovery workbench/tests/test_t157_stale_turn_e2e.py --mutant hide-recovery
run_probe split-regression workbench/tests/test_t159_split_e2e.py
run_probe review-regression workbench/tests/test_t160_review_recovery_e2e.py
run_probe controller-regression workbench/tests/test_t133_t107_terminal_controller_e2e.py

run_probe stop-input-positive-04 workbench/tests/test_t157_stop_input_e2e.py
run_probe stop-input-baseline workbench/tests/test_t157_stop_input_e2e.py --revision ef99842b35e17c4cd69e1e58d5afca0689bf88b1
run_probe stop-input-bad-caller workbench/tests/test_t157_stop_input_e2e.py --mutant submit-never-active

python3 - "$run_dir" <<'PY'
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
expected_failures = {
    'stale-baseline': 'stale_submit_explicitly_refused',
    'mutant-old-stop': 'unmatched_stop_never_enters_execution',
    'mutant-no-reason': 'header_and_sidebar_explain_refusal',
    'mutant-no-recovery': 'recovery_action_exists_but_no_automatic_retry',
}
names = ['stop-input-positive', 'stale-baseline', 'stale-recover', 'stale-expired',
         'mutant-old-stop', 'mutant-no-reason', 'mutant-no-recovery',
         'split-regression', 'review-regression', 'controller-regression',
         'stop-input-positive-04', 'stop-input-baseline', 'stop-input-bad-caller']
checks = []
for name in names:
    path = root / (name + '.json')
    if not path.is_file():
        checks.append(dict(name=name, passed=False, reason='summary absent'))
        continue
    report = json.loads(path.read_text(encoding='utf-8'))
    if name in ('stop-input-baseline', 'stop-input-bad-caller'):
        observed = {item['name']: item['passed'] for item in report.get('checks', [])}
        refused = any(event['type'] == 'relay_rejected' and
                      event['data'].get('result', {}).get('error') == 'worker_not_active'
                      for event in report.get('observed', {}).get('timeline', []))
        passed = (report.get('status') == 'INCOMPLETE' and refused and
                  observed.get('original_stop_submit_accepted') is False and
                  observed.get('input_intersects_original_stop_batch') is True and
                  observed.get('input_bytes_unchanged') is True and not report.get('errors'))
    elif name in expected_failures:
        failed = [c for c in report.get('checks', []) if c.get('name') == expected_failures[name] and c.get('passed') is False]
        native = [c for c in report.get('checks', []) if c.get('name') == 'actual_native_new_turn_after_original_stop' and c.get('passed') is True]
        passed = bool(failed and native) and report.get('status') == 'INCOMPLETE' and not report.get('errors')
    else:
        passed = report.get('status') == 'PASS' and not report.get('errors')
    checks.append(dict(name=name, passed=passed, status=report.get('status'), summary=str(path), errors=report.get('errors')))
result = dict(status='PASS' if all(c['passed'] for c in checks) else 'INCOMPLETE', checks=checks,
              scope='13-case candidate checkpoint after queued native turn correction; independent acceptance remains separate', vendor_model_turns=0)
with (root / 'RESULT.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
PY
