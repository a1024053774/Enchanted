"""T-247：普通终端里 `a2a hook` 上报的 cli 与 cli_pid 必须是运行这个钩子的 CLI 进程。经真实入口（terminal/bin/a2a 包装脚本
→ src/terminalCli.ts 的 hook），进程树由假 CLI 搭出（`node <目录>/codex` 之类，ps 里与真 CLI 一样认作 codex），各自把自己的
进程号写进文件作为预期；上报由一个只收一行就回 ok 的 Unix socket 收下。不起后台、不碰真实 CLI 与用户配置。

失败方式（先列再写）：
A. Codex 直接运行钩子、钩子环境里没有 CODEX_THREAD_ID（交互式 Codex 的实际情况，T-247 探针）：认不出 CLI，不上报。
B. 经 `sh -c` 中转时认不出，或报成 sh。
C. 运行钩子的是一个不认识的程序（它跑在 Codex 里）：报成外层 Codex（审查阻塞 1）。
D. Claude 里跑的 Codex 运行钩子，环境里有外层 Claude 的 CLAUDECODE：报成 Claude 或外层进程号。
E. Codex 里跑的 Codex 运行钩子，继承了外层的 CODEX_THREAD_ID：报成外层进程号。
F. Claude 运行钩子：认不出或报错进程号（回归）。
G. 运行者的路径带空格，ps 拆开后认不出：报成外层的 CLI（审查阻塞 2）；应不上报。

--revision 取该版本的 workbench/src 跑（修前红态）；--mutant nearest-cli 改为取最近的 CLI 祖先（第一版修法，应失败于 C、G）。
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
FAKE = r'''
const { spawnSync } = require("node:child_process");
const { writeFileSync } = require("node:fs");
const [label, command] = process.argv.slice(2);
writeFileSync(process.env.T247_OUT + "/" + label + ".pid", String(process.pid));
const [program, ...args] = JSON.parse(command);
process.exit(spawnSync(program, args, { stdio: "inherit" }).status ?? 1);
'''
NEAREST = ('      const runner = ancestors().find(row => !SHELLS.has((row.argv[0] ?? "").split("/").at(-1)!.replace(/^-/, "")));',
           '      const runner = ancestors().find(row => cliProgram(row.argv) !== undefined);')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['nearest-cli'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    work = Path(tempfile.mkdtemp(prefix='t247-', dir='/private/tmp')).resolve()
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, cases={}, failed=[])
    try:
        source = work / 'workbench'
        if args.revision:
            archive = subprocess.run(['git', '-C', str(ROOT), 'archive', args.revision, 'src', 'terminal'], capture_output=True, check=True).stdout
            source.mkdir()
            subprocess.run(['tar', '-x', '-C', str(source)], input=archive, check=True)
        else:
            shutil.copytree(ROOT / 'src', source / 'src')
            shutil.copytree(ROOT / 'terminal', source / 'terminal')
        if args.mutant:
            path = source / 'src/terminalCli.ts'
            text = path.read_text(encoding='utf-8')
            assert text.count(NEAREST[0]) == 1, 'mutant anchor'
            path.write_text(text.replace(*NEAREST), encoding='utf-8')
        os.symlink(ROOT / 'node_modules', source / 'node_modules')
        bins = work / 'bin'
        (bins / 'My Tools').mkdir(parents=True)
        for name in ('codex', 'claude', 'mycli'):
            (bins / name).write_text(FAKE, encoding='utf-8')
        (bins / 'My Tools' / 'codex').write_text(FAKE, encoding='utf-8')
        out = work / 'out'
        out.mkdir()

        received = []
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        address = str(work / 's')
        listener.bind(address)
        listener.listen(8)

        def serve():
            while True:
                try:
                    connection, _ = listener.accept()
                except OSError:
                    return
                with connection:
                    data = b''
                    while not data.endswith(b'\n'):
                        chunk = connection.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    if data:
                        received.append(json.loads(data))
                        connection.sendall(b'{"ok":true}\n')
        threading.Thread(target=serve, daemon=True).start()

        node = shutil.which('node')
        hook = [str(source / 'terminal/bin/a2a'), 'hook']

        def fake(name, label, command):
            return [node, str(bins / name), label, json.dumps(command)]

        def sh(command):
            # `; true` keeps the shell from exec'ing its last command, so the shell stays in the tree.
            return ['sh', '-c', shlex.join(command) + '; true']

        cases = {
            'A_codex_direct_no_thread_env': (fake('codex', 'A', hook), {}, ('codex', 'A')),
            'B_codex_through_sh': (fake('codex', 'B', sh(hook)), {}, ('codex', 'B')),
            'C_unknown_runner_inside_codex': (fake('codex', 'C-outer', sh(fake('mycli', 'C-runner', sh(hook)))), {'CODEX_THREAD_ID': 'outer-thread'}, None),
            'D_codex_inside_claude': (fake('claude', 'D-outer', sh(fake('codex', 'D', sh(hook)))), {'CLAUDECODE': '1'}, ('codex', 'D')),
            'E_codex_inside_codex_inherited_thread': (fake('codex', 'E-outer', sh(fake('codex', 'E', hook))), {'CODEX_THREAD_ID': 'outer-thread'}, ('codex', 'E')),
            'F_claude': (fake('claude', 'F', sh(hook)), {'CLAUDECODE': '1'}, ('claude', 'F')),
            'G_runner_path_with_space_inside_claude': (fake('claude', 'G-outer', sh([node, str(bins / 'My Tools' / 'codex'), 'G', json.dumps(hook)])), {'CLAUDECODE': '1'}, None),
        }
        base = {key: value for key, value in os.environ.items() if key not in ('CODEX_THREAD_ID', 'CLAUDECODE', 'CLAUDE_CODE_SESSION_ID')}
        base.update(A2A_NODE=node, A2A_TERMINAL_CLI=str(source / 'src/terminalCli.ts'), A2A_TERMINAL_BIN=str(source / 'terminal/bin'),
                    A2A_TERMINAL_SOCKET=address, A2A_TERMINAL='t247-terminal', A2A_TERMINAL_TOKEN='t247-token', T247_OUT=str(out),
                    CODEX_HOME=str(work / 'codex-home'), CLAUDE_CONFIG_DIR=str(work / 'claude-home'))
        for name, (command, env, expected) in cases.items():
            before = len(received)
            payload = json.dumps({'hook_event_name': 'UserPromptSubmit', 'session_id': 'session-' + name})
            run = subprocess.run(command, input=payload.encode(), env={**base, **env}, capture_output=True, timeout=60)
            got = received[before:]
            assert run.returncode == 0 and len(got) == 1, (name, run.returncode, run.stderr.decode()[-500:], got)
            sent = got[0]['input']
            observed = dict(cli=sent.get('cli'), cli_pid=sent.get('cli_pid'))
            want = None if expected is None else dict(cli=expected[0], cli_pid=int((out / (expected[1] + '.pid')).read_text()))
            ok = (observed['cli'] is None and observed['cli_pid'] is None) if want is None else observed == want
            pids = {path.stem: int(path.read_text()) for path in out.glob('*.pid') if path.stem.split('-')[0] == name[0]}
            report['cases'][name] = dict(expected=want, observed=observed, pids=pids, pass_=ok)
            if not ok:
                report['failed'].append(name)
        listener.close()
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except Exception as error:
        report.update(status='INCOMPLETE', error=f'{type(error).__name__}: {error}')
    finally:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        shutil.rmtree(work, ignore_errors=True)
    print(json.dumps({'status': report['status'], 'failed': report['failed'], 'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
