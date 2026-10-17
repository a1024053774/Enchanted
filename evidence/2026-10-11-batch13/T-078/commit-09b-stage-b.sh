#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, shutil, subprocess, sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078'); before='e301f15b0fd27f962f00001a4280cf08fbf19ea9'
def git(*args): return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35' and os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not git('diff','--cached','--name-only')
allow=json.loads((base/'09b-stage-b-allowlist.json').read_bytes());future={'evidence/2026-10-11-batch13/T-078/09b-stage-b-materials-01','evidence/2026-10-11-batch13/T-078/09b-stage-b-source-freeze.json','evidence/2026-10-11-batch13/T-078/09b-stage-b-commit','evidence/2026-10-11-batch13/T-078/09b-stage-b-ownership-preflight-01.json'}
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];assert any(n==p or n.startswith(p+'/') for p in allow),('Unowned work; no mutation',n)
for p in allow:
 if p not in future: assert Path(p).exists(),('Missing evidence',p)
scene=json.loads((base/'09b-stage-a-05/result.json').read_bytes()); ready=json.loads((base/'09b-stage-a-05/readiness.json').read_bytes())
assert scene['status']=='READY_FOR_APPROVAL' and scene['stage']=='A' and scene['real_vendor_model_turns']==0
assert ready['status']=='READY_FOR_APPROVAL' and ready['roles_started']==[] and ready['target_binding']==scene['attempt']
assert ready['target_process']['leader']==70839 and {x['pid'] for x in ready['api_processes']}=={70730,70731} and ready['daemon']['pid']==70733
spies=json.loads((base/'09b-stage-b-spies-03/results.json').read_bytes());assert spies['status']=='PASS' and spies['spawned'] is False and spies['real_process_starts']==0 and len(spies['checks'])==7
approval=json.loads((base/'stage-b-ideation-approval.json').read_bytes());assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['binding']==ready['target_binding']
assert Path(approval['p1_materials']).is_dir() and json.loads((Path(approval['p1_materials'])/'input.json').read_bytes())['root']==ready['root']
subprocess.run(['git','diff','--check'],check=True)
rows=[];unowned=[]
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];owner=next((p for p in allow if n==p or n.startswith(p+'/')),None);rows.append({'path':n,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});unowned += [] if owner else [n]
assert not unowned
ownership=base/'09b-stage-b-ownership-preflight-01.json';ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':unowned,'entries':rows},ensure_ascii=False,indent=2)+'\n')
first=[p for p in allow if p not in future]
subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','feat(T-078): gate stage B role approvals and binding'],check=True)
revision=git('rev-parse','HEAD')
with (base/'09b-stage-b-source-freeze.json').open('x',encoding='utf-8') as f: json.dump({'revision':revision,'parent_revision':before,'stage_a_binding_preserved':True,'roles_started':[],'launch':'NO_GO','scope':'approval/preflight only; no Claude spawn'},f,ensure_ascii=False,indent=2); f.write('\n')
out=base/'09b-stage-b-materials-01';out.mkdir();shutil.copyfile(base/'09B-STAGE-B-PLAN.md',out/'PLAN.md');shutil.copyfile(base/'stage-b-approval-template.json',out/'stage-b-approval-template.json');shutil.copyfile(base/'09b-stage-b-spies-01/results.json',out/'spies.json')
(out/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':revision,'stage_a':'09b-stage-a-05','real_cli_starts':0,'api_starts':0,'daemon_starts':0,'target_starts':0,'real_vendor_model_turns':0,'roles_started':[],'approval_required':'per-role/per-phase/per-screen'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:f.write('\n## 阶段 B materials-01 静态冻结\n\nB1 仅冻结逐角色审批门禁与 screen-key 计划，绑定 A-05 readiness；spies-02 PASS，含缺 approval/binding/并发三项变异红态，spawned=false；materials-01 静态 PASS 且 launch NO_GO。未启动 Claude、pane 输入、API、daemon、target 或模型。\n')
second=[str(out),str(base/'09b-stage-b-source-freeze.json'),str(base/'RESULTS.md'),str(base/'09b-stage-b-commit')]
run=base/'09b-stage-b-commit';run.mkdir();(run/'freeze.command.json').write_text(json.dumps({'revision':revision,'packet':str(out)},ensure_ascii=False,indent=2)+'\n')
subprocess.run(['git','add','--',*second],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze stage B approval materials'],check=True)
assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'packet':str(out),'launch':'NO_GO'},ensure_ascii=False))
PY
