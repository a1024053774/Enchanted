"""Restart the already stopped, task-owned fixture without re-seeding its data."""
import json
import subprocess
from pathlib import Path
import time
import sys

out=Path(__file__).resolve().parent
label=sys.argv[1] if len(sys.argv)>1 else 'restart01'
old=json.loads((out/'current-launch.json').read_text(encoding='utf-8'))
record={**old,'processes':[]}
for entry in old['processes']:
    if 'pid' not in entry: continue
    alive=subprocess.run(['ps','-p',str(entry['pid']),'-o','stat='],text=True,capture_output=True)
    if alive.returncode==0 and not alive.stdout.strip().startswith('Z'):
        raise RuntimeError('An old fixture PID remains; refusing duplicate startup')
    with (out/(label+'-'+entry['name']+'.log')).open('x',encoding='utf-8') as log:
        process=subprocess.Popen(entry['argv'],cwd=entry['cwd'],env=old['environment'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,stdin=subprocess.DEVNULL)
    new={**entry,'pid':process.pid,'lstart':subprocess.check_output(['ps','-p',str(process.pid),'-o','lstart='],env={**old['environment'],'LC_ALL':'C'},text=True).strip()}
    record['processes'].append(new)
    ready=Path(old['root'])/('ready.json' if entry['name']=='server' else 'web-ready.json')
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        if ready.exists() and json.loads(ready.read_text())['pid']==process.pid: break
        if process.poll() is not None: raise RuntimeError('Fixture ended during restart')
        time.sleep(.2)
    else: raise TimeoutError('Fixture restart readiness')
with (out/(label+'-launch.json')).open('x',encoding='utf-8') as file:
    json.dump(record,file,ensure_ascii=False,indent=2);file.write('\n')
print(json.dumps({'root':record['root'],'processes':record['processes']},ensure_ascii=False))
