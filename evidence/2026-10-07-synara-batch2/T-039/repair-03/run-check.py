import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
label, *args = sys.argv[1:]
argv = [str(fork / 'a2a/scripts/bun'), *args]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
env = dict(os.environ, A2A_SYNARA_SLOT='t039-repair03')
with (here / (label + '.log')).open('x', encoding='utf-8') as log:
    p = subprocess.run(argv, cwd=fork, env=env, stdout=log, stderr=subprocess.STDOUT)
with (here / (label + '.json')).open('x', encoding='utf-8') as out:
    json.dump(dict(argv=argv, cwd=str(fork), started=started,
                   ended=datetime.datetime.now(datetime.timezone.utc).isoformat(), exit=p.returncode,
                   fork=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip()),out,indent=2)
print(label, p.returncode)
sys.exit(p.returncode)
