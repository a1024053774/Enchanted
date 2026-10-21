"""Rev03 probe: approved terminal executor in 'proj'. Checks answer_issue provenance, card_* on foreign pending
task ids, role_request without wait, close-vs-approve race, daemon_stop during a wait."""
import json, os, socket, subprocess, sys, tempfile, time, uuid, sqlite3, threading
from pathlib import Path
SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])
fx = Path(tempfile.mkdtemp(prefix='p3-', dir='/private/tmp/t121-rev03')).resolve()
state, home, cwd, other, out = fx/'state', fx/'home', fx/'proj', fx/'other', fx/'out'
for p in (state, home, cwd, other, out): p.mkdir()
env = {k: os.environ[k] for k in ['PATH','LANG','TMPDIR'] if k in os.environ}
env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', A2A_OPERATOR_CREDENTIAL=str(fx/'operator.json'),
           GIT_AUTHOR_NAME='p', GIT_AUTHOR_EMAIL='p@example.invalid', GIT_COMMITTER_NAME='p', GIT_COMMITTER_EMAIL='p@example.invalid')
cli = SRC/'workbench/src/gates/cli.ts'
def run_cli(*a):
    r = subprocess.run(['node', str(cli), '--state', str(state), *a], env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr or r.stdout; return json.loads(r.stdout)
def conn(command, identity=None, **data):
    c = socket.socket(socket.AF_UNIX); c.settimeout(60); c.connect(str(state/'control.sock'))
    c.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity))+'\n').encode())
    return c
def read(c):
    b = b''
    while b'\n' not in b:
        part = c.recv(65536); assert part, 'closed'; b += part
    c.close(); return json.loads(b.split(b'\n',1)[0])
