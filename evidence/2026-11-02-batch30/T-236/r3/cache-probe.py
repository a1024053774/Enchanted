"""T-236 r3: does a file under ~/Documents read once by an authorized process stop blocking in an Enchanted terminal?
Usage: cache-probe.py <Enchanted.app> <new fixture> <file list> <out.json>
Even-numbered files are read first by this script's own process (group P); odd-numbered are not (group Q). Then the
Enchanted project terminal runs `zsh -f` on a script that opens each file with a 3 s alarm and writes OK/FAIL per file.
The app is only started with open -n ... --state <fixture>/state; cleanup kills only processes naming the fixture or app path."""
import base64, json, os, socket, subprocess, sys, time, uuid
from pathlib import Path
ROOT = Path('/Users/luckye/Documents/Code/a2a')
app, fixture, listing, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
assert str(app).startswith('/private/tmp/a2a-build-') and str(fixture).startswith('/private/tmp/') and not fixture.exists()
files = [l for l in listing.read_text().splitlines() if l]
state, project = fixture / 'state', fixture / 'project'
project.mkdir(parents=True)
cli = ROOT / 'workbench/src/gates/cli.ts'
env = {k: os.environ[k] for k in ['PATH', 'LANG', 'TMPDIR', 'HOME'] if k in os.environ}
def request(command, identity=None, **data):
    with socket.socket(socket.AF_UNIX) as c:
        c.settimeout(15); c.connect(str(state / 'control.sock'))
        c.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)) + '\n').encode())
        b = b''
        while b'\n' not in b:
            p = c.recv(65536); assert p; b += p
    return json.loads(b.split(b'\n', 1)[0])
result = dict(app=str(app), fixture=str(fixture), started=time.strftime('%H:%M:%S'))
pre = {}
for i, f in enumerate(files):
    if i % 2 == 0:
        t = time.time(); open(f, 'rb').read(1); pre[f] = round(time.time() - t, 4)
result['pre_read'] = pre
script = fixture / 'probe.zsh'
report = fixture / 'probe.out'
script.write_text(''.join(
    f"if perl -e 'alarm 3; open(F, \"<\", $ARGV[0]) or exit 1; exit 0' '{f}'; then print -r -- 'OK {f}' >> {report}; "
    f"else print -r -- 'FAIL {f}' >> {report}; fi\n" for f in files) + f"print -r -- END >> {report}\n")
try:
    subprocess.run(['open', '-n', str(app), '--args', '--state', str(state), '--user-data', str(fixture / 'ui')], check=True)
    t = time.monotonic()
    while not (fixture / 'state-credentials/desktop-connection.json').exists() or not (state / 'control.sock').exists():
        assert time.monotonic() - t < 60, 'app did not start'; time.sleep(.5)
    daemons = [l for l in subprocess.run(['ps', '-axo', 'pid,command'], capture_output=True, text=True).stdout.splitlines() if 'daemon' in l and str(state) in l]
    assert daemons, 'daemon with the fixture state not found'
    conn = json.loads((fixture / 'state-credentials/desktop-connection.json').read_text())
    env['A2A_OPERATOR_CREDENTIAL'] = conn.get('credential') or conn.get('path')
    while request('pane_layout').get('recovering') is not False: time.sleep(.05)
    r = subprocess.run(['node', str(cli), '--state', str(state), 'shell_start', '--project', 'proj', '--cwd', str(project)], env=env, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    launch = json.loads(r.stdout)['launch']['id']
    op = json.loads(Path(env['A2A_OPERATOR_CREDENTIAL']).read_text())
    opened = request('window_open', op, launch=launch, project='proj'); assert opened['ok'], opened
    time.sleep(5)
    r = request('window_input', opened['identity'], sequence=1, request_id=str(uuid.uuid4()), data=f'zsh -f {script}\r'); assert r['ok'], r
    t = time.monotonic()
    while time.monotonic() - t < 4 * len(files) + 20:
        if report.exists() and report.read_text().endswith('END\n'): break
        time.sleep(1)
    lines = report.read_text().splitlines() if report.exists() else []
    status = {l.split(' ', 1)[1]: l.split(' ', 1)[0] for l in lines if ' ' in l}
    result['rows'] = [dict(file=f, group='P' if i % 2 == 0 else 'Q', result=status.get(f, 'missing')) for i, f in enumerate(files)]
    for g in 'PQ':
        rows = [x for x in result['rows'] if x['group'] == g]
        result[f'group_{g}'] = dict(total=len(rows), fail=sum(x['result'] == 'FAIL' for x in rows), missing=sum(x['result'] == 'missing' for x in rows))
finally:
    subprocess.run(['pkill', '-f', str(fixture)]); subprocess.run(['pkill', '-f', f'{app}/Contents/Resources/app/hc/herdr-core'])
    time.sleep(2)
    result['left'] = subprocess.run(['pgrep', '-fl', f'{fixture}|{app}'], capture_output=True, text=True).stdout
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps({k: result.get(k) for k in ('group_P', 'group_Q', 'left')}, ensure_ascii=False))
