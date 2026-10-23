#!/bin/zsh
set -u
cd "${0:A:h}/../../.." || exit 1
export PYTHONDONTWRITEBYTECODE=1
python3 - <<'PY'
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

root = Path.cwd()
out = root / 'evidence/2026-10-23-batch23/T-140' / ('outside-02-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
out.mkdir()
candidate = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
# Reproduce the defective CDP driver against the same product sources. The helper module still
# resolves ROOT from workbench/tests, while this preserved driver lives only in the fresh run.
bad_revision = 'bffd3ca125a4605580b1d52d754b93e471ea40e5'
bad_driver = out / 'before-fix-driver.py'
bad_driver.write_bytes(subprocess.check_output(['git', 'show', bad_revision + ':workbench/tests/test_t140_extra_dirs_e2e.py']))
env = dict(os.environ, PYTHONPATH=str(root / 'workbench/tests') + os.pathsep + os.environ.get('PYTHONPATH', ''))
cases = [
    ('driver-green', 'workbench/tests/test_t140_scripted_plan.py', []),
    ('before-fix-driver-red', str(bad_driver), []),
    ('red', 'workbench/tests/test_t140_extra_dirs_e2e.py', ['--revision', 'ebbae7bd0']),
    ('green', 'workbench/tests/test_t140_extra_dirs_e2e.py', []),
    ('mutant-shell', 'workbench/tests/test_t140_extra_dirs_e2e.py', ['--mutant', 'claude-shell-deny-extra']),
    ('mutant-remove', 'workbench/tests/test_t140_extra_dirs_e2e.py', ['--mutant', 'removed-directory-retained']),
    ('regression-t131', 'workbench/tests/test_t131_parallel_workers_e2e.py', []),
    ('regression-t137', 'workbench/tests/test_t137_reflect_e2e.py', []),
    ('regression-t127', 'workbench/tests/test_t127_codex_home_e2e.py', []),
]
results = []
for name, test, extra in cases:
    summary = out / (name + '.json')
    command = ['python3', test, '--summary', str(summary), *extra]
    with (out / (name + '.log')).open('x', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    data = json.loads(summary.read_text(encoding='utf-8')) if summary.exists() else {}
    error = data.get('error', '')
    accepted = result.returncode == 0 and data.get('status') == 'PASS'
    details = {}
    if name == 'before-fix-driver-red':
        # The old driver submitted X twice. A permission leak after a saved [] is a different defect.
        events = []
        if data.get('fixture'):
            db = Path(data['fixture']) / 'state/state.sqlite3'
            if db.exists():
                with sqlite3.connect(f'file:{db}?mode=ro', uri=True) as connection:
                    events = [json.loads(row[0])['extra_directories'] for row in connection.execute(
                        "SELECT data FROM orchestration_events WHERE type='project_settings_saved' ORDER BY seq")]
        details = dict(settings_events=events, driver_revision=bad_revision)
        x = str(Path(data.get('external_fixture', 'missing')) / 'X')
        accepted = result.returncode != 0 and error.startswith('AssertionError: T-RC_shell_boundary:') and events == [[x], [x]]
    elif name == 'red':
        accepted = result.returncode != 0 and error.startswith('AssertionError: 超时：Edit Project menu')
    elif name == 'mutant-shell':
        observed = data.get('observed', {})
        launches = observed.get('launches', [])
        worker = next((row for row in launches if row.get('task') == 'demo+T-C' and row.get('role') == 'worker'), {})
        settings = json.loads(worker['argv'][15]) if worker else {}
        x = str(Path(data.get('external_fixture', 'missing')) / 'X')
        deny = settings.get('sandbox', {}).get('filesystem', {}).get('denyWrite', [])
        details = dict(result=observed.get('T-C', {}).get('result'), worker_shell_deny=deny,
                       reviewers_started=sum(row.get('role') == 'reviewer' for row in launches))
        accepted = (result.returncode != 0 and error.startswith('AssertionError: T-C_shell_boundary:') and
                    details['result'] == dict(x=False, y=False) and x in deny and details['reviewers_started'] == 0)
    elif name == 'mutant-remove':
        observed = data.get('observed', {})
        events = observed.get('settings_after_remove', [])
        x = str(Path(data.get('external_fixture', 'missing')) / 'X')
        details = dict(result=observed.get('T-RC', {}).get('result'), settings_events=events)
        accepted = (result.returncode != 0 and error.startswith('AssertionError: T-RC_shell_boundary:') and
                    details['result'] == dict(x=True, y=False) and [e['extra_directories'] for e in events] == [[x], []])
    if name.startswith('mutant-'):
        # No mutation-sensitivity claim without a successful unmodified run on this candidate.
        accepted = accepted and any(row['name'] == 'green' and row['status'] == 'PASS' for row in results)
    row = dict(name=name, command=command, exit_code=result.returncode, status='PASS' if accepted else 'INCOMPLETE',
               summary=str(summary), error=error[:500], details=details)
    results.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
    if data.get('fixture'):
        for screenshot in (Path(data['fixture']) / 'out').glob('*.png'):
            shutil.copy2(screenshot, out / (name + '-' + screenshot.name))
result = dict(status='PASS' if all(row['status'] == 'PASS' for row in results) else 'INCOMPLETE',
              candidate_revision=candidate, old_driver_revision=bad_revision, results=results)
(out / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(str(out / 'run.json'), flush=True)
sys.exit(0 if result['status'] == 'PASS' else 1)
PY
