"""Stop only the two processes recorded by this task's isolated launcher."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

out = Path(__file__).resolve().parent
label = sys.argv[1]
launch = json.loads((out/(label+'-launch.json')).read_text(encoding='utf-8'))
records = []
for entry in reversed(launch['processes']):
    if 'pid' not in entry: continue
    pid = entry['pid']
    env = {**os.environ, 'LC_ALL':'C'}
    p = subprocess.run(['ps','-p',str(pid),'-o','lstart=','-o','command='], env=env, text=True, capture_output=True)
    identity = p.stdout.strip()
    expected_source = entry['argv'][-1]
    record = {'pid':pid,'identity':identity,'source':expected_source}
    records.append(record)
    if p.returncode:
        record['already_exited'] = True
        continue
    if entry['lstart'] not in identity or expected_source not in identity:
        raise RuntimeError('Process identity changed; refusing to stop '+str(pid))
    os.kill(pid,signal.SIGTERM)
    deadline = time.monotonic()+10
    while time.monotonic()<deadline:
        state = subprocess.run(['ps','-p',str(pid),'-o','stat='],text=True,capture_output=True)
        if state.returncode or state.stdout.strip().startswith('Z'): break
        time.sleep(.2)
    else: raise TimeoutError('Own process did not stop: '+str(pid))
    record['stopped'] = True
with (out/(label+'-stop.json')).open('x',encoding='utf-8') as file:
    json.dump(records,file,ensure_ascii=False,indent=2);file.write('\n')
print(json.dumps(records,ensure_ascii=False))
