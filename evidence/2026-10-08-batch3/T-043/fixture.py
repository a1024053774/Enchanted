#!/usr/bin/env python3
"""Build the T-043 fixture on the t043 instance: pagination repo, a real gate task driven to a real
oracle failure, one project, three threads, one membership. No model turn is started."""
import json, os, shutil, subprocess, tempfile, uuid
from pathlib import Path
here = Path(__file__).resolve().parent
record = here / 'fixture.json'
assert not record.exists(), 'fixture already exists; keep its evidence'
a2a = Path('/Users/luckye/Documents/Code/a2a'); checkout = Path('/Users/luckye/Documents/Code/synara')
inst = Path('/Volumes/WD-Elements/dev-cache/synara/instances/t043')
state = inst / 'home/dev/a2a-gates'
root = Path(tempfile.mkdtemp(prefix='ui-', dir=str((inst / 'fixtures').resolve()) if (inst / 'fixtures').exists() or (inst / 'fixtures').mkdir() is None else None))
repo = root / 'pagination repo'; repo.mkdir()
genv = {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_TERMINAL_PROMPT': '0', 'PYTHONDONTWRITEBYTECODE': '1'}
for k in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR', 'GIT_CONFIG_COUNT'): genv.pop(k, None)
log = []
def run(argv, cwd=None, env=None, ok=(0,)):
    p = subprocess.run(argv, cwd=cwd, env=env or genv, text=True, capture_output=True, timeout=180)
    log.append({'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    assert p.returncode in ok, (argv, p.stdout, p.stderr)
    return p
def git(*a, repo_=None): return run(['git', '-C', str(repo_ or repo), *a]).stdout.strip()
git('init'); git('config', 'user.name', 'T-043 fixture'); git('config', 'user.email', 't043@example.invalid'); git('config', 'commit.gpgsign', 'false')
shutil.copyfile(a2a / 'fixtures/pagination/pager.py', repo / 'pager.py'); shutil.copyfile(a2a / 'fixtures/pagination/CONTRACT.md', repo / 'CONTRACT.md')
git('add', '--', 'pager.py', 'CONTRACT.md'); git('commit', '-m', 'Independent faulty pagination starter'); base = git('rev-parse', 'HEAD')
shutil.copyfile(a2a / 'acceptance/pagination_oracle.py', root / 'oracle.py'); shutil.copyfile(a2a / 'fixtures/pagination/CONTRACT.md', root / 'instructions.txt')
task = 't043-' + uuid.uuid4().hex[:12]
genv['A2A_SYNARA_SLOT'] = 't043'
def gate(*a, ok=(0,)):
    p = run(['./a2a/scripts/bun', 'packages/a2a-gates/src/cli.ts', '--state', str(state), *a], cwd=checkout, ok=ok)
    return json.loads(p.stdout)
gate('create', '--task', task, '--repo', str(repo), '--base', base, '--oracle', str(root / 'oracle.py'), '--instructions', str(root / 'instructions.txt'))
claim = gate('claim', '--task', task, '--owner', 't043-ui-fixture')['attempt']
ws = Path(claim['workspace']); assert ws.resolve().is_relative_to((state / 'worktrees').resolve())
(ws / 'candidate-note.txt').write_text('Known-bad starter retained for UI failure evidence.\n', encoding='utf-8')
for a in (['config', 'user.name', 'T-043 fixture'], ['config', 'user.email', 't043@example.invalid'], ['config', 'commit.gpgsign', 'false'],
          ['add', '--', 'pager.py', 'candidate-note.txt'], ['-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'T-043 known-bad candidate']): git(*a, repo_=ws)
commit = git('rev-parse', 'HEAD', repo_=ws)
gate('submit', '--task', task, '--attempt', claim['attempt_id'], '--session', claim['session_id'], '--fence', str(claim['fence']), '--spec-rev', str(claim['spec_rev']), '--commit', commit)
verify = gate('verify', '--task', task, '--attempt', claim['attempt_id'], ok=(1,))
assert verify['error'] == 'oracle_failed', verify
result = {'root': str(root), 'repo': str(repo), 'task': task, 'project': task, 'base': base, 'attempt': claim, 'commit': commit,
          'threads': {'worker': task + '-worker', 'reviewer': task + '-reviewer', 'monitor': task + '-monitor'}, 'commands': log}
record.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(task)
