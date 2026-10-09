import json,subprocess,urllib.request
from pathlib import Path
out=Path(__file__).resolve().parent
launch=json.loads((out/'server-boundaries-restart-14-launch.json').read_text());root=Path(launch['root']);endpoint=json.loads((root/'ready.json').read_text())['origin']
s=json.loads((out/'frozen-13/summary.json').read_text())
with urllib.request.urlopen(endpoint+'/api/a2a/membership?project=t056-project') as r:current=json.load(r)
managed=next(t for t in current['tasks'] if t['taskId']=='t056')
fixture=dict(task='t056',project='t056-project',revision=managed['revision'],worker=s['cases'][0]['thread'],reviewer=s['cases'][1]['thread'],unmanaged_task='t056-unmanaged-membership')
(out/'membership-fixture-frozen-16.json').write_text(json.dumps(fixture,indent=2)+'\n')
# Run the existing independent scenario with only its evidence destination changed.
source=Path('/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch5/T-044/membership-scenario.py').read_text()
(out/'membership-scenario-frozen-16.py').write_text(source)
argv=['python3',str(out/'membership-scenario-frozen-16.py'),'membership-frozen-16',endpoint,str(out/'membership-fixture-frozen-16.json')]
r=subprocess.run(argv,capture_output=True,text=True)
(out/'membership-frozen-16.command.json').write_text(json.dumps(dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),ensure_ascii=False,indent=2)+'\n')
print('exit',r.returncode);print(r.stdout);print(r.stderr[-2000:]);raise SystemExit(r.returncode)
