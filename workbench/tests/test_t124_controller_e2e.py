"""T-124：经角色申请批准的终端主控回答 worker 的问题、用 run 自动走完、挂只读 monitor；身份结束后已派出的工作继续。
真实后台、socket、终端（`a2a request`、`a2a release` 在终端里运行）、门禁，真实安装的 Claude Code（交互模式，在 node-pty 里）
做 worker、reviewer、monitor，模型换成本地脚本化的 Messages 接口，不调用供应商。

失败方式（先列再写）：
1. 终端主控的 answer_issue、attach、run 仍被拒（`role_command_not_scoped`）。
2. 主控的答复记成用户输入（写进 user_inputs）或人工介入；或者没有记下是哪个主控、哪次角色申请答的。
3. worker 收到的答复写成“用户答复”；或界面答复（用户）反而不再记为用户输入。
4. 门禁把 Claude Code worker 当成 Codex 线程：上报问题、run 回收 worker 被拒（`identity_conflict`，开发运行 01、11 发现）；
   Claude Code 在 worker 进程树里跑的 setuid-root `ps` 让进程快照失败，run 中途停下（`run_external_unknown`，开发运行 08～10）。
5. 主控身份还在时，run 不等主控打分就自己集成。
6. 主控身份结束（release）或额度用完后，run 卡在 verified 永远不集成；或集成时打分不是“未评分”、没写原因、没有记录。
7. 身份结束后，这个终端还能 dispatch、run、attach；或被拒却没留下记录。
8. 额度用完不读会话日志就不知道；或读了却不出通知；或额度恢复后通知不消失。
9. attach 的 monitor 能写项目；不在侧栏主控下面；启动参数不记；主控身份结束、终端关闭后 monitor 被一起回收。
--end quota：run 在 verified 时由额度用完（而不是 release）触发未评分集成。
--monitor-cli codex：monitor 用 Codex（attach 的默认 CLI，`--sandbox read-only`），模型换成本地脚本化的 Responses 接口。
--revision 在该版本的隔离源码上跑同一场景（修前应失败）；--mutant 跑已知坏实现。
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from t112_native_api import message_events, request_source, request_tools, shell_item, tool_events  # noqa: E402
TOKEN = 'a2a-fixture-key-not-a-secret'
SERVED_MODEL = 'claude-haiku-5-5-t124-served'
CONTROLLER_SESSION = 'c1a2b3c4-d5e6-4f70-8a9b-0c1d2e3f4a5b'

MUTANTS = {
    # A controller's issue answer goes down the user's path (user input, "用户答复").
    'answer-as-user': ('src/gates/core.ts', '    const controller = actor?.controller;\n    const replies =',
                       '    const controller = undefined as TerminalController | undefined;\n    const replies ='),
    # The run never notices its controller is gone and waits for a score forever.
    'run-waits-for-score': ('src/gates/core.ts', 'if (initiatorState && initiatorState !== "active") {', 'if (false) {'),
    # The run integrates without a score while its controller still holds the role.
    'run-ignores-active-controller': ('src/gates/core.ts', 'if (initiatorState && initiatorState !== "active") {', 'if (initiatorState) {'),
    # The unscored integration is written as a normal score with no reason.
    'unscored-without-reason': ('src/gates/core.ts', '? { result: "未评分", reason: run.initiator_unavailable.state === "ended" ? "主控身份已结束" : "主控额度用完" }',
                                '? { result: "未评分" }'),
    # Every thread without an attachment is taken for Codex, as before this ticket.
    'issue-provider-codex': ('src/gates/core.ts', 'return attempt && this.boundCard(attempt).executor.cli === "Claude Code" ? "claude" : "codex";', 'return "codex";'),
    # A process of another user in the worker's tree fails the snapshot, as before this ticket.
    # A Codex monitor's session cannot be bound (the resume argv refused its role), as before this ticket's fix.
    'codex-monitor-unbound': ('src/paneRecovery.ts', '["worker", "reviewer", "monitor"].includes(record.role)', '["worker", "reviewer"].includes(record.role)'),
    'snapshot-denies-privileged': ('src/processSnapshot.py', "        if size==0 and number==errno.EPERM:info=self.privileged(pid)\n        elif size",
                                   "        if size"),
    # The controller's session log is never read.
    'quota-unread': ('src/daemon.ts', 'try { quota.tick(roleRequests.all()', 'try { if (Date.now() < 0) quota.tick(roleRequests.all()'),
    # A monitor shell may write the project.
    'monitor-writable': ('src/panes.ts', 'review || monitor ? [] : [requestDirectory]', 'monitor ? [realpathSync(task.repo)] : review ? [] : [requestDirectory]'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    parser.add_argument('--end', choices=['release', 'quota'], default='release')
    parser.add_argument('--monitor-cli', choices=['claude', 'codex'], default='claude')
    parser.add_argument('--codex', default=os.path.realpath(shutil.which('codex') or str(Path.home() / '.local/bin/codex')))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t124-', dir='/private/tmp')).resolve()
    state, home, repo, out = (fixture / name for name in ('state', 'home', 'demo', 'out'))
    for path in (state, home, repo, out):
        path.mkdir()
    (home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark'}), encoding='utf-8')
    # The controller CLI's own home: only its session log is read, for the quota (failure 8).
    controller_home = fixture / 'controller-claude'
    transcript = controller_home / 'projects' / '-private-tmp-demo' / f'{CONTROLLER_SESSION}.jsonl'
    transcript.parent.mkdir(parents=True)
    MONITOR_STEP = f'git -C {repo} log --format=%s -1; echo "monitor read rc=$?"; echo x > {repo}/monitor-note.txt; echo "monitor write rc=$?"'
    source = ROOT
    if args.revision or args.mutant:
        source = fixture / 'source'
        if args.revision:
            for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', args.revision, 'workbench/src', 'workbench/terminal',
                                                 'workbench/hooks', 'workbench/roles'], cwd=ROOT, text=True).splitlines():
                target_path = source / name
                target_path.parent.mkdir(parents=True, exist_ok=True)
                mode = subprocess.check_output(['git', 'ls-tree', args.revision, name], cwd=ROOT, text=True).split()[0]
                if mode == '120000':
                    target_path.symlink_to(subprocess.check_output(['git', 'show', f'{args.revision}:{name}'], cwd=ROOT, text=True))
                    continue
                target_path.write_bytes(subprocess.check_output(['git', 'show', f'{args.revision}:{name}'], cwd=ROOT))
                if mode == '100755':
                    target_path.chmod(0o755)
            # The parent revision has no monitor card; the scenario still needs a file to name.
            (source / 'workbench/roles/monitor.md').exists() or shutil.copy(ROOT / 'workbench/roles/monitor.md', source / 'workbench/roles/monitor.md')
        else:
            for name in ('src', 'terminal', 'hooks', 'roles'):
                shutil.copytree(ROOT / 'workbench' / name, source / 'workbench' / name, symlinks=True)
            path, old, new = MUTANTS[args.mutant]
            path = source / 'workbench' / path
            text = path.read_text(encoding='utf-8')
            assert text.count(old) == 1, '变异定位必须唯一'
            path.write_text(text.replace(old, new), encoding='utf-8')
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    cli = source / 'workbench/src/gates/cli.ts'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, end=args.end, monitor_cli=args.monitor_cli,
                  fixture=str(fixture), claude=args.claude, checks=[])

    # The model: a scripted Messages endpoint. Each conversation's role is told apart by its first prompt;
    # a worker's phase by the newest prompt it was given (the dispatch, the controller's answer, the user's answer).
    api = dict(requests=0, results=dict(worker=[], reviewer=[], monitor=[]), error=None)

    def texts(message):
        content = message['content']
        if isinstance(content, str):
            return [content]
        return [part.get('text', '') for part in content if isinstance(part, dict) and part.get('type') == 'text']

    def plan_for(body):
        messages = body['messages']
        first = '\n'.join(texts(messages[0]))
        if '审查这一次交付' in first:
            shape = json.loads(first[first.rindex('{\n  "schema": 1'):])
            shape.update(verdict='可合并', findings=[], report={'结论': '候选加了 hello.txt，满足任务卡。',
                '完成条件与变异检查': '变异 1：删除 hello.txt，python3 check.py 退出 1。'})
            return 'reviewer', 0, [('Bash', dict(command='rm hello.txt; python3 check.py; echo "mutation-1 rc=$?"', description='mutation 1'))], \
                json.dumps(shape, ensure_ascii=False)
        if '角色卡：monitor' in first:
            return 'monitor', 0, [('Bash', dict(command=MONITOR_STEP, description='observe'))], '观察完毕：没有发现问题。'
        # The newest prompt (not a tool result) sets the worker's phase; steps count from it.
        phase, start = None, 0
        for index in range(len(messages) - 1, -1, -1):
            if messages[index]['role'] != 'user':
                continue
            joined = '\n'.join(texts(messages[index]))
            found = next((name for marker, name in (('用户答复', 'after-user'), ('主控答复', 'after-controller'), ('显式交付', 'dispatch'))
                          if marker in joined), None)
            if found:
                phase, start = found, index
                break
        assert phase, '找不到 worker 的当前提示'
        submit = re.search(r'显式交付：\n(.+)\n', first)
        assert submit, '派发提示里没有交付命令'
        prefix = submit.group(1).split(" 'submit' ", 1)[0]
        issue = lambda title, body: (prefix + ' issue --task T-1 --title ' + json.dumps(title, ensure_ascii=False) +
                                     ' --body ' + json.dumps(body, ensure_ascii=False))
        if phase == 'dispatch':
            steps = [('Bash', dict(command=issue('hello.txt 写什么', '任务卡没写内容，请主控决定。'), description='raise issue 1'))]
            final = '已上报问题，等答复。'
        elif phase == 'after-controller':
            steps = [('Bash', dict(command=issue('要不要加末尾换行', '请确认。'), description='raise issue 2'))]
            final = '又上报了一个问题。'
        else:
            steps = [('Write', dict(file_path=f'{body_cwd(body)}/hello.txt', content='hello from the T-124 fixture\n')),
                     ('Bash', dict(command='git add hello.txt', description='stage')),
                     ('Bash', dict(command='git commit -q -m "T-124 fixture change"', description='commit')),
                     ('Bash', dict(command=submit.group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"'), description='submit'))]
            final = '已提交并交付。'
        return 'worker', start, steps, final

    def body_cwd(body):
        found = re.search(r'[Ww]orking directory: (/[^\s"\\]+)', json.dumps(body, ensure_ascii=False))
        assert found, '请求里没有工作目录'
        return found.group(1)

    class Api(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            path = self.path.split('?', 1)[0]
            if self.headers.get('Authorization') != 'Bearer ' + TOKEN:
                api['error'] = 'request without the fixture token'
                self.send_error(401)
                return
            if path == '/v1/messages/count_tokens':
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(b'{"input_tokens":128}')
                return
            api['requests'] += 1
            with (out / 'api.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(body, ensure_ascii=False) + '\n')
            names = {tool.get('name') for tool in body.get('tools', [])}
            action, final = None, 'ok'
            if {'Bash', 'Write'} <= names:
                try:
                    role, start, steps, final = plan_for(body)
                except BaseException as error:
                    api['error'] = f'plan: {error}'
                    raise
                last = next((message['content'] for message in reversed(body['messages']) if message['role'] == 'user'), None)
                if isinstance(last, list):
                    for part in last:
                        if isinstance(part, dict) and part.get('type') == 'tool_result':
                            content = part.get('content')
                            text = content if isinstance(content, str) else ' '.join(item.get('text', '') for item in content or [] if isinstance(item, dict))
                            api['results'][role].append(dict(id=part.get('tool_use_id'), is_error=bool(part.get('is_error')), text=text[:4000]))
                used = sum(1 for message in body['messages'][start + 1:] if message['role'] == 'assistant' and isinstance(message['content'], list)
                           and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in message['content']))
                action = steps[used] if used < len(steps) else None
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()

            def emit(kind, value):
                self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps({'type': kind, **value}) + '\n\n').encode())
                self.wfile.flush()
            emit('message_start', {'message': {'id': f'msg_t124_{api["requests"]}', 'type': 'message', 'role': 'assistant',
                                               'model': SERVED_MODEL, 'content': [], 'stop_reason': None,
                                               'usage': {'input_tokens': 128, 'output_tokens': 0}}})
            if action:
                emit('content_block_start', {'index': 0, 'content_block': {'type': 'tool_use', 'id': f'toolu_t124_{api["requests"]}', 'name': action[0], 'input': {}}})
                emit('content_block_delta', {'index': 0, 'delta': {'type': 'input_json_delta', 'partial_json': json.dumps(action[1], ensure_ascii=False)}})
                reason = 'tool_use'
            else:
                emit('content_block_start', {'index': 0, 'content_block': {'type': 'text', 'text': ''}})
                emit('content_block_delta', {'index': 0, 'delta': {'type': 'text_delta', 'text': final}})
                reason = 'end_turn'
            emit('content_block_stop', {'index': 0})
            emit('message_delta', {'delta': {'stop_reason': reason, 'stop_sequence': None}, 'usage': {'output_tokens': 20}})
            emit('message_stop', {})

    server = ThreadingHTTPServer(('127.0.0.1', 0), Api)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # A Codex monitor's model: a scripted Responses endpoint, one shell step then a final message.
    class Responses(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_GET(self):
            payload = json.dumps({'object': 'list', 'data': [{'id': 'gpt-6.1-sol', 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if request_source(body) == 'thread_title':
                    events = message_events(json.dumps({'title': 'T-124 monitor'}), body['model'])
                else:
                    text = '\n'.join(part.get('text', '') for item in body['input'] if item.get('type') == 'message' and item.get('role') == 'user'
                                     for part in item.get('content', []) if isinstance(part, dict))
                    assert '角色卡：monitor' in text, '只有 monitor 用 Codex'
                    cwd = re.search(r'<cwd>([^<]+)</cwd>', text).group(1)
                    done = [item for item in body['input'] if item.get('type') == 'custom_tool_call']
                    outputs = [str(item.get('output'))[:4000] for item in body['input'] if item.get('type') == 'custom_tool_call_output']
                    if outputs:
                        api['results']['monitor'] = [dict(text=output) for output in outputs]
                    events = (tool_events(shell_item(request_tools(body), MONITOR_STEP, cwd), body['model']) if not done
                              else message_events('观察完毕：没有发现问题。', body['model']))
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for sequence, (name, payload) in enumerate(events):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api['error'] = f'responses: {type(error).__name__}: {error}'
                self.send_error(500)

    responses = ThreadingHTTPServer(('127.0.0.1', 0), Responses)
    threading.Thread(target=responses.serve_forever, daemon=True).start()
    codex_home = home / '.codex'
    codex_home.mkdir()
    (codex_home / 'config.toml').write_text('model_provider = "t124"\ncli_auth_credentials_store = "file"\n[model_providers.t124]\nname = "T124 fixture"\n'
        f'base_url = "http://127.0.0.1:{responses.server_port}/v1"\nwire_api = "responses"\nrequires_openai_auth = false\n', encoding='utf-8')

    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', ELECTRON_RUN_AS_NODE='1',
               A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'),
               ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}', ANTHROPIC_AUTH_TOKEN=TOKEN,
               GIT_AUTHOR_NAME='t124', GIT_AUTHOR_EMAIL='t124@example.invalid',
               GIT_COMMITTER_NAME='t124', GIT_COMMITTER_EMAIL='t124@example.invalid')
    env.pop('ZDOTDIR', None)
    running = False

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def run_cli(*arguments):
        run = subprocess.run(['node', str(cli), '--state', str(state), *arguments], env=env, capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, f'{arguments[0]}: {run.stderr or run.stdout}'
        return json.loads(run.stdout)

    def request(command, identity=None, timeout=60, **data):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(timeout)
            connection.connect(str(state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)) + '\n').encode())
            response = b''
            while b'\n' not in response:
                part = connection.recv(65536)
                assert part, 'daemon 在回执前断开'
                response += part
        return json.loads(response.split(b'\n', 1)[0])

    def events(types=None):
        rows = request('orchestration_events')['events']
        return [row for row in rows if types is None or row['type'] in types]

    def gate_events(operator, types):
        return [e for e in request('events', operator, task='T-1')['events'] if e['type'] in types]

    def wait(label, predicate, timeout=90):
        deadline = time.monotonic() + timeout
        while True:
            value = predicate()
            if value:
                return value
            assert not api['error'], api['error']
            assert time.monotonic() < deadline, f'超时：{label}'
            time.sleep(.2)

    def output(launch):
        result = request('pane_output', launch=launch, offset=0)
        assert result['ok'], result
        text = base64.b64decode(result['data_base64']).decode('utf-8', 'replace')
        return re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))', '', text)

    def stamp(offset=0):
        return datetime.fromtimestamp(time.time() + offset, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    def log_quota(rejected):
        # The records Claude Code writes when the account's limit rejects a request, and when a reply works again.
        record = (dict(type='assistant', isApiErrorMessage=True, timestamp=stamp(1), sessionId=CONTROLLER_SESSION,
                       quotaLimits=dict(status='rejected', rateLimitType='five_hour', resetsAt=int(time.time()) + 3600),
                       message=dict(role='assistant', content=[dict(type='text', text='usage limit reached')]))
                  if rejected else dict(type='assistant', timestamp=stamp(1), sessionId=CONTROLLER_SESSION,
                                        message=dict(role='assistant', content=[dict(type='text', text='ok')])))
        with transcript.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record) + '\n')

    try:
        config = dict(claude_bin=args.claude, codex_bin=args.codex, codex_home=str(codex_home), role_card=str(source / 'workbench/roles/worker.md'), role_card_revision='t124-fixture',
                      reviewer_role_card=str(source / 'workbench/roles/reviewer.md'), reviewer_role_card_revision='t124-fixture',
                      monitor_role_card=str(source / 'workbench/roles/monitor.md'), monitor_role_card_revision='t124-fixture',
                      code_revision='t124-fixture', hook_authorization='T-124 fixture: hooks only through launch arguments', turn_limit=6)
        (fixture / 'launch-config.json').write_text(json.dumps(config), encoding='utf-8')
        run_cli('daemon_start', '--launch-config', str(fixture / 'launch-config.json'))
        running = True
        wait('后台恢复结束', lambda: request('pane_layout').get('recovering') is False, 10)
        operator = json.loads((fixture / 'operator.json').read_text(encoding='utf-8'))

        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=env)
        (repo / 'README.md').write_text('demo\n', encoding='utf-8')
        (repo / 'check.py').write_text('import pathlib, sys\nsys.exit(0 if pathlib.Path("hello.txt").is_file() else 1)\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', 'README.md', 'check.py'], check=True, env=env)
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'init'], check=True, env=env)
        assert request('project_open', operator, repo=str(repo))['ok']

        # The controller: a project terminal whose CLI asks for the executor role with `a2a request`,
        # reporting its own session the way Claude Code's environment does.
        launch = run_cli('shell_start', '--project', 'demo', '--cwd', str(repo))['launch']['id']
        window = request('window_open', operator, launch=launch, project='demo')
        assert window['ok'], window
        shell = dict(identity=window['identity'], sequence=0)

        def type_line(line, marker, timeout=30):
            shell['sequence'] += 1
            sent = request('window_input', shell['identity'], sequence=shell['sequence'], request_id=str(uuid.uuid4()),
                           data=f'{line}; print -r -- "{marker}=$?"\r')
            assert sent['ok'], sent
            found = wait(f'终端输出 {marker}', lambda: re.search(rf'^{marker}=(\d+)\r?$', output(launch), re.M), timeout)
            return int(found.group(1))

        type_line(f'print -r -- $A2A_TERMINAL_TOKEN > {out}/token.txt', 'T124-TOKEN')
        terminal = dict(kind='terminal', launch=launch, token=(out / 'token.txt').read_text().strip())
        type_line(f'(CLAUDECODE=1 CLAUDE_CODE_SESSION_ID={CONTROLLER_SESSION} CLAUDE_CONFIG_DIR={controller_home} '
                  f'a2a request executor > {out}/request.json 2>/dev/null; print $? > {out}/request.exit) &!', 'T124-REQUEST-SENT')
        pending = wait('角色申请出现', lambda: request('sidebar_snapshot').get('role_requests'), 20)
        assert request('role_request_decide', operator, role_request=pending[0]['id'], approved=True)['ok']
        wait('a2a request 返回', lambda: (out / 'request.exit').exists() and (out / 'request.exit').read_text().strip(), 30)
        granted = json.loads((out / 'request.json').read_text(encoding='utf-8'))
        report['role_request'] = granted.get('role_request')
        assert granted.get('ok'), granted

        # 8: the quota is read from the controller's own session log, and the notice goes once it works again.
        log_quota(True)
        exhausted = wait('额度用完通知', lambda: request('sidebar_snapshot').get('controller_quota'), 30)
        report['quota_notice'] = exhausted
        check('quota_exhausted_noticed', len(exhausted) == 1 and exhausted[0]['launch'] == launch and exhausted[0]['role_label'] == '执行主控' and
              exhausted[0]['project'] == 'demo' and exhausted[0]['resets_at'], exhausted)
        log_quota(False)
        wait('额度恢复', lambda: request('sidebar_snapshot').get('controller_quota') == [], 30)
        quota_events = [e['type'] for e in events({'controller_quota_exhausted', 'controller_quota_restored'})]
        check('quota_events_recorded', quota_events == ['controller_quota_exhausted', 'controller_quota_restored'], quota_events)

        card = out / 'card.json'
        card.write_text(json.dumps(dict(id='T-1', source=None, goal='在仓库根目录加 hello.txt', non_goals=['不改别的文件'],
            paths=dict(allow=['hello.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
            red_commands=[], task_type='测试', repair_target=None, complexity='S',
            executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
        assert request('card_save', terminal, task='T-1', card=str(card), expected_version=0)['ok']
        assert request('create', terminal, task='T-1', project='demo', repo=str(repo), branch='refs/heads/main', card_version=1)['ok']
        user_inputs_before = len(request('issues', operator, task='T-1')['user_inputs'])

        # 1: the controller starts a run; it returns only when the task ends.
        run_result = {}

        def start_run():
            try:
                run_result['value'] = request('run', terminal, timeout=900, task='T-1', runtimeMode='workspace-write', wait_seconds=800)
            except BaseException as error:
                run_result['value'] = dict(ok=False, error=f'{type(error).__name__}: {error}')
        runner = threading.Thread(target=start_run, daemon=True)
        runner.start()
        time.sleep(1)
        check('run_opened_to_terminal', 'value' not in run_result or run_result['value'].get('error') != 'role_command_not_scoped',
              run_result.get('value'))
        worker = wait('worker 启动', lambda: next((r for r in request('sidebar_snapshot')['agents'] if r['role'] == 'worker'), None)
                      if 'value' not in run_result else (_ for _ in ()).throw(AssertionError(run_result['value'])), 60)
        worker_launch = worker['id']

        # 9: a read-only monitor, attached by the controller while the run goes on.
        instructions = out / 'monitor.txt'
        instructions.write_text('看一下项目最近的提交，写一句观察。\n', encoding='utf-8')
        # No cli for Codex: attach's default.
        attached = request('attach', terminal, task='T-1', role='monitor', instructions=str(instructions),
                           **(dict(cli='Claude Code', model='claude-haiku-5-5') if args.monitor_cli == 'claude' else dict(model='gpt-6.1-sol')), effort='low')
        report['attach'] = {key: attached.get(key) for key in ('ok', 'error', 'details')}
        check('attach_starts_monitor', attached.get('ok'), report['attach'])
        monitor = next(record for record in (request('launch_show', operator, launch=row['id'])['launch'] for row in request('sidebar_snapshot')['agents']
                                             if row['role'] == 'monitor'))
        margv = monitor['argv']
        nested = next(r for r in request('sidebar_snapshot')['agents'] if r['id'] == monitor['id'])
        check('monitor_nested_under_controller', nested.get('parent') == launch and nested.get('task') == 'T-1', nested)
        if args.monitor_cli == 'claude':
            msettings = json.loads(margv[margv.index('--settings') + 1])
            report['monitor'] = dict(role=monitor['role'], parent=monitor['parent_launch'], cli=monitor['cli'], argv=margv[:-1], settings=msettings)
            read_only = (monitor['cli'] == 'Claude Code' and margv[margv.index('--model') + 1] == 'claude-haiku-5-5' and
                         msettings['sandbox']['filesystem'].get('allowWrite') == [] and
                         not any(rule.startswith('Edit(') for rule in msettings['permissions']['allow']))
        else:
            report['monitor'] = dict(role=monitor['role'], parent=monitor['parent_launch'], cli=monitor['cli'], argv=margv, sandbox=monitor['sandbox'])
            read_only = (monitor['cli'] == 'Codex' and margv[margv.index('--sandbox') + 1] == 'read-only' and monitor['sandbox'] == 'read-only' and
                         margv[margv.index('-m') + 1] == 'gpt-6.1-sol' and margv[margv.index('-C') + 1] != str(repo))
        check('monitor_launch_recorded_read_only', monitor['role'] == 'monitor' and monitor['parent_launch'] == launch and read_only, report['monitor'])
        monitor_results = wait('monitor 回合', lambda: api['results']['monitor'] or None, 120)
        report['monitor_results'] = monitor_results
        check('monitor_reads_but_cannot_write', 'monitor read rc=0' in monitor_results[0]['text'] and
              'T-1' not in monitor_results[0]['text'] and 'monitor write rc=1' in monitor_results[0]['text'] and
              not (repo / 'monitor-note.txt').exists(), monitor_results)

        # 2, 3: the worker's first issue, answered by the controller.
        issue_one = wait('第一个问题', lambda: next((view for view in request('issues', terminal, task='T-1').get('issues', [])
                                                  if view['issue']['title'] == 'hello.txt 写什么'), None), 120)
        answered = request('answer_issue', terminal, task='T-1', issue=issue_one['issue']['id'], answer='写一行 hello 即可。')
        report['controller_answer'] = {key: answered.get(key) for key in ('ok', 'error', 'details')}
        check('controller_answers_issue', answered.get('ok'), report['controller_answer'])
        views = request('issues', operator, task='T-1')
        record = next(view for view in views['issues'] if view['issue']['id'] == issue_one['issue']['id'])['answer']
        report['controller_answer_record'] = record
        check('controller_answer_recorded_as_controller', record['from'] == 'executor' and
              f'controller-launch:{launch}' in record['refs'] and f"role-request:{granted['role_request']['id']}" in record['refs'] and
              not record.get('input_id'), record)
        check('controller_answer_not_user_input', len(views['user_inputs']) == user_inputs_before, views['user_inputs'])
        check('controller_answer_not_intervention', not gate_events(operator, {'human_intervention'}), gate_events(operator, {'human_intervention'}))
        check('controller_answer_event', [e['details']['launch'] for e in gate_events(operator, {'controller_answer'})] == [launch])

        # 3: the second issue, answered by the user in the workbench, stays user input.
        issue_two = wait('第二个问题', lambda: next((view for view in request('issues', operator, task='T-1').get('issues', [])
                                                  if view['issue']['title'] == '要不要加末尾换行'), None), 120)
        user_answer = request('answer_issue', operator, task='T-1', issue=issue_two['issue']['id'], answer='要。')
        check('user_answers_issue', user_answer.get('ok'), user_answer)
        views = request('issues', operator, task='T-1')
        check('user_answer_is_user_input', len(views['user_inputs']) == user_inputs_before + 1 and
              views['user_inputs'][-1]['text'] == '要。', views['user_inputs'])
        def worker_texts():
            # The newest worker request carries the whole conversation.
            bodies = [json.loads(line) for line in (out / 'api.jsonl').read_text(encoding='utf-8').splitlines()]
            body = [body for body in bodies if '显式交付' in '\n'.join(texts(body['messages'][0]))][-1]
            return '\n'.join(text for message in body['messages'] if message['role'] == 'user' for text in texts(message))
        wait('用户的答复到达 worker', lambda: '用户答复：要。' in worker_texts(), 60)
        check('worker_sees_who_answered', '主控答复：写一行 hello 即可。' in worker_texts() and worker_texts().count('用户答复') == 1)

        # 5: verified with the controller still in its role: the run waits for its score.
        task = wait('审查通过', lambda: (lambda current: current if current['state'] in ('verified', 'accepted', 'failed', 'rework') else None)(
            request('status', operator, task='T-1')['task']), 300)
        time.sleep(4)
        held = request('status', operator, task='T-1')['task']['state']
        early = gate_events(operator, {'run_initiator_ended', 'score_recorded'})
        phase = (request('status', operator, task='T-1').get('run') or {}).get('phase')
        report['while_active'] = dict(state=held, early=[e['type'] for e in early], run_returned='value' in run_result, phase=phase)
        check('run_waits_for_active_controller_score', task['state'] == 'verified' and held == 'verified' and not early and
              'value' not in run_result, report['while_active'])

        # 6, 7: the role ends while the run waits for its score. After a release this terminal can start no new
        # work (each refusal recorded); then the terminal is closed. The run goes on to integrate through the gate.
        if args.end == 'release':
            check('release_from_terminal', type_line(f'a2a release > {out}/release.json', 'T124-RELEASE') == 0,
                  (out / 'release.json').read_text(encoding='utf-8'))
            refused = {command: request(command, terminal, task='T-1', **data).get('error') for command, data in (
                ('dispatch', dict(runtimeMode='workspace-write')), ('run', dict(runtimeMode='workspace-write', wait_seconds=60)),
                ('attach', dict(role='monitor', instructions=str(instructions))))}
            rejected = [e['data']['input']['command'] for e in events({'request_rejected'})
                        if e['data']['result'].get('error') == 'approved_role_required']
            report['after_release'] = dict(refused=refused, rejected=rejected)
            check('new_work_refused_after_release', set(refused.values()) == {'approved_role_required'} and
                  {'dispatch', 'run', 'attach'} <= set(rejected), report['after_release'])
            assert request('shell_close', operator, launch=launch)['ok']
            reason = '主控身份已结束'
        else:
            log_quota(True)
            reason = '主控额度用完'
        runner.join(240)
        report['run'] = {key: (run_result.get('value') or {}).get(key) for key in ('ok', 'error', 'details')}
        report['run_outcome'] = ((run_result.get('value') or {}).get('run') or {}).get('outcome')
        final = request('status', operator, task='T-1')['task']
        main_files = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', '--name-only', 'refs/heads/main'], text=True).split()
        check('run_integrates_after_role_ends', run_result.get('value', {}).get('ok') and final['state'] == 'accepted' and 'hello.txt' in main_files,
              dict(run=report['run'], state=final['state'], files=main_files))
        scores = [e['details'] for e in gate_events(operator, {'score_recorded'})]
        report['score_recorded'] = scores
        # The user's answer to issue 2 is the one human intervention; the controller's answer adds none.
        check('integration_recorded_unscored', len(scores) == 1 and scores[0]['source'] == 'executor' and
              scores[0]['data'] == {'result': '未评分', 'reason': reason} and scores[0]['facts']['human_interventions'] == 1, scores)
        ended = [e['details'] for e in gate_events(operator, {'run_initiator_ended'})]
        check('run_initiator_end_recorded', len(ended) == 1 and ended[0]['launch'] == launch and
              ended[0]['state'] == ('ended' if args.end == 'release' else 'quota_exhausted'), ended)

        # 9: the monitor outlives the role and the terminal.
        if args.end == 'quota':
            assert request('shell_close', operator, launch=launch)['ok']
        time.sleep(2)
        row = next(r for r in request('sidebar_snapshot')['agents'] if r['id'] == monitor['id'])
        stopped = [e['type'] for e in events({'pane_exit', 'pane_stopped', 'pane_archived'}) if e['launch'] == monitor['id']]
        # The sidebar nests a session under a controller only while that controller holds its role; the
        # launch record keeps who started it.
        shown = request('launch_show', operator, launch=monitor['id'])
        assert shown.get('ok'), shown
        record = shown['launch']
        report['monitor_after'] = dict(state=row['state'], task=row.get('task'), parent=row.get('parent'), parent_launch=record['parent_launch'], stopped=stopped)
        check('monitor_survives_role_and_terminal', not stopped and row['role'] == 'monitor' and row['state'] != 'exited' and
              row.get('task') == 'T-1' and record['parent_launch'] == launch, report['monitor_after'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api_snapshot'] = dict(requests=api['requests'], results=api['results'], error=api['error'])
        try:
            report['events_tail'] = [dict(type=e['type'], launch=e['launch']) for e in events()][-60:]
        except BaseException:
            pass
        raise
    finally:
        try:
            if running:
                run_cli('daemon_stop')
        finally:
            server.shutdown()
            responses.shutdown()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
