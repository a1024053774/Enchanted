import subprocess,json,os,sys,datetime,shutil
from pathlib import Path
out=Path(__file__).resolve().parent
repo=Path('/Users/luckye/Documents/Code/synara')
base=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t042-verify-recovery-01')
paths=[repo/'node_modules',*[p/'node_modules' for kind in ['apps','packages'] for p in (repo/kind).iterdir() if p.is_dir()],repo/'scripts/node_modules']
records=[]
for p in paths:
 if not p.exists() and not p.is_symlink():continue
 target=base/'damaged-dependencies'/p.relative_to(repo)
 target.parent.mkdir(parents=True,exist_ok=True)
 record={'source':str(p),'destination':str(target),'started':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 with (out/'dependency-moves.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
 shutil.move(str(p),str(target))
 record['completed']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (out/'dependency-moves.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
print('damaged dependency trees preserved',flush=True)
env=dict(os.environ,A2A_SYNARA_SLOT='t042-verify-recovery-01',TMPDIR=str(base/'tmp'),HOME=str(base/'os-home'),XDG_CONFIG_HOME=str(base/'config'),XDG_DATA_HOME=str(base/'data'),XDG_CACHE_HOME=str(base/'cache'),CODEX_HOME=str(base/'codex'),CLAUDE_CONFIG_DIR=str(base/'claude'),PYTHONDONTWRITEBYTECODE='1')
argv=['./a2a/scripts/bun','install','--frozen-lockfile','--backend=copyfile','--no-progress']
record={'argv':argv,'cwd':str(repo),'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'env':{k:env[k] for k in ['A2A_SYNARA_SLOT','TMPDIR','HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','CODEX_HOME','CLAUDE_CONFIG_DIR']}}
(out/'install-command.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
with (out/'install.log').open('x',encoding='utf-8') as f:p=subprocess.run(argv,cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
record.update(exit_code=p.returncode,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
(out/'install-result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('install exit',p.returncode)
sys.exit(p.returncode)
