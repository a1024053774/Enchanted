import concurrent.futures
import datetime as dt
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

out = Path(__file__).resolve().parent
label = sys.argv[1]
launch = json.loads((out / ('server-' + label + '-launch.json')).read_text(encoding='utf-8'))
root = Path(launch['root'])
origin = json.loads((root/'ready.json').read_text(encoding='utf-8'))['origin']
results = out / (label + '-entry')
results.mkdir()
sequence = 0
def save(name, value):
    with (results / (name+'.json')).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
def uid(): return str(uuid.uuid4())
def now(): return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
def control(operation, expect_ok=True, **args):
    key = uid()
    request = dict(operation=operation, **args)
    (root/'control'/(key+'.request.json')).write_text(json.dumps(request), encoding='utf-8')
    for _ in range(450):
        path = root/'control'/(key+'.result.json')
        if path.exists():
            result = json.loads(path.read_text(encoding='utf-8'))
            if not result.get('pending'):
                save('control-'+key, dict(request=request, result=result))
                assert bool(result['ok']) == expect_ok, result
                return result.get('result', result)
        time.sleep(.1)
    raise TimeoutError(operation)
def http(path, body=None, token=None, persist=True):
    headers = {'Content-Type':'application/json'}
    if token: headers['Authorization'] = 'Bearer '+token
    request = urllib.request.Request(origin+path, data=None if body is None else json.dumps(body).encode(), headers=headers)
    try: response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as error: response = error
    with response:
        status = response.status
        raw = response.read().decode('utf-8')
        try: result = json.loads(raw)
        except json.JSONDecodeError: result = {'raw':raw}
    if persist:
        global sequence
        sequence += 1
        save('http-'+str(sequence), dict(path=path, request=body, status=status, result=result, credential_supplied=bool(token)))
    return status, result
def gate(command, **args):
    status, result = http('/api/a2a', dict(command=command, **args))
    assert status == 200 and result['ok'], result
    return result
def issue(thread, name):
    path = root / ('private-'+name+'.token')
    control('token', thread=thread, path=str(path))
    return path.read_text(encoding='utf-8')
def catalog(token):
    status, result = http('/mcp', dict(jsonrpc='2.0', id=uid(), method='tools/list', params={}), token)
    assert status == 200, result
    return sorted(tool['name'] for tool in result['result']['tools'])
def call(token, name, **args):
    status, result = http('/mcp', dict(jsonrpc='2.0', id=uid(), method='tools/call', params={'name':name,'arguments':args}), token)
    assert status == 200, result
    text = result['result']['content'][0]['text']
    try: return json.loads(text)
    except json.JSONDecodeError: return {'raw':text}
def permissions():
    status, value = http('/api/a2a/role-permissions')
    assert status == 200, value
    return value
def edit(role, command='save', selection=None, revision=None):
    if revision is None: revision = next(row['revision'] for row in permissions()['roles'] if row['role']==role)
    body = dict(command=command, role=role, revision=revision)
    if command=='save': body['selection']=selection
    return http('/api/a2a/role-permissions', body)

expected_caps = {'executor':['a2a:operate','a2a:read','a2a:inbox'], 'ideation':['a2a:read','a2a:inbox','a2a:stop'],
    'worker':['a2a:submit','a2a:raise'], 'reviewer':['a2a:raise'], 'monitor':['a2a:raise']}
expected_tools = {'worker':['a2a_raise','a2a_submit'], 'reviewer':['a2a_raise'], 'monitor':['a2a_raise'],
    'ideation':['a2a_disposition','a2a_events','a2a_inbox_ack','a2a_inbox_list','a2a_inbox_send','a2a_issues','a2a_status','a2a_stop'],
    'executor':['a2a_attach','a2a_claim','a2a_create','a2a_dispatch','a2a_disposition','a2a_events','a2a_inbox_ack','a2a_inbox_list','a2a_inbox_send','a2a_integrate','a2a_issues','a2a_reclaim','a2a_revise','a2a_revoke','a2a_run','a2a_status','a2a_verify']}
initial = permissions()
assert [row['role'] for row in initial['roles']]==list(expected_caps)
assert {row['role']:row['effective']['capabilities'] for row in initial['roles']} == expected_caps
assert all(row['custom'] is None and row['effective']['autoApproveTools'] is None for row in initial['roles'])
repo = root/'repo'; repo.mkdir()
genv = {k:v for k,v in os.environ.items() if k in ('PATH','SHELL','LANG','LC_ALL')}
genv.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
def git(*args): return subprocess.check_output(['git','-C',str(repo),*args], env=genv, text=True).strip()
git('init'); git('config','user.name','T064 fixture'); git('config','user.email','fixture@example.invalid')
(repo/'fixture.txt').write_text('T064 independent original Ω\n', encoding='utf-8')
git('add','fixture.txt'); git('-c','core.hooksPath=/dev/null','commit','-m','Independent fixture')
(root/'instructions.txt').write_text('T064 controlled contract setup, no model.\n', encoding='utf-8')
(root/'oracle.py').write_text('from pathlib import Path\nimport sys\nassert Path(sys.argv[1],"fixture.txt").read_text()=="T064 independent original Ω\\n"\n', encoding='utf-8')
gate('create',task='t064',project='t064-control',repo=str(repo),base=git('rev-parse','HEAD'),oracle=str(root/'oracle.py'),instructions=str(root/'instructions.txt'))
threads={}; tokens={}
for role in expected_caps:
    attached=gate('attach',task='t064',role='controller' if role in ('executor','ideation') else role,preset=role,
        modelSelection={'provider':'codex','model':'gpt-6.1-sol'},runtimeMode='full-access',instructions=str(root/'instructions.txt'))
    thread=attached['attachment']['thread_id'];threads[role]=thread
    time.sleep(.2)
    control('controlled-session',thread=thread,active=True,turn=uid(),workspace=str(repo))
    tokens[role]=issue(thread,role)
    actual=catalog(tokens[role]);save('catalog-'+role,dict(expected=expected_tools[role],observed=actual))
    assert actual==expected_tools[role], (role,actual)

