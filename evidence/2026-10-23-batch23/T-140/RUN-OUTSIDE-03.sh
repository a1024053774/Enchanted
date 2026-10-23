#!/bin/zsh
set -u
cd "${0:A:h}/../../.." || exit 1
export PYTHONDONTWRITEBYTECODE=1
python3 - "$@" <<'PY'
# Failure modes: diagnostic/JSON/screenshot reads abort later cases; a failed child
# passes by matching an unrelated message; mutations pass without an ordinary green.
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

if sys.argv[1:] not in ([], ['--self-test']):
    raise SystemExit('Usage: RUN-OUTSIDE-03.sh [--self-test]')
self_test = sys.argv[1:] == ['--self-test']
root = Path.cwd()
out = root / 'evidence/2026-10-23-batch23/T-140' / ('outside-03-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
out.mkdir()
candidate = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
bad_revision = 'bffd3ca125a4605580b1d52d754b93e471ea40e5'
bad_driver = out / 'before-fix-driver.py'
before = subprocess.check_output(['git', 'show', bad_revision + ':workbench/tests/test_t140_extra_dirs_e2e.py'], text=True)
marker = "        report['error'] = f'{type(error).__name__}: {error}'\n        raise\n"
assert before.count(marker) == 1
# Preserve the old UI behavior. Only collect authoritative events before its finally
# stops the daemon, rather than reopening its closed WAL database in this runner.
capture = """        report['error'] = f'{type(error).__name__}: {error}'
        try:
            snapshot = fixture.request('orchestration_events')
            assert snapshot.get('ok'), snapshot
            report['settings_before_stop'] = [e['data']['extra_directories'] for e in snapshot['events'] if e['type'] == 'project_settings_saved']
        except (OSError, AssertionError, ValueError) as diagnostic_error:
            report['snapshot_error'] = f'{type(diagnostic_error).__name__}: {diagnostic_error}'
        raise
"""
bad_driver.write_text(before.replace(marker, capture), encoding='utf-8')
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
if self_test:
    child = out / 'runner-self-test.py'
    child.write_text("""import json,sys
from pathlib import Path
p=Path(sys.argv[sys.argv.index('--summary')+1]); mode=sys.argv[-1]
if mode=='missing': sys.exit(0)
if mode=='malformed': p.write_text('{'); sys.exit(0)
if mode=='nonobject': p.write_text('[]'); sys.exit(0)
p.write_text(json.dumps({'status':'PASS'} if mode=='valid' else {'status':'INCOMPLETE','error':'AssertionError: T-RC_shell_boundary: test'}))
sys.exit(0 if mode=='valid' else 1)
""", encoding='utf-8')
    cases = [('malformed-summary', str(child), ['malformed']), ('non-object-summary', str(child), ['nonobject']), ('missing-summary', str(child), ['missing']),
             ('before-fix-driver-red', str(child), ['diagnostic-missing']), ('sentinel', str(child), ['valid'])]
results = []
for name, test, extra in cases:
    summary = out / (name + '.json')
    command = ['python3', test, '--summary', str(summary), *extra]
    data, details, exit_code, case_error = {}, {}, None, None
    accepted = False
    try:
        with (out / (name + '.log')).open('x', encoding='utf-8') as log:
            result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
        exit_code = result.returncode
        decoded = json.loads(summary.read_text(encoding='utf-8'))
        if not isinstance(decoded, dict):
            raise ValueError('summary must be a JSON object')
        data = decoded
        error = data.get('error', '')
        accepted = exit_code == 0 and data.get('status') == 'PASS' and not data.get('snapshot_error')
        if name == 'before-fix-driver-red':
            # A missing diagnostic is a failed case, never a batch abort or a guessed red.
            events = data['settings_before_stop']
            details = dict(settings_events=events, driver_revision=bad_revision, snapshot_error=data.get('snapshot_error'))
            x = str(Path(data['external_fixture']) / 'X')
            accepted = exit_code != 0 and error.startswith('AssertionError: T-RC_shell_boundary:') and events == [[x], [x]]
        elif name == 'red':
            accepted = exit_code != 0 and error.startswith('AssertionError: 超时：Edit Project menu')
        elif name == 'mutant-shell':
            observed = data.get('observed', {})
            launches = observed.get('launches', [])
            worker = next((row for row in launches if row.get('task') == 'demo+T-C' and row.get('role') == 'worker'), {})
            settings = json.loads(worker['argv'][15]) if worker else {}
            x = str(Path(data['external_fixture']) / 'X')
            deny = settings.get('sandbox', {}).get('filesystem', {}).get('denyWrite', [])
            details = dict(result=observed.get('T-C', {}).get('result'), worker_shell_deny=deny,
                           reviewers_started=sum(row.get('role') == 'reviewer' for row in launches))
            accepted = (exit_code != 0 and error.startswith('AssertionError: T-C_shell_boundary:') and
                        details['result'] == dict(x=False, y=False) and x in deny and details['reviewers_started'] == 0)
        elif name == 'mutant-remove':
            observed = data.get('observed', {})
            events = observed.get('settings_after_remove', [])
            x = str(Path(data['external_fixture']) / 'X')
            details = dict(result=observed.get('T-RC', {}).get('result'), settings_events=events)
            accepted = (exit_code != 0 and error.startswith('AssertionError: T-RC_shell_boundary:') and
                        details['result'] == dict(x=True, y=False) and [e['extra_directories'] for e in events] == [[x], []])
        if name.startswith('mutant-'):
            accepted = accepted and any(row['name'] == 'green' and row['status'] == 'PASS' for row in results)
        if data.get('snapshot_error'):
            accepted = False
        if data.get('fixture'):
            for screenshot in (Path(data['fixture']) / 'out').glob('*.png'):
                shutil.copy2(screenshot, out / (name + '-' + screenshot.name))
    except Exception as error:
        # This is the batch isolation boundary. Record the complete failure class and
        # keep INCOMPLETE; no retry, alternative oracle or successful fallback is used.
        accepted = False
        case_error = f'{type(error).__name__}: {error}'
    row = dict(name=name, command=command, exit_code=exit_code, status='PASS' if accepted else 'INCOMPLETE',
               summary=str(summary), error=str(data.get('error', ''))[:500], case_error=case_error, details=details)
    results.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
    run = dict(status='PASS' if len(results) == len(cases) and all(row['status'] == 'PASS' for row in results) else 'INCOMPLETE',
               candidate_revision=candidate, old_driver_revision=bad_revision, results=results,
               scope='runner error containment only' if self_test else 'native acceptance')
    (out / 'run.json').write_text(json.dumps(run, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if self_test:
    ok = ([row['status'] for row in results] == ['INCOMPLETE', 'INCOMPLETE', 'INCOMPLETE', 'INCOMPLETE', 'PASS'] and
          all(row['case_error'] for row in results[:4]))
    run['self_test_status'] = 'PASS' if ok else 'INCOMPLETE'
    (out / 'run.json').write_text(json.dumps(run, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
else:
    ok = run['status'] == 'PASS'
print(str(out / 'run.json'), flush=True)
sys.exit(0 if ok else 1)
PY
