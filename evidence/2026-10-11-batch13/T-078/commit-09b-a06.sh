#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,os,subprocess,sys,shutil
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='6f8bc4fc';check_only='--check-only' in sys.argv[1:]
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
allow=json.loads((base/'09b-a06-allowlist.json').read_bytes());future={'evidence/2026-10-11-batch13/T-078/09b-a06-materials-01','evidence/2026-10-11-batch13/T-078/09b-a06-source-freeze-01.json','evidence/2026-10-11-batch13/T-078/09b-a06-commit-01','evidence/2026-10-11-batch13/T-078/09b-a06-ownership-preflight-01.json'}
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];assert any(n==p or n.startswith(p+'/') for p in allow),('Unowned work; no mutation',n)
green=json.loads((base/'09b-full-protocol-green-01/results.json').read_bytes());assert green['status']=='PASS' and green['oracle']['dispatch_seq']==10
for m in ['seq','text','identity','role']:
 assert json.loads((base/f'09b-full-protocol-mutant-{m}-01/results.json').read_bytes())['status']=='PASS'
subprocess.run(['git','diff','--check'],check=True)
rows=[];bad=[]
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];owner=next((p for p in allow if n==p or n.startswith(p+'/')),None);rows.append({'path':n,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [n]
assert not bad
ownership=base/'09b-a06-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
first=[p for p in allow if p not in future];subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','test(T-078): freeze full A-06 protocol oracle'],check=True)
revision=git('rev-parse','HEAD');(base/'09b-a06-source-freeze-01.json').write_text(json.dumps({'revision':revision,'parent_revision':before,'I_budget':'4 roots/6 Messages','E_budget':'6 roots/11 Messages','launch':'NO_GO'},ensure_ascii=False,indent=2)+'\n')
out=base/'09b-a06-materials-01';out.mkdir();
for src,name in [(base/'09B-A06-PLAN.md','PLAN.md'),(base/'a06-stage-a-approval-template.json','stage-a-approval-template.json'),(base/'09b-full-protocol-green-01/results.json','protocol-green.json'),(base/'09b-full-protocol-mutant-seq-01/results.json','mutant-seq.json'),(base/'09b-full-protocol-mutant-text-01/results.json','mutant-text.json'),(base/'09b-full-protocol-mutant-identity-01/results.json','mutant-identity.json'),(base/'09b-full-protocol-mutant-role-01/results.json','mutant-role.json')]:shutil.copyfile(src,out/name)
(out/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':revision,'real_process_starts':0,'model_turns':0,'I_roots':4,'I_messages':6,'E_roots':6,'E_messages':11},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:f.write('\n## A-06 full protocol offline materials\n\n最终协议假 API 离线覆盖 I1-I4/E1-E6、全局 seq/登记正文/身份/预算与 SSE；green 10 stages、I 4/6、E 6/11，四类变异拒绝。A-06 材料静态 PASS、launch NO_GO；A-05 cleanup/历史证据保持。\n')
run=base/'09b-a06-commit-01';run.mkdir();(run/'freeze.command.json').write_text(json.dumps({'revision':revision,'packet':str(out)},ensure_ascii=False,indent=2)+'\n');subprocess.run(['git','add','--',str(out),str(base/'09b-a06-source-freeze-01.json'),str(run)],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze A-06 stage A and B1 materials'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','packet':str(out),'launch':'NO_GO'}))
PY
