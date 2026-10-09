import json, os, subprocess, sys
from pathlib import Path

out = Path(__file__).resolve().parent
label = sys.argv[1]
root = Path('/Volumes/WD-Elements/dev-cache/synara/instances') / ('t055-' + label)
if len(sys.argv) > 4:
    root = Path(sys.argv[4]).resolve()
    assert str(root).startswith('/Volumes/WD-Elements/dev-cache/synara/instances/t055-')
root.mkdir(mode=0o700, exist_ok=True)
for name in ['os-home', 'codex-empty', 'claude-empty']:
    (root/name).mkdir(exist_ok=True)
env = {k:v for k,v in os.environ.items() if k in ['PATH','SHELL','LANG','LC_ALL']}
env.update(HOME=str(root/'os-home'), CODEX_HOME=str(root/'codex-empty'),
    CLAUDE_CONFIG_DIR=str(root/'claude-empty'), A2A_SYNARA_SLOT='t055-'+label,
    T055_ROOT=str(root), T055_FORK='/Users/luckye/Documents/Code/synara')
if len(sys.argv) > 2:
    env.update(T055_PORT=sys.argv[2], T055_WEB='http://localhost:'+sys.argv[3])
argv = ['./a2a/scripts/bun', 'run', str(out/'server-fixture.ts')]
with (out/('server-'+label+'.log')).open('x') as log:
    process = subprocess.Popen(argv, cwd=env['T055_FORK'], env=env, stdout=log,
        stderr=subprocess.STDOUT, start_new_session=True, stdin=subprocess.DEVNULL)
with (out/('server-'+label+'-launch.json')).open('x',encoding='utf-8') as file:
    json.dump({'argv':argv,'pid':process.pid,'root':str(root),'environment':env}, file, indent=2)
    file.write('\n')
print(process.pid)
