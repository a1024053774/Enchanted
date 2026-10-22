# -*- coding: utf-8 -*-
"""T-126：项目终端只拿到专用 socket 与终端令牌。真实 CLI 入口、后台、两个 socket、zsh 与 `a2a` 命令。

失败方式（先列再写）：
1. 终端环境里还有后台数据目录（`A2A_STATE` 或任何含该路径的变量），或者操作员凭据路径。
2. 专用 socket 的路径在后台数据目录里，或者其他用户可读。
3. 终端里的 `a2a whoami`、`a2a request` 不再工作；界面（原 socket 上的操作员）批准后终端拿不到角色。
4. 专用 socket 接受操作员或窗口身份：持有真凭据的操作员命令、窗口命令、伪造身份、不带身份都能通过。
5. 终端用自己能看到的信息（环境、令牌、申请 id）在专用 socket 上批准自己的申请。
6. 专用 socket 上的拒绝不留记录，或者记录分不清来自哪个 socket。
7. 原 socket 的行为被改变（操作员命令照常可用）。
8. 后台停止后专用 socket 与其目录还在。
--revision 在该版本的隔离源码上跑同一场景（修前应失败于第 1 条）。
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]

ATTACK = r'''
// Runs inside the project terminal and uses only what the terminal can see.
import { connect } from "node:net";
const [roleRequest] = process.argv.slice(2);
const { A2A_TERMINAL_SOCKET: path, A2A_TERMINAL: launch, A2A_TERMINAL_TOKEN: token } = process.env;
const send = (identity) => new Promise((resolve, reject) => {
  const connection = connect(path); let buffer = "";
  connection.on("error", reject).on("data", (part) => { buffer += part; if (buffer.includes("\n")) { connection.end(); resolve(JSON.parse(buffer.split("\n")[0])); } });
  connection.write(JSON.stringify({ id: crypto.randomUUID(), identity, input: { command: "role_request_decide", role_request: roleRequest, approved: true } }) + "\n");
});
const tries = { none: null, own_terminal: { kind: "terminal", launch, token },
  forged_operator: { kind: "operator", token }, forged_window: { kind: "window", launch, token } };
const out = {};
for (const [name, identity] of Object.entries(tries)) out[name] = await send(identity);
process.stdout.write(JSON.stringify(out) + "\n");
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    # Known-bad: the terminal socket authenticates any identity; the shell still exports the data directory;
    # refusals on the terminal socket are recorded without naming it.
    target.add_argument('--mutant', choices=['socket-accepts-all', 'state-exported', 'refusal-unmarked'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t126-', dir='/private/tmp')).resolve()
    state, home, cwd, out, keys = fixture / 'state', fixture / 'home', fixture / 'proj', fixture / 'out', fixture / 'keys'
    for path in (state, home, cwd, out, keys):
        path.mkdir()
    (home / '.zshrc').write_text("PS1='T126% '\n", encoding='utf-8')
    credential = keys / 'operator.json'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, fixture=str(fixture), checks=[])
    running = False

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    source = ROOT
    if args.revision or args.mutant:
        source = fixture / 'source'
        if args.revision:
            for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', args.revision, 'workbench/src', 'workbench/terminal'],
                                                cwd=ROOT, text=True).splitlines():
                target_path = source / name
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(subprocess.check_output(['git', 'show', f'{args.revision}:{name}'], cwd=ROOT))
                if name.startswith('workbench/terminal/bin/'):
                    target_path.chmod(0o755)
        else:
            for name in ('src', 'terminal'):
                shutil.copytree(ROOT / 'workbench' / name, source / 'workbench' / name, symlinks=True)
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    if args.mutant:
        path, old, new = {
            'socket-accepts-all': ('src/daemon.ts', 'if (terminalOnly && envelope?.identity?.kind !== "terminal") throw new Refusal("terminal_socket_terminal_only");', ''),
            'state-exported': ('src/panes.ts', 'A2A_TERMINAL_SOCKET: this.terminalSocket,', 'A2A_TERMINAL_SOCKET: this.terminalSocket, A2A_STATE: this.root,'),
            'refusal-unmarked': ('src/daemon.ts', '...(terminalOnly ? { socket: "terminal" } : {})', ''),
        }[args.mutant]
        path = source / 'workbench' / path
        text = path.read_text(encoding='utf-8')
        assert text.count(old) == 1, '变异定位必须唯一'
        path.write_text(text.replace(old, new), encoding='utf-8')
    cli = source / 'workbench/src/gates/cli.ts'
    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', A2A_OPERATOR_CREDENTIAL=str(credential))
    env.pop('ZDOTDIR', None)

    def run_cli(*arguments):
        run = subprocess.run(['node', str(cli), '--state', str(state), *arguments], env=env, capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, f'{arguments[0]}: {run.stderr or run.stdout}'
        return json.loads(run.stdout)

    def request_at(path, command, identity=None, **data):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(30)
            connection.connect(str(path))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)) + '\n').encode())
            response = b''
            while b'\n' not in response:
                part = connection.recv(65536)
                assert part, 'daemon 在回执前断开'
                response += part
        return json.loads(response.split(b'\n', 1)[0])

    def request(command, identity=None, **data):
        return request_at(state / 'control.sock', command, identity, **data)

    def output(launch):
        result = request('pane_output', launch=launch, offset=0)
        assert result['ok'], result
        text = base64.b64decode(result['data_base64']).decode('utf-8', 'replace')
        return re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))', '', text)

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

    def wait_pending(timeout=20):
        deadline = time.monotonic() + timeout
        while True:
            pending = [item for item in request('sidebar_snapshot').get('role_requests') or [] if (item['project'], item['role']) == ('proj', 'executor')]
            if pending:
                return pending
            assert time.monotonic() < deadline, '后台没有出现待批准的申请'
            time.sleep(.2)

    try:
        run_cli('daemon_start')
        running = True
        deadline = time.monotonic() + 10
        while request('pane_layout').get('recovering') is not False:
            assert time.monotonic() < deadline, '后台恢复未结束'
            time.sleep(.05)
        operator = json.loads(credential.read_text(encoding='utf-8'))
        launch = run_cli('shell_start', '--project', 'proj', '--cwd', str(cwd))['launch']
        opened = request('window_open', operator, launch=launch['id'], project='proj')
        assert opened['ok'], opened
        a = dict(launch=launch['id'], identity=opened['identity'], sequence=0)

        # 1-2: what the terminal's environment holds.
        assert type_line(a, f'env > {out}/env.txt', 'T126-ENV') == 0
        variables = dict(line.split('=', 1) for line in (out / 'env.txt').read_text(encoding='utf-8').splitlines() if '=' in line)
        secret_paths = {str(state), os.path.realpath(state), str(credential), os.path.realpath(credential), str(keys)}
        leaking = sorted(key for key, value in variables.items() if any(path in value for path in secret_paths))
        report['terminal_env_keys'] = sorted(key for key in variables if key.startswith('A2A_'))
        check('terminal_env_has_no_data_directory_or_credential', 'A2A_STATE' not in variables and not leaking, leaking or 'A2A_STATE')
        terminal_socket = Path(variables.get('A2A_TERMINAL_SOCKET', ''))
        report['terminal_socket'] = str(terminal_socket)
        check('terminal_socket_private_and_outside_data_directory',
              terminal_socket.is_absolute() and terminal_socket.is_socket() and not str(terminal_socket).startswith(str(state)) and
              stat.S_IMODE(terminal_socket.stat().st_mode) == 0o600 and stat.S_IMODE(terminal_socket.parent.stat().st_mode) == 0o700,
              terminal_socket)

        # 3: the terminal's own commands, and the user's approval on the original socket.
        assert type_line(a, f'a2a whoami > {out}/whoami-0.json', 'T126-WHO0') == 0
        check('whoami_works_in_terminal', result_file('whoami-0.json')['project'] == 'proj' and result_file('whoami-0.json')['role'] is None,
              result_file('whoami-0.json'))
        type_line(a, f'(a2a request executor > {out}/request.json 2>/dev/null; print $? > {out}/request.exit) &!', 'T126-REQUEST-SENT')
        [pending] = wait_pending()

        # 4-5: the terminal tries to approve its own request with what it can see.
        (out / 'attack.mjs').write_text(ATTACK, encoding='utf-8')
        assert type_line(a, f'ELECTRON_RUN_AS_NODE=1 "$A2A_NODE" {out}/attack.mjs {pending["id"]} > {out}/attack.json', 'T126-ATTACK') == 0
        attack = result_file('attack.json')
        report['terminal_attack'] = {name: result.get('error') for name, result in attack.items()}
        check('terminal_visible_identities_cannot_decide', all(result.get('ok') is False for result in attack.values()) and
              {attack[name]['error'] for name in ('none', 'forged_operator', 'forged_window')} == {'terminal_socket_terminal_only'}, attack)
        real = dict(operator=request_at(terminal_socket, 'role_request_decide', operator, role_request=pending['id'], approved=True),
                    # Shell keystrokes are never recorded (key timings); a resize is a window command that is.
                    window=request_at(terminal_socket, 'window_resize', a['identity'], cols=100, rows=30))
        report['real_identities_on_terminal_socket'] = {name: result.get('error') for name, result in real.items()}
        check('operator_and_window_refused_on_terminal_socket', {result.get('error') for result in real.values()} == {'terminal_socket_terminal_only'}, real)
        check('request_still_pending_after_attempts', [item['id'] for item in wait_pending()] == [pending['id']])

        # 6: every refusal on the terminal socket is recorded and names that socket.
        refused = [event['data'] for event in request('orchestration_events')['events'] if event['type'] == 'request_rejected'
                   and event['data']['input'].get('command') in ('role_request_decide', 'window_resize')]
        report['recorded_refusals'] = [(data.get('socket'), data['result']['error']) for data in refused]
        check('terminal_socket_refusals_recorded', sorted(report['recorded_refusals']) == sorted(
            [('terminal', 'terminal_socket_terminal_only')] * 5 + [('terminal', attack['own_terminal']['error'])]), report['recorded_refusals'])

        # 7: the user's approval on the original socket.
        decided = request('role_request_decide', operator, role_request=pending['id'], approved=True)
        assert decided['ok'], decided
        deadline = time.monotonic() + 15
        while not (out / 'request.exit').exists():
            assert time.monotonic() < deadline, 'a2a request 没有在批准后返回'
            time.sleep(.1)
        check('request_returns_after_operator_approval', (out / 'request.exit').read_text().strip() == '0' and
              result_file('request.json')['role_request']['state'] == 'approved', result_file('request.json'))
        assert type_line(a, f'a2a whoami > {out}/whoami-1.json', 'T126-WHO1') == 0
        check('whoami_reports_approved_role', result_file('whoami-1.json')['role'] == 'executor', result_file('whoami-1.json'))

        # 8: stopping removes the terminal socket's directory.
        run_cli('daemon_stop')
        running = False
        deadline = time.monotonic() + 10
        while (state / 'control.sock').exists() and time.monotonic() < deadline:
            time.sleep(.05)
        check('terminal_socket_removed_on_stop', not terminal_socket.parent.exists(), terminal_socket.parent)
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
