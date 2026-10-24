#!/bin/zsh
set -u
# 同一冻结候选：T-161 绿态/四个变异，T-157 原输入与新回合恢复，T-159 分屏。
# 不调用供应商模型；T-157 使用真实 Claude CLI 加本地脚本化 Messages。
cd /Users/luckye/Documents/Code/a2a-wt-t161 || exit 2
run_dir=$(mktemp -d /private/tmp/t161-outside-05.XXXXXX) || exit 2
print -r -- "RUN_DIR=$run_dir"
git rev-parse HEAD > "$run_dir/candidate.txt"
run_probe() {
  local run_name="$1"
  shift
  python3 -B "$@" --summary "$run_dir/$run_name.json" > "$run_dir/$run_name.log" 2>&1
  local run_code=$?
  print -r -- "$run_name exit=$run_code summary=$run_dir/$run_name.json"
  print -r -- "$run_name=$run_code" >> "$run_dir/exits.txt"
}
run_probe green workbench/tests/test_t161_readonly_role_e2e.py
run_probe mutant-observation workbench/tests/test_t161_readonly_role_e2e.py --mutant readonly-observation
run_probe mutant-focus workbench/tests/test_t161_readonly_role_e2e.py --mutant readonly-focus
run_probe mutant-role workbench/tests/test_t161_readonly_role_e2e.py --mutant missing-role
run_probe mutant-input-error workbench/tests/test_t161_readonly_role_e2e.py --mutant suppress-input-errors
run_probe t157-stop-input workbench/tests/test_t157_stop_input_e2e.py
run_probe t157-recover workbench/tests/test_t157_stale_turn_e2e.py
run_probe t157-expired workbench/tests/test_t157_stale_turn_e2e.py --scenario expired
run_probe t159-split workbench/tests/test_t159_split_e2e.py

python3 - "$run_dir" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
exits = dict(line.split('=', 1) for line in (root / 'exits.txt').read_text().splitlines())
mutants = {
    'mutant-observation': {'reviewer_view_has_no_input_error', 'history_view_has_no_input_error'},
    'mutant-focus': {'reviewer_no_requested_input_focus', 'history_no_requested_input_focus'},
    'mutant-role': {'confirmed_executor_header_with_sidebar_hidden', 'renamed_controller_keeps_carrier_and_role'},
    'mutant-input-error': {'real_input_failure_still_visible'},
}
names = ['green', *mutants, 't157-stop-input', 't157-recover', 't157-expired', 't159-split']
checks = []
for name in names:
    path = root / (name + '.json')
    if not path.is_file():
        checks.append(dict(name=name, passed=False, reason='summary absent'))
        continue
    report = json.loads(path.read_text(encoding='utf-8'))
    errors = report.get('error') or report.get('errors') or report.get('cleanup_errors')
    failed = {c['name'] for c in report.get('checks', []) if c.get('passed') is False}
    if name in mutants:
        passed = (exits.get(name) == '1' and report.get('status') == 'INCOMPLETE' and not errors and
                  failed == mutants[name] and len(report.get('checks', [])) == 17 and report.get('model_calls') == 0)
    else:
        passed = exits.get(name) == '0' and report.get('status') == 'PASS' and not errors and not failed
        if name == 'green':
            passed = passed and len(report.get('checks', [])) == 17 and report.get('model_calls') == 0
    checks.append(dict(name=name, passed=bool(passed), status=report.get('status'), failed=sorted(failed),
                       errors=errors, summary=str(path), exit=exits.get(name)))
result = dict(status='PASS' if all(c['passed'] for c in checks) else 'INCOMPLETE',
              candidate=(root / 'candidate.txt').read_text().strip(), checks=checks,
              scope='候选行为检查；独立验收由执行主控安排', vendor_model_turns=0)
with (root / 'RESULT.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
PY
