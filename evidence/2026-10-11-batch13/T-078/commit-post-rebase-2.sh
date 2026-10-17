#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -B - <<'PY'
import json, os, subprocess
from pathlib import Path
root=Path.cwd();base=Path('evidence/2026-10-11-batch13/T-078')
before='bf9bb9d75def72c7c74ef6389bcb82647a29a697'
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not any(k in os.environ for k in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'))
assert not git('diff','--cached','--name-only'),'Existing staged work; no mutation'
freeze=base/'post-rebase-2-source-freeze.json';assert not freeze.exists()
paths=['workbench/tests/test_t078_input_entry.py','workbench/tests/test_t078_inbox_entry.py',
       'workbench/tests/run_t078_p1.py','workbench/tests/test_t078_fixture_cards.py',
       str(base/'RESULTS.md'),str(base/'POST-REBASE-2.md'),str(base/'post-rebase-2-stage.py'),
       str(base/'commit-post-rebase-2.sh'),str(base/'post-rebase-2-static.json'),
       str(base/'post-rebase-2-main-notification.json'),
       str(base/'post-rebase-2-project-map-status.txt'),str(base/'rebase-main-2/execution'),
       '.project-map/inbox/20261014T195342Z-worker:t078-postrebase2-report-001.md']
for name in ['card-red','card-green','score-schemas','t083','inbox-domain','pane-runtime',
             'controller-window','claude-epochs','window-binding']:
    paths.append(str(base/('post-rebase-2-'+name)))
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
    if row:
        name=row[3:]
        assert any(name==p or name.startswith(p+'/') for p in paths),('Unowned work; preserve it',name)
for p in paths:assert Path(p).exists(),('Missing handoff path',p)
subprocess.run(['git','diff','--check'],check=True)
subprocess.run(['git','add','--',*paths],check=True)
subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','test(T-078): migrate fixture oracles and preserve post-rebase checks'],check=True)
revision=git('rev-parse','HEAD')
with freeze.open('x',encoding='utf-8') as stream:
    json.dump({'revision':revision,'parent_revision':before,
               'rebase_target':'490de67d05a08ccf8a453a78694a106288579b47',
               'stage_script':str(base/'post-rebase-2-stage.py'),
               'real_model_turns':0,'vendor_cli_starts':0},stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print(json.dumps({'status':'PASS','revision':revision,'source_freeze':str(freeze),'next':'separate zero-model regression stage; no launch'},ensure_ascii=False))
subprocess.run(['git','status','--short'],check=True)
PY
