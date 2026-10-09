import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

out=Path(__file__).resolve().parent
root=out.parents[2]
fork=root.parent/'synara'
label,kind=sys.argv[1:]
destination=out/label;destination.mkdir()
artifacts=Path(tempfile.mkdtemp(prefix='a2a-t057-'+label+'-',dir='/tmp'))
env={**os.environ,'A2A_SYNARA_SLOT':'t057-checks','PYTHONPATH':str(root/'acceptance'),
     'COOP_E2E_ARTIFACT_ROOT':str(artifacts),'COOP_E2E_TRACE':str(destination/'trace.json')}
if kind=='delivery':
    suite=root/'evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py'
    env.update(COOP_SCRIPT=str(root/'acceptance/entry/a2a_gates.py'),COOP_NATIVE_ENTRY=str(fork/'packages/a2a-gates/src/cli.ts'))
elif kind=='orchestration':
    suite=root/'evidence/2026-10-09-batch5/T-044/round2/test_run_native_e2e.py'
    env['COOP_SCRIPT']=str(root/'evidence/2026-10-07-synara-batch2/T-037/native-entry.py')
else:raise ValueError(kind)
sources=destination/'sources';sources.mkdir()
for source in [suite,Path(env['COOP_SCRIPT']),fork/'packages/a2a-gates/src/core.ts',fork/'packages/a2a-gates/src/cli.ts',
               fork/'packages/contracts/src/a2aGates.ts',fork/'apps/server/src/a2a/service.ts']:
    shutil.copyfile(source,sources/source.name)
argv=[sys.executable,'-B',str(suite),'--run-suite']
record={'argv':argv,'cwd':str(root),'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'fork':subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip(),
        'a2a':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        'artifacts':str(artifacts),'environment':{key:value for key,value in env.items() if key.startswith('COOP_') or key in ['A2A_SYNARA_SLOT','PYTHONPATH']}}
result=subprocess.run(argv,cwd=root,env=env,capture_output=True,text=True)
record.update(exit=result.returncode,ended_at=dt.datetime.now(dt.timezone.utc).isoformat(),stdout=result.stdout,stderr=result.stderr)
with (destination/'command.json').open('x',encoding='utf-8') as file:json.dump(record,file,ensure_ascii=False,indent=2)
print(json.dumps({'label':label,'exit':result.returncode,'artifact_root':str(artifacts)},ensure_ascii=False))
sys.exit(result.returncode)
