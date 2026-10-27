"""T-193：执行主控的身份绑终端，不由启动目录决定项目；建卡、派发指定项目，只限已打开的项目；额外可写目录由主控每次派发
时指定。真实后台、socket、终端主控、门禁，真实安装的 Claude Code（交互模式，在 node-pty 里），模型换成本地脚本化接口。

失败方式（先列再写）：
1. 在 demo 目录启动并获批的主控，给另一个已打开的项目 other 建卡或派发被拒（修前的 role_project_mismatch）。
2. 派出的 worker 没出现在 other 下（侧栏行的项目不是 other），或者工作区不在 other 的仓库里。
3. 没打开的项目也能建卡；或者被拒却不说明原因。
4. 派发没指定额外目录时，worker 仍拿到项目设置里的额外目录（修前行为）。
5. 指定了额外目录，却没写进启动参数或启动记录；或者能把任务仓库本身当额外目录。
6. 派发后有人把获批目录（或其子目录）换成指向工作台数据目录的链接，之后启动的审查员跟着链接拿到数据目录的写权限
   （T-193 审查 F1）。
--revision 在该版本的隔离源码上跑同一场景（修前应在第 1 条失败）；--mutant 跑已知坏实现。
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
SERVED_MODEL = 'claude-haiku-5-5-t193-served'
MUTANTS = {
    # Before T-193: the project's settings still decide a worker's extra directories.
    'project-extra-dirs': ('src/panes.ts', 'const extraDirectories = monitor ? [] : attempt.extra_directories ?? [];',
                           'const extraDirectories = (this.store.openedProjects().find(project => project.project_id === task.project_id)?.extra_directories ?? []).map(path => realpathSync(path));'),
    # The role's own project again, whatever the command names.
    'home-project-only': ('src/daemon.ts', 'const target = typeof input.project === "string" ? input.project', 'const target = false ? input.project'),
    # The launch follows whatever the recorded path points to now (T-193 review F1).
    'follow-relinked': ('src/panes.ts', 'const extraDirectories = monitor ? [] : attempt.extra_directories ?? [];',
                        'const extraDirectories = monitor ? [] : (attempt.extra_directories ?? []).map(path => realpathSync(path));'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t193-', dir='/private/tmp')).resolve()
    state, home, repo, out = (fixture / name for name in ('state', 'home', 'demo', 'out'))
    for path in (state, home, repo, out):
        path.mkdir()
    (home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark'}), encoding='utf-8')
    source = ROOT
    if args.revision:
        source = fixture / 'source'
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
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    if args.mutant:
        source = fixture / 'source'
        for name in ('src', 'terminal', 'hooks', 'roles'):
            shutil.copytree(ROOT / 'workbench' / name, source / 'workbench' / name, symlinks=True)
        path, old, new = MUTANTS[args.mutant]
        path = source / 'workbench' / path
        text = path.read_text(encoding='utf-8')
        assert text.count(old) == 1, '变异定位必须唯一'
        path.write_text(text.replace(old, new), encoding='utf-8')
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    cli = source / 'workbench/src/gates/cli.ts'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, fixture=str(fixture), claude=args.claude, checks=[])

    # The model answers in words, except T-3's worker, which writes, commits and delivers so that a reviewer is started.
    def worker_steps(body):
        text = json.dumps(body, ensure_ascii=False)
        found = re.search(r'[Ww]orking directory: (/[^\s"\\]+)', text)
        if not found or not found.group(1).endswith('/T-3-a1') or not {'Bash', 'Write'} <= {tool.get('name') for tool in body.get('tools', [])}:
            return []
        first = next(message for message in body['messages'] if message['role'] == 'user')
        first = first['content'] if isinstance(first['content'], str) else '\n'.join(part.get('text', '') for part in first['content'] if isinstance(part, dict))
        submit = re.search(r'显式交付：\n(.+)\n', first)
        if not submit:
            return []
        cwd = found.group(1)
        return [('Write', dict(file_path=f'{cwd}/hello.txt', content='T-3\n')),
                ('Bash', dict(command='git add hello.txt && git commit -q -m "T-3 fixture change"', description='commit')),
                ('Bash', dict(command=submit.group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"'), description='submit'))]

    class Api(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if self.path.split('?', 1)[0] == '/v1/messages/count_tokens':
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(b'{"input_tokens":128}')
                return
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()

            def emit(kind, value):
                self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps({'type': kind, **value}) + '\n\n').encode())
                self.wfile.flush()
            emit('message_start', {'message': {'id': 'msg_t193_' + uuid.uuid4().hex, 'type': 'message', 'role': 'assistant',
                                               'model': SERVED_MODEL, 'content': [], 'stop_reason': None, 'usage': {'input_tokens': 128, 'output_tokens': 0}}})
            steps = worker_steps(body) if self.path.split('?', 1)[0] == '/v1/messages' else []
            step = sum(1 for message in body.get('messages', []) if message['role'] == 'assistant' and isinstance(message['content'], list)
                       and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in message['content']))
            if step < len(steps):
                emit('content_block_start', {'index': 0, 'content_block': {'type': 'tool_use', 'id': 'toolu_t193_' + uuid.uuid4().hex, 'name': steps[step][0], 'input': {}}})
                emit('content_block_delta', {'index': 0, 'delta': {'type': 'input_json_delta', 'partial_json': json.dumps(steps[step][1], ensure_ascii=False)}})
                reason = 'tool_use'
            else:
                emit('content_block_start', {'index': 0, 'content_block': {'type': 'text', 'text': ''}})
                emit('content_block_delta', {'index': 0, 'delta': {'type': 'text_delta', 'text': '收到。'}})
                reason = 'end_turn'
            emit('content_block_stop', {'index': 0})
            emit('message_delta', {'delta': {'stop_reason': reason, 'stop_sequence': None}, 'usage': {'output_tokens': 5}})
            emit('message_stop', {})

    server = ThreadingHTTPServer(('127.0.0.1', 0), Api)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', ELECTRON_RUN_AS_NODE='1',
               A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'),
               ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}', ANTHROPIC_AUTH_TOKEN=TOKEN,
               GIT_AUTHOR_NAME='t193', GIT_AUTHOR_EMAIL='t193@example.invalid',
               GIT_COMMITTER_NAME='t193', GIT_COMMITTER_EMAIL='t193@example.invalid')
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
            connection.settimeout(120)
            connection.connect(str(state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)) + '\n').encode())
            response = b''
            while b'\n' not in response:
                part = connection.recv(65536)
                assert part, 'daemon 在回执前断开'
                response += part
        return json.loads(response.split(b'\n', 1)[0])

    def wait(label, predicate, timeout=90):
        deadline = time.monotonic() + timeout
        while True:
            value = predicate()
            if value:
                return value
            assert time.monotonic() < deadline, f'超时：{label}'
            time.sleep(.2)

    def brief(value):
        return {key: value.get(key) for key in ('ok', 'error', 'details')}

    try:
        config = dict(claude_bin=args.claude, role_card=str(source / 'workbench/roles/worker.md'), role_card_revision='t193-fixture',
                      reviewer_role_card=str(source / 'workbench/roles/reviewer.md'), reviewer_role_card_revision='t193-fixture',
                      code_revision='t193-fixture', hook_authorization='T-193 fixture: hooks only through launch arguments', turn_limit=6)
        (fixture / 'launch-config.json').write_text(json.dumps(config), encoding='utf-8')
        run_cli('daemon_start', '--launch-config', str(fixture / 'launch-config.json'))
        running = True
        wait('后台恢复结束', lambda: request('pane_layout').get('recovering') is False, 10)
        operator = json.loads((fixture / 'operator.json').read_text(encoding='utf-8'))

        other, ghost, shared, settings_dir = (fixture / name for name in ('other', 'ghost', 'shared', 'settings-extra'))
        for path in (shared, settings_dir):
            path.mkdir()
        for path in (repo, other, ghost):
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(path)], check=True, env=env)
            (path / 'README.md').write_text(f'{path.name}\n', encoding='utf-8')
            (path / 'check.py').write_text('import pathlib, sys\nsys.exit(0 if pathlib.Path("hello.txt").is_file() else 1)\n', encoding='utf-8')
            subprocess.run(['git', '-C', str(path), 'add', '.'], check=True, env=env)
            subprocess.run(['git', '-C', str(path), 'commit', '-q', '-m', 'init'], check=True, env=env)
        for path in (repo, other):
            assert request('project_open', operator, repo=str(path))['ok']
        # The user's project setting for other names a directory; a worker gets it only if the controller names it.
        saved = request('project_settings_save', operator, project='other', extra_directories=[str(settings_dir)])
        assert saved.get('ok'), saved

        # The controller's terminal is in demo, approved there.
        launch = run_cli('shell_start', '--project', 'demo', '--cwd', str(repo))['launch']['id']
        window = request('window_open', operator, launch=launch, project='demo')
        assert window['ok'], window
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
        report['role_project'] = granted['role_request'].get('project')

        def card(task, file='hello.txt'):
            path = out / f'{task}.json'
            path.write_text(json.dumps(dict(id=task, source=None, goal=f'在仓库根目录加 {file}', non_goals=['不改别的文件'],
                paths=dict(allow=[file], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
                red_commands=[], task_type='测试', repair_target=None, complexity='S',
                executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
            return str(path)

        # 1, 2: a card and a dispatch in other, from the controller approved in demo.
        saved = request('card_save', terminal, task='T-1', project='other', card=card('T-1'), expected_version=0)
        created = request('create', terminal, task='T-1', project='other', repo=str(other), branch='refs/heads/main', card_version=1)
        dispatched = request('dispatch', terminal, task='other+T-1', runtimeMode='workspace-write')
        report['other'] = dict(card_save=brief(saved), create=brief(created), dispatch=brief(dispatched))
        check('controller_reaches_other_opened_project', saved.get('ok') and created.get('ok') and dispatched.get('ok') and
              created['task']['task_id'] == 'other+T-1', report['other'])
        worker = request('launch_show', operator, launch=dispatched['attempt']['runtime_identity']['launch'])['launch']
        row = wait('worker 出现在侧栏', lambda: next((agent for agent in request('sidebar_snapshot')['agents'] if agent['id'] == worker['id']), None), 30)
        report['worker'] = dict(project=row['project'], task=row['task'], workspace=worker.get('worktree'), extra=worker.get('extra_directories'))
        check('worker_listed_under_other', row['project'] == 'other' and row['task'] == 'other+T-1' and
              str(worker.get('worktree', '')).find('/worktrees/other/') >= 0, report['worker'])

        # 4: no directory named, none given, though other's settings name one.
        add_dirs = [worker['argv'][index + 1] for index, arg in enumerate(worker['argv']) if arg == '--add-dir']
        report['worker']['add_dirs'] = add_dirs
        check('no_extra_directory_unless_named', worker.get('extra_directories') == [] and str(settings_dir) not in add_dirs and
              os.path.realpath(settings_dir) not in add_dirs, report['worker'])

        # 3: a project the workbench has not opened.
        saved = request('card_save', terminal, task='T-9', project='ghost', card=card('T-9'), expected_version=0)
        created = request('create', terminal, task='T-9', project='ghost', repo=str(ghost), branch='refs/heads/main', card_version=1)
        report['ghost'] = dict(card_save=brief(saved), create=brief(created))
        check('unopened_project_refused_with_reason', created.get('error') == 'project_not_opened' and
              (created.get('details') or {}).get('project') == 'ghost' and 'other' in (created.get('details') or {}).get('opened', []) and
              (created.get('details') or {}).get('next'), report['ghost'])

        # 5: named directories reach the launch argv and record; the task's own repository cannot be one.
        request('card_save', terminal, task='T-2', project='other', card=card('T-2', 'second.txt'), expected_version=0)
        assert request('create', terminal, task='T-2', project='other', repo=str(other), branch='refs/heads/main', card_version=1)['ok']
        guarded = request('dispatch', terminal, task='other+T-2', runtimeMode='workspace-write', extra_directories=[str(other)])
        named = request('dispatch', terminal, task='other+T-2', runtimeMode='workspace-write', extra_directories=[str(shared)])
        report['named'] = dict(guarded=brief(guarded), named=brief(named))
        check('task_repository_is_not_an_extra_directory', guarded.get('error') == 'extra_directory_guarded', report['named'])
        assert named.get('ok'), named
        second = request('launch_show', operator, launch=named['attempt']['runtime_identity']['launch'])['launch']
        add_dirs = [second['argv'][index + 1] for index, arg in enumerate(second['argv']) if arg == '--add-dir']
        report['named'].update(extra=second.get('extra_directories'), add_dirs=add_dirs)
        check('named_directory_in_argv_and_record', second.get('extra_directories') == [os.path.realpath(shared)] and
              os.path.realpath(shared) in add_dirs and os.path.realpath(settings_dir) not in add_dirs, report['named'])

        # 6: two approved directories, one inside the other. After T-3's delivery its nested one becomes a link to the
        # workbench's data directory; the reviewer, started from the attempt's record, must not get the data directory.
        outer = fixture / 'shared2'
        (outer / 'nested').mkdir(parents=True)
        request('card_save', terminal, task='T-3', project='other', card=card('T-3'), expected_version=0)
        assert request('create', terminal, task='T-3', project='other', repo=str(other), branch='refs/heads/main', card_version=1)['ok']
        # The fixture's completion condition looks for hello.txt, which T-1 also may write: the overlap is deliberate.
        third = request('dispatch', terminal, task='other+T-3', runtimeMode='workspace-write', extra_directories=[str(outer), str(outer / 'nested')],
                        overlap_reason='T-193 夹具：T-1 的 worker 只回话，不写文件')
        assert third.get('ok'), third
        wait('T-3 交付', lambda: request('status', operator, task='other+T-3')['task']['state'] == 'submitted', 120)
        approved = [os.path.realpath(outer), os.path.realpath(outer / 'nested')]
        (outer / 'nested').rmdir()
        (outer / 'nested').symlink_to(state, target_is_directory=True)
        verified = request('verify', terminal, task='other+T-3')
        time.sleep(5)
        events = request('orchestration_events')['events']
        granted = []
        for launch in sorted({event['launch'] for event in events if event.get('launch')}):
            record = request('launch_show', operator, launch=launch).get('launch') or {}
            if os.path.realpath(state) in (record.get('extra_directories') or []) or os.path.realpath(state) in (record.get('argv') or []):
                granted.append(dict(launch=launch, role=record.get('role'), extra=record.get('extra_directories')))
        report['relinked'] = dict(approved=third['attempt'].get('extra_directories'), verify=brief(verified), granted=granted,
                                  task_state=request('status', operator, task='other+T-3')['task']['state'])
        check('relinked_directory_never_granted', not granted and third['attempt'].get('extra_directories') == approved,
              report['relinked'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
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
