"""Rev03 probe: approved terminal executor in 'proj'. Checks answer_issue provenance, card_* on foreign pending
task ids, role_request without wait, close-vs-approve race, daemon_stop during a wait."""
import json, os, socket, subprocess, sys, tempfile, time, uuid, sqlite3, threading
from pathlib import Path
SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])
fx = Path(tempfile.mkdtemp(prefix='p3-', dir='/private/tmp/t121-rev04')).resolve()
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
procs = []
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
    def terminal(name, project, repo):
        launch = run_cli('shell_start','--project',project,'--cwd',str(repo))['launch']['id']
        win = req('window_open', op, launch=launch, project=project); assert win['ok'], win
        req('window_input', win['identity'], sequence=1, request_id=str(uuid.uuid4()), data=f'print -r -- $A2A_TERMINAL_TOKEN > {fx}/{name}\r')
        t0 = time.monotonic()
        while not (fx/name).exists() or not (fx/name).read_text().strip():
            assert time.monotonic()-t0 < 20; time.sleep(.1)
        return dict(kind='terminal', launch=launch, token=(fx/name).read_text().strip())
    def approve(term, role):
        c = conn('role_request', term, role=role, cli='claude', wait_seconds=60)
        t0 = time.monotonic(); pend = None
        while not pend:
            pend = [r for r in req('terminal_whoami', term).get('role_requests') or [] if r['state']=='pending']
            assert time.monotonic()-t0 < 10
        assert req('role_request_decide', op, role_request=pend[0]['id'], approved=True)['ok']
        r = read(c); assert r['ok'], r
    tp = terminal('tokP', 'proj', cwd); to = terminal('tokO', 'other', other); tq = terminal('tokQ', 'proj', cwd)
    approve(tp, 'executor'); approve(to, 'executor')
    # P1 concurrent first save of the same id from two projects' terminals.
    races = []
    for i in range(10):
        task = f'race-{i}'; cp, co = card(task), card(task)
        a = conn('card_save', tp, task=task, card=cp, expected_version=0); b = conn('card_save', to, task=task, card=co, expected_version=0)
        ra, rb = read(a), read(b)
        owners = [json.loads(r[0])['project'] for r in sqlite3.connect(rows('orchestration_events')[0]).execute(
            "SELECT data FROM orchestration_events WHERE type='card_draft_owned' AND json_extract(data,'$.task')=?", (task,))]
        winner = 'proj' if ra.get('ok') else 'other' if rb.get('ok') else None
        races.append(dict(p=ra.get('ok') or ra.get('error'), o=rb.get('ok') or rb.get('error'), owners=owners, consistent=owners==[winner]))
    res['concurrent_first_save'] = races
    # P2 operator-saved (unowned) draft: terminal cannot show/save/create; operator then creates it in 'other'.
    assert req('card_save', op, task='opd-1', card=card('opd-1'), expected_version=0)['ok']
    res['unowned_operator_draft'] = {c: req(c, tp, task='opd-1', **d).get('error') for c, d in [
        ('card_show', dict(card_version=1)), ('card_save', dict(card=card('opd-1'), expected_version=0)), ('create', dict(project='proj', repo=str(cwd), branch='refs/heads/main', card_version=1))]}
    res['unowned_operator_draft_v1'] = req('card_save', tp, task='opd-1', card=card('opd-1'), expected_version=1).get('error')
    # P3 proj-owned draft, operator creates the task in 'other' using it (non-terminal create is not checked).
    assert req('card_save', tp, task='own-x', card=card('own-x'), expected_version=0)['ok']
    res['operator_create_from_proj_draft'] = req('create', op, task='own-x', project='other', repo=str(other), branch='refs/heads/main', card_version=1).get('ok')
    res['proj_terminal_status_after'] = req('status', tp, task='own-x').get('error')
    # P3b second proj terminal (no role) -> second role holder later uses proj-owned draft: ownership by project.
    # P4 squatting: terminal claims arbitrary ids before the other project's operator.
    assert req('card_save', tp, task='future-z', card=card('future-z'), expected_version=0)['ok']
    res['operator_v0_after_squat'] = req('card_save', op, task='future-z', card=card('future-z'), expected_version=0).get('error')
    res['other_terminal_after_squat'] = req('card_save', to, task='future-z', card=card('future-z'), expected_version=1).get('error')
    # P5 approve then close immediately (approved, maybe undelivered).
    req('role_release', tp)
    p5 = []
    for i in range(15):
        c = conn('role_request', tp, role='ideation', cli='claude', wait_seconds=60)
        t0 = time.monotonic(); pend = None
        while not pend:
            pend = [r for r in req('terminal_whoami', tp).get('role_requests') or [] if r['state']=='pending']
            assert time.monotonic()-t0 < 10
        d = conn('role_request_decide', op, role_request=pend[0]['id'], approved=True)
        time.sleep(0.002 * i)
        c.close()
        dr = read(d)
        time.sleep(0.4)
        who = req('terminal_whoami', tp)
        rr = [r for r in who['role_requests'] if r['id']==pend[0]['id']][0]
        p5.append(dict(delay_ms=2*i, decide=dr.get('ok') or dr.get('error'), state=rr['state'], reason=rr['ended_reason'], role=who.get('role')))
        if who.get('role'): req('role_release', tp)
    res['approve_then_close'] = p5
    # P6 close then approve, 20 times.
    p6 = []
    for i in range(20):
        c = conn('role_request', tp, role='ideation', cli='claude', wait_seconds=60)
        t0 = time.monotonic(); pend = None
        while not pend:
            pend = [r for r in req('terminal_whoami', tp).get('role_requests') or [] if r['state']=='pending']
            assert time.monotonic()-t0 < 10
        c.close()
        d = req('role_request_decide', op, role_request=pend[0]['id'], approved=True)
        who = req('terminal_whoami', tp)
        p6.append(d.get('ok') or d.get('error'))
        if who.get('role'): req('role_release', tp)
    res['close_then_approve'] = p6
    # P7 send request and close at once (FIN with the data).
    p7 = []
    for i in range(10):
        c = conn('role_request', tp, role='ideation', cli='claude', wait_seconds=60); c.close()
        time.sleep(0.5)
        live = [r for r in req('terminal_whoami', tp).get('role_requests') or [] if r['state'] in ('pending','approved')]
        p7.append(len(live))
        for r in live: req('role_request_decide', op, role_request=r['id'], approved=False)
    res['send_and_close_live_left'] = p7
    res['daemon_alive'] = req('pane_layout').get('ok')
    ev = rows('orchestration_events')[0]
    res['errors_logged'] = [r[0] for r in sqlite3.connect(ev).execute("SELECT type FROM orchestration_events WHERE type IN ('client_connection_error','queue_stopped')")]
finally:
    try: run_cli('daemon_stop')
    except Exception as e: res['cleanup'] = str(e)[:300]
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False)[:8000])
