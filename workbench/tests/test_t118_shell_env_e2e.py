"""T-118：普通终端不继承启动者的 agent 会话标记。真实 CLI/daemon/socket/zsh，无 Electron、模型。

失败方式：daemon 由 Claude Code（或 Codex）会话启动时带着 CLAUDECODE、CLAUDE_CODE_CHILD_SESSION、
CODEX_SANDBOX 等运行时标记，普通终端原样复制给用户的 zsh，用户在里面开的 claude 当自己是子会话、
不保存对话；或者过滤过头，把用户自己的普通变量也删了。
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
# Runtime variables observed in a live Claude Code / Codex shell on 2026-10-21.
MARKERS = {'CLAUDECODE': '1', 'CLAUDE_CODE_CHILD_SESSION': '1', 'CLAUDE_CODE_ENTRYPOINT': 'cli',
           'CLAUDE_CODE_SESSION_ID': 'fixture-session', 'CLAUDE_CODE_MESSAGING_SOCKET': '/tmp/fixture.sock',
           'CLAUDE_PID': '1', 'CODEX_SANDBOX': 'seatbelt', 'CODEX_SANDBOX_NETWORK_DISABLED': '1', 'CODEX_THREAD_ID': 'fixture'}
# User configuration (documented Claude Code settings) and ordinary variables must survive.
KEPT = {'T118_USER_VARIABLE': 'kept', 'CLAUDE_CODE_OAUTH_TOKEN': 'fixture-not-a-secret', 'CLAUDE_CODE_USE_BEDROCK': '1'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    # Known-bad first candidate: strips every CLAUDE_CODE_* variable, including user configuration.
    target.add_argument('--mutant', choices=['prefix-filter'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t118-', dir='/private/tmp')).resolve()
    state, home, cwd = fixture / 'state', fixture / 'home', fixture / 'project'
    for path in (state, home, cwd):
        path.mkdir()
    (home / '.zshrc').write_text("PS1='T118% '\n", encoding='utf-8')
    source = ROOT
    if args.revision:
        source = fixture / 'source'
        for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', args.revision, 'workbench/src'],
                                            cwd=ROOT, text=True).splitlines():
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(subprocess.check_output(['git', 'show', f'{args.revision}:{name}'], cwd=ROOT))
    if args.mutant:
        source = fixture / 'source'
        shutil.copytree(ROOT / 'workbench/src', source / 'workbench/src')
        path = source / 'workbench/src/panes.ts'
        text = path.read_text(encoding='utf-8')
        old = 'agentSessionMarkers.has(key)'
        assert text.count(old) == 1, '变异定位必须唯一'
        path.write_text(text.replace(old, 'key.startsWith("CLAUDE_CODE_") || key.startsWith("CLAUDE") || key.startsWith("CODEX_")'), encoding='utf-8')
    if source != ROOT:
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    cli = source / 'workbench/src/gates/cli.ts'
    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color',
               A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'), **MARKERS, **KEPT)
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, fixture=str(fixture), checks=[])
    running = False

    def run_cli(*arguments):
        run = subprocess.run(['node', str(cli), '--state', str(state), *arguments], env=env,
                             capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, f'{arguments[0]}: {run.stderr or run.stdout}'
        return json.loads(run.stdout)

    def request(command, identity=None, **data):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(15)
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
        text = base64.b64decode(result['data_base64']).decode('utf-8')
        return re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))', '', text)

    try:
        run_cli('daemon_start')
        running = True
        deadline = time.monotonic() + 10
        while request('pane_layout').get('recovering') is not False:
            assert time.monotonic() < deadline, '后台恢复未结束'
            time.sleep(.05)
        launch = run_cli('shell_start', '--project', 'proj', '--cwd', str(cwd))['launch']
        operator = json.loads((fixture / 'operator.json').read_text(encoding='utf-8'))
        opened = request('window_open', operator, launch=launch['id'], project='proj')
        assert opened['ok'], opened
        names = ' '.join([*MARKERS, *KEPT])
        command = f'for k in {names}; do print -r -- "T118 $k=${{(P)k-<unset>}}"; done; print T118-END\r'
        sent = request('window_input', opened['identity'], sequence=1, request_id=str(uuid.uuid4()), data=command)
        assert sent['ok'], sent
        deadline = time.monotonic() + 15
        while not re.search(r'^T118-END', output(launch['id']), re.M):
            assert time.monotonic() < deadline, '终端未输出结束标记'
            time.sleep(.1)
        seen = dict(re.findall(r'^T118 (\w+)=(.*?)\r?$', output(launch['id']), re.M))
        report['observed'] = seen
        leaked = sorted(key for key in MARKERS if seen.get(key) != '<unset>')
        assert not leaked, f'终端继承了 agent 会话标记：{leaked}'
        report['checks'].append('agent_session_markers_removed')
        removed = sorted(key for key, value in KEPT.items() if seen.get(key) != value)
        assert not removed, f'用户配置被删了：{removed}'
        report['checks'].append('ordinary_variables_kept')
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
