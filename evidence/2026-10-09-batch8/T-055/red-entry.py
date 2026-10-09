import json, sys, time, uuid, tempfile, urllib.request, urllib.error
from pathlib import Path

out = Path(__file__).resolve().parent
root = Path(sys.argv[1])
label = sys.argv[2]
origin = json.loads((root/'ready.json').read_text())['origin']
def control(operation, **args):
    name = str(uuid.uuid4())
    (root/'control'/f'{name}.request.json').write_text(json.dumps(dict(operation=operation, **args)))
    result = root/'control'/f'{name}.result.json'
    until = time.monotonic()+30
    while time.monotonic()<until:
        if result.exists():
            body=json.loads(result.read_text())
            if not body.get('pending'):
                assert body['ok'], body
                return body['result']
        time.sleep(.1)
    raise TimeoutError(operation)

project, thread = str(uuid.uuid4()), str(uuid.uuid4())
now = '2026-10-09T10:00:00.000Z'
control('command',command=dict(type='project.create',commandId=str(uuid.uuid4()),projectId=project,title='T055 red',workspaceRoot=str(root),createdAt=now))
control('command',command=dict(type='thread.create',commandId=str(uuid.uuid4()),threadId=thread,projectId=project,title='Red credential boundary',modelSelection=dict(provider='codex',model='gpt-6.1-sol'),runtimeMode='approval-required',interactionMode='default',envMode='local',branch=None,worktreePath=None,createdAt=now))
with tempfile.TemporaryDirectory(prefix='t055-red-token-',dir='/tmp') as directory:
    secret=Path(directory)/'token'
    control('token',thread=thread,path=str(secret))
    request=urllib.request.Request(origin+'/mcp',data=json.dumps(dict(jsonrpc='2.0',id=1,method='tools/list',params={})).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+secret.read_text()})
    with urllib.request.urlopen(request) as response: tools=json.load(response)
try:
    with urllib.request.urlopen(origin+'/api/a2a/issues?task=t055&thread='+thread) as response:
        panel=dict(status=response.status,body=json.load(response))
except urllib.error.HTTPError as error:
    panel=dict(status=error.code,body=error.read().decode())
report=dict(fork='6efac8432d7ae37e74b76e42d4e9fd3004d9a0e2',project=project,thread=thread,tools_list=tools,panel=panel,
    expected=['a2a_raise appears in authenticated tools/list','issue panel HTTP interface exists'])
with (out/(label+'.json')).open('x',encoding='utf-8') as file:
    json.dump(report,file,ensure_ascii=False,indent=2); file.write('\n')
names=[tool['name'] for tool in tools['result']['tools']]
print(json.dumps(dict(a2a_raise_present='a2a_raise' in names,panel_status=panel['status']),ensure_ascii=False))
assert 'a2a_raise' in names and panel['status']==200, 'T-055 contract absent at real HTTP/MCP entry'
