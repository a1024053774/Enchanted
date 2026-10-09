import json,subprocess,urllib.request
from pathlib import Path
out=Path(__file__).resolve().parent
launch=json.loads((out/'server-final-resume-44-launch.json').read_text());root=Path(launch['root']);endpoint=json.loads((root/'ready.json').read_text())['origin']
s=json.loads((out/'final-resume-44/summary.json').read_text())
with urllib.request.urlopen(endpoint+'/api/a2a/membership?project=t056-project') as r:current=json.load(r)
managed=next(t for t in current['tasks'] if t['taskId']=='t056')
fixture=dict(task='t056',project='t056-project',revision=managed['revision'],worker=s['cases'][0]['thread'],reviewer=s['cases'][1]['thread'],unmanaged_task='t056-unmanaged-membership')
(out/'membership-fixture-resume-45.json').write_text(json.dumps(fixture,indent=2)+'\n')
# Run the existing independent scenario with only its evidence destination changed.
source=Path('/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch5/T-044/membership-scenario.py').read_text()
(out/'membership-scenario-resume-45.py').write_text(source)
argv=['python3',str(out/'membership-scenario-resume-45.py'),'membership-resume-45',endpoint,str(out/'membership-fixture-resume-45.json')]
r=subprocess.run(argv,capture_output=True,text=True)
(out/'membership-resume-45.command.json').write_text(json.dumps(dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),ensure_ascii=False,indent=2)+'\n')
print('exit',r.returncode);print(r.stdout);print(r.stderr[-2000:]);raise SystemExit(r.returncode)
