#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json, subprocess, sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078'); before='872550a4'; check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-a12-i1-fix-allowlist.json').read_bytes()); future={str(base/'09b-a12-i1-fix-ownership-preflight-01.json')}
def git(*args): return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];unowned=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if not item: continue
 path=item[3:]; owner=next((e for e in allow if path==e or path.startswith(e+'/')),None); rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner}); unowned += [] if owner else [path]
assert not unowned, ('Unowned work; no mutation',unowned)
missing=[e for e in allow if e not in future and not Path(e).exists()]; assert not missing, ('Allowlist path missing before git add',missing)
assert (base/'09b-a12-i1-materials-01/execute-01-electron-driver.jsonl').is_file()
assert 'terminal-focus' in (base/'09b-a12-i1-materials-01/execute-01-electron-stderr.txt').read_text(encoding='utf-8') or 'Window is not available' in (base/'09b-a12-i1-materials-01/execute-01-electron-stderr.txt').read_text(encoding='utf-8')
assert len([l for l in (base/'09b-a12-i1-materials-01/dispatch-01/requests.ndjson').read_text().splitlines() if l]) == 1 if (base/'09b-a12-i1-materials-01/dispatch-01/requests.ndjson').exists() else True
source=Path('workbench/tests/electron_driver.mjs').read_text(); assert 'const delivered = await window.webContents.executeJavaScript("window.a2a.input' in source
green=json.loads((base/'09b-a12-permission-electron-green-01/result.json').read_bytes()); red=json.loads((base/'09b-a12-permission-electron-red-01/result.json').read_bytes()); assert green['status']=='PASS' and green['awaits_daemon_receipt'] is True and red['status']=='PASS' and red['decision']=='409'
approval=json.loads((base/'09b-a12-i1-materials-01/permission-approval-02.json').read_bytes()); assert approval['approved_by']=='executor' and '主控 #289' in approval['approval_ref']
commands=(base/'09b-a12-i1-materials-01/I1-COMMAND.txt').read_text(); assert commands.count('\\n')>=0 and 'pane_output' in commands and 't078_09b_i1_permission.py' in commands and 'process-manifest' in commands
assert (base/'09b-a12-b1-exec-approvals').is_dir() and (base/'09b-a12-b1-ideation-01/result.json').is_file()
subprocess.run(['git','diff','--check'],check=True)
ownership=base/'09b-a12-i1-fix-ownership-preflight-01.json'
if check_only:
 print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':unowned,'simulated_final_status':[],'launch':'NO_GO'},ensure_ascii=False)); raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':unowned,'entries':rows,'simulated_final_status':[]},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh: fh.write('\n## A-12 I1 Electron permission acknowledgement fix\n\nA-12 I1 dispatch reached the bound PermissionRequest; the first permission attempt produced terminal_focus_intercepted observations but no daemon window_input/terminal_input_write_intent. Root cause was electron_driver terminal-key returning after native sendInputEvent without awaiting the product window IPC receipt. The fixed permission path awaits window.a2a.input(\\r), while preserving the bound Electron window, dispatch and one control action. Original execute-01 failure remains; offline red/green oracle covers receipt absence and corrected path. No retry or real key was sent by this fix packet.\n')
paths=[Path(e) for e in allow if e not in future]+[ownership,base/'RESULTS.md']; subprocess.run(['git','add','--',*map(str,paths)],check=True); subprocess.run(['git','commit','-m','docs(T-078): freeze A12 permission receipt fix'],check=True); assert git('status','--porcelain')==''; print(json.dumps({'status':'PASS','commit':git('rev-parse','HEAD'),'simulated_final_status':[],'launch':'NO_GO'},ensure_ascii=False))
PY
