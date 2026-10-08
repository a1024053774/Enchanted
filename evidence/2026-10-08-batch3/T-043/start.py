#!/usr/bin/env python3
"""Start an isolated Synara dev:web instance (slot t043, ports 5816/7776) from the fork checkout.
Fresh home; only settings.json is copied from the T-038 instance, with every provider disabled."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path
out = Path(__file__).resolve().parent
checkout = Path('/Users/luckye/Documents/Code/synara')
vol = Path('/Volumes/WD-Elements'); assert vol.is_mount()
base = vol / 'dev-cache/synara/instances/t043'
label = sys.argv[1]  # new log label each start; refuses to overwrite
log_path = out / f'vite-{label}.log'; assert not log_path.exists()
home = base / 'home'
if not (home / 'dev').exists():
    (home / 'dev').mkdir(parents=True)
    src = vol / 'dev-cache/synara/instances/t038/home/dev/settings.json'
    settings = json.loads(src.read_text())
    settings['settings']['enableProviderUpdateChecks'] = False
    for v in settings['settings']['providers'].values(): v['enabled'] = False
    (home / 'dev/settings.json').write_text(json.dumps(settings, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for d in ['os-home', 'config', 'data', 'cache', 'codex', 'claude']: (base / d).mkdir(exist_ok=True)
env = {'PATH': os.environ['PATH'], 'HOME': str(base / 'os-home'), 'SHELL': '/bin/sh', 'ZDOTDIR': str(base / 'os-home'),
       'XDG_CONFIG_HOME': str(base / 'config'), 'XDG_DATA_HOME': str(base / 'data'), 'XDG_CACHE_HOME': str(base / 'cache'),
       'CODEX_HOME': str(base / 'codex'), 'CLAUDE_CONFIG_DIR': str(base / 'claude'),
       'A2A_SYNARA_SLOT': 't043', 'SYNARA_PORT_OFFSET': '2043'}
dry = subprocess.run(['./a2a/scripts/bun', 'run', 'dev', '--dry-run'], cwd=checkout, env=env, capture_output=True, text=True)
(out / f'dry-run-{label}.log').write_text(dry.stdout + dry.stderr); assert dry.returncode == 0, dry.stderr
argv = ['./a2a/scripts/bun', 'run', 'dev']
with log_path.open('x') as log:
    p = subprocess.Popen(argv, cwd=checkout, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, stdin=subprocess.DEVNULL)
(out / f'start-{label}.json').write_text(json.dumps({'argv': argv, 'cwd': str(checkout), 'pid': p.pid, 'pgid': p.pid, 'time': time.time(), 'env_keys': sorted(env)}, indent=2) + '\n')
print('pid', p.pid)
