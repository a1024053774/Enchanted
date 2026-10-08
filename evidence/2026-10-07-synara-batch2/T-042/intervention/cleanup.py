import json,os,signal,subprocess,time,shutil,tarfile
from pathlib import Path
p=Path(__file__).resolve().parent;base=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t042-intervention-01');home=Path(json.loads((p/'codex-isolation.json').read_text())['home'])
records=[]
for path in sorted(home.rglob('rollout*.jsonl')):
 entries=[json.loads(s) for s in path.read_text().splitlines()]; relevant=[e for e in entries if e['type']=='turn_context' or (e['type']=='event_msg' and e['payload'].get('type') in ['task_started','task_complete','user_message','agent_message'])]
 records.append({'source':str(path),'events':relevant})
(p/'model-turns.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
assert sum(e['type']=='event_msg' and e['payload'].get('type')=='task_started' for r in records for e in r['events'])==2
assert sum(e['type']=='event_msg' and e['payload'].get('type')=='task_complete' for r in records for e in r['events'])==2
pgids=[json.loads((p/(x+'-start.json')).read_text())['pgid'] for x in ['electron','vite']]
def owned():
 rows=subprocess.check_output(['ps','-axo','pid,ppid,pgid,command'],text=True).splitlines()[1:];return [s for s in rows if len(s.split(None,3))==4 and int(s.split(None,3)[2]) in pgids]
before=owned();(p/'processes-before-stop.txt').write_text('\n'.join(before)+'\n')
for pg in pgids:
 try:os.killpg(pg,signal.SIGTERM)
 except ProcessLookupError:pass
for _ in range(30):
 if not owned():break
 time.sleep(.5)
after=owned();assert not after,after
removed=[]
for d in [home,base/'desktop-home/codex-home-overlay',base/'codex']:
 assert str(d).startswith('/private/tmp/a2a-t042-codex-') or d in [base/'desktop-home/codex-home-overlay',base/'codex']
 if d.exists():shutil.rmtree(d)
 removed.append({'path':str(d),'exists':d.exists()})
assert not list(base.rglob('auth.json'))
# Retain only fixture and gate state, excluding provider credentials and desktop secrets.
f=json.loads((p/'fixture.json').read_text())
with tarfile.open(p/'retained-fixture.tar.gz','x:gz') as tar:
 tar.add(f['root'],arcname='fixture');tar.add(f['state'],arcname='a2a-gates')
(p/'cleanup.json').write_text(json.dumps({'pgids':pgids,'owned_after':after,'removed_homes':removed,'auth_files_under_isolated_root':[]},indent=2))
user=Path('/Users/luckye/.codex');paths=[user/'config.toml',user/'rules',*sorted((user/'rules').rglob('*'))];r=subprocess.run(['herdr','status'],capture_output=True,text=True)
snap={'metadata':[{'path':str(x),'size':x.stat().st_size,'mtime_ns':x.stat().st_mtime_ns} for x in paths],'herdr':{'argv':['herdr','status'],'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}}
(p/'user-after.json').write_text(json.dumps(snap,indent=2));previous=json.loads((p/'user-before.json').read_text());(p/'user-comparison.json').write_text(json.dumps({'equal':previous==snap,'metadata_equal':previous['metadata']==snap['metadata'],'herdr_equal':previous['herdr']==snap['herdr']},indent=2));assert previous==snap
r=subprocess.run(['git','status','--short'],cwd='/Users/luckye/Documents/Code/synara',capture_output=True,text=True);(p/'product-final-status.txt').write_text(r.stdout)
assert subprocess.run(['git','diff','--quiet','HEAD'],cwd='/Users/luckye/Documents/Code/synara').returncode==0
print('PASS: two completed turns, owned processes stopped, isolated homes removed, user metadata unchanged')
