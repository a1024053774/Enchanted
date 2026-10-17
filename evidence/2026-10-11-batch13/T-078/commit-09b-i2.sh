#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='f1362104';check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-i2-allowlist.json').read_bytes());future={str(base/'09b-i2-ownership-preflight-01.json')}
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if item:
  path=item[3:];owner=next((p for p in allow if path==p or path.startswith(p+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [path]
assert not bad,('Unowned work; no mutation',bad)
first=[p for p in allow if p not in future];missing=[p for p in first if not Path(p).exists()];assert not missing,('Allowlist path missing before git add',missing)
driver=Path('workbench/tests/t078_09b_i1_driver.py').read_text();assert "choices=['I1','I2','I3','I4','E1','E2','E3','E4','E5','E6']" in driver and 'stage_budget' in driver and '--resume-queued' in driver
material=json.loads((base/'09b-a10-i2-materials-01/static-check.json').read_bytes());assert material['status']=='PASS' and material['stage']=='I2' and material['role']=='ideation' and material['messages_expected']==1 and material['messages_budget']==6
spy1=json.loads((base/'09b-stage-driver-i1-spy-01/results.json').read_bytes());spy2=json.loads((base/'09b-stage-driver-i2-spy-01/results.json').read_bytes());assert spy1['status']=='PASS' and spy2['status']=='PASS'
assert (base/'09b-a10-i2-materials-01/PHASE-COMMAND.txt').is_file() and (base/'a10-i2-prompt.txt').is_file()
subprocess.run(['git','diff','--check'],check=True);ownership=base/'09b-i2-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:fh.write('\n## A-10 phase-parametric I2 driver\n\nI1 regression and I2 spy 均 PASS；driver 现在按 I1–I4/E1–E6 阶段选择 role、Messages budget 和 ACK，I1 默认行为保留。I2 材料由 --stage-a/--p1 读取真实绑定生成，launch NO_GO。\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','test(T-078): parameterize phase driver and freeze I2 materials'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','launch':'NO_GO'}))
PY
