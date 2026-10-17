#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,os,subprocess,sys,shutil
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='950dd0e4'
check_only='--check-only' in sys.argv[1:]
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
allow=json.loads((base/'09b-stage-b-07-allowlist.json').read_bytes());future={'evidence/2026-10-11-batch13/T-078/09b-stage-b-materials-06','evidence/2026-10-11-batch13/T-078/09b-stage-b-source-freeze-06.json','evidence/2026-10-11-batch13/T-078/09b-stage-b-commit-06','evidence/2026-10-11-batch13/T-078/09b-stage-b-07-ownership-preflight-01.json'}
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];assert any(n==p or n.startswith(p+'/') for p in allow),('Unowned work; no mutation',n)
for p in allow:
 if p not in future and p.startswith('workbench/'): assert Path(p).exists()
old=json.loads((base/'09b-stage-b1-screen-ideation-01/result.json').read_bytes());assert old['status']=='INCOMPLETE'
assert (base/'stage-b-ideation-approval-12.json').exists() and (base/'stage-b-ideation-approval-13.json').exists()
manifest=base/'09b-stage-b-ideation-p1-02/09b-stage-b1-ideation-04';assert (manifest/'process-manifest.json').exists() and (manifest/'runtime-manifest.json').exists()
subprocess.run(['git','diff','--check'],check=True)
rows=[];bad=[]
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];owner=next((p for p in allow if n==p or n.startswith(p+'/')),None);rows.append({'path':n,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [n]
assert not bad
ownership=base/'09b-stage-b-07-ownership-preflight-01.json';
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
first=[p for p in allow if p not in future];subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','fix(T-078): bind screen phases to labeled launch output'],check=True)
revision=git('rev-parse','HEAD');(base/'09b-stage-b-source-freeze-06.json').write_text(json.dumps({'revision':revision,'parent_revision':before,'screen_launch_label':'09b-stage-b1-ideation-04','screen_read_only':True,'keys_sent':False,'launch':'NO_GO'},ensure_ascii=False,indent=2)+'\n')
out=base/'09b-stage-b-materials-06';out.mkdir();shutil.copyfile(base/'stage-b-ideation-approval-13.json',out/'approval-13.json');shutil.copyfile(base/'09b-stage-b1-ideation-04/result.json',out/'launch-result.json');shutil.copyfile(base/'09b-stage-b1-screen-ideation-dry-run/result.json',out/'screen-dry-run.json');shutil.copyfile(base/'09b-stage-b1-screen-ideation-01/result.json',out/'screen-red-result.json');(out/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':revision,'screen_read_only':True,'keys_sent':False},ensure_ascii=False,indent=2)+'\n')
run=base/'09b-stage-b-commit-06';run.mkdir();(run/'freeze.command.json').write_text(json.dumps({'revision':revision,'packet':str(out)},ensure_ascii=False,indent=2)+'\n');subprocess.run(['git','add','--',str(out),str(base/'09b-stage-b-source-freeze-06.json'),str(base/'09b-stage-b-commit-06')],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze labeled read-only screen approval 13'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','packet':str(out),'launch':'NO_GO'}))
PY
