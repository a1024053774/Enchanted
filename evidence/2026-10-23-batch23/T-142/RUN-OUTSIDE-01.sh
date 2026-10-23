#!/bin/zsh
set -u
cd "${0:A:h}/../../.." || exit 2
root=$PWD
out=$(mktemp -d "$root/evidence/2026-10-23-batch23/T-142/outside-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX") || exit 2
export PYTHONPYCACHEPREFIX=/private/tmp/t142-outside-pycache
print -r -- "证据目录：$out"
git rev-parse HEAD > "$out/candidate.txt"
node --version > "$out/node-version.txt"
claude --version > "$out/claude-version.txt" 2>&1
run_case() {
  local label=$1
  shift
  print -r -- "运行 $label"
  print -r -- "${(q)@}" > "$out/$label.command.txt"
  "$@" > "$out/$label.log" 2>&1
  local code=$?
  print -r -- "$code" > "$out/$label.exit.txt"
  print -r -- "$label exit=$code"
}
run_case green python3 workbench/tests/test_t142_terminal_open_e2e.py --summary "$out/green.json"
run_case red python3 workbench/tests/test_t142_terminal_open_e2e.py --revision c113e71203bd37e151241b6ce44bd4bf773e356f --summary "$out/red.json"
run_case mutant python3 workbench/tests/test_t142_terminal_open_e2e.py --mutant cwd-unchecked --summary "$out/mutant.json"
run_case t121 python3 workbench/tests/test_t121_role_request_e2e.py --summary "$out/t121.json"
run_case t124 python3 workbench/tests/test_t124_controller_e2e.py --gui --summary "$out/t124.json"
run_case t139-t143 python3 workbench/tests/test_t139_t143_views_perf_e2e.py --summary "$out/t139-t143.json"
run_case t091 node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs "$out/t091.json"
python3 - "$out" <<'PY'
import json
from pathlib import Path
import sys
out = Path(sys.argv[1])
base = out.parent
reports = {}
for name in ('green', 'red', 'mutant', 't121', 't124', 't139-t143', 't091'):
    path = out / f'{name}.json'
    reports[name] = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'status': 'INCOMPLETE', 'error': '没有生成 summary'}
checks = {name: reports[name].get('status') == 'PASS' for name in ('green', 't121', 't124', 't139-t143')}
checks['red_expected_refusal'] = ('main_opened' in reports['red'].get('error', '') and
                                  reports['red'].get('observed', {}).get('main', {}).get('error') == 'role_command_not_scoped')
checks['mutant_caught'] = 'sibling_refused' in reports['mutant'].get('error', '')
baseline = json.loads((base / 'baseline-t091-01.json').read_text(encoding='utf-8'))
checks['t091_no_worse_than_base'] = all(reports['t091'].get(k) == baseline.get(k) for k in ('status', 'checks', 'error', 'known_bad_result', 'single_pane_counterexample', 'sidebar_known_bad'))
result = dict(status='PASS' if all(checks.values()) else 'INCOMPLETE', checks=checks,
              errors={name: r.get('error') for name, r in reports.items() if r.get('error')},
              raw_artifacts='各 summary 的 fixture 指向保留的 /private/tmp 原始现场；截图不提交，由执行主控归档。')
(out / 'RESULT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if result['status'] == 'PASS' else 1)
PY
