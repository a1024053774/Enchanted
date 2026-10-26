"""Shared fixture for end-to-end runs with a real daemon, an approved terminal controller and real Claude Code
workers whose model is a local scripted Messages endpoint (no vendor calls). Used from T-132 on; the T-122 and
T-131 tests keep their own copies."""
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[2]
TOKEN = 'a2a-fixture-key-not-a-secret'
SERVED_MODEL = 'claude-haiku-5-5-scripted-served'


def source_tree(fixture, revision=None, patches=()):
    """The workbench sources to run: the checkout, a revision's tree, or a patched copy."""
    if not revision and not patches:
        return ROOT
    source = fixture / 'source'
    parts = ['workbench/src', 'workbench/terminal', 'workbench/hooks', 'workbench/roles', 'workbench/app', 'workbench/LICENSE.synara']
    if revision:
        for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision, *parts], cwd=ROOT, text=True).splitlines():
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            mode = subprocess.check_output(['git', 'ls-tree', revision, name], cwd=ROOT, text=True).split()[0]
            if mode == '120000':
                target.symlink_to(subprocess.check_output(['git', 'show', f'{revision}:{name}'], cwd=ROOT, text=True))
                continue
            target.write_bytes(subprocess.check_output(['git', 'show', f'{revision}:{name}'], cwd=ROOT))
            if mode == '100755':
                target.chmod(0o755)
    else:
        for part in parts:
            if (ROOT / part).is_dir():
                shutil.copytree(ROOT / part, source / part, symlinks=True)
            else:
                shutil.copy2(ROOT / part, source / part)
    for path, old, new in patches:
        path = source / 'workbench' / path
        text = path.read_text(encoding='utf-8')
        assert text.count(old) == 1, '变异定位必须唯一'
        path.write_text(text.replace(old, new), encoding='utf-8')
    for name in ('node_modules', 'package.json'):
        (source / 'workbench' / name).symlink_to(ROOT / 'workbench' / name)
    return source


def prompt_text(body):
    first = body['messages'][0]['content']
    return first if isinstance(first, str) else '\n'.join(part.get('text', '') for part in first if isinstance(part, dict))


def working_directory(body):
    found = re.search(r'[Ww]orking directory: (/[^\s"\\]+)', json.dumps(body, ensure_ascii=False))
    assert found, '请求里没有工作目录'
    return found.group(1)


def gate_line(body, command):
    """The CLI entry from the dispatch prompt's submit line, with another command; {task} becomes the gate task id."""
    submit = re.search(r'显式交付：\n(.+)\n', prompt_text(body))
    assert submit, '派发提示里没有交付命令'
    task = re.search(r"'--task' '([^']+)'", submit.group(1)).group(1)
    return submit.group(1)[:submit.group(1).index("'submit'")] + command.replace('{task}', task)


def quote(value):
    return "'" + value.replace("'", "'\\''") + "'"


class ScriptedApi:
    """A Messages endpoint. plan(body) -> (conversation key, [(tool, input), ...], final text) for each main-loop
    request; the step is the number of tool calls the conversation already made. Side requests get short text."""

    def __init__(self, plan, out):
        self.plan, self.out = plan, out
        self.requests = self.main = 0
        self.results, self.bodies, self.error = {}, [], None
        self.lock = threading.Lock()
        api = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *values):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if self.headers.get('Authorization') != 'Bearer ' + TOKEN:
                    api.error = 'request without the fixture token'
                    self.send_error(401)
                    return
                if self.path.split('?', 1)[0] == '/v1/messages/count_tokens':
                    self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                    self.wfile.write(b'{"input_tokens":128}')
                    return
                with api.lock:
                    api.requests += 1
                    number = api.requests
                action, final = None, 'ok'
                if {'Bash', 'Write'} <= {tool.get('name') for tool in body.get('tools', [])}:
                    try:
                        key, steps, final = api.plan(body)
                    except Exception as error:  # a plan failure is the test's failure, reported at its next wait
                        api.error = f'plan: {type(error).__name__}: {error}'
                        raise
                    messages = body['messages']
                    with api.lock:
                        api.main += 1
                        api.bodies.append(dict(key=key, messages=messages))
                    last = next((message['content'] for message in reversed(messages) if message['role'] == 'user'), None)
                    if isinstance(last, list):
                        for part in last:
                            if isinstance(part, dict) and part.get('type') == 'tool_result':
                                content = part.get('content')
                                text = content if isinstance(content, str) else ' '.join(item.get('text', '') for item in content or [] if isinstance(item, dict))
                                with api.lock:
                                    api.results.setdefault(key, []).append(dict(is_error=bool(part.get('is_error')), text=text[:2000]))
                    step = sum(1 for message in messages if message['role'] == 'assistant' and isinstance(message['content'], list)
                               and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in message['content']))
                    action = steps[step] if step < len(steps) else None
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()

                def emit(kind, value):
                    self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps({'type': kind, **value}) + '\n\n').encode())
                    self.wfile.flush()
                emit('message_start', {'message': {'id': f'msg_scripted_{number}', 'type': 'message', 'role': 'assistant',
                                                   'model': SERVED_MODEL, 'content': [], 'stop_reason': None,
                                                   'usage': {'input_tokens': 128, 'output_tokens': 0}}})
                if action:
                    emit('content_block_start', {'index': 0, 'content_block': {'type': 'tool_use', 'id': f'toolu_scripted_{number}', 'name': action[0], 'input': {}}})
                    emit('content_block_delta', {'index': 0, 'delta': {'type': 'input_json_delta', 'partial_json': json.dumps(action[1], ensure_ascii=False)}})
                    reason = 'tool_use'
                else:
                    emit('content_block_start', {'index': 0, 'content_block': {'type': 'text', 'text': ''}})
                    emit('content_block_delta', {'index': 0, 'delta': {'type': 'text_delta', 'text': final}})
                    reason = 'end_turn'
                emit('content_block_stop', {'index': 0})
                emit('message_delta', {'delta': {'stop_reason': reason, 'stop_sequence': None}, 'usage': {'output_tokens': 20}})
                emit('message_stop', {})

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def snapshot(self):
        return dict(requests=self.requests, main=self.main, results=self.results)


