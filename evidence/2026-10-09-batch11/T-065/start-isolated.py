"""Reuse the T-057 setup in a new T-065 home; no live provider is started."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
label = sys.argv[1]
root = Path('/Volumes/WD-Elements/dev-cache/synara/instances') / ('t065-' + label)
root.mkdir(mode=0o700)
env = {k: v for k, v in os.environ.items() if k in ['PATH', 'SHELL', 'LANG', 'LC_ALL']}
for name in ['os-home', 'codex-empty', 'claude-empty']:
    (root / name).mkdir()
env.update(HOME=str(root/'os-home'), CODEX_HOME=str(root/'codex-empty'), CLAUDE_CONFIG_DIR=str(root/'claude-empty'),
           A2A_SYNARA_SLOT='t065-'+label, T057_ROOT=str(root), T057_FORK=str(fork),
           T055_ROOT=str(root), T055_FORK=str(fork), T055_PORT='8077', T055_WEB='http://localhost:8078',
           SYNARA_PORT_OFFSET='1717')
t057 = out.parent / 'T-057'
t055 = out.parents[1] / '2026-10-09-batch8/T-055'
if len(sys.argv)>2 and sys.argv[2]=='baseline': env['T065_BASELINE'] = '1'
if len(sys.argv)>2 and sys.argv[2]=='no-panel': env['T065_NO_ISSUES'] = '1'
record = {'source_revision': 'e94a0efc3' if env.get('T065_BASELINE') else None, 'root': str(root), 'processes': [], 'environment': env,
          'fork_revision': subprocess.check_output(['git', '-C', str(fork), 'rev-parse', 'HEAD'], text=True).strip()}
def run(argv, name, background=False):
    entry = {'argv': argv, 'name': name, 'cwd': str(fork)}
    record['processes'].append(entry)
    with (out / (label+'-'+name+'.log')).open('x', encoding='utf-8') as log:
        if background:
            p = subprocess.Popen(argv, cwd=fork, env=env, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True, stdin=subprocess.DEVNULL)
            entry['pid'] = p.pid
            entry['lstart'] = subprocess.check_output(['ps', '-p', str(p.pid), '-o', 'lstart='],
                                                     env={**env, 'LC_ALL': 'C'}, text=True).strip()
        else:
            p = subprocess.run(argv, cwd=fork, env=env, stdout=log, stderr=subprocess.STDOUT)
            entry['exit'] = p.returncode
            if p.returncode: raise RuntimeError(name)
try:
    run(['./a2a/scripts/bun', 'run', 'dev', '--dry-run'], 'dry-run')
    run(['./a2a/scripts/bun', 'run', str(out/'seed-fixture.ts')], 'seed')
    run(['./a2a/scripts/bun', 'run', str(t055/'server-fixture.ts')], 'server', True)
    deadline = time.monotonic()+55
    while not (root/'ready.json').exists() and time.monotonic()<deadline: time.sleep(.2)
    if not (root/'ready.json').exists(): raise TimeoutError('isolated server')
    spec = importlib.util.spec_from_file_location('fixture_api', t055/'fixture-api.py')
    api = importlib.util.module_from_spec(spec); spec.loader.exec_module(api)
    fixture = api.Fixture(root)
    seed = json.loads((root/'seed.json').read_text(encoding='utf-8'))
    task = seed['state']['task']; attempt = task['current_attempt']
    fixture.control('command', command={'type':'project.create', 'commandId':str(uuid.uuid4()), 'projectId':task['project_id'],
                    'title':'T065 隔离项目', 'workspaceRoot':task['repo'], 'createdAt':'2026-10-09T13:00:00Z'})
    fixture.control('command', command={'type':'thread.create', 'commandId':str(uuid.uuid4()), 'threadId':attempt['thread_id'],
                    'projectId':task['project_id'], 'title':'T065 浮层验证', 'modelSelection':{'provider':'codex','model':'gpt-6.1-sol','options':{'reasoningEffort':'xhigh','fastMode':True}},
                    'runtimeMode':'approval-required','interactionMode':'default','envMode':'worktree',
                    'branch':None,'worktreePath':attempt['workspace'],'createdAt':'2026-10-09T13:00:00Z'})
    run(['./a2a/scripts/bun', 'run', str(out/'web-fixture.ts')], 'web', True)
    deadline = time.monotonic()+30
    while not (root/'web-ready.json').exists() and time.monotonic()<deadline: time.sleep(.2)
    if not (root/'web-ready.json').exists(): raise TimeoutError('isolated web')
    record['ready'] = True
finally:
    with (out/(label+'-launch.json')).open('x',encoding='utf-8') as file:
        json.dump(record,file,ensure_ascii=False,indent=2);file.write('\n')
print(json.dumps({'root':str(root),'origin':'http://127.0.0.1:8077','web':'http://localhost:8078'},ensure_ascii=False))
