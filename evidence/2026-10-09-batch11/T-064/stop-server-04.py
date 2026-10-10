import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

out = Path(__file__).resolve().parent
label = sys.argv[1]
launch = json.loads((out / ('server-' + label + '-launch.json')).read_text(encoding='utf-8'))
ready = json.loads((Path(launch['root']) / 'ready.json').read_text(encoding='utf-8'))
pid = launch['pid']
assert ready['pid'] == pid
command = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True)
assert command.returncode == 0 and launch['argv'][-1] in command.stdout and 'bun' in command.stdout, command.stdout
os.kill(pid, signal.SIGTERM)
for _ in range(200):
    running = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True)
    if running.returncode != 0 or running.stdout.strip().startswith('Z'):
        break
    time.sleep(.1)
else:
    raise TimeoutError('Owned server did not stop; retained')
record = dict(label=label, pid=pid, verified_command=command.stdout.strip(), stopped=True,
    created_at=dt.datetime.now(dt.timezone.utc).isoformat())
with (out / ('server-' + label + '-stop.json')).open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
print(json.dumps(record))
