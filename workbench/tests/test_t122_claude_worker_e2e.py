"""T-122：经角色申请批准的终端主控派发 Claude Code worker。真实后台、socket、终端、门禁，
真实安装的 Claude Code（交互模式，在 node-pty 里），模型换成本地脚本化的 Messages 接口，不调用供应商。

失败方式（先列再写）：
1. 任务卡写 Claude Code，后台仍只会起 Codex（`worker_executor_mismatch`），或者起了却不带权限参数。
2. worker 加载了用户自己的设置、钩子或 MCP；没有 `dontAsk`，越界写入弹批准而不是被拒。
3. worker 能写出 worktree：文件工具写外面没被拒，或者拒绝没留下记录。
4. 新 worktree 的信任对话框没人按，worker 卡住；或者在收到任务后还会被代按。
5. 第一条任务在 CLI 就绪前送出（丢失），或者永远不送出（没人做初次放行）。
6. 提交钩子拿不到 Claude 的原生会话，提交失败或尾注与启动记录不符；门禁只认 Codex 的线程身份。
7. Stop 钩子没把交付请求转给门禁，或者转交时调用者身份核对失败。
8. 终端主控派出的 worker 没记上派发它的终端，侧栏显示为“未归属”。
9. 刚打开、还没有任务的项目，`inbox_ready` 返回 `unknown_project`。
10. Claude worker 的交付起不了审查（审查只认 Codex 的预建 home），或审查者换了 CLI/模型、能写候选 worktree、不在一次性副本里跑变异。
11. 审查通过后，打分与集成走不到项目工作分支。
--revision 在该版本的隔离源码上跑同一场景（修前应失败）；--mutant 跑已知坏实现。
"""
import argparse
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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[2]
TOKEN = 'a2a-fixture-key-not-a-secret'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['trust-unanswered', 'no-initial-release', 'user-settings-loaded',
                                             'codex-provider-only', 'no-terminal-parent', 'inbox-tasks-only',
                                             'reviewer-codex-only', 'reviewer-shell-writable'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t122-', dir='/private/tmp')).resolve()
    state, home, repo, out, outside = (fixture / name for name in ('state', 'home', 'demo', 'out', 'outside'))
    for path in (state, home, repo, out, outside):
        path.mkdir()
    # A Claude Code that has been set up once; the fixture HOME holds no login and no trust entries.
    (home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark'}), encoding='utf-8')
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
        else:
            for name in ('src', 'terminal', 'hooks', 'roles'):
                shutil.copytree(ROOT / 'workbench' / name, source / 'workbench' / name, symlinks=True)
            path, old, new = {
                'trust-unanswered': ('src/panes.ts', 'if (claude && pane.state === "unknown") this.confirmWorkerTrust(pane, data);', ''),
                'no-initial-release': ('src/panes.ts', '        pane.state = "idle";\n        return;', '        return;'),
                'user-settings-loaded': ('src/panes.ts', '"--setting-sources", "local", "--strict-mcp-config", ', ''),
                'codex-provider-only': ('src/gates/core.ts', '["codex", "claude"].includes(live.provider) &&', 'live.provider === "codex" &&'),
                'no-terminal-parent': ('src/daemon.ts', 'await panes.parentLaunch.run(terminal.id, () => gates.call(', 'await panes.parentLaunch.run(null, () => gates.call('),
                'inbox-tasks-only': ('src/gates/core.ts', 'if (opened) repos.add(opened);', ''),
                'reviewer-codex-only': ('src/panes.ts', '    if (task.card.executor.cli === "Claude Code") {\n      // D24', '    if (false) {\n      // D24'),
                'reviewer-shell-writable': ('src/panes.ts', 'review ? [] : [gitMetadata!, requestDirectory]', 'review ? [requestDirectory] : [gitMetadata!, requestDirectory]'),
            }[args.mutant]
            path = source / 'workbench' / path
            text = path.read_text(encoding='utf-8')
            assert text.count(old) == 1, '变异定位必须唯一'
            path.write_text(text.replace(old, new), encoding='utf-8')
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    cli = source / 'workbench/src/gates/cli.ts'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, fixture=str(fixture),
                  claude=args.claude, real_model_turns=0, checks=[])

    # The model: a scripted Messages endpoint. It answers each main-loop conversation (worker or
    # reviewer, told apart by the first prompt) by position, and any side request (no tools) with a short text.
    api = dict(requests=0, main=0, results=dict(worker=[], reviewer=[]), models=set(), error=None)

    def plan_for(body):
        # Claude Code states its working directory in the system prompt or a system-role message.
        found = re.search(r'[Ww]orking directory: (/[^\s"\\]+)', json.dumps(body, ensure_ascii=False))
        assert found, '请求里没有工作目录'
        cwd = found.group(1)
        first = body['messages'][0]['content']
        text = first if isinstance(first, str) else '\n'.join(part.get('text', '') for part in first if isinstance(part, dict))
        if '审查这一次交付' in text:
            shape = json.loads(text[text.rindex('{\n  "schema": 1'):])
            shape.update(verdict='可合并', findings=[], report={'结论': '候选加了 hello.txt，满足任务卡。',
                '完成条件与变异检查': '变异 1：删除 hello.txt，python3 check.py 退出 1；变异 2：hello.txt 换成目录，退出 1。'})
            review_worktree = state / 'worktrees/demo/T-1-a1-review-1'
            return 'reviewer', [
                ('Bash', dict(command='rm hello.txt; python3 check.py; echo "mutation-1 rc=$?"', description='mutation 1')),
                ('Bash', dict(command='mkdir hello.txt; python3 check.py; echo "mutation-2 rc=$?"', description='mutation 2')),
                ('Write', dict(file_path=f'{review_worktree}/reviewer-note.txt', content='reviewer must not write here\n')),
            ], json.dumps(shape, ensure_ascii=False)
        submit = re.search(r'显式交付：\n(.+)\n', text)
        assert submit, '派发提示里没有交付命令'
        line = submit.group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return 'worker', [
            ('Write', dict(file_path=f'{cwd}/hello.txt', content='hello from the T-122 fixture\n')),
            ('Write', dict(file_path=f'{outside}/escape.txt', content='must not be written\n')),
            ('Bash', dict(command='git add hello.txt', description='stage')),
            ('Bash', dict(command='git commit -q -m "T-122 fixture change"', description='commit')),
            ('Bash', dict(command=line, description='submit')),
        ], '已提交并交付。'

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
            api['models'].add(body.get('model'))
            with (out / 'api.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(body, ensure_ascii=False) + '\n')
            names = {tool.get('name') for tool in body.get('tools', [])}
            action, final = None, 'ok'
            if {'Bash', 'Write'} <= names:
                api['main'] += 1
                messages = body['messages']
                role, steps, final = plan_for(body)
                # The newest user message carries the tool result; a system-role message may follow it.
                last = next((message['content'] for message in reversed(messages) if message['role'] == 'user'), None)
                if isinstance(last, list):
                    for part in last:
                        if isinstance(part, dict) and part.get('type') == 'tool_result':
                            content = part.get('content')
                            text = content if isinstance(content, str) else ' '.join(item.get('text', '') for item in content or [] if isinstance(item, dict))
                            api['results'][role].append(dict(id=part.get('tool_use_id'), is_error=bool(part.get('is_error')), text=text[:600]))
                step = sum(1 for message in messages if message['role'] == 'assistant' and isinstance(message['content'], list)
                           and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in message['content']))
                action = steps[step] if step < len(steps) else None
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()

            def emit(kind, value):
                self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps({'type': kind, **value}) + '\n\n').encode())
                self.wfile.flush()
            emit('message_start', {'message': {'id': f'msg_t122_{api["requests"]}', 'type': 'message', 'role': 'assistant',
                                               'model': body.get('model'), 'content': [], 'stop_reason': None,
                                               'usage': {'input_tokens': 128, 'output_tokens': 0}}})
            if action:
                emit('content_block_start', {'index': 0, 'content_block': {'type': 'tool_use', 'id': f'toolu_t122_{api["main"]}', 'name': action[0], 'input': {}}})
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

    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', ELECTRON_RUN_AS_NODE='1',
               A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'),
               ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}', ANTHROPIC_AUTH_TOKEN=TOKEN,
               GIT_AUTHOR_NAME='t122', GIT_AUTHOR_EMAIL='t122@example.invalid',
               GIT_COMMITTER_NAME='t122', GIT_COMMITTER_EMAIL='t122@example.invalid')
    env.pop('ZDOTDIR', None)
    running = False

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def run_cli(*arguments):
        run = subprocess.run(['node', str(cli), '--state', str(state), *arguments], env=env, capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, f'{arguments[0]}: {run.stderr or run.stdout}'
        return json.loads(run.stdout)

    def request(command, identity=None, **data):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(60)
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

    def wait(label, predicate, timeout=90):
        deadline = time.monotonic() + timeout
        while True:
            value = predicate()
            if value:
                return value
            assert not api['error'], api['error']
            assert time.monotonic() < deadline, f'超时：{label}'
            time.sleep(.2)

    try:
        config = dict(claude_bin=args.claude, role_card=str(source / 'workbench/roles/worker.md'), role_card_revision='t122-fixture',
                      reviewer_role_card=str(source / 'workbench/roles/reviewer.md'), reviewer_role_card_revision='t122-fixture',
                      code_revision='t122-fixture', hook_authorization='T-122 fixture: hooks only through launch arguments', turn_limit=6)
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

        # A project terminal whose CLI the user approved as the executor controller.
        launch = run_cli('shell_start', '--project', 'demo', '--cwd', str(repo))['launch']['id']
        window = request('window_open', operator, launch=launch, project='demo')
        assert window['ok'], window
        # The terminal's token lives only in its own environment: read it from inside, as the T-121 test does.
        sent = request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()),
                       data=f'print -r -- $A2A_TERMINAL_TOKEN > {out}/token.txt\r')
        assert sent['ok'], sent
        wait('终端写出令牌', lambda: (out / 'token.txt').exists() and (out / 'token.txt').read_text().strip(), 30)
        terminal = dict(kind='terminal', launch=launch, token=(out / 'token.txt').read_text().strip())
        asker = socket.socket(socket.AF_UNIX)
        asker.connect(str(state / 'control.sock'))
        asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role='executor', wait_seconds=60),
                                       identity=terminal)) + '\n').encode())
        pending = wait('角色申请出现', lambda: request('sidebar_snapshot').get('role_requests'), 20)
        assert request('role_request_decide', operator, role_request=pending[0]['id'], approved=True)['ok']
        response = b''
        while b'\n' not in response:
            response += asker.recv(65536)
        asker.close()
        granted = json.loads(response.split(b'\n', 1)[0])
        assert request('role_request_confirm', terminal, role_request=granted['role_request']['id'])['ok']

        ready = request('inbox_ready', terminal, project='demo')
        report['inbox_ready'] = {key: ready.get(key) for key in ('ok', 'error')}
        # The controller prepares a card naming Claude Code and dispatches it.
        card = out / 'card.json'
        card.write_text(json.dumps(dict(id='T-1', source=None, goal='在仓库根目录加 hello.txt', non_goals=['不改别的文件'],
            paths=dict(allow=['hello.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
            red_commands=[], task_type='测试', repair_target=None, complexity='S',
            executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
        saved = request('card_save', terminal, task='T-1', card=str(card), expected_version=0)
        assert saved['ok'], saved
        created = request('create', terminal, task='T-1', project='demo', repo=str(repo), branch='refs/heads/main', card_version=1)
        assert created['ok'], created
        dispatched = request('dispatch', terminal, task='T-1', runtimeMode='workspace-write', model='claude-haiku-5-5', effort='low')
        report['dispatch'] = {key: dispatched.get(key) for key in ('ok', 'error')}
        check('dispatch_starts_claude_worker', dispatched.get('ok'), dispatched)
        attempt = dispatched['attempt']
        worker = request('launch_show', operator, launch=attempt['runtime_identity']['launch'])['launch']
        argv = worker['argv']
        settings = json.loads(argv[argv.index('--settings') + 1])
        report['worker'] = dict(cli=worker.get('cli'), argv=argv[:-1], settings=settings, parent_launch=worker.get('parent_launch'))
        flag = lambda name: argv[argv.index(name) + 1] if name in argv else None
        check('worker_launch_is_bounded_claude',
              worker.get('cli') == 'Claude Code' and flag('--permission-mode') == 'dontAsk' and
              flag('--setting-sources') == 'local' and '--strict-mcp-config' in argv and
              flag('--session-id') == worker.get('native_session') and
              settings['sandbox']['enabled'] is True and settings['sandbox']['allowUnsandboxedCommands'] is False, report['worker'])
        check('worker_belongs_to_terminal_controller', worker.get('parent_launch') == launch, worker.get('parent_launch'))

        # 4, 5: the trust screen is answered once, before the session reports ready; then the task goes in.
        worker_launch = worker['id']
        wait('worker 回合开始', lambda: [e for e in events({'turn_start_signal'}) if e['launch'] == worker_launch], 120)
        startup = [e['type'] for e in events({'worker_trust_confirm_intent', 'worker_trust_confirmed', 'native_session_started', 'turn_submitted'})
                   if e['launch'] == worker_launch]
        report['startup'] = startup
        check('trust_answered_before_first_task', startup[:4] == ['worker_trust_confirm_intent', 'worker_trust_confirmed',
                                                                   'native_session_started', 'turn_submitted'], startup)

        # 6, 7: the worker commits and submits; the Stop hook hands the request to the gate.
        def submitted():
            status = request('status', operator, task='T-1')
            return status['task'] if status['task']['state'] not in ('preparing', 'claimed') else None
        task = wait('交付到达门禁', submitted, 180)
        report['task_state'] = task['state']
        report['api'] = dict(requests=api['requests'], main=api['main'], models=sorted(map(str, api['models'])), results=api['results'])
        outside_result = api['results']['worker'][1] if len(api['results']['worker']) > 1 else None
        check('outside_write_refused', not (outside / 'escape.txt').exists() and outside_result and outside_result['is_error'], outside_result)
        commit = task.get('candidate_commit') or task['current_attempt'].get('delivery', {}).get('commit')
        message = subprocess.check_output(['git', '-C', str(repo), 'log', '-1', '--format=%B', commit], text=True)
        trailers = dict(re.findall(r'^A2A-([A-Za-z-]+): (.+)$', message, re.M))
        report['trailers'] = trailers
        check('commit_carries_claude_identity', trailers.get('Native-Session') == worker.get('native_session') and
              trailers.get('Launch') == worker_launch and trailers.get('Effort') == 'low', trailers)
        check('delivery_reached_gate', task['state'] == 'submitted', task['state'])

        # 10, 11: verification starts a fresh read-only Claude reviewer on the worker's model; it
        # passes; the controller scores and integrates into the fixture's working branch.
        verified = request('verify', terminal, task='T-1')
        report['verify'] = {key: verified.get(key) for key in ('ok', 'error')}
        assert verified.get('ok'), verified
        task = wait('审查结束', lambda: (lambda current: current if current['state'] in ('verified', 'submitted', 'rework', 'failed') and
                                          current.get('review', {}).get('state') not in (None, 'requested', 'running') else None)(
                                              request('status', operator, task='T-1')['task']), 240)
        review = task['review']
        reviewer = request('launch_show', operator, launch=review['launch_id'])['launch']
        rargv = reviewer['argv']
        rflag = lambda name: rargv[rargv.index(name) + 1] if name in rargv else None
        rsettings = json.loads(rflag('--settings'))
        report['reviewer'] = dict(cli=reviewer.get('cli'), model=rflag('--model'), effort=rflag('--effort'), settings=rsettings,
                                  results=api['results']['reviewer'], review_state=review['state'], task_state=task['state'])
        check('reviewer_same_cli_and_model', reviewer.get('cli') == 'Claude Code' and rflag('--model') == 'claude-haiku-5-5' and
              rflag('--effort') == 'low' and rflag('--permission-mode') == 'dontAsk' and reviewer['native_session'] != worker['native_session'] and
              rsettings['sandbox']['filesystem'] == {'allowWrite': []}, report['reviewer'])
        review_results = api['results']['reviewer']
        check('reviewer_mutations_ran_in_copy', len(review_results) >= 2 and 'mutation-1 rc=1' in review_results[0]['text'] and
              'mutation-2 rc=1' in review_results[1]['text'], review_results)
        # The review worktree is removed when the reviewer is reclaimed; the denial is the tool result.
        check('reviewer_cannot_write_review_worktree', len(review_results) >= 3 and review_results[2]['is_error'] and
              'denied' in review_results[2]['text'], review_results[2:])
        check('review_passed', review['state'] == 'passed' and task['state'] == 'verified', report['reviewer'])
        score = out / 'score.json'
        score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='只改了 hello.txt',
            engineering_taste=2, engineering_reason='夹具任务', notes='T-122 fixture'), ensure_ascii=False), encoding='utf-8')
        # The daemon reclaims the reviewer after its result, under the task's operation lock.
        wait('审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in request('events', operator, task='T-1')['events']), 60)
        integrated = request('integrate', terminal, task='T-1', score_file=str(score))
        report['integrate'] = {key: integrated.get(key) for key in ('ok', 'error', 'details')}
        main_files = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', '--name-only', 'refs/heads/main'], text=True).split()
        report['main_files'] = main_files
        final = request('status', operator, task='T-1')['task']
        report['final_state'] = final['state']
        check('integrated_into_working_branch', integrated.get('ok') and final['state'] == 'accepted' and 'hello.txt' in main_files and
              subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', commit, 'refs/heads/main']).returncode == 0, report['integrate'])

        # 8: the sidebar places the worker under the terminal controller.
        agents = request('sidebar_snapshot')['agents']
        row = next((agent for agent in agents if agent['id'] == worker_launch), None)
        report['sidebar_worker'] = row and {key: row[key] for key in ('role', 'cli', 'parent', 'state')}
        review_row = next((agent for agent in agents if agent['id'] == review['launch_id']), None)
        report['sidebar_reviewer'] = review_row and {key: review_row[key] for key in ('role', 'cli', 'task', 'parent', 'state')}
        check('sidebar_reviewer_under_task', review_row and review_row['task'] == 'T-1' and review_row['role'] == 'reviewer' and
              review_row['cli'] == 'claude', report['sidebar_reviewer'])
        check('sidebar_worker_under_controller', row and row['parent'] == launch and row['cli'] == 'claude' and row['role'] == 'worker', report['sidebar_worker'])
        # 9: asked before the project has any task; asserted last so a pre-change revision fails at dispatch first.
        check('inbox_ready_for_opened_project', ready.get('error') != 'unknown_project', ready)
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api_snapshot'] = dict(requests=api['requests'], main=api['main'], results=api['results'])
        try:
            report['events_tail'] = [dict(type=e['type'], launch=e['launch']) for e in events()][-40:]
        except BaseException:
            pass
        raise
    finally:
        try:
            if running:
                run_cli('daemon_stop')
        finally:
            server.shutdown()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
