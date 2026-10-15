#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

base = Path('evidence/2026-10-11-batch13/T-078')
before = '201602809'
check_only = '--check-only' in sys.argv[1:]
allow = json.loads((base / '09b-a11-b1-allowlist.json').read_bytes())
future = {str(base / '09b-a11-b1-ownership-preflight-01.json')}


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

stage = base / '09b-a11-stage-a-01'
readiness = json.loads((stage / 'readiness.json').read_bytes())
stage_result = json.loads((stage / 'result.json').read_bytes())
assert readiness['status'] == 'READY_FOR_APPROVAL' and stage_result['status'] == 'READY_FOR_APPROVAL'
assert readiness['stage'] == 'A' and readiness['roles_started'] == []
assert stage_result['root'] == readiness['root'] and stage_result['task'] == readiness['task']
assert readiness['daemon']['pid'] == 24112
assert readiness['target_process']['shell_pid'] == 24203 and readiness['target_process']['leader'] == 24205
assert {item['role']: item['pid'] for item in readiness['api_processes']} == {'ideation': 24109, 'executor': 24110}

stage_approval = json.loads((base / 'a11-stage-a-approval-01.json').read_bytes())
assert stage_approval['approved_by'] == 'executor' and '主控 #282' in stage_approval['approval_ref']
assert stage_approval['source_revision'] == readiness['source_revision']

p1 = base / '09b-a11-b1-ideation-p1-01'
p1_input = json.loads((p1 / 'input.json').read_bytes())
p1_approval = json.loads((p1 / 'approval.json').read_bytes())
p1_generation = json.loads((p1 / 'generation.json').read_bytes())
assert p1_input['root'] == readiness['root'] and p1_input['task'] == readiness['task']
assert p1_input['preset'] == 'ideation' and p1_input['api_url'] == 'http://127.0.0.1:0'
assert p1_approval['input'] == p1_input and p1_generation['status'] == 'PASS'
assert p1_generation['real_cli_starts'] == 0 and p1_generation['api_starts'] == 0

b1 = json.loads((base / 'stage-b-a11-ideation-approval-01.json').read_bytes())
assert b1['approved_by'] == 'executor' and '主控 #282' in b1['approval_ref']
assert b1['source_revision'] == readiness['source_revision'] and b1['role'] == 'ideation' and b1['phase'] == 'B1'
assert b1['binding'] == readiness['target_binding'] and b1['p1_materials'] == str(p1.resolve())
assert b1['allow_role_cli_spawn'] is True and b1['stop_after'] == 'first-screen'
assert b1['screen_approvals'] and b1['tool_approval'] == {'key': 'Enter', 'purpose': 'one-time-tool-approval', 'selected_label': '1. Yes', 'one_time': True}
assert b1['p1_args'] == ['--reuse-stage-a', '--reuse-api-root', str(Path(readiness['root']) / 'roles/ideation'), '--reuse-readiness-file', str((stage / 'readiness.json').resolve())]

dry = json.loads((base / '09b-a11-b1-ideation-dry-run-01/result.json').read_bytes())
assert dry['status'] == 'READY_FOR_ROLE' and dry['spawned'] is False and dry['p1_spawned'] is False and dry['cli_spawned'] is False
commands = (base / '09B-A11-B1-COMMANDS.txt').read_text(encoding='utf-8')
assert '--dry-run' in commands and commands.count('run-09b-stage-b.py') == 2
assert '09b-a11-b1-ideation-01' in commands and '09b-a11-stage-a-01' in commands
subprocess.run(['git', 'diff', '--check'], check=True)

ownership = base / '09b-a11-b1-ownership-preflight-01.json'
if check_only:
    print(json.dumps({'status': 'PASS', 'mode': 'check-only', 'head': git('rev-parse', 'HEAD'),
                      'cached_paths': 0, 'checked_paths': len(rows), 'unowned': unowned,
                      'stage_a': str(stage), 'p1_materials': str(p1),
                      'dry_run': str(base / '09b-a11-b1-ideation-dry-run-01')}, ensure_ascii=False))
    raise SystemExit(0)

ownership.write_text(json.dumps({'status': 'PASS', 'checked_paths': len(rows),
                                 'unowned': unowned, 'entries': rows}, ensure_ascii=False,
                                indent=2) + '\n', encoding='utf-8')
with (base / 'RESULTS.md').open('a', encoding='utf-8') as fh:
    fh.write('\n## A-11 Stage A and ideation B1 preparation\n\n'
             'A-11 Stage A 已由主控 #282 批准并实跑 PASS：readiness READY_FOR_APPROVAL，root `/private/tmp/t078-2-09b-run-j0ogu5t7`，daemon 24112，target shell/leader 24203/24205，ideation/executor protocol API 24109/24110；本提交保留签字 approval 与全部原始输出。\n'
             'ideation B1 P1 材料从本次 readiness 生成，复用 `/private/tmp/t078-2-09b-run-j0ogu5t7/roles/ideation` 的既有 API；签字批准绑定实际 attempt/session/fence/thread/workspace，逐屏 onboarding 与一次性工具许可模板完整。dry-run PASS、spawned=false、cli_spawned=false；本轮未启动角色 CLI、未发送输入。\n')
first = [
    base / '09b-a11-b1-allowlist.json', base / '09b-a11-stage-a-01',
    base / 'a11-stage-a-approval-01.json', base / '09B-A11-B1-COMMANDS.txt',
    base / '09b-a11-b1-ideation-p1-01', base / 'stage-b-a11-ideation-approval-01.json',
    base / '09b-a11-b1-ideation-dry-run-01', base / '09b-a11-b1-ownership-preflight-01.json',
    base / 'commit-09b-a11-b1.sh', base / 'RESULTS.md',
]
subprocess.run(['git', 'add', '--', *map(str, first)], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze A11 Stage A and ideation B1 materials'], check=True)
assert not git('status', '--porcelain')
print(json.dumps({'status': 'PASS', 'commit': git('rev-parse', 'HEAD'), 'launch': 'NO_GO'}, ensure_ascii=False))
PY
