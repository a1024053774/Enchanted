#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json, subprocess, sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='b77ccb29';check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-hooktrace-allowlist.json').read_bytes());future={str(base/'09b-hooktrace-ownership-preflight-01.json')}
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if item:
  path=item[3:];owner=next((p for p in allow if path==p or path.startswith(p+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [path]
assert not bad,('Unowned work; no mutation',bad)
first=[p for p in allow if p not in future];missing=[p for p in first if not Path(p).exists()];assert not missing,('Allowlist path missing before git add',missing)
red=json.loads((base/'09b-hooktrace-red-01/results.json').read_bytes());green=json.loads((base/'09b-hooktrace-green-03/results.json').read_bytes());legacy=json.loads((base/'09b-hooktrace-regression-01/results.json').read_bytes())
assert red['status']=='PASS' and red['phase']=='red' and red['cases']['valid']['binding_error']
assert green['status']=='PASS' and green['phase']=='green' and not green['cases']['valid']['binding_error'] and green['cases']['wrong-preset']['binding_error'] and green['cases']['wrong-launch']['binding_error']
assert legacy['status']=='PASS'
assert (base/'09b-a07-active-recovery-analysis.md').is_file()
subprocess.run(['git','diff','--check'],check=True);ownership=base/'09b-hooktrace-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:fh.write('\n## A-07 hookTrace binding red/green\n\n真实 cli.ts signal 入口在旧布局假设下取得 invalid_hook_trace_binding 红态；修复后允许 `root/roles/<preset>/hooks`，正确 preset/launch 绿态通过，错 preset/错 launch 仍拒绝。A-07 I1 active 卡住分析保留：Stop/pane stop/emergencyStop 均不能由 operator 合法收回，只有认证窗口用户 Esc/声明路径或 A-08 重建可继续。\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','fix(T-078): bind hook traces to controller role directories'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','launch':'NO_GO'}))
PY
