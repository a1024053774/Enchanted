import datetime,json,os,subprocess,sys,time
from pathlib import Path
out=Path(__file__).resolve().parent;fork=Path('/Users/luckye/Documents/Code/synara')
label=sys.argv[1];assert label.replace('-','').replace('_','').isalnum()
assert Path('/Volumes/WD-Elements').is_mount() and (fork/'a2a/scripts/bun').is_file()
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip()
status=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=fork,text=True)
root=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t056-'+label);root.mkdir(mode=0o700)
for name in ['os-home','codex-empty','claude-empty']: (root/name).mkdir(mode=0o700)
env={k:v for k,v in os.environ.items() if k in ['PATH','SHELL','LANG','LC_ALL']}
env.update(HOME=str(root/'os-home'),CODEX_HOME=str(root/'codex-empty'),CLAUDE_CONFIG_DIR=str(root/'claude-empty'),A2A_SYNARA_SLOT='t056-'+label,T056_ROOT=str(root),T056_FORK=str(fork),T056_SOURCE_REVISION=revision)
argv=['./a2a/scripts/bun','run',str(out/'server-fixture-61.ts')];started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/('server-'+label+'.log')).open('x',encoding='utf-8') as stream:process=subprocess.Popen(argv,cwd=fork,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
with (out/('server-'+label+'-launch.json')).open('x',encoding='utf-8') as stream:json.dump(dict(argv=argv,cwd=str(fork),pid=process.pid,root=str(root),environment=env,source_revision=revision,tracked_status=status,started=started),stream,indent=2);stream.write('\n')
for _ in range(450):
 if (root/'ready.json').exists():print((root/'ready.json').read_text(encoding='utf-8'));break
 if process.poll() is not None:raise RuntimeError('Fixture exited; raw launch/log retained')
 time.sleep(.1)
else:raise TimeoutError('Fixture ready')
