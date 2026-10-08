#!/usr/bin/env python3
"""Use the controller-authorized shared checkout after an idle A preflight."""
import importlib.util
import json
from pathlib import Path
import subprocess
import traceback

out = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('comparison',out/'run-comparison.py')
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)
fork = comparison.SHARED
original_branch = subprocess.check_output(['git','branch','--show-current'],cwd=fork,text=True).strip()
original_head = comparison.revision(fork)
assert original_branch == 'a2a' and original_head == comparison.SETUP['shared_checkout_head']
assert not (out/'results.jsonl').exists(), 'Do not overwrite a completed or partial test matrix'
assert not comparison.a_timing(), 'A timing is active; switching is forbidden'


def switch(kind):
    assert not comparison.a_timing(), 'A timing is active; switching is forbidden'
    dirty = subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=fork,text=True)
    assert not dirty, 'Preserve tracked edits; no checkout switch'
    revision = comparison.SETUP['revisions'][kind]['commit']
    result = subprocess.run(['git','switch','--detach',revision],cwd=fork,capture_output=True,text=True,check=True)
    comparison.append('switches.jsonl',{'at':comparison.now(),'kind':kind,'argv':['git','switch','--detach',revision],
                                      'stdout':result.stdout,'stderr':result.stderr,'head':comparison.revision(fork)})
    comparison.SETUP['shared_checkout_head'] = revision


try:
    env = comparison.environment()
    for package,test in comparison.FILES:
        stem = Path(test).stem.replace('.test','')
        for round_number in (1,2,3):
            for kind in ('parent','candidate'):
                switch(kind)
                label = f'{stem}-{round_number}-{kind}'
                result_path = out/(label+'.json')
                argv = [str(fork/'a2a/scripts/bun'),'run','env','TMPDIR='+str(comparison.EXTERNAL/'t'),
                        'bun','run','--cwd','apps/'+package,'test',test,
                        '--reporter=json','--outputFile='+str(result_path)]
                result = comparison.command(label,fork,argv,env,600)
                assert result_path.is_file(), 'Setup failure: Vitest result artifact missing'
                report = json.loads(result_path.read_text(encoding='utf-8'))
                result.update(test_file=test,package=package,kind=kind,round=round_number,
                              numTotalTests=report['numTotalTests'],numPassedTests=report['numPassedTests'],
                              numFailedTests=report['numFailedTests'],success=report['success'],
                              failures=[a['fullName'] for f in report['testResults'] for a in f['assertionResults'] if a['status']=='failed'])
                comparison.append('results.jsonl',result)
                print(json.dumps({'label':label,'exit':result['exit'],'failed':result['numFailedTests']}),flush=True)
    comparison.append('completion.jsonl',{'status':'COMPLETE','mode':'shared checkout',
                       'ended':comparison.now(),'runs':24,'test_or_product_source_edited':False})
except BaseException as error:
    comparison.append('completion.jsonl',{'status':'INCOMPLETE','mode':'shared checkout','ended':comparison.now(),'error':str(error)})
    traceback.print_exc()
    raise
finally:
    restore = subprocess.run(['git','switch',original_branch],cwd=fork,capture_output=True,text=True)
    comparison.append('switches.jsonl',{'at':comparison.now(),'kind':'restore','exit':restore.returncode,
                      'stdout':restore.stdout,'stderr':restore.stderr,'head':comparison.revision(fork)})
    assert restore.returncode == 0 and comparison.revision(fork) == original_head
