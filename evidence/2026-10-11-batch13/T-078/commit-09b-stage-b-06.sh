#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,os,subprocess,sys,shutil
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='54e13274675fc25d9cf558fb40803e2382540941';check_only='--check-only' in sys.argv[1:]
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==before and not git('diff','--cached','--name-only')
allow=json.loads((base/'09b-stage-b-06-allowlist.json').read_bytes());future={'evidence/2026-10-11-batch13/T-078/09b-stage-b-materials-05','evidence/2026-10-11-batch13/T-078/09b-stage-b-source-freeze-05.json','evidence/2026-10-11-batch13/T-078/09b-stage-b-commit-05','evidence/2026-10-11-batch13/T-078/09b-stage-b-06-ownership-preflight-01.json'}
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];assert any(n==p or n.startswith(p+'/') for p in allow),('Unowned work; no mutation',n)
for p in allow:
 if p not in future and p.startswith('workbench/') or (p not in future and p.startswith('evidence/') and not Path(p).exists()):
  if p.startswith('workbench/') or p not in future: assert Path(p).exists(),('Missing evidence',p)
red=json.loads((base/'09b-stage-b1-ideation-03/result.json').read_bytes());assert red['status']=='INCOMPLETE' and 'NameError' in red.get('p1_stdout','')
dry=json.loads((base/'09b-stage-b1-ideation-03-dry-run/result.json').read_bytes());assert dry['status']=='READY_FOR_ROLE' and dry['spawned'] is False
approval10=json.loads((base/'stage-b-ideation-approval-10.json').read_bytes());assert approval10['approved_by']=='executor' and approval10['approval_ref']
approval11=json.loads((base/'stage-b-ideation-approval-11.json').read_bytes());assert approval11['approved_by'] is None and approval11['approval_ref'] is None
resolver=json.loads((base/'09b-stage-b1-reuse-resolver-tests-01/results.json').read_bytes());assert resolver['status']=='PASS'
controller=json.loads((base/'09b-stage-b1-controller-gate-tests-01/results.json').read_bytes());assert controller['status']=='PASS'
subprocess.run(['git','diff','--check'],check=True)
rows=[];bad=[]
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];owner=next((p for p in allow if n==p or n.startswith(p+'/')),None);rows.append({'path':n,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [n]
assert not bad
ownership=base/'09b-stage-b-06-ownership-preflight-01.json'
if check_only:
 existing=json.loads(ownership.read_bytes());assert existing['status']=='PASS' and existing['unowned']==[]
 print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad},ensure_ascii=False));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows,'method':'same prefix owner function as commit-09b-stage-b-06.sh'},ensure_ascii=False,indent=2)+'\n')
first=[p for p in allow if p not in future];subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','fix(T-078): bind reuse controller task and label runtime files'],check=True)
revision=git('rev-parse','HEAD');(base/'09b-stage-b-source-freeze-05.json').write_text(json.dumps({'revision':revision,'parent_revision':before,'red_preserved':'stage-b1-ideation-03 NameError before controller_start','dry_run_preserved':'approval-10 dry-run READY_FOR_ROLE','p1_reuse':'existing API resolver + label runtime-input','controller_gate':'PASS with task mutation red','approval':'approval-11 unsigned','launch':'NO_GO'},ensure_ascii=False,indent=2)+'\n')
out=base/'09b-stage-b-materials-05';out.mkdir()
for src,name in [(base/'09B-STAGE-B-PLAN.md','PLAN.md'),(base/'stage-b-ideation-approval-11.json','stage-b-ideation-approval-11.json'),(base/'09b-stage-b1-reuse-resolver-tests-01/results.json','resolver-tests.json'),(base/'09b-stage-b1-controller-gate-tests-01/results.json','controller-gate-tests.json'),(base/'09b-stage-b1-ideation-03/result.json','red-result.json'),(base/'09b-stage-b1-ideation-03-dry-run/result.json','dry-run-result.json')]: shutil.copyfile(src,out/name)
(out/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':revision,'reuse_api':'existing A-05 only','cli_starts':0,'new_api_starts':0,'approval_signed':False},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:f.write('\n## B1 task binding/runtime path correction materials-05\n\n保留 approval-10 签字件、dry-run 与真实 B1 NameError 红态；复用分支现绑定 A-05 task 并将 runtime-input 写入按 label 的 P1 输出目录，controller-start 参数构造测试 PASS，删 task 变异被拒。approval-11 留空，materials-05 静态 launch NO_GO，A-05 现场不清理。\n')
run=base/'09b-stage-b-commit-05';run.mkdir();(run/'freeze.command.json').write_text(json.dumps({'revision':revision,'packet':str(out)},ensure_ascii=False,indent=2)+'\n')
second=[str(out),str(base/'09b-stage-b-source-freeze-05.json'),str(base/'RESULTS.md'),str(run)]
subprocess.run(['git','add','--',*second],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze B1 task binding and runtime path materials'],check=True);assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'packet':str(out),'launch':'NO_GO'},ensure_ascii=False))
PY
