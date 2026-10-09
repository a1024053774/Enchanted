import json,os,sqlite3,sys,time,uuid,datetime as dt,subprocess,urllib.request,shutil,signal
from pathlib import Path
out=Path(__file__).resolve().parent
root=Path(json.loads((out/'server-final-07-launch.json').read_text())['root'])
origin=json.loads((root/'ready.json').read_text())['origin'];results=out/'boundaries-09';results.mkdir()
fork=Path('/Users/luckye/Documents/Code/synara')
s= json.loads((out/'final-07/summary.json').read_text());worker=s['cases'][0]['thread'];ordinary=s['cases'][2]['thread']
def save(name,value): (results/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def uid():return str(uuid.uuid4())
def now():return dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
def rpc(name,command,tag='orchestration.dispatchCommand',expected=0):
 path=results/(name+'.input.json');path.write_text(json.dumps(command,ensure_ascii=False)+'\n')
 argv=['./a2a/scripts/bun','run',str(out/'native-rpc-02.mjs'),name,origin,str(path)]
 env={k:v for k,v in os.environ.items() if k in ('PATH','SHELL','LANG','LC_ALL')};env.update(A2A_SYNARA_SLOT='t056-boundaries-09',T056_EVIDENCE=str(results),A2A_RPC_TAG=tag)
 r=subprocess.run(argv,cwd=fork,env=env,text=True,capture_output=True,timeout=45)
 save(name+'.command',dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
 assert r.returncode==expected,(name,r.returncode,r.stderr)
def inputs():
 with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:return [json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
def events():
 with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:return [dict(seq=r[0],type=r[1],details=json.loads(r[2])) for r in db.execute('SELECT seq,type,details FROM events ORDER BY seq')]
# Oracle is the ticket/spec's fields and source channels, not production builders.
for c in s['cases']:
 matched=[v for v in inputs() if (c.get('message') and v['target']['message']==c['message']) or (c.get('command') and v['source_ref'].get('command_id')==c['command'])]
 assert len(matched)==1,c
 v=matched[0];assert v['certainty']=='observed' and v['form']==c['form']; assert v['target']['project']=='t056-project'
 assert all(k in v['target'] for k in ('task','attempt','thread','turn','message','request'))
 assert v['source_ref'].get('event_id') or v['source_ref'].get('command_id')
 assert v['target']['thread']==c['thread']
 if c.get('request'):assert v['target']['request']==c['request']
 assert v['channel']==('thread-message' if c.get('message') else 'ws-rpc')
 if c['label']=='managed-message':assert v['target']['attempt']==s['cases'][0].get('attempt',v['target']['attempt']) and v['target']['attempt']
 else:assert v['target']['attempt'] is None
before=inputs();priorInterventions=[e for e in events() if e['type']=='human_intervention']
for name,source,prefix in [('agent','agent',''),('automation','automation',''),('gate','agent','a2a:')]:
 cmd=dict(type='thread.turn.start',commandId=prefix+uid(),threadId=ordinary,dispatchOrigin=source,
  message=dict(messageId=uid(),role='user',text=name+' Ω 不是用户来源',attachments=[]),runtimeMode='approval-required',interactionMode='default',createdAt=now())
 # Server provenance cannot be supplied by a client: the client codec strips it.
 token=uid();path=root/'control'/f'{token}.request.json';path.write_text(json.dumps(dict(operation='command',command=cmd)))
 result=root/'control'/f'{token}.result.json'
 for _ in range(450):
  if result.exists():
   data=json.loads(result.read_text())
   if not data.get('pending'):break
  time.sleep(.1)
 else:raise TimeoutError('internal provenance command')
 save('negative-'+name,dict(input=cmd,receipt=data));assert data['ok'],data
for name,typ in [('quit-derived','thread.turn.interrupt'),('temporary-derived','thread.session.stop')]:
 cmd=dict(type=typ,origin='ui-derived',commandId=uid(),threadId=worker,createdAt=now());rpc(name,cmd);rpc(name+'-duplicate',cmd)
 v=[v for v in inputs() if v['source_ref'].get('command_id')==cmd['commandId']]
 assert len(v)==1 and v[0]['channel']=='ui-derived' and v[0]['form']=='action'
time.sleep(.4)
after=inputs();assert len(after)==len(before)+2
assert [e for e in events() if e['type']=='human_intervention']==priorInterventions
rpc('quit-resume',dict(threadIds=[ordinary],continuationPrompt='继续未完成的工作'),tag='orchestration.prepareQuitResume')
quit=[v for v in inputs() if v['source_ref'].get('rpc')=='orchestration.prepareQuitResume'];assert len(quit)==1 and quit[0]['channel']=='ui-derived'
# Explicit managed action keeps the derived intervention bound to its input.
cmd=dict(type='thread.turn.interrupt',commandId=uid(),threadId=worker,createdAt=now());rpc('managed-action',cmd)
v=[v for v in inputs() if v['source_ref'].get('command_id')==cmd['commandId']][0]
interventions=[e for e in events() if e['type']=='human_intervention' and e['details'].get('input_id')==v['id']]
assert len(interventions)==1 and interventions[0]['details']['attempt_id']==v['target']['attempt']
# Unknown non-observation commands do not become inputs.
count=len(inputs());rpc('metadata-only',dict(type='thread.meta.update',commandId=uid(),threadId=ordinary,title='未分类 Ω 元数据'))
assert len(inputs())==count
# Append-only violations fail, and a non-managed input write does not block RPC business.
state=root/'userdata/a2a-gates/state.sqlite3'
with sqlite3.connect(state) as db:
 for statement in ['UPDATE user_inputs SET data=\'rewritten\'','DELETE FROM user_inputs']:
  try:db.execute(statement)
  except sqlite3.IntegrityError as error:assert 'append only' in str(error)
  else:raise AssertionError('input mutable')
 db.execute("CREATE TRIGGER t056_input_failure BEFORE INSERT ON user_inputs BEGIN SELECT RAISE(FAIL,'T056 unavailable input sink'); END")
cmd=dict(type='thread.turn.interrupt',commandId=uid(),threadId=ordinary,createdAt=now());rpc('nonmanaged-recording-failure',cmd)
count=len(inputs());time.sleep(.2)
# Same failure in a managed attempt refuses its input; all gate mutations stay latched.
managed=dict(type='thread.turn.interrupt',commandId=uid(),threadId=worker,createdAt=now());rpc('managed-recording-failure',managed,expected=1)
req=urllib.request.Request(origin+'/api/a2a',data=json.dumps(dict(command='revise',task='t056')).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req) as response:refused=json.load(response)
save('managed-refusal',refused);assert not refused['ok'] and refused['error']=='user_input_observer_failed'
save('before-restart-inputs',inputs());save('before-restart-events',events())
# Recovery on a complete copy preserves the original failure evidence.
launch=json.loads((out/'server-final-07-launch.json').read_text());pid=launch['pid'];identity=subprocess.check_output(['ps','-p',str(pid),'-o','lstart=,command='],text=True);assert 'server-fixture-02.ts' in identity
os.kill(pid,signal.SIGTERM)
for _ in range(100):
 try:os.kill(pid,0)
 except ProcessLookupError:break
 time.sleep(.1)
else:raise RuntimeError('server did not exit')
copy=root.with_name(root.name+'-boundary-restart');shutil.copytree(root,copy);(copy/'ready.json').unlink()
with sqlite3.connect(copy/'userdata/a2a-gates/state.sqlite3') as db:db.execute('DROP TRIGGER t056_input_failure')
env=launch['environment'];env['T056_ROOT']=str(copy)
log=(out/'server-boundaries-restart-09.log').open('x');p=subprocess.Popen(launch['argv'],cwd=env['T056_FORK'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(out/'server-boundaries-restart-09-launch.json').write_text(json.dumps(dict(argv=launch['argv'],environment=env,pid=p.pid,root=str(copy)),indent=2)+'\n')
for _ in range(450):
 if (copy/'ready.json').exists():break
 if p.poll() is not None:raise RuntimeError('restart failed')
 time.sleep(.1)
else:raise TimeoutError('ready')
root=copy;time.sleep(.3);recovered=[v for v in inputs() if v['source_ref'].get('command_id')==cmd['commandId']]
assert len(recovered)==1 and recovered[0]['form']=='action' and recovered[0]['target']['attempt'] is None
save('after-restart-inputs',inputs());save('after-restart-events',events())
save('summary',dict(status='PASS',checks=['all fields and target bindings','agent/automation/a2a provenance excluded','ui-derived actions and duplicate RPC','prepareQuitResume entry','managed derived intervention','unknown non-observation command','append-only','nonmanaged business continues on record failure','managed failure rejects gate mutations','event+ingress replay recovers exact input'],root=str(root),pid=p.pid,limitations=['Provider disabled; async question setup and response delivery remain controlled in this matrix.','Gap recovery with failed ingress is tested separately in source-loss-06.']))
print('PASS',len(inputs()),'inputs; boundary restart',p.pid)
