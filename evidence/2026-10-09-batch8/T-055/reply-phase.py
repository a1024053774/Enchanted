import json,sys,importlib.util,time,tempfile,uuid,datetime
from pathlib import Path
base=Path(__file__).resolve().parent;out=Path(sys.argv[2]);label=sys.argv[3]
s=importlib.util.spec_from_file_location('a',base/'fixture-api.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a);f=a.Fixture(sys.argv[1])
dispatch=json.loads((out/'real-dispatch.json').read_text());thread=dispatch['attempt']['thread_id']
def save(name,value):
 with (out/name).open('x') as file:json.dump(value,file,ensure_ascii=False,indent=2);file.write('\n')
before=f.gate('issues',task='t055');save('after-restart-issues.json',before)
assert before['records']==json.loads((out/'before-restart-issues.json').read_text())['records']
assert before['user_inputs']==[]
receipt=out/(label+'-answer-receipt.json');deadline=time.monotonic()+120
while not receipt.exists() and time.monotonic()<deadline:time.sleep(.1)
assert receipt.exists(),'UI did not send answer'
deadline=time.monotonic()+60
while time.monotonic()<deadline:
 snapshot=f.control('snapshot');t=next(t for t in snapshot['threads'] if t['id']==thread)
 if t['latestTurn']['state']=='running':break
 time.sleep(.1)
else:raise TimeoutError('second actual model turn did not start')
save('reply-active-native.json',snapshot)
with tempfile.TemporaryDirectory(prefix='t055-reply-token-',dir='/tmp') as directory:
 token=Path(directory)/'token';f.control('token',thread=thread,path=str(token))
 tools=f.http('/mcp',dict(jsonrpc='2.0',id=1,method='tools/list',params={}),token.read_text());save('tools-list.json',tools)
 assert any(tool['name']=='a2a_raise' for tool in tools['result']['tools'])
 for number,args in [(2,dict(title='独立哨兵：引号 " 与换行',body='跨会话身份不可伪造。\n'+('界'*610),blocking=False,refs=['file:fixture.txt:1'],thread='forged-other',threadId='forged-other')),(3,dict(title='独立阻塞哨兵',body='',blocking=True))]:
  result=f.http('/mcp',dict(jsonrpc='2.0',id=number,method='tools/call',params=dict(name='a2a_raise',arguments=args)),token.read_text())
  save(f'raise-{number}-input.json',args);save(f'raise-{number}-result.json',result)
  assert not result['result'].get('isError'),result
  decoded=json.loads(result['result']['content'][0]['text']);assert decoded['ok'] and decoded['number']==number,decoded
deadline=time.monotonic()+120
while time.monotonic()<deadline:
 snapshot=f.control('snapshot');t=next(t for t in snapshot['threads'] if t['id']==thread)
 if t['latestTurn']['state']=='completed':break
 assert not t['hasPendingApprovals'],'unattended call unexpectedly requested approval'
 time.sleep(.2)
else:raise TimeoutError('actual reply turn did not complete')
save('reply-complete-native.json',snapshot)
issues=f.gate('issues',task='t055');events=f.gate('events',task='t055');status=f.gate('status',task='t055')
save('issues-after-answer.json',issues);save('events-after-answer.json',events);save('status-after-answer.json',status)
assert status['task']==dispatch['task']
# The expected string is written from spec section 4, not copied from output.
expected='问题 1：oracle 漏了空页\n分页夹具没有覆盖最后一页为空的情况。\n用户答复：补上，并在 RESULTS 里写明。'
message=[m for m in t['messages'] if m.get('dispatchOrigin')=='user'];assert len(message)==1,message
assert message[0]['role']=='user' and message[0]['text']==expected
assert t['messages'][-1]['role']=='assistant' and t['messages'][-1]['text'].strip()=='补上，并在 RESULTS 里写明。'
inputs=issues['user_inputs'];assert len(inputs)==1 and inputs[0]['form']=='answer'
original=next(x['issue'] for x in issues['issues'] if x['issue']['number']==1)
assert inputs[0]['reply_to']==original['id'] and inputs[0]['target']['message']==message[0]['id']
interventions=[e for e in events['events'] if e['type']=='human_intervention'];assert len(interventions)==1
assert interventions[0]['details']['input_id']==inputs[0]['id'] and interventions[0]['attempt']==dispatch['attempt']['attempt_id']
source=next(e for e in events['events'] if e['type']=='issue_answer');assert inputs[0]['source_ref']['event_id']==source['details']['id'] and inputs[0]['source_ref']['source_sequence']==source['seq']
assert len(issues['issues'])==3 and all(x['issue']['thread_id']==thread for x in issues['issues'])
assert not any(x['kind']=='approval' for x in t['activities'])
save('reply-oracle.json',dict(status='PASS',expected=expected,message=message[0],input=inputs[0],intervention=interventions[0],ready_rev=2))
print('Real Codex report/reply, exact user message, deduplication and active-thread identity PASS',flush=True)
