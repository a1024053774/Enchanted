"""T-247：穷举进程树，核对 `a2a hook` 上报的运行者。复审两次给出同一条不变式的新反例（T-240），所以不再逐个补反例，改为
写下不变式，枚举所有长度不超过 N 的进程链。

不变式（来自需求，不看实现）：钩子的运行者是钩子往上跳过 shell 后的第一个进程。
- 运行者是经 Enchanted 包装脚本启动的 Codex 或 Claude：上报它本身（cli 与它的进程号，即终端前台看到的那个进程）。
- 运行者是经包装脚本启动的 npm Codex 启动器（Node）的原生子进程：上报启动器。
- 其他情况（不经包装脚本的 CLI、其他程序）：不上报 cli。
- 无论哪种，钩子事件都要送到后台。

链上每一层取以下之一，最内层是 `terminal/bin/a2a hook`：
  S  `sh -c`（不 exec 最后一条命令，shell 留在树里）
  X  经包装脚本的 Codex（原生程序，ps 里的名字是 codex）
  Y  经包装脚本的 Claude（原生程序，名字 claude）
  U  不经包装脚本、直接运行的 codex（原生程序，名字 codex；继承外层的变量）
  O  其他程序（名字 mycli）
  N  经包装脚本的 npm Codex：Node 启动器，它再直接起名为 codex 的原生子进程，子进程再往下
假 CLI 是一个小 C 程序（按文件名出现在 ps 里），把自己的进程号写到 stderr，作为独立的预期。上报由本地 Unix socket 收下。

用法：python3 test_t247_hook_tree_search.py --summary <文件> [--length N，默认 3] [--revision <版本> | --mutant <名字>]
变异体：same-name-child（不核对声明的进程是不是运行时，第二版）、no-launcher-child（不认 npm 原生子进程）、
any-ancestor（声明的进程在祖先链任何位置都算）。
"""
import argparse
import itertools
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
FAKE_C = r'''
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
/* argv: [shim arguments...] T247:<label> <next command...>; the first marker is this process's own. */
int main(int argc, char **argv) {
  int i = 1;
  while (i < argc && strncmp(argv[i], "T247:", 5)) i++;
  if (i + 1 >= argc) return 2;
  fprintf(stderr, "T247PID %s %d\n", argv[i] + 5, getpid());
  fflush(stderr);
  pid_t child = fork();
  if (child == 0) { execvp(argv[i + 1], argv + i + 1); _exit(127); }
  int status;
  waitpid(child, &status, 0);
  return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
'''
LAUNCHER = r'''#!/usr/bin/env node
// npm's Codex: a Node launcher that runs the native binary as its child.
const { spawnSync } = require("node:child_process");
const at = process.argv.findIndex(arg => arg.startsWith("T247:"));
const label = process.argv[at].slice(5), rest = process.argv.slice(at + 1);
process.stderr.write(`T247PID ${label} ${process.pid}\n`);
process.exit(spawnSync(__dirname + "/native/codex", ["T247:" + label + "-native", ...rest], { stdio: "inherit" }).status ?? 1);
'''
WALK = '    if (!SHELLS.has(row.name)) return row.parent === pid && row.name === cli && RUNTIMES.has(rows.get(pid)?.name ?? "") ? { cli, pid } : undefined;\n'
MUTANTS = {'same-name-child': (WALK, '    if (!SHELLS.has(row.name)) return row.parent === pid && row.name === cli ? { cli, pid } : undefined;\n'),
           'no-launcher-child': (WALK, '    if (!SHELLS.has(row.name)) return undefined;\n'),
           'any-ancestor': (WALK, '    if (false) return undefined;\n')}
KINDS = 'SXYUON'


