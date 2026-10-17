#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path('evidence/2026-10-11-batch13/T-078')
BEFORE = '887d85cdb37889941f1ed26836d4c94b277ab5fa'
check_only = sys.argv[1:] == ['--check-only']
assert not sys.argv[1:] or check_only, 'only --check-only is supported'
allow = json.loads((BASE / 'pending-delivery-allowlist.json').read_bytes())
ownership = BASE / 'pending-ownership-preflight-01.json'
freeze = BASE / 'pending-source-freeze-01.json'
generated = {str(ownership), str(freeze)}
optional = {str(BASE / name) for name in ['09b-pending-runtime-01', '09b-pending-timeout-cleanup-01', '09b-pending-timeout-cleanup-02',
                                        '09b-a13-cleanup-01', '09b-a13-cleanup-01-dry-run']}


def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()


def owner(path):
    return next((entry for entry in allow if path == entry or path.startswith(entry + '/')), None)


assert git('rev-parse', 'HEAD') == BEFORE, ('head_changed', git('rev-parse', 'HEAD'))
assert not git('diff', '--cached', '--name-only'), 'staging must be empty'
assert not freeze.exists(), 'source freeze already exists; do not retry a partial commit'
rows = []
for item in subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode().split('\0'):
    if item:
        path = item[3:]
        assert not item[:2].startswith('R'), 'renamed work requires explicit handoff'
        rows.append({'path': path, 'allowlist_entry': owner(path)})
unowned = [row['path'] for row in rows if row['allowlist_entry'] is None]
assert not unowned, ('Unowned work; no mutation', unowned)
missing = [entry for entry in allow if not Path(entry).exists() and entry not in generated | optional]
assert not missing, ('missing planned add path', missing)
# Both commit phases use this same list. In particular, the ownership report
# is a generated first-commit path, not merely an entry that gets excluded.
first_paths = sorted({entry for entry in allow if Path(entry).exists()} | {str(ownership)})
second_paths = [str(freeze)]
assert all(Path(path).exists() or path in generated for path in first_paths + second_paths)
simulated_remaining = [row['path'] for row in rows
                       if not any(row['path'] == path or row['path'].startswith(path + '/') for path in first_paths)]
assert simulated_remaining == [], ('not in actual git add plan', simulated_remaining)

checks = json.loads((BASE / '09b-pending-local-03/result.json').read_bytes())
assert checks['status'] == 'PASS' and len(checks['checks']) == 11
assert all(row['status'] == 'PASS' and row['exit_code'] == 0 for row in checks['checks'])
runtime = BASE / '09b-pending-runtime-01/result.json'
if runtime.exists():
    runtime_result = json.loads(runtime.read_bytes())
    assert runtime_result['status'] == 'PASS', 'runtime failed; preserve evidence and stop before commit'
    assert runtime_result['checks'][0]['assertions'] == 14 and runtime_result['checks'][0]['exit_code'] == 0
socket_checks = json.loads((BASE / '09b-pending-socket-cleanup-green-02/result.json').read_bytes())
assert socket_checks['status'] == 'PASS' and len(socket_checks['checks']) == 3 and socket_checks['signals_sent'] == []
pending = json.loads((BASE / '09b-pending-local-03/pending/result.json').read_bytes())
assert pending['status'] == 'PASS' and len(pending['checks']) == 13 and pending['delivery']['state'] == 'delivered'
observed = json.loads((BASE / '09b-pending-local-03/pending/offline-observed.json').read_bytes())
assert observed['observed']['delivery'] == 'pending' and observed['observed']['relay_ok'] is True
assert observed['observed']['feedback_count'] == 0
timeline = json.loads((BASE / '09b-pending-local-03/pending/offline-delivery.json').read_bytes())
assert timeline['created_at_unchanged'] is True
assert len([event for event in timeline['events'] if event['type'] == 'relay_feedback_registered']) == 1
red = json.loads((BASE / '09b-pending-chain-red-03/red-verdict.json').read_bytes())
assert red['status'] == 'PASS' and red['exit_code'] == 1 and red['observed']['relay_error'] == 'wake_undelivered'
scene = json.loads((BASE / '09b-a13-i1-redacted-01/summary.json').read_bytes())
assert scene['status'] == 'PASS' and scene['request_count'] == 13 and scene['response_count'] == 2
assert scene['raw_logs_copied'] is False and scene['credentials_copied'] is False
assert (BASE / '20261016T012505Z-ideation-answer-001.md').is_file()
assert '主控 #299：pending 投递实现与延后 I2' in (BASE / 'RESULTS.md').read_text(encoding='utf-8')
for filename in ['cleanup-09b-a13.py', 'cleanup-pending-timeout.py', 'redact-a13-i1-scene.py',
                 'run-pending-checks.py', 'capture-a13-pending-red.py']:
    path = BASE / filename
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
for path in ['workbench/src/daemon.ts', 'workbench/src/relay.ts', 'workbench/src/gates/core.ts',
             'workbench/tests/test_t078_a13_rehearsal.ts']:
    subprocess.run(['node', '--check', path], check=True)
for name in ['09B-PENDING-OUTSIDE-COMMANDS.txt', '09B-A13-CLEANUP-COMMANDS.txt']:
    for line in (BASE / name).read_text(encoding='utf-8').splitlines():
        if line.startswith('python3 -B '):
            script = line.split()[2]
            assert Path(script).is_file(), ('command path missing', script)
subprocess.run(['git', 'diff', '--check'], check=True)
report = {'status': 'PASS', 'mode': 'check-only' if check_only else 'commit', 'head': BEFORE,
          'checked_paths': len(rows), 'unowned': unowned, 'simulated_final_status': simulated_remaining,
          'first_add_paths': first_paths, 'second_add_paths': second_paths,
          'local_checks': '11 groups PASS; pending chain 13 assertions',
          'runtime_regression': 'PASS' if runtime.exists() else 'pending controller execution', 'independent_review': 'pending controller review',
          'launch': 'NO_GO'}
if check_only:
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0)
assert os.environ.get('A2A_ROLE') == 'worker', 'run with the original worker launch identity'
assert os.environ.get('A2A_TASK') in ['T-078', 'T-078-1'] and os.environ.get('CODEX_THREAD_ID')
ownership.write_text(json.dumps({**report, 'entries': rows}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
subprocess.run(['git', 'add', '--', *first_paths], check=True)
subprocess.run(['git', 'commit', '-m', 'fix(T-078): retain offline inbox delivery and defer original feedback'], check=True)
source_revision = git('rev-parse', 'HEAD')
assert not git('status', '--porcelain'), 'first add plan omitted a file; stop before freeze'
freeze.write_text(json.dumps({'status': 'PASS', 'revision': source_revision, 'base_revision': BEFORE,
                             'task': 'T-078', 'scope': 'pending delivery and deferred I2; no A14 launch',
                             'checks': str(BASE / '09b-pending-local-03/result.json'),
                             'outside_commands': str(BASE / '09B-PENDING-OUTSIDE-COMMANDS.txt'),
                             'independent_review': 'INCOMPLETE; new read-only review arranged by controller',
                             'launch': 'NO_GO'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
subprocess.run(['git', 'add', '--', *second_paths], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze pending delivery review candidate'], check=True)
assert not git('status', '--porcelain'), 'final status must be empty'
print(json.dumps({'status': 'PASS', 'source_revision': source_revision, 'evidence_revision': git('rev-parse', 'HEAD'),
                  'launch': 'NO_GO', 'final_status': []}, ensure_ascii=False))
PY
