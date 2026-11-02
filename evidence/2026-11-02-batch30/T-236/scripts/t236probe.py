import base64, json, os, re, socket, subprocess, sys, tempfile, time, uuid
from pathlib import Path
ROOT = Path('/Users/luckye/Documents/Code/a2a')
cli = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'workbench/src/gates/cli.ts'
resize = os.environ.get('RESIZE')
fixture = Path(tempfile.mkdtemp(prefix='t236-', dir='/private/tmp')).resolve()
state, cwd = fixture / 'state', Path('/private/tmp/a2a-cu/project')
state.mkdir()
env = {k: os.environ[k] for k in ['PATH', 'LANG', 'TMPDIR', 'HOME'] if k in os.environ}
env.update(SHELL='/bin/zsh', TERM='xterm-256color', A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'))
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
    r = subprocess.run(['node', '/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/3f5514a4-d0d1-44ce-8f38-5ed7424cdfa6/scratchpad/startd.mts', str(state)], env=env, capture_output=True, text=True, timeout=90)
    print('daemon', r.stdout.strip()[:200], r.stderr[-300:])
    cred = json.loads(r.stdout.strip().splitlines()[-1])['credential']
    while request('pane_layout').get('recovering') is not False: time.sleep(.05)
    launch = run_cli('shell_start', '--project', 'proj', '--cwd', str(cwd))['launch']['id']
    op = json.loads((fixture / 'operator.json').read_text())
    opened = request('window_open', op, launch=launch, project='proj'); assert opened['ok'], opened
    ident = opened['identity']
    if resize:
        c, r = map(int, resize.split('x'))
        print('resize', request('window_resize', ident, sequence=1, request_id=str(uuid.uuid4()), cols=c, rows=r))
    time.sleep(3)
    send(ident, 'stty size; print T236-SIZE-END\r')
    time.sleep(2)
    before = len(raw(launch))
    send(ident, 'CLAUDE_CODE_NO_FLICKER=1 claude --model claude-haiku-5-5\r')
    t0 = time.monotonic(); first = None
    while time.monotonic() - t0 < 25:
        out = raw(launch)[before:]
        if b'\x1b[?1049h' in out and first is None: first = ('altscreen', round(time.monotonic() - t0, 1))
        if b'Claude Code' in out or b'Haiku' in out:
            first = first or ('?',); print('frame at', round(time.monotonic() - t0, 1)); break
        time.sleep(.2)
    time.sleep(12)  # keep it alive past the 10 s health window
    out = raw(launch)
    txt = re.sub(rb'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))', b'', out).decode('utf-8', 'replace')
    print('SIZE', re.findall(r'^(\d+ \d+)\r?$', txt, re.M), 'first', first)
    print('tail bytes after claude:', repr(out[before:][:1500]))
    send(ident, '\x03\x03')
    time.sleep(2)
finally:
    try: run_cli('daemon_stop')
    except Exception as e: print('stop', e)
    print('fixture', fixture)
