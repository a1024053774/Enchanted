import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

out=Path(__file__).resolve().parent
for label in sys.argv[1:]:
 launch=json.loads((out/('server-'+label+'-launch.json')).read_text(encoding='utf-8'))
 root=Path(launch['root']);ready=json.loads((root/'ready.json').read_text(encoding='utf-8'))
 pid=launch['pid'];assert ready['pid']==pid
 env={**os.environ,'LC_ALL':'C'}
 row=subprocess.run(['ps','-p',str(pid),'-o','lstart=','-o','command='],env=env,capture_output=True,text=True)
 if row.returncode:
  result=dict(pid=pid,already_exited=True,root=str(root))
 else:
  text=row.stdout.strip();words=text.split();started=' '.join(words[:5]);command=' '.join(words[5:])
  assert str(out/'server-fixture-05.ts') in command,(pid,command)
  observed=dt.datetime.strptime(started,'%a %b %d %H:%M:%S %Y').astimezone(dt.timezone.utc)
  expected=dt.datetime.fromisoformat(launch['started'])
  assert abs((observed-expected).total_seconds())<10,(observed,expected)
  os.kill(pid,signal.SIGTERM)
  deadline=time.monotonic()+15
  while time.monotonic()<deadline:
   status=subprocess.run(['ps','-p',str(pid),'-o','stat='],capture_output=True,text=True)
   if status.returncode or status.stdout.strip().startswith('Z'):break
   time.sleep(.2)
  else:raise TimeoutError('Owned server did not exit')
  result=dict(pid=pid,root=str(root),identity_start=started,identity_command=command,signal='SIGTERM',exited=True)
 with (out/('cleanup-'+label+'-16.json')).open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
 print(label,'stopped',flush=True)
