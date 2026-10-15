#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,os,subprocess,sys,shutil
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='5fd62384';check_only='--check-only' in sys.argv[1:]
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
allow=json.loads((base/'09b-a06-02-allowlist.json').read_bytes());future={'evidence/2026-10-11-batch13/T-078/09b-a06-materials-02','evidence/2026-10-11-batch13/T-078/09b-a06-source-freeze-02.json','evidence/2026-10-11-batch13/T-078/09b-a06-commit-02','evidence/2026-10-11-batch13/T-078/09b-a06-02-ownership-preflight-01.json'}
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];assert any(n==p or n.startswith(p+'/') for p in allow),('Unowned work; no mutation',n)
http=json.loads((base/'09b-http-protocol-red-green-01/results.json').read_bytes());assert http['status']=='PASS' and len(http['checks'])==7
cleanup=json.loads((base/'09b-a05-cleanup/result.json').read_bytes());assert cleanup['status']=='PASS'
subprocess.run(['git','diff','--check'],check=True)
rows=[];bad=[]
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];owner=next((p for p in allow if n==p or n.startswith(p+'/')),None);rows.append({'path':n,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [n]
assert not bad
ownership=base/'09b-a06-02-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
first=[p for p in allow if p not in future];subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','fix(T-078): add shared full protocol fake API'],check=True)
revision=git('rev-parse','HEAD');(base/'09b-a06-source-freeze-02.json').write_text(json.dumps({'revision':revision,'parent_revision':before,'shared_protocol_core':True,'http_red_green':'PASS','archive_bytes_recorded':8062309,'launch':'NO_GO'},ensure_ascii=False,indent=2)+'\n')
out=base/'09b-a06-materials-02';out.mkdir();
for src,name in [(base/'09B-A06-PLAN.md','PLAN.md'),(base/'09b-http-protocol-red-green-01/results.json','http-protocol.json'),(base/'09b-full-protocol-green-01/results.json','offline-green.json'),(base/'cleanup-09b-a05.py','a05-cleanup.py')]:shutil.copyfile(src,out/name)
(out/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':revision,'shared_protocol_core':True,'I_roots':4,'I_messages':6,'E_roots':6,'E_messages':11},ensure_ascii=False,indent=2)+'\n')
run=base/'09b-a06-commit-02';run.mkdir();(run/'freeze.command.json').write_text(json.dumps({'revision':revision,'packet':str(out)},ensure_ascii=False,indent=2)+'\n');subprocess.run(['git','add','--',str(out),str(base/'09b-a06-source-freeze-02.json'),str(run),str(base/'RESULTS.md')],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze shared protocol A-06 bridge'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','packet':str(out),'launch':'NO_GO'}))
PY
