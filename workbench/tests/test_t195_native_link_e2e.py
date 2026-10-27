"""T-195：右键“复制深度链接”背后的 native_link：会话的 CLI 名、CLI 自己的会话号与记录文件。真实后台、socket、门禁；
Claude Code worker 是真实安装的 CLI（模型换成本地脚本化接口）；Codex worker 是真实 Codex 与真实模型，按项目规则用 /tmp 下的隔离
CODEX_HOME：只复制 auth.json，只信任本夹具的仓库根目录；副本不入证据，结束后整个删除，不写用户的 ~/.codex。

预期来自 CLI 自己写的记录文件（独立来源）：Claude 的 jsonl 行里的 sessionId 与 cwd，Codex rollout 首行 session_meta 的
id 与 cwd，必须分别等于链接给出的会话号和 worker 的工作区。

失败方式（先列再写）：
1. 没有这个命令，或者给出的路径不存在、打开的不是这个会话的记录。
2. 会话号是 a2a 自造的编号（osc7501:<launch>、launch id），不是 CLI 自己的。
3. 拿不到时仍给出看似可用的链接，或者不给原因。
4. 复制的文本缺 CLI 名、会话号或路径。
5. 会话变了仍给旧的（T-195 审查 F1）：项目终端里的 Claude Code 在 /clear 之后仍给 /clear 之前的会话；CLI 退出后仍给它的会话。
6. 终端里的 opencode 报了会话号就给出：它的报告不带进程号，分不出来自哪一次运行（第 3 轮审查 F1；v3 按命令边界归属，
   `opencode; opencode`、管道、子 shell 都会归错）。
7. agy 的记录库有一个读不了时，把它当成“不匹配”，从多个会话里挑出一个（F3）。
8. 第 2 轮审查：受管 Claude 在窗格里 /clear 后仍给启动时的会话（R5）；受管 Codex 的工作区出现第二个根线程仍给绑定的那个（R4）；
   终端 agy 按启动目录挑出一个以前的会话（R3）。
9. 第 3 轮审查：受管 Codex 的某份 rollout 读不了（权限、被删）时报错而不是置灰（F4）；启动之前写完的 rollout 被当成本次的
   第二个根线程（M1）。
10. 第 4 轮审查：扫描范围内有一天的目录看不进去（祖先目录没有搜索权限），被当成那天没有记录，读不了反而给出链接（R4-F1）。
opencode 与 agy 在终端里用最小替身（名为 opencode、agy 的 node 脚本）：只报 OSC 7501 或占住前台，记录库是夹具里按两家真实格式建的
SQLite；两家真实 CLI 的事实见 findings/2026-10-27-native-session-ids.zh-CN.md。Codex 的第二个根线程是本测试写进隔离 CODEX_HOME
的一份 rollout（只有首行 session_meta），代表在 worker 窗格里开了新线程。
--revision 在该版本的隔离源码上跑同一场景（修前应在第 1 条失败）。
"""
import argparse
from datetime import datetime, timedelta
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
SERVED_MODEL = 'claude-haiku-5-5-t195-served'
# Each one undoes one finding of review 1; the run must fail at that finding's check.
MUTANTS = {
    # R5: a managed Claude pane keeps its bound session after the CLI reported another.
    'claude-ignores-other-session': ('src/nativeLink.ts', '    if (others.size) return', '    if (false) return'),
    # R4: a second root thread in a managed Codex worktree goes unnoticed.
    'codex-ignores-second-thread': ('src/nativeLink.ts', 'const other = threads.find(id => id !== session);', 'const other = undefined as string | undefined;'),
    # R3: a terminal agy takes the only conversation file of the terminal's directory.
    'terminal-agy-by-directory': ('src/nativeLink.ts', "  if (cli === 'agy') return { available: false, cli, reason: 'agy 不报会话号，终端里分不出是哪一次会话（受管 agy worker 按工作区可以）' };",
                                  "  if (cli === 'agy') return agyLink(userHome, record.worktree);"),
    # M1: a rollout last written before the launch counts as a thread of this run.
    'codex-counts-older-rollouts': ('src/nativeLink.ts', '        if (statSync(path).mtimeMs < since) continue;\n', '        statSync(path);\n'),
    # F4: a rollout that cannot be opened ends the lookup with an error instead of greying the link.
    'codex-read-error-escapes': ('src/nativeLink.ts', "      } catch (error) { return { unreadable: `${path}（${(error as Error).message}）` }; }",
                                 '      } catch (error) { throw error; }'),
    # R4-F1: a day directory that cannot be looked into counts as a day without rollouts.
    'codex-unsearchable-day-skipped': ('src/nativeLink.ts', "      if ((error as NodeJS.ErrnoException).code === 'ENOENT') continue;\n",
                                       "      continue;\n"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    parser.add_argument('--codex', default=shutil.which('codex') or str(Path.home() / '.local/bin/codex'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t195-', dir='/private/tmp')).resolve()
    state, home, repo, out, doubles = (fixture / name for name in ('state', 'home', 'demo', 'out', 'doubles'))
    for path in (state, home, repo, out, doubles):
        path.mkdir()
    (home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
                                                   'projects': {str(repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
    # The opencode double reports what opencode reports (T-187 facts): its first report carries no session id; after a line
    # is typed it reports one. "q" ends it. The agy double only holds the foreground.
    (doubles / 'opencode').write_text('#!/usr/bin/env node\n'
        'const report = id => process.stdout.write(`\\x1b]7501;state=idle:app=opencode${id ? ":id=" + id : ""}\\x07`);\n'
        'report(null);\n'
        'process.stdin.setEncoding("utf8");\n'
        'process.stdin.on("data", line => { line = line.trim(); if (line === "q") process.exit(0);\n'
        '  if (line.startsWith("late ")) { report(line.slice(5)); process.exit(0); } if (line) report(line); });\n', encoding='utf-8')
    (doubles / 'agy').write_text('#!/usr/bin/env node\nprocess.stdin.on("data", line => { if (String(line).trim() === "q") process.exit(0); });\n', encoding='utf-8')
    for name in ('opencode', 'agy'):
        (doubles / name).chmod(0o755)
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

    # The model answers every turn in words: the workers only have to start.
    class Api(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            if self.path.split('?', 1)[0] == '/v1/messages/count_tokens':
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(b'{"input_tokens":128}')
                return
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()

            def emit(kind, value):
                self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps({'type': kind, **value}) + '\n\n').encode())
                self.wfile.flush()
            emit('message_start', {'message': {'id': 'msg_t195_' + uuid.uuid4().hex, 'type': 'message', 'role': 'assistant',
                                               'model': SERVED_MODEL, 'content': [], 'stop_reason': None, 'usage': {'input_tokens': 128, 'output_tokens': 0}}})
            emit('content_block_start', {'index': 0, 'content_block': {'type': 'text', 'text': ''}})
            emit('content_block_delta', {'index': 0, 'delta': {'type': 'text_delta', 'text': '收到。'}})
            emit('content_block_stop', {'index': 0})
            emit('message_delta', {'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 5}})
            emit('message_stop', {})

    server = ThreadingHTTPServer(('127.0.0.1', 0), Api)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
    env['PATH'] = f"{doubles}:{env.get('PATH', '')}"
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', ELECTRON_RUN_AS_NODE='1',
               A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'),
               ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}', ANTHROPIC_AUTH_TOKEN=TOKEN,
               GIT_AUTHOR_NAME='t195', GIT_AUTHOR_EMAIL='t195@example.invalid',
               GIT_COMMITTER_NAME='t195', GIT_COMMITTER_EMAIL='t195@example.invalid')
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

    def link(launch):
        return request('native_link', operator, launch=launch)

    codex_home = Path(tempfile.mkdtemp(prefix='t195-codex-home-', dir='/private/tmp')).resolve()
    try:
        shutil.copyfile(Path.home() / '.codex/auth.json', codex_home / 'auth.json')
        (codex_home / 'auth.json').chmod(0o600)
        (codex_home / 'config.toml').write_text(f'[projects."{repo}"]\ntrust_level = "trusted"\n', encoding='utf-8')
        report['codex_home'] = dict(path=str(codex_home), files=['auth.json (copy)', 'config.toml (trusts the fixture repo only)'])
        config = dict(claude_bin=args.claude, codex_bin=args.codex, codex_home=str(codex_home),
                      role_card=str(source / 'workbench/roles/worker.md'), role_card_revision='t195-fixture',
                      reviewer_role_card=str(source / 'workbench/roles/reviewer.md'), reviewer_role_card_revision='t195-fixture',
                      code_revision='t195-fixture', hook_authorization='T-195 fixture: hooks only through launch arguments', turn_limit=6)
        (fixture / 'launch-config.json').write_text(json.dumps(config), encoding='utf-8')
        run_cli('daemon_start', '--launch-config', str(fixture / 'launch-config.json'))
        running = True
        wait('后台恢复结束', lambda: request('pane_layout').get('recovering') is False, 10)
        operator = json.loads((fixture / 'operator.json').read_text(encoding='utf-8'))
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=env)
        (repo / 'README.md').write_text('demo\n', encoding='utf-8')
        (repo / 'check.py').write_text('import pathlib, sys\nsys.exit(0 if pathlib.Path("hello.txt").is_file() else 1)\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True, env=env)
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'init'], check=True, env=env)
        assert request('project_open', operator, repo=str(repo))['ok']

        # 1: before the command exists (the red revision) this is where it fails.
        shell_launch = run_cli('shell_start', '--project', 'demo', '--cwd', str(repo))['launch']
        shell = shell_launch['id']
        plain = link(shell)
        report['plain_terminal'] = plain
        check('native_link_answers', plain.get('ok'), plain)
        check('plain_terminal_unavailable_with_reason', plain['link']['available'] is False and plain['link']['reason'], plain)

        def card(task, cli, model, effort):
            path = out / f'{task}.json'
            path.write_text(json.dumps(dict(id=task, source=None, goal='在仓库根目录加 hello.txt，内容一行 hello', non_goals=['不改别的文件'],
                paths=dict(allow=['hello.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
                red_commands=[], task_type='测试', repair_target=None, complexity='S',
                executor=dict(cli=cli, model=model, effort=effort), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
            return str(path)

        workers = {}
        for task, executor, model, effort in (('T-1', 'Claude Code', 'claude-haiku-5-5', 'low'), ('T-2', 'Codex', 'gpt-6.1-sol', 'low')):
            assert request('card_save', operator, task=task, project='demo', card=card(task, executor, model, effort), expected_version=0)['ok']
            assert request('create', operator, task=task, project='demo', repo=str(repo), branch='refs/heads/main', card_version=1)['ok']
            dispatched = request('dispatch', operator, task='demo+' + task, runtimeMode='workspace-write', overlap_reason='T-195 夹具：两个 worker 只为取会话号')
            assert dispatched.get('ok'), dispatched
            workers[task] = request('launch_show', operator, launch=dispatched['attempt']['runtime_identity']['launch'])['launch']

        def oracle(executor, path, workspace):
            lines = [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
            if executor == 'Claude Code':
                return {(line.get('sessionId'), line.get('cwd')) for line in lines if line.get('sessionId') and line.get('cwd') == workspace}
            first = lines[0] if lines else {}
            return {(first.get('payload', {}).get('id'), first.get('payload', {}).get('cwd'))} if first.get('type') == 'session_meta' else set()

        for task, executor in (('T-1', 'Claude Code'), ('T-2', 'Codex')):
            worker = workers[task]
            got = wait(f'{task} 的深度链接可用', lambda: (lambda value: value['link'] if value.get('ok') and value['link'].get('available') else None)(link(worker['id'])),
                       240 if executor == 'Codex' else 120)
            workspace = os.path.realpath(worker['worktree'])
            # The CLI writes its record as the session goes; give it time to write a line naming its working directory.
            deadline = time.monotonic() + 60
            while not (found := oracle(executor, got['record'], workspace)) and time.monotonic() < deadline:
                time.sleep(.5)
            report[task] = dict(link=got, workspace=workspace, record_says=sorted(map(list, found)))
            check(f'{task}_{executor.replace(" ", "_")}_link_opens_its_record', got['cli'] == executor and Path(got['record']).is_file() and
                  (got['session'], workspace) in found, report[task])
            check(f'{task}_session_is_the_clis_own', not got['session'].startswith('osc7501:') and got['session'] != worker['id'] and
                  got['text'] == f"{executor} 会话 {got['session']}，记录 {got['record']}", report[task])

        # 8, R5: the user types /clear and a new line into the Claude worker's pane: the CLI is in another session now.
        pane = request('window_open', operator, launch=workers['T-1']['id'], task=workers['T-1']['task'])
        assert pane['ok'], pane
        for sequence, data in enumerate(['/clear', '\r', 'T-195 worker /clear 之后', '\r'], 1):
            assert request('window_input', pane['identity'], sequence=sequence, request_id=str(uuid.uuid4()), data=data)['ok']
            time.sleep(1.5)
        cleared = wait('/clear 后受管 Claude 的链接置灰', lambda: (lambda value: value['link'] if not value['link']['available'] else None)(link(workers['T-1']['id'])), 90)
        report['managed_claude_clear'] = cleared
        check('managed_claude_clear_not_the_old_session', cleared['cli'] == 'Claude Code' and '换了会话' in cleared['reason'], cleared)

        # 8, R4: a second root thread of Codex in the T-2 worktree.
        bound = report['T-2']['link']['session']
        other = str(uuid.uuid4())
        day = codex_home / 'sessions' / time.strftime('%Y/%m/%d')
        day.mkdir(parents=True, exist_ok=True)
        (day / f'rollout-{time.strftime("%Y-%m-%dT%H-%M-%S")}-{other}.jsonl').write_text(json.dumps(dict(timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            type='session_meta', payload=dict(id=other, cwd=report['T-2']['workspace'], source='cli', originator='codex_cli_rs'))) + '\n', encoding='utf-8')
        second_rollout = next(day.glob(f'rollout-*-{other}.jsonl'))
        second = link(workers['T-2']['id'])['link']
        report['managed_codex_second_thread'] = dict(bound=bound, other=other, link=second)
        check('managed_codex_second_thread_not_the_bound_one', second['available'] is False and other in second['reason'], report['managed_codex_second_thread'])
        second_rollout.unlink()
        # 5-7: a project terminal, through its window as the user types into it.
        window = request('window_open', operator, launch=shell, project='demo')
        assert window['ok'], window
        typed = dict(sequence=0)

        def type_in(data):
            typed['sequence'] += 1
            sent = request('window_input', window['identity'], sequence=typed['sequence'], request_id=str(uuid.uuid4()), data=data)
            assert sent['ok'], sent

        def submit(text):
            type_in(text)
            time.sleep(1)
            type_in('\r')

        def screen():
            raw = (state / 'traces' / shell / 'pty.raw').read_text(encoding='utf-8', errors='replace')
            return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

        def shell_link(predicate, label, timeout=60):
            return wait(label, lambda: (lambda value: value['link'] if value.get('ok') and predicate(value['link']) else None)(link(shell)), timeout)

        def claude_session_of(prompt):
            # Claude Code's own record: the session file whose lines carry this prompt.
            return sorted({line['sessionId'] for path in (home / '.claude/projects').glob('*/*.jsonl')
                           for line in map(json.loads, filter(str.strip, path.read_text(encoding='utf-8').splitlines()))
                           if prompt in json.dumps(line, ensure_ascii=False) and line.get('sessionId')})

        type_in('claude --model claude-haiku-5-5\r')
        wait('终端里的 Claude 启动', lambda: 'ClaudeCodev' in screen() and '❯' in screen()[screen().index('ClaudeCodev'):], 60)
        before = link(shell)['link']
        first, second = 'T-195 终端第一句', 'T-195 /clear 之后第二句'
        submit(first)
        got_first = shell_link(lambda value: value['available'], 'Claude 报来会话号')
        first_sessions = wait('Claude 记下第一句', lambda: claude_session_of(first), 30)
        type_in('/clear')
        time.sleep(1)
        type_in('\r')
        time.sleep(2)
        submit(second)
        got_second = shell_link(lambda value: value['available'] and value['session'] != got_first['session'], '/clear 后的新会话号')
        second_sessions = wait('Claude 记下第二句', lambda: claude_session_of(second), 30)
        report['terminal_claude'] = dict(before=before, first=got_first, first_record_says=first_sessions, second=got_second, second_record_says=second_sessions)
        check('terminal_claude_unavailable_before_it_reports', before['available'] is False and before['cli'] == 'Claude Code' and before['reason'], before)
        check('terminal_claude_follows_clear', first_sessions == [got_first['session']] and second_sessions == [got_second['session']] and
              Path(got_second['record']).name == got_second['session'] + '.jsonl' and Path(got_second['record']).is_file(), report['terminal_claude'])
        type_in('/exit\r')
        exited = shell_link(lambda value: value['cli'] is None, 'Claude 退出后前台为空', 30)
        check('terminal_link_ends_with_the_cli', exited['available'] is False and exited['reason'], exited)

        # 6: opencode in the terminal reports its session id; the link stays grey, saying why.
        store = home / '.local/share/opencode'
        store.mkdir(parents=True)
        subprocess.run(['sqlite3', str(store / 'opencode.db'), "CREATE TABLE session_v2 (id text PRIMARY KEY); INSERT INTO session_v2 VALUES ('ses_first');"], check=True)
        type_in('opencode\r')
        shell_link(lambda value: value['cli'] == 'opencode', 'opencode 在前台', 30)
        submit('ses_first')
        # The report reached the daemon: the terminal's turn state carries the id.
        reported = wait('opencode 的报告到了后台', lambda: (lambda turn: turn if turn and turn.get('id') == 'ses_first' else None)(
            request('pane_status', thread=shell_launch['thread']).get('cli_turn')), 30)
        opencode_link = link(shell)['link']
        type_in('q\r')
        report['terminal_opencode'] = dict(reported=reported, link=opencode_link)
        check('terminal_opencode_unavailable_with_reason', opencode_link['available'] is False and opencode_link['cli'] == 'opencode' and
              '不带进程' in opencode_link['reason'], report['terminal_opencode'])

        # 7 / R3: agy's conversation files, as agy keeps them: one SQLite file per conversation naming its working directory.
        # In a terminal none of them is known to be this run's, even the only one for the directory.
        conversations = home / '.gemini/antigravity-cli/conversations'
        conversations.mkdir(parents=True)
        subprocess.run(['sqlite3', str(conversations / 'conv-one.db'),
                        f"CREATE TABLE trajectory_metadata_blob (id text PRIMARY KEY, data blob); INSERT INTO trajectory_metadata_blob VALUES ('main', CAST('workspace file://{repo} end' AS BLOB));"], check=True)
        shell_link(lambda value: value['cli'] is None, 'opencode 退出', 30)
        type_in('agy\r')
        agy = shell_link(lambda value: value['cli'] == 'agy', 'agy 在前台')
        type_in('q\r')
        report['terminal_agy'] = agy
        check('terminal_agy_unavailable_with_reason', agy['available'] is False and '不报会话号' in agy['reason'], agy)

        # 9, M1: a rollout of another thread in the same worktree, last written before the worker started, is not this run's.
        again = wait('删掉第二个线程后 T-2 的链接恢复', lambda: (lambda value: value if value['available'] else None)(link(workers['T-2']['id'])['link']), 30)
        older = str(uuid.uuid4())
        older_rollout = day / f'rollout-older-{older}.jsonl'
        older_rollout.write_text(json.dumps(dict(type='session_meta', payload=dict(id=older, cwd=report['T-2']['workspace'], source='cli'))) + '\n', encoding='utf-8')
        launched = datetime.fromisoformat(workers['T-2']['created_at'].replace('Z', '+00:00')).timestamp()
        os.utime(older_rollout, (launched - 3600, launched - 3600))
        with_older = link(workers['T-2']['id'])
        report['managed_codex_older_rollout'] = dict(again=again, older=older, answer=with_older)
        check('managed_codex_older_rollout_not_counted', with_older.get('ok') and with_older['link']['available'] and
              with_older['link']['session'] == bound, report['managed_codex_older_rollout'])

        # 9, F4: a rollout written since the launch that cannot be opened: the current thread is unknown, so the link is grey.
        locked = day / f'rollout-locked-{uuid.uuid4()}.jsonl'
        locked.write_text(json.dumps(dict(type='session_meta', payload=dict(id=str(uuid.uuid4()), cwd='/elsewhere', source='cli'))) + '\n', encoding='utf-8')
        locked.chmod(0)
        try:
            unreadable = link(workers['T-2']['id'])
        finally:
            locked.chmod(0o600)
        report['managed_codex_unreadable_rollout'] = unreadable
        check('managed_codex_unreadable_rollout_grey', unreadable.get('ok') and unreadable['link']['available'] is False and
              '读不了' in unreadable['link']['reason'] and str(locked) in unreadable['link']['reason'], unreadable)
        locked.unlink()

        # 10, R4-F1: the scan reaches tomorrow; tomorrow's day directory is there but cannot be looked into (its real place
        # is under a directory without search permission). Codex may have written there, so the current thread is unknown.
        before_day = link(workers['T-2']['id'])
        tomorrow = datetime.now() + timedelta(days=1)
        next_day = codex_home / 'sessions' / tomorrow.strftime('%Y/%m/%d')
        next_day.parent.mkdir(parents=True, exist_ok=True)
        hidden = fixture / 'hidden'
        (hidden / 'day').mkdir(parents=True)
        next_day.symlink_to(hidden / 'day', target_is_directory=True)
        hidden.chmod(0)
        try:
            unsearchable = link(workers['T-2']['id'])
        finally:
            hidden.chmod(0o700)
            next_day.unlink()
        report['managed_codex_unsearchable_day'] = dict(before=before_day, during=unsearchable)
        check('managed_codex_unsearchable_day_grey', before_day.get('ok') and before_day['link']['available'] and unsearchable.get('ok') and
              unsearchable['link']['available'] is False and '读不了' in unsearchable['link']['reason'] and str(next_day) in unsearchable['link']['reason'],
              report['managed_codex_unsearchable_day'])
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
            # The Codex worker may still be exiting after daemon_stop and would write its home again; remove it once nothing
            # runs with it, and look again after that.
            deadline = time.monotonic() + 60
            while subprocess.run(['pgrep', '-f', str(codex_home)], capture_output=True).returncode == 0 and time.monotonic() < deadline:
                time.sleep(1)
            shutil.rmtree(codex_home, ignore_errors=True)
            time.sleep(2)
            if 'codex_home' in report:
                report['codex_home']['removed'] = not codex_home.exists()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
