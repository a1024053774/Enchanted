"""Preserve a bounded fork check's command and full output."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

out = Path(__file__).resolve().parent
fork = out.parents[2].parent / 'synara'
label, *args = sys.argv[1:]
argv = [str(fork / 'a2a/scripts/bun'), *args]
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
env = dict(os.environ, A2A_SYNARA_SLOT='t036')
with (out / (label + '.log')).open('x', encoding='utf-8') as log:
    p = subprocess.run(argv, cwd=fork, env=env, stdout=log, stderr=subprocess.STDOUT)
with (out / (label + '.json')).open('x', encoding='utf-8') as f:
    json.dump(dict(argv=argv, cwd=str(fork), started=start, finished=datetime.datetime.now(datetime.timezone.utc).isoformat(), exit_code=p.returncode), f, indent=2)
    f.write('\n')
print(label, p.returncode)
sys.exit(p.returncode)
