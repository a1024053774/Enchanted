#!/bin/bash
set -eu
# One controller-run final checkpoint on the rebased, committed candidate.
# No Git writes, identity restoration, real vendor CLI, or Claude fixture.
task_root=/Users/luckye/Documents/Code/a2a-wt-t078
evidence_root=/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078
run_label="${1:-outside-final-01}"
cd "$task_root"
python3 - "$run_label" <<'PY'
import json, os, subprocess, sys
from pathlib import Path
root=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
base=root/'evidence/2026-10-11-batch13/T-078'
label=sys.argv[1]
if not label or label in ('.','..') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in label):
    raise RuntimeError('A new single-directory label is required')
if (base/label).exists():raise RuntimeError('Existing evidence must not be overwritten')
git=lambda *argv:subprocess.check_output(['git',*argv],cwd=root,text=True).strip()
head=git('rev-parse','HEAD');parent=git('rev-parse','HEAD^')
if head!='b3fb998cf48574821c39440ece3f9ff897f26cf9' or parent!='532c51f4cc12352bb7cf545ce1e5f824d68bdc4a':
    raise RuntimeError('The candidate differs from the commit approved in controller message 68')
if git('branch','--show-current')!='exec/t078' or git('status','--porcelain','--','workbench'):
    raise RuntimeError('The candidate branch or frozen workbench changed')
if not os.path.ismount('/Volumes/WD-Elements'):raise RuntimeError('External volume is not mounted; no fallback')
subprocess.run(['git','merge-base','--is-ancestor','main','HEAD'],cwd=root,check=True)
assertions=['acceptance/test_coop_e2e.py','acceptance/test_recovery_e2e.py','acceptance/test_run_e2e.py']
if git('diff','14b57d22','HEAD','--',*assertions):raise RuntimeError('Original business assertions changed')
plan=json.loads((base/'freeze-plan.json').read_text(encoding='utf-8'))
trailers=subprocess.check_output(['git','interpret-trailers','--parse'],cwd=root,input=git('show','-s','--format=%B','HEAD'),text=True).splitlines()
for key,value in plan['expected_trailers'].items():
    if [line for line in trailers if line.startswith(key+':')]!=[key+': '+value]:
        raise RuntimeError('Original worker trailer changed: '+key)
with (base/('final-preflight-'+label+'.json')).open('x',encoding='utf-8') as stream:
    json.dump({'status':'PASS','head':head,'parent':parent,'main':git('rev-parse','main'),
               'branch':'exec/t078','worker_trailers':trailers,'workbench_clean':True,
               'assertions_unchanged_from':'14b57d22','execution_authorization':'controller message 68',
               'scope':'preflight only; tests have not started'},stream,ensure_ascii=False,indent=2)
print(json.dumps({'status':'PASS','phase':'final-preflight','head':head}))
PY
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/run_t078_stage2.py --final --label "$run_label" --identity-file "$evidence_root/worker-evidence-identity.json"
# The runner stops on any unexpected exit. Do not retry or continue after it.
