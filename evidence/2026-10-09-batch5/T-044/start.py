"""Start only the isolated T-044 dev instance; never touch desktop outputs or user data."""
import json, os, subprocess, sys, time
from pathlib import Path

out = Path(__file__).resolve().parent
checkout = Path('/Users/luckye/Documents/Code/synara')
base = Path('/Volumes/WD-Elements/dev-cache/synara/instances/t044')
assert Path('/Volumes/WD-Elements').is_mount()
label = sys.argv[1]
log_path = out / f'dev-{label}.log'
assert not log_path.exists()
(base / 'home/dev').mkdir(parents=True, exist_ok=True)
settings_path = base / 'home/dev/settings.json'
if not settings_path.exists():
    settings = json.loads(Path('/Volumes/WD-Elements/dev-cache/synara/instances/t043/home/dev/settings.json').read_text())
    settings['settings']['enableProviderUpdateChecks'] = False
    for provider in settings['settings']['providers'].values():
        provider['enabled'] = False
    settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for directory in ['os-home', 'config', 'data', 'cache', 'codex', 'claude']:
    (base / directory).mkdir(exist_ok=True)
env = {'PATH': os.environ['PATH'], 'HOME': str(base / 'os-home'), 'SHELL': '/bin/sh',
       'ZDOTDIR': str(base / 'os-home'), 'XDG_CONFIG_HOME': str(base / 'config'),
       'XDG_DATA_HOME': str(base / 'data'), 'XDG_CACHE_HOME': str(base / 'cache'),
       'CODEX_HOME': str(base / 'codex'), 'CLAUDE_CONFIG_DIR': str(base / 'claude'),
       'A2A_SYNARA_SLOT': 't044', 'SYNARA_PORT_OFFSET': '2044'}
dry = subprocess.run(['./a2a/scripts/bun', 'run', 'dev', '--dry-run'], cwd=checkout, env=env, capture_output=True, text=True)
(out / f'dry-run-{label}.log').write_text(dry.stdout + dry.stderr)
assert dry.returncode == 0, dry.stderr
argv = ['./a2a/scripts/bun', 'run', 'dev']
with log_path.open('x') as log:
    process = subprocess.Popen(argv, cwd=checkout, env=env, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True, stdin=subprocess.DEVNULL)
(out / f'start-{label}.json').write_text(json.dumps({'argv': argv, 'cwd': str(checkout), 'pid': process.pid,
    'pgid': process.pid, 'time': time.time(), 'environment': env}, indent=2) + '\n')
print(process.pid)
