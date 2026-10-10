import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import tarfile
import time
out=Path(__file__).resolve().parent
web=json.loads((out/'web-final11-launch.json').read_text(encoding='utf-8'))
root=Path(web['root']);ready=json.loads((root/'web-ready.json').read_text(encoding='utf-8'))
assert ready['pid']==web['pid']
command=subprocess.check_output(['ps','-p',str(web['pid']),'-o','command='],text=True).strip()
assert web['argv'][-1] in command
os.kill(web['pid'],signal.SIGTERM)
for _ in range(200):
    p=subprocess.run(['ps','-p',str(web['pid']),'-o','stat='],capture_output=True,text=True)
    if p.returncode!=0 or p.stdout.strip().startswith('Z'):break
    time.sleep(.1)
else:raise TimeoutError('Owned web did not stop')
stop_argv=['python3',str(out/'stop-server-04.py'),'final11']
stopped=subprocess.run(stop_argv,cwd=out.parents[2],capture_output=True,text=True)
assert stopped.returncode==0,stopped.stderr
roots=[Path('/Volumes/WD-Elements/dev-cache/synara/instances/s11-t064-'+name) for name in ('red03','green05','final11','crash06','protocol02')]
for name in ('orchestration','delivery-recovery'):
    roots.append(Path(json.loads((out/('final12-'+name)/'command.json').read_text(encoding='utf-8'))['artifacts']))
excluded=[]
def select(info):
    parts=Path(info.name).parts
    if any(part.startswith('browser-') or part in ('os-home','claude-empty','codex-empty') for part in parts) or info.name.endswith('.token'):
        excluded.append(info.name);return None
    return info
archive=out/'retained-fixtures-16.tar.gz'
with tarfile.open(archive,'x:gz') as tar:
    for path in roots:tar.add(path,arcname=path.name,filter=select)
with (out/'cleanup-and-archive-16.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(created_at=dt.datetime.now(dt.timezone.utc).isoformat(),web_pid=web['pid'],web_identity=command,
        server_stop=dict(argv=stop_argv,stdout=stopped.stdout,stderr=stopped.stderr),archive=archive.name,roots=[str(path) for path in roots],
        excluded=excluded,original_roots_retained=True,new_auth_copies=0,new_model_turns=0),stream,ensure_ascii=False,indent=2)
print('PASS owned web/server stopped; fixture SQLite/Git/control state archived; originals retained; credentials and profiles excluded')
