#!/bin/zsh
set -u

# 真实 Electron 绿态、反事实和相关回归。只用隔离夹具，不调用供应商模型。
cd "${0:A:h}/../../.." || exit 2
python3 - <<'PY'
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import uuid

root = Path.cwd()
evidence = root / 'evidence/2026-10-23-batch24/T-162'
tag = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
prefix = evidence / ('verify-' + tag)
candidate = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', 'workbench'], check=True)
report = dict(status='INCOMPLETE', candidate=candidate, tests=[], vendor_model_turns=0)

def run(label, argv, bad_check=None):
    summary = Path(str(prefix) + '-' + label + '.json')
    command = [*argv, '--summary', str(summary)]
    with Path(str(prefix) + '-' + label + '.log').open('x', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
    data = json.loads(summary.read_text(encoding='utf-8')) if summary.is_file() else {}
    if bad_check:
        checks = {row['name']: row['status'] for row in data.get('checks', [])}
        passed = result.returncode == 1 and data.get('status') == 'NO_GO' and checks.get(bad_check) == 'FAIL' and not data.get('error') and not data.get('cleanup_error')
    else:
        passed = result.returncode == 0 and data.get('status') == 'PASS' and not data.get('error') and not data.get('cleanup_error')
    item = dict(label=label, argv=command, exit_code=result.returncode, status='PASS' if passed else 'INCOMPLETE',
                summary=str(summary.relative_to(root)), expected_bad_check=bad_check, fixture=data.get('fixture'))
    report['tests'].append(item)
    if data.get('fixture'):
        out = Path(data['fixture']) / 'out'
        if out.is_dir():
            for image in out.glob('*.png'):
                destination = Path(str(prefix) + '-' + label + '-' + image.name)
                with destination.open('xb') as stream:
                    stream.write(image.read_bytes())
    print(json.dumps(item, ensure_ascii=False), flush=True)
    return summary

unit = ['node', 'workbench/tests/test_t162_metrics_sources.mjs']
run('metrics-fixture', [*unit, '--revision', candidate])
for mutant, check in [('unknown-as-zero', 'no_source_is_unknown'), ('zero-as-unknown', 'verified_recorded_zero_is_distinct'),
                       ('source-dropped', 'claude_replay_sources'), ('range-ignored', 'old_session_with_in_range_turns_is_included')]:
    run('metrics-mutant-' + mutant, [*unit, '--mutant', mutant], check)

e2e = ['python3', 'workbench/tests/test_t162_role_records_metrics_e2e.py']
run('electron-green', [*e2e, '--revision', candidate])
for mutant, check in [('unknown-as-zero', 'controller_without_native_count_is_unknown'),
                       ('decision-unrecorded', 'two_explicit_decisions_are_user_inputs'),
                       ('non-atomic-decision', 'decision_and_input_roll_back_together')]:
    run('electron-mutant-' + mutant, [*e2e, '--mutant', mutant], check)

# 既有真实入口回归：角色申请权限/生命周期；记录与四个指标；原生终端主控提示与层级。
# 两项 T-133 测试运行真实 Claude CLI，但 Messages 接口在本机脚本化，不消耗供应商回合。
run('regression-t121', ['python3', 'workbench/tests/test_t121_role_request_e2e.py', '--revision', candidate])
run('regression-t133-t134', ['python3', 'workbench/tests/test_t133_t134_records_metrics_e2e.py', '--revision', candidate])
controller_summary = run('regression-native-controller', ['python3', 'workbench/tests/test_t133_t107_terminal_controller_e2e.py', '--revision', candidate])
run('native-controller-audit', ['node', 'workbench/tests/test_t162_native_controller_audit.mjs', '--controller-summary', str(controller_summary)])
run('native-controller-parent', ['node', 'workbench/tests/test_t162_native_controller_audit.mjs', '--controller-summary', str(controller_summary),
                                '--revision', 'c01742804'], 'native_controller_turns_are_explicitly_uncovered:ideation')

unchanged = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == candidate
unchanged = unchanged and subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', 'workbench']).returncode == 0
report['candidate_unchanged'] = unchanged
report['status'] = 'PASS' if unchanged and all(row['status'] == 'PASS' for row in report['tests']) else 'INCOMPLETE'
summary = Path(str(prefix) + '-SUMMARY.json')
with summary.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(report['status'] + '\nSUMMARY=' + str(summary.relative_to(root)), flush=True)
raise SystemExit(0 if report['status'] == 'PASS' else 1)
PY
