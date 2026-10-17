#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
base = Path('evidence/2026-10-11-batch13/T-078')
before = '2f34ae8eb8666b9fda4feada4118c05f6f18d25d'

def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()

assert git('rev-parse', 'HEAD') == before and git('branch', '--show-current') == 'exec/t078'
assert os.environ.get('CODEX_THREAD_ID') == '01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK') == 'T-078-1' and os.environ.get('A2A_ROLE') == 'worker'
assert not git('diff', '--cached', '--name-only')
allow = json.loads((base / '09b-run-05-allowlist.json').read_bytes())
future = {
    'evidence/2026-10-11-batch13/T-078/09b-run-05-source-freeze.json',
    'evidence/2026-10-11-batch13/T-078/09b-run-05-commit',
    'evidence/2026-10-11-batch13/T-078/09b-executable-materials-05',
    'evidence/2026-10-11-batch13/T-078/09b-run-05-ownership-preflight-01.json',
}
for row in subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode().split('\0'):
    if row:
        name = row[3:]
        assert any(name == p or name.startswith(p + '/') for p in allow), ('Unowned work; no mutation', name)
for p in allow:
    if p not in future:
        assert Path(p).exists(), ('Missing required pre-commit evidence', p)
old = json.loads((base / '09b-stage-a-04/result.json').read_bytes())
assert old['status'] == 'INCOMPLETE' and old['spawned'] is True and 'AssertionError' in old.get('error', '')
diagnosis = json.loads((base / '09b-stage-a-04-readback-01/result.json').read_bytes())
assert diagnosis['status'] == 'PASS' and diagnosis['leader'] is None and diagnosis['pane_processes_only_zsh'] is True
assert diagnosis['pane_text_contains_create_sessions_file_exists'] is True and diagnosis['receiver_started_observed'] is False
receiver = json.loads((base / '09b-receiver-launch-green-10/result.json').read_bytes())
assert receiver['status'] == 'PASS' and receiver['ready_marker'] and receiver['sessions_created'] and receiver['started_file']
dry = json.loads((base / '09b-stage-a-04-cleanup-dry-run/result.json').read_bytes())
assert dry['status'] == 'PASS' and dry['dry_run'] is True and dry['signals_sent'] == [] and dry['root_removed'] is False
clean = json.loads((base / '09b-stage-a-04-cleanup/result.json').read_bytes())
assert clean['status'] == 'PASS' and clean['dry_run'] is False and clean['byte_readback'] == 'PASS' and clean['root_removed'] is True
assert clean['signals_sent'] == [{'pid': 68081, 'signal': 'SIGTERM'}, {'pid': 68082, 'signal': 'SIGTERM'}]
assert all(float(v) <= 2.0 for v in clean.get('api_exit_seconds', {}).values())
subprocess.run(['git', 'diff', '--check'], check=True)
# Record a final ownership readback before staging it, then verify the added
# readback itself is covered by the same allowlist.
rows=[]; unowned=[]
for row in subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode().split('\0'):
    if row:
        name=row[3:]; owner=next((p for p in allow if name == p or name.startswith(p + '/')), None)
        rows.append({'path':name,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner})
        if owner is None: unowned.append(name)
assert not unowned
ownership = base / '09b-run-05-ownership-preflight-01.json'
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':unowned,'entries':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
first = [p for p in allow if p not in future]
subprocess.run(['git', 'add', '--', *first, str(ownership)], check=True)
subprocess.run(['git', 'diff', '--cached', '--stat'], check=True)
subprocess.run(['git', 'commit', '-m', 'fix(T-078): avoid precreating deterministic receiver sessions'], check=True)
revision = git('rev-parse', 'HEAD')
with (base / '09b-run-05-source-freeze.json').open('x', encoding='utf-8') as f:
    json.dump({'revision':revision,'parent_revision':before,'old_red_preserved':True,
               'diagnosis':'stage-a-04 pane showed create sessions: File exists; receiver absent',
               'fix':'runner leaves isolated CODEX_HOME/sessions absent for receiver mkdir',
               'receiver_stop':'fake API SystemExit path already in parent source',
               'launch':'NO_GO'},f,ensure_ascii=False,indent=2); f.write('\n')
run = base / '09b-run-05-commit'; run.mkdir()
prepare = [sys.executable,'-B',str((base/'prepare-09b-executable.py').resolve()),'--label','09b-executable-materials-05']
with (run/'prepare.stdout.bin').open('xb') as stdout,(run/'prepare.stderr.bin').open('xb') as stderr:
    result=subprocess.run(prepare,stdout=stdout,stderr=stderr)
(run/'prepare.command.json').write_text(json.dumps({'argv':prepare,'revision':revision,'exit_code':result.returncode},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert result.returncode == 0
facts=json.loads((base/'09b-executable-materials-05/static-check.json').read_bytes())
assert facts['status']=='PASS' and facts['launch_status']=='NO_GO' and facts['revision']==revision
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:
    f.write('\n## 阶段 A-04 receiver 修复与 materials-05 冻结\n\n真实 Stage-A-04 红态已读回：dispatch/claim 回执完整，但 pane 只有 zsh，屏幕 `create sessions: File exists`，launch-config receiver 路径存在而未启动；根因是 runner 预创建 CODEX_HOME/sessions。已删除该预创建并以空 HOME receiver 进程回归 PASS。A-04 cleanup dry-run/正式 PASS，两个假 API 各一次 SIGTERM 均在两秒内退出，归档逐成员读回后 root 删除。materials-05 静态 PASS，launch 继续 NO_GO；未启动新的 Stage A、供应商 CLI 或模型。\n')
second=[str(base/'09b-executable-materials-05'),str(run),str(base/'09b-run-05-source-freeze.json'),str(base/'RESULTS.md')]
subprocess.run(['git','add','--',*second],check=True); subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','docs(T-078): freeze Stage-A-04 receiver fix and materials 05'],check=True)
assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'packet':str(base/'09b-executable-materials-05'),'launch':'NO_GO'},ensure_ascii=False))
PY
