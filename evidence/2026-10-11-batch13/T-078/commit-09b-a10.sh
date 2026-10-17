#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='b36c81aa';label='09b-executable-materials-10';materials=base/label;check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-a10-allowlist.json').read_bytes());future={str(base/'09b-a10-ownership-preflight-01.json'),str(base/'09b-a10-source-freeze-01.json'),str(materials),str(base/'09b-a10-commit-01')}
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if item:
  path=item[3:];owner=next((p for p in allow if path==p or path.startswith(p+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [path]
assert not bad,('Unowned work; no mutation',bad)
first=[p for p in allow if p not in future];missing=[p for p in first if not Path(p).exists()];assert not missing,('Allowlist path missing before git add',missing)
api=Path('workbench/tests/t078_09b_fake_api.py').read_text(encoding='utf-8');assert 'ROLE=a.role' in api and 'http-exchanges' in api
red=json.loads((base/'09b-a10-http-red-observed-01/results.json').read_bytes());assert red['status']=='PASS' and red['error']=="name 'ROLE' is not defined"
red2=json.loads((base/'09b-a10-http-red-02/results.json').read_bytes());green=json.loads((base/'09b-a10-http-green-02/results.json').read_bytes());assert red2['status']=='PASS' and green['status']=='PASS'
assert (base/'cleanup-09b-a09.py').is_file() and (base/'09B-A10-STAGE-A-COMMAND.txt').is_file()
approval=json.loads((base/'a10-stage-a-approval-01.json').read_bytes());assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['protocol_tag']=='a07-registered-anthropic-v1'
subprocess.run(['git','diff','--check'],check=True);ownership=base/'09b-a10-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:fh.write('\n## A-10 API role binding and raw HTTP evidence\n\nA-09 live API 红态原件记录 name ROLE 未定义，11 次重试均只回 409；A-10 修复从 --role 赋 ROLE，并按序保存 request/response 原文。真实 Claude 2.1.296 请求原件出处为 slice1-green-3-readback/api.jsonl；A-10 loopback test 使用该结构，launch NO_GO。A-09 owner-bound cleanup 脚本绑定新现场参数，未运行。\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','test(T-078): prepare A10 protocol API evidence'],check=True)
parent=git('rev-parse','HEAD');prepare=[sys.executable,'-B',str((base/'prepare-09b-executable.py').resolve()),'--label',label,'--protocol'];run=base/'09b-a10-commit-01';run.mkdir()
with (run/'prepare.stdout.bin').open('xb') as so,(run/'prepare.stderr.bin').open('xb') as se:res=subprocess.run(prepare,stdout=so,stderr=se)
(run/'prepare.command.json').write_text(json.dumps({'argv':prepare,'exit_code':res.returncode},ensure_ascii=False,indent=2)+'\n');assert res.returncode==0
static=json.loads((materials/'static-check.json').read_bytes());assert static['status']=='PASS' and static['protocol'] is True and static['protocol_tag']=='a07-registered-anthropic-v1' and static['revision']==parent
(base/'09b-a10-source-freeze-01.json').write_text(json.dumps({'revision':parent,'parent_revision':parent,'materials':'prepare-09b-executable.py --label '+label+' --protocol','protocol_tag':'a07-registered-anthropic-v1','launch':'NO_GO'},ensure_ascii=False,indent=2)+'\n')
approval['source_revision']=static['revision'];approval['basis']='A-10 materials-10 static PASS; role-bound raw HTTP API; sign after review';(base/'a10-stage-a-approval-01.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n')
subprocess.run(['git','add','--',str(materials),str(base/'09b-a10-source-freeze-01.json'),str(base/'a10-stage-a-approval-01.json'),str(run)],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze A10 materials'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','materials':str(materials),'launch':'NO_GO'}))
PY
