from pathlib import Path
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile

out=Path(__file__).resolve().parent
repo=out.parents[2]
fork=Path('/Users/luckye/Documents/Code/synara')
label=sys.argv[1]
cases=[
 ('orchestration',repo/'evidence/2026-10-07-synara-batch2/T-037/test_run_native_e2e.py',repo/'evidence/2026-10-07-synara-batch2/T-037/native-entry.py'),
 ('delivery-recovery',repo/'evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py',repo/'acceptance/entry/a2a_gates.py'),
]
for name,script,entry in cases:
 dest=out/(label+'-'+name); dest.mkdir()
 artifacts=Path(tempfile.mkdtemp(prefix='a2a-t058-'+name+'-',dir='/tmp'))
 env={k:v for k,v in os.environ.items() if k in ['PATH','SHELL','LANG','LC_ALL']}
 env.update(A2A_SYNARA_SLOT='s11-t058-suites',COOP_SCRIPT=str(entry),COOP_E2E_ARTIFACT_ROOT=str(artifacts),COOP_E2E_TRACE=str(dest/'trace.json'),PYTHONPATH=str(repo/'acceptance'))
 if name=='delivery-recovery':env['COOP_NATIVE_ENTRY']=str(fork/'packages/a2a-gates/src/cli.ts')
 argv=[sys.executable,'-B',str(script),'--run-suite']
 started=dt.datetime.now(dt.timezone.utc).isoformat()
 p=subprocess.run(argv,cwd=repo,env=env,capture_output=True,text=True)
 with (dest/'command.json').open('x',encoding='utf-8') as f:
  json.dump(dict(argv=argv,cwd=str(repo),started=started,finished=dt.datetime.now(dt.timezone.utc).isoformat(),exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,artifacts=str(artifacts),environment={k:env[k] for k in env if k.startswith('COOP_') or k in ['A2A_SYNARA_SLOT','PYTHONPATH']},fork=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip(),tracked_status=subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=fork,text=True)),f,ensure_ascii=False,indent=2)
 print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
