"""T-127 probe 02: rendered start-up screens for the trust question, and what a per-session
trust override does. Same isolation as probe.py (tmp CODEX_HOME, local fake API, no model
calls). Needs pyte. Usage: python probe2.py <codex binary> <output dir>.

Cases (each starts the TUI with the product's Codex argv plus marker hooks):
  worktree-untrusted       linked worktree of a repo the home does not trust
  worktree-cli-trusted     same, with -c projects."<repo>".trust_level="trusted"
  copy-untrusted           non-Git copy with project .codex hooks (the review candidate copy)
  copy-cli-untrusted       same, with -c projects."<copy>".trust_level="untrusted"
Nothing is pressed while a trust question is on screen; a prompt is typed only when the
start-up screen shows no trust question.
"""
import json, os, pty, re, select, shutil, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import pyte

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'workbench/tests'))
from t112_native_api import message_events, request_source

codex, out = Path(sys.argv[1]), Path(sys.argv[2])
INLINE = len(sys.argv) > 3 and sys.argv[3] == 'inline'
ONLY = sys.argv[4].split(',') if len(sys.argv) > 4 else None
RESTRICTED = len(sys.argv) > 5 and sys.argv[5] == 'restricted'
out.mkdir(parents=True, exist_ok=False)
root = Path(tempfile.mkdtemp(prefix='t127-probe2-', dir='/private/tmp'))


class Api(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        payload = json.dumps({'object': 'list', 'data': [{'id': 'gpt-6.1-sol', 'object': 'model', 'owned_by': 'fixture'}]}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        reply = json.dumps({'title': 'probe'}) if request_source(body) == 'thread_title' else 'PROBE_DONE'
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
        for n, (name, payload) in enumerate(message_events(reply, body['model'])):
            self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=n, **payload)) + '\n\n').encode())
        self.wfile.flush()


server = ThreadingHTTPServer(('127.0.0.1', 0), Api)
threading.Thread(target=server.serve_forever, daemon=True).start()


def toml_hooks(path):
    command = f"printf '%s\\n' fired >> {path}"
    return '[{hooks=[{type="command",command=' + json.dumps(command) + ',timeout=10}]}]'


def json_hooks(path):
    return [{'hooks': [{'type': 'command', 'command': f"printf '%s\\n' fired >> {path}", 'timeout': 10}]}]


def git(*args):
    subprocess.run(['git', *args], check=True, capture_output=True)


def run_case(name, kind, cli_trust):
    case = root / name; case.mkdir()
    home, repo, marks = case / 'home', case / 'repo', case / 'marks'
    home.mkdir(); marks.mkdir()
    git('init', '-q', '-b', 'main', str(repo))
    (repo / 'README.md').write_text('probe\n')
    (repo / '.codex').mkdir()
    (repo / '.codex/config.toml').write_text('[hooks]\nStop = ' + toml_hooks(marks / 'project-config-stop') + '\n')
    (repo / '.codex/hooks.json').write_text(json.dumps({'hooks': {'Stop': json_hooks(marks / 'project-hooksjson-stop')}}))
    git('-C', str(repo), 'add', '-A')
    git('-C', str(repo), '-c', 'user.name=p', '-c', 'user.email=p@example.invalid', 'commit', '-q', '-m', 'init')
    if kind == 'worktree':
        cwd = case / 'worktree'; git('-C', str(repo), 'worktree', 'add', '-q', '-b', 'a', str(cwd))
        trust_path = repo
    else:
        cwd = case / 'copy'
        shutil.copytree(repo, cwd, ignore=shutil.ignore_patterns('.git'))
        trust_path = cwd
    config = ('model_provider = "probe"\ncli_auth_credentials_store = "file"\n[model_providers.probe]\nname = "probe"\n'
              f'base_url = "http://127.0.0.1:{server.server_port}/v1"\nwire_api = "responses"\nrequires_openai_auth = false\n')
    (home / 'config.toml').write_text(config)
    (home / 'hooks.json').write_text(json.dumps({'hooks': {'Stop': json_hooks(marks / 'home-hooksjson-stop')}}))
    argv = [str(codex), '--no-daemon', '--no-alt-screen', '-C', str(cwd), '-a', 'never', '--sandbox', 'workspace-write',
            '-m', 'gpt-6.1-sol', '-c', 'check_for_update_on_startup=false', '-c', 'tui.notifications=false',
            '-c', 'hooks.Stop=' + toml_hooks(marks / 'cli-stop')]
    if cli_trust:
        argv += ['-c', f'projects={{{json.dumps(str(trust_path))}={{trust_level="{cli_trust}"}}}}'] if INLINE else             ['-c', f'projects.{json.dumps(str(trust_path))}.trust_level="{cli_trust}"']
    argv.append('--dangerously-bypass-hook-trust')
    env = {'PATH': os.environ['PATH'], 'HOME': str(case), 'CODEX_HOME': str(home), 'TERM': 'xterm-256color', 'LANG': 'en_US.UTF-8'}
    screen, stream = pyte.Screen(160, 45), None
    stream = pyte.ByteStream(screen)
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(cwd); os.execve(argv[0], argv, env)
    import fcntl, struct, termios
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

    def text():
        return '\n'.join(line.rstrip() for line in screen.display).strip()
    pump(8)
    startup = text()
    trust_question = bool(re.search(r'trust', startup, re.I))
    restricted = '› 1. Open restricted' in startup
    if restricted and RESTRICTED:
        # "Open restricted" saves nothing ("Opening will not change saved trust").
        send(b'\r'); pump(4)
    if not trust_question or (restricted and RESTRICTED):
        send(b'say hi'); pump(1); send(b'\r'); pump(12)
    final = text()
    send(b'\x03'); pump(1); send(b'\x03'); pump(2)
    try: os.kill(pid, 9)
    except ProcessLookupError: pass
    os.waitpid(pid, 0)
    (out / f'{name}-startup.txt').write_text(startup + '\n')
    (out / f'{name}-final.txt').write_text(final + '\n')
    after = (home / 'config.toml').read_text()
    return {'restricted_answered': restricted and RESTRICTED, 'case': name, 'cwd_kind': kind, 'cli_trust': cli_trust, 'trust_question_on_screen': trust_question,
            'markers': sorted(p.name for p in marks.iterdir()), 'reply_seen': 'PROBE_DONE' in final,
            'projects_written_to_home': re.findall(r'\[projects\.[^\]]+\]\s*\ntrust_level = "\w+"', after)}


version = subprocess.run([str(codex), '--version'], capture_output=True, text=True).stdout.strip()
cases = [('worktree-untrusted', 'worktree', None), ('worktree-cli-trusted', 'worktree', 'trusted'),
         ('copy-untrusted', 'copy', None), ('copy-cli-untrusted', 'copy', 'untrusted'), ('copy-cli-trusted', 'copy', 'trusted'), ('worktree-cli-untrusted', 'worktree', 'untrusted')]
results = [run_case(*c) for c in cases if (ONLY or ['worktree-untrusted', 'worktree-cli-trusted', 'copy-untrusted', 'copy-cli-untrusted']).count(c[0])]
(out / 'results.json').write_text(json.dumps({'codex': str(codex), 'version': version, 'fixture': str(root), 'results': results},
                                             ensure_ascii=False, indent=2) + '\n')
for r in results:
    print(json.dumps(r, ensure_ascii=False))
