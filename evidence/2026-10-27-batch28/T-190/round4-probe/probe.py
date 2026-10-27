# T-191 probe: an ordinary project terminal runs agy (or opencode); sample the sidebar row and the pane's own report
# every 0.3 s from before the prompt until after the reply.
import json, socket, sys, time, uuid, pathlib
state = pathlib.Path('/private/tmp/t190/state'); cli = sys.argv[1]; project = sys.argv[2]; cwd = sys.argv[3]
operator = json.loads(pathlib.Path(sys.argv[4]).read_text())
def request(command, identity=None, **data):
    with socket.socket(socket.AF_UNIX) as c:
        c.settimeout(60); c.connect(str(state / 'control.sock'))
        c.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)) + '\n').encode())
        r = b''
        while b'\n' not in r: r += c.recv(65536)
    return json.loads(r.split(b'\n', 1)[0])
launch = request('shell_start', operator, project=project, cwd=cwd)['launch']['id']
window = request('window_open', operator, launch=launch, project=project)
seq = [0]
def send(text):
    seq[0] += 1
    assert request('window_input', window['identity'], sequence=seq[0], request_id=str(uuid.uuid4()), data=text)['ok']
samples = []
def sample(label):
    row = next((a for a in request('sidebar_snapshot')['terminals'] if a['id'] == launch), None)
    thread = request('launch_show', operator, launch=launch)['launch']['thread']
    pane = request('pane_status', operator, thread=thread)
    samples.append(dict(t=round(time.time(), 2), label=label, row_state=row and row['state'], row_cli=row and row['cli'],
                        foreground_cli=pane.get('foreground_cli'), cli_turn=pane.get('cli_turn'), unwired=pane.get('unwired_cli')))
sample('shell')
send(cli + '\r')
for _ in range(60): sample('starting'); time.sleep(0.3)
send(sys.argv[6] if len(sys.argv) > 6 else '只回复 ok 两个字母')
time.sleep(0.5); send('\r')
for _ in range(120): sample('turn'); time.sleep(0.3)
send('\x03'); time.sleep(1); send('\x03'); time.sleep(2); sample('exited')
request('shell_close', operator, launch=launch)
out = pathlib.Path(sys.argv[5]); out.write_text(json.dumps(samples, ensure_ascii=False, indent=1))
seen = []
for s in samples:
    key = (s['label'], s['row_state'], s['foreground_cli'], (s['cli_turn'] or {}).get('state'))
    if not seen or seen[-1][0] != key: seen.append([key, 1])
    else: seen[-1][1] += 1
for key, n in seen: print(n, key)
