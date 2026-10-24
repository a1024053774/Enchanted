#!/bin/zsh
set -u

# 20 个计划内独立实例；本地脚本化 Messages，供应商模型回合 0。
# 坏实现/旧基线必须在指定行为断言失败；不把启动失败算成反证。
task_root="${0:A:h:h:h:h}"
run_dir="$(mktemp -d /private/tmp/t165-outside-03.XXXXXX)" || exit 2
print -r -- "RUN_DIR=$run_dir"
cd "$task_root" || exit 2
git rev-parse HEAD > "$run_dir/candidate.txt"
run_probe() {
  local run_name="$1"
  shift
  python3 -B "$@" --summary "$run_dir/$run_name.json" > "$run_dir/$run_name.log" 2>&1
  local run_code=$?
  print -r -- "$run_code" > "$run_dir/$run_name.exit"
  print -r -- "$run_name TEST_EXIT=$run_code SUMMARY=$run_dir/$run_name.json"
}

run_probe ordered-1 workbench/tests/test_t165_queued_stop_e2e.py
run_probe ordered-2 workbench/tests/test_t165_queued_stop_e2e.py
run_probe ordered-3 workbench/tests/test_t165_queued_stop_e2e.py
run_probe ordered-baseline workbench/tests/test_t165_queued_stop_e2e.py --revision f2756ea2030d8ce0bddf9980d3f36d1825201d3a
run_probe unrelated-stop workbench/tests/test_t165_queued_stop_e2e.py --scenario unrelated-stop
run_probe mutant-drop-stop workbench/tests/test_t165_queued_stop_e2e.py --mutant drop-early-stop

run_probe stop-input-1 workbench/tests/test_t157_stop_input_e2e.py
run_probe stop-input-2 workbench/tests/test_t157_stop_input_e2e.py
run_probe stop-input-3 workbench/tests/test_t157_stop_input_e2e.py
run_probe stop-input-baseline workbench/tests/test_t157_stop_input_e2e.py --revision ef99842b35e17c4cd69e1e58d5afca0689bf88b1
run_probe stop-input-bad-caller workbench/tests/test_t157_stop_input_e2e.py --mutant submit-never-active
run_probe stale-baseline workbench/tests/test_t157_stale_turn_e2e.py --revision c6725344ae81dce51656b2e44d1035a247df6604
run_probe stale-recover workbench/tests/test_t157_stale_turn_e2e.py
run_probe stale-expired workbench/tests/test_t157_stale_turn_e2e.py --scenario expired
run_probe mutant-old-stop workbench/tests/test_t157_stale_turn_e2e.py --mutant execute-old-stop
run_probe mutant-no-reason workbench/tests/test_t157_stale_turn_e2e.py --mutant hide-reason
run_probe mutant-no-recovery workbench/tests/test_t157_stale_turn_e2e.py --mutant hide-recovery
run_probe split-regression workbench/tests/test_t159_split_e2e.py
run_probe review-regression workbench/tests/test_t160_review_recovery_e2e.py
run_probe controller-regression workbench/tests/test_t133_t107_terminal_controller_e2e.py

python3 - "$run_dir" <<'PY'
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
names = ['ordered-1', 'ordered-2', 'ordered-3', 'ordered-baseline', 'unrelated-stop', 'mutant-drop-stop',
         'stop-input-1', 'stop-input-2', 'stop-input-3', 'stop-input-baseline', 'stop-input-bad-caller',
         'stale-baseline', 'stale-recover', 'stale-expired', 'mutant-old-stop', 'mutant-no-reason',
         'mutant-no-recovery', 'split-regression', 'review-regression', 'controller-regression']
stale_failures = {
    'stale-baseline': 'stale_submit_explicitly_refused',
    'mutant-old-stop': 'unmatched_stop_never_enters_execution',
    'mutant-no-reason': 'header_and_sidebar_explain_refusal',
    'mutant-no-recovery': 'recovery_action_exists_but_no_automatic_retry',
}
ordered_failures = {'positive_returns_idle_without_regular_recovery',
                    'intervention_turn_stop_restores_idle', 'queued_native_turn_bound_and_completed'}
checks = []
for name in names:
    path = root / (name + '.json')
    if not path.is_file():
        checks.append(dict(name=name, passed=False, reason='summary absent'))
        continue
    report = json.loads(path.read_text(encoding='utf-8'))
    code = int((root / (name + '.exit')).read_text().strip())
    observed = {c['name']: c['passed'] for c in report.get('checks', [])}
    failed = {key for key, value in observed.items() if not value}
    clean = not report.get('errors')
    if name in ('ordered-baseline', 'mutant-drop-stop'):
        pane = report.get('observed', {}).get('final_pane', {})
        passed = (code == 1 and report.get('status') == 'INCOMPLETE' and clean and
                  failed == ordered_failures and observed.get('real_stop_before_native_turn_registration') is True and
                  observed.get('original_stop_submit_accepted') is True and pane.get('state') == 'busy' and
                  pane.get('active') is not None)
        if name == 'ordered-baseline':
            passed = passed and report.get('red_reproduced') is True
    elif name in ('stop-input-baseline', 'stop-input-bad-caller'):
        refused = any(e['type'] == 'relay_rejected' and e['data'].get('result', {}).get('error') == 'worker_not_active'
                      for e in report.get('observed', {}).get('timeline', []))
        passed = (code == 1 and report.get('status') == 'INCOMPLETE' and clean and refused and
                  observed.get('original_stop_submit_accepted') is False and
                  observed.get('input_intersects_original_stop_batch') is True and
                  observed.get('input_bytes_unchanged') is True)
    elif name in stale_failures:
        passed = (code == 1 and report.get('status') == 'INCOMPLETE' and clean and
                  observed.get(stale_failures[name]) is False and
                  observed.get('actual_native_new_turn_after_original_stop') is True)
    else:
        passed = code == 0 and report.get('status') == 'PASS' and clean and not failed
        if name == 'unrelated-stop':
            passed = passed and all(observed.get(key) is True for key in (
                'unrelated_stop_remains_unmatched', 'unrelated_stop_never_completes_turn',
                'unrelated_stop_never_transfers_request', 'real_stop_before_native_turn_registration'))
    checks.append(dict(name=name, passed=bool(passed), exit=code, status=report.get('status'),
                       failed_checks=sorted(failed), errors=report.get('errors'), summary=str(path)))
result = dict(status='PASS' if all(c['passed'] for c in checks) else 'INCOMPLETE', checks=checks,
              scope='20-case T-165 candidate behavior checkpoint; independent acceptance remains separate', vendor_model_turns=0)
with (root / 'RESULT.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
PY