assert edit('worker',selection={'capabilities':['a2a:raise','a2a:read'],'autoApproveTools':['a2a_raise']})[0]==200
assert catalog(tokens['worker'])==['a2a_raise','a2a_submit']
fresh=issue(threads['worker'],'worker-new')
assert catalog(fresh)==['a2a_events','a2a_issues','a2a_raise','a2a_status']
assert call(fresh,'a2a_status',task='t064')['ok']
assert call(fresh,'a2a_submit',task='t064')['error']['code']=='capability_denied'
raised=call(fresh,'a2a_raise',title='T064 新凭据实际问题',body='独立哨兵 Ω',blocking=True)
assert raised['ok'],raised
assert call(tokens['worker'],'a2a_raise',title='T064 旧凭据仍可上报')['ok']
assert edit('executor',selection={'capabilities':expected_caps['executor'],'autoApproveTools':['a2a_disposition']})[0]==200
executor_fresh=issue(threads['executor'],'executor-new')
assert call(executor_fresh,'a2a_disposition',task='t064',issue=raised['id'],action='dismiss')['error']=='user_required'
assert call(executor_fresh,'a2a_disposition',task='t064',issue=raised['id'],action='close',reason='反例',basis='不可越过核心')['error']=='blocking_requires_user'
assert edit('monitor',selection={'capabilities':[],'autoApproveTools':[]})[0]==200
empty=issue(threads['monitor'],'empty')
assert catalog(empty)==[]
assert call(empty,'a2a_raise',title='必须拒绝')['error']['code']=='capability_denied'
assert catalog(tokens['monitor'])==['a2a_raise']
assert edit('monitor','reset')[0]==200
restored=issue(threads['monitor'],'restored')
assert catalog(restored)==['a2a_raise']

before=permissions()
revision=next(row['revision'] for row in before['roles'] if row['role']=='monitor')
requests=[dict(command='save',role='monitor',revision=revision,selection={'capabilities':caps,'autoApproveTools':[]}) for caps in ([],['a2a:raise'])]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    concurrent_results=list(pool.map(lambda body:http('/api/a2a/role-permissions',body,persist=False),requests))
save('concurrent-cas',dict(requests=requests,results=concurrent_results))
assert sorted(status for status,_ in concurrent_results)==[200,409],concurrent_results
assert len(permissions()['changes'])==len(before['changes'])+1
assert edit('monitor','reset')[0]==200
changes=permissions()['changes']
assert edit('worker',selection={'capabilities':['a2a:gone'],'autoApproveTools':[]})[0]==400
assert edit('worker',selection={'capabilities':[],'autoApproveTools':['a2a_disposition']})[0]==400
assert permissions()['changes']==changes

with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
    bad=json.dumps({'capabilities':['a2a:removed'],'autoApproveTools':[]})
    db.execute('INSERT INTO role_permissions(role,revision,data) VALUES (?,?,?)',('reviewer',7,bad))
invalid=permissions();view=next(row for row in invalid['roles'] if row['role']=='reviewer')
assert view['effective'] is None and view['custom']['capabilities']==['a2a:removed']
control('token',expect_ok=False,thread=threads['reviewer'],path=str(root/'private-invalid.token'))
assert edit('reviewer','reset',revision=7)[0]==200
assert edit('worker','reset')[0]==200
assert edit('executor','reset')[0]==200
final=permissions()
assert all(row['custom'] is None for row in final['roles'])
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
    inputs=[json.loads(row[0]) for row in db.execute("SELECT data FROM user_inputs WHERE json_extract(data,'$.channel')='settings-page' ORDER BY rowid")]
    all_changes=[json.loads(row[0]) for row in db.execute('SELECT data FROM role_permission_changes ORDER BY seq')]
assert len(inputs)==len(all_changes)==9,(len(inputs),len(all_changes))
for change, user_input in zip(all_changes,inputs):
    assert user_input['id']==change['input_id'] and user_input['content']==change
    assert user_input['form']=='action' and user_input['certainty']=='observed' and change['actor']=='user'
    assert change['text']==user_input['text'] and dt.datetime.fromisoformat(change['created_at'].replace('Z','+00:00')).tzinfo
save('audit',dict(inputs=inputs,changes=all_changes))
save('oracle',dict(status='PASS',controlled_native_provider_state=True,model_turns=0,threads=threads,
    spec_expected_capabilities=expected_caps,spec_expected_tools=expected_tools,raised=raised,
    ordinary_processes_not_used=True,final_roles=final['roles']))
print('PASS actual owner HTTP/MCP: five default catalogs, custom/frozen credentials, calls and denials, empty set, CAS, invalid config, restore and immutable audit')
