#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='60a3db95';label='09b-executable-materials-09';materials=base/label;check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-a09-allowlist.json').read_bytes());future={str(base/'09b-a09-ownership-preflight-01.json'),str(base/'09b-a09-source-freeze-01.json'),str(materials),str(base/'09b-a09-commit-01')}
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if item:
  path=item[3:];owner=next((p for p in allow if path==p or path.startswith(p+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [path]
assert not bad,('Unowned work; no mutation',bad)
first=[p for p in allow if p not in future];missing=[p for p in first if not Path(p).exists()];assert not missing,('Allowlist path missing before git add',missing)
cmd=(base/'09B-A09-STAGE-A-COMMAND.txt').read_text(encoding='utf-8');assert label.startswith('09b-executable-materials-') and f'--materials {base.resolve()}/{label}' in cmd and not materials.exists()
approval=json.loads((base/'a09-stage-a-approval-01.json').read_bytes());assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['protocol_tag']=='a07-registered-anthropic-v1'
b1=json.loads((base/'stage-b-a09-ideation-approval-template.json').read_bytes());assert len(b1['screen_approvals'])==6 and b1['tool_approval']['one_time'] is True
assert (base/'cleanup-09b-a08.py').is_file() and (base/'T-078-A09-COMMAND-TEMPLATES.md').is_file()
subprocess.run(['git','diff','--check'],check=True);ownership=base/'09b-a09-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:
    fh.write('\n## A-09 packet and A-08 cleanup\n\nA-08 owner-bound cleanup script dry-run/formal由主控运行后归档读回；A-09 materials-09 由同一 prepare-09b-executable.py --protocol 生成，协议标记 a07-registered-anthropic-v1。Stage A approval 与 B1 template 留空，screen approvals/tool approval 完整，launch NO_GO。\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','test(T-078): prepare A09 packet and A08 cleanup'],check=True)
parent=git('rev-parse','HEAD');prepare=[sys.executable,'-B',str((base/'prepare-09b-executable.py').resolve()),'--label',label,'--protocol'];run=base/'09b-a09-commit-01';run.mkdir()
with (run/'prepare.stdout.bin').open('xb') as so,(run/'prepare.stderr.bin').open('xb') as se:res=subprocess.run(prepare,stdout=so,stderr=se)
(run/'prepare.command.json').write_text(json.dumps({'argv':prepare,'exit_code':res.returncode},ensure_ascii=False,indent=2)+'\n');assert res.returncode==0
static=json.loads((materials/'static-check.json').read_bytes());assert static['status']=='PASS' and static['protocol'] is True and static['protocol_tag']=='a07-registered-anthropic-v1' and static['revision']==parent
freeze={'revision':parent,'parent_revision':parent,'materials':'prepare-09b-executable.py --label '+label+' --protocol','protocol_tag':'a07-registered-anthropic-v1','launch':'NO_GO','cleanup':'owner-bound A08 cleanup script'}
(base/'09b-a09-source-freeze-01.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
approval['source_revision']=static['revision'];approval['basis']='A-09 materials-09 static PASS; protocol-tagged API; sign after review';(base/'a09-stage-a-approval-01.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n')
subprocess.run(['git','add','--',str(materials),str(base/'09b-a09-source-freeze-01.json'),str(base/'a09-stage-a-approval-01.json'),str(run)],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze A09 materials'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','materials':str(materials),'launch':'NO_GO'}))
PY
