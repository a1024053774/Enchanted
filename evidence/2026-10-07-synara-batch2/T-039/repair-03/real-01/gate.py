import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

here = Path(__file__).resolve().parent
r = json.loads((here / 'runtime.json').read_text(encoding='utf-8'))
label, raw = sys.argv[1:]
record = here / (label + '.json')
assert not record.exists()
request = json.loads(raw)
argv = ['./a2a/scripts/bun', 'run', 'packages/a2a-gates/src/cli.ts', r['endpoint'], json.dumps(request)]
env = dict(os.environ, A2A_SYNARA_SLOT=r['slot'],
           A2A_GATE_BEARER=Path(r['root'], 'bootstrap-token').read_text(encoding='utf-8'))
started = datetime.now(timezone.utc).isoformat()
p = subprocess.run(argv, cwd='/Users/luckye/Documents/Code/synara', env=env,
                   capture_output=True, text=True, timeout=1000)
value = dict(started=started, ended=datetime.now(timezone.utc).isoformat(), argv=argv,
             cwd='/Users/luckye/Documents/Code/synara', request=request, stdout=p.stdout,
             stderr=p.stderr, exit=p.returncode)
with record.open('x', encoding='utf-8') as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
with (here / 'commands.jsonl').open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(value, ensure_ascii=False) + '\n')
print(p.stdout)
sys.exit(p.returncode)
