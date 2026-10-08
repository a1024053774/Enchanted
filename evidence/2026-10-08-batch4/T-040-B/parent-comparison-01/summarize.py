#!/usr/bin/env python3
"""Check comparison completeness and report the controller's decision rule."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
rows = [json.loads(line) for line in (out / 'results.jsonl').read_text(encoding='utf-8').splitlines()]
expected_files = {
    'src/appSnapManager.test.ts', 'src/cuaDriverHost.test.ts', 'src/macAppIcon.native.test.ts',
    'src/orchestration/Layers/ProviderCommandReactor.test.ts',
}
expected = {(file, kind, round_number) for file in expected_files for kind in ('parent','candidate') for round_number in (1,2,3)}
actual = {(r['test_file'],r['kind'],r['round']) for r in rows}
assert len(rows) == 24 and actual == expected
commands = [json.loads(line) for line in (out/'commands.jsonl').read_text(encoding='utf-8').splitlines()]
tests = [r for r in commands if r['event']=='start' and not r['label'].startswith('install-')]
for offset in range(0,len(tests),2):
    assert tests[offset]['label'].endswith('parent') and tests[offset+1]['label'].endswith('candidate')
for previous,next_row in zip(rows,rows[1:]):
    assert previous['ended'] <= next_row['started'], 'tests overlapped'
assert all(not r['A_overlap_observed'] for r in rows)
titles = [
    ('src/appSnapManager.test.ts','retains a full composer batch and reports any overflow'),
    ('src/cuaDriverHost.test.ts','retires a cached native process once when grants change, then requires fresh observation'),
    ('src/macAppIcon.native.test.ts','keeps a custom icon after the writer exits and removes it for Default'),
    ('src/orchestration/Layers/ProviderCommandReactor.test.ts','keeps an operator retried slow cache response alive beyond the command deadline'),
    ('src/orchestration/Layers/ProviderCommandReactor.test.ts','keeps slow cancel-follow-up alive beyond the command deadline while another chat sends'),
]
cases=[]
for file,title in titles:
    item={'file':file,'title':title}
    for kind in ('parent','candidate'):
        statuses=[]
        for round_number in (1,2,3):
            row=next(r for r in rows if (r['test_file'],r['kind'],r['round'])==(file,kind,round_number))
            document=json.loads((out/(row['label']+'.json')).read_text(encoding='utf-8'))
            assertions=[a for f in document['testResults'] for a in f['assertionResults'] if a['title']==title]
            assert len(assertions)==1, (file,title,kind,round_number)
            statuses.append(assertions[0]['status'])
        item[kind]=statuses
    if item['parent']==['passed']*3 and 'failed' in item['candidate']:
        item['classification']='candidate regression signal; diagnosis required'
    elif item['parent']==item['candidate'] and item['parent']==['passed']*3:
        item['classification']='both pass; original workspace failure not reproduced'
    elif item['parent']==item['candidate']:
        item['classification']='same baseline/candidate failure or instability'
    elif 'failed' in item['parent']:
        item['classification']='baseline failure observed; compare failure details before classification'
    else:
        item['classification']='unresolved difference'
    cases.append(item)
summary={'runs':len(rows),'alternating_serial':True,'A_overlap_observed':False,
         'file_runs':[{'file':file,'parent':[r['exit'] for r in rows if r['test_file']==file and r['kind']=='parent'],
                      'candidate':[r['exit'] for r in rows if r['test_file']==file and r['kind']=='candidate']} for file in sorted(expected_files)],
         'original_five_cases':cases}
regressions=[]
for file in sorted(expected_files):
    groups={}
    for row in [r for r in rows if r['test_file']==file]:
        document=json.loads((out/(row['label']+'.json')).read_text(encoding='utf-8'))
        for f in document['testResults']:
            for assertion in f['assertionResults']:
                groups.setdefault(assertion['fullName'],{'parent':[],'candidate':[]})[row['kind']].append(assertion['status'])
    for name,statuses in groups.items():
        if statuses['parent'] and all(s=='passed' for s in statuses['parent']) and 'failed' in statuses['candidate']:
            regressions.append({'file':file,'case':name,**statuses})
summary['candidate_regression_signals_all_cases']=regressions
with (out/'summary.json').open('x',encoding='utf-8') as stream:
    json.dump(summary,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
