"""Rev05 probe: approved terminal executor in 'proj'. Checks answer_issue provenance, card_* on foreign pending
task ids, role_request without wait, close-vs-approve race, daemon_stop during a wait."""
import json, os, socket, subprocess, sys, tempfile, time, uuid, sqlite3, threading
from pathlib import Path
SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])
fx = Path(tempfile.mkdtemp(prefix='p3-', dir='/private/tmp/t121-rev05/probe')).resolve()
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

    tp = terminal('tokP', 'proj', cwd); tq = terminal('tokQ', 'proj', cwd); tr = terminal('tokR', 'proj', cwd); to = terminal('tokO', 'other', other)
    def pending_of(term):
        t0 = time.monotonic()
        while True:
            p = [r for r in req('terminal_whoami', term).get('role_requests') or [] if r['state']=='pending']
            if p: return p[0]
            assert time.monotonic()-t0 < 10; time.sleep(.05)
    def row(term, rid): return [r for r in req('terminal_whoami', term)['role_requests'] if r['id']==rid][0]
    # S1: asker reads the grant and dies before confirming; another process in the same terminal confirms via whoami.
    c = conn('role_request', tp, role='executor', cli='claude', wait_seconds=60); p = pending_of(tp)
    assert req('role_request_decide', op, role_request=p['id'], approved=True)['ok']
    ans = read(c)
    gid = [r['id'] for r in req('terminal_whoami', tp)['role_requests'] if r['state']=='granted']
    conf = req('role_request_confirm', tp, role_request=gid[0]) if gid else None
    res['S1_other_process_confirm'] = dict(answer=ans.get('role_request',{}).get('state'), whoami_shows_granted_id=bool(gid), confirm=conf and conf.get('ok'), role=req('terminal_whoami', tp)['role'])
    req('role_release', tp)
    # S2: confirm sent, connection closed before reading the reply.
    c = conn('role_request', tp, role='executor', cli='claude', wait_seconds=60); p = pending_of(tp)
    assert req('role_request_decide', op, role_request=p['id'], approved=True)['ok']; read(c)
    k = conn('role_request_confirm', tp, role_request=p['id']); k.close(); time.sleep(.5)
    res['S2_confirm_reply_lost'] = dict(state=row(tp, p['id'])['state'], role=req('terminal_whoami', tp)['role'])
    req('role_release', tp)
    # S3: grant tp, tp never confirms; rival tq auto-rejected; after expiry role vacant.
    cp = conn('role_request', tp, role='executor', cli='claude', wait_seconds=60); pp = pending_of(tp)
    cq = conn('role_request', tq, role='executor', cli='codex', wait_seconds=60); pq = pending_of(tq)
    cr = conn('role_request', tr, role='ideation', cli='codex', wait_seconds=60); pr = pending_of(tr)
    co = conn('role_request', to, role='executor', cli='codex', wait_seconds=60); po = pending_of(to)
    assert req('role_request_decide', op, role_request=pp['id'], approved=True)['ok']
    ap, aq = read(cp), read(cq)
    s3 = dict(winner=ap.get('role_request',{}).get('state'), rival_answer=aq.get('error'), rival_row=row(tq, pq['id'])['state'],
              other_role_same_project=row(tr, pr['id'])['state'], same_role_other_project=row(to, po['id'])['state'])
    s3['rival_requests_again_during_grant'] = req('role_request', tq, role='executor', wait_seconds=1).get('error')
    time.sleep(16)
    s3['winner_after_16s'] = (row(tp, pp['id'])['state'], row(tp, pp['id'])['ended_reason'])
    s3['role_holders'] = [req('terminal_whoami', t)['role'] for t in (tp, tq)]
    ev = rows('orchestration_events')[0]
    s3['not_confirmed_event_recorded'] = sqlite3.connect(ev).execute("SELECT count(*) FROM orchestration_events WHERE data LIKE '%not_confirmed%'").fetchone()[0]
    s3['sidebar_pending_after'] = [(r['project'], r['role']) for r in req('sidebar_snapshot').get('role_requests') or []]
    res['S3_unconfirmed_grant_rivals'] = s3
    # settle remaining
    for t, pid, cc in ((tr, pr['id'], cr), (to, po['id'], co)):
        req('role_request_decide', op, role_request=pid, approved=False); read(cc)
    # S4: concurrent approve A + approve B for same role; and approve A + reject B.
    s4 = []
    for mode in ('approve_both', 'approve_reject', 'reject_approve'):
        ca = conn('role_request', tp, role='executor', cli='claude', wait_seconds=60); pa = pending_of(tp)
        cb = conn('role_request', tq, role='executor', cli='claude', wait_seconds=60); pb = pending_of(tq)
        da = conn('role_request_decide', op, role_request=pa['id'], approved=mode != 'reject_approve')
        db = conn('role_request_decide', op, role_request=pb['id'], approved=mode != 'approve_reject')
        ra, rb = read(da), read(db)
        xa, xb = read(ca), read(cb)
        s4.append(dict(mode=mode, decide_a=ra.get('ok') or ra.get('error'), decide_b=rb.get('ok') or rb.get('error'),
                       ask_a=xa.get('ok') or xa.get('error'), ask_b=xb.get('ok') or xb.get('error'),
                       reason_b=row(tq, pb['id'])['ended_reason']))
        for t, rid, x in ((tp, pa['id'], xa), (tq, pb['id'], xb)):
            if x.get('ok'): req('role_request_confirm', t, role_request=rid); req('role_release', t)
    res['S4_concurrent_decisions'] = s4
    # S5: release racing confirm.
    s5 = []
    for i in range(5):
        c = conn('role_request', tp, role='executor', cli='claude', wait_seconds=60); p = pending_of(tp)
        assert req('role_request_decide', op, role_request=p['id'], approved=True)['ok']; read(c)
        a = conn('role_release', tp); b = conn('role_request_confirm', tp, role_request=p['id'])
        ra, rb = read(a), read(b)
        s5.append(dict(release=ra.get('ok') or ra.get('error'), confirm=rb.get('ok') or rb.get('error'), state=row(tp, p['id'])['state'], role=req('terminal_whoami', tp)['role']))
        if req('terminal_whoami', tp)['role']: req('role_release', tp)
    res['S5_release_vs_confirm'] = s5
    res['daemon_alive'] = req('pane_layout').get('ok')
finally:
    try: run_cli('daemon_stop')
    except Exception as e: res['cleanup'] = str(e)[:300]
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False)[:8000])
