import base64, json, os, re, socket, subprocess, sys, tempfile, time, uuid
from pathlib import Path
ROOT = Path('/Users/luckye/Documents/Code/a2a')
cli = ROOT / 'workbench/src/gates/cli.ts'  # usage: t236open5.py - <pkg dir> <fixture>
resize = os.environ.get('RESIZE')
PKG = sys.argv[2]; fixture = Path(sys.argv[3]); state = fixture/'state'; cwd = fixture/'project'; cwd.mkdir(parents=True)
env = {k: os.environ[k] for k in ['PATH', 'LANG', 'TMPDIR', 'HOME'] if k in os.environ}
def run_cli(*a):
    r = subprocess.run(['node', str(cli), '--state', str(state), *a], env=env, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr or r.stdout
    return json.loads(r.stdout)
def request(command, identity=None, **data):
    with socket.socket(socket.AF_UNIX) as c:
        c.settimeout(15); c.connect(str(state / 'control.sock'))
        c.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)) + '\n').encode())
        b = b''
        while b'\n' not in b:
            p = c.recv(65536); assert p; b += p
    return json.loads(b.split(b'\n', 1)[0])
def raw(launch):
    r = request('pane_output', launch=launch, offset=0); assert r['ok'], r
    return base64.b64decode(r['data_base64'])
seq = [0]
def send(ident, data):
    seq[0] += 1
    r = request('window_input', ident, sequence=seq[0], request_id=str(uuid.uuid4()), data=data); assert r['ok'], r
try:
    subprocess.run(['open','-n',PKG + '/Enchanted.app','--args','--state',str(state),'--user-data',str(fixture/'ui')],check=True)
    t=time.monotonic()
    while not (fixture/'state-credentials/desktop-connection.json').exists() or not (state/'control.sock').exists():
        assert time.monotonic()-t<60; time.sleep(.5)
    print('ps', subprocess.run(['pgrep','-fl',str(fixture)],capture_output=True,text=True).stdout[:300])
    conn=json.loads((fixture/'state-credentials/desktop-connection.json').read_text())
    print('conn keys', list(conn))
    credpath = conn.get('credential') or conn.get('path')
    env['A2A_OPERATOR_CREDENTIAL'] = credpath
    while request('pane_layout').get('recovering') is not False: time.sleep(.05)
    launch = run_cli('shell_start', '--project', 'proj', '--cwd', str(cwd))['launch']['id']
    op = json.loads(Path(env['A2A_OPERATOR_CREDENTIAL']).read_text())
    opened = request('window_open', op, launch=launch, project='proj'); assert opened['ok'], opened
    ident = opened['identity']
    if resize:
        c, r = map(int, resize.split('x'))
        print('resize', request('window_resize', ident, sequence=1, request_id=str(uuid.uuid4()), cols=c, rows=r))
    time.sleep(3)
    send(ident, 'stty size; print T236-SIZE-END\r')
    time.sleep(2)
    before = len(raw(launch))
    send(ident, f'CLAUDE_CODE_NO_FLICKER=1 claude --model claude-haiku-5-5 --debug-file {fixture}/claude-debug.log\r')
    t0 = time.monotonic(); first = None
    while time.monotonic() - t0 < 25:
        out = raw(launch)[before:]
        if b'\x1b[?1049h' in out and first is None: first = ('altscreen', round(time.monotonic() - t0, 1))
        if b'Claude Code' in out or b'Haiku' in out:
            first = first or ('?',); print('frame at', round(time.monotonic() - t0, 1)); break
        time.sleep(.2)
    if not first or first[0] != 'altscreen' or b'Claude Code' not in raw(launch)[before:]:
        pids = subprocess.run(['pgrep','-f','--plugin-dir ' + PKG],capture_output=True,text=True).stdout.split()
        print('NO FRAME; claude pids', pids)
        tree = subprocess.run(['ps','-axo','pid,ppid,stat,etime,command'],capture_output=True,text=True).stdout.splitlines()
        rows = {int(l.split()[0]): l for l in tree[1:]}
        par = {int(l.split()[0]): int(l.split()[1]) for l in tree[1:]}
        core = [p for p,l in rows.items() if PKG + '/Enchanted.app/Contents/Resources/app/hc/herdr-core serve' in l]
        def under(p):
            while p > 1:
                if p in core: return True
                p = par.get(p, 1)
            return False
        print('TREE'); [print('  ', rows[p][:260]) for p in sorted(rows) if under(p)]
        for p in [p for p in rows if under(p) and p not in core]:
            smp = subprocess.run(['sample',str(p),'1'],capture_output=True,text=True).stdout
            print('SAMPLE', p, [l.strip()[:120] for l in smp.splitlines() if 'libsystem_kernel' in l][:4])
        for pid in pids:
            print(subprocess.run(['ps','-o','pid,ppid,stat,wchan,command','-p',pid],capture_output=True,text=True).stdout[:300])
            print('LSOF-DOCS', [l for l in subprocess.run(['lsof','-p',pid],capture_output=True,text=True).stdout.splitlines() if 'Documents' in l][:10])
            smp = subprocess.run(['sample',pid,'2'],capture_output=True,text=True).stdout
            print('SAMPLE', '\n'.join([l for l in smp.splitlines() if any(k in l for k in ('open','stat','access','realpath','readlink','getattrlist','__'))][:25]))
    time.sleep(12)  # keep it alive past the 10 s health window
    out = raw(launch)
    txt = re.sub(rb'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))', b'', out).decode('utf-8', 'replace')
    print('SIZE', re.findall(r'^(\d+ \d+)\r?$', txt, re.M), 'first', first)
    print('tail bytes after claude:', repr(out[before:][:1500]))
    send(ident, '\x03\x03')
    time.sleep(1)
    log = fixture/'claude-debug.log'
    print('DEBUG-LOG', log.read_text()[-6000:] if log.exists() else 'missing')
    time.sleep(2)
finally:
    subprocess.run(['pkill','-f',str(fixture)]); subprocess.run(['pkill','-f',PKG + '/Enchanted.app/Contents/Resources/app/hc/herdr-core'])
    print('fixture', fixture)
