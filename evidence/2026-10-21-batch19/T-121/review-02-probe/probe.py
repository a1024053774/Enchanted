"""Probe: approved terminal executor in project 'proj' adds task=<own task> to inbox/stop commands."""
import json, os, socket, subprocess, sys, tempfile, time, uuid, sqlite3, re, base64
from pathlib import Path
SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])
fx = Path(tempfile.mkdtemp(prefix='t121probe-', dir='/private/tmp/t121-rev02')).resolve()
state, home, cwd = fx/'state', fx/'home', fx/'project'
for p in (state, home, cwd): p.mkdir()
env = {k: os.environ[k] for k in ['PATH','LANG','TMPDIR'] if k in os.environ}
env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', A2A_OPERATOR_CREDENTIAL=str(fx/'operator.json'))
cli = SRC/'workbench/src/gates/cli.ts'
def run_cli(*a):
    r = subprocess.run(['node', str(cli), '--state', str(state), *a], env=env, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr or r.stdout; return json.loads(r.stdout)
def req(command, identity=None, **data):
    with socket.socket(socket.AF_UNIX) as c:
        c.settimeout(30); c.connect(str(state/'control.sock'))
        c.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity))+'\n').encode())
        b = b''
        while b'\n' not in b:
            part = c.recv(65536); assert part; b += part
    return json.loads(b.split(b'\n',1)[0])
res = {}
try:
    run_cli('daemon_start')
    t0 = time.monotonic()
    while req('pane_layout').get('recovering') is not False:
        assert time.monotonic()-t0 < 10; time.sleep(.05)
    op = json.loads((fx/'operator.json').read_text())
    launch = run_cli('shell_start','--project','proj','--cwd',str(cwd))['launch']['id']
    win = req('window_open', op, launch=launch, project='proj'); assert win['ok'], win
    seq = 1
    req('window_input', win['identity'], sequence=seq, request_id=str(uuid.uuid4()), data=f'print -r -- $A2A_TERMINAL_TOKEN > {fx}/tok\r')
    t0 = time.monotonic()
    while not (fx/'tok').exists() or not (fx/'tok').read_text().strip():
        assert time.monotonic()-t0 < 20; time.sleep(.1)
    term = dict(kind='terminal', launch=launch, token=(fx/'tok').read_text().strip())
    rr = req('role_request', term, role='executor', cli='claude'); assert rr['ok'], rr
    d = req('role_request_decide', op, role_request=rr['role_request']['id'], approved=True); assert d['ok'], d
    dbs = [p for p in state.rglob('state.sqlite3')]
    res['dbs'] = [str(p) for p in dbs]
    gdb = next(p for p in dbs if sqlite3.connect(p).execute("SELECT name FROM sqlite_master WHERE name='inbox_records'").fetchone())
    con = sqlite3.connect(gdb, timeout=10)
    con.execute("INSERT INTO tasks VALUES (?,?)", ('own-task', json.dumps(dict(task_id='own-task', project_id='proj', repo=str(cwd), state='open'))))
    con.execute("INSERT INTO tasks VALUES (?,?)", ('other-task', json.dumps(dict(task_id='other-task', project_id='other', repo='/x', state='open'))))
    entry = dict(id='entry-other', schema=1, kind='assign', from_='ideation', to='executor', reply_to=None, refs=['task:other-task'],
                 created_at='2026-10-21T00:00:00Z', body='OTHER PROJECT SECRET')
    entry['from'] = entry.pop('from_')
    con.execute("INSERT INTO inbox_records VALUES (?,?)", (entry['id'], json.dumps(entry)))
    con.commit(); con.close()
    res['plain_inbox_list'] = req('inbox_list', term)
    res['own_task_inbox_list'] = req('inbox_list', term, task='own-task')
    res['other_task_inbox_list'] = req('inbox_list', term, task='other-task')
    res['own_task_inbox_ack_other'] = req('inbox_ack', term, task='own-task', id='entry-other')
    res['own_task_stop'] = req('stop', term, task='own-task', thread='x', stop_id='entry-other')
    res['own_task_inbox_send'] = req('inbox_send', term, task='own-task', kind='report', to='ideation', body='from proj terminal')
    res['create_with_task'] = req('create', term, task='new-task', project='proj', repo=str(cwd), branch='refs/heads/main', card_version=1)
    res['create_without_task'] = req('create', term, project='proj', repo=str(cwd), branch='refs/heads/main', card_version=1)
finally:
    try: run_cli('daemon_stop')
    except Exception as e: res['cleanup'] = str(e)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False)[:6000])
