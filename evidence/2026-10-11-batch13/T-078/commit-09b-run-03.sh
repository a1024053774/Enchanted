#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
base = Path('evidence/2026-10-11-batch13/T-078')
before = '88d3c422bd4b1729eca2b146a9cc923ad5796978'
def git(*args): return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()
assert git('rev-parse','HEAD') == before and git('branch','--show-current') == 'exec/t078'
assert os.environ.get('CODEX_THREAD_ID') == '01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK') == 'T-078-1' and os.environ.get('A2A_ROLE') == 'worker'
assert not git('diff','--cached','--name-only')
paths = json.loads((base/'09b-run-03-allowlist.json').read_bytes())
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
    if row:
        name=row[3:]; assert any(name==p or name.startswith(p+'/') for p in paths), ('Unowned work; no mutation',name)
assert all(Path(p).exists() for p in paths)
for name in ['09b-run-03-source-freeze.json','09b-run-03-commit','09b-executable-materials-03']:
    assert not (base/name).exists(), ('Existing output; preserve it, no retry',name)
old=json.loads((base/'09b-stage-a-01/result.json').read_bytes()); assert old['spawned'] is False and 'Executable packet is stale' in old.get('error','')
subprocess.run(['git','diff','--check'],check=True); subprocess.run(['git','add','--',*paths],check=True); subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','fix(T-078): gate stage runner on ancestor material lineage'],check=True)
revision=git('rev-parse','HEAD')
with (base/'09b-run-03-source-freeze.json').open('x',encoding='utf-8') as f:
    json.dump({'revision':revision,'parent_revision':before,'old_red_preserved':True,'runner_lineage':'ancestor + ticket-evidence-only','blocked':['workbench/','scripts/','runner self changes'],'launch':'NO_GO'},f,indent=2); f.write('\n')
run=base/'09b-run-03-commit'; run.mkdir()
prepare=[sys.executable,'-B',str((base/'prepare-09b-executable.py').resolve()),'--label','09b-executable-materials-03']
with (run/'prepare.stdout.bin').open('xb') as stdout,(run/'prepare.stderr.bin').open('xb') as stderr:
    result=subprocess.run(prepare,stdout=stdout,stderr=stderr)
with (run/'prepare.command.json').open('x',encoding='utf-8') as f:
    json.dump({'argv':prepare,'revision':revision,'exit_code':result.returncode},f,indent=2); f.write('\n')
assert result.returncode==0, 'Preserve failed package/commit; no retry'
spy=base/'09b-run-revision-spy-03'
subprocess.run([sys.executable,'-B','workbench/tests/test_t078_09b_revision_gate.py','--materials',str(base/'09b-executable-materials-03'),'--output',str(spy)],check=True)
facts=json.loads((base/'09b-executable-materials-03/static-check.json').read_bytes())
assert facts['status']=='PASS' and facts['launch_status']=='NO_GO' and facts['revision']==revision
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:
    f.write('\n## 阶段 A 材料 revision lineage 修复与 spy 绿态\n\n旧 [stage-a-01](09b-stage-a-01/result.json) stale 红态保留：spawned=false、无 root。runner 现要求材料 revision 是 HEAD 祖先，revision..HEAD 只允许本票证据目录，并拒绝 workbench/scripts/runner 自身变化。新 [materials-03](09b-executable-materials-03/static-check.json) 静态 PASS；[revision spy](09b-run-revision-spy-03/results.json) 绿态接受当前 lineage，workbench/src 反例拒绝，spawned=false。仍未执行阶段 A。\n')
second=[str(base/'09b-executable-materials-03'),str(run),str(base/'09b-run-03-source-freeze.json'),str(base/'RESULTS.md'),str(spy)]
subprocess.run(['git','add','--',*second],check=True); subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','docs(T-078): freeze stage runner lineage spy and materials 03'],check=True)
assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'packet':str(base/'09b-executable-materials-03'),'launch':'NO_GO'},ensure_ascii=False))
PY
