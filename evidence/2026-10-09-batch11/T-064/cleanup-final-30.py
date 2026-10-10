import json
import os
from pathlib import Path
import signal
import subprocess
import tarfile
import time
out=Path(__file__).resolve().parent
web=json.loads((out/'web-final22-launch.json').read_text(encoding='utf-8'));root=Path(web['root'])
ready=json.loads((root/'web-ready.json').read_text(encoding='utf-8'));assert ready['pid']==web['pid']
identity=subprocess.check_output(['ps','-p',str(web['pid']),'-o','command='],text=True).strip();assert web['argv'][-1] in identity
os.kill(web['pid'],signal.SIGTERM)
for _ in range(200):
    p=subprocess.run(['ps','-p',str(web['pid']),'-o','stat='],capture_output=True,text=True)
    if p.returncode!=0 or p.stdout.strip().startswith('Z'):break
    time.sleep(.1)
else:raise TimeoutError('Owned web did not stop')
p=subprocess.run(['python3',str(out/'stop-server-04.py'),'final27'],capture_output=True,text=True);assert p.returncode==0,p.stderr
roots=[root,Path(json.loads((out/'server-final27-launch.json').read_text(encoding='utf-8'))['root'])]
for prefix in ('final23','final28'):
    for suite in ('orchestration','delivery-recovery'):
        roots.append(Path(json.loads((out/(prefix+'-'+suite)/'command.json').read_text(encoding='utf-8'))['artifacts']))
excluded=[]
def select(info):
    if info.name.endswith('.token') or any(part.startswith('browser-') or part in ('os-home','claude-empty','codex-empty') for part in Path(info.name).parts):
        excluded.append(info.name);return None
    return info
with tarfile.open(out/'retained-final-fixtures-30.tar.gz','x:gz') as tar:
    for path in roots:tar.add(path,arcname=path.name,filter=select)
with (out/'cleanup-final-30.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(web_pid=web['pid'],verified_web_identity=identity,server_stop=p.stdout,roots=[str(path) for path in roots],excluded=excluded,
        original_roots_retained=True,new_model_turns=0,new_auth_copies=0),stream,ensure_ascii=False,indent=2)
print('PASS all owned services stopped; final SQLite/Git/control artifacts retained without credentials or profiles')
