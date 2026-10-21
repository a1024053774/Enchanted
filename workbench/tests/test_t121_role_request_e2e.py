"""T-121：项目终端里经角色申请成为主控。真实 CLI 入口、后台、socket、zsh（经 ZDOTDIR 引导）与 `a2a` 命令；
用夹具 claude 记录包装命令转发的参数，不调用模型。

失败方式（先列再写）：
1. 终端里没有 `a2a`，或者用户的 .zshrc 把自己的目录排到前面，包装命令被跳过。
2. 包装命令丢了用户参数，或者没加 --plugin-dir。
3. 打包版后台的 ELECTRON_RUN_AS_NODE 传进用户的 shell。
4. 用户的启动文件没加载（.zshenv/.zshrc 里的变量不在），或者被改写了；用户自己在 .zshenv 里设的
   ZDOTDIR（XDG 写法）启动后丢了；历史写进应用资源目录。
5. 没申请、待批准、被拒绝、已结束的终端还能用主控命令。
6. 已批准的角色越出本项目：调用不带项目的命令（收件箱、stop）或别的项目。
7. 两个终端同时拿到同一项目的同一角色；一个终端申请两个角色。
8. 伪造或借用别的终端的令牌能冒充；终端或窗口身份能自己批准申请。
9. 申请者不等了（超时、被杀），申请仍可被批准。
10. 终端关闭后身份仍在，侧栏仍显示主控。
--revision 在该版本的隔离源码上跑同一场景（修前应失败）。
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
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    # Known-bad: a pending roleRequest already grants the role's authority.
    # Known-bad: history follows macOS /etc/zshrc into Enchanted's ZDOTDIR.
    # Known-bad: a killed asker leaves its request approvable; the user's own ZDOTDIR is dropped.
    target.add_argument('--mutant', choices=['pending-authority', 'history-in-zdotdir', 'no-withdraw', 'zdotdir-dropped', 'refusal-unrecorded', 'task-widens-scope',
                                                 'drafts-unowned', 'foreign-owned-save', 'approved-not-ended', 'grant-has-authority',
                                                 'rivals-left-pending', 'expiry-unrecorded', 'stale-notice'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t121-', dir='/private/tmp')).resolve()
    state, home, cwd, out = fixture / 'state', fixture / 'home', fixture / 'proj', fixture / 'out'
    other_repo = fixture / 'other'
    for path in (state, home, cwd, out, home / 'userbin', other_repo):
        path.mkdir()
    # The user's own startup files: .zshrc puts its own bin first, like a real setup.
    user_files = {'.zshenv': 'export T121_ZSHENV=loaded\n[[ -f $HOME/use-xdg ]] && ZDOTDIR=$HOME/.config/zsh\n',
                  '.config/zsh/.zshrc': "PS1='T121% '\nexport T121_XDG_ZSHRC=loaded\n",
                  '.zshrc': "PS1='T121% '\npath=($HOME/userbin $path)\nexport T121_ZSHRC=loaded\n"}
    for name, text in user_files.items():
        (home / name).parent.mkdir(parents=True, exist_ok=True)
        (home / name).write_text(text, encoding='utf-8')
    fake = home / 'userbin/claude'
    fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$T121_ARGV"\n', encoding='utf-8')
    fake.chmod(0o755)
    source = ROOT
    if args.revision:
        source = fixture / 'source'
        for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', args.revision, 'workbench/src', 'workbench/terminal'],
                                            cwd=ROOT, text=True).splitlines():
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(subprocess.check_output(['git', 'show', f'{args.revision}:{name}'], cwd=ROOT))
            if name.startswith('workbench/terminal/bin/'):
                target.chmod(0o755)
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', ELECTRON_RUN_AS_NODE='1',
               T121_ARGV=str(out / 'claude-argv.txt'), A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'))
    env.pop('ZDOTDIR', None)
    if args.mutant:
        source = fixture / 'source'
        for name in ('src', 'terminal'):
            shutil.copytree(ROOT / 'workbench' / name, source / 'workbench' / name, symlinks=True)
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
        if args.mutant == 'pending-authority':
            path = source / 'workbench/src/daemon.ts'
            old, new = ('const roleRequest: RoleRequest | undefined = roleRequests.approved(terminal.id);',
                        'const roleRequest: RoleRequest | undefined = roleRequests.current(terminal.id);')
        elif args.mutant == 'history-in-zdotdir':
            path = source / 'workbench/terminal/zdotdir/.zshrc'
            old, new = '[[ $HISTFILE == $A2A_TERMINAL_ZDOTDIR/.zsh_history ]] && HISTFILE=$ZDOTDIR/.zsh_history\n', ''
        elif args.mutant == 'no-withdraw':
            path = source / 'workbench/src/daemon.ts'
            old, new = 'try { asker.gone?.(); }', 'try { }'
        elif args.mutant == 'task-widens-scope':
            # The first candidate's rule: any command with a task of this project passes.
            path = source / 'workbench/src/daemon.ts'
            old, new = '} else if (taskCommands.has(input.command)) {', '} else if (input.task !== undefined) {'
        elif args.mutant == 'drafts-unowned':
            # Drop the ownership check of card_show and create (card_save keeps its own checks).
            path = source / 'workbench/src/daemon.ts'
            old, new = 'if (draftOwner(input.task) !== roleRequest.project) throw new Refusal("card_draft_not_owned");', ''
        elif args.mutant == 'foreign-owned-save':
            path = source / 'workbench/src/daemon.ts'
            old, new = 'if (owner !== undefined && owner !== roleRequest.project) throw new Refusal("card_draft_not_owned");', ''
        elif args.mutant == 'approved-not-ended':
            path = source / 'workbench/src/daemon.ts'
            old, new = 'else if (current.state === "granted") roleRequests.end(terminal.id, "asker_gone");', ''
        elif args.mutant == 'grant-has-authority':
            path = source / 'workbench/src/roleRequests.ts'
            old, new = 'return roleRequest?.state === "approved" ? roleRequest : undefined;', \
                'return roleRequest?.state === "approved" || roleRequest?.state === "granted" ? roleRequest : undefined;'
        elif args.mutant == 'rivals-left-pending':
            path = source / 'workbench/src/roleRequests.ts'
            old, new = 'this.store.event("role_request_decided", { role_request: other.id, approved: false, reason: "role_given_to_other" }', 'void ({ role_request: other.id }'
        elif args.mutant == 'expiry-unrecorded':
            path = source / 'workbench/src/roleRequests.ts'
            old, new = 'if (granted?.state === "granted") this.store.event(', 'if (false) this.store.event('
        elif args.mutant == 'stale-notice':
            path = source / 'workbench/src/sidebar.ts'
            old, new = ' &&\n    !current.some(later => later.launch === row.launch && Date.parse(later.requested_at) > Date.parse(row.requested_at)))', ')'
        elif args.mutant == 'refusal-unrecorded':
            path = source / 'workbench/src/daemon.ts'
            old, new = 'store.event("request_rejected", ', 'void ('
        else:
            path = source / 'workbench/terminal/zdotdir/.zlogin'
            old, new = ' || $A2A_USER_ZDOTDIR != $HOME', ''
        text = path.read_text(encoding='utf-8')
        assert text.count(old) == 1, '变异定位必须唯一'
        path.write_text(text.replace(old, new), encoding='utf-8')
    cli = source / 'workbench/src/gates/cli.ts'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, fixture=str(fixture), checks=[])
    running = False

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def run_cli(*arguments):
        run = subprocess.run(['node', str(cli), '--state', str(state), *arguments], env=env,
                             capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, f'{arguments[0]}: {run.stderr or run.stdout}'
        return json.loads(run.stdout)

    def request(command, identity=None, **data):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(30)
            connection.connect(str(state / 'control.sock'))
            payload = dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)
            connection.sendall((json.dumps(payload) + '\n').encode())
            response = b''
            while b'\n' not in response:
                part = connection.recv(65536)
                assert part, 'daemon 在回执前断开'
                response += part
        return json.loads(response.split(b'\n', 1)[0])

    def output(launch):
        result = request('pane_output', launch=launch, offset=0)
        assert result['ok'], result
        text = base64.b64decode(result['data_base64']).decode('utf-8', 'replace')
        return re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))', '', text)

    terminals = {}

    def open_terminal(name, project='proj', directory=None):
        launch = run_cli('shell_start', '--project', project, '--cwd', str(directory or cwd))['launch']
        opened = request('window_open', operator, launch=launch['id'], project=project)
        assert opened['ok'], opened
        terminals[name] = dict(launch=launch['id'], identity=opened['identity'], sequence=0)
        return terminals[name]

    def type_line(terminal, line, marker, timeout=30):
        terminal['sequence'] += 1
        sent = request('window_input', terminal['identity'], sequence=terminal['sequence'],
                       request_id=str(uuid.uuid4()), data=f'{line}; print -r -- "{marker}=$?"\r')
        assert sent['ok'], sent
        deadline = time.monotonic() + timeout
        while True:
            found = re.search(rf'^{marker}=(\d+)\r?$', output(terminal['launch']), re.M)
            if found:
                return int(found.group(1))
            assert time.monotonic() < deadline, f'终端没有输出 {marker}'
            time.sleep(.1)

    def result_file(name):
        return json.loads((out / name).read_text(encoding='utf-8'))

    def ask(identity, role):
        asker = socket.socket(socket.AF_UNIX)
        asker.connect(str(state / 'control.sock'))
        asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role=role, wait_seconds=60),
                                       identity=identity)) + '\n').encode())
        return asker

    def answer(asker):
        response = b''
        while b'\n' not in response:
            part = asker.recv(65536)
            assert part, '申请连接在回执前断开'
            response += part
        asker.close()
        return json.loads(response.split(b'\n', 1)[0])

    def wait_pending(project_role, timeout=20):
        deadline = time.monotonic() + timeout
        while True:
            roleRequests = request('sidebar_snapshot').get('role_requests') or []
            match = [roleRequest for roleRequest in roleRequests if (roleRequest['project'], roleRequest['role']) == project_role]
            if match:
                return match
            assert time.monotonic() < deadline, f'后台没有出现待批准的申请 {project_role}'
            time.sleep(.2)

    try:
        run_cli('daemon_start')
        running = True
        deadline = time.monotonic() + 10
        while request('pane_layout').get('recovering') is not False:
            assert time.monotonic() < deadline, '后台恢复未结束'
            time.sleep(.05)
        operator = json.loads((fixture / 'operator.json').read_text(encoding='utf-8'))
        a = open_terminal('a')

        # 1-4: the terminal environment.
        type_line(a, f'print -r -- "${{path[1]}}|${{ELECTRON_RUN_AS_NODE-<unset>}}|${{T121_ZSHENV-}}|${{T121_ZSHRC-}}|${{ZDOTDIR-<unset>}}|${{HISTFILE-<unset>}}|$A2A_TERMINAL_TOKEN" > {out}/env.txt', 'T121-ENV')
        first, run_as_node, zshenv, zshrc, zdotdir, histfile, token_a = (out / 'env.txt').read_text(encoding='utf-8').strip().split('|')
        report['terminal_env'] = dict(path_first=first, electron_run_as_node=run_as_node, zshenv=zshenv, zshrc=zshrc, zdotdir=zdotdir, histfile=histfile)
        check('a2a_command_first_on_path', first.endswith('/workbench/terminal/bin') and (Path(first) / 'a2a').exists(), first)
        check('electron_run_as_node_removed', run_as_node == '<unset>', run_as_node)
        check('user_startup_files_loaded', zshenv == 'loaded' and zshrc == 'loaded', (zshenv, zshrc))
        check('zdotdir_restored_after_startup', zdotdir == '<unset>', zdotdir)
        # macOS /etc/zshrc derives HISTFILE from ZDOTDIR; it must name the user's own history file.
        check('history_goes_to_user_home', histfile == f'{home}/.zsh_history', histfile)
        check('user_startup_files_unchanged', all((home / name).read_text(encoding='utf-8') == text for name, text in user_files.items()))
        assert type_line(a, "claude --model 'x y' -p hello", 'T121-SHIM') == 0
        forwarded = (out / 'claude-argv.txt').read_text(encoding='utf-8').splitlines()
        report['claude_argv'] = forwarded
        check('claude_shim_adds_plugin_and_keeps_arguments', forwarded[:1] == ['--plugin-dir'] and
              forwarded[1].endswith('/workbench/terminal/plugin/enchanted-a2a') and forwarded[2:] == ['--model', 'x y', '-p', 'hello'], forwarded)

        # 5: no identity yet.
        code = type_line(a, f"a2a call '{{\"command\":\"inbox_list\"}}' > {out}/a-no-role.json", 'T121-NO-ROLE')
        check('controller_command_refused_without_role', code == 1 and result_file('a-no-role.json')['error'] == 'approved_role_required',
              result_file('a-no-role.json'))
        assert type_line(a, f'a2a whoami > {out}/a-whoami-0.json', 'T121-WHO0') == 0
        check('whoami_reports_project_without_role', result_file('a-whoami-0.json')['project'] == 'proj' and result_file('a-whoami-0.json')['role'] is None)

        # Request and approve: the request command waits for the user's decision.
        type_line(a, f'(a2a request executor > {out}/a-request.json 2>/dev/null; print $? > {out}/a-request.exit) &!', 'T121-REQUEST-SENT')
        [pending] = wait_pending(('proj', 'executor'))
        check('pending_request_names_terminal_and_role', pending['launch'] == a['launch'] and pending['role_label'] == '执行主控', pending)
        code = type_line(a, f"a2a call '{{\"command\":\"inbox_list\"}}' > {out}/a-pending.json", 'T121-PENDING')
        check('pending_request_has_no_authority', code == 1 and result_file('a-pending.json')['error'] == 'approved_role_required')
        # The window identity stops at the window command allow-list; the terminal one at the gate scope.
        by_window = request('role_request_decide', a['identity'], role_request=pending['id'], approved=True)
        check('window_identity_cannot_decide', by_window.get('error') == 'window_command_forbidden', by_window)
        by_terminal = request('role_request_decide', dict(kind='terminal', launch=a['launch'], token=token_a), role_request=pending['id'], approved=True)
        check('pending_terminal_cannot_decide', by_terminal.get('error') == 'approved_role_required', by_terminal)
        decided = request('role_request_decide', operator, role_request=pending['id'], approved=True)
        assert decided['ok'] and decided['role_request']['state'] == 'granted', decided
        deadline = time.monotonic() + 15
        while not (out / 'a-request.exit').exists():
            assert time.monotonic() < deadline, 'a2a request 没有在批准后返回'
            time.sleep(.1)
        check('request_command_returns_after_approval', (out / 'a-request.exit').read_text().strip() == '0' and
              result_file('a-request.json')['role_request']['state'] == 'approved')
        assert type_line(a, f'a2a whoami > {out}/a-whoami-1.json', 'T121-WHO1') == 0
        check('whoami_reports_approved_role', result_file('a-whoami-1.json')['role'] == 'executor')
        # inbox_ready names its project; with no tasks in it the gate itself answers unknown_project.
        code = type_line(a, f"a2a call '{{\"command\":\"inbox_ready\",\"project\":\"proj\"}}' > {out}/a-approved.json", 'T121-APPROVED')
        check('approved_controller_command_reaches_gate', code == 1 and result_file('a-approved.json')['error'] == 'unknown_project',
              result_file('a-approved.json'))
        code = type_line(a, f"a2a call '{{\"command\":\"inbox_ready\",\"project\":\"other\"}}' > {out}/a-other.json", 'T121-OTHER')
        check('approved_role_limited_to_its_project', code == 1 and result_file('a-other.json')['error'] == 'role_project_mismatch')
        unscoped = {}
        for name, command in [('inbox_list', '{"command":"inbox_list"}'), ('inbox_ack', '{"command":"inbox_ack","id":"x"}'),
                              ('stop', '{"command":"stop","thread":"x","stop_id":"x"}'),
                              ('decide', '{"command":"role_request_decide","role_request":"x","approved":true}')]:
            type_line(a, f"a2a call '{command}' > {out}/a-unscoped-{name}.json", f'T121-UNSCOPED-{name.upper()}')
            unscoped[name] = result_file(f'a-unscoped-{name}.json').get('error')
        report['unscoped_errors'] = unscoped
        check('commands_without_project_refused', set(unscoped.values()) == {'role_command_not_scoped'}, unscoped)

        # 5b: tasks. The terminal controller prepares and creates a task in its own opened project; a task
        # field never widens inbox or stop, and another project's task and repo stay out of reach.
        git_env = dict(env, GIT_AUTHOR_NAME='t121', GIT_AUTHOR_EMAIL='t121@example.invalid',
                       GIT_COMMITTER_NAME='t121', GIT_COMMITTER_EMAIL='t121@example.invalid')
        for repo in (cwd, other_repo):
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=git_env)
            (repo / 'check.py').write_text('print("ok")\n', encoding='utf-8')
            subprocess.run(['git', '-C', str(repo), 'add', 'check.py'], check=True, env=git_env)
            subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'init'], check=True, env=git_env)
            assert request('project_open', operator, repo=str(repo))['ok']
        terminal_a = dict(kind='terminal', launch=a['launch'], token=token_a)

        def card(task):
            path = out / f'{task}.card.json'
            path.write_text(json.dumps(dict(id=task, source=None, goal='T-121 夹具任务', non_goals=['无'],
                paths=dict(allow=['check.py'], deny=[]), oracle_paths=['check.py'],
                completion_conditions=[dict(argv=['python3', 'check.py'])], red_commands=[], task_type='测试',
                repair_target=None, complexity='S', executor=dict(cli='Codex', model='m', effort='high'),
                base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
            return str(path)

        def create(identity, task, project, repo):
            saved = request('card_save', identity, task=task, card=card(task), expected_version=0)
            if not saved['ok']:
                return saved
            return request('create', identity, task=task, project=project, repo=str(repo), branch='refs/heads/main', card_version=1)

        assert create(operator, 'other-1', 'other', other_repo)['ok']
        own = create(terminal_a, 'own-1', 'proj', cwd)
        check('terminal_controller_creates_task_in_own_project', own['ok'] and request('status', terminal_a, task='own-1')['ok'], own)
        wrong_repo = create(terminal_a, 'own-2', 'proj', other_repo)
        assert request('card_save', terminal_a, task='own-3', card=card('own-3'), expected_version=0)['ok']
        foreign = {label: request(command, terminal_a, **data).get('error') for label, command, data in [
            ('create_in_other_project', 'create', dict(task='own-3', project='other', repo=str(other_repo), branch='refs/heads/main', card_version=1)),
            ('status_of_other_task', 'status', dict(task='other-1')),
            ('card_save_on_other_task', 'card_save', dict(task='other-1', card=card('other-1'), expected_version=1))]}
        foreign['create_with_other_repo'] = wrong_repo.get('error')
        report['foreign_errors'] = foreign
        check('other_project_task_and_repo_refused', foreign == dict(create_in_other_project='role_project_mismatch',
              status_of_other_task='role_project_mismatch', card_save_on_other_task='role_project_mismatch',
              create_with_other_repo='project_repo_mismatch'), foreign)
        widened = {name: request(name, terminal_a, task='own-1', **data).get('error') for name, data in [
            ('inbox_list', {}), ('inbox_ack', dict(id='x')), ('inbox_send', dict(to='executor', kind='note', body='x')),
            ('stop', dict(thread='x', stop_id='x'))]}
        report['task_field_errors'] = widened
        check('task_field_does_not_widen_scope', set(widened.values()) == {'role_command_not_scoped'}, widened)
        # A draft another project saved for a task it has not created yet stays that project's.
        assert request('card_save', operator, task='other-2', card=card('other-2'), expected_version=0)['ok']
        drafts = {label: request(command, terminal_a, task='other-2', **data).get('error') for label, command, data in [
            ('card_show', 'card_show', dict(card_version=1)),
            ('card_save_next', 'card_save', dict(card=card('other-2'), expected_version=1)),
            ('card_save_first', 'card_save', dict(card=card('other-2'), expected_version=0)),
            ('create', 'create', dict(project='proj', repo=str(cwd), branch='refs/heads/main', card_version=1))]}
        report['draft_errors'] = drafts
        check('other_project_draft_refused', drafts == dict(card_show='card_draft_not_owned', card_save_next='card_draft_not_owned',
              card_save_first='card_version_conflict', create='card_draft_not_owned') and
              request('create', operator, task='other-2', project='other', repo=str(other_repo), branch='refs/heads/main', card_version=1)['ok'], drafts)
        # A draft another project's terminal saved first stays that project's.
        o = open_terminal('o', 'other', other_repo)
        type_line(o, f'print -r -- $A2A_TERMINAL_TOKEN > {out}/o-token.txt', 'T121-O-TOKEN')
        terminal_o = dict(kind='terminal', launch=o['launch'], token=(out / 'o-token.txt').read_text(encoding='utf-8').strip())
        asker = ask(terminal_o, 'executor')
        [waiting_o] = wait_pending(('other', 'executor'))
        assert request('role_request_decide', operator, role_request=waiting_o['id'], approved=True)['ok']
        assert answer(asker)['ok'] and request('role_request_confirm', terminal_o, role_request=waiting_o['id'])['ok']
        assert request('card_save', terminal_o, task='oth-3', card=card('oth-3'), expected_version=0)['ok']
        squatted = {label: request(command, terminal_a, task='oth-3', **data).get('error') for label, command, data in [
            ('card_save_next', 'card_save', dict(card=card('oth-3'), expected_version=1)),
            ('card_show', 'card_show', dict(card_version=1))]}
        report['other_terminal_draft_errors'] = squatted
        check('other_terminal_draft_refused', set(squatted.values()) == {'card_draft_not_owned'} and
              request('card_show', terminal_o, task='oth-3', card_version=1)['ok'], squatted)
        no_runtime = {command: request(command, terminal_a, task='own-1').get('error') for command in ('answer_issue', 'answer_issues', 'attach', 'run')}
        check('user_answer_and_run_commands_not_for_terminals', set(no_runtime.values()) == {'role_command_not_scoped'}, no_runtime)
        code = type_line(a, f"a2a call '{{\"command\":\"status\",\"task\":\"no-such-task\"}}' > {out}/a-task.json", 'T121-TASK')
        check('unknown_task_refused_before_gate', code == 1 and result_file('a-task.json')['ok'] is False, result_file('a-task.json'))
        code = type_line(a, f'a2a request ideation > {out}/a-second.json', 'T121-SECOND')
        check('one_role_per_terminal', code == 1 and result_file('a-second.json')['error'] == 'role_already_held')
        sidebar = request('sidebar_snapshot')
        rows = [agent for agent in sidebar['agents'] if agent['id'] == a['launch']]
        check('sidebar_shows_requested_controller', len(rows) == 1 and rows[0]['role_label'] == '执行主控' and rows[0]['terminal'] is True, rows)

        # 6: a second terminal in the same project.
        b = open_terminal('b')
        code = type_line(b, f'a2a request executor > {out}/b-taken.json', 'T121-TAKEN')
        check('role_held_by_one_terminal_per_project', code == 1 and result_file('b-taken.json')['error'] == 'role_taken')
        type_line(b, f'(a2a request ideation > {out}/b-request.json 2>/dev/null; print $? > {out}/b-request.exit) &!', 'T121-B-SENT')
        [pending_b] = wait_pending(('proj', 'ideation'))
        assert request('role_request_decide', operator, role_request=pending_b['id'], approved=False)['ok']
        deadline = time.monotonic() + 15
        while not (out / 'b-request.exit').exists():
            assert time.monotonic() < deadline, 'a2a request 没有在拒绝后返回'
            time.sleep(.1)
        check('rejected_request_returns_failure', (out / 'b-request.exit').read_text().strip() == '1' and
              result_file('b-request.json')['error'] == 'request_rejected')
        code = type_line(b, f"a2a call '{{\"command\":\"inbox_list\"}}' > {out}/b-rejected.json", 'T121-B-REJECTED')
        check('rejected_terminal_has_no_authority', code == 1 and result_file('b-rejected.json')['error'] == 'approved_role_required')
        again = request('role_request_decide', operator, role_request=pending_b['id'], approved=True)
        check('decided_request_cannot_be_redecided', again['ok'] is False and again['error'] == 'request_not_pending', again)
        rejected = [event for event in request('orchestration_events')['events'] if event['type'] == 'role_request_decided'
                    and event['data']['role_request'] == pending_b['id']]
        check('rejection_recorded', len(rejected) == 1 and rejected[0]['data']['approved'] is False and rejected[0]['launch'] == b['launch'], rejected)
        # Controller commands refused for want of a role are recorded with the terminal that sent them.
        events = request('orchestration_events')['events']
        senders = {event['data']['id']: event['data']['source'] for event in events if event['type'] == 'request_received'}
        refused = [(senders.get(event['data']['id']), event['data']['input']['command']) for event in events
                   if event['type'] == 'request_rejected' and event['data']['result']['error'] == 'approved_role_required']
        check('role_refusals_recorded', refused.count(('terminal:' + a['launch'], 'inbox_list')) >= 2 and
              ('terminal:' + b['launch'], 'inbox_list') in refused, refused)

        # 7: forged or borrowed identities.
        forged = request('inbox_list', dict(kind='terminal', launch=a['launch'], token='0' * 64))
        borrowed = request('inbox_list', dict(kind='terminal', launch=b['launch'], token=token_a))
        check('forged_and_borrowed_tokens_refused', forged.get('ok') is False and borrowed.get('ok') is False and
              'invalid_terminal_identity' in json.dumps([forged, borrowed]), [forged, borrowed])
        anonymous = request('role_request', None, role='executor', wait_seconds=5)
        check('anonymous_request_refused', anonymous['ok'] is False, anonymous)

        # 7b: a request exists only while its asker waits on the connection.
        type_line(b, f'print -r -- $A2A_TERMINAL_TOKEN > {out}/b-token.txt', 'T121-B-TOKEN')
        terminal_b = dict(kind='terminal', launch=b['launch'], token=(out / 'b-token.txt').read_text(encoding='utf-8').strip())
        unwaited = request('role_request', terminal_b, role='ideation')
        check('request_without_wait_refused', unwaited.get('error') == 'invalid_wait_seconds' and
              not [row for row in request('sidebar_snapshot').get('role_requests') or [] if row['launch'] == b['launch']], unwaited)
        late_decisions = []
        for _ in range(3):
            asker = socket.socket(socket.AF_UNIX)
            asker.connect(str(state / 'control.sock'))
            asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role='ideation', wait_seconds=60),
                                           identity=terminal_b)) + '\n').encode())
            [waiting] = wait_pending(('proj', 'ideation'))
            asker.close()
            late_decisions.append(request('role_request_decide', operator, role_request=waiting['id'], approved=True).get('error'))
        check('closed_asker_cannot_be_approved', late_decisions == ['request_not_pending'] * 3 and
              request('terminal_whoami', terminal_b)['role'] is None, late_decisions)
        # Approved, then the asker dies before reading the answer: the role ends with it.
        unreceived = []
        for _ in range(3):
            asker = socket.socket(socket.AF_UNIX)
            asker.connect(str(state / 'control.sock'))
            asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role='ideation', wait_seconds=60),
                                           identity=terminal_b)) + '\n').encode())
            [waiting] = wait_pending(('proj', 'ideation'))
            assert request('role_request_decide', operator, role_request=waiting['id'], approved=True)['ok']
            asker.close()
            deadline = time.monotonic() + 5
            while request('terminal_whoami', terminal_b)['role'] is not None and time.monotonic() < deadline:
                time.sleep(.1)
            row = [r for r in request('terminal_whoami', terminal_b)['role_requests'] if r['id'] == waiting['id']][0]
            unreceived.append((row['state'], row['ended_reason']))
        check('unreceived_approval_ends', unreceived == [('ended', 'asker_gone')] * 3, unreceived)
        # The user's approval grants the role; only the asker's confirmation makes it take effect.
        # Two terminals ask for the same role. Granting one leaves the other pending until the
        # grant is confirmed; an unconfirmed grant expires (recorded) and the role is free again.
        d = open_terminal('d')
        type_line(d, f'print -r -- $A2A_TERMINAL_TOKEN > {out}/d-token.txt', 'T121-D-TOKEN')
        terminal_d = dict(kind='terminal', launch=d['launch'], token=(out / 'd-token.txt').read_text(encoding='utf-8').strip())

        def pending_of(terminal):
            return [row for row in request('sidebar_snapshot').get('role_requests') or [] if row['launch'] == terminal['launch']]

        ask_b = ask(terminal_b, 'ideation')
        wait_pending(('proj', 'ideation'))
        ask_d = ask(terminal_d, 'ideation')
        deadline = time.monotonic() + 15
        while not pending_of(d):
            assert time.monotonic() < deadline, '第二个申请没有出现'
            time.sleep(.2)
        [first] = pending_of(b)
        assert request('role_request_decide', operator, role_request=first['id'], approved=True)['ok']
        granted = answer(ask_b)
        unconfirmed = dict(answer=granted['role_request']['state'], role=request('terminal_whoami', terminal_b)['role'],
                           call=request('status', terminal_b, task='own-1').get('error'),
                           sidebar=[agent['id'] for agent in request('sidebar_snapshot')['agents'] if agent['id'] == b['launch']],
                           shown_as_granted=[row['id'] for row in request('sidebar_snapshot').get('granted_role_requests') or []],
                           rival_pending=len(pending_of(d)), rival_decide=request('role_request_decide', operator,
                               role_request=pending_of(d)[0]['id'], approved=True).get('error') if pending_of(d) else 'rival_already_settled')
        time.sleep(16)
        expired = [event['data']['reason'] for event in request('orchestration_events')['events']
                   if event['type'] == 'role_request_ended' and event['data']['role_request'] == first['id']]
        unconfirmed.update(expired=expired, late_confirm=request('role_request_confirm', terminal_b, role_request=first['id']).get('error'),
                           notice=[row['id'] for row in request('sidebar_snapshot').get('unconfirmed_role_requests') or []],
                           rival_still_pending=len(pending_of(d)))
        report['unconfirmed_grant'] = unconfirmed
        check('grant_needs_confirmation', unconfirmed == dict(answer='granted', role=None, call='approved_role_required', sidebar=[],
              shown_as_granted=[first['id']],
              rival_pending=1, rival_decide='role_taken', expired=['not_confirmed'], late_confirm='request_not_granted',
              notice=[first['id']], rival_still_pending=1), unconfirmed)
        # The role is free again: b asks once more, d is granted and confirms; b's request is then settled.
        ask_b = ask(terminal_b, 'ideation')
        deadline = time.monotonic() + 15
        while not pending_of(b):
            assert time.monotonic() < deadline, 'b 的新申请没有出现'
            time.sleep(.2)
        stale_notice = [row['id'] for row in request('sidebar_snapshot').get('unconfirmed_role_requests') or []]
        check('void_notice_cleared_when_terminal_asks_again', stale_notice == [], stale_notice)
        [second] = pending_of(d)
        assert request('role_request_decide', operator, role_request=second['id'], approved=True)['ok']
        winner = answer(ask_d)
        before_confirm = len(pending_of(b))
        confirmed = request('role_request_confirm', terminal_d, role_request=second['id'])
        ask_b.settimeout(5)
        try:
            rival = answer(ask_b).get('error')
        except socket.timeout:
            rival = 'still_waiting'
            ask_b.close()
        conflict = dict(winner=winner['role_request']['state'], before_confirm=before_confirm, confirmed=confirmed['ok'], rival=rival,
                        pending=[row['id'] for row in request('sidebar_snapshot').get('role_requests') or []],
                        b_role=request('terminal_whoami', terminal_b)['role'], d_role=request('terminal_whoami', terminal_d)['role'])
        report['same_role_conflict'] = conflict
        check('confirmed_grant_settles_rivals', conflict == dict(winner='granted', before_confirm=1, confirmed=True, rival='role_given_to_other',
              pending=[], b_role=None, d_role='ideation'), conflict)
        assert request('role_release', terminal_d)['ok']

        # 8: closing the terminal ends its role.
        closed = request('shell_close', operator, launch=a['launch'])
        assert closed['ok'], closed
        borrowed_after = request('inbox_list', dict(kind='terminal', launch=a['launch'], token=token_a))
        check('closed_terminal_identity_refused', borrowed_after['ok'] is False, borrowed_after)
        sidebar = request('sidebar_snapshot')
        check('sidebar_drops_closed_controller', not [agent for agent in sidebar['agents'] if agent['id'] == a['launch']])
        type_line(b, f'(a2a request executor > {out}/b-request2.json 2>/dev/null; print $? > {out}/b-request2.exit) &!', 'T121-B-SENT2')
        [pending_b2] = wait_pending(('proj', 'executor'))
        check('role_free_again_after_close', pending_b2['launch'] == b['launch'])
        assert request('role_request_decide', operator, role_request=pending_b2['id'], approved=False)['ok']

        # 9: the asker stops waiting and cannot clean up (a tool timeout SIGKILLs it): the daemon withdraws the request.
        type_line(b, f'a2a request executor 2>/dev/null > {out}/b-killed.json & A2APID=$!', 'T121-B-SENT3')
        [pending_b3] = wait_pending(('proj', 'executor'))
        type_line(b, 'kill -KILL $A2APID; wait $A2APID', 'T121-B-KILLED')
        deadline = time.monotonic() + 15
        while [row for row in request('sidebar_snapshot').get('role_requests') or [] if row['id'] == pending_b3['id']]:
            assert time.monotonic() < deadline, '被杀的申请没有撤回'
            time.sleep(.2)
        late = request('role_request_decide', operator, role_request=pending_b3['id'], approved=True)
        withdrawn = [event for event in request('orchestration_events')['events'] if event['type'] == 'role_request_ended'
                     and event['data']['role_request'] == pending_b3['id']]
        check('killed_request_withdrawn_and_not_approvable', late.get('error') == 'request_not_pending' and
              len(withdrawn) == 1 and withdrawn[0]['data']['reason'] == 'asker_gone', [late, withdrawn])

        # 4 (XDG): the user's .zshenv sets ZDOTDIR; it must stay set after startup.
        (home / 'use-xdg').write_text('', encoding='utf-8')
        c = open_terminal('c')
        type_line(c, f'print -r -- "${{ZDOTDIR-<unset>}}|${{T121_XDG_ZSHRC-}}|${{path[1]}}|${{HISTFILE-<unset>}}" > {out}/xdg.txt', 'T121-XDG')
        zdotdir_c, xdg_zshrc, first_c, histfile_c = (out / 'xdg.txt').read_text(encoding='utf-8').strip().split('|')
        report['xdg_env'] = dict(zdotdir=zdotdir_c, zshrc=xdg_zshrc, path_first=first_c, histfile=histfile_c)
        check('user_zdotdir_kept', zdotdir_c == f'{home}/.config/zsh' and xdg_zshrc == 'loaded' and
              first_c.endswith('/workbench/terminal/bin') and histfile_c == f'{home}/.config/zsh/.zsh_history', report['xdg_env'])

        events = request('orchestration_events')['events']
        kinds = [event['type'] for event in events if event['type'].startswith('role_')]
        report['role_request_events'] = kinds
        # Append-only: every later event refers to an earlier request, at most once per kind,
        # and a confirmation follows an approving decision.
        seen, ok = {}, True
        for event in sorted((e for e in events if e['type'].startswith('role_')), key=lambda e: e['seq']):
            rid = event['data']['role_request']
            if event['type'] == 'role_requested':
                ok = ok and rid not in seen
                seen[rid] = []
                continue
            ok = ok and rid in seen and event['type'] not in seen[rid]
            if event['type'] == 'role_request_confirmed':
                ok = ok and 'approved' in seen.get(rid, [])
            seen.setdefault(rid, []).append(event['type'])
            if event['type'] == 'role_request_decided' and event['data']['approved']:
                seen[rid].append('approved')
        check('role_requests_recorded_append_only', ok and len(seen) >= 10 and kinds.count('role_request_confirmed') == 3, kinds)
        stray = sorted(str(path) for path in (source / 'workbench/terminal').rglob('*') if path.name.startswith('.zsh_history'))
        check('nothing_written_into_app_resources', not stray, stray)
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        if running:
            try:
                run_cli('daemon_stop')
                deadline = time.monotonic() + 10
                while (state / 'control.sock').exists() and time.monotonic() < deadline:
                    time.sleep(.05)
            except Exception as error:
                report['cleanup_error'] = str(error)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        shutil.rmtree(fixture, ignore_errors=True)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
