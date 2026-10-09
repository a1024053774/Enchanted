import json, os, subprocess, time, sys
from pathlib import Path
out=Path(__file__).resolve().parent
label=sys.argv[1] if len(sys.argv)>1 else 'red-matrix-02'
assert label.replace('-','').replace('_','').isalnum(), label
root=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t056-'+label)
root.mkdir(mode=0o700)
for name in ('os-home','codex-empty','claude-empty'): (root/name).mkdir(mode=0o700)
env={k:v for k,v in os.environ.items() if k in ('PATH','SHELL','LANG','LC_ALL')}
env.update(HOME=str(root/'os-home'),CODEX_HOME=str(root/'codex-empty'),CLAUDE_CONFIG_DIR=str(root/'claude-empty'),A2A_SYNARA_SLOT='t056-'+label,T056_ROOT=str(root),T056_FORK='/Users/luckye/Documents/Code/synara')
argv=['./a2a/scripts/bun','run',str(out/'server-fixture-02.ts')]
with (out/('server-'+label+'.log')).open('x') as log:
    p=subprocess.Popen(argv,cwd=env['T056_FORK'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
with (out/('server-'+label+'-launch.json')).open('x',encoding='utf-8') as file:
    file.write(json.dumps(dict(argv=argv,pid=p.pid,root=str(root),environment=env),indent=2)+'\n')
for _ in range(450):
    if (root/'ready.json').exists():
        print((root/'ready.json').read_text()); break
    if p.poll() is not None: raise RuntimeError('server stopped; inspect original log')
    time.sleep(.1)
else: raise TimeoutError('server ready')
