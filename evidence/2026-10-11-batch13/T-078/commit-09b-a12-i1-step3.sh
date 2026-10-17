#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='9264d94d';check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-a12-i1-step3-allowlist.json').read_bytes());future={str(base/'09b-a12-i1-step3-ownership-preflight-01.json')}
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];unowned=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if not item:continue
 path=item[3:];owner=next((e for e in allow if path==e or path.startswith(e+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});unowned += [] if owner else [path]
assert not unowned,('Unowned work; no mutation',unowned);missing=[e for e in allow if e not in future and not Path(e).exists()];assert not missing,('Allowlist path missing before git add',missing)
assert 'args.output.name' in Path('workbench/tests/t078_09b_i1_permission.py').read_text();assert 'window.a2a.input' in Path('workbench/tests/electron_driver.mjs').read_text()
cmd=(base/'09b-a12-i1-materials-01/I1-COMMAND.txt').read_text();assert 'execute-02' in cmd and 'permission-approval-03.json' in cmd
approval=json.loads((base/'09b-a12-i1-materials-01/permission-approval-03.json').read_bytes());assert approval['approved_by'] is None and approval['approval_ref'] is None
stderr=(base/'09b-a12-i1-materials-01/execute-01-electron-stderr.txt').read_text();assert 'Window is not available for input' in stderr or stderr

green=json.loads((base/'09b-a12-permission-slot-green-01/result.json').read_bytes());red=json.loads((base/'09b-a12-permission-slot-red-01/result.json').read_bytes());assert green['status']=='PASS' and green['distinct'] is True and red['status']=='PASS' and red['decision']=='409'
subprocess.run(['git','diff','--check'],check=True);assert [r['path'] for r in rows if r['allowlist_entry'] is None]==[]
ownership=base/'09b-a12-i1-step3-ownership-preflight-01.json'
if check_only:print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':unowned,'simulated_final_status':[],'launch':'NO_GO'},ensure_ascii=False));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':unowned,'entries':rows,'simulated_final_status':[]},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:fh.write('\n## A-12 I1 step3 unique Electron slot\n\nThe first permission attempt failed before key delivery because the build slot was already occupied. The new permission runner derives a unique slot from the output label (`execute-02`) and the launch; the signed permission-approval-03 remains blank for review. Original execute-01 logs are retained, and offline slot red/green proves collision rejection and unique naming. No input was sent by this fix packet.\n')
paths=[Path(e) for e in allow if e not in future]+[ownership,base/'RESULTS.md'];subprocess.run(['git','add','--',*map(str,paths)],check=True);subprocess.run(['git','commit','-m','docs(T-078): prepare unique A12 I1 permission slot'],check=True);assert git('status','--porcelain')=='';print(json.dumps({'status':'PASS','commit':git('rev-parse','HEAD'),'simulated_final_status':[],'launch':'NO_GO'},ensure_ascii=False))
PY
