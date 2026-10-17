#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json, subprocess, sys
from pathlib import Path

base = Path('evidence/2026-10-11-batch13/T-078')
before = 'e5de6ec4'
check_only = '--check-only' in sys.argv[1:]
allow = json.loads((base / '09b-a06-b1-allowlist.json').read_bytes())
future = {str(base / '09b-a06-b1-ownership-preflight-01.json')}

def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()

assert git('rev-parse', 'HEAD').startswith(before) and not git('diff', '--cached', '--name-only')
rows = []
bad = []
for item in subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode().split('\0'):
    if not item:
        continue
    path = item[3:]
    owner = next((entry for entry in allow if path == entry or path.startswith(entry + '/')), None)
    rows.append({'path': path, 'status': 'PASS' if owner else 'INCOMPLETE', 'allowlist_entry': owner})
    if owner is None:
        bad.append(path)
assert not bad, ('Unowned work; no mutation', bad)
first = [entry for entry in allow if entry not in future]
missing = [entry for entry in first if not Path(entry).exists()]
assert not missing, ('Allowlist path missing before git add', missing)

stage_result = json.loads((base / '09b-a06-stage-a-02/result.json').read_bytes())
readiness = json.loads((base / '09b-a06-stage-a-02/readiness.json').read_bytes())
assert stage_result['status'] == 'READY_FOR_APPROVAL' and readiness['status'] == 'READY_FOR_APPROVAL'
assert stage_result['root'] == readiness['root'] and readiness['roles_started'] == []
assert len(readiness['api_processes']) == 2 and all(item['ready']['stage'] == 'A' for item in readiness['api_processes'])
assert (base / '09B-A06-STAGE-A-COMMAND-02.txt').is_file()
stage_approval = json.loads((base / 'a06-stage-a-approval-02.json').read_bytes())
assert stage_approval['approved_by'] == 'executor' and stage_approval['source_revision'] == readiness['source_revision']

p1 = base / '09b-a06-b1-ideation-p1-01'
p1_preflight = json.loads((base / '09b-a06-b1-p1-preflight-01/results.json').read_bytes())
assert p1_preflight['status'] == 'PASS' and p1_preflight['real_cli_starts'] == 0
p1_input = json.loads((p1 / 'input.json').read_bytes())
assert p1_input['root'] == readiness['root'] and p1_input['task'] == readiness['task']
assert p1_input['preset'] == 'ideation' and p1_input['api_url'] == 'http://127.0.0.1:0'
assert json.loads((p1 / 'generation.json').read_bytes())['real_cli_starts'] == 0

b1 = json.loads((base / 'stage-b-a06-ideation-approval-01.json').read_bytes())
assert b1['approved_by'] is None and b1['approval_ref'] is None
assert b1['stage'] == 'B' and b1['phase'] == 'B1' and b1['p1_phase'] == 'launch'
assert b1['source_revision'] == readiness['source_revision'] and b1['p1_materials'] == str(p1.resolve())
assert '--reuse-stage-a' in b1['p1_args'] and '--reuse-api-root' in b1['p1_args'] and '--reuse-readiness-file' in b1['p1_args']
assert b1['readiness_reference'] == str((base / '09b-a06-stage-a-02/readiness.json').resolve())

blank_red = json.loads((base / '09b-a06-b1-approval-dry-run-01/result.json').read_bytes())
assert blank_red['status'] == 'INCOMPLETE' and blank_red['spawned'] is False and blank_red['cli_spawned'] is False
subprocess.run(['git', 'diff', '--check'], check=True)
ownership = base / '09b-a06-b1-ownership-preflight-01.json'
if check_only:
    existing = json.loads(ownership.read_bytes())
    assert existing['status'] == 'PASS' and existing['unowned'] == []
    print(json.dumps({'status': 'PASS', 'mode': 'check-only', 'head': git('rev-parse', 'HEAD'),
                      'cached_paths': 0, 'checked_paths': len(rows), 'unowned': bad}))
    raise SystemExit(0)

ownership.write_text(json.dumps({'status': 'PASS', 'checked_paths': len(rows), 'unowned': bad,
                                'entries': rows}, ensure_ascii=False, indent=2) + '\n')
assert ownership.exists()
results = base / 'RESULTS.md'
with results.open('a', encoding='utf-8') as fh:
    fh.write('\n## A-06 B1 ideation P1 materials\n\n'
             'A-06 stage A readiness 已保留并绑定新 root；生成 ideation P1 材料，input 使用 `http://127.0.0.1:0` 模板，实际 API root/readiness 由 B1 approval 的 reuse 参数绑定。只读前置校验 PASS，未启动 CLI/API/daemon/target。空签字 approval 的 dry-run 被 runner 在 spawn 前拒绝，结果保留为 INCOMPLETE、spawned=false、cli_spawned=false。\n')
subprocess.run(['git', 'add', '--', *first, str(ownership)], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): prepare A06 ideation B1 launch materials'], check=True)
assert not git('status', '--porcelain')
print(json.dumps({'status': 'PASS', 'commit': git('rev-parse', 'HEAD'), 'launch': 'NO_GO'}))
PY
