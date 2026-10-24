#!/bin/zsh
set -u

# Fixture-only correction: xterm bracketed paste followed by a separate Enter.
# Product is unchanged from 710a72060. All processes/data are isolated; zero vendor turns.
task_root="${0:A:h:h:h:h}"
run_dir="$(mktemp -d /private/tmp/t157-outside-04.XXXXXX)" || exit 2
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
run_probe stop-input-baseline workbench/tests/test_t157_stop_input_e2e.py --revision ef99842b35e17c4cd69e1e58d5afca0689bf88b1
run_probe stop-input-bad-caller workbench/tests/test_t157_stop_input_e2e.py --mutant submit-never-active

python3 - "$run_dir" <<'PY'
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
checks = []
for name in ['stop-input-positive', 'stop-input-baseline', 'stop-input-bad-caller']:
    path = root / (name + '.json')
    if not path.is_file():
        checks.append(dict(name=name, passed=False, reason='summary absent'))
        continue
    report = json.loads(path.read_text(encoding='utf-8'))
    observed = {item['name']: item['passed'] for item in report.get('checks', [])}
    if name == 'stop-input-positive':
        passed = report.get('status') == 'PASS' and all(observed.get(key) is True for key in [
            'original_stop_submit_accepted', 'native_cli_received_original_input',
            'input_intersects_original_stop_batch', 'input_bytes_unchanged',
            'human_intervention_bound_original_attempt', 'submit_bound_original_native_turn'])
    else:
        timeline = report.get('observed', {}).get('timeline', [])
        refused = any(event['type'] == 'relay_rejected' and
                      event['data'].get('result', {}).get('error') == 'worker_not_active' for event in timeline)
        passed = (report.get('status') == 'INCOMPLETE' and refused and
                  observed.get('original_stop_submit_accepted') is False and
                  observed.get('input_intersects_original_stop_batch') is True and
                  observed.get('input_bytes_unchanged') is True)
    passed = passed and not report.get('errors')
    checks.append(dict(name=name, passed=passed, status=report.get('status'), summary=str(path), errors=report.get('errors')))
result = dict(status='PASS' if all(c['passed'] for c in checks) else 'INCOMPLETE', checks=checks,
              scope='corrected Stop-input fixture checkpoint; unchanged product, other scenarios in OUTSIDE-03', vendor_model_turns=0)
with (root / 'RESULT.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
PY