def req(command, identity=None, **data): return read(conn(command, identity, **data))
def card(task):
    path = out/f'{task}.card.json'
    path.write_text(json.dumps(dict(id=task, source=None, goal='probe '+task, non_goals=['无'],
        paths=dict(allow=['check.py'], deny=[]), oracle_paths=['check.py'],
        completion_conditions=[dict(argv=['python3','check.py'])], red_commands=[], task_type='测试',
        repair_target=None, complexity='S', executor=dict(cli='Codex', model='m', effort='high'),
        base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
    return str(path)
def rows(name):
    return [p for p in state.rglob('*.sqlite3') if sqlite3.connect(p).execute("SELECT name FROM sqlite_master WHERE name=?", (name,)).fetchone()]
res = {}
try:
    run_cli('daemon_start')
    t0 = time.monotonic()
    while req('pane_layout').get('recovering') is not False:
        assert time.monotonic()-t0 < 10; time.sleep(.05)
    op = json.loads((fx/'operator.json').read_text())
    for repo in (cwd, other):
        subprocess.run(['git','init','-q','-b','main',str(repo)], check=True, env=env)
        (repo/'check.py').write_text('print("ok")\n')
        subprocess.run(['git','-C',str(repo),'add','check.py'], check=True, env=env)
        subprocess.run(['git','-C',str(repo),'commit','-q','-m','init'], check=True, env=env)
        assert req('project_open', op, repo=str(repo))['ok']
    def terminal(name):
        launch = run_cli('shell_start','--project','proj','--cwd',str(cwd))['launch']['id']
        win = req('window_open', op, launch=launch, project='proj'); assert win['ok'], win
        req('window_input', win['identity'], sequence=1, request_id=str(uuid.uuid4()), data=f'print -r -- $A2A_TERMINAL_TOKEN > {fx}/{name}\r')
        t0 = time.monotonic()
        while not (fx/name).exists() or not (fx/name).read_text().strip():
            assert time.monotonic()-t0 < 20; time.sleep(.1)
        return dict(kind='terminal', launch=launch, token=(fx/name).read_text().strip())
    term = terminal('tokA')
    rr = req('role_request', term, role='executor', cli='claude'); assert rr['ok'], rr
    assert req('role_request_decide', op, role_request=rr['role_request']['id'], approved=True)['ok']
    # own task via terminal
    assert req('card_save', term, task='own-1', card=card('own-1'), expected_version=0)['ok']
    res['create_own'] = req('create', term, task='own-1', project='proj', repo=str(cwd), branch='refs/heads/main', card_version=1)['ok']
    # P1: answer_issue as the terminal executor -> recorded as the user's answer?
    gdb = rows('issue_records')[0]
    con = sqlite3.connect(gdb, timeout=10)
    issue = dict(id='iss-1', issue_id='iss-1', turn_id='turn-x', schema=1, kind='issue', number=1, task_id='own-1', attempt_id=None, thread_id='thr-x', from_='worker:thr-x',
                 to='executor', title='需要用户决定', body='问用户的问题', blocking=True, refs=[], created_at='2026-10-21T00:00:00Z', reply_to=None)
    issue['from'] = issue.pop('from_')
    con.execute("INSERT INTO issue_records VALUES (?,?,?,?)", ('iss-1','own-1','thr-x', json.dumps(issue)))
    con.commit(); con.close()
    res['answer_issue'] = req('answer_issue', term, task='own-1', issue='iss-1', answer='主控冒充的用户答复')
    con = sqlite3.connect(gdb, timeout=10)
    res['user_inputs_after'] = [json.loads(r[0]) for r in con.execute("SELECT data FROM user_inputs WHERE task='own-1'")]
    res['answer_records'] = [json.loads(r[0]) for r in con.execute("SELECT data FROM issue_records WHERE task='own-1'") if json.loads(r[0])['kind']!='issue']
    con.close()
    # P2: another project's controller (operator) saved a card for a task not yet created.
    assert req('card_save', op, task='other-2', card=card('other-2'), expected_version=0)['ok']
    res['card_show_foreign_pending'] = req('card_show', term, task='other-2', card_version=1)
    res['card_save_foreign_pending'] = req('card_save', term, task='other-2', card=card('other-2'), expected_version=1)
    # P3: terminal squats the task id using the other project's card in its own project.
    res['create_squat'] = req('create', term, task='other-2', project='proj', repo=str(cwd), branch='refs/heads/main', card_version=1)
    res['other_create_after_squat'] = req('create', op, task='other-2', project='other', repo=str(other), branch='refs/heads/main', card_version=1)
    # P2b: card poisoning: terminal pre-saves a card for a future id; the other project's create picks it up.
    req('card_save', term, task='future-1', card=card('future-1'), expected_version=0)
    res['other_save_after_poison'] = req('card_save', op, task='future-1', card=card('future-1'), expected_version=0).get('error')
    # P4: role_request without wait_seconds from a second terminal; connection closes; still approvable later?
    term2 = terminal('tokB')
    nowait = req('role_request', term2, role='ideation', cli='claude')
    time.sleep(1.0)
    res['nowait_request'] = nowait.get('role_request', {}).get('state')
    res['nowait_late_decide'] = req('role_request_decide', op, role_request=nowait['role_request']['id'], approved=True)
    req('role_release', term2)
    # P5: close-vs-approve race: asker closes right before the user approves.
    races = []
    for i in range(5):
        c = conn('role_request', term2, role='ideation', cli='claude', wait_seconds=60)
        t0 = time.monotonic(); pend = None
        while not pend:
            pend = [r for r in req('terminal_whoami', term2).get('role_requests') or [] if r['state']=='pending']
            assert time.monotonic()-t0 < 10
        c.close()
        d = req('role_request_decide', op, role_request=pend[0]['id'], approved=True)
        who = req('terminal_whoami', term2)
        races.append(dict(decide=d.get('ok') or d.get('error'), role=who.get('role')))
        if who.get('role'): req('role_release', term2)
        time.sleep(0.3)
    res['close_then_approve'] = races
    # P7: daemon_stop while a request waits.
    c = conn('role_request', term2, role='ideation', cli='claude', wait_seconds=600)
    time.sleep(0.5)
    t0 = time.monotonic(); stop = run_cli('daemon_stop')
    res['stop_during_wait'] = dict(stop_seconds=round(time.monotonic()-t0,2), waiter=read(c))
finally:
    try: run_cli('daemon_stop')
    except Exception as e: res['cleanup'] = str(e)[:300]
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False)[:8000])
