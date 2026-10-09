import importlib.util,json,os,subprocess,tempfile,time,uuid,datetime,sys
from pathlib import Path
base=Path(__file__).resolve().parent;out=Path(sys.argv[2])
spec=importlib.util.spec_from_file_location('api',base/'fixture-api.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
f=a.Fixture(sys.argv[1]);dispatch=json.loads((out/'real-dispatch.json').read_text());thread=dispatch['attempt']['thread_id']
deadline=time.monotonic()+90
while time.monotonic()<deadline:
 snapshot=f.control('snapshot');t=next(x for x in snapshot['threads'] if x['id']==thread)
 pending=[x for x in t['pendingInteractions'] if x['interactionKind']=='approval' and x['status']=='pending']
 if pending:break
 time.sleep(.2)
else:raise TimeoutError('a2a_raise permission request absent')
assert len(pending)==1,pending
request=pending[0]
activity=next(x for x in t['activities'] if x['kind']=='approval.requested' and x['payload']['requestId']==request['requestId'])
assert activity['payload']['detail']=='Allow the synara MCP server to run tool "a2a_raise"?',activity
with (out/'approval-before.json').open('x') as file:json.dump(snapshot,file,ensure_ascii=False,indent=2)
command=dict(type='thread.approval.respond',commandId=str(uuid.uuid4()),threadId=thread,requestId=request['requestId'],lifecycleGeneration=request['lifecycleGeneration'],decision='accept',createdAt=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (out/'approval-input.json').open('x') as file:json.dump(command,file,ensure_ascii=False,indent=2)
record=dict(request_id=request['requestId'],at=command['createdAt'],thread=thread,decision='accept',reason='执行主控决定 02 授权：仅在本 worker 自启隔离实例中逐次批准 a2a_raise，以完成 T-055 验收。',authorization='controller-decision-02.md 第 1 项；当前用户消息明确要求执行此决定。',runtimeMode='approval-required')
with (out/'manual-approval.json').open('x') as file:json.dump(record,file,ensure_ascii=False,indent=2)
with tempfile.TemporaryDirectory(prefix='t055-round3-token-',dir='/tmp') as directory:
 token=Path(directory)/'token';f.control('token',thread=thread,path=str(token))
 env={**os.environ,'A2A_SYNARA_SLOT':'t055-round3-rpc','T055_EVIDENCE':str(out.resolve())}
 argv=['./a2a/scripts/bun','run',str(base/'native-rpc.mjs'),'approval-response',f.origin,str((out/'approval-input.json').resolve())]
 result=subprocess.run(argv,cwd='/Users/luckye/Documents/Code/synara',env=env,capture_output=True,text=True)
 with (out/'approval-response-command.json').open('x') as file:json.dump(dict(argv=argv,exit=result.returncode,stdout=result.stdout,stderr=result.stderr),file,indent=2)
 assert result.returncode==0,result.stderr
 print('Manually approved',request['requestId'],flush=True)
 deadline=time.monotonic()+20
 while time.monotonic()<deadline:
  issues=f.gate('issues',task='t055')
  if issues['issues']:break
  time.sleep(.03)
 else:raise TimeoutError('approved real worker did not persist issue')
 original=issues['issues'][0]['issue'];assert original['number']==1
 assert original['title']=='oracle 漏了空页' and original['body']=='分页夹具没有覆盖最后一页为空的情况。' and original['blocking'] is True
 # A separate, explicitly supplied sentinel changes title/body/blocking. Its
 # forged thread parameter must not replace credential identity.
 forged_args=dict(title='独立哨兵：引号 " 与换行',body='另一个会话的身份不能取代当前凭据。\n'+('界'*610),blocking=False,refs=['file:fixture.txt:1'],thread='other-thread-forged',threadId='other-thread-forged')
 forged=f.http('/mcp',dict(jsonrpc='2.0',id=2,method='tools/call',params=dict(name='a2a_raise',arguments=forged_args)),token.read_text())
 with (out/'forged-thread-input.json').open('x') as file:json.dump(forged_args,file,ensure_ascii=False,indent=2)
 with (out/'forged-thread-result.json').open('x') as file:json.dump(forged,file,ensure_ascii=False,indent=2)
 assert not forged['result'].get('isError'),forged
 sentinel=json.loads(forged['result']['content'][0]['text']);assert sentinel['ok'] and sentinel['number']==2,sentinel
 with (out/'real-raise-result.json').open('x') as file:json.dump(issues,file,ensure_ascii=False,indent=2)
after=f.gate('status',task='t055');assert after['task']==dispatch['task']
all_issues=f.gate('issues',task='t055');assert len(all_issues['issues'])==2
assert all(x['issue']['thread_id']==thread for x in all_issues['issues'])
assert all_issues['issues'][1]['issue']['body']==forged_args['body']
for name,value in [('issues-before-answer.json',all_issues),('status-after-raises.json',after)]:
 with (out/name).open('x') as file:json.dump(value,file,ensure_ascii=False,indent=2)
print('Real raise and forged-thread sentinel PASS',flush=True)
