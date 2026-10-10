"""Capture bounded repository checks without overwriting earlier evidence."""
import json
from pathlib import Path
import subprocess
import sys

out=Path(__file__).resolve().parent
label=sys.argv[1]; argv=['./a2a/scripts/bun',*sys.argv[2:]]
fork=Path('/Users/luckye/Documents/Code/synara')
with (out/(label+'.log')).open('x',encoding='utf-8') as log:
    result=subprocess.run(argv,cwd=fork,stdout=log,stderr=subprocess.STDOUT)
with (out/(label+'.json')).open('x',encoding='utf-8') as stream:
    json.dump(dict(argv=argv,cwd=str(fork),exit_code=result.returncode,
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip(),
        tracked_status=subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=fork,text=True)),stream,ensure_ascii=False,indent=2)
print(label,result.returncode)
raise SystemExit(result.returncode)
