#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -B - <<'PY'
import json,os,subprocess
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='3d5225a9689bf04bf839967dc059e0a8e7adc300'
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not any(k in os.environ for k in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'))
assert not git('diff','--cached','--name-only'),'Existing staged work; no mutation'
assert not git('diff','--','workbench/src','workbench/app','workbench/hooks','workbench/bin','acceptance','scripts')
freeze=base/'post-rebase-2b-source-freeze.json';assert not freeze.exists()
paths=['workbench/tests/test_daemon_gates_e2e.py','workbench/tests/test_t078_cards_host_bootstrap.py',
       str(base/'RESULTS.md'),str(base/'POST-REBASE-2.md'),str(base/'POST-REBASE-2B.md'),
       str(base/'post-rebase-2-stage.py'),str(base/'commit-post-rebase-2b.sh'),
       str(base/'post-rebase-2-source-freeze.json'),str(base/'post-rebase-2-outside-01'),
       str(base/'post-rebase-2b-diagnosis'),str(base/'post-rebase-2b-bootstrap-red'),
       str(base/'post-rebase-2b-bootstrap-green'),str(base/'post-rebase-2b-static.json'),
       str(base/'post-rebase-2b-project-map-status.txt'),str(base/'post-rebase-2b-main-notification.json'),
       '.project-map/inbox/20261014T200545Z-worker:t078-postrebase2b-report-001.md']
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
    if row:
        name=row[3:]
        assert any(name==p or name.startswith(p+'/') for p in paths),('Unowned work; preserve it',name)
for p in paths:assert Path(p).exists(),('Missing handoff path',p)
subprocess.run(['git','diff','--check'],check=True)
subprocess.run(['git','add','--',*paths],check=True)
subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','test(T-078): bind card host bootstrap credentials and resume regression'],check=True)
revision=git('rev-parse','HEAD')
with freeze.open('x',encoding='utf-8') as stream:
    json.dump({'revision':revision,'parent_revision':before,'reused_inbox_revision':before,
               'rebase_target':'490de67d05a08ccf8a453a78694a106288579b47',
               'stage_script':str(base/'post-rebase-2-stage.py'),'resume_from':'cards',
               'real_model_turns':0,'vendor_cli_starts':0},stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print(json.dumps({'status':'PASS','revision':revision,'source_freeze':str(freeze),'next':'separate regression continuation; no native launch'},ensure_ascii=False))
subprocess.run(['git','status','--short'],check=True)
PY
