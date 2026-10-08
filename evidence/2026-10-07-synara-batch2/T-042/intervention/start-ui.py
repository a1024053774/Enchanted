import os,json,subprocess,time,urllib.request
from pathlib import Path
out=Path(__file__).resolve().parent
repo=Path('/Users/luckye/Documents/Code/synara')
base=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t042-intervention-01')
assert Path('/Volumes/WD-Elements').is_mount()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()=='3566ef4eb34b18c480c7a49e4b5d741681b72426'
assert subprocess.run(['git','diff','--quiet'],cwd=repo).returncode==0
for port in [5811,7771]:
 r=subprocess.run(['lsof','-nP',f'-iTCP:{port}','-sTCP:LISTEN'],capture_output=True,text=True)
 (out/f'port-{port}-before.json').write_text(json.dumps({'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})+'\n')
 assert r.returncode==1 and not r.stdout
keys={'PATH':os.environ['PATH'],'HOME':str(base/'os-home'),'SHELL':'/bin/sh','ZDOTDIR':str(base/'os-home'),'XDG_CONFIG_HOME':str(base/'config'),'XDG_DATA_HOME':str(base/'data'),'XDG_CACHE_HOME':str(base/'cache'),'CODEX_HOME':str(base/'codex'),'CLAUDE_CONFIG_DIR':str(base/'claude'),'TMPDIR':str(base/'tmp'),'A2A_SYNARA_SLOT':'t042-intervention-01','SYNARA_PORT_OFFSET':'2038','PYTHONDONTWRITEBYTECODE':'1'}
(out/'isolation.json').write_text(json.dumps({'env':keys,'fresh_data':str(base/'desktop-home'),'profile':str(base/'profile')},indent=2)+'\n')
argv=['./a2a/scripts/bun','run','dev:web','--dry-run']
r=subprocess.run(argv,cwd=repo,env=keys,capture_output=True,text=True)
(out/'dry-run.json').write_text(json.dumps({'argv':argv,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
assert r.returncode==0
argv=['./a2a/scripts/bun','run','dev:web']
with (out/'vite.log').open('x') as log:p=subprocess.Popen(argv,cwd=repo,env=keys,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,stdin=subprocess.DEVNULL)
(out/'vite-start.json').write_text(json.dumps({'argv':argv,'cwd':str(repo),'pid':p.pid,'pgid':p.pid,'time':time.time()},indent=2)+'\n')
for i in range(60):
 try:
  with urllib.request.urlopen('http://localhost:7771/',timeout=2) as r:
   if r.status==200:break
 except Exception:time.sleep(1)
else:raise RuntimeError('renderer not ready')
argv=['./a2a/scripts/bun','run','node',str(out/'launch-electron.cjs')]
r=subprocess.run(argv,cwd=repo,env=keys,capture_output=True,text=True)
(out/'electron-command.json').write_text(json.dumps({'argv':argv,'cwd':str(repo),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
assert r.returncode==0
print((out/'electron-start.json').read_text())
