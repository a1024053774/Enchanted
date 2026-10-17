"""Read saved regression-02 evidence without restarting any fixture."""
import json,subprocess
from pathlib import Path

ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=Path(__file__).resolve().parent
OUT=BASE/'rebased-outside-regression-02-09a3'
revision='567d7748c40ca511f170997d7fe216063fb7c4f1'
stage=json.loads((OUT/'result.json').read_bytes())
assert stage['status']=='PASS' and stage['revision']==revision and stage['real_model_turns']==0
assert json.loads((BASE/'regression-02-source-freeze.json').read_bytes())['revision']==revision
checks=[]
for name,count in [('worker-inbox',14),('coop',8),('recovery',9),('run',18),('cas',1)]:
    facts=json.loads((OUT/name/('results.json' if name=='worker-inbox' else 'run.json')).read_bytes())
    assert facts['status']=='PASS'
    if name=='worker-inbox':
        assert facts['setup_complete'] and facts['cleanup_complete'] and len(facts['checks'])==count
        assert all(row['status']=='PASS' for row in facts['checks'])
    else:
        assert facts['tests_run']==count and not facts['failures'] and not facts['errors'] and not facts['skipped']
    checks.append({'name':name,'checks':count,'status':'PASS','file':str(OUT/name)})
verdicts=json.loads((OUT/'worker-rule-verdicts.json').read_bytes())
assert set(verdicts)=={'assign','ready','foreign-ack','revoked'}
for name,verdict in verdicts.items():
    facts=json.loads((OUT/('worker-rule-'+name)/'results.json').read_bytes())
    failed=[row['name'] for row in facts['checks'] if row['status']!='PASS']
    assert verdict['pass'] and verdict['mutated_backend_loaded'] and verdict['forbidden_outcome_observed']
    assert failed==verdict['failed_checks']==[verdict['contract']]
    assert facts['setup_complete'] and facts['cleanup_complete'] and len(facts['checks'])==14
    assert not facts.get('setup_or_probe_error') and not facts.get('cleanup_error')
    checks.append({'name':'mutant-'+name,'contract':verdict['contract'],'status':'PASS'})
previous=stage['previous_passes']
assert previous['source_revision']=='0f754a6dfd555568cb377affbbe52655a13d3d4d'
assert previous['runtime']==12 and previous['input-failures']==11 and previous['not_rerun'] and previous['product_files_unchanged']
diff=subprocess.check_output(['git','diff',previous['source_revision'],revision,'--','workbench/src','workbench/app','workbench/hooks'],cwd=ROOT)
assert not diff
result={'status':'PASS','scope':'保存结果的只读核对；未重跑、未启动，不是独立 reviewer','source_revision':revision,
        'checks':checks,'previous_passes':previous,'real_model_turns':0,'new_starts':0,
        'remaining':'真实 09A-3 clean/block、09B/09C、真实 IME、真登录和新候选独立 reviewer 未完成'}
with (BASE/'regression02-readback-09a3r.json').open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2)
print(json.dumps({'status':result['status'],'checks':len(checks),'new_starts':0},ensure_ascii=False))
