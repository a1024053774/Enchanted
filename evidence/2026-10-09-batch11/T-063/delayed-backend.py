"""Delay only our recorded isolated backend, then read the real UI's recovery."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time

out = Path(__file__).resolve().parent
label = 'delayed01'
launch = json.loads((out/'probe01-launch.json').read_text(encoding='utf-8'))
fork = Path('/Users/luckye/Documents/Code/synara')
entry = next(e for e in launch['processes'] if e['name']=='server')
env = launch['environment']
identity = subprocess.check_output(['ps','-p',str(entry['pid']),'-o','lstart=','-o','command='],env={**env,'LC_ALL':'C'},text=True).strip()
if entry['lstart'] not in identity or entry['argv'][-1] not in identity:
    raise RuntimeError('Own server identity changed')
root = Path(launch['root'])
(out/(label+'-before-ready.json')).write_bytes((root/'ready.json').read_bytes())
os.kill(entry['pid'],signal.SIGTERM)
for _ in range(50):
    state=subprocess.run(['ps','-p',str(entry['pid']),'-o','stat='],capture_output=True,text=True)
    if state.returncode or state.stdout.strip().startswith('Z'): break
    time.sleep(.2)
else: raise RuntimeError('Own server did not stop')
record={'root':str(root),'stopped':{'pid':entry['pid'],'identity':identity},'processes':[]}
try:
    with (out/(label+'-ui.log')).open('x',encoding='utf-8') as log:
        argv=['./a2a/scripts/bun',str(out/'delayed-backend.mjs'),str(out),str(root),label]
        browser=subprocess.Popen(argv,cwd=fork,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        record['browserArgv']=argv
        deadline=time.monotonic()+80
        while not (out/(label+'-waiting.json')).exists():
            if browser.poll() is not None: raise RuntimeError('UI probe ended before delayed-start marker')
            if time.monotonic()>deadline: raise TimeoutError('UI delayed-start marker')
            time.sleep(.2)
        with (out/(label+'-server.log')).open('x',encoding='utf-8') as server_log:
            process=subprocess.Popen(entry['argv'],cwd=fork,env=env,stdout=server_log,stderr=subprocess.STDOUT,start_new_session=True,stdin=subprocess.DEVNULL)
            new_entry={'name':'server','argv':entry['argv'],'cwd':str(fork),'pid':process.pid,
                       'lstart':subprocess.check_output(['ps','-p',str(process.pid),'-o','lstart='],env={**env,'LC_ALL':'C'},text=True).strip()}
            record['processes'].append(new_entry)
        record['browserExit']=browser.wait(timeout=90)
finally:
    with (out/(label+'-launch.json')).open('x',encoding='utf-8') as file:
        json.dump(record,file,ensure_ascii=False,indent=2);file.write('\n')
print(json.dumps(record,ensure_ascii=False))
raise SystemExit(record['browserExit'])
