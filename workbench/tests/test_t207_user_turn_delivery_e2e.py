"""T-207：用户按 Esc 打断后自己发出的那一回合里，worker 交的请求在回合结束时就被门禁受理。
真实 Electron 窗口（CDP 发原生按键给 xterm）、真实后台与门禁，worker 是真实 Claude Code（模型换成本地脚本化接口，零真实模型调用）。

预期来自需求（UAT-03 3b 发现 2；用户 2026-10-28 选“回合结束就受理”）：
1. worker 在派发回合里跑一个长命令，用户按 Esc，再打一句话按回车。worker 在这个用户回合里提交并交付。
   回合结束后门禁就是“已交付”：不用点放行，也不用让 worker 再跑一回合。
2. 窗格仍是“被打断、等用户放行”（打断语义不变）；没有出现 user_queue_release。
3. 这个用户回合的工具钩子没有被判为身份不符，回合结束没有被判为 current_turn_untrusted。
身份核对不放宽：打断之前开始的回合、再次打断后的回合，钩子仍被拒收，见 test_t207_interrupted_turn_hooks.ts。

失败方式（先列再写）：
1. 修前：用户回合的每个工具钩子都因窗格“被打断”判为不符，回合结束判为不可信，请求搁着，门禁停在 claimed。
2. 修过头：被打断的那个回合（或打断后又被打断的回合）的钩子也被放行。
3. 测试在放行或再跑一回合之后才看门禁，看到的交付不能说明“回合结束就受理”。
--revision 在该版本源码上跑同一场景；--mutant 见 MUTANTS。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback

from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory

ROOT = Path(__file__).resolve().parents[2]
MUTANTS = {
    # A turn the user started after the Esc is still treated as the interrupted one.
    'user-turn-not-marked': [('src/panes.ts', "nativeTurn: null, interruption: pane.interrupted ? pane.interruption : null };\n            pane.claudePromptId = null; pane.state = 'busy';",
                              "nativeTurn: null, interruption: null };\n            pane.claudePromptId = null; pane.state = 'busy';")],
}
SENTENCE = 'deliver now'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  runtime='real Electron/daemon/gate/Claude Code; native CDP key events; scripted Messages API; zero vendor model calls',
                  checks=[], observed={})
    fixture = electron = None

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        (report['checks'] if condition else report.setdefault('failed', [])).append(name)

    def plan(body):
        # Step 0 is the dispatch turn's long command, cut off by Esc; the rest run in the user's own turn.
        text = prompt_text(body)
        cwd = working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return 'worker', [('Bash', dict(command='python3 -c "import time; time.sleep(120)"', description='long build', timeout=180000)),
                          ('Write', dict(file_path=f'{cwd}/answer.txt', content='accepted')),
                          ('Bash', dict(command='git add answer.txt', description='stage')),
                          ('Bash', dict(command='git commit -q -m ' + quote('T207 fixture candidate'), description='commit')),
                          ('Bash', dict(command=submit, description='submit'))], '已交付。'

    try:
        fixture = Fixture('t207-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
        report['fixture'] = str(fixture.dir)
        (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        fixture.start(args.claude, {'README.md': 'T-207 fixture\n', 'check.py':
            'from pathlib import Path\nassert Path("answer.txt").read_text() == "accepted"\n'})
        electron = Electron(fixture, 't207-' + fixture.dir.name[5:])
        electron.until('项目可见', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        fixture.card('T-1', 'answer.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        status = lambda: fixture.request('status', fixture.operator, task='demo+T-1')['task']
        pane_status = lambda: fixture.request('pane_status', thread=attempt['thread_id'])
        rows = fixture.request('sidebar_snapshot')['agents']
        launch = next(row['id'] for row in rows if row['attempt'] == attempt['attempt_id'] and row['role'] == 'worker')
        events = lambda: [e for e in fixture.request('orchestration_events', task='demo+T-1')['events'] if e['launch'] == launch]
        selector = '[data-agent-launch=' + json.dumps(launch) + ']'
        electron.until('worker 侧栏可见', f'!!document.querySelector({json.dumps(selector)})')
        electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
        pane = 'document.querySelector(' + json.dumps('.pane[data-launch-id=' + json.dumps(launch) + ']') + ')'
        electron.until('worker 窗格可输入', f'{pane}?.dataset.inputEnabled === "true"')

        def cdp(method, **params):
            run = subprocess.run(['node', str(ROOT / 'workbench/tests/t145_cdp.mjs'), str(electron.port), method,
                                  json.dumps(params, ensure_ascii=False)], capture_output=True, text=True, timeout=25)
            assert run.returncode == 0, run.stderr

        def press(key, code, virtual, text=None):
            electron.evaluate(f'{pane}.querySelector("textarea.xterm-helper-textarea").focus(), true')
            down = dict(type='keyDown', key=key, code=code, windowsVirtualKeyCode=virtual, nativeVirtualKeyCode=virtual)
            if text is not None:
                down.update(text=text, unmodifiedText=text)
            cdp('Input.dispatchKeyEvent', **down)
            cdp('Input.dispatchKeyEvent', type='keyUp', key=key, code=code, windowsVirtualKeyCode=virtual, nativeVirtualKeyCode=virtual)
            time.sleep(.12)

        # 1. The dispatch turn is inside its long command; the user cuts it off and sends a sentence.
        fixture.wait('派发回合在跑长命令', lambda: any(e['type'] == 'hook_received' and '"hook_event_name":"PreToolUse"' in e['data'].get('raw_stdin', '')
                                                       for e in events()), 120)
        time.sleep(2)
        press('Escape', 'Escape', 27)
        fixture.wait('Esc 让派发回合退场', lambda: any(e['type'] == 'claude_submission_retired' and e['data'].get('reason') == 'user-esc'
                                                      for e in events()), 30)
        time.sleep(2)
        for letter in SENTENCE:
            press(' ', 'Space', 32, ' ') if letter == ' ' else press(letter, 'Key' + letter.upper(), ord(letter.upper()), letter)
        press('Enter', 'Enter', 13, '\r')
        sent = time.time()

        # 2. The user's turn ends after its submit; the gate takes the delivery then, with no release and no further turn.
        def user_turn_ended():
            seen = events()
            start = next((e['seq'] for e in seen if e['type'] == 'user_prompt_unregistered'), None)
            return start is not None and any(e['type'] == 'turn_end_signal' and e['seq'] > start for e in seen)
        fixture.wait('用户回合结束', user_turn_ended, 120)
        try:
            fixture.wait('门禁已交付', lambda: status()['state'] == 'submitted', 20)
        except BaseException as error:
            report['observed']['wait_submitted'] = str(error)
        report['observed']['seconds_after_enter'] = round(time.time() - sent, 1)
        state = status()['state']
        mine = events()
        unregistered = [e for e in mine if e['type'] == 'user_prompt_unregistered']
        user_turn = unregistered[0]['seq'] if unregistered else None
        after = [e for e in mine if user_turn is not None and e['seq'] > user_turn]
        pane_now = pane_status()
        report['observed'].update(gate_state=state, pane_interrupted=pane_now.get('interrupted'), pane_state=pane_now.get('state'),
                                  user_turns=len(unregistered),
                                  unverified=[dict(seq=e['seq'], reason=e['data'].get('reason'), hook=e['data'].get('hook_event_name'))
                                              for e in after if e['type'] == 'native_question_unverified'],
                                  relay=[dict(seq=e['seq'], type=e['type']) for e in after if e['type'].startswith('relay_')])
        check('delivered_at_turn_end', state == 'submitted', state)
        check('no_release_no_extra_turn', not any(e['type'] == 'user_queue_release' for e in mine) and len(unregistered) == 1,
              dict(release=[e['seq'] for e in mine if e['type'] == 'user_queue_release'], user_turns=len(unregistered)))
        check('still_waiting_for_release', bool(pane_now.get('interrupted')), pane_now.get('interrupted'))
        check('user_turn_hooks_trusted', user_turn is not None and not report['observed']['unverified'], report['observed']['unverified'])
        electron.screenshot(fixture.out / 'after-turn.png')
        assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
        for resource in (electron, fixture):
            if resource:
                try:
                    resource.stop()
                except BaseException as cleanup:
                    report.setdefault('cleanup_errors', []).append(str(cleanup))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    print(report['status'], report.get('error', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
