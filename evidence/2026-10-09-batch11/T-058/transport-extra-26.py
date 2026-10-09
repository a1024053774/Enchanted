import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

out=Path(__file__).resolve().parent
label=sys.argv[1]
launch=json.loads((out/('server-'+label+'-launch.json')).read_text(encoding='utf-8'))
root=Path(launch['root']); fork=Path('/Users/luckye/Documents/Code/synara')
oracle=json.loads((out/label/'transport-oracle.json').read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('t058_extra_api',out.parents[1]/'2026-10-09-batch8/T-055/fixture-api.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
f=api.Fixture(root)
results=out/(label+'-extra26');results.mkdir()
def save(name,value):
 with (results/(name+'.json')).open('x',encoding='utf-8') as s:json.dump(value,s,ensure_ascii=False,indent=2);s.write('\n')
token=(root/'private-executor.token').read_text(encoding='utf-8')
def call(name,args):
 request=dict(jsonrpc='2.0',id=str(uuid.uuid4()),method='tools/call',params=dict(name=name,arguments=args))
 result=f.http('/mcp',request,token);save('mcp-'+str(len(list(results.iterdir()))),dict(request=request,result=result,authenticated=True))
 return json.loads(result['result']['content'][0]['text'])
before=f.gate('status',task='t058')['task']
observed=[]
for command in ['create','claim','dispatch','attach','verify','integrate','reclaim','run','revoke','revise','status','events']:
 args=dict(task='missing-t058-contract',repo=str(root/'absent'),base=before['base_commit'],oracle=str(root/'oracle.py'),instructions=str(root/'instructions.txt'),owner='nonce-owner',reason='nonce-reason',spec_rev=9,runtimeMode='full-access',wait_seconds=1,role='worker',modelSelection=dict(provider='codex',model='gpt-6.1-sol'))
 via_mcp=call('a2a_'+command,args)
 via_http=f.http('/api/a2a',dict(command=command,**args))
 save('parity-'+command,dict(mcp=via_mcp,http=via_http))
 assert via_mcp['ok']==via_http['ok'] and via_mcp.get('error')==via_http.get('error'),command
 if command not in ['create','events']: assert via_mcp.get('error')=='unknown_task',(command,via_mcp)
 if command=='create': assert not via_mcp['ok']
 if command=='events':
  assert via_mcp['ok'] and via_mcp['events']==via_http['events']
  assert all(event['task']=='missing-t058-contract' for event in via_mcp['events'])
 observed.append(command)
assert f.gate('status',task='t058')['task']==before

created=call('a2a_create',dict(task='mcp-positive26',project='t058-control',repo=str(root/'repo'),base=before['base_commit'],oracle=str(root/'oracle.py'),instructions=str(root/'instructions.txt'),title='外部 MCP 标题 ζ'))
assert created['ok'] and created['task']['title']=='外部 MCP 标题 ζ',created
claimed=call('a2a_claim',dict(task='mcp-positive26',owner='外部 owner ζ'))
assert claimed['ok'] and claimed['attempt']['owner']=='外部 owner ζ',claimed
revoked=call('a2a_revoke',dict(task='mcp-positive26',reason='外部撤销理由 ζ'))
assert revoked['ok'] and revoked['task']['state']=='ready' and revoked['task']['current_attempt'] is None
revised=call('a2a_revise',dict(task='mcp-positive26',spec_rev=2))
assert revised['ok'] and revised['task']['spec_rev']==2

env={k:v for k,v in os.environ.items() if k in ['PATH','SHELL','LANG','LC_ALL']}
env.update(A2A_SYNARA_SLOT='s11-t058-'+label,A2A_GATE_BEARER='fixture-local-owner')
def cli(name,request):
 argv=['./a2a/scripts/bun','run','packages/a2a-gates/src/cli.ts',f.origin,json.dumps(request,ensure_ascii=False)]
 p=subprocess.run(argv,cwd=fork,env=env,capture_output=True,text=True)
 save(name,dict(argv=argv,cwd=str(fork),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 return json.loads(p.stdout)
sent=cli('cli-send',dict(command='inbox_send',from_ignored='not-a-sender',**{'from':'ideation'},to='executor',kind='revise',refs=['ticket:T-058'],body='CLI 哨兵 κ\n后续正文'))
assert sent['ok'] and sent['entry']['body']=='CLI 哨兵 κ\n后续正文',sent
ack=cli('cli-ack',dict(command='inbox_ack',role='executor',id=sent['entry']['id']))
assert ack['entry']['reply_to']==sent['entry']['id']
listed=cli('cli-unconfirmed',dict(command='inbox_list',role='executor'))
assert not any(v['entry']['id']==sent['entry']['id'] for v in listed['entries'])
f.control('command',command=dict(type='thread.archive',commandId=str(uuid.uuid4()),threadId=oracle['threads']['ideation']))
missing=f.gate('inbox_send',**{'from':'executor'},to='ideation',kind='report',body='已结束的目标必须保留条目')
assert not missing['ok'] and missing['delivery']['state']=='undelivered' and missing['entry']['body']=='已结束的目标必须保留条目'
save('extra-oracle',dict(status='PASS',candidate=launch['source_revision'],twelve_mcp_commands=observed,positive_create=created,positive_claim=claimed,positive_revoke=revoked,positive_revise=revised,cli_send=sent,cli_ack=ack,missing_target=missing,task_unchanged=True,new_model_turns=0))
print('PASS twelve MCP dispatches through shared core, real positive gate transitions and CLI inbox writes')
