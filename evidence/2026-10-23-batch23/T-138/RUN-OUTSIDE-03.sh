#!/bin/zsh
# T-138-1 / a1：修前红态、候选绿态、还原修复的变异和输入回归。
set -u
if (( $# != 1 )); then
  print -u2 -- '用法：zsh RUN-OUTSIDE-03.sh <本次交付的完整提交号>'
  exit 2
fi
cd /Users/luckye/Documents/Code/a2a-wt-t138 || exit 2
OUT="evidence/2026-10-23-batch23/T-138/outside-03-$(date +%Y%m%d-%H%M%S)-$$"
mkdir "$OUT" || exit 2
python3 - "$OUT" "$1" <<'PY'
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path.cwd()
out = root / sys.argv[1]
base = 'b99f4869bbe087946017716a5a8479c0cb47e6c8'
candidate = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
expected = subprocess.check_output(['git', 'rev-parse', '--verify', sys.argv[2] + '^{commit}'], text=True).strip()
assert candidate == expected, f'HEAD {candidate} 不是待验收提交 {expected}'
subprocess.run(['git', 'diff', '--quiet', expected, '--', 'workbench'], check=True)
rows = []


def run(name, command):
    with (out / (name + '.log')).open('x', encoding='utf-8') as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    row = dict(name=name, argv=command, exit=result.returncode)
    rows.append(row)
    print(name, 'exit=', result.returncode, flush=True)


ime = ['python3', 'workbench/tests/test_t138_ime_e2e.py']
run('red', [*ime, '--revision', base, '--summary', str(out / 'red.json')])
run('green', [*ime, '--revision', candidate, '--summary', str(out / 'green.json')])
run('mutant', [*ime, '--mutant', 'retain-input', '--summary', str(out / 'mutant.json')])
run('t139-t143', ['python3', 'workbench/tests/test_t139_t143_views_perf_e2e.py', '--summary', str(out / 't139-t143.json')])

sys.path.insert(0, str(root / 'workbench/tests'))
from scripted_claude import source_tree
baseline_fixture = Path(tempfile.mkdtemp(prefix='t138-t091-', dir='/private/tmp'))
source = source_tree(baseline_fixture, base)
node = ['node', '--experimental-vm-modules', 'workbench/tests/test_t091_pane_ipc.mjs']
run('t091-baseline', [*node, str(out / 't091-baseline.json'), '--source', str(source)])
run('t091-candidate', [*node, str(out / 't091-candidate.json')])


def report(name):
    path = out / (name + '.json')
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def ime_bad(name):
    value = report(name)
    return (value.get('status') == 'NO_GO' and value.get('defect_reproduced') is True
            and not value.get('cleanup_errors') and all(c['passed'] for c in value.get('checks', []))
            and any(c['screen_reader'] and c['name'].startswith('middle') and c['actual'] == '怪了'
                    and c['expected'] == '打出' for c in value.get('cases', [])))


def signature(value):
    return {key: value.get(key) for key in ('status', 'checks', 'error', 'known_bad_result',
                                           'single_pane_counterexample', 'sidebar_known_bad')}

checks = dict(red_rejects_fault=ime_bad('red'), green=report('green').get('status') == 'PASS',
              mutant_rejects_fault=ime_bad('mutant'),
              t139_t143=report('t139-t143').get('status') == 'PASS',
              t091_unchanged=bool(report('t091-baseline')) and bool(report('t091-candidate'))
                  and signature(report('t091-baseline')) == signature(report('t091-candidate')))
checks['candidate_unchanged'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == expected and \
    subprocess.run(['git', 'diff', '--quiet', expected, '--', 'workbench']).returncode == 0
result = dict(status='PASS' if all(checks.values()) else 'INCOMPLETE', candidate=candidate, expected=expected, base=base,
              checks=checks, commands=rows, baseline_fixture=str(baseline_fixture),
              excluded_checks=[dict(name='t145', status='NOT_RUN', owner='T-148',
                                    reason='主控确认：T-141 后旧 receiver 不发 native 就绪包；本轮不计入 T-138 结果')])
with (out / 'run-summary.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
print('请回传 run-summary.json 路径。截图不提交，夹具由主控归档。')
raise SystemExit(0 if result['status'] == 'PASS' else 1)
PY
