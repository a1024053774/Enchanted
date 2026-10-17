#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import ast,json,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='26d2820a';check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-a12-b1-allowlist.json').read_bytes());future={str(base/'09b-a12-ownership-preflight-01.json')}
def git(*args): return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before),git('rev-parse','HEAD');assert not git('diff','--cached','--name-only')
rows=[];unowned=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if not item: continue
 path=item[3:];owner=next((e for e in allow if path==e or path.startswith(e+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});unowned += [] if owner else [path]
assert not unowned,('Unowned work; no mutation',unowned);missing=[e for e in allow if e not in future and not Path(e).exists()];assert not missing,('Allowlist path missing before git add',missing)
ast.parse((base/'cleanup-09b-a11.py').read_text(),filename=str(base/'cleanup-09b-a11.py'))
dry=json.loads((base/'09b-a11-cleanup-01-dry-run/result.json').read_bytes());clean=json.loads((base/'09b-a11-cleanup-01/result.json').read_bytes());assert dry['status']=='PASS' and dry['dry_run'] and dry['signals_sent']==[];assert clean['status']=='PASS' and clean['root_removed'] and clean['byte_readback']=='PASS' and len(clean['signals_sent'])==2 and clean['archive'].endswith('/09b-a11-cleanup/fixture.tar.gz')
stage=json.loads((base/'09b-a12-stage-a-01/readiness.json').read_bytes());stage_result=json.loads((base/'09b-a12-stage-a-01/result.json').read_bytes());assert stage['status']=='READY_FOR_APPROVAL' and stage_result['status']=='READY_FOR_APPROVAL' and stage['roles_started']==[];assert stage['root']=='/private/tmp/t078-2-09b-run-3ec7pe2c' and stage['daemon']['pid']==93829 and stage['target_process']['shell_pid']==93921 and stage['target_process']['leader']==93923 and {x['role']:x['pid'] for x in stage['api_processes']}=={'ideation':93826,'executor':93827}
approval=json.loads((base/'a12-stage-a-approval-01.json').read_bytes());static=json.loads((base/'09b-executable-materials-12/static-check.json').read_bytes());assert approval['approved_by']=='executor' and '主控 #287' in approval['approval_ref'] and approval['source_revision']==static['revision'];assert static['status']=='PASS' and static['protocol'] is True;subprocess.run(['git','merge-base','--is-ancestor',static['revision'],git('rev-parse','HEAD')],check=True)
p1=base/'09b-a12-b1-ideation-p1-01';inp=json.loads((p1/'input.json').read_bytes());assert inp['root']==stage['root'] and inp['preset']=='ideation' and json.loads((p1/'generation.json').read_bytes())['status']=='PASS'
onboard=json.loads((base/'09b-a12-b1-onboard-materials-01/static-check.json').read_bytes());assert onboard['status']=='PASS' and onboard['messages_expected']==0 and onboard['screen_reads']==7
i1=json.loads((base/'09b-a12-i1-materials-01/static-check.json').read_bytes());assert i1['status']=='PASS' and i1['messages_expected']==2 and i1['permission_screens_expected']==1 and i1['tool']=='I_SEND_STOP';i1a=json.loads((base/'09b-a12-i1-materials-01/approval.json').read_bytes());assert i1a['approved_by'] is None and i1a['approval_ref'] is None and i1a['launch']==inp['launch'] and i1a['session']==inp['session'];assert '--protocol-phase dispatch' in (base/'09b-a12-i1-materials-01/I1-COMMAND.txt').read_text() and 'onboarding-notice' in (base/'09b-a12-b1-onboard-materials-01/ONBOARD-COMMANDS.txt').read_text()
b1=json.loads((base/'stage-b-a12-ideation-approval-01.json').read_bytes());assert b1['approved_by']=='executor' and '主控 #288' in b1['approval_ref'] and b1['binding']==stage['target_binding'] and b1['p1_materials']==str(p1.resolve())
dryb1=json.loads((base/'09b-a12-b1-ideation-dry-run-01/result.json').read_bytes());assert dryb1['status']=='READY_FOR_ROLE' and dryb1['spawned'] is False and dryb1['p1_spawned'] is False and dryb1['cli_spawned'] is False
assert (base/'09B-A12-B1-COMMANDS.txt').read_text().count('run-09b-stage-b.py')==2
subprocess.run(['git','diff','--check'],check=True);assert [r['path'] for r in rows if r['allowlist_entry'] is None]==[]
ownership=base/'09b-a12-ownership-preflight-01.json'
if check_only: print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':unowned,'simulated_final_status':[],'materials':str(base/'09b-executable-materials-12'),'launch':'NO_GO'},ensure_ascii=False));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':unowned,'entries':rows,'simulated_final_status':[]},ensure_ascii=False,indent=2)+'\n');
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh: fh.write('\n## A-11 cleanup and A-12 B1/I1 packet\n\nA-11 owner-bound cleanup dry-run/formal PASS：两个 protocol API 各 SIGTERM 一次，七进程退出，逐成员读回后 root 删除，归档在 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a11-cleanup/fixture.tar.gz`。A-12 Stage A READY_FOR_APPROVAL，root/API/daemon/target 绑定与签字 approval 保留；ideation B1 onboarding、0 Messages 断言和 split protocol I1 材料均为 NO_GO 静态准备，本轮未启动角色、未发送输入。\n')
paths=[Path(e) for e in allow if e not in future]+[ownership,base/'RESULTS.md'];subprocess.run(['git','add','--',*map(str,paths)],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze A12 B1 and cleanup packet'],check=True);assert git('status','--porcelain')=='';print(json.dumps({'status':'PASS','commit':git('rev-parse','HEAD'),'simulated_final_status':[],'launch':'NO_GO'},ensure_ascii=False))
PY
