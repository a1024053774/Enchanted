import json,sys,importlib.util,tempfile,uuid,datetime,subprocess,os
from pathlib import Path
base=Path(__file__).resolve().parent;source=Path(sys.argv[2]);out=source/'boundaries';out.mkdir();sp=importlib.util.spec_from_file_location('a',base/'fixture-api.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);f=a.Fixture(sys.argv[1])
thread=json.loads((source/'real-dispatch.json').read_text())['attempt']['thread_id']
def save(name,value):
 with (out/name).open('x') as file:json.dump(value,file,ensure_ascii=False,indent=2);file.write('\n')
before=f.gate('status',task='t055');before_events=f.gate('events',task='t055')
snapshot=f.control('snapshot');real=next(t for t in snapshot['threads'] if t['id']==thread)
assert real['latestTurn']['state']=='completed' and not real['hasPendingApprovals']
assert not any(x['kind']=='approval.requested' for x in real['activities'])
# A controlled native frame supplies an active, unbound thread. No unbound
# model is run. Authentication, tool dispatch and gate refusal are all real.
unbound=str(uuid.uuid4());now=datetime.datetime.now(datetime.timezone.utc).isoformat()
create=dict(type='thread.create',commandId=str(uuid.uuid4()),threadId=unbound,projectId='t055-project',title='Unbound credential counterexample',modelSelection=dict(provider='codex',model='gpt-6.1-sol'),runtimeMode='full-access',interactionMode='default',envMode='local',branch=None,worktreePath=None,createdAt=now)
f.control('command',command=create)
session=dict(type='thread.session.set',commandId=str(uuid.uuid4()),threadId=unbound,session=dict(threadId=unbound,status='running',providerName='codex',runtimeMode='full-access',activeTurnId='controlled-unbound-turn',lastError=None,updatedAt=now),createdAt=now)
f.control('command',command=session)
save('unbound-frame.json',dict(create=create,session=session,snapshot=f.control('snapshot')))
with tempfile.TemporaryDirectory(prefix='t055-negative-token-',dir='/tmp') as directory:
 for name,target in [('unbound',unbound),('inactive',thread)]:
  token=Path(directory)/name;f.control('token',thread=target,path=str(token))
  result=f.http('/mcp',dict(jsonrpc='2.0',id=7,method='tools/call',params=dict(name='a2a_raise',arguments=dict(title='This report must be rejected',body='',blocking=False))),token.read_text())
  save(name+'-result.json',result)
  assert result['result']['isError'] is True,result
  if name=='unbound':assert result['result']['content'][0]['text']=='stale_thread'
  else:assert 'caller_turn_inactive' in result['result']['content'][0]['text']
 invalid=f.http('/mcp',dict(jsonrpc='2.0',id=8,method='tools/call',params=dict(name='a2a_raise',arguments=dict(title='Invalid credential'))),'invalid-fixture-token')
 save('invalid-credential-result.json',invalid);assert invalid['status']==401 and json.loads(invalid['body'])['error']['code']==-32600
after=f.gate('status',task='t055');after_events=f.gate('events',task='t055');assert before['task']==after['task'] and before_events['events']==after_events['events']
save('negative-state-unchanged.json',dict(before=before,after=after,events_unchanged=True))
session['commandId']=str(uuid.uuid4());session['session']['status']='stopped';session['session']['activeTurnId']=None;f.control('command',command=session)
# Publish only fixture-owned discovery files for the real operator gate CLI.
# This is not a desktop instance; the process identity is the actual test server.
owner=f.root/'cli-owner';(owner/'a2a-gates').mkdir(parents=True,mode=0o700)
pid=json.loads((f.root/'ready.json').read_text())['pid']
identity=subprocess.check_output(['ps','-p',str(pid),'-o','lstart=','-o','command='],text=True,env={**os.environ,'LC_ALL':'C','LANG':'C'}).strip()
(owner/'workbench-process.json').write_text(json.dumps(dict(pid=pid,identity=identity)))
endpoint=owner/'a2a-gates/endpoint.json';endpoint.write_text(json.dumps(dict(origin=f.origin,token=str(uuid.uuid4()),desktopPid=pid,home=str(owner))));endpoint.chmod(0o600)
env={**os.environ,'A2A_WORKBENCH_DATA_DIR':str(owner),'A2A_SYNARA_SLOT':'t055-cli'}
for command in ['issues','events','status']:
 argv=['./a2a/scripts/gate',json.dumps(dict(command=command,task='t055'))]
 result=subprocess.run(argv,cwd='/Users/luckye/Documents/Code/synara',env=env,capture_output=True,text=True)
 save('gate-'+command+'-command.json',dict(argv=argv,exit=result.returncode,stdout=result.stdout,stderr=result.stderr,discovery='fixture-owned endpoint and actual server PID'))
 assert result.returncode==0,result.stderr
 parsed=json.loads(result.stdout);assert parsed['ok']
 save('gate-'+command+'.json',parsed)
 if command=='issues':assert [r['kind'] for r in parsed['records'][:3]]==['issue','answer','disposition'] and parsed['records'][2]['action']=='delivered'
 elif command=='events':assert any(e['type']=='issue_issue' for e in parsed['events']) and any(e['type']=='issue_answer' for e in parsed['events'])
 else:assert parsed['task']==before['task']
assert not (owner/'a2a-gates/endpoint.json').is_symlink()
f.control('settings',patch={'providers':{'codex':{'enabled':False}}})
save('before-replay-issues.json',f.gate('issues',task='t055'));save('before-replay-events.json',f.gate('events',task='t055'))
print('Unbound/inactive/invalid identity, unchanged gate state and real gate CLI chain PASS')