class Fixture:
    def __init__(self, prefix, plan, source=None, revision=None, patches=(), home=None, repo=None):
        """home: run in this existing HOME instead of a fixture one, and write nothing into it (T-187: real agy and
        opencode run in the user's own HOME). repo: where to make the project repository; its name is the project's."""
        self.dir = Path(tempfile.mkdtemp(prefix=prefix, dir='/private/tmp')).resolve()
        self.state, self.out = self.dir / 'state', self.dir / 'out'
        self.home = Path(home) if home else self.dir / 'home'
        self.repo = Path(repo) if repo else self.dir / 'demo'
        self.project = self.repo.name
        for path in (self.state, self.out, self.repo) + (() if home else (self.home,)):
            path.mkdir()
        if not home:
            (self.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark'}), encoding='utf-8')
        self.source = source or source_tree(self.dir, revision, patches)
        self.cli = self.source / 'workbench/src/gates/cli.ts'
        self.api = ScriptedApi(plan, self.out)
        self.env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
        self.env.update(HOME=str(self.home), SHELL='/bin/zsh', TERM='xterm-256color', ELECTRON_RUN_AS_NODE='1',
                        A2A_OPERATOR_CREDENTIAL=str(self.dir / 'operator.json'),
                        ANTHROPIC_BASE_URL=f'http://127.0.0.1:{self.api.server.server_port}', ANTHROPIC_AUTH_TOKEN=TOKEN,
                        GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                        GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
        self.running = False
        self.operator = self.terminal = self.terminal_launch = None

    def run_cli(self, *arguments):
        run = subprocess.run(['node', str(self.cli), '--state', str(self.state), *arguments], env=self.env, capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, f'{arguments[0]}: {run.stderr or run.stdout}'
        return json.loads(run.stdout)

    def request(self, command, identity=None, **data):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(60)
            connection.connect(str(self.state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)) + '\n').encode())
            response = b''
            while b'\n' not in response:
                part = connection.recv(65536)
                assert part, 'daemon 在回执前断开'
                response += part
        return json.loads(response.split(b'\n', 1)[0])

    def wait(self, label, predicate, timeout=90):
        deadline = time.monotonic() + timeout
        while True:
            value = predicate()
            if value:
                return value
            assert not self.api.error, self.api.error
            assert time.monotonic() < deadline, f'超时：{label}'
            time.sleep(.2)

    def git(self, *arguments):
        return subprocess.check_output(['git', '-C', str(self.repo), *arguments], text=True).strip()

    def start(self, claude, files, launch_config=None):
        """Start the daemon, make the demo repository with the given files, open it, and approve a terminal controller.
        launch_config adds to the daemon's worker launch configuration (T-187: agy_bin, opencode_bin)."""
        config = dict(claude_bin=claude, role_card=str(self.source / 'workbench/roles/worker.md'), role_card_revision='fixture',
                      reviewer_role_card=str(self.source / 'workbench/roles/reviewer.md'), reviewer_role_card_revision='fixture',
                      monitor_role_card=str(self.source / 'workbench/roles/monitor.md'), monitor_role_card_revision='fixture',
                      code_revision='fixture', hook_authorization='fixture: hooks only through launch arguments', turn_limit=6,
                      **(launch_config or {}))
        (self.dir / 'launch-config.json').write_text(json.dumps(config), encoding='utf-8')
        self.run_cli('daemon_start', '--launch-config', str(self.dir / 'launch-config.json'))
        self.running = True
        self.wait('后台恢复结束', lambda: self.request('pane_layout').get('recovering') is False, 10)
        self.operator = json.loads((self.dir / 'operator.json').read_text(encoding='utf-8'))
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(self.repo)], check=True, env=self.env)
        for name, text in files.items():
            (self.repo / name).write_text(text, encoding='utf-8')
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True, env=self.env)
        subprocess.run(['git', '-C', str(self.repo), 'commit', '-q', '-m', 'init'], check=True, env=self.env)
        assert self.request('project_open', self.operator, repo=str(self.repo))['ok']
        launch = self.run_cli('shell_start', '--project', self.project, '--cwd', str(self.repo))['launch']['id']
        window = self.request('window_open', self.operator, launch=launch, project=self.project)
        assert window['ok'], window
        sent = self.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()),
                            data=f'print -r -- $A2A_TERMINAL_TOKEN > {self.out}/token.txt\r')
        assert sent['ok'], sent
        token = self.out / 'token.txt'
        self.wait('终端写出令牌', lambda: token.exists() and token.read_text().strip(), 30)
        self.terminal_launch = launch
        self.terminal = dict(kind='terminal', launch=launch, token=token.read_text().strip())
        asker = socket.socket(socket.AF_UNIX)
        asker.connect(str(self.state / 'control.sock'))
        asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role='executor', wait_seconds=60),
                                       identity=self.terminal)) + '\n').encode())
        pending = self.wait('角色申请出现', lambda: self.request('sidebar_snapshot').get('role_requests'), 20)
        assert self.request('role_request_decide', self.operator, role_request=pending[0]['id'], approved=True)['ok']
        response = b''
        while b'\n' not in response:
            response += asker.recv(65536)
        asker.close()
        granted = json.loads(response.split(b'\n', 1)[0])
        assert self.request('role_request_confirm', self.terminal, role_request=granted['role_request']['id'])['ok']

    def card(self, task, allow, oracle, task_type='测试'):
        path = self.out / f'{task}.json'
        path.write_text(json.dumps(dict(id=task, source=None, goal=f'在仓库根目录加 {allow}', non_goals=['不改别的文件'],
            paths=dict(allow=[allow], deny=[]), oracle_paths=[oracle], completion_conditions=[dict(argv=['python3', oracle])],
            red_commands=[], task_type=task_type, repair_target=None, complexity='S',
            executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
        saved = self.request('card_save', self.terminal, task=task, card=str(path), expected_version=0)
        assert saved['ok'], saved
        created = self.request('create', self.terminal, task=task, project=self.project, repo=str(self.repo), branch='refs/heads/main', card_version=1)
        assert created['ok'], created

    def stop(self):
        try:
            if self.running:
                self.running = False
                self.run_cli('daemon_stop')
        finally:
            self.api.server.shutdown()


class Electron:
    """The workbench window, built from the given sources into a fresh slot, driven over the DevTools protocol
    by tests/cdp.mjs. Build output is removed by stop()."""

    def __init__(self, fixture, slot):
        self.fixture = fixture
        app = fixture.source / 'workbench/app'
        built = subprocess.run(['node', str(app / 'build.mjs'), '--slot', slot], cwd=fixture.source / 'workbench',
                               capture_output=True, text=True, timeout=600)
        if built.returncode != 0:
            failed = Path(os.environ.get('TMPDIR', '/tmp')) / ('a2a-build-' + slot)
            if failed.is_dir():
                shutil.rmtree(failed)
            raise AssertionError(built.stderr[-2000:])
        self.build = json.loads(built.stdout.strip().splitlines()[-1])
        self.slot = Path(self.build['out']).parent
        electron = subprocess.check_output(['node', '-p', "require('electron')"], cwd=ROOT / 'workbench', text=True).strip()
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            self.port = probe.getsockname()[1]
        env = {key: value for key, value in fixture.env.items() if key != 'ELECTRON_RUN_AS_NODE'}
        self.log = (fixture.out / 'electron.log').open('w')
        self.process = subprocess.Popen([electron, str(ROOT / 'workbench/tests/cdp_launch.cjs'), self.build['main'], str(fixture.state),
                                         str(fixture.dir / 'ui'), str(self.port)], env=env, stdout=self.log, stderr=subprocess.STDOUT,
                                        start_new_session=True)

    def evaluate(self, expression, timeout=20):
        run = subprocess.run(['node', str(ROOT / 'workbench/tests/cdp.mjs'), str(self.port), 'eval', expression],
                             capture_output=True, text=True, timeout=timeout)
        assert run.returncode == 0, run.stderr[-2000:]
        return json.loads(run.stdout)

    def until(self, label, expression, timeout=60):
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            try:
                value = self.evaluate(expression)
                if value:
                    return value
            except AssertionError as error:
                last = str(error)
            time.sleep(.3)
        raise AssertionError(f'超时：{label} {last or ""}')

    def screenshot(self, path):
        run = subprocess.run(['node', str(ROOT / 'workbench/tests/cdp.mjs'), str(self.port), 'shot', str(path)],
                             capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, run.stderr[-2000:]

    def stop(self):
        try:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
        finally:
            self.log.close()
            if self.slot.name.startswith('a2a-build-') and self.slot.is_dir():
                shutil.rmtree(self.slot)
