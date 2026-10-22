"""T-123：任务与任务卡按项目区分身份。真实后台、socket、终端、门禁与安装的 Claude Code（交互模式，
在 node-pty 里），模型换成本地脚本化的 Messages 接口，不调用供应商。

失败方式（先列再写）：
1. 第二个项目建不了同名任务（`task_exists`，或草稿归属 `card_draft_not_owned`）。
2. 两个项目的同名任务共用一条记录：卡片版本、事件、交付或评分串到另一个项目；一个集成把另一个的候选并进自己的仓库。
3. 同时在跑的两个同名任务共用操作锁或 run 锁，一个被另一个挡住（`operation_busy`）或误收另一个的交付。
4. 一个项目的终端主控用完整 id 读、改另一个项目的同名任务或卡片，门禁没拒绝，或拒绝没留记录。
5. 管理凭据只写任务名、而任务名在两个项目里重名时，门禁随便挑一个，而不是拒绝。
6. 旧库迁移丢记录：任务、卡片版本、事件条数变了；旧任务没归入原项目；旧任务在迁移后读不出、走不下去。
7. `card_draft_owned` 仍被写入或仍被检查（两套归属并存）。
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
# The parent of T-123: the migration starts from a library this revision wrote.
BEFORE = '4116c8b44'
PROJECTS = ('alpha', 'beta')
# Tables only task commands write: a status read after the migration adds nothing to them.
KEPT = ('tasks', 'task_card_versions', 'task_card_snapshots', 'attempts', 'events', 'runs', 'issue_records', 'launch_records')
TASK = 'T-1-1'
MUTANTS = {
    # Every task lands in one shared namespace again: the project no longer tells two ids apart.
    'global-task-id': ('src/gates/core.ts', 'return `${id(project)}+${id(name)}`;', 'return `shared+${id(name)}`;'),
    # A bare name resolves to the first match instead of being refused as ambiguous.
    'ambiguous-name-picks-first': ('src/gates/core.ts',
                                   'requireGate(matches.length === 1, matches.length ? "task_ambiguous" : "unknown_task", { task: name, projects: matches.map(taskProject) });',
                                   'requireGate(matches.length >= 1, "unknown_task", { task: name });'),
    # T-128: only records interrupted by this restart are registered; after a second restart the old worker is unknown.
    'gone-only-first-restart': ('src/panes.ts', 'if (!this.store.lastEvent(record.id, ["pane_recovered"])) continue;',
                                'if (this.store.lastEvent(record.id, ["pane_recovered"])?.data.daemon !== daemon) continue;'),
    # A full id with a different project is resolved by the id alone.
    'full-id-ignores-project': ('src/gates/core.ts',
                                'requireGate(project === undefined || taskProject(full) === project, "task_project_mismatch", { task: full, project });', ''),
    # The migration leaves the events of old tasks under their old ids.
    'migration-skips-events': ('src/gates/core.ts', 'const plain = columns.filter(column => column === "task" || keyed[table] === column);',
                               'const plain = columns.filter(column => (column === "task" && table !== "events") || keyed[table] === column);'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    # same-name skips the migration (6) so a revision without one still reaches the same-name scenario (1-5).
    parser.add_argument('--scenario', choices=['all', 'same-name'], default='all')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t123-', dir='/private/tmp')).resolve()
    state, home, out = (fixture / name for name in ('state', 'home', 'out'))
    for path in (state, home, out):
        path.mkdir()
    (home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark'}), encoding='utf-8')

    def isolated(revision, target):
        for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision, 'workbench/src', 'workbench/terminal',
                                             'workbench/hooks', 'workbench/roles'], cwd=ROOT, text=True).splitlines():
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            mode = subprocess.check_output(['git', 'ls-tree', revision, name], cwd=ROOT, text=True).split()[0]
            if mode == '120000':
                path.symlink_to(subprocess.check_output(['git', 'show', f'{revision}:{name}'], cwd=ROOT, text=True))
                continue
            path.write_bytes(subprocess.check_output(['git', 'show', f'{revision}:{name}'], cwd=ROOT))
            if mode == '100755':
                path.chmod(0o755)
        (target / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
        return target

    before = isolated(BEFORE, fixture / 'source-before')
    source = ROOT
    if args.revision:
        source = isolated(args.revision, fixture / 'source')
    elif args.mutant:
        source = fixture / 'source'
        for name in ('src', 'terminal', 'hooks', 'roles'):
            shutil.copytree(ROOT / 'workbench' / name, source / 'workbench' / name, symlinks=True)
        path, old, new = MUTANTS[args.mutant]
        path = source / 'workbench' / path
        text = path.read_text(encoding='utf-8')
        assert text.count(old) == 1, '变异定位必须唯一'
        path.write_text(text.replace(old, new), encoding='utf-8')
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, scenario=args.scenario, fixture=str(fixture),
                  claude=args.claude, checks=[])

    # The model: a scripted Messages endpoint. A worker writes a file naming its own project (from its
    # working directory), commits and submits; a reviewer runs two mutations and passes.
    api = dict(requests=0, error=None)

    def plan_for(body):
        found = re.search(r'[Ww]orking directory: (/[^\s"\\]+)', json.dumps(body, ensure_ascii=False))
        assert found, '请求里没有工作目录'
        cwd = found.group(1)
        first = body['messages'][0]['content']
        text = first if isinstance(first, str) else '\n'.join(part.get('text', '') for part in first if isinstance(part, dict))
        if '审查这一次交付' in text:
            shape = json.loads(text[text.rindex('{\n  "schema": 1'):])
            shape.update(verdict='可合并', findings=[], report={'结论': '候选加了 hello.txt，满足任务卡。',
                '完成条件与变异检查': '变异 1：删除 hello.txt，python3 check.py 退出 1；变异 2：hello.txt 换成目录，退出 1。'})
            return [('Bash', dict(command='rm hello.txt; python3 check.py; echo "mutation-1 rc=$?"', description='mutation 1')),
                    ('Bash', dict(command='mkdir hello.txt; python3 check.py; echo "mutation-2 rc=$?"', description='mutation 2'))], \
                json.dumps(shape, ensure_ascii=False)
        # A reviewer works in a copy; a worker in its project's worktree.
        project = next(name for name in PROJECTS + ('legacy',) if f'/worktrees/{name}/' in cwd)
        submit = re.search(r'显式交付：\n(.+)\n', text)
        assert submit, '派发提示里没有交付命令'
        line = submit.group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return [('Write', dict(file_path=f'{cwd}/hello.txt', content=f'hello from {project}\n')),
                ('Bash', dict(command='git add hello.txt', description='stage')),
                ('Bash', dict(command=f'git commit -q -m "{project} change"', description='commit')),
                ('Bash', dict(command=line, description='submit'))], '已提交并交付。'

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
            names = {tool.get('name') for tool in body.get('tools', [])}
            action, final = None, 'ok'
            if {'Bash', 'Write'} <= names:
                steps, final = plan_for(body)
                step = sum(1 for message in body['messages'] if message['role'] == 'assistant' and isinstance(message['content'], list)
                           and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in message['content']))
                action = steps[step] if step < len(steps) else None
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()

            def emit(kind, value):
                self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps({'type': kind, **value}) + '\n\n').encode())
                self.wfile.flush()
            emit('message_start', {'message': {'id': f'msg_t123_{api["requests"]}', 'type': 'message', 'role': 'assistant',
                                               'model': 'claude-haiku-5-5', 'content': [], 'stop_reason': None,
                                               'usage': {'input_tokens': 128, 'output_tokens': 0}}})
            if action:
                emit('content_block_start', {'index': 0, 'content_block': {'type': 'tool_use', 'id': f'toolu_t123_{api["requests"]}', 'name': action[0], 'input': {}}})
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
               GIT_AUTHOR_NAME='t123', GIT_AUTHOR_EMAIL='t123@example.invalid',
               GIT_COMMITTER_NAME='t123', GIT_COMMITTER_EMAIL='t123@example.invalid')
    env.pop('ZDOTDIR', None)
    running = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def run_cli(code, *arguments):
        run = subprocess.run(['node', str(code / 'workbench/src/gates/cli.ts'), '--state', str(state), *arguments], env=env,
                             capture_output=True, text=True, timeout=60)
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

    def wait(label, predicate, timeout=90):
        deadline = time.monotonic() + timeout
        while True:
            value = predicate()
            if value:
                return value
            assert not api['error'], api['error']
            assert time.monotonic() < deadline, f'超时：{label}'
            time.sleep(.2)

    def start(code):
        nonlocal running
        credential = fixture / 'operator.json'
        if credential.exists():
            credential.rename(fixture / f'operator-{uuid.uuid4().hex[:8]}.json')
        config = dict(claude_bin=args.claude, role_card=str(code / 'workbench/roles/worker.md'), role_card_revision='t123-fixture',
                      reviewer_role_card=str(code / 'workbench/roles/reviewer.md'), reviewer_role_card_revision='t123-fixture',
                      code_revision='t123-fixture', hook_authorization='T-123 fixture: hooks only through launch arguments', turn_limit=6)
        (fixture / 'launch-config.json').write_text(json.dumps(config), encoding='utf-8')
        run_cli(code, 'daemon_start', '--launch-config', str(fixture / 'launch-config.json'))
        running = code
        wait('后台恢复结束', lambda: request('pane_layout').get('recovering') is False, 30)
        return json.loads(credential.read_text(encoding='utf-8'))

    def stop():
        nonlocal running
        run_cli(running, 'daemon_stop')
        # The stop returns before the daemon process has exited; it removes its pid file last.
        wait('后台停止', lambda: not (state / 'daemon.pid').exists(), 90)
        running = None

    def make_repo(name):
        repo = fixture / name
        repo.mkdir()
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=env)
        (repo / 'README.md').write_text(f'{name}\n', encoding='utf-8')
        (repo / 'check.py').write_text('import pathlib, sys\nsys.exit(0 if pathlib.Path("hello.txt").is_file() else 1)\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', 'README.md', 'check.py'], check=True, env=env)
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'init'], check=True, env=env)
        return repo

    def card_file(name, goal, task=TASK):
        card = out / f'card-{name}.json'
        card.write_text(json.dumps(dict(id=task, source=None, goal=goal, non_goals=['不改别的文件'],
            paths=dict(allow=['hello.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
            red_commands=[], task_type='测试', repair_target=None, complexity='S',
            executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
        return card

    def controller(operator, project, repo):
        launch = run_cli(source, 'shell_start', '--project', project, '--cwd', str(repo))['launch']['id']
        window = request('window_open', operator, launch=launch, project=project)
        assert window['ok'], window
        token = out / f'token-{project}.txt'
        sent = request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()),
                       data=f'print -r -- $A2A_TERMINAL_TOKEN > {token}\r')
        assert sent['ok'], sent
        wait('终端写出令牌', lambda: token.exists() and token.read_text().strip(), 30)
        terminal = dict(kind='terminal', launch=launch, token=token.read_text().strip())
        asker = socket.socket(socket.AF_UNIX)
        asker.connect(str(state / 'control.sock'))
        asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role='executor', wait_seconds=60),
                                       identity=terminal)) + '\n').encode())
        pending = wait('角色申请出现', lambda: [row for row in request('sidebar_snapshot').get('role_requests', []) if row['launch'] == launch], 20)
        assert request('role_request_decide', operator, role_request=pending[0]['id'], approved=True)['ok']
        response = b''
        while b'\n' not in response:
            response += asker.recv(65536)
        asker.close()
        granted = json.loads(response.split(b'\n', 1)[0])
        assert request('role_request_confirm', terminal, role_request=granted['role_request']['id'])['ok']
        return terminal

    def library():
        # Read only, while no daemon writes: the counts the migration must keep.
        import sqlite3
        # A copy with its WAL: the daemon has stopped, but its last writes may still be in the WAL file.
        copy = Path(tempfile.mkdtemp(dir=fixture))
        for suffix in ('', '-wal', '-shm'):
            if (state / f'state.sqlite3{suffix}').exists():
                shutil.copy(state / f'state.sqlite3{suffix}', copy / f'state.sqlite3{suffix}')
        connection = sqlite3.connect(copy / 'state.sqlite3')
        try:
            counts = {table: connection.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                      for table in ('tasks', 'task_card_versions', 'task_card_snapshots', 'attempts', 'events', 'runs', 'issue_records',
                                    'launch_records', 'orchestration_events')}
            tasks = [(row[0], json.loads(row[1])) for row in connection.execute('SELECT id, data FROM tasks')]
            cards = [row[0] for row in connection.execute('SELECT DISTINCT task FROM task_card_versions')]
            event_tasks = sorted({row[0] for row in connection.execute('SELECT DISTINCT task FROM events')})
            owned = connection.execute("SELECT count(*) FROM orchestration_events WHERE type='card_draft_owned'").fetchone()[0]
        finally:
            connection.close()
        return dict(counts=counts, tasks=tasks, cards=cards, event_tasks=event_tasks, owned=owned)

    try:
        if args.scenario == 'all':
            # 6: a library written by the revision before this ticket: one project, one task with a card, events.
            operator = start(before)
            legacy_repo = make_repo('legacy')
            assert request('project_open', operator, repo=str(legacy_repo))['ok']
            legacy_card = card_file('legacy', '旧库里的任务', 'T-0')
            saved = request('card_save', operator, task='T-0', card=str(legacy_card), expected_version=0)
            assert saved['ok'], saved
            created = request('create', operator, task='T-0', project='legacy', repo=str(legacy_repo), branch='refs/heads/main', card_version=1)
            assert created['ok'], created
            # The old task is dispatched and delivered, so the library holds an attempt, a launch and its events.
            dispatched = request('dispatch', operator, task='T-0', runtimeMode='workspace-write')
            assert dispatched['ok'], dispatched
            wait('旧任务交付', lambda: request('status', operator, task='T-0')['task']['state'] == 'submitted', 240)
            stop()
            old = library()
            report['before_migration'] = old

            operator = start(source)
            status = request('status', operator, task='T-0')
            report['legacy_status'] = {key: status.get(key) for key in ('ok', 'error')} | ({'task_id': status['task']['task_id'], 'project': status['task']['project_id']}
                                                                                           if status.get('ok') else {})
            check('legacy_task_readable_by_name', status.get('ok') and status['task']['project_id'] == 'legacy', report['legacy_status'])
            stop()
            new = library()
            report['after_migration'] = new
            check('migration_keeps_counts', all(new['counts'][table] >= old['counts'][table] for table in old['counts']) and
                  {table: new['counts'][table] for table in KEPT} == {table: old['counts'][table] for table in KEPT},
                  dict(before=old['counts'], after=new['counts']))
            check('legacy_task_in_its_project', [row[0] for row in new['tasks']] == ['legacy+T-0'] and new['cards'] == ['legacy+T-0'] and
                  new['event_tasks'] == ['legacy+T-0'] and new['tasks'][0][1]['project_id'] == 'legacy', new)
            operator = start(source)
            # The old attempt's worker went with the old daemon: the migrated attempt is reclaimed through the gate
            # (its launch record, pane and events under the new id), then the task is dispatched and delivered again.
            reclaimed = request('reclaim', operator, task='legacy+T-0')
            report['legacy_reclaim'] = {key: reclaimed.get(key) for key in ('ok', 'error', 'details')}
            check('migrated_attempt_reclaimed', reclaimed.get('ok'), report['legacy_reclaim'])
            dispatched = request('dispatch', operator, task='legacy+T-0', runtimeMode='workspace-write')
            assert dispatched.get('ok'), dispatched
            wait('旧任务再次交付', lambda: request('status', operator, task='legacy+T-0')['task']['state'] == 'submitted', 240)
            verified = request('verify', operator, task='legacy+T-0')
            assert verified.get('ok'), verified
            wait('旧任务审查通过', lambda: request('status', operator, task='legacy+T-0')['task']['state'] == 'verified' and
                 any(e['type'] == 'review_reclaimed' for e in request('events', operator, task='legacy+T-0')['events']), 300)
            score = out / 'score-legacy.json'
            score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='只改了 hello.txt',
                engineering_taste=2, engineering_reason='夹具任务', notes='T-123 legacy'), ensure_ascii=False), encoding='utf-8')
            integrated = request('integrate', operator, task='legacy+T-0', score_file=str(score))
            legacy_content = subprocess.run(['git', '-C', str(legacy_repo), 'show', 'refs/heads/main:hello.txt'], capture_output=True, text=True).stdout
            report['legacy_integrate'] = dict(result={key: integrated.get(key) for key in ('ok', 'error', 'details')}, content=legacy_content)
            check('migrated_task_continues_to_integration', integrated.get('ok') and legacy_content == 'hello from legacy\n', report['legacy_integrate'])
            reclaimed = request('reclaim', operator, task='legacy+T-0')
            assert reclaimed.get('ok'), reclaimed
            stop()

        # 1-3: two projects, one task name.
        operator = start(source)
        repos = {name: make_repo(name) for name in PROJECTS}
        for name in PROJECTS:
            assert request('project_open', operator, repo=str(repos[name]))['ok']
        terminals = {name: controller(operator, name, repos[name]) for name in PROJECTS}
        created = {}
        for name in PROJECTS:
            saved = request('card_save', terminals[name], task=TASK, card=str(card_file(name, f'{name} 加 hello.txt')), expected_version=0)
            created[name] = request('create', terminals[name], task=TASK, project=name, repo=str(repos[name]), branch='refs/heads/main', card_version=1) \
                if saved.get('ok') else saved
        report['create'] = {name: {key: value.get(key) for key in ('ok', 'error')} for name, value in created.items()}
        check('same_name_created_in_both_projects', all(value.get('ok') for value in created.values()), report['create'])
        keys = {name: created[name]['task']['task_id'] for name in PROJECTS}
        report['keys'] = keys
        check('task_ids_carry_project', keys == {name: f'{name}+{TASK}' for name in PROJECTS} and
              all(created[name]['task']['name'] == TASK and created[name]['task']['project_id'] == name for name in PROJECTS), report['keys'])
        cards = {name: request('card_show', terminals[name], task=TASK, card_version=1) for name in PROJECTS}
        check('each_terminal_reads_its_own_card', all(cards[name].get('ok') and cards[name]['card']['goal'] == f'{name} 加 hello.txt'
                                                      for name in PROJECTS), {name: cards[name].get('card', cards[name]) for name in PROJECTS})
        # 4, 5: refusals while both tasks exist.
        crossed = {
            'status': request('status', terminals['alpha'], task=keys['beta']),
            'card_save': request('card_save', terminals['alpha'], task=keys['beta'], card=str(card_file('crossed', 'alpha 改 beta 的卡')), expected_version=1),
            'card_show': request('card_show', terminals['alpha'], task=keys['beta'], card_version=1),
            'new_draft': request('card_save', terminals['alpha'], task='beta+T-9', card=str(card_file('draft', 'alpha 在 beta 起草', 'T-9')), expected_version=0),
        }
        report['crossed'] = {command: {key: value.get(key) for key in ('ok', 'error')} for command, value in crossed.items()}
        # The gate's refusal is recorded as a failed request_result; its request_received names the terminal it came from.
        events = request('orchestration_events')['events']
        sources = {row['data']['id']: row['data'].get('source') for row in events if row['type'] == 'request_received'}
        rejected = [row for row in events if row['type'] == 'request_result' and row['data'].get('ok') is False
                    and row['data'].get('error') == 'task_project_mismatch'
                    and sources.get(row['data']['id']) == f"terminal:{terminals['alpha']['launch']}"]
        check('other_project_refused_and_recorded', all(not value.get('ok') and value.get('error') == 'task_project_mismatch' for value in crossed.values()) and
              len(rejected) >= len(crossed), dict(crossed=report['crossed'], recorded=len(rejected)))
        beta_card = request('card_show', operator, task=keys['beta'], card_version=1)
        check('other_card_unchanged', beta_card.get('ok') and beta_card['card']['goal'] == 'beta 加 hello.txt', beta_card.get('card'))
        ambiguous = request('status', operator, task=TASK)
        report['ambiguous'] = {key: ambiguous.get(key) for key in ('ok', 'error', 'details')}
        check('bare_name_ambiguous_for_operator', not ambiguous.get('ok') and ambiguous.get('error') == 'task_ambiguous', report['ambiguous'])
        # A full id with a different project beside it is refused, not resolved by either.
        contradicted = request('card_save', operator, task='alpha+T-8', project='beta', card=str(card_file('contradicted', '矛盾', 'T-8')), expected_version=0)
        report['contradicted'] = {key: contradicted.get(key) for key in ('ok', 'error')}
        check('full_id_with_other_project_refused', not contradicted.get('ok') and contradicted.get('error') == 'task_project_mismatch' and
              request('card_show', operator, task='alpha+T-8', card_version=1).get('ok') is not True and
              request('card_show', operator, task='beta+T-8', card_version=1).get('ok') is not True, report['contradicted'])

        # The daemon runs one worker at a time (single_worker_slice), so the two tasks go through in turn; each worker
        # is reclaimed after its task integrates. Both terminals name the task by its bare name.
        def delivered(name):
            current = request('status', terminals[name], task=TASK)['task']
            return current if current['state'] not in ('preparing', 'claimed') else None
        def reviewed(name):
            current = request('status', terminals[name], task=TASK)['task']
            return current if current['state'] == 'verified' and any(e['type'] == 'review_reclaimed'
                                                                     for e in request('events', terminals[name], task=TASK)['events']) else None
        tasks, trailers, integrated, rows = {}, {}, {}, {}
        for name in PROJECTS:
            dispatched = request('dispatch', terminals[name], task=TASK, runtimeMode='workspace-write')
            assert dispatched.get('ok'), (name, dispatched)
            tasks[name] = wait(f'{name} 交付', lambda name=name: delivered(name), 240)
            rows[name] = sorted((row.get('project'), row.get('task'), row.get('task_name'))
                                for row in request('sidebar_snapshot')['agents'] if row.get('role') == 'worker' and row.get('state') != 'ended')
            if tasks[name]['state'] != 'submitted':
                break
            commit = tasks[name]['current_attempt']['delivery']['commit']
            trailers[name] = dict(re.findall(r'^A2A-([A-Za-z-]+): (.+)$', subprocess.check_output(
                ['git', '-C', str(repos[name]), 'log', '-1', '--format=%B', commit], text=True), re.M))
            verified = request('verify', terminals[name], task=TASK)
            assert verified.get('ok'), (name, verified)
            wait(f'{name} 审查通过', lambda name=name: reviewed(name), 300)
            score = out / f'score-{name}.json'
            score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='只改了 hello.txt',
                engineering_taste=2, engineering_reason='夹具任务', notes=f'T-123 {name}'), ensure_ascii=False), encoding='utf-8')
            integrated[name] = request('integrate', terminals[name], task=TASK, score_file=str(score))
            reclaimed = request('reclaim', operator, task=keys[name])
            assert reclaimed.get('ok'), (name, reclaimed)
        report['delivered'] = {name: task['state'] for name, task in tasks.items()}
        check('both_delivered', all(tasks.get(name, {}).get('state') == 'submitted' for name in PROJECTS), report['delivered'])
        report['trailers'] = trailers
        check('trailers_name_project_task', all(trailers[name].get('Task') == keys[name] for name in PROJECTS), trailers)
        report['integrate'] = {name: {key: value.get(key) for key in ('ok', 'error')} for name, value in integrated.items()}
        contents = {name: subprocess.run(['git', '-C', str(repos[name]), 'show', 'refs/heads/main:hello.txt'], capture_output=True, text=True).stdout
                    for name in PROJECTS}
        report['contents'] = contents
        check('each_integrated_into_its_own_repo', all(integrated[name].get('ok') and contents[name] == f'hello from {name}\n' for name in PROJECTS),
              dict(integrate=report['integrate'], contents=contents))
        finals = {name: request('status', terminals[name], task=TASK)['task'] for name in PROJECTS}
        commits = {name: tasks[name]['current_attempt']['delivery']['commit'] for name in PROJECTS}
        check('two_independent_records', all(finals[name]['state'] == 'accepted' and finals[name]['task_id'] == keys[name] and
                                             finals[name]['current_attempt']['delivery']['commit'] == commits[name] for name in PROJECTS) and
              commits['alpha'] != commits['beta'], {name: finals[name]['state'] for name in PROJECTS})
        report['sidebar_workers'] = rows
        check('sidebar_names_task_per_project', all(rows[name] == [(name, keys[name], TASK)] for name in PROJECTS), rows)
        stop()
        final = library()
        report['final_library'] = dict(counts=final['counts'], tasks=sorted(row[0] for row in final['tasks']), owned=final['owned'])
        check('no_draft_ownership_records', final['owned'] == 0, final['owned'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        try:
            if running:
                stop()
        finally:
            server.shutdown()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
