import json,sqlite3,time,uuid,urllib.request,subprocess,os
from pathlib import Path
out=Path(__file__).resolve().parent;results=out/'checkpoint-23';results.mkdir();root=Path(json.loads((out/'server-scope-22-launch.json').read_text())['root']);origin=json.loads((root/'ready.json').read_text())['origin'];s=json.loads((out/'scope-22/summary.json').read_text());worker=s['cases'][0]['thread'];ordinary=s['cases'][2]['thread'];fork=Path('/Users/luckye/Documents/Code/synara')
def save(n,v):(results/(n+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def rpc(n,c):
 p=results/(n+'.input.json');p.write_text(json.dumps(c)+'\n');argv=['./a2a/scripts/bun','run',str(out/'native-rpc-02.mjs'),n,origin,str(p)]
 env={k:v for k,v in os.environ.items() if k in ['PATH','LANG','LC_ALL','SHELL']};env.update(T056_EVIDENCE=str(results),A2A_SYNARA_SLOT='t056-checkpoint-23')
 r=subprocess.run(argv,cwd=fork,env=env,capture_output=True,text=True);save(n+'.command',dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:db.execute('DROP TRIGGER t056_nonmanaged_failure')
rpc('recover-nonmanaged',dict(type='thread.turn.interrupt',commandId=str(uuid.uuid4()),threadId=ordinary,createdAt='2026-10-09T18:10:00.000Z'));time.sleep(.3)
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:db.execute("CREATE TRIGGER t056_checkpoint_failure BEFORE INSERT ON user_input_checkpoint BEGIN SELECT RAISE(FAIL,'T056 progress unavailable, input sink works'); END")
rpc('managed-metadata-only',dict(type='thread.meta.update',commandId=str(uuid.uuid4()),threadId=worker,title='仅进度故障 Ω'));time.sleep(.3)
with urllib.request.urlopen(origin+'/api/a2a?thread='+worker) as r:status=json.load(r)
save('oracle',dict(expected='healthy: only checkpoint progress write failed, no managed input recording failed',observed=status['user_input_observer']))
assert status['user_input_observer']['state']=='healthy','progress-only failure attributed to managed input'

# A progress-only failure also must not prevent cold startup and business reads.
import shutil,signal
launch=json.loads((out/'server-scope-22-launch.json').read_text());pid=launch['pid']
identity=subprocess.check_output(['ps','-p',str(pid),'-o','lstart=,command='],text=True);assert 'server-fixture-02.ts' in identity
os.kill(pid,signal.SIGTERM)
for _ in range(100):
 try:os.kill(pid,0)
 except ProcessLookupError:break
 time.sleep(.1)
else:raise RuntimeError('fixture did not stop')
copy=root.with_name(root.name+'-checkpoint-restart');shutil.copytree(root,copy);(copy/'ready.json').unlink();env=launch['environment'];env['T056_ROOT']=str(copy)
log=(out/'server-checkpoint-restart-23.log').open('x');process=subprocess.Popen(launch['argv'],cwd=env['T056_FORK'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(out/'server-checkpoint-restart-23-launch.json').write_text(json.dumps(dict(argv=launch['argv'],environment=env,pid=process.pid,root=str(copy)),indent=2)+'\n')
for _ in range(450):
 if (copy/'ready.json').exists():break
 if process.poll() is not None:raise RuntimeError('progress-only fault blocked startup')
 time.sleep(.1)
else:raise TimeoutError('restart ready')
restart_origin=json.loads((copy/'ready.json').read_text())['origin']
with urllib.request.urlopen(restart_origin+'/api/a2a?thread='+worker) as response:restarted=json.load(response)
assert restarted['user_input_observer']['state']=='healthy',restarted
save('cold-start-oracle',dict(status='PASS',checkpoint_fault_still_installed=True,observer=restarted['user_input_observer'],root=str(copy),pid=process.pid))
