#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json, subprocess, sys
from pathlib import Path

base = Path('evidence/2026-10-11-batch13/T-078')
before = 'e15d1890'
check_only = '--check-only' in sys.argv[1:]
allow = json.loads((base / '09b-a06-i1-allowlist.json').read_bytes())
future = {str(base / '09b-a06-i1-ownership-preflight-01.json')}

def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()

assert git('rev-parse', 'HEAD').startswith(before) and not git('diff', '--cached', '--name-only')
rows=[]; bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
    if not item: continue
    path=item[3:]; owner=next((entry for entry in allow if path==entry or path.startswith(entry+'/')),None)
    rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner})
    if owner is None: bad.append(path)
assert not bad, ('Unowned work; no mutation', bad)
first=[entry for entry in allow if entry not in future]
missing=[entry for entry in first if not Path(entry).exists()]
assert not missing, ('Allowlist path missing before git add', missing)

# Preserve the signed B1 launch evidence and all executor screen approvals.
b1_approval=json.loads((base/'stage-b-a06-ideation-approval-01.json').read_bytes())
assert b1_approval['approved_by']=='executor' and b1_approval['approval_ref']
b1_planner=json.loads((base/'09b-a06-b1-ideation-01/result.json').read_bytes())
assert b1_planner['status']=='PASS' and b1_planner['cli_spawned'] is True
b1_p1=json.loads((base/'09b-a06-b1-ideation-p1-01/09b-a06-b1-ideation-01/result.json').read_bytes())
assert b1_p1['process_manifest'] and b1_p1['runtime_manifest'] and b1_p1['api_url']

spy=json.loads((base/'09b-a06-i1-spy-01/results.json').read_bytes())
assert spy['status']=='PASS' and len(spy['checks'])==7 and all(row['status']=='PASS' for row in spy['checks'])
spy2=json.loads((base/'09b-a06-i1-spy-02/results.json').read_bytes())
assert spy2['status']=='PASS' and len(spy2['checks'])==7 and all(row['status']=='PASS' for row in spy2['checks'])
materials=json.loads((base/'09b-a06-i1-materials-01/static-check.json').read_bytes())
assert materials['status']=='PASS' and materials['launch_status']=='NO_GO' and materials['messages_expected']==1 and materials['roots_expected']==1 and materials['api_protocol_tag']=='a06-registered-anthropic-v1'
approval=json.loads((base/'09b-a06-i1-materials-01/approval-template.json').read_bytes())
assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['phase']=='I1'
assert approval['messages_expected']==1 and approval['messages_budget']==6
assert (base/'09b-a06-i1-materials-01/I1-COMMAND.txt').is_file()
subprocess.run(['git','diff','--check'],check=True)
ownership=base/'09b-a06-i1-ownership-preflight-01.json'
if check_only:
    existing=json.loads(ownership.read_bytes());assert existing['status']=='PASS' and existing['unowned']==[]
    print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}))
    raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
assert ownership.exists()
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:
    fh.write('\n## A-06 B1 ideation readback and I1 protocol driver\n\n'
             '主控已签 B1 approval 并完成 A-06 ideation 首启、逐屏主题/安全说明/信任选择，停在 s13 idle；B1 executor approvals、环境和原始读回全部保留。I1 新 driver 先取离线/spy 绿态与正文、seq、身份、stop/request、角色、预算六类 409 反例；真实路径只登记一条 dispatch，写入实际 request/stop ID 后 release 一次，预期 1 root/1 Messages，收到响应并 idle 即停。I1 材料 launch NO_GO，未启动新东西。\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True)
subprocess.run(['git','commit','-m','test(T-078): prepare A06 I1 registered protocol driver'],check=True)
assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','commit':git('rev-parse','HEAD'),'launch':'NO_GO'}))
PY
