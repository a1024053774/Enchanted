#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import ast
import json
import subprocess
import sys
from pathlib import Path

base = Path('evidence/2026-10-11-batch13/T-078')
before = '9a38d968'
check_only = '--check-only' in sys.argv[1:]
allow = json.loads((base / '09b-a12-allowlist.json').read_bytes())
future = {str(base / '09b-a12-ownership-preflight-01.json')}


def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()


assert git('rev-parse', 'HEAD').startswith(before), git('rev-parse', 'HEAD')
assert not git('diff', '--cached', '--name-only')
rows = []
unowned = []
for item in subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode().split('\0'):
    if not item:
        continue
    path = item[3:]
    owner = next((entry for entry in allow if path == entry or path.startswith(entry + '/')), None)
    rows.append({'path': path, 'status': 'PASS' if owner else 'INCOMPLETE', 'allowlist_entry': owner})
    if owner is None:
        unowned.append(path)
assert not unowned, ('Unowned work; no mutation', unowned)
missing = [entry for entry in allow if entry not in future and not Path(entry).exists()]
assert not missing, ('Allowlist path missing before git add', missing)

cleanup = base / 'cleanup-09b-a11.py'
ast.parse(cleanup.read_text(encoding='utf-8'), filename=str(cleanup))
command = (base / '09B-A11-CLEANUP-COMMAND.txt').read_text(encoding='utf-8')
for required in ['主控 #286 T-078 A-11 owner-bound cleanup', '--root /private/tmp/t078-2-09b-run-j0ogu5t7',
                 '--api-ideation-pid 24109', '--api-executor-pid 24110', '--daemon-pid 24112',
                 '--target-shell-pid 24203', '--target-leader-pid 24205', '--claude-shell-pid 29924',
                 '--claude-cli-pid 29925', '09b-a11-b1-ideation-01/process-manifest.json']:
    assert required in command, required
assert command.count('cleanup-09b-a11.py') == 2 and command.count('--dry-run') == 1
static = json.loads((base / '09b-executable-materials-12/static-check.json').read_bytes())
assert static['status'] == 'PASS' and static['protocol'] is True and static['revision'] == git('rev-parse', 'HEAD')
approval = json.loads((base / 'a12-stage-a-approval-01.json').read_bytes())
assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['source_revision'] == static['revision']
stage_command = (base / '09B-A12-STAGE-A-COMMAND.txt').read_text(encoding='utf-8')
assert '09b-executable-materials-12' in stage_command and '--protocol' in stage_command and 'a12-stage-a-approval-01.json' in stage_command

# Simulate the final tree after adding every allowlisted path.  This catches
# the recurring failure where a new evidence file is omitted from the commit.
simulated_remaining = [row['path'] for row in rows if row['allowlist_entry'] is None]
assert simulated_remaining == []
assert all(Path(entry).exists() or entry in future for entry in allow)
subprocess.run(['git', 'diff', '--check'], check=True)
ownership = base / '09b-a12-ownership-preflight-01.json'
if check_only:
    print(json.dumps({'status': 'PASS', 'mode': 'check-only', 'head': git('rev-parse', 'HEAD'),
                      'cached_paths': 0, 'checked_paths': len(rows), 'unowned': unowned,
                      'simulated_final_status': [], 'materials': str(base / '09b-executable-materials-12'),
                      'launch': 'NO_GO'}, ensure_ascii=False))
    raise SystemExit(0)

ownership.write_text(json.dumps({'status': 'PASS', 'checked_paths': len(rows), 'unowned': unowned,
                                 'entries': rows, 'simulated_final_status': []}, ensure_ascii=False, indent=2) + '\n')
with (base / 'RESULTS.md').open('a', encoding='utf-8') as fh:
    fh.write('\n## A-11 owner-bound cleanup and A-12 rebuild packet\n\n'
             'A-11 cleanup is prepared with root `/private/tmp/t078-2-09b-run-j0ogu5t7`, API 24109/24110, daemon 24112, target 24203/24205 and Claude 29924/29925; dry-run and formal commands are both frozen, with external archive/readback before deletion. A-11现场未在本轮操作。\n'
             'A-12 materials-12 was generated from the current source revision with protocol=true, fresh root proposal and blank Stage-A approval. The prior A-11 I1 schema failure and 12/6 Messages overrun remain evidence; A-12 launch is NO_GO.\n')
paths = [Path(entry) for entry in allow if entry not in future] + [ownership, base / 'RESULTS.md']
subprocess.run(['git', 'add', '--', *map(str, paths)], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): prepare A12 packet and A11 cleanup'], check=True)
assert git('status', '--porcelain') == ''
print(json.dumps({'status': 'PASS', 'commit': git('rev-parse', 'HEAD'), 'simulated_final_status': [], 'launch': 'NO_GO'}, ensure_ascii=False))
PY
