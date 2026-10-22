"""T-127 probe 01: how Codex's TUI treats a user home's hooks.json, -c hooks, and project trust.

Isolated CODEX_HOME under /tmp with a credential-free local fake Responses API; no model calls,
the user's ~/.codex is never read or written. Usage: python3 probe.py <codex binary> <output dir>.
Cases:
  untrusted   repo not in [projects]: does a startup dialog appear?
  layered     trusted repo; hooks.json and -c hooks both write markers: which fire?
  project     trusted repo carrying .codex/config.toml with a hook: is it loaded?
  cli-untrusted  -c projects."<repo>".trust_level="untrusted": dialog? project hook loaded?
"""
import json, os, pty, re, select, shutil, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'workbench/tests'))
from t112_native_api import message_events, request_source

codex, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=False)
root = Path(tempfile.mkdtemp(prefix='t127-probe-', dir='/private/tmp'))
requests = []


class Api(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        payload = json.dumps({'object': 'list', 'data': [{'id': 'gpt-6.1-sol', 'object': 'model', 'owned_by': 'fixture'}]}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        kind = request_source(body)
        requests.append(kind)
        reply = json.dumps({'title': 'probe'}) if kind == 'thread_title' else 'PROBE_DONE'
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
        for n, (name, payload) in enumerate(message_events(reply, body['model'])):
            self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=n, **payload)) + '\n\n').encode())
        self.wfile.flush()


server = ThreadingHTTPServer(('127.0.0.1', 0), Api)
threading.Thread(target=server.serve_forever, daemon=True).start()
ansi = re.compile(r'\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[=>()][0-9A-Za-z]?')


def marker_hook(path):
    command = f"printf '%s\\n' fired >> {path}"
    return [{'hooks': [{'type': 'command', 'command': command, 'timeout': 10}]}]


def run_case(name, trusted, project_hook, cli_trust=None):
    case = root / name; case.mkdir()
    home, repo, marks = case / 'home', case / 'repo', case / 'marks'
    home.mkdir(); marks.mkdir()
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
    (repo / 'README.md').write_text('probe\n')
    if project_hook:
        (repo / '.codex').mkdir()
        (repo / '.codex/config.toml').write_text('[hooks]\nStop = ' + toml_hooks(marks / 'project-config-stop') + '\n')
        (repo / '.codex/hooks.json').write_text(json.dumps({'hooks': {'Stop': marker_hook(marks / 'project-hooksjson-stop')}}))
    subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=p', '-c', 'user.email=p@example.invalid', 'commit', '-q', '-m', 'init'], check=True)
    config = ('model_provider = "probe"\ncli_auth_credentials_store = "file"\n[model_providers.probe]\nname = "probe"\n'
              f'base_url = "http://127.0.0.1:{server.server_port}/v1"\nwire_api = "responses"\nrequires_openai_auth = false\n')
    if trusted:
        config += f'[projects.{json.dumps(str(repo))}]\ntrust_level = "trusted"\n'
    (home / 'config.toml').write_text(config)
    (home / 'hooks.json').write_text(json.dumps({'hooks': {'Stop': marker_hook(marks / 'home-hooksjson-stop'),
                                                           'UserPromptSubmit': marker_hook(marks / 'home-hooksjson-prompt')}}))
    argv = [str(codex), '--no-daemon', '--no-alt-screen', '-C', str(repo), '-a', 'never', '--sandbox', 'workspace-write',
            '-m', 'gpt-6.1-sol', '-c', 'check_for_update_on_startup=false', '-c', 'tui.notifications=false',
            '-c', 'hooks.Stop=' + toml_hooks(marks / 'cli-stop'), '-c', 'hooks.UserPromptSubmit=' + toml_hooks(marks / 'cli-prompt'),
            '--dangerously-bypass-hook-trust']
    if cli_trust:
        argv[-1:-1] = ['-c', f'projects.{json.dumps(str(repo))}.trust_level="{cli_trust}"']
    env = {'PATH': os.environ['PATH'], 'HOME': str(case), 'CODEX_HOME': str(home), 'TERM': 'xterm-256color', 'LANG': 'en_US.UTF-8'}
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(repo); os.execve(argv[0], argv, env)
    os.set_blocking(fd, False)
    screen = b''

    def pump(seconds):
        nonlocal screen
        end = time.time() + seconds
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.2)
            if r:
                try: screen += os.read(fd, 65536)
                except OSError: return
    def send(data):
        try: os.write(fd, data)
        except OSError: pass
    pump(8)
    startup = ansi.sub('', screen.decode('utf-8', 'replace'))
    dialog = bool(re.search(r'trust|Trust', startup))
    if not dialog:
        send(b'say hi'); pump(1); send(b'\r'); pump(12)
    send(b'\x03'); pump(1); send(b'\x03'); pump(2)
    try: os.kill(pid, 9)
    except ProcessLookupError: pass
    os.waitpid(pid, 0)
    text = ansi.sub('', screen.decode('utf-8', 'replace'))
    (out / f'{name}-screen.txt').write_text(text)
    config_after = (home / 'config.toml').read_text()
    return {'case': name, 'trusted_in_home': trusted, 'cli_trust': cli_trust, 'project_hook_files': project_hook,
            'startup_dialog_text': dialog, 'startup_excerpt': startup[-1200:],
            'markers': sorted(p.name for p in marks.iterdir()), 'home_config_changed': config_after != config,
            'reply_seen': 'PROBE_DONE' in text}


def toml_hooks(path):
    command = f"printf '%s\\n' fired >> {path}"
    return '[{hooks=[{type="command",command=' + json.dumps(command) + ',timeout=10}]}]'


version = subprocess.run([str(codex), '--version'], capture_output=True, text=True).stdout.strip()
results = [run_case('untrusted', False, False), run_case('layered', True, False),
           run_case('project', True, True), run_case('cli-untrusted', False, True, 'untrusted')]
(out / 'results.json').write_text(json.dumps({'codex': str(codex), 'version': version, 'fixture': str(root),
                                              'requests': requests, 'results': results}, ensure_ascii=False, indent=2) + '\n')
for r in results:
    print(r['case'], 'dialog' if r['startup_dialog_text'] else 'no-dialog', r['markers'], 'config-changed' if r['home_config_changed'] else '', 'reply' if r['reply_seen'] else '')
