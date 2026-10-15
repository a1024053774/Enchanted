#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,os,subprocess,sys,shutil
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='c2c7c544';check_only='--check-only' in sys.argv[1:]
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
allow=json.loads((base/'09b-i1-allowlist.json').read_bytes());future={'evidence/2026-10-11-batch13/T-078/09b-i1-materials-01','evidence/2026-10-11-batch13/T-078/09b-i1-source-freeze-01.json','evidence/2026-10-11-batch13/T-078/09b-i1-commit-01','evidence/2026-10-11-batch13/T-078/09b-i1-ownership-preflight-01.json'}
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];assert any(n==p or n.startswith(p+'/') for p in allow),('Unowned work; no mutation',n)
green=json.loads((base/'09b-i1-green-01/results.json').read_bytes());assert green['status']=='PASS' and green['oracle']['messages_used']==1
for m in ['text','seq','role','budget']:
 assert json.loads((base/f'09b-i1-mutant-{m}-01/results.json').read_bytes())['status']=='PASS'
assert json.loads((base/'09b-i1-mutant-request-02/results.json').read_bytes())['status']=='PASS'
subprocess.run(['git','diff','--check'],check=True)
rows=[];bad=[]
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];owner=next((p for p in allow if n==p or n.startswith(p+'/')),None);rows.append({'path':n,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [n]
assert not bad
ownership=base/'09b-i1-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
first=[p for p in allow if p not in future];subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','test(T-078): freeze offline I1 Messages protocol red and green'],check=True)
revision=git('rev-parse','HEAD');(base/'09b-i1-source-freeze-01.json').write_text(json.dumps({'revision':revision,'parent_revision':before,'messages_used':1,'roots_used':1,'budget':'I 4 roots/6 Messages','launch':'NO_GO'},ensure_ascii=False,indent=2)+'\n')
out=base/'09b-i1-materials-01';out.mkdir();
for src,name in [(base/'09B-I1-PLAN.md','PLAN.md'),(base/'i1-ideation-approval-template.json','approval-template.json'),(base/'09b-i1-green-01/results.json','green.json'),(base/'09b-i1-mutant-text-01/results.json','mutant-text.json'),(base/'09b-i1-mutant-seq-01/results.json','mutant-seq.json'),(base/'09b-i1-mutant-request-02/results.json','mutant-request.json'),(base/'09b-i1-mutant-role-01/results.json','mutant-role.json'),(base/'09b-i1-mutant-budget-01/results.json','mutant-budget.json')]:shutil.copyfile(src,out/name)
(out/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':revision,'real_process_starts':0,'model_turns':0,'messages_used':1,'roots_used':1},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:f.write('\n## I1 offline Messages protocol red/green\n\n离线 I1 绿色请求 1 Messages/1 root，SSE 四事件；正文、dispatch.seq、request_id、role、预算五类变异均被独立 oracle 拒绝。无 socket/API/CLI/daemon/target/model；I1 待批材料绑定实际 ideation session/target attempt，launch NO_GO。\n')
run=base/'09b-i1-commit-01';run.mkdir();(run/'freeze.command.json').write_text(json.dumps({'revision':revision,'packet':str(out)},ensure_ascii=False,indent=2)+'\n');subprocess.run(['git','add','--',str(out),str(base/'09b-i1-source-freeze-01.json'),str(run)],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze I1 offline protocol materials'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','packet':str(out),'launch':'NO_GO'}))
PY
