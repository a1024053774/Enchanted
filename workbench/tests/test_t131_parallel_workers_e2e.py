"""T-131：同一项目两个 worker 同时运行，各自交付、审查、打分、集成。真实后台、socket、终端主控、门禁，
真实安装的 Claude Code（交互模式，在 node-pty 里），模型换成本地脚本化的 Messages 接口，不调用供应商。

失败方式（先列再写）：
1. 第一个 worker 还在跑时，第二次派发被后台拒绝（S1 的 `single_worker_slice`）。
2. 两个 worker 并不真正同时运行：接口在两边都发出第一次请求之前，不给任何一边下发工具调用（屏障），
   做不到同时就超时。
3. 两个 worker 串了：提交尾注、交付记录的启动记录、worktree 或文件落到对方任务上。
4. 路径相交的第三张卡不给理由也能派发（门禁的交集规则被绕过）。
5. 两份审查同时进行时互相干扰，或者审查结论落到另一个任务上。
6. 第二个任务集成时工作分支已被第一个推进，门禁没有在新头上重新验收就推进，或者直接失败。
8. 一个任务的审查进行时，另一个任务新建了自己的验收引用、或经门禁集成推进了工作分支，审查结束时的引用核对
   把它当成审查员改了仓库（`review_shared_refs_changed`）；反过来，不是门禁写的引用出现时（--foreign-ref plain），
   或者在别的任务命名空间下出现门禁不会起的名字时（--foreign-ref other-task），照样拒绝；另一个任务验收冲突时门禁
   保留的 `…/v<K>-candidate`、`…/v<K>-base` 引用（--retained-ref，用 update-ref 按门禁的命名写入，不是真造冲突）照样放行。
7. 侧栏里两个 worker 没有都挂在派发它们的终端主控下。
--revision 在该版本的隔离源码上跑同一场景（修前应在第二次派发失败）；--mutant 跑已知坏实现。
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
SERVED_MODEL = 'claude-haiku-5-5-t131-served'
TASKS = {'T-1': 'a.txt', 'T-2': 'b.txt'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['strict-ref-equality', 'integration-chain-ignored', 'any-ref-accepted', 'other-namespace-prefix-only'])
    # A ref no gate operation wrote appears while T-2's review runs: the review boundary must refuse it.
    # other-task: a name under another task's attempt namespace that the gate never gives (review 01 P2).
    parser.add_argument('--foreign-ref', choices=['plain', 'other-task'])
    parser.add_argument('--retained-ref', action='store_true')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t131-', dir='/private/tmp')).resolve()
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
        path, old, new = {
            # The review boundary before T-131: any ref change since the review started is refused.
            'strict-ref-equality': ('src/gates/core.ts', 'requireGate(this.reviewRefsUnchanged(task, review, refs),', 'requireGate(refs === review.shared_refs,'),
            'integration-chain-ignored': ('src/gates/core.ts', 'intent.G === head) head = intent.M;', 'intent.G === head) head = head;'),
            'any-ref-accepted': ('src/gates/core.ts', 'requireGate(this.reviewRefsUnchanged(task, review, refs),', 'requireGate(true,'),
            # Candidate 1: any ref under another task's namespace was accepted.
            'other-namespace-prefix-only': ('src/gates/core.ts', 'return fence !== null && fence >= 1 && fence <= other.fence;',
                                            "return fence !== null || ref.startsWith(`refs/a2a/attempts/${other.task_id}/`);"),
        }[args.mutant]
        path = source / 'workbench' / path
        text = path.read_text(encoding='utf-8')
        assert text.count(old) == 1, '变异定位必须唯一'
        path.write_text(text.replace(old, new), encoding='utf-8')
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    cli = source / 'workbench/src/gates/cli.ts'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, foreign_ref=args.foreign_ref, retained_ref=args.retained_ref, fixture=str(fixture), claude=args.claude,
                  real_model_turns=0, checks=[])

    # The model: a scripted Messages endpoint. Main-loop conversations are told apart by their working
    # directory (each worker's worktree) or the review prompt. No worker gets a tool call before both
    # workers have sent their first request: the barrier proves the two run at the same time.
    api = dict(requests=0, main=0, results={}, first_request={}, error=None)
    lock = threading.Lock()
    both_started = threading.Event()
    release_t2_review = threading.Event()

    def plan_for(body):
        found = re.search(r'[Ww]orking directory: (/[^\s"\\]+)', json.dumps(body, ensure_ascii=False))
        assert found, '请求里没有工作目录'
        cwd = found.group(1)
        first = body['messages'][0]['content']
        text = first if isinstance(first, str) else '\n'.join(part.get('text', '') for part in first if isinstance(part, dict))
        if '审查这一次交付' in text:
            shape = json.loads(text[text.rindex('{\n  "schema": 1'):])
            # The reviewer runs in a one-time copy; the prompt names the task under review.
            named = {name for name in TASKS if f'demo+{name}' in text}
            assert len(named) == 1, f'审查提示里的任务不唯一：{named}'
            task = named.pop()
            shape.update(verdict='可合并', findings=[], report={'结论': f'候选只加了 {TASKS[task]}，满足任务卡。',
                '完成条件与变异检查': f'变异：删除 {TASKS[task]}，完成条件退出 1。'})
            return 'reviewer:' + task, [
                ('Bash', dict(command=f'rm {TASKS[task]}; python3 check_{task}.py; echo "mutation rc=$?"', description='mutation')),
            ], json.dumps(shape, ensure_ascii=False)
        task = next(name for name in TASKS if cwd.endswith(f'/{name}-a1'))
        submit = re.search(r'显式交付：\n(.+)\n', text)
        assert submit, '派发提示里没有交付命令'
        line = submit.group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return 'worker:' + task, [
            ('Write', dict(file_path=f'{cwd}/{TASKS[task]}', content=f'written by the {task} worker\n')),
            ('Bash', dict(command=f'git add {TASKS[task]}', description='stage')),
            ('Bash', dict(command=f'git commit -q -m "{task} fixture change"', description='commit')),
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
            names = {tool.get('name') for tool in body.get('tools', [])}
            action, final = None, 'ok'
            with lock:
                api['requests'] += 1
                number = api['requests']
            if {'Bash', 'Write'} <= names:
                role, steps, final = plan_for(body)
                with lock:
                    api['main'] += 1
                    api['first_request'].setdefault(role, time.time())
                    if sum(1 for key in api['first_request'] if key.startswith('worker:')) == len(TASKS):
                        both_started.set()
                if role.startswith('worker:') and not both_started.wait(120):
                    api['error'] = f'{role}: the other worker never sent a request (not running at the same time)'
                messages = body['messages']
                last = next((message['content'] for message in reversed(messages) if message['role'] == 'user'), None)
                if isinstance(last, list):
                    for part in last:
                        if isinstance(part, dict) and part.get('type') == 'tool_result':
                            content = part.get('content')
                            text = content if isinstance(content, str) else ' '.join(item.get('text', '') for item in content or [] if isinstance(item, dict))
                            with lock:
                                api['results'].setdefault(role, []).append(dict(is_error=bool(part.get('is_error')), text=text[:2000]))
                step = sum(1 for message in messages if message['role'] == 'assistant' and isinstance(message['content'], list)
                           and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in message['content']))
                action = steps[step] if step < len(steps) else None
                if role == 'reviewer:T-2' and action is None and not release_t2_review.wait(240):
                    api['error'] = 'T-2 review verdict was never released'
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()

            def emit(kind, value):
                self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps({'type': kind, **value}) + '\n\n').encode())
                self.wfile.flush()
            emit('message_start', {'message': {'id': f'msg_t131_{number}', 'type': 'message', 'role': 'assistant',
                                               'model': SERVED_MODEL, 'content': [], 'stop_reason': None,
                                               'usage': {'input_tokens': 128, 'output_tokens': 0}}})
            if action:
                emit('content_block_start', {'index': 0, 'content_block': {'type': 'tool_use', 'id': f'toolu_t131_{number}', 'name': action[0], 'input': {}}})
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
               GIT_AUTHOR_NAME='t131', GIT_AUTHOR_EMAIL='t131@example.invalid',
               GIT_COMMITTER_NAME='t131', GIT_COMMITTER_EMAIL='t131@example.invalid')
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

    def git(*arguments):
        return subprocess.check_output(['git', '-C', str(repo), *arguments], text=True).strip()

    try:
        config = dict(claude_bin=args.claude, role_card=str(source / 'workbench/roles/worker.md'), role_card_revision='t131-fixture',
                      reviewer_role_card=str(source / 'workbench/roles/reviewer.md'), reviewer_role_card_revision='t131-fixture',
                      code_revision='t131-fixture', hook_authorization='T-131 fixture: hooks only through launch arguments', turn_limit=6)
        (fixture / 'launch-config.json').write_text(json.dumps(config), encoding='utf-8')
        run_cli('daemon_start', '--launch-config', str(fixture / 'launch-config.json'))
        running = True
        wait('后台恢复结束', lambda: request('pane_layout').get('recovering') is False, 10)
        operator = json.loads((fixture / 'operator.json').read_text(encoding='utf-8'))

        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=env)
        (repo / 'README.md').write_text('demo\n', encoding='utf-8')
        for task, name in TASKS.items():
            (repo / f'check_{task}.py').write_text(f'import pathlib, sys\nsys.exit(0 if pathlib.Path("{name}").is_file() else 1)\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True, env=env)
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'init'], check=True, env=env)
        main_before = git('rev-parse', 'refs/heads/main')
        assert request('project_open', operator, repo=str(repo))['ok']

        # A project terminal whose CLI the user approved as the executor controller (as in T-122).
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

        def card(task, allow, oracle):
            path = out / f'{task}.json'
            path.write_text(json.dumps(dict(id=task, source=None, goal=f'在仓库根目录加 {allow}', non_goals=['不改别的文件'],
                paths=dict(allow=[allow], deny=[]), oracle_paths=[oracle], completion_conditions=[dict(argv=['python3', oracle])],
                red_commands=[], task_type='测试', repair_target=None, complexity='S',
                executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
            saved = request('card_save', terminal, task=task, card=str(path), expected_version=0)
            assert saved['ok'], saved
            created = request('create', terminal, task=task, project='demo', repo=str(repo), branch='refs/heads/main', card_version=1)
            assert created['ok'], created

        # 1: the second dispatch while the first worker is still running.
        attempts, workers = {}, {}
        for task, name in TASKS.items():
            card(task, name, f'check_{task}.py')
            dispatched = request('dispatch', terminal, task=task, runtimeMode='workspace-write')
            report.setdefault('dispatch', {})[task] = {key: dispatched.get(key) for key in ('ok', 'error')}
            check(f'dispatch_{task}_starts_worker', dispatched.get('ok'), dispatched)
            attempts[task] = dispatched['attempt']
            workers[task] = request('launch_show', operator, launch=attempts[task]['runtime_identity']['launch'])['launch']

        # 4: a third card whose allowed paths meet T-1's, without a reason.
        card('T-3', TASKS['T-1'], 'check_T-1.py')
        overlap = request('dispatch', terminal, task='T-3', runtimeMode='workspace-write')
        report['overlap_dispatch'] = {key: overlap.get(key) for key in ('ok', 'error', 'details')}
        check('overlapping_card_refused_without_reason', not overlap.get('ok') and overlap.get('error') == 'path_overlap', report['overlap_dispatch'])

        # 2: the barrier opened, so both workers were running at once.
        wait('两个 worker 都发出请求', both_started.is_set, 180)
        report['first_request'] = {key: round(value, 3) for key, value in api['first_request'].items()}
        check('both_workers_ran_at_once', both_started.is_set(), report['first_request'])

        # 3: each delivery reaches the gate bound to its own launch, worktree and file.
        def submitted(task):
            status = request('status', operator, task=task)['task']
            return status if status['state'] not in ('preparing', 'claimed') else None
        delivered = {task: wait(f'{task} 交付到达门禁', lambda task=task: submitted(task), 180) for task in TASKS}
        report['deliveries'] = {}
        for task, name in TASKS.items():
            current = delivered[task]
            commit = current['candidate_commit']
            files = git('diff', '--name-only', f'{main_before}..{commit}').split()
            trailers = dict(re.findall(r'^A2A-([A-Za-z-]+): (.+)$', git('log', '-1', '--format=%B', commit), re.M))
            delivery = current['current_attempt'].get('delivery') or {}
            report['deliveries'][task] = dict(state=current['state'], files=files, trailers=trailers,
                                              workspace=current['current_attempt']['workspace'], delivery_model=delivery.get('model'))
            check(f'{task}_delivery_is_its_own', current['state'] == 'submitted' and files == [name] and
                  trailers.get('Task') == f'demo+{task}' and trailers.get('Launch') == workers[task]['id'] and
                  trailers.get('Native-Session') == workers[task]['native_session'] and trailers.get('Model') == SERVED_MODEL and
                  current['current_attempt']['workspace'].endswith(f'/{task}-a1'), report['deliveries'][task])

        # 5, 6: both reviews start; T-2's reviewer holds its verdict until T-1 is integrated, so T-2's review
        # sees another task's verification ref appear and the working branch move while it runs.
        for task in TASKS:
            verified = request('verify', terminal, task=task)
            report.setdefault('verify', {})[task] = {key: verified.get(key) for key in ('ok', 'error')}
            assert verified.get('ok'), verified

        def review_settled(task):
            failed = [row['data'] for row in events(['stop_transfer_failed'])]
            assert not failed, f'stop_transfer_failed: {failed}'
            current = request('status', operator, task=task)['task']
            return current if current['state'] in ('verified', 'submitted', 'rework', 'failed', 'paused') and \
                current.get('review', {}).get('state') not in (None, 'requested', 'running') else None

        def reclaimed(task):
            return any(e['type'] == 'review_reclaimed' for e in request('events', operator, task=task)['events'])

        def integrate(task):
            score = out / f'score-{task}.json'
            score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason=f'只改了 {TASKS[task]}',
                engineering_taste=2, engineering_reason='夹具任务', notes='T-131 fixture'), ensure_ascii=False), encoding='utf-8')
            integrated = request('integrate', terminal, task=task, score_file=str(score))
            report.setdefault('integrate', {})[task] = {key: integrated.get(key) for key in ('ok', 'error', 'details')}
            return integrated

        reviewed = {'T-1': wait('T-1 审查结束', lambda: review_settled('T-1'), 240)}
        wait('T-1 审查会话回收', lambda: reclaimed('T-1'), 60)
        check('t2_review_still_running_when_t1_integrates', 'reviewer:T-2' in api['first_request'] and not release_t2_review.is_set() and
              request('status', operator, task='T-2')['task']['state'] == 'reviewing', api['first_request'])
        assert integrate('T-1').get('ok'), report['integrate']
        t1_head = git('rev-parse', 'refs/heads/main')
        if args.foreign_ref:
            # A ref no gate operation wrote, appearing while T-2's review runs.
            ref = 'refs/heads/foreign' if args.foreign_ref == 'plain' else 'refs/a2a/attempts/demo+T-1/rogue'
            subprocess.run(['git', '-C', str(repo), 'update-ref', ref, main_before], check=True, env=env)
        if args.retained_ref:
            # The names the gate retains a conflicted verification under (core.ts verification_conflict), for T-1's attempt 1.
            for suffix in ('candidate', 'base'):
                subprocess.run(['git', '-C', str(repo), 'update-ref', f'refs/a2a/verifications/demo+T-1/a1/v1-{suffix}', main_before], check=True, env=env)
        release_t2_review.set()
        reviewed['T-2'] = wait('T-2 审查结束', lambda: review_settled('T-2'), 240)
        report['reviews'] = {task: dict(task_state=value['state'], review=value['review']['state'], launch=value['review']['launch_id'],
                                        mutation=(api['results'].get('reviewer:' + task) or [{}])[0].get('text'))
                             for task, value in reviewed.items()}
        if args.foreign_ref:
            failed = [e['details'] for e in request('events', operator, task='T-2')['events'] if e['type'] == 'review_lifecycle_failed']
            report['review_lifecycle_failed'] = [dict(phase=item.get('phase'), error=(item.get('details') or {}).get('error')) for item in failed]
            check('foreign_ref_during_review_refused', report['review_lifecycle_failed'] == [dict(phase='reclaim', error='review_shared_refs_changed')] and
                  reviewed['T-2']['state'] == 'paused', report['review_lifecycle_failed'])
            report['status'] = 'PASS'
            return
        check('both_reviews_passed_on_their_own_task', all(value['state'] == 'verified' and value['review']['state'] == 'passed' and
              'mutation rc=1' in (api['results'].get('reviewer:' + task) or [{}])[0].get('text', '') for task, value in reviewed.items()) and
              reviewed['T-1']['review']['launch_id'] != reviewed['T-2']['review']['launch_id'], report['reviews'])

        # T-2 was verified on the old head, so the gate re-verifies it on the new one before advancing.
        wait('T-2 审查会话回收', lambda: reclaimed('T-2'), 60)
        integrate('T-2')
        revalidated = [e['details'] for e in request('events', operator, task='T-2')['events'] if e['type'] == 'integration_compare_failed']
        main_files = git('ls-tree', '--name-only', 'refs/heads/main').split()
        finals = {task: request('status', operator, task=task)['task']['state'] for task in TASKS}
        report['main_files'], report['finals'] = main_files, finals
        report['revalidated'] = [dict(expected=item.get('expected'), actual=item.get('actual')) for item in revalidated]
        check('second_integration_reverified_on_new_head', all(value.get('ok') for value in report['integrate'].values()) and
              finals == {'T-1': 'accepted', 'T-2': 'accepted'} and {'a.txt', 'b.txt'} <= set(main_files) and
              len(revalidated) == 1 and revalidated[0].get('actual') == t1_head and
              all(subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', delivered[task]['candidate_commit'], 'refs/heads/main']).returncode == 0
                  for task in TASKS), dict(integrate=report['integrate'], finals=finals, revalidated=report['revalidated']))

        # 7: both workers sit under the terminal controller in the sidebar.
        agents = request('sidebar_snapshot')['agents']
        rows = {task: next((agent for agent in agents if agent['id'] == workers[task]['id']), None) for task in TASKS}
        report['sidebar'] = {task: row and {key: row[key] for key in ('role', 'cli', 'parent', 'task')} for task, row in rows.items()}
        check('sidebar_both_workers_under_controller', all(row and row['parent'] == launch and row['role'] == 'worker' and row['task'] == f'demo+{task}'
                                                           for task, row in rows.items()), report['sidebar'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api_snapshot'] = dict(requests=api['requests'], main=api['main'], first_request=api['first_request'], results=api['results'])
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
