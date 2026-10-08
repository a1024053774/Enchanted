import os, json, sqlite3, shutil, subprocess, time
from pathlib import Path
out=Path(__file__).resolve().parent
checkout=Path('/Users/luckye/Documents/Code/synara-t038')
base=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t042-desktop')
assert Path('/Volumes/WD-Elements').is_mount()
base.mkdir(exist_ok=False)
home=base/'desktop-home'
(home/'dev').mkdir(parents=True)
source=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t038/desktop-home/dev')
src=sqlite3.connect(f'file:{source}/state.sqlite?mode=ro',uri=True)
dst=sqlite3.connect(str(home/'dev/state.sqlite')); src.backup(dst); dst.close(); src.close()
shutil.copytree(source/'a2a-gates',home/'dev/a2a-gates')
settings=json.loads((source/'settings.json').read_text())
settings['settings']['enableProviderUpdateChecks']=False
for v in settings['settings']['providers'].values(): v['enabled']=False
(home/'dev/settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for d in ['os-home','config','data','cache','codex','claude','profile']: (base/d).mkdir()
env={'PATH':os.environ['PATH'],'HOME':str(base/'os-home'),'SHELL':'/bin/sh','ZDOTDIR':str(base/'os-home'),'XDG_CONFIG_HOME':str(base/'config'),'XDG_DATA_HOME':str(base/'data'),'XDG_CACHE_HOME':str(base/'cache'),'CODEX_HOME':str(base/'codex'),'CLAUDE_CONFIG_DIR':str(base/'claude'),'A2A_SYNARA_SLOT':'t042-desktop','SYNARA_PORT_OFFSET':'2038'}
(out/'isolation.json').write_text(json.dumps({'fixture_source':str(source),'copy':['state.sqlite (SQLite backup)','a2a-gates','settings.json (all providers disabled)'],'env':env,'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()},indent=2)+'\n')
argv=['./a2a/scripts/bun','run','dev:web','--dry-run']
r=subprocess.run(argv,cwd=checkout,env=env,capture_output=True,text=True)
(out/'dry-run.log').write_text(r.stdout+r.stderr)
assert r.returncode==0
argv=['./a2a/scripts/bun','run','dev:web']
with (out/'vite.log').open('x') as log: p=subprocess.Popen(argv,cwd=checkout,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,stdin=subprocess.DEVNULL)
(out/'vite-start.json').write_text(json.dumps({'argv':argv,'cwd':str(checkout),'pid':p.pid,'pgid':p.pid,'time':time.time()},indent=2)+'\n')
print('Vite PID',p.pid)
