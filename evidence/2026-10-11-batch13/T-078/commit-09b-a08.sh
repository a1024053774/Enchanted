#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json, subprocess, sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078')
before='ea4c6e05'; label='09b-executable-materials-08'; materials=base/label
check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-a08-allowlist.json').read_bytes())
future={str(base/'09b-a08-ownership-preflight-01.json'),str(base/'09b-a08-source-freeze-01.json'),str(materials),str(base/'09b-a08-commit-01')}
def git(*args): return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
    if item:
        path=item[3:]; owner=next((p for p in allow if path==p or path.startswith(p+'/')),None)
        rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner})
        if owner is None: bad.append(path)
assert not bad, ('Unowned work; no mutation',bad)
first=[p for p in allow if p not in future]; missing=[p for p in first if not Path(p).exists()]
assert not missing, ('Allowlist path missing before git add',missing)
command=(base/'09B-A08-STAGE-A-COMMAND.txt').read_text(encoding='utf-8')
assert label.startswith('09b-executable-materials-') and f'--materials {base.resolve()}/{label}' in command and not materials.exists()
approval=json.loads((base/'a08-stage-a-approval-01.json').read_bytes()); assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['protocol_tag']=='a07-registered-anthropic-v1'
b1=(base/'stage-b-a08-ideation-approval-template.json').read_text(encoding='utf-8'); assert '"approved_by": null' in b1 and '"p1_materials": null' in b1
templates=(base/'T-078-A08-COMMAND-TEMPLATES.md').read_text(encoding='utf-8'); assert '--stage-a' in templates and '--p1' in templates
subprocess.run(['git','diff','--check'],check=True)
ownership=base/'09b-a08-ownership-preflight-01.json'
if check_only:
    ex=json.loads(ownership.read_bytes()); assert ex['status']=='PASS' and ex['unowned']==[]
    print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad})); raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True)
subprocess.run(['git','commit','-m','test(T-078): prepare A08 static packet and parameterized generators'],check=True)
parent=git('rev-parse','HEAD'); prepare=[sys.executable,'-B',str((base/'prepare-09b-executable.py').resolve()),'--label',label,'--protocol']; run=base/'09b-a08-commit-01'; run.mkdir()
with (run/'prepare.stdout.bin').open('xb') as so,(run/'prepare.stderr.bin').open('xb') as se: result=subprocess.run(prepare,stdout=so,stderr=se)
(run/'prepare.command.json').write_text(json.dumps({'argv':prepare,'exit_code':result.returncode},ensure_ascii=False,indent=2)+'\n'); assert result.returncode==0
static=json.loads((materials/'static-check.json').read_bytes()); assert static['status']=='PASS' and static['protocol'] is True and static['protocol_tag']=='a07-registered-anthropic-v1' and static['revision']==parent
freeze={'revision':parent,'parent_revision':parent,'materials':'prepare-09b-executable.py --label '+label+' --protocol','protocol_tag':'a07-registered-anthropic-v1','launch':'NO_GO','p1_generator':'prepare-a07-b1-ideation-p1.py --stage-a --p1','i1_generator':'prepare-09b-i1-materials.py --stage-a --p1'}
(base/'09b-a08-source-freeze-01.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
approval['source_revision']=static['revision']; approval['basis']='A-08 materials-08 static PASS; protocol-tagged API; sign after review'; (base/'a08-stage-a-approval-01.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:
    fh.write('\n## A-08 static packet and parameterized generators\n\nA-07 owner-bound cleanup script已交主控运行；A-08 materials-08 由同一 prepare-09b-executable.py --protocol 生成，协议标记 a07-registered-anthropic-v1。B1 P1 与 I1 生成器均从显式 --stage-a/--p1 读取真实 readiness/input/manifest，不写死 A-06/A-07 路径；approval 从实际输入生成并留空。A-08 launch NO_GO。\n')
subprocess.run(['git','add','--',str(materials),str(base/'09b-a08-source-freeze-01.json'),str(base/'a08-stage-a-approval-01.json'),str(run)],check=True)
subprocess.run(['git','commit','-m','docs(T-078): freeze A08 materials and command templates'],check=True)
assert not git('status','--porcelain'); print(json.dumps({'status':'PASS','materials':str(materials),'launch':'NO_GO'}))
PY
