#!/usr/bin/env python3
"""Reproduce bounded parent-observation counterexamples against the checker."""
import copy
import json
import pathlib
import subprocess
import tempfile

root = pathlib.Path('evidence/2026-11-08-batch34/T-249/terra')
checker = root / 'check_observations.py'
good = json.loads((root / 'observations.json').read_text(encoding='utf-8'))
facts = json.loads((root / 'git-facts.json').read_text(encoding='utf-8'))
revs = [line.split() for line in facts['alpha_rev_list'].splitlines()]
cases = []
for field, index, expected in [('merge_parents', 0, revs[0][1]), ('merge_parents', 1, revs[0][2]), ('normal_parent', None, revs[1][1])]:
    wrong = ('0' if expected[0] != '0' else '1') + expected[1:10]
    for label, value in [('empty', ''), ('short', expected[:9]), ('overlong-11', expected[:11]), ('overlong-40', expected), ('nonhex', 'g' + expected[1:10]), ('wrong-valid', wrong)]:
        obs = copy.deepcopy(good)
        if index is None:
            obs[field] = value
        else:
            obs[field][index] = value
        cases.append((f'{field}-{index}-{label}', obs, {f'{field}' + (f'[{index}]' if index is not None else ''): value}, '普通提交和父提交' if index is None else '合并哈希和两个父提交'))
for label, parents in [('swapped', good['merge_parents'][::-1]), ('duplicate', [good['merge_parents'][0]] * 2)]:
    obs = copy.deepcopy(good)
    obs['merge_parents'] = parents
    cases.append((label, obs, {'merge_parents': parents}, '合并哈希和两个父提交'))
results = []
with tempfile.TemporaryDirectory(prefix='parent-cases-', dir=root) as tmp:
    for name, obs, difference, assertion in cases:
        path = pathlib.Path(tmp) / (name + '.json')
        path.write_text(json.dumps(obs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        cmd = ['/usr/bin/python3', str(checker), str(path)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        results.append({'case': name, 'difference_from': str(root / 'observations.json'), 'difference': difference, 'command': cmd, 'expected_exit': 1, 'actual_exit': p.returncode, 'required_assertion': 'FAIL ' + assertion, 'stdout': p.stdout, 'stderr': p.stderr, 'passed': p.returncode == 1 and 'FAIL ' + assertion in p.stdout})
    for name, path, expected, assertion in [('good', root / 'observations.json', 0, None), ('bad-parent', root / 'bad-parent.json', 1, 'FAIL 合并哈希和两个父提交'), ('bad-untracked', root / 'bad-untracked.json', 1, 'FAIL diff alpha/uncommitted/untracked.txt'), ('controller-empty', pathlib.Path('/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-249/controller-package/terra-bad-empty-parent.json'), 1, 'FAIL 合并哈希和两个父提交')]:
        cmd = ['/usr/bin/python3', str(checker), str(path)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        results.append({'case': name, 'input': str(path), 'command': cmd, 'expected_exit': expected, 'actual_exit': p.returncode, 'required_assertion': assertion, 'stdout': p.stdout, 'stderr': p.stderr, 'passed': p.returncode == expected and (assertion is None or assertion in p.stdout) and (name != 'controller-empty' or 'FAIL 普通提交和父提交' in p.stdout)})
(root / 'parent-cases-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f"{sum(r['passed'] for r in results)}/{len(results)} cases passed; details: {root / 'parent-cases-results.json'}")
raise SystemExit(not all(r['passed'] for r in results))
