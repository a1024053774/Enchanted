"""Rev05 probe: approved terminal executor in 'proj'. Checks answer_issue provenance, card_* on foreign pending
task ids, role_request without wait, close-vs-approve race, daemon_stop during a wait."""
import json, os, socket, subprocess, sys, tempfile, time, uuid, sqlite3, threading
from pathlib import Path
SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])
fx = Path(tempfile.mkdtemp(prefix='p3-', dir='/private/tmp/t121-rev06/probe')).resolve()
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
    def pending_of(term):
        t0 = time.monotonic()
        while True:
            p = [r for r in req('terminal_whoami', term).get('role_requests') or [] if r['state']=='pending']
            if p: return p[0]
            assert time.monotonic()-t0 < 10; time.sleep(.05)
    def row(term, rid): return [r for r in req('terminal_whoami', term)['role_requests'] if r['id']==rid][0]
    def evs(rid): return [(e['type'], e['data'].get('reason'), e['data'].get('approved')) for e in req('orchestration_events')['events'] if e['type'].startswith('role_') and e['data'].get('role_request')==rid]
    def banner(): return [r['id'] for r in req('sidebar_snapshot').get('unconfirmed_role_requests') or []]
    def pend_ids(): return [r['id'] for r in req('sidebar_snapshot').get('role_requests') or []]
    def grant(term, role='executor'):
        c = conn('role_request', term, role=role, cli='claude', wait_seconds=120); p = pending_of(term)
        d = req('role_request_decide', op, role_request=p['id'], approved=True); assert d['ok'], d
        t = time.monotonic(); a = read(c); assert a['ok'], a
        return p['id'], t
    tp = terminal('tokP', 'proj', cwd); tq = terminal('tokQ', 'proj', cwd); tr = terminal('tokR', 'proj', cwd)
    tw = terminal('tokW', 'proj', cwd); ti = terminal('tokI', 'proj', cwd); to = terminal('tokO', 'other', other)
    # P1: confirm settles multiple rivals; withdrawn rival, other role, other project untouched.
    cq = conn('role_request', tq, role='executor', cli='codex', wait_seconds=120); pq = pending_of(tq)
    cr = conn('role_request', tr, role='executor', cli='codex', wait_seconds=120); pr = pending_of(tr)
    cw = conn('role_request', tw, role='executor', cli='codex', wait_seconds=120); pw = pending_of(tw); cw.close(); time.sleep(.5)
    ci = conn('role_request', ti, role='ideation', cli='codex', wait_seconds=120); pi = pending_of(ti)
    co = conn('role_request', to, role='executor', cli='codex', wait_seconds=120); po = pending_of(to)
    gid, _ = grant(tp)
    during = dict(q=row(tq, pq['id'])['state'], r=row(tr, pr['id'])['state'], approve_q=req('role_request_decide', op, role_request=pq['id'], approved=True).get('error'))
    cf = req('role_request_confirm', tp, role_request=gid)
    aq, ar = read(cq), read(cr)
    res['P1'] = dict(during=during, confirm=cf.get('ok'), q=(aq.get('error'), row(tq, pq['id'])['state']), r=(ar.get('error'), row(tr, pr['id'])['state']),
        withdrawn=evs(pw['id']), ideation_same_project=row(ti, pi['id'])['state'], other_project=row(to, po['id'])['state'], pending=len(pend_ids()))
    req('role_request_decide', op, role_request=pi['id'], approved=False); read(ci)
    req('role_request_decide', op, role_request=po['id'], approved=False); read(co)
    req('role_release', tp)
    # P2: release during grant, then timer fires.
    gid, t = grant(tp); time.sleep(5); rel = req('role_release', tp); time.sleep(max(0, 16-(time.monotonic()-t)))
    res['P2_release_then_timer'] = dict(release=rel.get('ok'), events=evs(gid), banner=gid in banner())
    # P3: confirm near the timer boundary.
    p3 = []
    for off in (14.6, 14.9, 15.0, 15.1, 15.4):
        gid, t = grant(tp)
        time.sleep(max(0, off-(time.monotonic()-t)))
        r = req('role_request_confirm', tp, role_request=gid); time.sleep(max(0, 16-(time.monotonic()-t)))
        p3.append(dict(offset=off, confirm=r.get('ok') or r.get('error'), state=row(tp, gid)['state'], events=evs(gid), role=req('terminal_whoami', tp)['role'], banner=gid in banner()))
        if req('terminal_whoami', tp)['role']: req('role_release', tp)
    res['P3_confirm_vs_timer'] = p3
    # P5: stale banner after re-request succeeds.
    old = [x for x in p3 if x['state']=='ended']
    gid2, _ = grant(tp); req('role_request_confirm', tp, role_request=gid2)
    res['P5_banner_after_reapproval'] = dict(role=req('terminal_whoami', tp)['role'], banner_count=len(banner()), old_unconfirmed=len(old),
        sidebar_controller=[a['id'] for a in req('sidebar_snapshot')['agents'] if a['id']==tp['launch']])
    req('role_release', tp)
    # P4: terminal closed during grant.
    gid, t = grant(tq); cl = req('shell_close', op, launch=tq['launch']); time.sleep(max(0, 16-(time.monotonic()-t)))
    ev = [(e['type'], e['data'].get('reason')) for e in req('orchestration_events')['events'] if e['type'].startswith('role_') and e['data'].get('role_request')==gid]
    res['P4_terminal_closed'] = dict(close=cl.get('ok'), events=ev, banner=gid in banner())
    # P6: daemon restart during grant.
    gid, t = grant(tr)
    run_cli('daemon_stop'); time.sleep(1); run_cli('daemon_start')
    t0 = time.monotonic()
    while req('pane_layout').get('recovering') is not False:
        assert time.monotonic()-t0 < 20; time.sleep(.05)
    time.sleep(max(0, 17-(time.monotonic()-t)))
    allrows = [e for e in req('orchestration_events')['events'] if e['type'].startswith('role_') and e['data'].get('role_request')==gid]
    res['P6_restart'] = dict(events=[(e['type'], e['data'].get('reason')) for e in allrows], banner=gid in banner(), pending=pend_ids())
    res['daemon_alive'] = req('pane_layout').get('ok')
finally:
    try: run_cli('daemon_stop')
    except Exception as e: res['cleanup'] = str(e)[:300]
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False)[:8000])
