#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -B - <<'PY'
import json,os,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='ee2f7c1b7c19153ffec07abd2eb30574863d8c77'
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not any(k in os.environ for k in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'))
assert not git('diff','--cached','--name-only'),'Existing staged work; preserve it'
assert not git('diff','--','workbench/src','workbench/app','workbench/hooks','workbench/bin','acceptance','scripts')
for name in ['slice1-code-freeze.json','slice1-preparation-run','p1-materials-slice1-red']:
    assert not (base/name).exists(),('Preserve existing preparation; no retry',name)
paths=['workbench/tests/regenerate_t078_p1.py','workbench/tests/run_t078_p1.py',
       'workbench/tests/run_t078_slice1.py','workbench/tests/t078_slice1_protocol.py',
       'workbench/tests/test_t078_slice1_protocol.py','workbench/tests/t078_fake_inbox_tool.py',
       'workbench/tests/electron_driver.mjs','workbench/tests/test_t078_slice1_permission_key.mjs',
       str(base/'RESULTS.md'),str(base/'SLICE-1-RED.md'),str(base/'FAILURE-MODES-SLICE1.md'),
       str(base/'ISSUE-SLICE1-RELAY-FILE-OWNERSHIP.md'),str(base/'prepare-slice1-red.py'),
       str(base/'ISSUE-SLICE1-PERMISSION-ENTER.md'),
       str(base/'commit-and-prepare-slice1.sh'),str(base/'slice1-static.json'),
       str(base/'slice1-project-map-status.txt'),str(base/'slice1-main-notification.json'),
       str(base/'post-rebase-2-outside-02'),str(base/'post-rebase-2b-source-freeze.json'),
       str(base/'slice1-protocol-green'),str(base/'slice1-protocol-mutant-budget'),
       str(base/'slice1-protocol-mutant-budget-02'),str(base/'slice1-readback-regression.json'),
       str(base/'slice1-permission-key-red'),str(base/'slice1-permission-key-green'),str(base/'slice1-window-binding-regression'),
       '.project-map/inbox/20261014T203118Z-worker:t078-slice1-issue-001.md',
       '.project-map/inbox/20261014T203805Z-worker:t078-slice1-issue-001.md',
       '.project-map/inbox/20261014T203805Z-worker:t078-slice1-report-001.md']
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
    if row:
        name=row[3:]
        assert any(name==p or name.startswith(p+'/') for p in paths),('Unowned work; no mutation',name)
for p in paths:assert Path(p).exists(),('Missing handoff path',p)
subprocess.run(['git','diff','--check'],check=True)
subprocess.run(['git','add','--',*paths],check=True)
subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','test(T-078): prepare one-controller native inbox red slice'],check=True)
revision=git('rev-parse','HEAD')
with (base/'slice1-code-freeze.json').open('x',encoding='utf-8') as stream:
    json.dump({'revision':revision,'parent_revision':before,'product_source_revision':before,
               'root_submit_budget':1,'messages_request_budget':2,'tool_call_budget':1,
               'real_model_turns':0,'real_cli_starts':0},stream,ensure_ascii=False,indent=2);stream.write('\n')
run=base/'slice1-preparation-run';run.mkdir()
argv=[sys.executable,'-B',str((base/'prepare-slice1-red.py').resolve())]
with (run/'stdout.bin').open('xb') as stdout,(run/'stderr.bin').open('xb') as stderr:
    result=subprocess.run(argv,stdout=stdout,stderr=stderr)
with (run/'command.json').open('x',encoding='utf-8') as stream:
    json.dump({'argv':argv,'revision':revision,'exit_code':result.returncode,
               'scope':'Static generation only; no services or native CLI'},stream,indent=2);stream.write('\n')
assert result.returncode==0,'Preparation failed; preserve the commit and new fixture; no retry'
packet=base/'p1-materials-slice1-red'
facts=json.loads((packet/'static-check.json').read_bytes());assert facts['status']=='PASS' and facts['revision']==revision
subprocess.run(['git','add','--',str(packet),str(run),str(base/'slice1-code-freeze.json')],check=True)
subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','docs(T-078): freeze single-controller red launch packet'],check=True)
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),
                  'materials':str(packet),'root':facts['root'],'launch':facts['launch'],
                  'next':'Read this new launch packet and approve launch separately; no process started'},ensure_ascii=False))
subprocess.run(['git','status','--short'],check=True)
PY
