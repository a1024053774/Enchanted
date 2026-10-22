"""T-127 probe 03: do the home's rules (git add / git commit allow prefix rules) still apply after
a session opens an untrusted folder in restricted mode? Isolated tmp CODEX_HOME, local fake API
that returns shell tool calls, no model calls. Needs pyte. Usage: python probe3.py <codex> <out>.

Cases: rules / no-rules. The session starts in a linked worktree with
-c projects={"<repo>"={trust_level="untrusted"}}, "Open restricted" is answered, one prompt is
typed, and the fake API asks for: echo x > new.txt; git add new.txt; git commit -m probe.
"""
import json, os, pty, re, select, subprocess, sys, tempfile, threading, time, fcntl, struct, termios
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import pyte

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'workbench/tests'))
from t112_native_api import message_events, request_source, request_tools, shell_item, tool_events

codex, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=False)
root = Path(tempfile.mkdtemp(prefix='t127-probe3-', dir='/private/tmp'))
state = {'cwd': None, 'step': 0, 'outputs': []}
STEPS = ["printf 'x\\n' > new.txt", 'git add new.txt', 'git commit -m probe']


class Api(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        payload = json.dumps({'object': 'list', 'data': [{'id': 'gpt-6.1-sol', 'object': 'model', 'owned_by': 'fixture'}]}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if request_source(body) == 'thread_title':
            events = message_events(json.dumps({'title': 'probe'}), body['model'])
        else:
            for item in body['input']:
                if item.get('type') in ('custom_tool_call_output', 'function_call_output'):
                    state['outputs'].append(item.get('output'))
            if state['step'] < len(STEPS):
                events = tool_events(shell_item(request_tools(body), STEPS[state['step']], state['cwd']), body['model'])
                state['step'] += 1
            else:
                events = message_events('PROBE_DONE', body['model'])
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
        for n, (name, payload) in enumerate(events):
            self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=n, **payload)) + '\n\n').encode())
        self.wfile.flush()


server = ThreadingHTTPServer(('127.0.0.1', 0), Api)
threading.Thread(target=server.serve_forever, daemon=True).start()


def git(*args, check=True):
    return subprocess.run(['git', *args], check=check, capture_output=True, text=True)


def run_case(name, rules):
    state.update(step=0, outputs=[])
    case = root / name; case.mkdir()
    home, repo, cwd = case / 'home', case / 'repo', case / 'worktree'
    home.mkdir()
    git('init', '-q', '-b', 'main', str(repo))
    (repo / 'README.md').write_text('probe\n')
    git('-C', str(repo), 'add', '-A')
    git('-C', str(repo), '-c', 'user.name=p', '-c', 'user.email=p@example.invalid', 'commit', '-q', '-m', 'init')
    git('-C', str(repo), 'worktree', 'add', '-q', '-b', 'a', str(cwd))
    state['cwd'] = str(cwd)
    (home / 'config.toml').write_text('model_provider = "probe"\ncli_auth_credentials_store = "file"\n[model_providers.probe]\nname = "probe"\n'
        f'base_url = "http://127.0.0.1:{server.server_port}/v1"\nwire_api = "responses"\nrequires_openai_auth = false\n')
    if rules:
        (home / 'rules').mkdir()
        (home / 'rules/default.rules').write_text('prefix_rule(pattern=["git", "add"], decision="allow")\n'
                                                  'prefix_rule(pattern=["git", "commit"], decision="allow")\n')
    argv = [str(codex), '--no-daemon', '--no-alt-screen', '-C', str(cwd), '-a', 'never', '--sandbox', 'workspace-write',
            '-m', 'gpt-6.1-sol', '-c', 'check_for_update_on_startup=false', '-c', 'tui.notifications=false',
            '-c', 'sandbox_workspace_write.network_access=false',
            '-c', f'projects={{{json.dumps(str(repo))}={{trust_level="untrusted"}}}}']
    env = {'PATH': os.environ['PATH'], 'HOME': str(case), 'CODEX_HOME': str(home), 'TERM': 'xterm-256color', 'LANG': 'en_US.UTF-8',
           'GIT_AUTHOR_NAME': 'p', 'GIT_AUTHOR_EMAIL': 'p@example.invalid', 'GIT_COMMITTER_NAME': 'p', 'GIT_COMMITTER_EMAIL': 'p@example.invalid'}
    screen = pyte.Screen(160, 45); stream = pyte.ByteStream(screen)
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(cwd); os.execve(argv[0], argv, env)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', 45, 160, 0, 0))
    os.set_blocking(fd, False)

    def pump(seconds):
        end = time.time() + seconds
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.2)
            if r:
                try: stream.feed(os.read(fd, 65536))
                except OSError: return

    def send(data):
        try: os.write(fd, data)
        except OSError: pass
    text = lambda: '\n'.join(line.rstrip() for line in screen.display).strip()
    pump(8)
    startup = text()
    restricted = '› 1. Open restricted' in startup
    if restricted:
        send(b'\r'); pump(4)
    send(b'run the steps'); pump(1); send(b'\r'); pump(25)
    final = text()
    send(b'\x03'); pump(1); send(b'\x03'); pump(2)
    try: os.kill(pid, 9)
    except ProcessLookupError: pass
    os.waitpid(pid, 0)
    (out / f'{name}-final.txt').write_text(final + '\n')
    log = git('-C', str(cwd), 'log', '--format=%s', '-3').stdout.split()
    return {'case': name, 'home_rules': rules, 'restricted_answered': restricted, 'steps_sent': state['step'],
            'branch_log': log, 'committed': 'probe' in log, 'tool_outputs': [str(o)[:300] for o in state['outputs']]}


version = subprocess.run([str(codex), '--version'], capture_output=True, text=True).stdout.strip()
results = [run_case('rules', True), run_case('no-rules', False)]
(out / 'results.json').write_text(json.dumps({'codex': str(codex), 'version': version, 'fixture': str(root), 'results': results},
                                             ensure_ascii=False, indent=2) + '\n')
for r in results:
    print(json.dumps({k: r[k] for k in ('case', 'restricted_answered', 'steps_sent', 'branch_log', 'committed')}))
