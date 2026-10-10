"""UI-only rerun on the same persisted candidate database; zero model turns."""
import json
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

out=Path(__file__).resolve().parent
source=out/sys.argv[1]; run=out/sys.argv[2]; run.mkdir()
launch=json.loads((source/'launch.json').read_text(encoding='utf-8'))
root=Path(launch['root']); fork=Path('/Users/luckye/Documents/Code/synara')
env=launch['isolated_environment'].copy()
with socket.socket() as bound:
    bound.bind(('127.0.0.1',0)); port=bound.getsockname()[1]
env['T058_WEB']='http://127.0.0.1:'+str(port);env['T066_WEB_PORT']=str(port)
def save(name,value):
    with (run/name).open('x',encoding='utf-8') as f: json.dump(value,f,ensure_ascii=False,indent=2)
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip()
assert revision==launch['revision'],'Candidate changed'
dry_argv=['./a2a/scripts/bun','run','dev','--dry-run']
dry=subprocess.run(dry_argv,cwd=fork,env=env,capture_output=True,text=True)
save('dry-run.json',dict(argv=dry_argv,exit_code=dry.returncode,stdout=dry.stdout,stderr=dry.stderr))
assert dry.returncode==0
(run/'ui-expectations.json').write_bytes((source/'ui-expectations.json').read_bytes())
ready=root/'ready.json'
if ready.exists():
    (run/'previous-ready.json').write_bytes(ready.read_bytes());ready.unlink()
argv=['./a2a/scripts/bun','run',str(out/'server-fixture.ts')]
with (run/'server.log').open('x',encoding='utf-8') as log:
    proc=subprocess.Popen(argv,cwd=fork,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save('launch.json',dict(argv=argv,pid=proc.pid,root=str(root),revision=revision,model_turns=0,source_data=sys.argv[1]))
    try:
        for _ in range(450):
            if ready.exists():break
            if proc.poll() is not None:raise RuntimeError('server exited')
            time.sleep(.1)
        else:raise TimeoutError('server ready')
        ui_argv=['./a2a/scripts/bun','run',str(out/'ui-probe.ts'),str(run),str(root)]
        ui=subprocess.run(ui_argv,cwd=fork,env=env,capture_output=True,text=True,timeout=180)
        save('ui-command.json',dict(argv=ui_argv,exit_code=ui.returncode,stdout=ui.stdout,stderr=ui.stderr,revision=revision))
        print('UI',ui.returncode)
        raise SystemExit(ui.returncode)
    finally:
        proc.send_signal(signal.SIGTERM)
        try:proc.wait(timeout=30)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
        save('shutdown.json',dict(pid=proc.pid,exit_code=proc.returncode))
