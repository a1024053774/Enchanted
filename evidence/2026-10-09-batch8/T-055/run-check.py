import datetime, json, os, subprocess, sys
from pathlib import Path
out=Path(__file__).resolve().parent
label,*args=sys.argv[1:]
argv=['./a2a/scripts/bun',*args]
env={**os.environ,'A2A_SYNARA_SLOT':'t055-checks'}
record={'argv':argv,'cwd':'/Users/luckye/Documents/Code/synara','start':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (out/(label+'.log')).open('x') as log:
    result=subprocess.run(argv,cwd=record['cwd'],env=env,stdout=log,stderr=subprocess.STDOUT)
record.update(exit=result.returncode,end=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (out/(label+'.command.json')).open('x') as file:
    json.dump(record,file,indent=2);file.write('\n')
print(label,result.returncode)
sys.exit(result.returncode)
