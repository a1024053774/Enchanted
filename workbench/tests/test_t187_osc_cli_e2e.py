"""T-187：项目终端里的 agy 与 opencode 经包装脚本接入：角色申请记下是哪个 CLI，侧栏状态取自 CLI 自己报给终端的
OSC 7501，做不到的信号显示“未知”；绕过包装脚本启动时窗格提示没接入。
真实后台、项目终端（zsh 与包装脚本）、真实 Electron 窗口。agy 与 opencode 用本地原生替身 t187_fake_cli.c：按 T-187
facts.md 里真实 CLI 的报告格式输出（agy 只在 AGY_CLI_OSC7501=on 时报，opencode 总是报），不连模型。真实 CLI 另做实跑。

ticket 原话（用户 2026-10-25）：“增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下”。验收：两种
CLI 的状态（运行中/空闲/等回答）在侧栏正确；做不到的信号在界面上显示“未知”而不是猜。

场景（期望来自 ticket 与 facts.md 的实测报告，不读被测代码的输出）：
1. 终端 A 直接敲 `agy`，替身在 shell 里运行 `a2a request executor`，用户批准。期望：角色记为 agy；空闲报告→“空闲”，
   working→“运行中”，提问→“等待用户回答”，权限确认→“未知”，回合结束（done、idle）→“空闲”；窗格没有提示。
2. 终端 B 用替身 agy 的绝对路径启动。期望：窗格提示 agy 没接入，状态未知。
3. 终端 C 先 `export CLAUDECODE=1`（如同在 Claude 会话里启动 opencode，继承了外层的变量），再直接敲 `opencode`，
   申请并批准（构思主控，另一个角色）。期望：角色记为 opencode（最近的那个 CLI），不是 claude；启动参数带 --standalone，
   本会话配置的 instructions 文件内容就是 Claude、Codex 开局拿到的同一段说明（a2a session-context）；分两段到达的
   working 报告→“运行中”；拆在开头标记中间的报告也读出；提问→“等待用户回答”；退出 opencode 回到 shell 后（不再敲回车），不再沿用最后一条报告，显示“未知”；再以 `opencode; sleep 30` 启动，opencode 退出、sleep 占着前台时也显示“未知”。
4. 终端 D 用替身 opencode 的绝对路径启动。期望：窗格提示 opencode 没接入。

失败方式（先列再写）：
1. 角色申请不认 agy、opencode，记成未知 CLI，状态一直未知（修前）。
2. 不读 OSC 7501，状态一直未知；或只认 claude/codex 的钩子。
3. 一条报告被拆在两次输出里时丢掉（只在单次输出里找完整序列，或拆在开头标记中间时丢掉）。
8. 外层 CLI 的变量被继承时，按登记顺序认成外层的 CLI。
4. 把权限确认、登录等也当成“等待用户回答”或“运行中”（猜）。
5. CLI 退出后仍沿用最后一条报告（包括退出后用户没在 shell 里再敲回车的情况）。
6. 绕过包装脚本时不提示；或经包装脚本也提示。
7. opencode 没有拿到开局说明，或拿到的是另一份文字。
--revision 在该版本源码上跑；--mutant 跑已知坏实现。
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
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture  # noqa: E402

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['no-carry', 'blocked-is-waiting', 'kept-after-exit', 'enter-only', 'env-order', 'other-in-front'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, real_model_turns=0,
                  checks=[], failed=[], observed={})
    patches = {
        # A report is looked for only inside one chunk of output.
        'no-carry': [('src/terminalClis.ts', '  return { carry: from >= 0 && text.length - from < 4096 ? text.slice(from) : "", turns };',
                      '  return { carry: "", turns };')],
        # Any blocked report counts as waiting for the user's answer.
        'blocked-is-waiting': [('src/terminalClis.ts', '  return turn.state === "blocked" && turn.kind === "question" ? "waiting_user_answer" : "unknown";',
                                '  return turn.state === "blocked" ? "waiting_user_answer" : "unknown";')],
        # The last report stays after the CLI exits.
        'kept-after-exit': [('src/panes.ts', '      if (!leader) { pane.unwiredCli = null; pane.cliTurn = null; return; }',
                             '      if (!leader) { pane.unwiredCli = null; return; }')],
        # The foreground is looked at again only after a line typed at the prompt (review F2).
        'enter-only': [('src/panes.ts', '      if (unwired || pane.cliTurn) pane.wiringCheckAt = Date.now() + WIRING_RECHECK_MS;',
                        '      if (unwired) pane.wiringCheckAt = Date.now() + WIRING_RECHECK_MS;'),
                       ('src/panes.ts', 'pane.cliTurn = reports.turns.at(-1); pane.wiringCheckAt ??= Date.now() + WIRING_RECHECK_MS; }',
                        'pane.cliTurn = reports.turns.at(-1); }')],
        # The first CLI in the register wins when an outer CLI's variable is inherited (review F1).
        'env-order': [('src/terminalClis.ts', '  return ancestors().map(cliProgram).find(name => name !== undefined && claimed.includes(name));', '  return claimed[0];')],
        # Another program in front after the CLI exits keeps its last report (review round 2, F2).
        'other-in-front': [('src/panes.ts', '      if (cli?.turns !== "osc7501") pane.cliTurn = null;\n', '')],
    }.get(args.mutant, [])

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    fixture = Fixture('t187-', lambda body: ('unused', [], '好的。'), revision=args.revision, patches=patches)
    report['fixture'] = str(fixture.dir)
    electron = None
    fake = fixture.dir / 'fake-bin'
    fake.mkdir()
    subprocess.run(['cc', '-O2', '-o', str(fake / 'agy'), str(HERE / 't187_fake_cli.c')], check=True)
    os.link(fake / 'agy', fake / 'opencode')

    def strip(raw):
        return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

    def screen(term):
        return strip((fixture.state / 'traces' / term['launch'] / 'pty.raw').read_text(encoding='utf-8', errors='replace'))

    def type_in(term, data):
        term['sequence'] += 1
        sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    def terminal(name):
        launch = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        term = dict(name=name, launch=launch, identity=window['identity'], sequence=0)
        # The fake CLIs come right after the shims on PATH, ahead of the user's real agy and opencode.
        type_in(term, f'export PATH="$A2A_TERMINAL_BIN:{fake}:$PATH"\r')
        fixture.wait(f'{name} 的 shell', lambda: 'exportPATH' in screen(term), 30)
        return term

    def show(term):
        row = f"document.querySelector('[data-terminal-launch=\"{term['launch']}\"], [data-agent-launch=\"{term['launch']}\"]')"
        electron.until(f'{term["name"]} 的窗格', f"(()=>{{const r={row};if(r)r.click();const p=document.querySelector('.pane[data-launch-id=\"{term['launch']}\"]');"
                       f"return !!p && p.offsetParent !== null}})()", 30)
        time.sleep(2)

    def hint(term):
        show(term)
        return electron.evaluate(f"document.querySelector('.pane[data-launch-id=\"{term['launch']}\"] [data-unwired-cli]')?.dataset.unwiredCli ?? null")

    def row(term):
        snapshot = fixture.request('sidebar_snapshot')
        return next((r for r in snapshot.get('agents', []) + snapshot.get('terminals', []) if r.get('id') == term['launch']), {})

    def settle(label, term, expected, seconds=12):
        deadline = time.time() + seconds
        seen = row(term).get('state')
        while seen != expected and time.time() < deadline:
            time.sleep(0.5)
            seen = row(term).get('state')
        report['observed'][label] = dict(state=seen, cli=row(term).get('cli'))
        check(label, seen == expected, report['observed'][label])
        return seen

    def wait_hint(label, term, expected, seconds=20):
        deadline = time.time() + seconds
        seen = hint(term)
        while seen != expected and time.time() < deadline:
            time.sleep(1)
            seen = hint(term)
        report['observed'][label] = dict(hint=seen, state=row(term).get('state'))
        check(label, seen == expected, report['observed'][label])

    def request_role(term, role):
        type_in(term, f'request {role}\r')
        pending = fixture.wait(f'{term["name"]} 的角色申请',
                               lambda: [r for r in fixture.request('sidebar_snapshot').get('role_requests', []) if r.get('launch') == term['launch']], 30)
        report['observed'][f'{term["name"]}_request'] = dict(role=pending[0].get('role'), cli=pending[0].get('cli'))
        assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)['ok']
        fixture.wait(f'{term["name"]} 的申请结束', lambda: 'requestexit' in screen(term), 30)
        return pending[0]

    try:
        fixture.start(args.claude, {'README.md': 'demo\n'})
        assert fixture.request('role_release', fixture.terminal)['ok']
        electron = Electron(fixture, 't187-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")

        # 1. agy as typed.
        a = terminal('A')
        agy_launch_out = fixture.dir / 'agy-launch.txt'
        type_in(a, f'export T187_LAUNCH_OUT={agy_launch_out}; agy\r')
        fixture.wait('A 的 agy 启动', lambda: 'agyfakeready' in screen(a), 30)
        type_in(a, 'launch\r')
        fixture.wait('A 的启动记录', lambda: agy_launch_out.exists() and 'launchwritten' in screen(a), 30)
        agy_argv = [v for k, v in (l.split('\t', 1) for l in agy_launch_out.read_text(encoding='utf-8').splitlines()) if k == 'argv']
        # agy reads the AGENTS.md of each workspace directory; the shim adds the orientation's directory (real probe in RESULTS).
        added = agy_argv[agy_argv.index('--add-dir') + 1] if '--add-dir' in agy_argv[:-1] else None
        given = (Path(added) / 'AGENTS.md').read_text(encoding='utf-8').strip() if added and (Path(added) / 'AGENTS.md').is_file() else None
        context = subprocess.run([shutil.which('node'), str(Path(fixture.source) / 'workbench/src/terminalCli.ts'), 'session-context'], capture_output=True, text=True,
                                 env={**os.environ, 'A2A_TERMINAL_SOCKET': 'x', 'A2A_TERMINAL': 'x', 'A2A_TERMINAL_TOKEN': 'x'})
        expected = json.loads(context.stdout)['hookSpecificOutput']['additionalContext'] if context.stdout.strip() else None
        report['observed']['agy_launch'] = agy_argv
        check('agy_orientation_same', expected is not None and given == expected.strip(), dict(argv=agy_argv, given=given))
        asked = request_role(a, 'executor')
        check('agy_request_cli', asked.get('cli') == 'agy', asked)
        settle('agy_idle_after_request', a, 'idle')
        check('agy_row_cli', row(a).get('cli') == 'agy', row(a))
        type_in(a, 'work\r'); settle('agy_working_running', a, 'running')
        type_in(a, 'ask\r'); settle('agy_question_waiting', a, 'waiting_user_answer')
        type_in(a, 'perm\r'); settle('agy_permission_unknown', a, 'unknown')
        type_in(a, 'done\r'); settle('agy_done_idle', a, 'idle')
        wait_hint('agy_shim_not_warned', a, None, 3)
        electron.screenshot(fixture.out / 'agy-controller-idle.png')

        # 2. agy by its real path.
        b = terminal('B')
        type_in(b, f'{fake / "agy"}\r')
        fixture.wait('B 的 agy 启动', lambda: 'agyfakeready' in screen(b), 30)
        wait_hint('agy_bypassed_warned', b, 'agy')
        check('agy_bypassed_state_unknown', row(b).get('state') == 'unknown', row(b))

        # 3. opencode as typed, as the ideation controller.
        c = terminal('C')
        launch_out = fixture.dir / 'opencode-launch.txt'
        type_in(c, f'export T187_LAUNCH_OUT={launch_out} CLAUDECODE=1; opencode\r')
        fixture.wait('C 的 opencode 启动', lambda: 'opencodefakeready' in screen(c), 30)
        type_in(c, 'launch\r')
        fixture.wait('C 的启动记录', lambda: launch_out.exists() and 'launchwritten' in screen(c), 30)
        launch = [line.split('\t', 1) for line in launch_out.read_text(encoding='utf-8').splitlines()]
        argv = [value for key, value in launch if key == 'argv']
        config = json.loads(dict(launch).get('config') or '{}')
        context = subprocess.run([shutil.which('node'), str(Path(fixture.source) / 'workbench/src/terminalCli.ts'), 'session-context'], capture_output=True, text=True,
                                 env={**os.environ, 'A2A_TERMINAL_SOCKET': 'x', 'A2A_TERMINAL': 'x', 'A2A_TERMINAL_TOKEN': 'x'})
        expected = json.loads(context.stdout)['hookSpecificOutput']['additionalContext'] if context.stdout.strip() else None
        files = config.get('instructions') or []
        given = Path(files[0]).read_text(encoding='utf-8').strip() if len(files) == 1 and Path(files[0]).is_file() else None
        report['observed']['opencode_launch'] = dict(argv=argv, config=config, shim=dict(launch).get('shim'))
        check('opencode_standalone', '--standalone' in argv[1:], argv)
        check('opencode_orientation_same', expected is not None and given == expected.strip(), dict(given=given, expected=expected))
        asked = request_role(c, 'ideation')
        check('opencode_request_cli', asked.get('cli') == 'opencode', asked)
        settle('opencode_idle_after_request', c, 'idle')
        type_in(c, 'split\r'); settle('opencode_split_report_running', c, 'running')
        type_in(c, 'done\r'); settle('opencode_done_before_prefix', c, 'idle')
        type_in(c, 'prefix\r'); settle('opencode_prefix_split_running', c, 'running')
        type_in(c, 'ask\r'); settle('opencode_question_waiting', c, 'waiting_user_answer')
        type_in(c, 'done\r'); settle('opencode_done_idle', c, 'idle')
        electron.screenshot(fixture.out / 'opencode-controller-idle.png')
        type_in(c, 'leave\r')  # opencode ends by itself; nothing is typed at the shell prompt afterwards
        fixture.wait('C 回到 shell', lambda: screen(c).rstrip().endswith('%'), 30)
        settle('opencode_exit_unknown', c, 'unknown')
        # Another program takes the foreground as opencode ends (`opencode; sleep 30`): its last report does not stand.
        type_in(c, 'opencode; sleep 30\r')
        fixture.wait('C 的第二个 opencode 启动', lambda: screen(c).count('opencodefakeready') >= 2, 30)
        type_in(c, 'done\r'); settle('opencode_again_idle', c, 'idle')
        type_in(c, 'leave\r')
        settle('opencode_then_other_unknown', c, 'unknown')

        # 4. opencode by its real path.
        d = terminal('D')
        type_in(d, f'{fake / "opencode"}\r')
        fixture.wait('D 的 opencode 启动', lambda: 'opencodefakeready' in screen(d), 30)
        wait_hint('opencode_bypassed_warned', d, 'opencode')
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(status=report['status'], failed=[f['name'] for f in report['failed']], error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
