"""T-127：Codex worker 与 reviewer 用用户自己的 Codex home（夹具里是 $HOME/.codex）。真实后台、socket、终端、门禁，
真实安装的 Codex（交互 TUI，在 node-pty 里），模型换成本地脚本化的 Responses 接口，不调用供应商。

失败方式（先列再写）：
1. 后台仍要求隔离 home（`isolated_codex_home_required`），或 reviewer 仍要预建 home（`review_launch_config_required`）。
2. 会话所在目录被当作受信任：项目自己的 .codex 钩子（worker 能改、reviewer 的副本里也有）在 worker 或 reviewer 里运行。
3. 受信任对话框被按下“Trust and continue”，信任写进用户 home 的 config.toml；或“Open restricted”没人按，worker 卡住，
   第一条任务永远不送出。
4. home 自己的规则、钩子、skill 没生效：git add / git commit 被沙箱拒、home 的钩子不触发、skill 不在请求里。
5. a2a 改写了用户 home 的 config.toml、rules 或 hooks.json。
6. 共享 home 里别的会话（另一个目录）的原生记录被读进这个 worker；或者因为 home 里旧会话太多，找不到本会话。
7. 交付到不了门禁，审查起不来（reviewer 不在同一 home、不在一次性副本里、副本没以 untrusted 打开），或审查通过后集成不到工作分支。
8. 门禁放过不合格的 Codex reviewer：untrusted 指向别的目录，原生会话的工作目录不是一次性副本，
   或者续接了 worker 的会话（启动记录写明 resume，或只在实际命令里 resume）。
   --reviewer-case 改写源码副本里 reviewer 的启动方式。
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from t112_native_api import message_events, request_source, request_tools, shell_item, tool_events  # noqa: E402



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--codex', default=os.path.realpath(shutil.which('codex') or str(Path.home() / '.local/bin/codex')))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    # Several mutants may be combined, e.g. a runtime fault together with the gate check that should catch it.
    target.add_argument('--mutant', nargs='+', choices=['restricted-unanswered', 'untrusted-config-missing', 'project-trusted',
                                             'gate-trust-unchecked', 'gate-folder-unchecked', 'scan-any-folder', 'scan-whole-home',
                                             'reviewer-folder-unbound'])
    # Earlier sessions already in the home; timings are compared across runs with different counts.
    parser.add_argument('--old-sessions', type=int, default=400)
    parser.add_argument('--reviewer-case', choices=['trust-other-folder', 'session-folder-differs', 'resume-worker-in-argv', 'resume-worker-hidden'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t127-', dir='/private/tmp')).resolve()
    state, home, repo, out, outside = (fixture / name for name in ('state', 'home', 'demo', 'out', 'outside'))
    for path in (state, home, repo, out, outside):
        path.mkdir()
    codex_home = home / '.codex'
    source = ROOT
    if args.revision or args.mutant or args.reviewer_case:
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
        if not args.revision:
            for name in ('src', 'terminal', 'hooks', 'roles'):
                shutil.copytree(ROOT / 'workbench' / name, source / 'workbench' / name, symlinks=True)
        patches = []
        if args.mutant:
            table = {
                'restricted-unanswered': [('src/panes.ts', 'if (pane.state === "unknown") (claude ? this.confirmWorkerTrust(pane, data) : this.openCodexRestricted(pane, data));',
                                           'if (pane.state === "unknown" && claude) this.confirmWorkerTrust(pane, data);')],
                'untrusted-config-missing': [('src/panes.ts', '      "-c", `projects={${JSON.stringify(trustRoot)}={trust_level="untrusted"}}`,\n', '')],
                'project-trusted': [('src/panes.ts', '={trust_level="untrusted"}}`,\n      ...(review', '={trust_level="trusted"}}`,\n      ...(review')],
                'gate-trust-unchecked': [('src/gates/core.ts', '        config(`projects={${JSON.stringify(realpathSync(review.candidate_workspace))}={trust_level="untrusted"}}`) &&\n', '')],
                'gate-folder-unchecked': [('src/gates/core.ts', 'requireGate(cwd === review.candidate_workspace, "review_native_session_folder",',
                                           'requireGate(true, "review_native_session_folder",')],
                # The scan before T-127: every file under sessions/, on every read.
                'scan-whole-home': [('src/panes.ts', 'pane.nativeFile ? [pane.nativeFile] : [...new Set([...pane.offsets.keys(), ...days.flatMap(walk).filter((file) => statSync(file).mtimeMs >= since)])];',
                                     'pane.nativeFile ? [pane.nativeFile] : walk(join(home, "sessions"));')],
                'scan-any-folder': [('src/panes.ts', 'if (!final && (metadata.type !== "session_meta" || metadata.payload?.cwd !== pane.attempt.workspace)) continue;',
                                     'if (!final && metadata.type !== "session_meta") continue;')],
                # The runtime binds a reviewer's session by the read-only review worktree instead of the candidate
                # copy, leaving the gate's folder check to notice. Observed (round 05): the reviewer's Stop hook is
                # refused earlier (question_origin_unverified), so the result never reaches that gate check.
                'reviewer-folder-unbound': [
                    ('src/panes.ts', 'if (!final && (metadata.type !== "session_meta" || metadata.payload?.cwd !== pane.attempt.workspace)) continue;',
                     'if (!final && (metadata.type !== "session_meta" || metadata.payload?.cwd !== (pane.record.review_workspace ?? pane.attempt.workspace))) continue;'),
                    ('src/panes.ts', 'const rootFile = codexSessionOrigin(file, metadata, metadata.payload?.id, pane.attempt.workspace) === "root";',
                     'const rootFile = codexSessionOrigin(file, metadata, metadata.payload?.id, pane.record.review_workspace ?? pane.attempt.workspace) === "root";')],
            }
            for name in args.mutant:
                patches += table[name]
        if args.reviewer_case:
            patches += {
                # The reviewer opens the read-only review worktree untrusted instead of its candidate copy.
                'trust-other-folder': [('src/panes.ts', 'const trustRoot = claude ? null : review ? realpathSync(launchWorkspace)',
                                        'const trustRoot = claude ? null : review ? realpathSync(review.workspace)')],
                # The reviewer's Codex runs in the review worktree (opened untrusted at its repository root, so it
                # starts) while its launch record and argv name the candidate copy.
                'session-folder-differs': [('src/panes.ts', 'const terminal = require("node-pty").spawn("/bin/zsh", shellArgv, {',
                                            'if (review) shellArgv[3] = shellArgv[3].replace(quote("-C") + " " + quote(launchWorkspace), quote("-C") + " " + quote(review.workspace))\n'
                                            '      .replace(JSON.stringify(trustRoot), JSON.stringify(await repositoryRoot(review.workspace)));\n'
                                            '    const terminal = require("node-pty").spawn("/bin/zsh", shellArgv, {')],
                # The reviewer resumes the worker's own session, and its launch record says so.
                'resume-worker-in-argv': [('src/panes.ts', 'review ? [] : await workerGitDenied(launchWorkspace)) : [executable, "--no-daemon",',
                                           'review ? [] : await workerGitDenied(launchWorkspace)) : [executable, ...(review ? ["resume", review.attempt.runtime_identity!.native_session!] : []), "--no-daemon",')],
                # The same, but only the started command resumes; the launch record and argv look like a fresh session.
                'resume-worker-hidden': [('src/panes.ts', 'const terminal = require("node-pty").spawn("/bin/zsh", shellArgv, {',
                                          'if (review) shellArgv[3] = shellArgv[3].replace(quote(executable) + " ", quote(executable) + " \'resume\' " + quote(review.attempt.runtime_identity!.native_session!) + " ");\n'
                                          '    const terminal = require("node-pty").spawn("/bin/zsh", shellArgv, {')],
            }[args.reviewer_case]
        for path, old, new in patches:
            path = source / 'workbench' / path
            text = path.read_text(encoding='utf-8')
            assert text.count(old) == 1, ('变异定位必须唯一', old)
            path.write_text(text.replace(old, new), encoding='utf-8')
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    cli = source / 'workbench/src/gates/cli.ts'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, reviewer_case=args.reviewer_case,
                  fixture=str(fixture), codex=args.codex, real_model_turns=0, checks=[])

    # The model: a scripted Responses endpoint. Worker and reviewer are told apart by their prompt;
    # each gets its shell steps in order, then a final message.
    api = dict(requests=0, outputs=dict(worker=[], reviewer=[]), bodies=dict(worker=[], reviewer=[]), error=None)

    def user_text(body):
        return '\n'.join(part.get('text', '') for item in body['input'] if item.get('type') == 'message' and item.get('role') == 'user'
                         for part in item.get('content', []) if isinstance(part, dict))

    def plan_for(body):
        text = user_text(body)
        found = re.search(r'<cwd>([^<]+)</cwd>', text)
        assert found, '请求里没有工作目录'
        cwd = found.group(1)
        if '审查这一次交付' in text:
            start = text.rindex('{\n  "schema": 1')
            shape, _ = json.JSONDecoder().raw_decode(text[start:])
            shape.update(verdict='可合并', findings=[], report={'结论': '候选加了 hello.txt，内容为 hello，满足任务卡。',
                '完成条件与变异检查': '变异 1：删除 hello.txt，python3 check.py 退出 1；变异 2：内容改成 bye，退出 1。'})
            review_worktree = state / 'worktrees/demo/T-1-a1-review-1'
            return 'reviewer', cwd, [
                'rm hello.txt; python3 check.py; echo "mutation-1 rc=$?"',
                "printf 'bye\\n' > hello.txt; python3 check.py; echo \"mutation-2 rc=$?\"",
                f'echo x > {review_worktree}/shell-note.txt; echo "wt rc=$?"; echo x > "$A2A_REQUEST_DIR/forged.json"; echo "req rc=$?"',
            ], json.dumps(shape, ensure_ascii=False)
        submit = re.search(r'显式交付：\n(.+)\n', text)
        assert submit, '派发提示里没有交付命令'
        line = submit.group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return 'worker', cwd, [
            "printf 'hello\\n' > hello.txt",
            # Allowed by the home's own rules, not by any rule a2a adds.
            'git add hello.txt',
            'git commit -q -m "T-127 fixture change"',
            line,
        ], '已提交并交付。'

    class Api(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_GET(self):
            payload = json.dumps({'object': 'list', 'data': [{'id': 'gpt-6.1-sol', 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                api['requests'] += 1
                with (out / 'api.jsonl').open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(body, ensure_ascii=False) + '\n')
                if request_source(body) == 'thread_title':
                    events = message_events(json.dumps({'title': 'T-127 fixture'}), body['model'])
                else:
                    role, cwd, steps, final = plan_for(body)
                    api['bodies'][role].append(body)
                    done = [item for item in body['input'] if item.get('type') == 'custom_tool_call']
                    outputs = [item for item in body['input'] if item.get('type') == 'custom_tool_call_output']
                    api['outputs'][role] = [str(item.get('output'))[:4000] for item in outputs]
                    events = (tool_events(shell_item(request_tools(body), steps[len(done)], cwd), body['model'])
                              if len(done) < len(steps) else message_events(final, body['model']))
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for sequence, (name, payload) in enumerate(events):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api['error'] = f'{type(error).__name__}: {error}'
                self.send_error(500)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Api)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # The user's Codex home: their provider (here the fixture API), the two Git allow rules, a hook
    # and a skill of their own, and many earlier sessions. Nothing in it trusts the fixture project.
    (codex_home / 'rules').mkdir(parents=True)
    (codex_home / 'config.toml').write_text('model_provider = "t127"\ncli_auth_credentials_store = "file"\n[model_providers.t127]\nname = "T127 fixture"\n'
        f'base_url = "http://127.0.0.1:{server.server_port}/v1"\nwire_api = "responses"\nrequires_openai_auth = false\n', encoding='utf-8')
    (codex_home / 'rules/default.rules').write_text('prefix_rule(pattern=["git", "add"], decision="allow")\n'
                                                    'prefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding='utf-8')
    marker = lambda name: [{'hooks': [{'type': 'command', 'command': f'touch {out}/{name}-$A2A_ROLE', 'timeout': 10}]}]
    (codex_home / 'hooks.json').write_text(json.dumps({'hooks': {event: marker('home-hook-' + event) for event in ('UserPromptSubmit', 'Stop')}}), encoding='utf-8')
    (codex_home / 'skills/t127-user-skill').mkdir(parents=True)
    (codex_home / 'skills/t127-user-skill/SKILL.md').write_text('---\nname: t127-user-skill\ndescription: A skill the user installed in their own Codex home.\n---\n\nSay hello.\n', encoding='utf-8')
    old_day = codex_home / 'sessions/2026/09/01'
    old_day.mkdir(parents=True)
    for index in range(args.old_sessions):
        session = str(uuid.uuid4())
        (old_day / f'rollout-2026-09-01T00-00-{index:02d}-{session}.jsonl').write_text(json.dumps(
            {'type': 'session_meta', 'payload': {'id': session, 'cwd': str(fixture / 'elsewhere'), 'source': 'cli'}}) + '\n', encoding='utf-8')
    home_before = {name: (codex_home / name).read_bytes() for name in ('config.toml', 'rules/default.rules', 'hooks.json', 'skills/t127-user-skill/SKILL.md')}

    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', ELECTRON_RUN_AS_NODE='1',
               A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'),
               GIT_AUTHOR_NAME='t127', GIT_AUTHOR_EMAIL='t127@example.invalid',
               GIT_COMMITTER_NAME='t127', GIT_COMMITTER_EMAIL='t127@example.invalid')
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

    def failures(launch):
        return [dict(type=e['type'], data=e.get('data')) for e in events() if e['launch'] == launch and
                e['type'] in ('worker_startup_unrecognised', 'codex_folder_trust_requested', 'codex_restricted_open_failed', 'launch_failed')]

    try:
        report['codex_version'] = subprocess.check_output([args.codex, '--version'], text=True).strip()
        config = dict(codex_bin=args.codex, codex_home=str(codex_home), role_card=str(source / 'workbench/roles/worker.md'), role_card_revision='t127-fixture',
                      reviewer_role_card=str(source / 'workbench/roles/reviewer.md'), reviewer_role_card_revision='t127-fixture',
                      code_revision='t127-fixture', hook_authorization='T-127 fixture: hooks only through launch arguments', turn_limit=8)
        (fixture / 'launch-config.json').write_text(json.dumps(config), encoding='utf-8')
        run_cli('daemon_start', '--launch-config', str(fixture / 'launch-config.json'))
        running = True
        wait('后台恢复结束', lambda: request('pane_layout').get('recovering') is False, 10)
        operator = json.loads((fixture / 'operator.json').read_text(encoding='utf-8'))

        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=env)
        (repo / 'README.md').write_text('demo\n', encoding='utf-8')
        (repo / 'check.py').write_text('import pathlib, sys\np = pathlib.Path("hello.txt")\nsys.exit(0 if p.is_file() and p.read_bytes() == b"hello\\n" else 1)\n', encoding='utf-8')
        # The project's own Codex config and hooks: a worker could write these, and the reviewer's copy carries them.
        (repo / '.codex').mkdir()
        (repo / '.codex/hooks.json').write_text(json.dumps({'hooks': {event: marker('project-hook-' + event) for event in ('UserPromptSubmit', 'Stop')}}), encoding='utf-8')
        (repo / '.codex/config.toml').write_text('[hooks]\nStop = [{hooks=[{type="command",command=' + json.dumps(f'touch {out}/project-config-hook-$A2A_ROLE') + ',timeout=10}]}]\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True, env=env)
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'init'], check=True, env=env)
        main_before = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'refs/heads/main'], text=True).strip()
        assert request('project_open', operator, repo=str(repo))['ok']

        # A project terminal whose CLI the user approved as the executor controller.
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

        card = out / 'card.json'
        card.write_text(json.dumps(dict(id='T-1', source=None, goal='在仓库根目录加 hello.txt，内容为 hello', non_goals=['不改别的文件'],
            paths=dict(allow=['hello.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
            red_commands=[], task_type='测试', repair_target=None, complexity='S',
            executor=dict(cli='Codex', model='gpt-6.1-sol', effort='low'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
        saved = request('card_save', terminal, task='T-1', card=str(card), expected_version=0)
        assert saved['ok'], saved
        created = request('create', terminal, task='T-1', project='demo', repo=str(repo), branch='refs/heads/main', card_version=1)
        assert created['ok'], created
        dispatched = request('dispatch', terminal, task='T-1', runtimeMode='workspace-write', model='gpt-6.1-sol', effort='low')
        report['dispatch'] = {key: dispatched.get(key) for key in ('ok', 'error', 'details')}
        check('dispatch_starts_codex_worker_in_user_home', dispatched.get('ok'), report['dispatch'])
        attempt = dispatched['attempt']
        workspace = Path(attempt['workspace'])
        worker = request('launch_show', operator, launch=attempt['runtime_identity']['launch'])['launch']
        worker_launch = worker['id']
        dispatched_at = time.monotonic()
        # 6: the user runs Codex elsewhere at the same time; its rollout lands in today's directory.
        today = time.localtime()
        foreign_day = codex_home / 'sessions' / time.strftime('%Y/%m/%d', today)
        foreign_day.mkdir(parents=True, exist_ok=True)
        foreign_id = str(uuid.uuid4())
        foreign = foreign_day / f'rollout-{time.strftime("%Y-%m-%dT%H-%M-%S", today)}-{foreign_id}.jsonl'
        foreign.write_text(json.dumps({'type': 'session_meta', 'payload': {'id': foreign_id, 'cwd': str(outside), 'source': 'cli'}}) + '\n'
                           + json.dumps({'type': 'event_msg', 'payload': {'type': 'task_started', 'turn_id': 'foreign'}}) + '\n', encoding='utf-8')
        argv = worker['argv']
        report['worker'] = dict(cli=worker.get('cli'), codex_home=worker['env'].get('CODEX_HOME'), argv=[a for a in argv if not a.startswith('hooks.')])
        check('worker_runs_in_user_home', worker.get('cli') == 'Codex' and worker['env'].get('CODEX_HOME') == os.path.realpath(codex_home), report['worker'])

        # 3: the restricted screen is answered once, then the task goes in.
        wait('worker 第一条任务送达', lambda: api['bodies']['worker'] or failures(worker_launch), 150)
        check('worker_started', not failures(worker_launch), failures(worker_launch))
        startup = [e['type'] for e in events({'codex_restricted_open_intent', 'codex_restricted_opened', 'turn_submitted'}) if e['launch'] == worker_launch]
        report['startup'] = startup
        check('restricted_answered_before_first_task', startup[:3] == ['codex_restricted_open_intent', 'codex_restricted_opened', 'turn_submitted'], startup)
        native = wait('worker 原生会话', lambda: [e for e in events({'pane_native_session'}) if e['launch'] == worker_launch], 60)
        report['native_session_after_dispatch_s'] = round(time.monotonic() - dispatched_at, 1)
        report['old_session_files'] = args.old_sessions

        def submitted():
            status = request('status', operator, task='T-1')
            failed = failures(worker_launch)
            assert not failed, failed
            return status['task'] if status['task']['state'] not in ('preparing', 'claimed') else None
        task = wait('交付到达门禁', submitted, 240)
        report['delivery_after_dispatch_s'] = round(time.monotonic() - dispatched_at, 1)
        report['task_state'] = task['state']
        outputs = api['outputs']['worker']
        report['worker_outputs'] = outputs
        # 4: the home's skill reached the model; its hook fired; its rules let git add and commit out.
        first = json.dumps(api['bodies']['worker'][0], ensure_ascii=False)
        check('home_skill_loaded', 't127-user-skill' in first)
        commit = task.get('candidate_commit') or task['current_attempt'].get('delivery', {}).get('commit')
        branch_log = subprocess.check_output(['git', '-C', str(repo), 'log', '--format=%H %s', f'{main_before}..{commit}'], text=True).splitlines()
        report['branch_log'] = branch_log
        check('home_rules_let_git_commit', len(branch_log) == 1 and branch_log[0].endswith('T-127 fixture change'), branch_log)
        message = subprocess.check_output(['git', '-C', str(repo), 'log', '-1', '--format=%B', commit], text=True)
        trailers = dict(re.findall(r'^A2A-([A-Za-z-]+): (.+)$', message, re.M))
        report['trailers'] = trailers
        check('commit_carries_codex_identity', trailers.get('Native-Session') == native[0]['data']['native_session'] and
              trailers.get('Launch') == worker_launch, trailers)
        # The sandbox boundary is not checked here: the fixture lives under /tmp, which a Codex worker
        # may write by design (its request directory is there). T-112's reviewer diagnosis covers it.
        check('delivery_reached_gate', task['state'] == 'submitted', task['state'])
        # 6: nothing from the other session was read into this worker.
        foreign_rows = [e for e in events({'native_record'}) if foreign_id in json.dumps(e.get('data'))]
        check('foreign_session_in_home_ignored', not foreign_rows, len(foreign_rows))

        # 7: verification starts a fresh Codex reviewer in the same home, in an untrusted one-time copy.
        verified = request('verify', terminal, task='T-1')
        report['verify'] = {key: verified.get(key) for key in ('ok', 'error')}
        if args.reviewer_case in ('trust-other-folder', 'resume-worker-in-argv'):
            check('reviewer_launch_refused_' + args.reviewer_case.replace('-', '_'), not verified.get('ok') and verified.get('error') == 'review_launch_boundary', report['verify'])
            report['status'] = 'PASS'
            return
        assert verified.get('ok'), verified
        if args.reviewer_case in ('session-folder-differs', 'resume-worker-hidden') and 'reviewer-folder-unbound' not in (args.mutant or []):
            # The runtime binds only a session whose rollout names the candidate copy, so this reviewer's
            # session is never bound: its finished turn delivers nothing, and the review cannot pass.
            # A hidden resume of the still-running worker session never starts a turn: Codex answers "This
            # conversation is open in another app" (round 05). So the Stop hook is waited for, not required.
            review_launch = request('status', operator, task='T-1')['task']['review']['launch_id']
            stop_seen = lambda: [e for e in events({'hook_received'}) if e['launch'] == review_launch and
                                 '"hook_event_name":"Stop"' in e['data'].get('raw_stdin', '').replace(' ', '')]
            deadline = time.monotonic() + 150
            while not stop_seen() and time.monotonic() < deadline:
                time.sleep(1)
            report['reviewer_stop_seen'] = bool(stop_seen())
            time.sleep(5)
            current = request('status', operator, task='T-1')['task']
            bound = [e for e in events({'pane_native_session'}) if e['launch'] == review_launch]
            report['review'] = {key: current['review'].get(key) for key in ('state', 'error', 'details')}
            check('reviewer_elsewhere_never_bound_or_passed', not bound and current['review']['state'] != 'passed' and current['state'] != 'verified',
                  dict(bound=bound, review=report['review'], task=current['state']))
            report['status'] = 'PASS'
            return
        task = wait('审查结束', lambda: (lambda current: current if current['state'] in ('verified', 'submitted', 'rework', 'failed') and
                                          current.get('review', {}).get('state') not in (None, 'requested', 'running') else None)(
                                              request('status', operator, task='T-1')['task']), 240)
        review = task['review']
        report['review'] = {key: review.get(key) for key in ('state', 'error', 'details', 'verdict')}
        expected_refusals = {'session-folder-differs': ('review_native_session_folder',),
                             'resume-worker-hidden': ('review_writer_conflict', 'review_native_session_reused')}.get(args.reviewer_case)
        if expected_refusals and 'reviewer-folder-unbound' in (args.mutant or []):
            refusals = [e for e in request('events', operator, task='T-1')['events'] if any(name in json.dumps(e) for name in expected_refusals)]
            report['refusals'] = refusals[-3:]
            check('reviewer_result_refused_' + args.reviewer_case.replace('-', '_'), review['state'] != 'passed' and refusals, report['review'])
            report['status'] = 'PASS'
            return
        reviewer = request('launch_show', operator, launch=review['launch_id'])['launch']
        rargv = reviewer['argv']
        candidate_copy = reviewer['candidate_workspace']
        report['reviewer'] = dict(cli=reviewer.get('cli'), codex_home=reviewer['env'].get('CODEX_HOME'), candidate=candidate_copy,
                                  argv=[a for a in rargv if not a.startswith('hooks.')], outputs=api['outputs']['reviewer'], review_state=review['state'])
        check('reviewer_same_home_untrusted_copy', reviewer.get('cli') == 'Codex' and reviewer['env'].get('CODEX_HOME') == os.path.realpath(codex_home) and
              rargv[rargv.index('-C') + 1] == candidate_copy and
              f'projects={{{json.dumps(os.path.realpath(candidate_copy))}={{trust_level="untrusted"}}}}' in rargv, report['reviewer'])
        routs = api['outputs']['reviewer']
        check('reviewer_mutations_ran_in_copy', len(routs) >= 2 and 'mutation-1 rc=1' in routs[0] and 'mutation-2 rc=1' in routs[1], routs)
        check('reviewer_cannot_write_outside_copy', len(routs) >= 3 and 'wt rc=0' not in routs[2] and 'req rc=0' not in routs[2] and 'wt rc=' in routs[2], routs[2:])
        check('review_passed', review['state'] == 'passed' and task['state'] == 'verified', report['review'])
        score = out / 'score.json'
        score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='只改了 hello.txt',
            engineering_taste=2, engineering_reason='夹具任务', notes='T-127 fixture'), ensure_ascii=False), encoding='utf-8')
        wait('审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in request('events', operator, task='T-1')['events']), 60)
        integrated = request('integrate', terminal, task='T-1', score_file=str(score))
        report['integrate'] = {key: integrated.get(key) for key in ('ok', 'error', 'details')}
        final = request('status', operator, task='T-1')['task']
        main_files = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', '--name-only', 'refs/heads/main'], text=True).split()
        check('integrated_into_working_branch', integrated.get('ok') and final['state'] == 'accepted' and 'hello.txt' in main_files, report['integrate'])

        # 2, 4: markers. The home's hooks ran in both sessions; the project's .codex hooks in neither.
        markers = sorted(path.name for path in out.iterdir() if 'hook' in path.name)
        report['markers'] = markers
        check('home_hooks_ran', {'home-hook-UserPromptSubmit-worker', 'home-hook-Stop-worker',
                                 'home-hook-UserPromptSubmit-reviewer', 'home-hook-Stop-reviewer'} <= set(markers), markers)
        check('project_codex_hooks_not_run', not any(name.startswith('project') for name in markers), markers)
        # 3, 5: the user's home files are as they were, and no trust entry was saved.
        # Codex itself records its TUI state in config.toml ([tui] screen_reader_detection_done and
        # model_availability_nux, T-127 probe-01); everything else must be byte for byte as before.
        changed = [name for name, data in home_before.items() if name != 'config.toml' and (codex_home / name).read_bytes() != data]
        config_before = home_before['config.toml'].decode('utf-8')
        config_after = (codex_home / 'config.toml').read_text(encoding='utf-8')
        added = config_after[len(config_before):] if config_after.startswith(config_before) else None
        headers = re.findall(r'^\[[^\]]+\]', added or '', re.M)
        report.update(home_changed=changed, config_added=added)
        check('user_home_not_rewritten', changed == [] and added is not None and all(h.startswith('[tui') for h in headers) and
              '[projects' not in config_after, dict(changed=changed, added=added))
        # Asserted last, so a launch without it is first judged by its behaviour above.
        check('worker_folder_untrusted_in_argv', f'projects={{{json.dumps(os.path.realpath(repo))}={{trust_level="untrusted"}}}}' in argv, report['worker'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api_snapshot'] = dict(requests=api['requests'], outputs=api['outputs'], error=api['error'])
        try:
            report['events_tail'] = [dict(type=e['type'], launch=e['launch']) for e in events()][-40:]
            report['failures'] = [dict(type=e['type'], data=e.get('data')) for e in events() if 'fail' in e['type'] or 'unrecognised' in e['type'] or 'trust' in e['type']][-6:]
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
