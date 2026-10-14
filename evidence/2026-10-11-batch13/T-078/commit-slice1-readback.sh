#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -B - <<'PY'
import os,subprocess
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078')
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
assert git('rev-parse','HEAD')=='14e19e2bff16eacfcba7ab00bd63906aef42cced'
assert git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not any(k in os.environ for k in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'))
assert not git('diff','--cached','--name-only'),'Preserve preexisting staged work'
assert not git('diff','--','workbench/src','workbench/app','workbench/hooks','workbench/bin','acceptance','scripts')
paths=['workbench/tests/t078_slice1_protocol.py','workbench/tests/test_t078_slice1_recorded_request.py',
       'workbench/tests/regenerate_t078_p1.py',str(base/'prepare-slice1-red.py'),
       str(base/'RESULTS.md'),str(base/'SLICE-1-READBACK.md'),str(base/'cleanup-slice1-red.py'),
       str(base/'commit-slice1-readback.sh'),str(base/'slice1-readback'),str(base/'slice1-recorded-api-red'),
       str(base/'slice1-recorded-api-green'),str(base/'slice1-recorded-api-mutant-command'),
       str(base/'slice1-protocol-system-tail-regression'),str(base/'slice1-protocol-system-tail-mutant-budget'),
       str(base/'slice1-template-check'),str(base/'slice1-readback-static.json'),
       str(base/'slice1-readback-project-map-status.txt'),str(base/'p1-materials-slice1-red'),
       '.project-map/inbox/20261014T222756Z-worker:t078-slice1-readback-report-001.md']
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
    if row:
        name=row[3:]
        assert any(name==p or name.startswith(p+'/') for p in paths),('Unowned change; no mutation',name)
for p in paths:assert Path(p).exists(),('Missing handoff path',p)
subprocess.run(['git','diff','--check'],check=True)
subprocess.run(['git','add','--',*paths],check=True)
subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','test(T-078): preserve native tool red and locate results before system metadata'],check=True)
print('PASS: native failure and fixture fix frozen; no cleanup, retry, generation or launch')
subprocess.run(['git','status','--short'],check=True)
PY