def oracle(chain):
    """The expected report for a chain (outermost first), from the invariant alone: (cli, label) or None."""
    for index in range(len(chain) - 1, -1, -1):
        kind = chain[index]
        if kind == 'S':
            continue
        return {'X': ('codex', f'X{index}'), 'Y': ('claude', f'Y{index}'), 'N': ('codex', f'N{index}')}.get(kind)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--length', type=int, default=3)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    work = Path(tempfile.mkdtemp(prefix='t247t-', dir='/private/tmp')).resolve()
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, length=args.length,
                  chains=0, failed=[], failed_count=0)
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
        (work / 'fake.c').write_text(FAKE_C, encoding='utf-8')
        fakes, direct, npm = work / 'bin', work / 'direct', work / 'npm'
        for folder in (fakes, direct, npm / 'native'):
            folder.mkdir(parents=True)
        subprocess.run(['cc', '-O0', '-o', str(fakes / 'codex'), str(work / 'fake.c')], check=True)
        for path in (fakes / 'claude', fakes / 'mycli', direct / 'codex', npm / 'native' / 'codex'):
            shutil.copyfile(fakes / 'codex', path)
            path.chmod(0o755)
        (npm / 'codex').write_text(LAUNCHER, encoding='utf-8')
        (npm / 'codex').chmod(0o755)

        received = []
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        address = str(work / 's')
        listener.bind(address)
        listener.listen(16)

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

        system_path = os.environ['PATH']

        def build(chain):
            command = hook
            for index in range(len(chain) - 1, -1, -1):
                kind, label = chain[index], f'T247:{chain[index]}{index}'
                if kind == 'S':
                    command = ['sh', '-c', shlex.join(command) + '; true']
                elif kind in 'XY':
                    # env execs the shim, and the shim execs the CLI it finds first on this PATH: one process.
                    command = ['env', f'PATH={fakes}:{system_path}', str(shims / ('codex' if kind == 'X' else 'claude')), label, *command]
                elif kind == 'N':
                    command = ['env', f'PATH={npm}:{system_path}', str(shims / 'codex'), label, *command]
                else:
                    command = [str((direct / 'codex') if kind == 'U' else (fakes / 'mycli')), label, *command]
            return command

        base = {key: value for key, value in os.environ.items() if not key.startswith(('CODEX_THREAD', 'CLAUDECODE', 'CLAUDE_CODE_', 'A2A_'))}
        base.update(A2A_NODE=shutil.which('node'), A2A_TERMINAL_CLI=str(source / 'src/terminalCli.ts'), A2A_TERMINAL_BIN=str(shims),
                    A2A_TERMINAL_PLUGIN=str(work / 'plugin'), A2A_TERMINAL_SOCKET=address, A2A_TERMINAL='t247-terminal',
                    A2A_TERMINAL_TOKEN='t247-token', CODEX_HOME=str(work / 'codex-home'), CLAUDE_CONFIG_DIR=str(work / 'claude-home'))
        payload = json.dumps({'hook_event_name': 'UserPromptSubmit', 'session_id': 'search'}).encode()
        for length in range(1, args.length + 1):
            for chain in itertools.product(KINDS, repeat=length):
                chain = ''.join(chain)
                before = len(received)
                run = subprocess.run(build(chain), input=payload, env=base, cwd=work, capture_output=True, timeout=60)
                stderr = run.stderr.decode(errors='replace')
                pids = {label: int(pid) for label, pid in re.findall(r'^T247PID (\S+) (\d+)$', stderr, re.M)}
                got = received[before:]
                sent = got[0]['input'] if len(got) == 1 else {}
                observed = dict(exit=run.returncode, delivered=len(got), cli=sent.get('cli'), cli_pid=sent.get('cli_pid'))
                expected = oracle(chain)
                want = dict(exit=0, delivered=1, cli=expected and expected[0], cli_pid=expected and pids.get(expected[1]))
                report['chains'] += 1
                if observed != want:
                    report['failed_count'] += 1
                    if len(report['failed']) < 60:
                        report['failed'].append(dict(chain=chain, expected=want, observed=observed, pids=pids, stderr=stderr[-300:]))
        listener.close()
        report['status'] = 'PASS' if not report['failed_count'] else 'INCOMPLETE'
    except Exception as error:
        report.update(status='INCOMPLETE', error=f'{type(error).__name__}: {error}')
    finally:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        shutil.rmtree(work, ignore_errors=True)
    print(json.dumps({'status': report['status'], 'chains': report['chains'], 'failed_count': report['failed_count'],
                      'first_failed': [item['chain'] for item in report['failed'][:12]], 'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
