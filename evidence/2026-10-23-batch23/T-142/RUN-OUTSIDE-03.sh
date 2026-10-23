#!/bin/zsh
set -u
cd "${0:A:h}/../../.." || exit 2
root=$PWD
out=$(mktemp -d "$root/evidence/2026-10-23-batch23/T-142/outside-03-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX") || exit 2
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
python3 - "$out" <<'PY'
import json
from pathlib import Path
import sys
out = Path(sys.argv[1])
reports = {}
exits = {}
for name in ('green', 'red', 'mutant'):
    path = out / f'{name}.json'
    reports[name] = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'status': 'INCOMPLETE', 'error': '没有生成 summary'}
    exits[name] = int((out / f'{name}.exit.txt').read_text(encoding='utf-8').strip())
checks = {'green': reports['green'].get('status') == 'PASS' and exits['green'] == 0}
for name, report in reports.items():
    permissions = report.get('observed', {}).get('fixture_permissions', {})
    checks[name + '_default_permissions'] = permissions == {'defaultMode': 'default', 'allow': ['Bash(a2a request:*)', 'Bash(a2a call:*)']}
    checks[name + '_cleanup_confirmed'] = not report.get('cleanup_errors')
red, mutant = reports['red'], reports['mutant']
checks['red_expected_refusal'] = (exits['red'] == 1 and 'real_claude_requested_and_ui_approved' in red.get('checks', []) and
                                red.get('error', '').startswith('AssertionError: main_opened:') and
                                red.get('observed', {}).get('main', {}).get('error') == 'role_command_not_scoped')
checks['mutant_caught'] = (exits['mutant'] == 1 and 'real_claude_requested_and_ui_approved' in mutant.get('checks', []) and
                         all(name + '_ui_pwd' in mutant.get('checks', []) for name in ('main', 'extra', 'child')) and
                         mutant.get('error', '').startswith('AssertionError: sibling_refused:') and
                         mutant.get('observed', {}).get('sibling', {}).get('ok') is True)
result = dict(status='PASS' if all(checks.values()) else 'INCOMPLETE', scope='T-142 完整 UI 链路、起点红态与 cwd-unchecked 变异重跑',
              checks=checks, exits=exits,
              errors={name: r.get('error') for name, r in reports.items() if r.get('error')},
              prior_regressions='outside-20261023T153047Z-v7ZOxk：T-124、T-139/T-143 通过，T-091 与起点一致；执行主控本轮裁定 T-121 交 T-147，不算 T-142。此次只改 T-142 测试夹具，未重复已通过的产品回归。',
              raw_artifacts='各 summary.fixture 指向保留的 /private/tmp 原始现场；截图不提交，由执行主控归档。')
(out / 'RESULT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if result['status'] == 'PASS' else 1)
PY
