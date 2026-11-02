"""T-236 / T-238 探针：打包应用的项目终端里，读 ~/Documents 下的文件会不会卡住，对照读 /private/tmp 下的文件。
用法：python3 t236tcc.py <Enchanted.app 路径> <一次性夹具目录>
应用只以 open -n ... --state <夹具>/state --user-data <夹具>/ui 启动；结束时只结束命令行含该夹具或该包路径的进程。
"""
import base64, json, os, re, socket, subprocess, sys, time, uuid
from pathlib import Path

ROOT = Path('/Users/luckye/Documents/Code/a2a')
app, fixture = Path(sys.argv[1]), Path(sys.argv[2])
assert str(app).startswith('/private/tmp/a2a-build-') and str(fixture).startswith('/private/tmp/') and not fixture.exists()
state, project = fixture / 'state', fixture / 'project'
project.mkdir(parents=True)
(fixture / 'probe.txt').write_text('tmp\n')
DOCS = ROOT / 'AGENTS.md'  # any file under ~/Documents; only read, output discarded
cli = ROOT / 'workbench/src/gates/cli.ts'
env = {k: os.environ[k] for k in ['PATH', 'LANG', 'TMPDIR', 'HOME'] if k in os.environ}
# The app is started by `open`, so its terminals run the user's own zsh and HOME whatever this script's environment is.


def request(command, identity=None, **data):
    with socket.socket(socket.AF_UNIX) as c:
        c.settimeout(15); c.connect(str(state / 'control.sock'))
        c.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)) + '\n').encode())
        b = b''
        while b'\n' not in b:
            p = c.recv(65536); assert p; b += p
    return json.loads(b.split(b'\n', 1)[0])


def text(launch):
    r = request('pane_output', launch=launch, offset=0); assert r['ok'], r
    return re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))', '', base64.b64decode(r['data_base64']).decode('utf-8', 'replace'))


seq = [0]
def send(ident, data):
    seq[0] += 1
    r = request('window_input', ident, sequence=seq[0], request_id=str(uuid.uuid4()), data=data); assert r['ok'], r


def until(launch, marker, limit):
    t0 = time.monotonic()
    while time.monotonic() - t0 < limit:
        # The command echo carries the marker split by '' and the user's prompt pads lines, so match it anywhere.
        if marker in text(launch): return round(time.monotonic() - t0, 2)
        time.sleep(.1)
    return None


result = dict(app=str(app), fixture=str(fixture), docs_file=str(DOCS))
try:
    subprocess.run(['open', '-n', str(app), '--args', '--state', str(state), '--user-data', str(fixture / 'ui')], check=True)
    t = time.monotonic()
    while not (fixture / 'state-credentials/desktop-connection.json').exists() or not (state / 'control.sock').exists():
        assert time.monotonic() - t < 60, 'app did not start'; time.sleep(.5)
    daemons = [l for l in subprocess.run(['ps', '-axo', 'pid,command'], capture_output=True, text=True).stdout.splitlines() if 'daemon' in l and str(state) in l]
    assert daemons, 'daemon with the fixture state not found'
    result['daemon'] = daemons[0][:200]
    conn = json.loads((fixture / 'state-credentials/desktop-connection.json').read_text())
    env['A2A_OPERATOR_CREDENTIAL'] = conn.get('credential') or conn.get('path')
    while request('pane_layout').get('recovering') is not False: time.sleep(.05)
    r = subprocess.run(['node', str(cli), '--state', str(state), 'shell_start', '--project', 'proj', '--cwd', str(project)], env=env, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    launch = json.loads(r.stdout)['launch']['id']
    op = json.loads(Path(env['A2A_OPERATOR_CREDENTIAL']).read_text())
    opened = request('window_open', op, launch=launch, project='proj'); assert opened['ok'], opened
    ident = opened['identity']
    time.sleep(5)  # the user's zsh startup
    send(ident, f"cat {fixture / 'probe.txt'} >/dev/null && print TMP-''OK\r")
    result['tmp_read_s'] = until(launch, 'TMP-OK', 10)
    send(ident, f"cat {DOCS} >/dev/null && print DOCS-''OK\r")
    result['docs_read_s'] = until(launch, 'DOCS-OK', 20)
    if os.environ.get('PARALLEL'):
        # Each file read in its own background job; whichever never prints its OK line is blocked.
        files = [str(Path(f).expanduser()) for f in os.environ['PARALLEL'].split(':')]
        send(ident, ' '.join(f"(cat '{f}' >/dev/null 2>&1 && print -r -- 'PAR-OK {i}') &!" for i, f in enumerate(files)) + '\r')
        time.sleep(5)
        screen = text(launch)
        result['parallel'] = {f: f'PAR-OK {i}' in screen for i, f in enumerate(files)}
    if os.environ.get('SKILLS'):
        # Every SKILL.md Claude's skill loader can reach under ~/.claude/skills, one cat at a time, to find one that blocks.
        skills = Path.home() / '.claude/skills'
        targets = [str((skills / name).resolve() / 'SKILL.md') for name in sorted(os.listdir(skills)) if not name.startswith('.')]
        send(ident, ' '.join(f"print -r -- 'SKL-START {path}'; cat '{path}' >/dev/null 2>&1; print -r -- 'SKL-DONE {path}';" for path in targets) + " print SKILLS-''END\r")
        result['skills_s'] = until(launch, 'SKILLS-END', 30)
        lines = [l.strip() for l in text(launch).splitlines() if 'SKL-' in l and 'print -r' not in l]
        result['skills_last'] = lines[-3:]
        result['skills_count'] = sum('SKL-DONE' in l for l in lines)
        if result['skills_s'] is None:
            blocked = []
            for pid in subprocess.run(['pgrep', '-f', 'cat /Users/'], capture_output=True, text=True).stdout.split():
                ps = subprocess.run(['ps', '-o', 'pid,ppid,stat,etime,command', '-p', pid], capture_output=True, text=True).stdout
                smp = subprocess.run(['sample', pid, '1'], capture_output=True, text=True).stdout
                lsof = subprocess.run(['lsof', '-p', pid], capture_output=True, text=True).stdout
                blocked.append(dict(ps=ps, stack=[l.strip()[:160] for l in smp.splitlines() if '(in ' in l][:12], lsof=lsof.splitlines()[-6:]))
            result['blocked'] = blocked
            send(ident, '\x03')
    if result['docs_read_s'] is None:
        cats = subprocess.run(['pgrep', '-f', f'cat {DOCS}'], capture_output=True, text=True).stdout.split()
        result['blocked_cat'] = []
        for pid in cats:
            ps = subprocess.run(['ps', '-o', 'pid,ppid,stat,etime,command', '-p', pid], capture_output=True, text=True).stdout
            smp = subprocess.run(['sample', pid, '1'], capture_output=True, text=True).stdout
            result['blocked_cat'].append(dict(ps=ps, kernel=[l.strip()[:140] for l in smp.splitlines() if 'libsystem_kernel' in l][:4]))
        send(ident, '\x03')
    result['screen_tail'] = text(launch)[-600:]
finally:
    subprocess.run(['pkill', '-f', str(fixture)]); subprocess.run(['pkill', '-f', f'{app}/Contents/Resources/app/hc/herdr-core'])
    time.sleep(2)
    result['left'] = subprocess.run(['pgrep', '-fl', f'{fixture}|{app}'], capture_output=True, text=True).stdout
    print(json.dumps(result, ensure_ascii=False, indent=1))
