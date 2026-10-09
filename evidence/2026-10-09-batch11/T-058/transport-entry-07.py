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
fork = Path('/Users/luckye/Documents/Code/synara')
label = sys.argv[1]
launch = json.loads((out/('server-'+label+'-launch.json')).read_text(encoding='utf-8'))
root = Path(launch['root'])
origin = json.loads((root/'ready.json').read_text(encoding='utf-8'))['origin']
results = out/label
results.mkdir()

def save(name, value):
    with (results/(name+'.json')).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

def now(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
def uid(): return str(uuid.uuid4())

def control(operation, **args):
    key = uid(); request = dict(operation=operation, **args)
    (root/'control'/f'{key}.request.json').write_text(json.dumps(request), encoding='utf-8')
    for _ in range(450):
        path = root/'control'/f'{key}.result.json'
        if path.exists():
            result = json.loads(path.read_text(encoding='utf-8'))
            if not result.get('pending'):
                save('control-'+key, dict(request=request, result=result))
                assert result['ok'], result
                return result['result']
        time.sleep(.1)
    raise TimeoutError(operation)

def http(path, request, token=None):
    headers = {'Content-Type':'application/json'}
    if token: headers['Authorization'] = 'Bearer '+token
    req = urllib.request.Request(origin+path, data=json.dumps(request).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as response: result = json.load(response)
    except urllib.error.HTTPError as response: result = json.load(response)
    save('http-'+str(len(list(results.iterdir()))), dict(path=path, request=request, result=result, provider_credential=bool(token)))
    return result

def gate(command, **args): return http('/api/a2a', dict(command=command, **args))
def mcp(token, name, **args):
    result = http('/mcp', dict(jsonrpc='2.0', id=uid(), method='tools/call', params=dict(name=name, arguments=args)), token)
    if 'error' in result: return dict(rpc_error=result['error'])
    content = result['result']['content']
    try: return json.loads(content[0]['text'])
    except json.JSONDecodeError: return dict(raw=content[0]['text'])

repo = root/'repo'; repo.mkdir()
genv = {k:v for k,v in os.environ.items() if k in ['PATH','SHELL','LANG','LC_ALL']}
genv.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
def git(*args): return subprocess.check_output(['git','-C',str(repo),*args], env=genv, text=True).strip()
git('init'); git('config','user.name','T058 independent entry'); git('config','user.email','fixture@example.invalid')
(repo/'fixture.txt').write_text('External Ω original\n', encoding='utf-8')
git('add','fixture.txt'); git('-c','core.hooksPath=/dev/null','commit','-m','Independent original')
(root/'instructions.txt').write_text('Controlled contract setup; no model.\n', encoding='utf-8')
(root/'oracle.py').write_text('from pathlib import Path\nimport sys\nassert Path(sys.argv[1],"fixture.txt").read_text()=="External Ω original\\n"\n', encoding='utf-8')
created = gate('create', task='t058', project='t058-control', repo=str(repo), base=git('rev-parse','HEAD'), oracle=str(root/'oracle.py'), instructions=str(root/'instructions.txt'))
assert created['ok'], created

expected = {
    'worker':['a2a_raise','a2a_submit'], 'reviewer':['a2a_raise'], 'monitor':['a2a_raise'],
    'ideation':['a2a_disposition','a2a_events','a2a_inbox_ack','a2a_inbox_list','a2a_inbox_send','a2a_issues','a2a_status','a2a_stop'],
    'executor':['a2a_attach','a2a_claim','a2a_create','a2a_dispatch','a2a_disposition','a2a_events','a2a_inbox_ack','a2a_inbox_list','a2a_inbox_send','a2a_integrate','a2a_issues','a2a_reclaim','a2a_revise','a2a_revoke','a2a_run','a2a_status','a2a_verify'],
}
threads = {}; tokens = {}; issued = {}
for role in ['executor','ideation','worker','reviewer','monitor']:
    result = gate('attach', task='t058', role='controller' if role in ['executor','ideation'] else role, preset=role,
        modelSelection=dict(provider='codex',model='gpt-6.1-sol'), runtimeMode='full-access', instructions=str(root/'instructions.txt'))
    assert result['ok'], result
    thread = result['attachment']['thread_id']; threads[role] = thread
    # Only the native provider state is controlled. The credential, gateway,
    # core, projection, routes and SQL recording remain the real product.
    time.sleep(.3)
    control('controlled-session', thread=thread, active=True, turn=uid(), workspace=str(repo))
    path = root/('private-'+role+'.token'); issued[role] = control('token', thread=thread, path=str(path))
    tokens[role] = path.read_text(encoding='utf-8')
    listed = http('/mcp', dict(jsonrpc='2.0', id=uid(), method='tools/list', params={}), tokens[role])
    observed = sorted(tool['name'] for tool in listed['result']['tools'])
    save('catalog-'+role, dict(expected=expected[role], observed=observed, credential=issued[role]))
    assert observed == expected[role], (role, observed)

for role, name in [('worker','a2a_create'),('worker','a2a_inbox_send'),('ideation','a2a_claim'),('reviewer','a2a_submit'),('monitor','a2a_inbox_list'),('executor','a2a_stop')]:
    denied = mcp(tokens[role], name, task='t058', to='executor', kind='assign', body='forged', thread=threads['worker'], stop_id='missing')
    assert denied['error']['code'] == 'capability_denied', (role, name, denied)

entry = mcp(tokens['ideation'], 'a2a_inbox_send', to='executor', kind='assign', body='新哨兵 Ω\n尾行保留', refs=['ticket:T-058'], **{'from':'executor'})
assert entry['ok'] and entry['entry']['from'] == 'ideation', entry
entry_id = entry['entry']['id']; message_id = entry['delivery']['message']
native = control('thread', thread=threads['executor'])['value']
message = next(m for m in native['messages'] if m['id']==message_id)
assert message['text'] == '收件箱 '+entry_id+'：新哨兵 Ω' and message['dispatchOrigin']=='agent', message
assert entry['entry']['body'] == '新哨兵 Ω\n尾行保留'
listed = mcp(tokens['executor'], 'a2a_inbox_list')
assert any(v['entry']['id']==entry_id for v in listed['entries'])
ack = mcp(tokens['executor'], 'a2a_inbox_ack', id=entry_id)
assert ack['entry']['reply_to']==entry_id and ack['entry']['kind']=='ack'
again = mcp(tokens['executor'], 'a2a_inbox_ack', id=entry_id)
assert again['entry']['id']==ack['entry']['id']
assert mcp(tokens['ideation'], 'a2a_inbox_ack', id=ack['entry']['id'])['error']=='ack_is_terminal'
assert not any(v['entry']['id']==entry_id for v in mcp(tokens['executor'], 'a2a_inbox_list')['entries'])

raised = mcp(tokens['reviewer'], 'a2a_raise', title='外部问题 δ', body='保存至已有问题记录', blocking=True)
assert raised['ok'], raised
closed = mcp(tokens['ideation'], 'a2a_disposition', task='t058', issue=raised['id'], action='close', reason='拒绝伪关', basis='外部哨兵')
assert closed['error']=='blocking_requires_user', closed
control('command', command=dict(type='thread.archive',commandId=uid(),threadId=threads['reviewer']))
answered = gate('answer_issue', task='t058', issue=raised['id'], answer='用户答复保留 Ω')
assert answered['ok'], answered
forwarded = next(v for v in mcp(tokens['executor'], 'a2a_inbox_list')['entries'] if v['entry'].get('reason')=='session-ended')
assert forwarded['entry']['to']=='executor' and forwarded['entry']['reply_to'] in [r['id'] for r in answered['records'] if r['kind']=='answer']

# CLI is the actual remote entry, not a local database mutation substitute.
request = dict(command='inbox_list', role='executor')
argv = ['./a2a/scripts/bun','run','packages/a2a-gates/src/cli.ts',origin,json.dumps(request)]
env = {**genv, 'A2A_SYNARA_SLOT':'s11-t058-'+label, 'A2A_GATE_BEARER':'fixture-local-owner'}
run = subprocess.run(argv, cwd=fork, env=env, capture_output=True, text=True)
save('cli-list', dict(argv=argv, cwd=str(fork), returncode=run.returncode, stdout=run.stdout, stderr=run.stderr))
assert run.returncode==0
assert json.loads(run.stdout)['entries']==gate('inbox_list', role='executor')['entries']

with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
    inputs = [json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
    assert not any(v['target'].get('message')==message_id for v in inputs), inputs
    counts = dict(inbox_records=db.execute('SELECT count(*) FROM inbox_records').fetchone()[0], inbox_deliveries=db.execute('SELECT count(*) FROM inbox_deliveries').fetchone()[0])
save('transport-oracle', dict(status='PASS', source_revision=launch['source_revision'], tracked_status=launch['tracked_status'], controlled_native_provider_state=True,
    new_model_turns=0, threads=threads, issued_capabilities=issued, sent=entry, native_message=message, ack=ack, ended_forward=forwarded, counts=counts))
print('PASS real HTTP/MCP/CLI, exact role catalogs, credential denials, agent wake record and ended forward; native provider state controlled')
