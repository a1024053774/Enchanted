"""Independent T-044 HTTP contract inputs. Never write membership directly."""
import json, os, shutil, subprocess, sys, tempfile, urllib.request, urllib.error, uuid
from pathlib import Path

here = Path(__file__).resolve().parent
label, mode = sys.argv[1:]
run = here / label
run.mkdir()
instance = Path('/Volumes/WD-Elements/dev-cache/synara/instances/t044')
fixtures = instance / 'fixtures'
fixtures.mkdir(exist_ok=True)
root = Path(tempfile.mkdtemp(prefix=label + '-', dir=fixtures))
repo = root / 'repo'
repo.mkdir()
env = {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_TERMINAL_PROMPT': '0'}
for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR', 'GIT_CONFIG_COUNT'):
    env.pop(key, None)
trace = run / 'trace.jsonl'
def record(value):
    with trace.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + '\n')
def git(*args):
    argv = ['git', '-C', str(repo), *args]
    result = subprocess.run(argv, env=env, capture_output=True, text=True, check=True)
    record({'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    return result.stdout.strip()
git('init'); git('config', 'user.name', 'T-044 fixture'); git('config', 'user.email', 't044@example.invalid')
git('config', 'commit.gpgsign', 'false')
(repo / 'input.txt').write_text('Independent fixture ' + uuid.uuid4().hex + '\n', encoding='utf-8')
git('add', '--', 'input.txt'); git('-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'Independent task window fixture')
base = git('rev-parse', 'HEAD')
(root / 'oracle.py').write_text('raise SystemExit(0)\n', encoding='utf-8')
(root / 'instructions.txt').write_text('T-044 isolated protocol fixture. No model calls.\n', encoding='utf-8')
task = 't044-' + uuid.uuid4().hex[:12]
title = '门禁自动归属 ' + label
endpoint = 'http://127.0.0.1:5817'
def request(path, body=None):
    req = urllib.request.Request(endpoint + path, data=None if body is None else json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            status, raw = response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read().decode()
    record({'path': path, 'input': body, 'status': status, 'output': json.loads(raw)})
    return json.loads(raw)
def gate(command, **args): return request('/api/a2a', {'command': command, 'task': task, **args})
created = gate('create', title=title, project=task + '-project', repo=str(repo), base=base,
    oracle=str(root / 'oracle.py'), instructions=str(root / 'instructions.txt'))
assert created['ok'], created
memberships = request('/api/a2a/membership')
membership = next((item for item in memberships['tasks'] if item['taskId'] == task), None)
dispatched = None
if mode != 'red':
    dispatched = gate('dispatch', runtimeMode='approval-required')
role = os.environ.get('T044_ROLE', 'reviewer')
model = os.environ.get('T044_MODEL', 'gpt-6.1-sol')
attached = gate('attach', role=role, modelSelection={'provider': 'codex', 'model': model,
    'options': {'reasoningEffort': 'high', 'fastMode': True}}, runtimeMode='approval-required',
    instructions=str(root / 'instructions.txt'))
(run / 'fixture.json').write_text(json.dumps({'root': str(root), 'repo': str(repo), 'base': base,
    'task': task, 'title': title, 'created': created, 'membership': membership, 'attached': attached,
    'dispatched': dispatched}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if mode == 'red':
    assert membership is None and attached['ok'] is False, (membership, attached)
    print('EXPECTED RED: create has no membership; attach is unavailable')
else:
    assert membership is not None and membership['title'] == title, membership
    assert attached['ok'], attached
    assert attached['attachment']['role'] == role and attached['attachment']['modelSelection']['model'] == model, attached
    print('PASS initial create + attach; dispatch result:', dispatched)
