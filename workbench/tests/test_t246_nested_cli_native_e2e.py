"""T-246：普通终端的原生会话报告只属于报告它的进程。终端里的 Claude Code（外层）用 Bash 工具运行另一个 Claude Code
（内层 `claude -p`，同样经过包装脚本、带 Enchanted 钩子）；内层的钩子带着内层的进程号和会话号到达后台，不能顶替外层的。
真实后台、私有 hc core、真实 Claude Code；模型由夹具的脚本化 API 应答（没有真实模型回合），内层的模型请求由测试扣住。

失败方式（先列再写）：
1. 内层运行时，“复制深度链接”变成不可用：报告被内层顶替，进程号与前台（外层）不符。
2. 内层运行时，后台给这个终端的 native_session 变成内层的会话。
3. 内层结束后仍是 1 或 2（要等外层下一次钩子才恢复，或一直不恢复）。
4. 后台重启后，按记录恢复出来的报告是内层的，外层的链接不可用。
5. 外层退出后链接仍给出外层的会话；终端状态里的会话在前台复查后仍不清掉（审查第 1 条）。
6. 同一进程号换了进程（复用）仍沿用旧进程的报告：端到端造不出，由 test_by_process.ts 穷举。

--revision 在该版本的隔离源码上跑（修前应失败于 1）；--mutant last-report 改为取最后到达的报告（应失败于 1）；--mutant last-recorded 重启时只按最后一条记录恢复（应失败于 4）；
--front-failure 让终端自己的前台复查从 /exit 起失败（复审第 2 条：修前应失败于 5）。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from scripted_claude import Fixture  # noqa: E402

# A restarted daemon rebuilds only from the last report recorded (what it did before T-246).
LAST_RECORDED = [('src/panes.ts', "type='shell_native_session' ORDER BY seq\")", "type='shell_native_session' ORDER BY seq DESC LIMIT 1\")")]
# Fault injection (T-246 re-review, finding 2): the terminal's own front recheck fails while a flag file exists.
FRONT_FAILURE = [('src/panes.ts', '    pane.wiringBusy = true; pane.wiringCheckAt = undefined;\n    try {\n',
                  '    pane.wiringBusy = true; pane.wiringCheckAt = undefined;\n    try {\n'
                  '      if (existsSync(join(this.root, "t246-fail-front"))) throw new Error("T-246 injected front read failure");\n')]
LAST_REPORT = [('src/byProcess.ts', 'const report = this.front && this.byPid.get(this.front.pid);', 'const report = [...this.byPid.values()].at(-1);'),
               ('src/byProcess.ts', 'return report && report.at >= this.front!.started ? report.value : null;', 'return report ? report.value : null;')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--mutant', choices=['last-report', 'last-recorded'])
    parser.add_argument('--front-failure', action='store_true', help='the front recheck fails from /exit on (finding 2)')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, front_failure=args.front_failure,
                  checks=[], observed={})
    marker = 'T246-' + uuid.uuid4().hex[:12]
    outer_marker, inner_marker = marker + '-outer', marker + '-inner'
    hold = threading.Event()
    held = []

    def plan(body):
        text = json.dumps(body, ensure_ascii=False)
        if outer_marker in text:
            return ('outer', [('Bash', dict(command=f"claude -p '{inner_marker} 只回复 ok' --model claude-haiku-5-5",
                                            description='run a nested Claude Code'))], '外层完成。')
        # The inner CLI's turn waits until the test has looked at the terminal while it runs.
        held.append(time.time())
        hold.wait(120)
        return ('inner', [], 'ok')

    fixture = Fixture('t246-', plan, revision=args.revision, patches=[*{'last-report': LAST_REPORT, 'last-recorded': LAST_RECORDED}.get(args.mutant, ()), *(FRONT_FAILURE if args.front_failure else ())])
    report['fixture'] = str(fixture.dir)

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def strip(raw):
        return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

    try:
        fixture.start(shutil.which('claude') or str(Path.home() / '.local/bin/claude'), {'README.md': 'demo\n'})
        assert fixture.request('role_release', fixture.terminal)['ok']
        claude_json = json.loads((fixture.home / '.claude.json').read_text(encoding='utf-8'))
        claude_json['projects'] = {str(fixture.repo): {'hasTrustDialogAccepted': True}}
        (fixture.home / '.claude.json').write_text(json.dumps(claude_json), encoding='utf-8')
        shell = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']
        launch = shell['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        sequence = 0

        def type_in(data):
            nonlocal sequence
            sequence += 1
            sent = fixture.request('window_input', window['identity'], sequence=sequence, request_id=str(uuid.uuid4()), data=data)
            assert sent['ok'], sent

        def screen():
            return strip((fixture.state / 'traces' / launch / 'pty.raw').read_text(encoding='utf-8', errors='replace'))

        def link():
            answer = fixture.request('native_link', fixture.operator, launch=launch)
            assert answer.get('ok'), answer
            return answer['link']

        def native():
            return fixture.request('pane_status', thread=shell['thread']).get('native_session')

        def sessions_with(text):
            # Claude Code's own records: the session files whose lines carry this text.
            return sorted({line['sessionId'] for path in (fixture.home / '.claude/projects').glob('*/*.jsonl')
                           for line in map(json.loads, filter(str.strip, path.read_text(encoding='utf-8').splitlines()))
                           if text in json.dumps(line, ensure_ascii=False) and line.get('sessionId')})

        def reported(session):
            with sqlite3.connect('file:' + str(fixture.state / 'state.sqlite3') + '?mode=ro', uri=True) as db:
                rows = db.execute("SELECT data FROM orchestration_events WHERE launch=? AND type='shell_native_session'", (launch,)).fetchall()
            return any(json.loads(row[0]).get('session') == session for row in rows)

        type_in('claude --model claude-haiku-5-5 --permission-mode default --allowedTools Bash\r')
        fixture.wait('外层 Claude 启动', lambda: 'ClaudeCodev' in screen() and '❯' in screen().rsplit('ClaudeCodev', 1)[1], 60)
        type_in(f'运行内层 Claude。{outer_marker}')
        time.sleep(1)
        type_in('\r')
        fixture.wait('内层的模型请求到了', lambda: held, 60)
        outer = fixture.wait('外层会话写进记录', lambda: (lambda found: found[0] if len(found) == 1 else None)(sessions_with(outer_marker)), 30)
        inner = fixture.wait('内层会话写进记录', lambda: (lambda found: found[0] if len(found) == 1 else None)(
            [session for session in sessions_with(inner_marker) if session != outer]), 30)
        fixture.wait('内层的钩子到了后台', lambda: reported(inner), 30)
        report['observed'].update(outer=outer, inner=inner)

        # 1, 2: while the inner CLI runs, the terminal still names the outer one's session.
        during = link()
        report['observed'].update(during_link=during, during_native=native())
        check('during_inner_link_is_outer', during.get('available') and during.get('session') == outer, during)
        check('during_inner_native_is_outer', report['observed']['during_native'] == outer, report['observed']['during_native'])

        # 3: after the inner CLI ends and the outer turn finishes.
        hold.set()
        fixture.wait('外层回复', lambda: screen().split(outer_marker, 1)[-1].count('外层完成。') >= 1, 120)
        time.sleep(2)
        after = link()
        report['observed'].update(after_link=after, after_native=native())
        check('after_inner_link_is_outer', after.get('available') and after.get('session') == outer, after)
        check('after_inner_native_is_outer', report['observed']['after_native'] == outer, report['observed']['after_native'])

        # 4: a restarted daemon rebuilds the reports from the records; the outer one is still the one in front.
        fixture.run_cli('daemon_stop')
        (fixture.dir / 'operator.json').rename(fixture.dir / 'operator-before-restart.json')
        fixture.run_cli('daemon_start', '--launch-config', str(fixture.dir / 'launch-config.json'))
        fixture.wait('后台恢复结束', lambda: fixture.request('pane_layout').get('recovering') is False, 30)
        fixture.operator = json.loads((fixture.dir / 'operator.json').read_text(encoding='utf-8'))
        restarted = link()
        report['observed']['restarted_link'] = restarted
        check('after_restart_link_is_outer', restarted.get('available') and restarted.get('session') == outer, restarted)
        report['observed']['restarted_native'] = native()
        check('after_restart_native_is_outer', report['observed']['restarted_native'] == outer, report['observed']['restarted_native'])

        # 5: the outer CLI exits; nothing is named any more.
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        sequence = 0
        if args.front_failure:
            (fixture.state / 't246-fail-front').write_text('', encoding='utf-8')
        type_in('/exit')
        time.sleep(1)
        type_in('\r')
        # Read without native_link (which reads the front itself): the terminal's own front recheck clears the session
        # once the outer CLI has left the front, within one recheck (T-246 review, finding 1); a recheck that fails
        # leaves no session standing either (re-review, finding 2).
        exit_typed = time.time()
        fixture.wait('外层会话从终端状态清掉', lambda: native() is None, 30)
        report['observed']['native_cleared_after_s'] = round(time.time() - exit_typed, 2)
        # The CLI's own exit, then at most one recheck (5 s) after the line typed (first check 1.5 s after it).
        check('native_cleared_within_recheck', report['observed']['native_cleared_after_s'] <= 10, report['observed']['native_cleared_after_s'])
        if args.front_failure:
            (fixture.state / 't246-fail-front').unlink()
        exited = fixture.wait('外层退出后前台为空', lambda: (lambda value: value if value['cli'] is None else None)(link()), 30)
        check('after_exit_unavailable', exited['available'] is False, exited)
        report['status'] = 'PASS'
    except Exception as error:
        report.update(status='INCOMPLETE', error=f'{type(error).__name__}: {error}')
    finally:
        hold.set()
        try:
            fixture.stop()
            report['core_cleanup'] = fixture.core_cleanup
        except AssertionError as error:
            report.update(status='INCOMPLETE', residue=str(error))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        if report['status'] == 'PASS':
            shutil.rmtree(fixture.dir)
    print(json.dumps({'status': report['status'], 'checks': report['checks'], 'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
