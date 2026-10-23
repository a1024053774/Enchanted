#!/bin/zsh
set -u
task_root=${0:A:h:h:h:h}
cd "$task_root" || exit 1
task_output=$(mktemp -d "$task_root/evidence/2026-10-23-batch23/T-148/outside01-XXXXXXXX") || exit 1
export PYTHONPYCACHEPREFIX=/private/tmp/t148-pycache
python3 - "$task_root" "$task_output" <<'PY'
import json
from pathlib import Path
import subprocess
import sys

root, out = map(Path, sys.argv[1:])
manifest = dict(status='INCOMPLETE', task='T-148-1', attempt='a1', commands=[],
                candidate=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                fixture_policy='原始夹具保留在 /private/tmp；由执行主控按 T-088 归档。')
(out / 'candidate.diff').write_text(subprocess.check_output(['git', 'diff', 'HEAD'], cwd=root, text=True), encoding='utf-8')
cases = [
    ('t146-green-and-mutants', ['node', 'workbench/tests/test_t146_reviewer_hooks.mjs', str(out / 't146-green-and-mutants.json'), '.'], None),
    ('t145-green', ['python3', 'workbench/tests/test_t145_mouse_reports_e2e.py'], None),
    ('t145-red-reverted', ['python3', 'evidence/2026-10-23-batch23/T-148/t145_reverted_fixture.py'], 'mouse_focus_do_not_create_records'),
    ('t145-mutant-record', ['python3', 'workbench/tests/test_t145_mouse_reports_e2e.py', '--mutant', 'record-reports'], 'mouse_focus_do_not_create_records'),
    ('t145-mutant-drop', ['python3', 'workbench/tests/test_t145_mouse_reports_e2e.py', '--mutant', 'drop-reports'], '三次移动均到 PTY'),
    ('t127-green', ['python3', 'workbench/tests/test_t127_codex_home_e2e.py'], None),
    ('t141-green', ['python3', 'workbench/tests/test_t141_loosened_limits_e2e.py'], None),
    ('t141-launch', ['node', 'workbench/tests/test_t141_launch_contract.mjs', str(out / 't141-launch.json'), '.'], None),
    ('t141-reviewer', ['node', 'workbench/tests/test_t141_reviewer_contract.mjs', str(out / 't141-reviewer.json'), '.'], None),
    ('t141-startup', ['node', 'workbench/tests/test_t141_startup_signal.mjs', str(out / 't141-startup.json'), '.'], None),
]
for label, command, expected_error in cases:
    summary = out / (label + '.json')
    if command[0] == 'python3':
        command += ['--summary', str(summary)]
    row = dict(label=label, argv=command, summary=str(summary), passed=False)
    manifest['commands'].append(row)
    with (out / (label + '.stdout.txt')).open('x', encoding='utf-8') as stdout, \
         (out / (label + '.stderr.txt')).open('x', encoding='utf-8') as stderr:
        result = subprocess.run(command, cwd=root, stdout=stdout, stderr=stderr)
    row['exit_code'] = result.returncode
    if summary.exists():
        data = json.loads(summary.read_text(encoding='utf-8'))
        row.update(status=data.get('status'), error=data.get('error'), fixture=data.get('fixture'))
        if expected_error:
            required = ['receiver_native_identity_bound']
            if label != 't145-mutant-drop':
                required += ['motion_bytes_match_coordinates_exactly', 'cli_receives_only_complete_reports']
            row['passed'] = (result.returncode != 0 and expected_error in data.get('error', '') and
                             all(name in data.get('checks', []) for name in required) and
                             data.get('cleanup_complete') is True)
        else:
            row['passed'] = result.returncode == 0 and data.get('status') == 'PASS'
    else:
        row['error'] = '未生成摘要；不能作为红态证据'
    with (out / 'MANIFEST.json').open('w', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(label, row['passed'], flush=True)
manifest['status'] = 'PASS' if all(row['passed'] for row in manifest['commands']) else 'INCOMPLETE'
with (out / 'MANIFEST.json').open('w', encoding='utf-8') as stream:
    json.dump(manifest, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(out)
raise SystemExit(0 if manifest['status'] == 'PASS' else 1)
PY
