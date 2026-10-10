"""Real isolated server/MCP/SQLite; controlled active sessions, zero model turns."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
import uuid

p = argparse.ArgumentParser()
p.add_argument('label')
p.add_argument('--mode', choices=['red', 'green'], required=True)
p.add_argument('--legacy', type=Path)
a = p.parse_args()
out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
run = out / a.label
run.mkdir()
root = Path('/Volumes/WD-Elements/dev-cache/synara/instances') / ('t066-' + a.label)
root.mkdir(mode=0o700)
for name in ('os-home', 'codex-empty', 'claude-empty'):
    (root / name).mkdir(mode=0o700)
env = {k: v for k, v in os.environ.items() if k in ('PATH', 'SHELL', 'LANG', 'LC_ALL')}
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fork, text=True).strip()
env.update(HOME=str(root/'os-home'), CODEX_HOME=str(root/'codex-empty'),
           CLAUDE_CONFIG_DIR=str(root/'claude-empty'), A2A_SYNARA_SLOT='t066-' + a.label,
           T058_ROOT=str(root), T058_FORK=str(fork), T058_SOURCE_REVISION=revision)
argv = ['./a2a/scripts/bun', 'run', str(out/'server-fixture.ts')]
log = (run/'server.log').open('x', encoding='utf-8')
proc = subprocess.Popen(argv, cwd=fork, env=env, stdin=subprocess.DEVNULL,
                        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
trace = []
checks = []
def save(name, value):
    with (run/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
save('launch.json', dict(argv=argv, cwd=str(fork), root=str(root), pid=proc.pid,
    revision=revision, source_status=subprocess.check_output(
        ['git', 'status', '--short', '--untracked-files=no'], cwd=fork, text=True),
    isolated_environment=env, model_turns=0))
def uid(): return str(uuid.uuid4())
def control(operation, **args):
    key=uid(); request=dict(operation=operation, **args)
    (root/'control'/(key+'.request.json')).write_text(json.dumps(request), encoding='utf-8')
    end=time.monotonic()+45
    while time.monotonic()<end:
        path=root/'control'/(key+'.result.json')
        if path.exists():
            result=json.loads(path.read_text(encoding='utf-8'))
            if not result.get('pending'):
                trace.append(dict(control=request, response=result))
                assert result['ok'], result
                return result['result']
        time.sleep(.1)
    raise TimeoutError(operation)
def http(path, body=None, token=None):
    headers={'Content-Type':'application/json'}
    if token: headers['Authorization']='Bearer '+token
    request=urllib.request.Request(origin+path, data=None if body is None else json.dumps(body).encode(), headers=headers)
    try: response=urllib.request.urlopen(request, timeout=45)
    except urllib.error.HTTPError as e: response=e
    with response: status=response.status; result=json.load(response)
    trace.append(dict(path=path, request=body, status=status, response=result, credential_supplied=bool(token)))
    return result
def gate(command, **args): return http('/api/a2a', dict(command=command, **args))
def call(token, **args):
    result=http('/mcp', dict(jsonrpc='2.0',id=uid(),method='tools/call',
        params=dict(name='a2a_stop',arguments=args)),token)
    if 'error' in result: return result
    return json.loads(result['result']['content'][0]['text'])
def check(name, actual, expected):
    checks.append(dict(name=name, observed=actual, expected=expected, pass_=actual==expected))
def events():
    result=gate('events',task='t066')
    assert result['ok'],result
    return result['events']
def emergency(): return [e for e in events() if e['type']=='emergency_interrupt_requested']
tokens={}; threads={}; turns={}
try:
    for _ in range(450):
        if (root/'ready.json').exists(): break
        if proc.poll() is not None: raise RuntimeError('server exited; see log')
        time.sleep(.1)
    else: raise TimeoutError('server ready')
    origin=json.loads((root/'ready.json').read_text(encoding='utf-8'))['origin']
    repo=root/'repo'; repo.mkdir()
    genv={**env,'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1'}
    def git(*args): return subprocess.check_output(['git','-C',str(repo),*args],env=genv,text=True).strip()
    git('init');git('config','user.name','T066 fixture');git('config','user.email','fixture@example.invalid')
    (repo/'sentinel.txt').write_text('独立哨兵 Ω\n',encoding='utf-8')
    git('add','sentinel.txt');git('-c','core.hooksPath=/dev/null','commit','-m','fixture')
    (root/'instructions.txt').write_text('Controlled session; no provider turn.\n',encoding='utf-8')
    (root/'oracle.py').write_text('raise SystemExit(0)\n',encoding='utf-8')
    created=gate('create',task='t066',project='t066',repo=str(repo),base=git('rev-parse','HEAD'),
        oracle=str(root/'oracle.py'),instructions=str(root/'instructions.txt'))
    assert created['ok'],created
    permissions=http('/api/a2a/role-permissions')
    view=next(r for r in permissions['roles'] if r['role']=='executor')
    updated=http('/api/a2a/role-permissions',dict(command='save',role='executor',revision=view['revision'],
        selection=dict(capabilities=['a2a:operate','a2a:read','a2a:inbox','a2a:stop'],autoApproveTools=None)))
    assert 'roles' in updated,updated
    for role in ('executor','ideation','worker'):
        attached=gate('attach',task='t066',role='controller' if role!='worker' else role,preset=role,
            modelSelection=dict(provider='codex',model='gpt-6.1-sol'),runtimeMode='full-access',instructions=str(root/'instructions.txt'))
        assert attached['ok'],attached
        threads[role]=attached['attachment']['thread_id']
        turns[role]=uid()
        time.sleep(.3)
        control('controlled-session',thread=threads[role],active=True,turn=turns[role],workspace=str(repo))
        token_path=root/('private-'+role+'.token')
        identity=control('token',thread=threads[role],path=str(token_path))
        tokens[role]=token_path.read_text(encoding='utf-8')
        check('credential-role-'+role,identity['a2aPermissions']['role'],role)
    receipts={}
    for name in ('normal','ack-first','concurrent'):
        receipt=gate('inbox_send',**{'kind':'stop','from':'user','to':'executor','refs':['thread:'+threads['worker']],'body':'停止指定会话 '+name})
        if not receipt.get('entry'):
            raise AssertionError(receipt)
        receipts[name]=receipt['entry']
    fresh=receipts['normal']
    check('fresh-stop-rejected',call(tokens['executor'],thread=threads['worker'],stop_id=fresh['id']).get('error'),'stop_too_early')
    ack=gate('inbox_ack',role='executor',id=receipts['ack-first']['id'])
    assert ack.get('entry',{}).get('kind')=='ack',ack
    # Natural clock at the real boundary: no event timestamp is modified.
    deadline=dt.datetime.fromisoformat(receipts['concurrent']['created_at'].replace('Z','+00:00')).timestamp()+121
    print('receipts created; waiting for real two-minute threshold',flush=True)
    while time.time()<deadline: time.sleep(min(1,deadline-time.time()))
    before=gate('status',task='t066')['task']
    native_before=control('events')
    forged=dict(thread=threads['worker'],stop_id=fresh['id'],actor='ideation',address='ideation',
                caller_thread='forged-thread',caller_turn='forged-turn',callerA2ARole='ideation')
    result=call(tokens['executor'],**forged)
    check('executor-stop-succeeded',result.get('interruptRequested'),True)
    record=emergency()[-1]
    save('executor-event.json',record)
    check('actual-executor-address',record['details'].get('actor'),'executor')
    check('credential-thread',record['details'].get('caller_thread'),threads['executor'])
    check('credential-turn',record['details'].get('caller_turn'),turns['executor'])
    check('target-preserved',record['details'].get('thread'),threads['worker'])
    check('task-state-unchanged',gate('status',task='t066')['task'],before)
    native_after=control('events')
    delta=[e for e in native_after if e['sequence']>max((v['sequence'] for v in native_before),default=0)]
    save('native-stop-delta.json',delta)
    # Provider consumers append their own activity/session facts. Only the
    # gate's command receipts establish what action this tool requested.
    check('only-interrupt-command',[e['type'] for e in delta if e['commandId'].startswith('a2a:')],['thread.turn-interrupt-requested'])
    if a.mode=='green':
        if a.legacy:
            legacy=json.loads(a.legacy.read_text(encoding='utf-8'))
            legacy_details=json.dumps(legacy['details'],ensure_ascii=False)
            with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
                db.execute('INSERT INTO events(time,task,attempt,type,details) VALUES (?,?,?,?,?)',
                    (legacy['time'],'t066',None,legacy['type'],legacy_details))
                legacy_seq=db.execute('SELECT max(seq) FROM events').fetchone()[0]
            check('legacy-read-unchanged',next(e for e in events() if e['seq']==legacy_seq)['details'],legacy['details'])
        # Restore controlled target activity after the actual interrupt request.
        control('controlled-session',thread=threads['worker'],active=True,turn=uid(),workspace=str(repo))
        ideation_result=call(tokens['ideation'],thread=threads['worker'],stop_id=fresh['id'])
        check('ideation-stop-succeeded',ideation_result.get('interruptRequested'),True)
        ideation=emergency()[-1]
        check('ideation-address-preserved',ideation['details'].get('actor'),'ideation')
        check('ideation-caller-thread',ideation['details'].get('caller_thread'),threads['ideation'])
        check('ideation-caller-turn',ideation['details'].get('caller_turn'),turns['ideation'])
        check('same-target-two-roles',[record['details']['thread'],ideation['details']['thread']],[threads['worker']]*2)
        count=len(emergency())
        check('ack-rejects-stop',call(tokens['executor'],thread=threads['worker'],stop_id=receipts['ack-first']['id']).get('error'),'stop_already_acknowledged')
        check('ack-no-event',len(emergency()),count)
        # No stop grant on the real worker credential.
        denied=call(tokens['worker'],thread=threads['worker'],stop_id=fresh['id'])
        check('missing-capability-rejected',denied.get('error',{}).get('code'),'capability_denied')
        control('controlled-session',thread=threads['executor'],active=False,turn=uid(),workspace=str(repo))
        inactive=call(tokens['executor'],thread=threads['worker'],stop_id=fresh['id'])
        check('inactive-credential-rejected',inactive.get('error',{}).get('code'),'caller_turn_inactive')
        check('inactive-no-event',len(emergency()),count)
        if a.legacy:
            with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
                check('legacy-stored-bytes-unchanged',db.execute('SELECT details FROM events WHERE seq=?',(legacy_seq,)).fetchone()[0],legacy_details)
    save('events.json',events())
    save('identity.json',dict(threads=threads,turns=turns,receipts=receipts,model_turns=0))
    save('checks.json',checks)
    failures=[c['name'] for c in checks if not c['pass_']]
    save('verdict.json',dict(status='PASS' if not failures else 'FAIL',failures=failures,mode=a.mode))
    print(json.dumps(dict(status='PASS' if not failures else 'FAIL',failures=failures),ensure_ascii=False),flush=True)
    if failures: raise SystemExit(1)
finally:
    save('trace.json',trace)
    proc.send_signal(signal.SIGTERM)
    try: proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill();proc.wait(timeout=10)
    log.close()
    for path in root.glob('private-*.token'): path.unlink()
    # Preserve the database and controlled inputs; credentials never enter evidence.
    dbpath=root/'userdata/a2a-gates/state.sqlite3'
    if dbpath.exists():
        with sqlite3.connect(dbpath) as source, sqlite3.connect(run/'state.sqlite3') as target:
            source.backup(target)
    save('shutdown.json',dict(pid=proc.pid,exit_code=proc.returncode,private_tokens_removed=True))
