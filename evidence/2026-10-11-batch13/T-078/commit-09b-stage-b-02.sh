#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='c04bc41030e20c8aeaf12274fa086b8f9df0044c'
def git(*args): return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35' and os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not git('diff','--cached','--name-only')
allow=json.loads((base/'09b-stage-b-02-allowlist.json').read_bytes());future={'evidence/2026-10-11-batch13/T-078/09b-stage-b-materials-02','evidence/2026-10-11-batch13/T-078/09b-stage-b-source-freeze-02.json','evidence/2026-10-11-batch13/T-078/09b-stage-b-commit-02','evidence/2026-10-11-batch13/T-078/09b-stage-b-ownership-preflight-02.json'}
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];assert any(n==p or n.startswith(p+'/') for p in allow),('Unowned work; no mutation',n)
for p in allow:
 if p not in future: assert Path(p).exists(),('Missing evidence',p)
red=json.loads((base/'09b-stage-b1-ideation/result.json').read_bytes());assert red['status']=='INCOMPLETE' and red.get('p1_exit_code')==1 and 'FileNotFoundError' in red.get('p1_stderr','') and 'scenario.json' in red.get('p1_stderr','')
pre=json.loads((base/'09b-stage-b1-p1-prereq-02/result.json').read_bytes());assert pre['status']=='PASS' and pre['spawned'] is False and pre['cli_spawned'] is False
new=json.loads((base/'stage-b-ideation-approval-02.json').read_bytes());assert new['approved_by'] is None and new['approval_ref'] is None
subprocess.run(['git','diff','--check'],check=True)
rows=[];bad=[]
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];owner=next((p for p in allow if n==p or n.startswith(p+'/')),None);rows.append({'path':n,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [n]
assert not bad
ownership=base/'09b-stage-b-ownership-preflight-02.json';ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows,'method':'same prefix owner function as commit-09b-stage-b-02.sh'},ensure_ascii=False,indent=2)+'\n')
first=[p for p in allow if p not in future];subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','fix(T-078): preserve P1 launch failure and split spawn verdicts'],check=True)
revision=git('rev-parse','HEAD')
(base/'09b-stage-b-source-freeze-02.json').write_text(json.dumps({'revision':revision,'parent_revision':before,'red_preserved':'p1 missing scenario preflight','p1_prereq':'PASS before spawn','spawn_verdicts':['p1_spawned','cli_spawned'],'launch':'NO_GO'},ensure_ascii=False,indent=2)+'\n')
out=base/'09b-stage-b-materials-02';out.mkdir();
for src,name in [(base/'09B-STAGE-B-PLAN.md','PLAN.md'),(base/'stage-b-approval-template.json','stage-b-approval-template.json'),(base/'09b-stage-b1-p1-prereq-02/result.json','p1-prereq.json'),(base/'09b-stage-b1-ideation/result.json','red-result.json'),(base/'09b-stage-b1-ideation-dry-run/result.json','dry-run-result.json')]: __import__('shutil').copyfile(src,out/name)
(out/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':revision,'stage_a':'09b-stage-a-05','p1_prereq_status':'PASS','cli_starts':0,'model_turns':0,'roles_started':[]},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:f.write('\n## Stage-B B1 P1 prerequisite red/green correction\n\n保留 `09b-stage-b1-ideation` 红态：run_t078_p1 在 spawn 前因 A-05 root 缺 `scenario.json` 退出，p1 exit=1、p1_stderr 含 FileNotFoundError/scenario.json；CLI 未启动这一事实以主控 #207 的 pgrep 读回为准，不从旧 result 推断。补齐 root/input、nonce、scenario 与角色隔离目录后，独立 prerequisite preflight-02 PASS，未启动任何进程。runner 现在传播 p1 非零退出，并分别记录 p1_spawned 与 cli_spawned；approval-02 重新留空签字字段，材料-02 静态 launch NO_GO。\n')
run=base/'09b-stage-b-commit-02';run.mkdir();(run/'freeze.command.json').write_text(json.dumps({'revision':revision,'packet':str(out)},ensure_ascii=False,indent=2)+'\n')
second=[str(out),str(base/'09b-stage-b-source-freeze-02.json'),str(base/'RESULTS.md'),str(run)]
subprocess.run(['git','add','--',*second],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze B1 P1 prerequisite correction'],check=True);assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'packet':str(out),'launch':'NO_GO'},ensure_ascii=False))
PY
