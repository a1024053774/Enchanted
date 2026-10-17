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
before = 'f664724f'
label = '09b-executable-materials-11'
materials = base / label
check_only = '--check-only' in sys.argv[1:]
allow = json.loads((base / '09b-a11-allowlist.json').read_bytes())
future = {
    str(base / '09b-a11-ownership-preflight-01.json'),
    str(base / '09b-a11-source-freeze-01.json'),
    str(base / '09b-a11-commit-01'),
    str(materials),
}


def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()


assert git('rev-parse', 'HEAD').startswith(before), git('rev-parse', 'HEAD')
assert not git('diff', '--cached', '--name-only')
rows = []
unowned = []
for item in subprocess.check_output(
        ['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode().split('\0'):
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
for source in [base / 'cleanup-09b-a10.py']:
    ast.parse(source.read_text(encoding='utf-8'), filename=str(source))
cleanup_command = (base / '09B-A10-CLEANUP-COMMAND.txt').read_text(encoding='utf-8')
for required in [
    '--root /private/tmp/t078-2-09b-run-t1q79hur',
    '--api-ideation-pid 23489', '--api-executor-pid 23490', '--daemon-pid 23492',
    '--target-shell-pid 23602', '--target-leader-pid 23605',
    '--claude-shell-pid 23893', '--claude-cli-pid 23894', '--dry-run',
    '09b-a10-b1-ideation-p1-01/09b-a10-b1-ideation-01/process-manifest.json',
    '主控 #281 T-078 A-10 owner-bound cleanup (executor)',
]:
    assert required in cleanup_command, required
assert cleanup_command.count('cleanup-09b-a10.py') == 2 and cleanup_command.count('--dry-run') == 1
budget = (base / '09B-A11-PROTOCOL-BUDGET.md').read_text(encoding='utf-8')
for phase in ['I1', 'I2', 'I3', 'I4', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6']:
    assert f'| {phase} |' in budget, phase
assert 'ideation 4 roots/6 Messages' in budget and 'executor 6 roots/11 Messages' in budget
approval = json.loads((base / 'a11-stage-a-approval-01.json').read_bytes())
assert approval['approved_by'] is None and approval['approval_ref'] is None
assert approval['allow_role_cli_spawn'] is False and approval['final_protocol_api'] is True
subprocess.run(['git', 'diff', '--check'], check=True)

ownership = base / '09b-a11-ownership-preflight-01.json'
if check_only:
    print(json.dumps({'status': 'PASS', 'mode': 'check-only', 'head': git('rev-parse', 'HEAD'),
                      'cached_paths': 0, 'checked_paths': len(rows), 'unowned': unowned,
                      'prepare_label': label, 'prepare_label_prefix': True,
                      'material_target_exists': materials.exists()}, ensure_ascii=False))
    raise SystemExit(0)

ownership.write_text(json.dumps({'status': 'PASS', 'checked_paths': len(rows),
                                 'unowned': unowned, 'entries': rows}, ensure_ascii=False,
                                indent=2) + '\n', encoding='utf-8')
with (base / 'RESULTS.md').open('a', encoding='utf-8') as fh:
    fh.write('\n## A-10 cleanup handoff and A-11 protocol budget\n\n'
             'A-10 owner-bound cleanup 已执行 PASS：daemon_stop 关闭 Claude/目标，API 23489/23490 各一次 SIGTERM，七个进程退出；逐成员归档读回后 root 已删除。归档路径为 /Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a10-cleanup/fixture.tar.gz。批准引用为“主控 #281 T-078 A-10 owner-bound cleanup (executor)”。'
             'A-10 cleanup command 保留 dry-run 与正式两条实际命令。'
             'A-11 excludes the independent A-10 1-root/1-Message pipeline turn from the 09B budget. Frozen protocol budgets are ideation I1-I4 = 4 roots/6 Messages and executor E1-E6 = 6 roots/11 Messages. A-11 Stage A is prepared with protocol fake APIs and no role CLI spawn; launch remains NO_GO.\n')
first = [
    base / '09B-A10-CLEANUP-COMMAND.txt', base / '09B-A11-PROTOCOL-BUDGET.md',
    base / '09B-A11-STAGE-A-COMMAND.txt', base / 'a11-stage-a-approval-01.json',
    base / 'cleanup-09b-a10.py', base / '09b-a11-allowlist.json', base / 'commit-09b-a11.sh',
    base / '09b-a10-cleanup-01-dry-run', base / '09b-a10-cleanup-01',
    base / '09b-a11-ownership-preflight-01.json', base / 'RESULTS.md',
]
subprocess.run(['git', 'add', '--', *map(str, first)], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): prepare A11 protocol budget and cleanup'], check=True)
parent = git('rev-parse', 'HEAD')
prepare = [sys.executable, '-B', str((base / 'prepare-09b-executable.py').resolve()),
           '--label', label, '--protocol']
commit_dir = base / '09b-a11-commit-01'
commit_dir.mkdir()
with (commit_dir / 'prepare.stdout.bin').open('xb') as stdout, (commit_dir / 'prepare.stderr.bin').open('xb') as stderr:
    result = subprocess.run(prepare, stdout=stdout, stderr=stderr)
(commit_dir / 'prepare.command.json').write_text(json.dumps({'argv': prepare, 'exit_code': result.returncode}, ensure_ascii=False, indent=2) + '\n')
assert result.returncode == 0
static = json.loads((materials / 'static-check.json').read_bytes())
assert static['status'] == 'PASS' and static['protocol'] is True
assert static['protocol_tag'] == 'a07-registered-anthropic-v1' and static['revision'] == parent
source_freeze = {
    'status': 'PASS', 'revision': static['revision'], 'parent_revision': parent,
    'materials': f'prepare-09b-executable.py --label {label} --protocol',
    'protocol_tag': static['protocol_tag'], 'launch': 'NO_GO', 'real_process_starts': 0,
}
(base / '09b-a11-source-freeze-01.json').write_text(json.dumps(source_freeze, ensure_ascii=False, indent=2) + '\n')
approval['source_revision'] = static['revision']
approval['basis'] = 'A-11 materials-11 static PASS; sign only after review'
(base / 'a11-stage-a-approval-01.json').write_text(json.dumps(approval, ensure_ascii=False, indent=2) + '\n')
second = [materials, base / '09b-a11-source-freeze-01.json', base / 'a11-stage-a-approval-01.json', commit_dir]
subprocess.run(['git', 'add', '--', *map(str, second)], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze A11 executable materials'], check=True)
assert not git('status', '--porcelain')
print(json.dumps({'status': 'PASS', 'materials': str(materials), 'launch': 'NO_GO'}, ensure_ascii=False))
PY
