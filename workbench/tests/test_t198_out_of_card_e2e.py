"""T-198：交付改了任务卡以外的文件，交主控判断，不再直接以 path_boundary_failed 结束验收。真实后台、socket、
终端主控、门禁，真实安装的 Claude Code（交互模式，在 node-pty 里），模型换成本地脚本化的 Messages 接口（与 T-131 同一做法）。

失败方式（先列再写）：
1. 卡外改动仍让验收直接失败（修前行为），或者反过来被静默放行、不留待判断的清单。
2. 主控还没判断就能集成；空白理由被当成理由；放行理由没进事件。
3. 放行后集成没有经过原有检查（审查、打分），或者放行记在别的候选上也算数。
4. 主控打回时 worker 收不到卡外清单，任务也没回到可修订的状态。
7. 主控先放行、后打回，worker 再交新候选、又被打回后交回最初那个提交：旧的放行仍算数，未经判断就能集成（T-198 审查 P1）。
5. 卡外改动碰到验收文件（oracle_paths）时被当成“待判断”放过，而不是照旧硬拒。
6. 审查员的输入里没有卡外清单。
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
from scripted_claude import review_steps  # T-203: a scripted reviewer hands in its result through review_submit

ROOT = Path(__file__).resolve().parents[2]
TOKEN = 'a2a-fixture-key-not-a-secret'
SERVED_MODEL = 'claude-haiku-5-5-t198-served'
# The controller's two rejections of T-2; the T-2 worker acts on each when it arrives.
REJECT_FIRST, REJECT_SECOND = 'notes/ 不在这次范围，删掉再交', 'notes/extra-2.txt 还在，仍不在这次范围'
# task: (file the card allows, extra file outside the card). T-3's extra file is its own oracle.
TASKS = {'T-1': ('a.txt', 'notes/extra-1.txt'), 'T-2': ('b.txt', 'notes/extra-2.txt'), 'T-3': ('c.txt', 'check_T-3.py')}
MUTANTS = {
    # Before T-198: the paths check ended the verification.
    'boundary-still-fails': ('src/gates/core.ts', 'const outOfCard = [...paths].filter((path) => !pathAllowed(card, path));',
                             'const outOfCard = [...paths].filter((path) => !pathAllowed(card, path)); requireGate(outOfCard.length === 0, "path_boundary_failed", { forbidden: outOfCard });'),
    # Integration does not wait for the controller's judgement.
    'integrate-unjudged': ('src/gates/core.ts', 'requireGate(this.outOfCardJudged(task, v), "out_of_card_unjudged",', 'requireGate(true, "out_of_card_unjudged",'),
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
    fixture = Path(tempfile.mkdtemp(prefix='t198-', dir='/private/tmp')).resolve()
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

    # The model: workers write their allowed file and one more; reviewers pass. Every user text a role receives is kept,
    # so the reviewer's prompt and a worker's feedback can be read back.
    api = dict(requests=0, received={}, error=None)
    lock = threading.Lock()

    def user_texts(body):
        texts = []
        for message in body['messages']:
            if message['role'] != 'user':
                continue
            content = message['content']
            texts.append(content if isinstance(content, str) else '\n'.join(part.get('text', '') for part in content
                                                                             if isinstance(part, dict) and part.get('type') == 'text'))
        return [text for text in texts if text]

    def plan_for(body):
        found = re.search(r'[Ww]orking directory: (/[^\s"\\]+)', json.dumps(body, ensure_ascii=False))
        assert found, '请求里没有工作目录'
        cwd = found.group(1)
        first = user_texts(body)[0]
        if '审查这一次交付' in first:
            named = {name for name in TASKS if f'demo+{name}' in first}
            assert len(named) == 1, f'审查提示里的任务不唯一：{named}'
            task = named.pop()
            fields = dict(verdict='可合并', findings=[], report={'结论': '夹具审查', '完成条件与变异检查': '夹具：删除目标文件后完成条件退出 1。'})
            return 'reviewer:' + task, review_steps(body, [], fields), '已提交审查结论。'
        task = next(name for name in TASKS if cwd.endswith(f'/{name}-a1'))
        allowed, extra = TASKS[task]
        submit = re.search(r'显式交付：\n(.+)\n', first)
        assert submit, '派发提示里没有交付命令'
        line = submit.group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        steps = [
            ('Write', dict(file_path=f'{cwd}/{allowed}', content=f'written by the {task} worker\n')),
            ('Write', dict(file_path=f'{cwd}/{extra}', content=f'# {task} also touched this\n')),
            ('Bash', dict(command=f'git add {allowed} {extra} && git commit -q -m "{task} fixture change"', description='commit')),
            ('Bash', dict(command=line, description='submit')),
        ]
        texts = '\n'.join(user_texts(body))
        # T-2 after the first rejection: a second candidate that keeps the extra file. After the second rejection it
        # delivers HEAD again, which the fixture has put back on the first candidate (the worker's sandbox lets only a
        # standalone git add or git commit touch Git metadata).
        if REJECT_FIRST in texts:
            steps += [('Write', dict(file_path=f'{cwd}/{allowed}', content=f'written by the {task} worker, second try\n')),
                      ('Bash', dict(command=f'git commit -qam "{task} second candidate"', description='commit')),
                      ('Bash', dict(command=line, description='submit'))]
        if REJECT_SECOND in texts:
            steps += [('Bash', dict(command=line, description='submit'))]
        return 'worker:' + task, steps, '已提交并交付。'

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
                    api['received'][role] = user_texts(body)
                messages = body['messages']
                step = sum(1 for message in messages if message['role'] == 'assistant' and isinstance(message['content'], list)
                           and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in message['content']))
                # A worker that got feedback after its delivery answers in words; the feedback itself is what is checked.
                action = steps[step] if step < len(steps) else None
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()

            def emit(kind, value):
                self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps({'type': kind, **value}) + '\n\n').encode())
                self.wfile.flush()
            emit('message_start', {'message': {'id': f'msg_t198_{number}', 'type': 'message', 'role': 'assistant',
                                               'model': SERVED_MODEL, 'content': [], 'stop_reason': None,
                                               'usage': {'input_tokens': 128, 'output_tokens': 0}}})
            if action:
                emit('content_block_start', {'index': 0, 'content_block': {'type': 'tool_use', 'id': f'toolu_t198_{number}', 'name': action[0], 'input': {}}})
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
               GIT_AUTHOR_NAME='t198', GIT_AUTHOR_EMAIL='t198@example.invalid',
               GIT_COMMITTER_NAME='t198', GIT_COMMITTER_EMAIL='t198@example.invalid')
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
            assert not api['error'], api['error']
            assert time.monotonic() < deadline, f'超时：{label}'
            time.sleep(.2)

    def git(*arguments):
        return subprocess.check_output(['git', '-C', str(repo), *arguments], text=True).strip()

    def brief(value):
        return {key: value.get(key) for key in ('ok', 'error', 'details')}

    try:
        config = dict(claude_bin=args.claude, role_card=str(source / 'workbench/roles/worker.md'), role_card_revision='t198-fixture',
                      reviewer_role_card=str(source / 'workbench/roles/reviewer.md'), reviewer_role_card_revision='t198-fixture',
                      code_revision='t198-fixture', hook_authorization='T-198 fixture: hooks only through launch arguments', turn_limit=6)
        (fixture / 'launch-config.json').write_text(json.dumps(config), encoding='utf-8')
        run_cli('daemon_start', '--launch-config', str(fixture / 'launch-config.json'))
        running = True
        wait('后台恢复结束', lambda: request('pane_layout').get('recovering') is False, 10)
        operator = json.loads((fixture / 'operator.json').read_text(encoding='utf-8'))

        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=env)
        (repo / 'README.md').write_text('demo\n', encoding='utf-8')
        for task, (allowed, _) in TASKS.items():
            (repo / f'check_{task}.py').write_text(f'import pathlib, sys\nsys.exit(0 if pathlib.Path("{allowed}").is_file() else 1)\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True, env=env)
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'init'], check=True, env=env)
        assert request('project_open', operator, repo=str(repo))['ok']

        # A project terminal whose CLI the user approved as the executor controller (as in T-131).
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

        for task, (allowed, _) in TASKS.items():
            path = out / f'{task}.json'
            path.write_text(json.dumps(dict(id=task, source=None, goal=f'在仓库根目录加 {allowed}', non_goals=['不改别的文件'],
                paths=dict(allow=[allowed], deny=[]), oracle_paths=[f'check_{task}.py'], completion_conditions=[dict(argv=['python3', f'check_{task}.py'])],
                red_commands=[], task_type='测试', repair_target=None, complexity='S',
                executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
            assert request('card_save', terminal, task=task, card=str(path), expected_version=0)['ok']
            assert request('create', terminal, task=task, project='demo', repo=str(repo), branch='refs/heads/main', card_version=1)['ok']
            dispatched = request('dispatch', terminal, task=task, runtimeMode='workspace-write')
            assert dispatched.get('ok'), dispatched

        def state_of(task):
            return request('status', operator, task=task)['task']

        def events(task, kind):
            return [e['details'] for e in request('events', operator, task=task)['events'] if e['type'] == kind]

        for task in TASKS:
            wait(f'{task} 交付', lambda task=task: state_of(task)['state'] not in ('preparing', 'claimed'), 180)
        verified = {task: request('verify', terminal, task=task) for task in TASKS}
        report['verify'] = {task: brief(value) for task, value in verified.items()}

        # 1: T-1 and T-2 go on to review instead of ending in path_boundary_failed; the list is recorded.
        def settled(task):
            current = state_of(task)
            return current if current['state'] in ('verified', 'submitted', 'rework', 'failed', 'paused') and \
                (current.get('review') or {}).get('state') not in (None, 'requested', 'running') else None
        settled_states = {}
        for task in ('T-1', 'T-2'):
            if not verified[task].get('ok'):
                settled_states[task] = state_of(task)['state']
                continue
            settled_states[task] = wait(f'{task} 审查结束', lambda task=task: settled(task), 240)['state']
        report['settled'] = settled_states
        path_checks = {task: events(f'demo+{task}', 'path_check') for task in ('T-1', 'T-2')}
        report['path_check'] = {task: [{key: e.get(key) for key in ('out_of_card', 'passed')} for e in value] for task, value in path_checks.items()}
        check('out_of_card_waits_for_judgement', all(verified[task].get('ok') and settled_states[task] == 'verified' and
              path_checks[task] and path_checks[task][-1].get('out_of_card') == [TASKS[task][1]] for task in ('T-1', 'T-2')),
              dict(verify=report['verify'], settled=settled_states, path_check=report['path_check']))

        # 5: the extra file is T-3's oracle: refused as before, not left for judgement.
        check('out_of_card_oracle_still_refused', verified['T-3'].get('error') == 'oracle_modified' and
              state_of('T-3')['repair'] is not None, report['verify']['T-3'])

        # 6: the reviewer was told which files are outside the card.
        prompt = '\n'.join(api['received'].get('reviewer:T-1', []))
        check('reviewer_input_lists_out_of_card', '卡外改动' in prompt and TASKS['T-1'][1] in prompt, prompt[-600:])

        # 2: no integration before a judgement; a blank reason is none; a reason lets it through and is recorded.
        score = out / 'score.json'
        score.write_text(json.dumps(dict(result='通过', boundary_discipline=2, boundary_reason='多写了一个说明文件',
            engineering_taste=2, engineering_reason='夹具', notes='T-198 fixture'), ensure_ascii=False), encoding='utf-8')
        unjudged = request('integrate', terminal, task='T-1', score_file=str(score))
        blank = request('out_of_card', terminal, task='T-1', decision='accept', reason=' 　 ')
        reason = 'notes/extra-1.txt 是这次改动的说明，留下无妨'
        accepted = request('out_of_card', terminal, task='T-1', decision='accept', reason=reason)
        integrated = request('integrate', terminal, task='T-1', score_file=str(score))
        report['t1'] = dict(unjudged=brief(unjudged), blank=brief(blank), accepted=brief(accepted), integrated=brief(integrated))
        check('integrate_refused_before_judgement', unjudged.get('error') == 'out_of_card_unjudged' and
              (unjudged.get('details') or {}).get('out_of_card') == [TASKS['T-1'][1]], report['t1']['unjudged'])
        check('blank_reason_is_no_reason', blank.get('error') == 'invalid_text', report['t1']['blank'])
        judged = events('demo+T-1', 'out_of_card_judged')
        report['t1']['judged'] = judged
        check('accepted_with_reason_integrates', accepted.get('ok') and integrated.get('ok') and state_of('T-1')['state'] == 'accepted' and
              TASKS['T-1'][1] in git('ls-tree', '-r', '--name-only', 'refs/heads/main').split() and
              len(judged) == 1 and judged[0]['decision'] == 'accept' and judged[0]['reason'] == reason and
              judged[0]['out_of_card'] == [TASKS['T-1'][1]], report['t1'])

        # 4: the controller first lets T-2's extra file stay, then changes its mind and sends T-2 back; its worker
        # gets the list and the task waits for a new delivery.
        first_candidate = state_of('T-2')['candidate_commit']
        first_accept = request('out_of_card', terminal, task='T-2', decision='accept', reason='先留下')
        before = len(api['received'].get('worker:T-2', []))
        rejected = request('out_of_card', terminal, task='T-2', decision='reject', reason=REJECT_FIRST)
        report['t2'] = dict(first_candidate=first_candidate, first_accept=brief(first_accept), rejected=brief(rejected))
        feedback = wait('T-2 worker 收到打回', lambda: [text for text in api['received'].get('worker:T-2', [])[before:]
                                                        if TASKS['T-2'][1] in text], 90)
        current = state_of('T-2')
        report['t2'].update(state=current['state'], repair=current.get('repair'), feedback=feedback[-1][-800:])
        check('reject_reaches_worker_with_list', rejected.get('ok') and current['state'] == 'submitted' and
              (current.get('repair') or {}).get('check') == 'path_boundary' and
              ((current.get('repair') or {}).get('failure') or {}).get('error') == 'out_of_card_rejected' and REJECT_FIRST in feedback[-1], report['t2'])

        # 7: a second candidate, rejected too; the worker then delivers the first one again. The earlier accept was
        # withdrawn, so integration waits for a new judgement.
        def delivered(task, commit_filter):
            current = state_of(task)
            return current if current['state'] == 'submitted' and not current.get('repair') and commit_filter(current['candidate_commit']) else None

        def verified_again(task):
            assert request('verify', terminal, task=task).get('ok'), state_of(task)
            return wait(f'{task} 审查结束', lambda: settled(task), 240)

        def once_idle(command, **data):
            # The review's own cleanup holds the operation lock for a moment after its result is in, and integration
            # waits for that cleanup's record.
            return wait(command + ' 等审查收尾', lambda: (lambda value: value if value.get('error') not in ('operation_busy', 'review_end_check_required') else None)(
                request(command, terminal, task='T-2', **data)), 60)

        second = wait('T-2 交第二个候选', lambda: delivered('T-2', lambda commit: commit != first_candidate), 120)
        verified_again('T-2')
        second_unjudged = once_idle('integrate', score_file=str(score))
        workspace = state_of('T-2')['current_attempt']['workspace']
        subprocess.run(['git', '-C', workspace, 'reset', '-q', '--hard', first_candidate], check=True, env=env)
        rejected_again = once_idle('out_of_card', decision='reject', reason=REJECT_SECOND)
        wait('T-2 交回第一个候选', lambda: delivered('T-2', lambda commit: commit == first_candidate), 120)
        again = verified_again('T-2')
        reappeared = once_idle('integrate', score_file=str(score))
        report['t2'].update(second_candidate=second['candidate_commit'], second_unjudged=brief(second_unjudged),
                            rejected_again=brief(rejected_again), reappeared_state=again['state'], reappeared=brief(reappeared),
                            main_files=git('ls-tree', '-r', '--name-only', 'refs/heads/main').split())
        check('withdrawn_accept_does_not_return', first_accept.get('ok') and second_unjudged.get('error') == 'out_of_card_unjudged' and
              rejected_again.get('ok') and again['state'] == 'verified' and reappeared.get('error') == 'out_of_card_unjudged' and
              TASKS['T-2'][1] not in report['t2']['main_files'], report['t2'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api_roles'] = {role: len(texts) for role, texts in api['received'].items()}
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
