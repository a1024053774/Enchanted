import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

out = Path(__file__).resolve().parent
old = out.parents[1]/'2026-10-09-batch8/T-055'
spec = importlib.util.spec_from_file_location('fixture_api',old/'fixture-api.py')
api = importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
f = api.Fixture(sys.argv[1]);label=sys.argv[2]
seed=json.loads((f.root/'seed.json').read_text(encoding='utf-8'))
def save(name,value):
    with (out/(label+'-'+name+'.json')).open('x',encoding='utf-8') as file:json.dump(value,file,ensure_ascii=False,indent=2)
before=f.gate('status',task='t057')
instructions=f.root/'controller-transport-instructions.txt'
instructions.write_text('这是隔离的 T-057 协议验证。不要改文件，不要调用任何工具，不要 submit。只逐行写出从 1 到 200 的数字。',encoding='utf-8')
attached=f.gate('attach',task='t057',role='controller',modelSelection={'provider':'codex','model':'gpt-6.1-sol','options':{'reasoningEffort':'xhigh','fastMode':True}},runtimeMode='approval-required',instructions=str(instructions))
save('attach',attached);assert attached['ok'],attached
thread=attached['attachment']['thread_id']
with tempfile.TemporaryDirectory(prefix='a2a-t057-mcp-token-',dir='/tmp') as directory:
    token_path=Path(directory)/'controller';f.control('token',thread=thread,path=str(token_path));token=token_path.read_text()
    listed=f.http('/mcp',{'jsonrpc':'2.0','id':10,'method':'tools/list','params':{}},token)
    names=[tool['name'] for tool in listed['result']['tools']]
    save('tools-list',listed);assert 'a2a_disposition' in names
    until=time.monotonic()+55
    while True:
        snapshot=f.control('snapshot');shell=next(t for t in snapshot['threads'] if t['id']==thread)
        if shell.get('session',{}).get('activeTurnId') and shell.get('latestTurn',{}).get('state')=='running':break
        if time.monotonic()>until:raise TimeoutError('controller active turn')
        time.sleep(.1)
    save('active-caller',{'thread':thread,'session':shell['session'],'latestTurn':shell['latestTurn'],'role':'controller'})
    for ordinal,(action,issue,expected_error) in enumerate([
        ('close',seed['issues'][0]['id'],'blocking_requires_user'),
        ('dismiss',seed['issues'][1]['id'],'user_required'),
        ('close',seed['issues'][1]['id'],None),
    ]):
        request={'jsonrpc':'2.0','id':20+ordinal,'method':'tools/call','params':{'name':'a2a_disposition','arguments':{
            'task':'t057','issue':issue,'action':action,'reason':'真实 MCP 处置哨兵','basis':'ticket:T-057','actor':'user'}}}
        result=f.http('/mcp',request,token);save('call-'+str(ordinal),{'request':request,'result':result,
            'boundary':'operator-supplied HTTP MCP call under a real active controller credential; not a model permission bypass'})
        if expected_error:
            assert result['result']['isError'] is True,result
            assert expected_error in json.dumps(result['result'],ensure_ascii=False),result
        else:assert not result['result'].get('isError',False),result
    after=f.gate('issues',task='t057');save('issues-after-mcp',after)
    closed=next(view for view in after['issues'] if view['issue']['id']==seed['issues'][1]['id'])
    assert closed['state']=='已关闭' and closed['disposition']['from']=='controller:'+thread

owner=f.root/'cli-owner';(owner/'a2a-gates').mkdir(parents=True,mode=0o700)
pid=json.loads((f.root/'ready.json').read_text())['pid']
identity=subprocess.check_output(['ps','-p',str(pid),'-o','lstart=','-o','command='],text=True,env={**os.environ,'LC_ALL':'C','LANG':'C'}).strip()
(owner/'workbench-process.json').write_text(json.dumps({'pid':pid,'identity':identity}),encoding='utf-8')
endpoint=owner/'a2a-gates/endpoint.json';endpoint.write_text(json.dumps({'origin':f.origin,'token':str(uuid.uuid4()),'desktopPid':pid,'home':str(owner)}),encoding='utf-8');endpoint.chmod(0o600)
request={'command':'disposition','task':'t057','issue':seed['issues'][1]['id'],'action':'reopen'}
argv=['./a2a/scripts/gate',json.dumps(request,ensure_ascii=False)]
result=subprocess.run(argv,cwd='/Users/luckye/Documents/Code/synara',env={**os.environ,'A2A_WORKBENCH_DATA_DIR':str(owner),'A2A_SYNARA_SLOT':'t057-cli'},capture_output=True,text=True)
save('cli',{'argv':argv,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
            'discovery':'fixture-owned discovery metadata; real test-server PID; not an Electron launcher test'})
assert result.returncode==0,result.stderr
parsed=json.loads(result.stdout);assert parsed['ok']
assert next(view for view in parsed['issues'] if view['issue']['id']==seed['issues'][1]['id'])['state']=='等你决定'
assert f.gate('status',task='t057')['task']==before['task']
save('binding',{'thread':thread,'native_controller_model_turns':1,'task_unchanged':True,'computerToolPermission_modified':False})
print('MCP registration, active controller identity, blocking/dismiss refusals, close and operator CLI reopen PASS')
