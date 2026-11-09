#!/usr/bin/env python3
"""Bounded review replay; writes only beneath the disposable review copy."""
import difflib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
REPO = Path('/Users/luckye/Documents/Code/a2a')
REL = Path('evidence/2026-11-08-batch34/T-249/terra')
OLD = Path('evidence/2026-11-09-batch35/T-249/review-terra-a5-01')
C = '6f7d0fd8e0731f51c425bbc22ff8ce8091355c35'
G = '4f63a989f5e2efbdc56a7c3d02eadb476e42a10b'
CHECKPOINT = 'c16489e2d435513a00bfa3b61ec2ae346549bfb0'
A4 = 'd9b75c077bbcc33ae9b77e7f188916d787f2c803'

def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(REPO), *args])

def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    assert json.loads(path.read_text(encoding='utf-8')) == value

def paths(rev):
    return [p.decode('utf-8') for p in git('ls-tree', '-r', '-z', '--name-only', rev, '--', str(REL)).split(b'\0') if p]

changed = git('diff', '--name-only', G, C).decode().splitlines()
checkpoint_paths = paths(CHECKPOINT)
candidate_paths = paths(C)
binding = {
    'candidate': C, 'base': G, 'checkpoint': CHECKPOINT,
    'method': 'Direct byte comparison of git show output; no hashes',
    'changed_paths': changed,
    'out_of_card': [p for p in changed if not p.startswith(str(REL) + '/')],
    'candidate_files': [{'path': p, 'bytes': len((ROOT / p).read_bytes()), 'equal': (ROOT / p).read_bytes() == git('show', C + ':' + p)} for p in candidate_paths],
    'checkpoint_files': [{'path': p, 'bytes': len((ROOT / p).read_bytes()), 'equal': (ROOT / p).read_bytes() == git('show', CHECKPOINT + ':' + p)} for p in checkpoint_paths],
    'recovery_additions': sorted(set(candidate_paths) - set(checkpoint_paths)),
    'checkpoint_change_paths': git('diff', '--name-only', CHECKPOINT + '^', CHECKPOINT).decode().splitlines(),
    'a4_files': [{'path': p, 'equal': (ROOT / p).read_bytes() == git('show', A4 + ':' + p)} for p in paths(A4)],
    'oracles': [],
}
for p in ['acceptance/T-249/check_git_graph.py', 'evidence/2026-11-08-batch34/T-249/controller/prepare-terra-fixture.py', 'REVIEW.md']:
    binding['oracles'].append({'path': p, 'candidate_equals_base': git('show', C + ':' + p) == git('show', G + ':' + p), 'copy_equals_candidate': (ROOT / p).read_bytes() == git('show', C + ':' + p)})
save(OUT / 'binding.json', binding)
assert len(checkpoint_paths) == 31 and len(candidate_paths) == 36
assert not binding['out_of_card']
assert all(r['equal'] for r in binding['candidate_files'] + binding['checkpoint_files'])
assert all(r['candidate_equals_base'] and r['copy_equals_candidate'] for r in binding['oracles'])
assert len(binding['checkpoint_change_paths']) == 5
print('binding: 36/36 candidate files; 31/31 checkpoint files; oracles unchanged', flush=True)

names = ['check_observations.py', 'check-parent-cases.py', 'replay-overlong.py', 'observations.json', 'git-facts.json', 'bad-parent.json', 'bad-untracked.json']
source = (ROOT / REL / 'check_observations.py').read_text(encoding='utf-8')
strict = "re.fullmatch(r'[0-9a-f]{10}', short) is not None and short == full[:10]"
assert source.count(strict) == 1

