#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json, subprocess, sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='178ca7e4';check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-a07-i1-allowlist.json').read_bytes());future={str(base/'09b-a07-i1-ownership-preflight-01.json')}
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if item:
  path=item[3:];owner=next((p for p in allow if path==p or path.startswith(p+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [path]
assert not bad,('Unowned work; no mutation',bad)
first=[p for p in allow if p not in future];missing=[p for p in first if not Path(p).exists()];assert not missing,('Allowlist path missing before git add',missing)
ready=json.loads((base/'09b-a07-stage-a-01/readiness.json').read_bytes());stage=json.loads((base/'09b-a07-stage-a-01/result.json').read_bytes());assert ready['status']=='READY_FOR_APPROVAL' and stage['status']=='READY_FOR_APPROVAL' and ready['roles_started']==[]
assert ready['api_processes'][0]['pid']==5436 and ready['api_processes'][0]['ready']['port']==54603 and ready['api_processes'][0]['ready']['protocol']=='a07-registered-anthropic-v1'
p1=json.loads((base/'09b-a07-b1-ideation-p1-01/09b-a07-b1-ideation-01/result.json').read_bytes());manifest=json.loads((base/'09b-a07-b1-ideation-p1-01/09b-a07-b1-ideation-01/process-manifest.json').read_bytes());assert p1['process_manifest'] and manifest['cli']['pid']==10267
b1=json.loads((base/'stage-b-a07-ideation-approval-01.json').read_bytes());assert b1['approved_by']=='executor' and b1['approval_ref'] and b1['p1_args'][1:3]==['--reuse-api-root','/private/tmp/t078-2-09b-run-1o4prsr5/roles/ideation']
material=json.loads((base/'09b-a07-i1-materials-01/static-check.json').read_bytes());assert material['status']=='PASS' and material['launch_status']=='NO_GO' and material['api_pid']==5436 and material['api_port']==54603 and material['api_protocol_tag']=='a07-registered-anthropic-v1' and material['messages_expected']==1
approval=json.loads((base/'09b-a07-i1-materials-01/approval-template.json').read_bytes());assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['target_binding']==ready['target_binding']
audit=json.loads((base/'09b-a07-i1-materials-01/b1-approval-audit.json').read_bytes());assert audit['status']=='INCOMPLETE' and audit['b1_p1_args_binding']=='PASS' and audit['signed_evidence_unchanged'] is True
spy=json.loads((base/'09b-a07-i1-spy-02/results.json').read_bytes());assert spy['status']=='PASS' and len(spy['checks'])==8 and spy['checks'][-1]['name']=='approved-p1-path-red-green'
old=json.loads((base/'09b-a07-i1-execute-01/result.json').read_bytes());assert old['status']=='INCOMPLETE' and 'FileNotFoundError' in old['error']
command=(base/'09b-a07-i1-materials-01/I1-COMMAND.txt').read_text(encoding='utf-8');assert '09b-a07-i1-execute-02' in command and '09b-a07-i1-execute-01' not in command
assert (base/'09b-a07-b1-exec-approvals').is_dir() and (base/'09b-a07-i1-materials-01/I1-COMMAND.txt').is_file()
subprocess.run(['git','diff','--check'],check=True);ownership=base/'09b-a07-i1-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:fh.write('\n## A-07 I1 materials\n\nA-07 readiness、B1 P1 launch/session 与 ideation API 5436/54603 的实际绑定已读回；I1 材料预期 1 root/1 Messages，正文、dispatch.seq、request/stop ID 登记方式和停止条件均冻结，approval 留空、launch NO_GO。B1 signed approval 的冗余 api_reuse 元数据仍指向旧 A-06，已单独审计为 INCOMPLETE，签字证据未改写；I1 使用正确的 A-07 readiness/API root。\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','docs(T-078): prepare A07 I1 materials'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','launch':'NO_GO'}))
PY
