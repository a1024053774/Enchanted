#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='50efd2f0f6f27fffa89d8609c5d952906cd1125a'
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35';assert os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not any(k in os.environ for k in ['GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE']) and not git('diff','--cached','--name-only')
paths=json.loads((base/'09b-driver-allowlist.json').read_bytes())
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
    if row:
        name=row[3:];assert any(name==p or name.startswith(p+'/') for p in paths),('Unowned work; no mutation',name)
assert all(Path(p).exists() for p in paths)
for p in ['09b-driver-source-freeze.json','09b-driver-commit-run','09b-executable-materials-01']:assert not (base/p).exists(),('Existing output; preserve it, no retry',p)
green=json.loads((base/'09b-driver-green-05/results.json').read_bytes());assert green['status']=='PASS' and green['oracle']['role_budgets']=={'ideation':[4,6],'executor':[6,11]}
role_red=json.loads((base/'09b-role-file-red/results.json').read_bytes());assert role_red['status']=='INCOMPLETE' and role_red['observed']=='accepted'
role_green=json.loads((base/'09b-role-file-green-rejection/results.json').read_bytes());assert role_green['status']=='PASS' and role_green['observed']=='controller_launch_config_required'
final_green=json.loads((base/'09b-driver-green-role-only-final/results.json').read_bytes());assert final_green['status']=='PASS'
assert json.loads((base/'09b-driver-red-role-only-final/results.json').read_bytes())['status']=='INCOMPLETE'
assert json.loads((base/'09b-driver-red-feedback-05/results.json').read_bytes())['status']=='INCOMPLETE'
for mutant in ['seq-reset','identity','duplicate-esc']:
    assert json.loads((base/f'09b-driver-mutant-{mutant}-05/results.json').read_bytes())['status']=='INCOMPLETE'
subprocess.run(['git','diff','--check'],check=True);subprocess.run(['git','add','--',*paths],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','test(T-078): bind 09B double-role driver to registered dispatches'],check=True)
revision=git('rev-parse','HEAD')
with (base/'09b-driver-source-freeze.json').open('x',encoding='utf-8') as f:
    json.dump({'revision':revision,'parent_revision':before,'budgets':{'ideation':[4,6],'executor':[6,11],'combined_messages':17},'real_model_turns':0,'launch':'NO_GO'},f,indent=2);f.write('\n')
run=base/'09b-driver-commit-run';run.mkdir();argv=[sys.executable,'-B',str((base/'prepare-09b-executable.py').resolve())]
with (run/'stdout.bin').open('xb') as stdout,(run/'stderr.bin').open('xb') as stderr:r=subprocess.run(argv,stdout=stdout,stderr=stderr)
with (run/'command.json').open('x',encoding='utf-8') as f:json.dump({'argv':argv,'revision':revision,'exit_code':r.returncode,'scope':'Static launch packet only; no process'},f,indent=2);f.write('\n')
assert r.returncode==0,'Preserve failed packet/commit; no retry'
packet=base/'09b-executable-materials-01';facts=json.loads((packet/'static-check.json').read_bytes());assert facts['status']=='PASS' and facts['launch_status']=='NO_GO' and facts['revision']==revision
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:f.write('\n## 09B driver 首提交与可执行 launch 包静态冻结\n\ndriver／oracle source `'+revision+'` 已冻结；纯夹具 red→green→反例通过，I=4/6、E=6/11、合计17、模型0。新 [可执行包](09b-executable-materials-01/static-check.json) 静态 PASS，双角色新 root/manifest/独立目录、target card oracle_paths、空审批与 source tar 均读回；`launch_status=NO_GO`，无目标 claim、attempt/fence、CLI/API/目标启动。\n')
second=[str(packet),str(run),str(base/'09b-driver-source-freeze.json'),str(base/'RESULTS.md')];subprocess.run(['git','add','--',*second],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze 09B executable launch review packet'],check=True);assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'packet':str(packet),'launch':'NO_GO','next':'Review static package; no process started'},ensure_ascii=False))
PY
