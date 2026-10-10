import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import time

out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
root = Path('/Volumes/WD-Elements/dev-cache/synara/instances/s11-t064-crash06')
root.mkdir(mode=0o700)
env = {k:v for k,v in os.environ.items() if k in ('PATH','SHELL','LANG','LC_ALL')}
env.update(A2A_SYNARA_SLOT='s11-t064-crash06', T064_CRASH_ROOT=str(root))
argv = ['./a2a/scripts/bun','run',str(out/'crash-child-06.ts')]
with (out/'crash-child-06.log').open('x',encoding='utf-8') as log:
    process = subprocess.Popen(argv,cwd=fork,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    until=time.monotonic()+20
    while not (root/'inside-transaction.json').exists() and time.monotonic()<until:
        if process.poll() is not None: raise RuntimeError('Injection failed; raw log retained')
        time.sleep(.05)
    marker=json.loads((root/'inside-transaction.json').read_text(encoding='utf-8'))
    assert marker['pid']==process.pid
    identity=subprocess.check_output(['ps','-p',str(process.pid),'-o','command='],text=True).strip()
    assert str(out/'crash-child-06.ts') in identity
    os.kill(process.pid,signal.SIGTERM)
    exit_code=process.wait(timeout=15)
read_argv=['./a2a/scripts/bun','run',str(out/'crash-read-06.ts')]
read=subprocess.run(read_argv,cwd=fork,env=env,capture_output=True,text=True,timeout=20)
record=dict(argv=argv,read_argv=read_argv,cwd=str(fork),env_override=env,marker=marker,verified_identity=identity,
    child_exit=exit_code,read_returncode=read.returncode,read_stdout=read.stdout,read_stderr=read.stderr,
    created_at=dt.datetime.now(dt.timezone.utc).isoformat())
with (out/'crash-transaction-06.json').open('x',encoding='utf-8') as stream:
    json.dump(record,stream,ensure_ascii=False,indent=2)
    stream.write('\n')
assert read.returncode==0,read.stderr
observed=json.loads(read.stdout)
worker=next(row for row in observed['settings']['roles'] if row['role']=='worker')
assert worker['revision']==0 and worker['custom'] is None
assert worker['effective']['capabilities']==['a2a:submit','a2a:raise']
assert observed['inputs']==[] and observed['settings']['changes']==[]
print('PASS interrupted actual CLI save after role write, restarted core shows configuration/input/audit all rolled back')
