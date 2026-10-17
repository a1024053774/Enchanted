#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json, subprocess, sys, shutil
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078'); before='81ea4754'; check_only='--check-only' in sys.argv[1:]
label='09b-executable-materials-07'; command_file=base/'09B-A07-STAGE-A-COMMAND.txt'; materials=base/label
allow=json.loads((base/'09b-a07-allowlist.json').read_bytes()); future={str(base/'09b-a07-ownership-preflight-01.json'),str(base/'09b-a07-source-freeze-01.json'),str(materials),str(base/'09b-a07-commit-02')}
def git(*args): return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if item:
  path=item[3:];owner=next((p for p in allow if path==p or path.startswith(p+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [path]
assert not bad,('Unowned work; no mutation',bad)
first=[p for p in allow if p not in future];missing=[p for p in first if not Path(p).exists()];assert not missing,('Allowlist path missing before git add',missing)
matrix=json.loads((base/'09b-a07-protocol-matrix-01/summary.json').read_bytes());assert matrix['status']=='PASS' and len(matrix['stages'])==9 and all(s['green']['status']=='PASS' and s['red']['status']=='PASS' for s in matrix['stages'])
assert (base/'cleanup-09b-a06.py').is_file() and command_file.is_file()
command_text=command_file.read_text(encoding='utf-8');assert label.startswith('09b-executable-materials-') and f'--materials {base.resolve()}/{label}' in command_text and not materials.exists()
approval=json.loads((base/'a07-stage-a-approval-01.json').read_bytes());assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['protocol_tag']=='a07-registered-anthropic-v1'
b1=json.loads((base/'09b-a07-b1-ideation-p1-template/approval-template.json').read_bytes());assert b1['approved_by'] is None and b1['p1_materials'] is None and b1['api_protocol_tag']=='a07-registered-anthropic-v1'
subprocess.run(['git','diff','--check'],check=True)
ownership=base/'09b-a07-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
run=base/'09b-a07-commit-02';run.mkdir();parent_revision=git('rev-parse','HEAD');prepare=[sys.executable,'-B',str((base/'prepare-09b-executable.py').resolve()),'--label',label,'--protocol'];
with (run/'prepare.stdout.bin').open('xb') as so,(run/'prepare.stderr.bin').open('xb') as se: result=subprocess.run(prepare,stdout=so,stderr=se)
(run/'prepare.command.json').write_text(json.dumps({'argv':prepare,'exit_code':result.returncode},ensure_ascii=False,indent=2)+'\n');assert result.returncode==0
static=json.loads((materials/'static-check.json').read_bytes());assert static['status']=='PASS' and static['protocol'] is True and static['protocol_tag']=='a07-registered-anthropic-v1' and static['revision']==parent_revision
revision=static['revision'];freeze={'revision':revision,'parent_revision':parent_revision,'materials':'prepare-09b-executable.py --label '+label+' --protocol','protocol_tag':'a07-registered-anthropic-v1','matrix':str(base/'09b-a07-protocol-matrix-01/summary.json'),'cleanup':'owner-bound A06 script; launch NO_GO','launch':'NO_GO'}
(base/'09b-a07-source-freeze-01.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
approval['source_revision']=static['revision'];approval['basis']='A-07 materials-01 static PASS; protocol-tagged API; sign after review';(base/'a07-stage-a-approval-01.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:fh.write('\n## A-07 protocol matrix and A-06 cleanup handoff\n\nI2–I4/E1–E6 离线矩阵逐阶段绿态与 409 反例 PASS，ideation 3 阶段、executor 6 阶段，均只写登记和读取共享 protocol core；未启动服务。A-06 owner-bound cleanup 脚本绑定 root、daemon、target、Claude shell/CLI 与两个 API，dry-run 后才允许 daemon_stop、API 一次 SIGTERM、归档逐成员读回和删除。A-07 '+label+' 由同一 prepare-09b-executable.py --protocol 生成，协议标记为 a07-registered-anthropic-v1；Stage A/B1 approval 均留空，launch NO_GO。\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze A07 executable materials'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','materials':str(materials),'launch':'NO_GO'}))
PY
