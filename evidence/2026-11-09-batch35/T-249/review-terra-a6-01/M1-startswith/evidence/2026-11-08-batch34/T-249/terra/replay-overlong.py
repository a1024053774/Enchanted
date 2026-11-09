#!/usr/bin/env python3
"""Run the parent checks against isolated original and overlong-prefix mutant copies."""
import copy
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

root = pathlib.Path('evidence/2026-11-08-batch34/T-249/terra')
stage = sys.argv[1]
if stage not in ('before', 'after'):
    raise SystemExit('usage: replay-overlong.py before|after')
out = root / ('overlong-' + stage + '.json')
if out.exists():
    raise SystemExit('refusing to overwrite evidence: ' + str(out))
original = "re.fullmatch(r'[0-9a-f]{10}', short) is not None and short == full[:10]"
mutant = "re.fullmatch(r'[0-9a-f]{10,}', short) is not None and short[:10] == full[:10]"
results = {'stage': stage, 'mutation': {'from': original, 'to': mutant}, 'runs': {}}
with tempfile.TemporaryDirectory(prefix='overlong-replay-', dir=root.resolve()) as temp:
    temp = pathlib.Path(temp)
    target = temp / root
    target.mkdir(parents=True)
    for name in ('check_observations.py', 'check-parent-cases.py', 'observations.json', 'git-facts.json', 'bad-parent.json', 'bad-untracked.json'):
        shutil.copyfile(root / name, target / name)
    checker = target / 'check_observations.py'
    src = checker.read_text(encoding='utf-8')
    assert src.count(original) == 1
    facts = json.loads((target / 'git-facts.json').read_text(encoding='utf-8'))
    good = json.loads((target / 'observations.json').read_text(encoding='utf-8'))
    revs = [line.split() for line in facts['alpha_rev_list'].splitlines()]
    for kind in ('original', 'mutant'):
        checker.write_text(src if kind == 'original' else src.replace(original, mutant), encoding='utf-8')
        runs = []
        for command in (['/usr/bin/python3', str(root / 'check_observations.py')], ['/usr/bin/python3', str(root / 'check-parent-cases.py')]):
            p = subprocess.run(command, cwd=temp, capture_output=True, text=True)
            run = {'cwd': str(temp), 'argv': command, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
            if command[-1].endswith('check-parent-cases.py'):
                run['cases'] = json.loads((target / 'parent-cases-results.json').read_text(encoding='utf-8'))
            runs.append(run)
        for field, index, full in [('merge_parents', 0, revs[0][1]), ('merge_parents', 1, revs[0][2]), ('normal_parent', None, revs[1][1])]:
            for length in (11, 40):
                obs = copy.deepcopy(good)
                if index is None:
                    obs[field] = full[:length]
                else:
                    obs[field][index] = full[:length]
                path = target / f'input-{field}-{index}-{length}.json'
                path.write_text(json.dumps(obs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                command = ['/usr/bin/python3', str(root / 'check_observations.py'), str(path.relative_to(temp))]
                p = subprocess.run(command, cwd=temp, capture_output=True, text=True)
                runs.append({'cwd': str(temp), 'argv': command, 'difference': {field + (f'[{index}]' if index is not None else ''): full[:length]}, 'expected_exit': 1, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
        results['runs'][kind] = runs
out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for kind, runs in results['runs'].items():
    print(kind, 'completion=', runs[0]['exit'], 'cases=', runs[1]['exit'], runs[1]['stdout'].strip(), 'overlong exits=', [r['exit'] for r in runs[2:]])
