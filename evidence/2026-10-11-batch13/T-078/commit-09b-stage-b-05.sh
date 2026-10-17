#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json,os,subprocess,sys,shutil
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='92a61308f9467a0b90b7cbf0ca6534081502a5d1'
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35' and os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not git('diff','--cached','--name-only')
allow=json.loads((base/'09b-stage-b-05-allowlist.json').read_bytes());future={'evidence/2026-10-11-batch13/T-078/09b-stage-b-materials-04','evidence/2026-10-11-batch13/T-078/09b-stage-b-source-freeze-04.json','evidence/2026-10-11-batch13/T-078/09b-stage-b-commit-04','evidence/2026-10-11-batch13/T-078/09b-stage-b-05-ownership-preflight-01.json'}
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];assert any(n==p or n.startswith(p+'/') for p in allow),('Unowned work; no mutation',n)
for p in allow:
 if p not in future:assert Path(p).exists(),('Missing evidence',p)
red=json.loads((base/'09b-stage-b1-reuse-red-02/result.json').read_bytes());assert red.get('p1_exit_code')==1
for name in ['09b-stage-b1-reuse-green-07/result.json','09b-stage-b1-reuse-identity-readback-02/result.json','09b-stage-b1-reuse-resolver-tests-01/results.json']:
 assert json.loads((base/name).read_bytes())['status']=='PASS'
approval=json.loads((base/'stage-b-ideation-approval-10.json').read_bytes());assert approval['approved_by'] is None and approval['approval_ref'] is None and '--stop-before-cli' not in approval['p1_args']
subprocess.run(['git','diff','--check'],check=True)
rows=[];bad=[]
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];owner=next((p for p in allow if n==p or n.startswith(p+'/')),None);rows.append({'path':n,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [n]
assert not bad
ownership=base/'09b-stage-b-05-ownership-preflight-01.json';ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows,'method':'same prefix owner function as commit-09b-stage-b-05.sh'},ensure_ascii=False,indent=2)+'\n')
first=[p for p in allow if p not in future];subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','fix(T-078): complete bound API reuse readback and B1 gate'],check=True)
revision=git('rev-parse','HEAD');(base/'09b-stage-b-source-freeze-04.json').write_text(json.dumps({'revision':revision,'parent_revision':before,'reuse_green':'green-07 + readback-02 PASS','resolver_tests':'five mutation reds + valid green','messages_claim':'slice1 evidence only; B1 first-screen timing not yet observed','approval':'approval-10 unsigned','launch':'NO_GO'},ensure_ascii=False,indent=2)+'\n')
out=base/'09b-stage-b-materials-04';out.mkdir()
for src,name in [(base/'09B-STAGE-B-PLAN.md','PLAN.md'),(base/'stage-b-ideation-approval-10.json','stage-b-ideation-approval-10.json'),(base/'09b-stage-b1-reuse-green-07/result.json','reuse-green.json'),(base/'09b-stage-b1-reuse-identity-readback-02/result.json','identity-readback.json'),(base/'09b-stage-b1-reuse-resolver-tests-01/results.json','resolver-tests.json')]:shutil.copyfile(src,out/name)
(out/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':revision,'existing_api_reuse':True,'second_api_starts':0,'cli_starts':0,'first_screen_messages':'not observed in this stage; slice1 evidence only','approval_signed':False},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:f.write('\n## Stage-B bounded API reuse/readback materials-04\n\n完整 fake API argv/lstart resolver与五类 mutation red/green PASS；readback-02 argv_match true、两次身份一致；reuse-green-07 PASS，cli_spawned=false，A-05 无新 API。approval-10 留空签字，首屏 Messages 时序未在本阶段观测，slice1 证据只证明提交后请求。materials-04 静态 PASS，launch NO_GO。\n')
run=base/'09b-stage-b-commit-04';run.mkdir();(run/'freeze.command.json').write_text(json.dumps({'revision':revision,'packet':str(out)},ensure_ascii=False,indent=2)+'\n')
second=[str(out),str(base/'09b-stage-b-source-freeze-04.json'),str(base/'RESULTS.md'),str(run)]
subprocess.run(['git','add','--',*second],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze bounded API reuse and B1 approval 10'],check=True);assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'packet':str(out),'launch':'NO_GO'},ensure_ascii=False))
PY
