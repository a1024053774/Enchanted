import importlib.util
import json
from pathlib import Path
import sys
import uuid
out=Path(__file__).resolve().parent
label=sys.argv[1]
launch=json.loads((out/('server-'+label+'-launch.json')).read_text(encoding='utf-8'))
root=Path(launch['root']);oracle=json.loads((out/(label+'-entry')/'oracle.json').read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('api',out.parents[1]/'2026-10-09-batch8/T-055/fixture-api.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api);f=api.Fixture(root)
thread=oracle['threads']['ideation'];target=oracle['threads']['worker']
f.control('controlled-session',thread=thread,active=True,turn=str(uuid.uuid4()),workspace=str(root/'repo'))
base_path=root/('private-cap-base-'+str(uuid.uuid4())+'.token')
f.control('token',thread=thread,path=str(base_path))
old=base_path.read_text(encoding='utf-8')
def invoke(token):
    request=dict(jsonrpc='2.0',id=str(uuid.uuid4()),method='tools/call',params=dict(name='a2a_stop',arguments=dict(thread=target,stop_id='t064-deliberately-missing')))
    return dict(request=request,response=f.http('/mcp',request,token))
before=invoke(old)
view=next(row for row in f.http('/api/a2a/role-permissions')['roles'] if row['role']=='ideation')
saved=f.http('/api/a2a/role-permissions',dict(command='save',role='ideation',revision=view['revision'],selection=dict(capabilities=['a2a:read','a2a:inbox','a2a:stop','a2a:operate'],autoApproveTools=None)))
assert 'roles' in saved,saved
path=root/('private-cap-composition-'+str(uuid.uuid4())+'.token')
issued=f.control('token',thread=thread,path=str(path));fresh=path.read_text(encoding='utf-8')
after=invoke(fresh)
revision=next(row['revision'] for row in f.http('/api/a2a/role-permissions')['roles'] if row['role']=='ideation')
restored=f.http('/api/a2a/role-permissions',dict(command='reset',role='ideation',revision=revision))
record=dict(source_revision=launch['source_revision'],issued=issued,before=before,after=after,restored=restored,
    expected='Adding operate must not remove stop authority; both calls should reach the same missing-stop business validation')
with (out/('cap-composition-'+label+'-active-'+sys.argv[2]+'.json')).open('x',encoding='utf-8') as stream:json.dump(record,stream,ensure_ascii=False,indent=2)
before_error=json.loads(before['response']['result']['content'][0]['text'])['error']
after_error=json.loads(after['response']['result']['content'][0]['text'])['error']
print(json.dumps(dict(before=before_error,after=after_error),ensure_ascii=False))
assert before_error=='unknown_inbox_entry','The absent stop receipt must reach entry validation, not an unrelated rejection'
assert after_error=='unknown_inbox_entry','T064 added capability removed an existing stop authority'
