#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, shutil, subprocess, sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='92a61308f9467a0b90b7cbf0ca6534081502a5d1'
def git(*args): return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35' and os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not git('diff','--cached','--name-only')
allow=json.loads((base/'09b-stage-b-03-allowlist.json').read_bytes());future={'evidence/2026-10-11-batch13/T-078/09b-stage-b-materials-03','evidence/2026-10-11-batch13/T-078/09b-stage-b-source-freeze-03.json','evidence/2026-10-11-batch13/T-078/09b-stage-b-commit-03','evidence/2026-10-11-batch13/T-078/09b-stage-b-03-ownership-preflight-01.json'}
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];assert any(n==p or n.startswith(p+'/') for p in allow),('Unowned work; no mutation',n)
for p in allow:
 if p not in future: assert Path(p).exists(),('Missing evidence',p)
red=json.loads((base/'09b-stage-b1-ideation-02/result.json').read_bytes());assert red['status']=='INCOMPLETE' and red.get('p1_exit_code')==1 and red.get('cli_spawned') is False
assert 'Local API exited before readiness' in red.get('p1_stderr','')
spy=json.loads((base/'09b-stage-b1-reuse-spy-01/results.json').read_bytes());assert spy['status']=='PASS' and spy['spawned'] is False and spy['api_starts']==0 and spy['cli_starts']==0
approval=json.loads((base/'stage-b-ideation-approval-03.json').read_bytes());assert approval['approved_by'] is None and approval['approval_ref'] is None and '--reuse-stage-a' in approval['p1_args']
subprocess.run(['git','diff','--check'],check=True)
rows=[];bad=[]
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];owner=next((p for p in allow if n==p or n.startswith(p+'/')),None);rows.append({'path':n,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [n]
assert not bad
ownership=base/'09b-stage-b-03-ownership-preflight-01.json';ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows,'method':'same prefix owner function as commit-09b-stage-b-03.sh'},ensure_ascii=False,indent=2)+'\n')
first=[p for p in allow if p not in future];subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','fix(T-078): reuse bound Stage-A API for P1 launch'],check=True)
revision=git('rev-parse','HEAD')
(base/'09b-stage-b-source-freeze-03.json').write_text(json.dumps({'revision':revision,'parent_revision':before,'red_preserved':'self-start API exits before readiness','reuse':'existing A-05 role API PID/lstart/ready only; no second API','launch':'NO_GO'},ensure_ascii=False,indent=2)+'\n')
out=base/'09b-stage-b-materials-03';out.mkdir()
for src,name in [(base/'09B-STAGE-B-PLAN.md','PLAN.md'),(base/'stage-b-ideation-approval-03.json','stage-b-ideation-approval-03.json'),(base/'09b-stage-b1-p1-prereq-02/result.json','p1-prereq.json'),(base/'09b-stage-b1-reuse-spy-01/results.json','reuse-spy.json'),(base/'09b-stage-b1-ideation-02/result.json','red-result.json')]: shutil.copyfile(src,out/name)
(out/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':revision,'stage_a':'09b-stage-a-05','existing_api_reuse':True,'second_api_starts':0,'cli_starts':0,'model_turns':0},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:f.write('\n## Stage-B B1 existing-API reuse correction\n\n保留 `09b-stage-b1-ideation-02` 红态：旧 P1 自启第二 API，因模板 api_url=127.0.0.1:0 退出，p1 非零、cli_spawned=false；stderr 原件已由 #210 读回。runner/P1 新分支要求 `--reuse-stage-a --reuse-api-root`，只核对 A-05 已就绪 API 的 ready/PID/lstart/command，跳过第二 API 与重复 daemon/setup，再委托同一 run_t078_p1.py。reuse spy PASS，api_starts=0、cli_starts=0；approval-03 留空签字字段，materials-03 launch NO_GO。\n')
run=base/'09b-stage-b-commit-03';run.mkdir();(run/'freeze.command.json').write_text(json.dumps({'revision':revision,'packet':str(out)},ensure_ascii=False,indent=2)+'\n')
second=[str(out),str(base/'09b-stage-b-source-freeze-03.json'),str(base/'RESULTS.md'),str(run)]
subprocess.run(['git','add','--',*second],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze existing API reuse and B1 materials 03'],check=True);assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'packet':str(out),'launch':'NO_GO'},ensure_ascii=False))
PY
