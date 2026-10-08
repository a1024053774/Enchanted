import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

here = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
path = fork / 'apps/server/src/a2a/orchestration.ts'
fixed = path.read_bytes()
parent = 'fa3fc3352805d00e41c454fa6f810807528de3a9'
bad = subprocess.check_output(['git','show',parent+':apps/server/src/a2a/orchestration.ts'],cwd=fork)
assert fixed != bad
with (here/'counterfactual-fixed-source.txt').open('xb') as out:out.write(fixed)
started = datetime.now(timezone.utc).isoformat()
try:
    path.write_bytes(bad)
    p = subprocess.run(['python3','-B',str(here/'run-check.py'),'seam-final-parent-red',
                        'run','--cwd','apps/server','test','src/a2a/service.test.ts'],text=True,capture_output=True)
finally:
    assert path.read_bytes() == bad, 'Exclusive source changed during counterfactual; preserve it'
    path.write_bytes(fixed)
with (here/'counterfactual.json').open('x') as out:
    json.dump(dict(started=started,ended=datetime.now(timezone.utc).isoformat(),parent=parent,
                   argv=p.args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,
                   restored_fixed_bytes=path.read_bytes()==fixed),out,indent=2)
print(p.stdout)
assert p.returncode == 1
