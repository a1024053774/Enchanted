#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='e980099a';check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-a12-i1-settle-allowlist.json').read_bytes());future={str(base/'09b-a12-i1-settle-ownership-preflight-01.json')}
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];unowned=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if not item:continue
 path=item[3:];owner=next((e for e in allow if path==e or path.startswith(e+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});unowned += [] if owner else [path]
assert not unowned,('Unowned work; no mutation',unowned);missing=[e for e in allow if e not in future and not Path(e).exists()];assert not missing,('Allowlist path missing before git add',missing)
# Preserve the real failed execute-02 Electron evidence and signed approval.
assert (base/'09b-a12-i1-materials-01/execute-02-electron-driver.jsonl').is_file(); approval=json.loads((base/'09b-a12-i1-materials-01/permission-approval-03.json').read_bytes());assert approval['approved_by']=='executor' and '主控 #291' in approval['approval_ref']
cmd=(base/'09b-a12-i1-materials-01/I1-COMMAND.txt').read_text();assert 'execute-02' in cmd and 'permission-approval-03.json' in cmd
# Real queued receipt shape: API settles the request receipt, relay later creates stop entry/wake.
g=json.loads((base/'09b-a12-i1-e2e-green-03/result.json').read_bytes());assert g['status']=='PASS' and g['messages_used']==2 and g['queued_receipt']['queued'] is True and g['stop_entry']['from']=='ideation' and g['relay']['delivered'] is True
for name in ['missing-queue','wrong-request','wrong-target']:
 r=json.loads((base/f'09b-a12-i1-e2e-{name}-red-03/result.json').read_bytes());assert r['status']=='PASS'
assert 'request_root' in Path('workbench/tests/t078_09b_protocol_core.py').read_text()
assert (base/'09b-a13-rebuild-plan.md').is_file()
subprocess.run(['git','diff','--check'],check=True);assert [r['path'] for r in rows if r['allowlist_entry'] is None]==[]
ownership=base/'09b-a12-i1-settle-ownership-preflight-01.json'
if check_only:print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':unowned,'simulated_final_status':[],'a13_required':True,'launch':'NO_GO'},ensure_ascii=False));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':unowned,'entries':rows,'simulated_final_status':[],'a13_required':True},ensure_ascii=False,indent=2)+'\n');
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:fh.write('\n## A-12 I1 queued receipt settlement and A-13 requirement\n\nA-12 I1 real tool_result was the queued controller request receipt (`queued=true`, `delivered=false`, request_id/path); the actual stop entry is created later by the Stop hook relay. Shared validation and offline end-to-end oracle now settle the queued receipt first, then require the actual ideation→executor stop entry and wake. A-12 ideation used 1 root/12 Messages and exceeded 4/6; A-13 fresh rebuild is required. Original execute-02 failure evidence and signed permission approval remain unchanged.\n')
paths=[Path(e) for e in allow if e not in future]+[ownership,base/'RESULTS.md'];subprocess.run(['git','add','--',*map(str,paths)],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze queued stop settlement and A13 plan'],check=True);assert git('status','--porcelain')=='';print(json.dumps({'status':'PASS','commit':git('rev-parse','HEAD'),'simulated_final_status':[],'a13_required':True,'launch':'NO_GO'},ensure_ascii=False))
PY
