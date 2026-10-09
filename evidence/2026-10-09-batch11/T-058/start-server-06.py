import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time

out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
label = sys.argv[1]
assert label.replace('-', '').replace('_', '').isalnum()
root = Path('/Volumes/WD-Elements/dev-cache/synara/instances/s11-t058-' + label)
root.mkdir(mode=0o700)
for name in ['os-home', 'codex-empty', 'claude-empty']:
    (root / name).mkdir(mode=0o700)
env = {k: v for k, v in os.environ.items() if k in ['PATH', 'SHELL', 'LANG', 'LC_ALL']}
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fork, text=True).strip()
env.update(HOME=str(root/'os-home'), CODEX_HOME=str(root/'codex-empty'), CLAUDE_CONFIG_DIR=str(root/'claude-empty'),
    A2A_SYNARA_SLOT='s11-t058-' + label, T058_ROOT=str(root), T058_FORK=str(fork), T058_SOURCE_REVISION=revision)
argv = ['./a2a/scripts/bun', 'run', str(out/'server-fixture-05.ts')]
log_path = root/'private-server.log' if label.startswith('real') else out/('server-' + label + '.log')
with log_path.open('x', encoding='utf-8') as log:
    process = subprocess.Popen(argv, cwd=fork, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
with (out / ('server-' + label + '-launch.json')).open('x', encoding='utf-8') as stream:
    json.dump(dict(argv=argv, cwd=str(fork), pid=process.pid, root=str(root), environment=env, source_revision=revision,
        log_path=str(log_path), tracked_status=subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=fork, text=True),
        started=dt.datetime.now(dt.timezone.utc).isoformat()), stream, indent=2)
for _ in range(450):
    if (root/'ready.json').exists():
        print((root/'ready.json').read_text(encoding='utf-8')); break
    if process.poll() is not None: raise RuntimeError('Fixture exited; raw log retained')
    time.sleep(.1)
else: raise TimeoutError('Fixture ready')
