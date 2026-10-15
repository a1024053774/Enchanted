#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json,os,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='05cac8b4d4b0c00f35e7ce145ecb7d6b16b02552'
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078';assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35';assert os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker';assert not git('diff','--cached','--name-only')
paths=json.loads((base/'09b-run-allowlist.json').read_bytes())
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if row:
  n=row[3:];assert any(n==p or n.startswith(p+'/') for p in paths),('Unowned work; no mutation',n)
assert all(Path(p).exists() for p in paths)
for p in ['09b-run-source-freeze.json','09b-run-commit','09b-executable-materials-02']:assert not (base/p).exists(),('Existing output; preserve it, no retry',p)
assert json.loads((base/'09b-executable-materials-01/static-check.json').read_bytes())['launch_status']=='NO_GO'
spy=json.loads((base/'09b-run-spies-06/results.json').read_bytes());assert spy['status']=='PASS' and len(spy['checks'])==5 and spy['real_process_starts']==0
subprocess.run(['git','diff','--check'],check=True);subprocess.run(['git','add','--',*paths],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','test(T-078): stage-gate 09B entry runner without launch'],check=True)
revision=git('rev-parse','HEAD')
with (base/'09b-run-source-freeze.json').open('x',encoding='utf-8') as f:json.dump({'revision':revision,'parent_revision':before,'runner':'run-09b.py','stage_A':'approval-gated','stage_B':'not spawned','stage_C':'not spawned','real_process_starts':0,'launch':'NO_GO'},f,indent=2);f.write('\n')
run=base/'09b-run-commit';run.mkdir();argv=[sys.executable,'-B',str((base/'prepare-09b-executable.py').resolve()),'--label','09b-executable-materials-02']
with (run/'stdout.bin').open('xb') as stdout,(run/'stderr.bin').open('xb') as stderr:r=subprocess.run(argv,stdout=stdout,stderr=stderr)
with (run/'command.json').open('x',encoding='utf-8') as f:json.dump({'argv':argv,'revision':revision,'exit_code':r.returncode,'scope':'Static package only; runner not executed'},f,indent=2);f.write('\n')
assert r.returncode==0,'Preserve failed packet/commit; no retry'
packet=base/'09b-executable-materials-02';facts=json.loads((packet/'static-check.json').read_bytes());assert facts['status']=='PASS' and facts['launch_status']=='NO_GO' and facts['revision']==revision
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:f.write('\n## 09B 阶段 A runner 与可执行包静态冻结\n\nrunner source `'+revision+'` 已冻结；默认无 approval 不 spawn，A 阶段批准后才创建 root、detached fake API/daemon、card/dispatch/claim target 并写 readiness。新 [executable-02](09b-executable-materials-02/static-check.json) 静态 PASS、launch NO_GO；没有执行 runner、没有真实 CLI/API/目标，阶段 B/C 未启动。\n')
second=[str(packet),str(run),str(base/'09b-run-source-freeze.json'),str(base/'RESULTS.md')];subprocess.run(['git','add','--',*second],check=True);subprocess.run(['git','diff','--cached','--stat'],check=True);subprocess.run(['git','commit','-m','docs(T-078): freeze staged 09B launch review materials'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'packet':str(packet),'launch':'NO_GO'},ensure_ascii=False))
PY
