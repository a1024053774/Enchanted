"""T-187：真实 opencode 在项目终端里经包装脚本启动，拿到开局说明，对“你来当执行主控”直接运行 a2a request；用户在
后台批准；侧栏状态随 opencode 自己报给终端的 OSC 7501 变化（运行中、空闲、等待用户回答）。
隔离后台、PTY、Electron；用户自己的 opencode（不登录，用它默认的免费模型；--standalone 的私有服务只在本会话运行，
会话数据照常写进用户 opencode 自己的数据目录，不写它的配置）。真实提示 2 条。

ticket 原话（用户 2026-10-25）：“增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下”。期望来自
ticket 的验收（申请主控→批准；状态在侧栏正确，做不到的显示未知）与开局说明要点（T-181、T-185）。本测试只走到批准与
状态，不派 worker：worker 用哪种 CLI 待用户决定（inbox 20261025T150744Z）。

失败方式（先列再写）：
1. 开局说明没进 opencode 的会话：它不知道 a2a，在文件系统里找，或先问用户是否批准，而不是运行 a2a request。
2. 角色申请记成未知 CLI（不是 opencode）。
3. 侧栏状态不跟着 opencode 的回合走：回合中不是运行中、结束后不是空闲、提问时不是等待用户回答。
4. 登录、权限或模型错误被当成产品结果（如实记录，不判通过）。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import time
import traceback
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture  # noqa: E402

PROMPT = '你来当执行主控。申请生效以后先停下，什么都不要派，只回复“已就绪”。'
QUESTION = '用你的提问工具问我一个选择题：喜欢红色还是蓝色？只问这一个问题。'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    parser.add_argument('--revision')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, real_model_turns=0, cli=None,
                  checks=[], failed=[], observed={}, states=[])

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    fixture = Fixture('t187r-', lambda body: ('unused', [], '好的。'), revision=args.revision)
    report['fixture'] = str(fixture.dir)
    electron = None

    def raw(term):
        return (fixture.state / 'traces' / term['launch'] / 'pty.raw').read_text(encoding='utf-8', errors='replace')

    def text(term):
        return re.sub(r'[ \t]+', ' ', re.sub(r'\x1b\[[0-9;?<>=]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw(term)))

    def reports(term):
        return re.findall(r'\x1b\]7501;([^\x07\x1b]*)', raw(term))

    def type_in(term, data):
        term['sequence'] += 1
        sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    def row(term):
        snapshot = fixture.request('sidebar_snapshot')
        return next((r for r in snapshot.get('agents', []) + snapshot.get('terminals', []) if r.get('id') == term['launch']), {})

    def watch(term, label, until, seconds):
        """Record each change of the sidebar state with the CLI's last report, until `until(state)` or time runs out."""
        deadline, last = time.time() + seconds, None
        while time.time() < deadline:
            current = (row(term).get('state'), (reports(term) or [None])[-1])
            if current != last:
                report['states'].append(dict(phase=label, t=round(time.time(), 1), state=current[0], report=(current[1] or '')[:60]))
                last = current
            if until(current[0], current[1] or ''):
                return current
            time.sleep(0.5)
        return last

    def shown(term, label, expected):
        """What the sidebar row itself shows (data-agent-state), once the window has refreshed."""
        selector = f"document.querySelector('[data-agent-launch=\"{term['launch']}\"]')?.dataset.agentState ?? null"
        deadline, seen = time.time() + 8, None
        while time.time() < deadline:
            seen = electron.evaluate(selector)
            if seen == expected:
                break
            time.sleep(0.5)
        report['observed'][f'sidebar_{label}'] = seen
        check(f'sidebar_shows_{label}', seen == expected, seen)

    try:
        fixture.start(args.claude, {'README.md': '# demo\n'})
        assert fixture.request('role_release', fixture.terminal)['ok']
        electron = Electron(fixture, 't187r-' + fixture.dir.name[6:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        launch = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        term = dict(name='T', launch=launch, identity=window['identity'], sequence=0)
        electron.until('终端窗格', f"(()=>{{const r=document.querySelector('[data-agent-launch=\"{launch}\"]');if(r)r.click();"
                       f"return !!document.querySelector('.pane[data-launch-id=\"{launch}\"]')}})()", 30)
        type_in(term, 'opencode\r')
        fixture.wait('opencode 就绪', lambda: any(r.startswith('state=idle') for r in reports(term)), 90)
        time.sleep(3)
        type_in(term, PROMPT)
        time.sleep(1)
        type_in(term, '\r')
        report['real_model_turns'] += 1
        pending = fixture.wait('角色申请', lambda: [r for r in fixture.request('sidebar_snapshot').get('role_requests', [])
                                                   if r.get('launch') == launch], 240)
        report['cli'] = pending[0].get('cli')
        check('request_cli_opencode', pending[0].get('cli') == 'opencode', pending[0])
        assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)['ok']
        held = fixture.wait('角色生效', lambda: row(term).get('role') == 'controller' or None, 60)
        seen = watch(term, 'after_approval', lambda state, last: state == 'idle' and last.startswith('state=idle'), 240)
        check('idle_after_turn', seen and seen[0] == 'idle', seen)
        shown(term, 'idle_after_turn', 'idle')
        check('running_seen_during_turn', any(s['phase'] == 'after_approval' and s['state'] == 'running' for s in report['states']), report['states'])
        electron.screenshot(fixture.out / 'opencode-controller-idle.png')

        type_in(term, QUESTION)
        time.sleep(1)
        type_in(term, '\r')
        report['real_model_turns'] += 1
        seen = watch(term, 'question', lambda state, last: state == 'waiting_user_answer', 180)
        check('question_waiting_user_answer', seen and seen[0] == 'waiting_user_answer', seen)
        shown(term, 'question_waiting', 'waiting_user_answer')
        electron.screenshot(fixture.out / 'opencode-controller-question.png')
        type_in(term, '\r')  # the user picks the first choice
        seen = watch(term, 'answered', lambda state, last: state == 'idle' and last.startswith('state=idle'), 180)
        check('idle_after_answer', seen and seen[0] == 'idle', seen)
        shown(term, 'idle_after_answer', 'idle')

        screen = text(term)
        report['observed']['model'] = sorted(set(re.findall(r'Build\s*·\s*([A-Za-z][A-Za-z0-9 .\-]*?)\s*·', screen)))
        report['observed']['a2a_commands'] = sorted(set(re.findall(r'a2a (?:help|request \w+|whoami)', screen)))
        report['observed']['searched_filesystem'] = bool(re.search(r'which a2a|command -v a2a|find [^\n]*a2a|terminal/bin', screen))
        check('ran_a2a_request', 'a2a request executor' in report['observed']['a2a_commands'], report['observed']['a2a_commands'])
        check('did_not_search_filesystem', not report['observed']['searched_filesystem'])
        (fixture.out / 'screen.txt').write_text(screen[-20000:], encoding='utf-8')
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()[-2000:]
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
