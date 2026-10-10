import json
import os
from pathlib import Path
import subprocess
import sys
import time
out=Path(__file__).resolve().parent
fork=Path('/Users/luckye/Documents/Code/synara')
label=sys.argv[1]
launch=json.loads((out/('server-'+label+'-launch.json')).read_text(encoding='utf-8'))
root=Path(launch['root']);env=launch['environment'];env['T064_ROOT']=str(root)
dry_argv=['./a2a/scripts/bun','run','dev','--dry-run']
dry=subprocess.run(dry_argv,cwd=fork,env=env,capture_output=True,text=True)
assert dry.returncode==0 and str(root/'home') in dry.stdout+dry.stderr
argv=['./a2a/scripts/bun','run',str(out/'web-fixture-10.ts')]
with (out/('web-'+label+'.log')).open('x',encoding='utf-8') as log:
    process=subprocess.Popen(argv,cwd=fork,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
with (out/('web-'+label+'-launch.json')).open('x',encoding='utf-8') as stream:
    json.dump(dict(argv=argv,cwd=str(fork),pid=process.pid,root=str(root),dry_run=dict(argv=dry_argv,stdout=dry.stdout,stderr=dry.stderr)),stream,indent=2)
for _ in range(300):
    if (root/'web-ready.json').exists():
        print((root/'web-ready.json').read_text(encoding='utf-8'));break
    if process.poll() is not None:raise RuntimeError('Web fixture exited')
    time.sleep(.1)
else:raise TimeoutError('Web fixture')
