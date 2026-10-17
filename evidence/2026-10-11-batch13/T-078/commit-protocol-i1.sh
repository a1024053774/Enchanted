#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='da91e780';check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-protocol-i1-allowlist.json').read_bytes());future={str(base/'09b-protocol-i1-ownership-preflight-01.json')}
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if item:
  path=item[3:];owner=next((p for p in allow if path==p or path.startswith(p+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [path]
assert not bad,('Unowned work; no mutation',bad)
first=[p for p in allow if p not in future];missing=[p for p in first if not Path(p).exists()];assert not missing,('Allowlist path missing before git add',missing)
green=json.loads((base/'09b-protocol-i1-green-02/result.json').read_bytes());assert green['status']=='PASS' and green['phases']['I1']['messages']==2 and green['phases']['I1']['tool_use']['name']=='Bash'
for m in ['target','seq','id','actor','text']:
 red=json.loads((base/f'09b-protocol-{m}-red-02/result.json').read_bytes());assert red['status']=='PASS' and red['decision']=='409'
api_green=json.loads((base/'09b-protocol-api-green-04/result.json').read_bytes());assert api_green['status']=='PASS'
assert api_green['I1']['messages_used']==2 and api_green['I1']['first']['stop_reason']=='tool_use' and api_green['I1']['second']['settlement'] is True
assert api_green['I2']['messages_used']==1 and api_green['I2']['confirm_only'] is True
assert api_green['E1']['wrong_target_rejected'] is True and api_green['E1']['second_settlement'] is True
for m in ['tool_id','entry_id','target','seq','role','text']:
 red=json.loads((base/f'09b-protocol-api-{m}-red-04/result.json').read_bytes());assert red['status']=='PASS' and red['decision']=='409'
material=json.loads((base/'09b-protocol-i1-materials-01/static-check.json').read_bytes());assert material['status']=='PASS' and material['messages_expected']==2 and material['permission_screens_expected']==1
assert material['tool_result_settlement'] is True and material['sse_events_expected']==6
assert Path('workbench/tests/t078_09b_fake_api.py').exists() and Path('workbench/tests/t078_09b_i1_driver.py').exists() and Path('workbench/tests/t078_09b_protocol_api_oracle.py').exists()
subprocess.run(['git','diff','--check'],check=True);ownership=base/'09b-protocol-i1-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:fh.write('\n## Protocol I1 tool/inbox stage oracle\n\n冻结 protocol 的 I1 离线绿态实现 I_SEND_STOP tool_use、tool_result、实际 stop/wake 关联；I2/E1 材料边界按协议保留。A-10 管道回合已计入 ideation 4/6（1 root/1 Messages），Protocol I1 追加 1 root/2 Messages 后仍在预算内。未启动或发送。\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','test(T-078): freeze protocol I1 tool and inbox oracle'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','launch':'NO_GO'}))
PY
