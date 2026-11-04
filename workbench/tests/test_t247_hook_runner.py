"""T-247：普通终端里 `a2a hook` 上报的 cli 与 cli_pid 必须是运行这个钩子的那个 CLI 进程（终端前台看到的那个进程）。
走真实入口：Enchanted 的 claude、codex 包装脚本（terminal/bin）启动 CLI，钩子经 terminal/bin/a2a 进入 src/terminalCli.ts。
CLI 用假程序代替（node 脚本，经包装脚本 exec 启动，与真 CLI 一样），每个假程序把自己的进程号写到 stderr，作为独立的预期；
上报由一个只收一行就回 ok 的 Unix socket 收下。不起后台，不碰真实 CLI 的会话与用户配置。

失败方式（先列再写）：
A. Codex 直接运行钩子，环境里没有 CODEX_THREAD_ID（交互式 Codex 的实际情况）：认不出，不上报。
B. 经 `sh -c` 中转时认不出，或报成 sh。
C. 运行钩子的是一个不认识的程序（它跑在 Codex 的 shell 工具里）：报成外层 Codex。
D. Claude 里跑的 Codex 运行钩子，环境里有外层 Claude 的变量：报成 Claude 或外层进程号。
E. Codex 里跑的 Codex 运行钩子，继承了外层的变量：报成外层进程号。
F. Claude 经 sh 运行钩子：认不出或报错进程号。
G. CLI 装在带空格的路径下（ps 的整行参数被空白拆开）：认不出。
H. npm 安装的 Codex：Node 启动器（终端前台）再起原生二进制，钩子由原生二进制运行：报成原生二进制的进程号，前台对不上。
H2. 同 H，原生二进制经 sh 运行钩子。
H3. 同 H2，装在带空格的路径下（要读进程表里带空格的可执行文件名）。
J. Codex 直接启动的另一个程序（如 MCP 服务，或 shell 经 exec 优化后直接成为子进程的程序）运行钩子：因为是 CLI 的直接子进程，
   报成外层 Codex（审查阻塞，T-247 局限修复第 1 轮）。
J2. 同 J，经 sh 运行钩子。
I. 不经包装脚本直接运行的 CLI 跑在 Codex 里：继承了外层的变量，报成外层 Codex。
S. Codex 的 workspace-write 沙箱里（ps 不能执行）CLI 直接运行钩子：报不上来。
S2. 同 S，CLI 经 sh 运行钩子（要读进程表才能核对）：整条事件丢掉；应照常发出，只是不带 cli。
（S、S2 打开沙箱的网络访问：网络关着时 seatbelt 连 Unix socket 也禁止，钩子什么都发不出，只读沙箱同样如此；真实交互式
Codex 在沙箱外运行钩子，见 test_t247_sandboxed_codex_e2e.py。）
没有 cli 的预期都要求事件照常送到后台。

--revision 取该版本的 workbench/src 与 terminal 跑（修前红态）；--mutant any-ancestor（声明的进程在祖先链上任何位置都算）
应失败于 C、I；--mutant no-launcher-child（不允许 CLI 的直接子进程）应失败于 H、H2、H3；--mutant any-direct-child
（CLI 的任何直接子进程都算）应失败于 J、J2；--mutant ps-error-drops（读不到进程表
时整条事件丢掉）应失败于 S2。进程链的穷举（含“原生 Codex 直接起同名 codex”）见 test_t247_hook_tree_search.py。
"""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
FAKE = r'''#!/usr/bin/env node
const { spawnSync } = require("node:child_process");
// The shims put their own arguments first; the label and the next command are always the last two.
const [label, command] = process.argv.slice(-2);
process.stderr.write(`T247PID ${label} ${process.pid}\n`);
const [program, ...args] = JSON.parse(command);
process.exit(spawnSync(program, args, { stdio: "inherit" }).status ?? 1);
'''
WALK = '    if (!SHELLS.has(row.name)) return row.parent === pid && row.name === cli && RUNTIMES.has(rows.get(pid)?.name ?? "") ? { cli, pid } : undefined;\n'
MUTANTS = {'any-ancestor': (WALK, '    if (false) return undefined;\n'),
           'any-direct-child': (WALK, '    if (!SHELLS.has(row.name)) return row.parent === pid ? { cli, pid } : undefined;\n'),
           'no-launcher-child': (WALK, '    if (!SHELLS.has(row.name)) return undefined;\n'),
           'ps-error-drops': (' catch { return undefined; }', ' catch (error) { throw error; }')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
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
            old, new = MUTANTS[args.mutant]
            assert text.count(old) == 1, 'mutant anchor'
            path.write_text(text.replace(old, new), encoding='utf-8')
        os.symlink(ROOT / 'node_modules', source / 'node_modules')
        shims, hook = source / 'terminal/bin', [str(source / 'terminal/bin/a2a'), 'hook']
        fakes, spaced, npm, spaced_npm, direct = work / 'bin', work / 'My Tools', work / 'npm', work / 'My Tools' / 'npm', work / 'direct'
        for folder, names in ((fakes, ('codex', 'claude', 'mycli')), (spaced, ('codex',)), (npm, ('codex',)), (spaced_npm, ('codex',)), (direct, ('codex',))):
            folder.mkdir(parents=True, exist_ok=True)
            for name in names:
                (folder / name).write_text(FAKE, encoding='utf-8')
                (folder / name).chmod(0o755)
        # npm's native binary: an executable named codex itself (ps names it by that path), here Node under that name.
        script = work / 'fake.js'
        script.write_text(FAKE, encoding='utf-8')
        for folder in (npm, spaced_npm):
            (folder / 'native').mkdir()
            (folder / 'native' / 'codex').symlink_to(shutil.which('node'))

        (work / 'codex-home').mkdir()  # `codex sandbox` (case S) needs its home to exist; nothing else reads it
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

        def via_shim(name, label, command, path=None):
            # The CLI as the user starts it in a project terminal: through Enchanted's shim, which finds the real one on PATH.
            line = shlex.join([str(shims / name), label, json.dumps(command)])
            return ['sh', '-c', (f'PATH={shlex.quote(path)}:"$PATH" ' if path else '') + line + '; true']

        def fake(path, label, command):
            return [str(path), label, json.dumps(command)]

        def native(folder, label, command):
            return [str(folder / 'native' / 'codex'), str(script), label, json.dumps(command)]

        def sh(command):
            # `; true` keeps the shell from exec'ing its last command, so the shell stays in the tree.
            return ['sh', '-c', shlex.join(command) + '; true']

        real_codex = shutil.which('codex') or str(Path.home() / '.local/bin/codex')
        cases = {
            'A_codex_direct_no_thread_env': (via_shim('codex', 'A', hook), ('codex', 'A')),
            'B_codex_through_sh': (via_shim('codex', 'B', sh(hook)), ('codex', 'B')),
            'C_unknown_runner_inside_codex': (via_shim('codex', 'C-outer', sh(fake(fakes / 'mycli', 'C-runner', sh(hook)))), None),
            'D_codex_inside_claude': (via_shim('claude', 'D-outer', via_shim('codex', 'D', sh(hook))), ('codex', 'D')),
            'E_codex_inside_codex': (via_shim('codex', 'E-outer', via_shim('codex', 'E', hook)), ('codex', 'E')),
            'F_claude_through_sh': (via_shim('claude', 'F', sh(hook)), ('claude', 'F')),
            'G_codex_installed_under_spaced_path': (via_shim('claude', 'G-outer', via_shim('codex', 'G', hook, path=str(spaced))), ('codex', 'G')),
            'H_npm_codex_native_child': (via_shim('codex', 'H', native(npm, 'H-native', hook), path=str(npm)), ('codex', 'H')),
            'H2_npm_codex_native_child_through_sh': (via_shim('codex', 'H2', native(npm, 'H2-native', sh(hook)), path=str(npm)), ('codex', 'H2')),
            'H3_npm_codex_under_spaced_path_through_sh': (via_shim('codex', 'H3', native(spaced_npm, 'H3-native', sh(hook)), path=str(spaced_npm)), ('codex', 'H3')),
            'J_other_direct_child_of_codex': (via_shim('codex', 'J-outer', fake(fakes / 'mycli', 'J-runner', hook)), None),
            'J2_other_direct_child_of_codex_through_sh': (via_shim('codex', 'J2-outer', fake(fakes / 'mycli', 'J2-runner', sh(hook))), None),
            'I_unshimmed_cli_inside_codex': (via_shim('codex', 'I-outer', sh(fake(direct / 'codex', 'I-runner', hook))), None),
            'S_codex_in_workspace_write_sandbox': ([real_codex, 'sandbox', '-c', 'sandbox_mode="workspace-write"', '-c', 'sandbox_workspace_write.network_access=true', '--'] + via_shim('codex', 'S', hook), ('codex', 'S')),
            'S2_through_sh_in_workspace_write_sandbox': ([real_codex, 'sandbox', '-c', 'sandbox_mode="workspace-write"', '-c', 'sandbox_workspace_write.network_access=true', '--'] + via_shim('codex', 'S2', sh(hook)), None),
        }
        base = {key: value for key, value in os.environ.items() if not key.startswith(('CODEX_THREAD', 'CLAUDECODE', 'CLAUDE_CODE_', 'A2A_'))}
        base.update(PATH=f'{fakes}:{base["PATH"]}', A2A_NODE=shutil.which('node'), A2A_TERMINAL_CLI=str(source / 'src/terminalCli.ts'),
                    A2A_TERMINAL_BIN=str(shims), A2A_TERMINAL_PLUGIN=str(work / 'plugin'), A2A_TERMINAL_SOCKET=address,
                    A2A_TERMINAL='t247-terminal', A2A_TERMINAL_TOKEN='t247-token', CODEX_HOME=str(work / 'codex-home'),
                    CLAUDE_CONFIG_DIR=str(work / 'claude-home'))
        for name, (command, expected) in cases.items():
            before = len(received)
            payload = json.dumps({'hook_event_name': 'UserPromptSubmit', 'session_id': 'session-' + name})
            run = subprocess.run(command, input=payload.encode(), env=base, cwd=work, capture_output=True, timeout=60)
            stderr = run.stderr.decode(errors='replace')
            pids = {label: int(pid) for label, pid in re.findall(r'^T247PID (\S+) (\d+)$', stderr, re.M)}
            got = received[before:]
            assert run.returncode == 0 and len(got) <= 1, (name, run.returncode, stderr[-800:], got)
            sent = got[0]['input'] if got else {}
            observed = dict(delivered=bool(got), cli=sent.get('cli'), cli_pid=sent.get('cli_pid'))
            want = dict(delivered=True, cli=None, cli_pid=None) if expected is None else dict(delivered=True, cli=expected[0], cli_pid=pids[expected[1]])
            ok = observed == want
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