def setup(name, replacement=None):
    cwd = OUT / name
    target = cwd / REL
    target.mkdir(parents=True, exist_ok=False)
    for name in names:
        shutil.copyfile(ROOT / REL / name, target / name)
    if replacement is not None:
        changed_source = source.replace(strict, replacement)
        (target / 'check_observations.py').write_text(changed_source, encoding='utf-8')
        (cwd / 'change.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True), changed_source.splitlines(True), fromfile='candidate', tofile='mutant')), encoding='utf-8')
    return cwd

def run(cwd, argv):
    p = subprocess.run(argv, cwd=cwd, text=True, encoding='utf-8', capture_output=True, timeout=60)
    return {'cwd': str(cwd), 'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}

checker_cmd = ['/usr/bin/python3', str(REL / 'check_observations.py')]
cases_cmd = ['/usr/bin/python3', str(REL / 'check-parent-cases.py')]
baseline = setup('candidate')
# First replay the six counterexamples preserved by the previous independent review.
prior = []
for p in sorted((ROOT / OLD / 'overlong-counterexamples').glob('*.json')):
    if p.name == 'results.json':
        continue
    result = run(baseline, checker_cmd + [str(p)])
    assertion = 'FAIL 普通提交和父提交' if p.name.startswith('normal') else 'FAIL 合并哈希和两个父提交'
    result['required_assertion'] = assertion
    result['passed'] = result['exit'] == 1 and assertion in result['stdout'] and not result['stderr']
    prior.append(result)
save(OUT / 'prior-counterexamples.json', prior)
assert len(prior) == 6 and all(r['passed'] for r in prior)
print('previous independent counterexamples: 6/6 rejected by business assertion', flush=True)

base_runs = [run(baseline, checker_cmd), run(baseline, cases_cmd)]
save(OUT / 'candidate-runs.json', base_runs)
assert all(r['exit'] == 0 and not r['stderr'] for r in base_runs)
base_cases = json.loads((baseline / REL / 'parent-cases-results.json').read_text(encoding='utf-8'))
assert len(base_cases) == 24 and all(r['passed'] for r in base_cases)
print('candidate completion: 0, 0; 24/24 cases', flush=True)

replay = run(baseline, ['/usr/bin/python3', str(REL / 'replay-overlong.py'), 'after'])
save(OUT / 'replay-run.json', replay)
assert replay['exit'] == 0 and not replay['stderr']
replayed = json.loads((baseline / REL / 'overlong-after.json').read_text(encoding='utf-8'))
for kind, expected_cases_exit, expected_long in [('original', 0, 1), ('mutant', 1, 0)]:
    runs = replayed['runs'][kind]
    assert runs[0]['exit'] == 0 and runs[1]['exit'] == expected_cases_exit
    assert [r['exit'] for r in runs[2:]] == [expected_long] * 6
    assert all(not r['stderr'] for r in runs)
print(replay['stdout'], end='', flush=True)

mutants = []
for name, replacement, failure_count in [
    ('M5-overlong', "re.fullmatch(r'[0-9a-f]{10,}', short) is not None and short[:10] == full[:10]", 6),
    ('M1-startswith', 'full.startswith(short)', 13),
]:
    cwd = setup(name, replacement)
    runs = [run(cwd, checker_cmd), run(cwd, cases_cmd)]
    save(cwd / 'runs.json', runs)
    cases = json.loads((cwd / REL / 'parent-cases-results.json').read_text(encoding='utf-8'))
    failed = [r['case'] for r in cases if not r['passed']]
    item = {'mutation': name, 'replacement': replacement, 'runs': runs, 'failed_cases': failed}
    mutants.append(item)
    assert runs[0]['exit'] == 0 and runs[1]['exit'] == 1
    assert len(failed) == failure_count and all(not r['stderr'] for r in cases)
    print(name, 'completion exits:', [r['exit'] for r in runs], 'failed cases:', failed, flush=True)
save(OUT / 'mutation-summary.json', mutants)

integrity = [{'path': p, 'unchanged': (ROOT / p).read_bytes() == git('show', C + ':' + p)} for p in candidate_paths]
save(OUT / 'final-integrity.json', integrity)
assert all(r['unchanged'] for r in integrity)
print('original candidate copy: 36/36 files remain byte-identical', flush=True)
