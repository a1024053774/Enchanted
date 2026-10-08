import os,json,subprocess,sys,datetime
from pathlib import Path
out=Path(__file__).resolve().parent
root=Path('/Users/luckye/Documents/Code/a2a')
fork=root.parent/'synara'
base=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t042-verify-recovery-01')
env=dict(os.environ,A2A_SYNARA_SLOT='t042-verify-recovery-01',TMPDIR=str(base/'tmp'),HOME=str(base/'os-home'),XDG_CONFIG_HOME=str(base/'config'),XDG_DATA_HOME=str(base/'data'),XDG_CACHE_HOME=str(base/'cache'),CODEX_HOME=str(base/'codex'),CLAUDE_CONFIG_DIR=str(base/'claude'),PYTHONDONTWRITEBYTECODE='1')
for key in ['A2A_MUTANT_ENTRY','A2A_MUTANT_CORE','A2A_MUTANT_CLI','COOP_SCRIPT','COOP_NATIVE_ENTRY']: env.pop(key,None)
label=sys.argv[1]
if label=='lint': argv=['./a2a/scripts/bun','run','lint'];cwd=fork
elif label in ('build:desktop','typecheck'): argv=['./a2a/scripts/bun','run',label];cwd=fork
else:
 env['PYTHONPATH']=str(root/'acceptance')
 env['COOP_E2E_ARTIFACT_ROOT']=str(base/label);(base/label).mkdir()
 env['COOP_E2E_TRACE']=str(out/(label+'-trace.json'))
 env['COOP_SCRIPT']=str(root/('evidence/2026-10-07-synara-batch2/T-037/native-entry.py' if label=='orchestration' else 'acceptance/entry/a2a_gates.py'))
 env['COOP_NATIVE_ENTRY']=str(fork/'packages/a2a-gates/src/cli.ts')
 suite='evidence/2026-10-07-synara-batch2/T-037/test_run_native_e2e.py' if label=='orchestration' else 'evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py'
 argv=[sys.executable,'-B',str(root/suite),'--run-suite'];cwd=root
record={'argv':argv,'cwd':str(cwd),'env':{k:v for k,v in env.items() if k.startswith(('A2A_','COOP_','XDG_')) or k in ['TMPDIR','HOME','CODEX_HOME','CLAUDE_CONFIG_DIR','PYTHONPATH']},'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip()}
with (out/(label+'-command.json')).open('x',encoding='utf-8') as f: json.dump(record,f,ensure_ascii=False,indent=2)
with (out/(label+'.log')).open('x',encoding='utf-8') as log: p=subprocess.run(argv,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
record.update(exit_code=p.returncode,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
(out/(label+'-result.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(label,p.returncode,flush=True)
sys.exit(p.returncode)
