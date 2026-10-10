import json
from pathlib import Path
import subprocess
import sys
out=Path(__file__).resolve().parent
fork=Path('/Users/luckye/Documents/Code/synara')
label=sys.argv[1]
output_label=sys.argv[2] if len(sys.argv)>2 else label
launch=json.loads((out/('server-'+label+'-launch.json')).read_text(encoding='utf-8'))
argv=['./a2a/scripts/bun','run',str(out/'ui-probe-11.mjs'),label,output_label]
with (out/(output_label+'-ui.log')).open('x',encoding='utf-8') as log:
    run=subprocess.run(argv,cwd=fork,env=launch['environment'],stdout=log,stderr=subprocess.STDOUT)
with (out/(output_label+'-ui-command.json')).open('x',encoding='utf-8') as stream:
    json.dump(dict(argv=argv,cwd=str(fork),returncode=run.returncode,source_revision=launch['source_revision']),stream,indent=2)
print('UI exit',run.returncode)
raise SystemExit(run.returncode)
