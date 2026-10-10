import datetime as dt
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import uuid
out=Path(__file__).resolve().parent;label=sys.argv[1]
launch=json.loads((out/('server-'+label+'-launch.json')).read_text(encoding='utf-8'));root=Path(launch['root'])
spec=importlib.util.spec_from_file_location('fixture_api',out.parents[1]/'2026-10-09-batch8/T-055/fixture-api.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api);f=api.Fixture(root)
thread=str(uuid.uuid4());now=dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
f.control('command',command=dict(type='thread.create',commandId=str(uuid.uuid4()),threadId=thread,projectId='t064-control',title='T064 普通会话反例',
    modelSelection=dict(provider='codex',model='gpt-6.1-sol'),runtimeMode='full-access',interactionMode='default',envMode='local',branch=None,worktreePath=None,createdAt=now))
path=root/'private-ordinary14.token';issued=f.control('token',thread=thread,path=str(path));token=path.read_text(encoding='utf-8')
f.control('controlled-session',thread=thread,active=True,turn=str(uuid.uuid4()),workspace=str(root/'repo'))
expected=['automation:write','browser:control','device:control','diagnostics:read','thread:read','thread:write']
assert issued['capabilities']==expected
request=dict(jsonrpc='2.0',id=str(uuid.uuid4()),method='tools/list',params={})
listed=f.http('/mcp',request,token);names=sorted(tool['name'] for tool in listed['result']['tools'])
assert not any(name.startswith('a2a_') for name in names),names
denied=f.http('/mcp',dict(jsonrpc='2.0',id=str(uuid.uuid4()),method='tools/call',params=dict(name='a2a_raise',arguments=dict(title='必须拒绝普通凭据'))),token)
with (out/'ordinary-raw15.json').open('x',encoding='utf-8') as stream:json.dump(dict(issued=issued,listed=listed,denied=denied),stream,ensure_ascii=False,indent=2)
body=json.loads(denied['result']['content'][0]['text']);assert body['error']['code']=='capability_denied'
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
    inputs=[json.loads(row[0]) for row in db.execute("SELECT data FROM user_inputs WHERE json_extract(data,'$.channel')='settings-page' ORDER BY rowid")]
    changes=[json.loads(row[0]) for row in db.execute('SELECT data FROM role_permission_changes ORDER BY seq')]
assert len(inputs)==len(changes)==11
assert [change['command'] for change in changes[-2:]]==['save','reset']
for change,input_ in zip(changes,inputs):assert input_['id']==change['input_id'] and input_['content']==change
with (out/'ordinary-and-audit-14.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(source_revision=launch['source_revision'],expected_capabilities=expected,issued=issued,actual_tools=names,
        denied=denied,settings_inputs=inputs,changes=changes,status='PASS'),stream,ensure_ascii=False,indent=2)
print('PASS ordinary credential matches parent capabilities, real MCP has no a2a authority, all 11 settings/UI actions have atomic audit')
