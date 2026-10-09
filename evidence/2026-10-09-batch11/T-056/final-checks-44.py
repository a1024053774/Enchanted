from pathlib import Path
import json,os,subprocess,datetime as dt,sys
out=Path(__file__).resolve().parent;fork=Path('/Users/luckye/Documents/Code/synara')
# Explicit paths keep neighboring task changes out of format mutations.
paths=subprocess.check_output(['git','diff','--name-only','--diff-filter=ACMR'],cwd=fork,text=True).splitlines()+['apps/server/src/a2a/userInput.ts','apps/web/src/a2a/UserInputObserverStatus.tsx','apps/web/src/a2a/userInputObserver.ts']
commands=[('fmt',['./a2a/scripts/bun','run','fmt:check']),('lint',['./a2a/scripts/bun','run','lint']),('typecheck',['./a2a/scripts/bun','run','typecheck']),('migrations',['./a2a/scripts/bun','run','migrations:check']),('gates',['./a2a/scripts/bun','run','--cwd','packages/a2a-gates','test']),('server',['./a2a/scripts/bun','run','--cwd','apps/server','test','src/a2a/service.test.ts','src/a2a/layer-sharing.test.ts','src/a2a/project-title.test.ts','src/a2a/raise-permission.test.ts']),('web',['./a2a/scripts/bun','run','--cwd','apps/web','test','src/a2a/humanIntervention.test.ts','src/a2a/issues.test.ts','src/uiFontSize.test.ts'])]
failed=False
for name,argv in commands:
 log=out/('final-'+name+'-44.log');started=dt.datetime.now(dt.timezone.utc).isoformat()
 with log.open('x') as file:r=subprocess.run(argv,cwd=fork,stdout=file,stderr=subprocess.STDOUT,env={**os.environ,'A2A_SYNARA_SLOT':'t056-final-44'})
 with (out/('final-'+name+'-44.command.json')).open('x') as file:json.dump(dict(argv=argv,cwd=str(fork),started=started,exit_code=r.returncode,log=log.name,environment={'A2A_SYNARA_SLOT':'t056-final-44'}),file,indent=2)
 print(name,r.returncode,flush=True);failed|=r.returncode!=0
raise SystemExit(int(failed))
