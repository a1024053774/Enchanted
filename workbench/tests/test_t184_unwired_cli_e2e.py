"""T-184（ready_rev 2）：项目终端里绕过包装脚本启动的 CLI，窗格提示“没接入 Enchanted”，状态显示未知。
真实后台、项目终端（zsh 与包装脚本）、真实 Electron 窗口；真实 Claude Code（模型是本地脚本化接口，不发提示词）与真实
Codex（隔离的空 CODEX_HOME，停在它自己的启动画面，不连模型）。

用户决定（2026-10-25，逐字，经构思主控转述）：“不加固，绕过时界面提示 (Recommended)”。ticket：后台发现项目终端里前台的
claude/codex 进程没有带 Enchanted 的接入参数时，在窗格里提示“这个会话没接入 Enchanted，状态和主控命令不可用，直接敲 claude
（或 codex）重启”，该会话状态显示未知，不显示假状态。只依据进程 argv。验收：真实应用中用绝对路径启动 claude，修前无提示且
显示假状态，修后窗格提示且状态为未知；正常敲 claude 不出现提示。

场景（期望来自 ticket，不读被测代码的输出）：
1. 终端 B：用真实 claude 的绝对路径启动（lcu 实测原样）；随后这个终端经角色申请成为执行主控（与 Claude 里运行
   `a2a request executor` 相同：终端身份、cli=claude、上报会话号），用户在后台批准。期望：B 的窗格有提示，侧栏状态“未知”。
   修前：没有提示，侧栏一直“运行中”（lcu L03 的假状态）。
2. 终端 N：直接敲 `claude`（经包装脚本）。期望：没有提示，状态照常。
3. 终端 C：用真实 codex 的绝对路径启动；终端 D：直接敲 `codex`。期望：C 有提示（codex），D 没有。
4. B 里退出 Claude 回到 shell。期望：提示消失。

失败方式（先列再写）：
1. 绕过时没有提示，侧栏显示“运行中”（修前）。
2. 正常经包装脚本启动也提示（误报），例如只看可执行文件路径或进程名而不看接入参数。
3. 只认 claude，不认 codex；或反之。
4. CLI 退出后提示不消失。
5. 读不到进程信息时凭空提示。
--revision 在该版本源码上跑；--mutant 跑已知坏实现。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import socket
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    parser.add_argument('--codex', default=shutil.which('codex') or str(Path.home() / '.local/bin/codex'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['name-only', 'never-clears'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, real_model_turns=0,
                  checks=[], failed=[], observed={})
    patches = {
        # Any claude/codex in the foreground counts as unwired: the launch arguments are not looked at.
        'name-only': [('src/panes.ts', 'const unwired = Boolean(wired) && !wired(argv);', 'const unwired = Boolean(wired);')],
        # The warning is never re-read, so it stays after the CLI exits.
        'never-clears': [('src/panes.ts', '      if (!leader) { pane.unwiredCli = null; return; }', '      if (!leader) return;')],
    }.get(args.mutant, [])

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    fixture = Fixture('t184-', lambda body: ('unused', [], '好的。'), revision=args.revision, patches=patches)
    report['fixture'] = str(fixture.dir)
    electron = None

    def strip(raw):
        return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

    def screen(term):
        return strip((fixture.state / 'traces' / term['launch'] / 'pty.raw').read_text(encoding='utf-8', errors='replace'))

    def terminal(name):
        launch = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        term = dict(name=name, launch=launch, identity=window['identity'], sequence=0)
        token = fixture.out / f'token-{name}.txt'
        type_in(term, f'print -r -- $A2A_TERMINAL_TOKEN > {token}\r')
        fixture.wait(f'{name} 写出令牌', lambda: token.exists() and token.read_text().strip(), 30)
        term['terminal'] = dict(kind='terminal', launch=launch, token=token.read_text().strip())
        return term

    def type_in(term, data):
        term['sequence'] += 1
        sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    def show(term):
        row = f"document.querySelector('[data-terminal-launch=\"{term['launch']}\"], [data-agent-launch=\"{term['launch']}\"]')"
        # A pane stays mounted while hidden and reads its status only while visible: select the row each time.
        electron.until(f'{term["name"]} 的窗格', f"(()=>{{const r={row};if(r)r.click();const p=document.querySelector('.pane[data-launch-id=\"{term['launch']}\"]');"
                       f"return !!p && p.offsetParent !== null}})()", 30)
        time.sleep(2)  # one status read (every second while visible)

    def hint(term):
        show(term)
        return electron.evaluate(f"document.querySelector('.pane[data-launch-id=\"{term['launch']}\"] [data-unwired-cli]')?.dataset.unwiredCli ?? null")

    def state(term):
        snapshot = fixture.request('sidebar_snapshot')
        rows = snapshot.get('agents', []) + snapshot.get('terminals', [])
        return next((row.get('state') for row in rows if row.get('id') == term['launch']), None)

    def settle(label, term, expected, seconds=20):
        """The warning as the pane shows it once the daemon has had time to read the foreground process."""
        deadline = time.time() + seconds
        seen = hint(term)
        while seen != expected and time.time() < deadline:
            time.sleep(1)
            seen = hint(term)
        report['observed'][label] = dict(hint=seen, state=state(term))
        return seen

    def claude_ready(term):
        text = screen(term)
        return 'ClaudeCodev' in text and '❯' in text.split('ClaudeCodev', 1)[1]

    try:
        fixture.start(args.claude, {'README.md': 'demo\n'})
        assert fixture.request('role_release', fixture.terminal)['ok']
        claude_json = json.loads((fixture.home / '.claude.json').read_text(encoding='utf-8'))
        claude_json['projects'] = {str(fixture.repo): {'hasTrustDialogAccepted': True}}
        (fixture.home / '.claude.json').write_text(json.dumps(claude_json), encoding='utf-8')
        empty_codex = fixture.dir / 'codex-empty-home'
        empty_codex.mkdir()
        (empty_codex / 'config.toml').write_text('check_for_update_on_startup = false\n', encoding='utf-8')
        electron = Electron(fixture, 't184-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")

        # 1. Claude by its real path, then approved as the executor controller the way `a2a request` does it from inside.
        b = terminal('B')
        session = str(uuid.uuid4())
        type_in(b, f'{args.claude} --model claude-haiku-5-5 --session-id {session}\r')
        fixture.wait('B 的 Claude 启动', lambda: claude_ready(b), 60)
        asker = socket.socket(socket.AF_UNIX)
        asker.connect(str(fixture.state / 'control.sock'))
        asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role='executor', wait_seconds=60, cli='claude',
                                                                        native_session=session, native_home=str(fixture.home / '.claude')),
                                       identity=b['terminal'])) + '\n').encode())
        pending = fixture.wait('B 的角色申请', lambda: [r for r in fixture.request('sidebar_snapshot').get('role_requests', []) if r.get('launch') == b['launch']], 20)
        assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)['ok']
        response = b''
        while b'\n' not in response:
            response += asker.recv(65536)
        asker.close()
        granted = json.loads(response.split(b'\n', 1)[0])
        assert fixture.request('role_request_confirm', b['terminal'], role_request=granted['role_request']['id'])['ok']
        seen = settle('B_bypassed_claude_controller', b, 'claude')
        check('bypassed_claude_warned', seen == 'claude', report['observed']['B_bypassed_claude_controller'])
        check('bypassed_claude_state_unknown', state(b) == 'unknown', report['observed']['B_bypassed_claude_controller'])
        electron.screenshot(fixture.out / 'bypassed-claude.png')

        # 2. `claude` as typed, through the shim.
        n = terminal('N')
        type_in(n, 'claude --model claude-haiku-5-5\r')
        fixture.wait('N 的 Claude 启动', lambda: claude_ready(n), 60)
        time.sleep(8)
        seen = settle('N_shim_claude', n, None, 3)
        check('shim_claude_not_warned', seen is None, report['observed']['N_shim_claude'])
        check('shim_claude_state_known', state(n) == 'running', report['observed']['N_shim_claude'])

        # 3. Codex both ways, each held at its own start screen (an empty home: no login, no model).
        c = terminal('C')
        type_in(c, f'export CODEX_HOME={empty_codex}; {args.codex}\r')
        fixture.wait('C 的 Codex 启动', lambda: 'Codex' in screen(c).split('CODEX_HOME=')[-1], 60)
        seen = settle('C_bypassed_codex', c, 'codex')
        check('bypassed_codex_warned', seen == 'codex', report['observed']['C_bypassed_codex'])
        check('bypassed_codex_state_unknown', state(c) == 'unknown', report['observed']['C_bypassed_codex'])
        d = terminal('D')
        type_in(d, f'export CODEX_HOME={empty_codex}; codex\r')
        fixture.wait('D 的 Codex 启动', lambda: 'Codex' in screen(d).split('CODEX_HOME=')[-1], 60)
        time.sleep(8)
        seen = settle('D_shim_codex', d, None, 3)
        check('shim_codex_not_warned', seen is None, report['observed']['D_shim_codex'])

        # 4. Claude in B exits; the shell is back in the foreground.
        type_in(b, '/exit')
        time.sleep(1)
        type_in(b, '\r')
        fixture.wait('B 回到 shell', lambda: screen(b).rstrip().endswith('%') or screen(b).rstrip().endswith('demo%'), 30)
        seen = settle('B_after_exit', b, None)
        check('warning_clears_after_exit', seen is None, report['observed']['B_after_exit'])
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
