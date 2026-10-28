"""T-206：受管窗格里的用户输入在发出时记一条，不逐键记。
真实 Electron 窗口（CDP 发原生按键给 xterm）、真实后台与门禁，worker 是真实 Claude Code（模型换成本地脚本化接口，零真实模型调用）。

预期来自需求（用户 2026-10-27：“在我消息发送成功出去的那一刻,也就是输入完之后再记录”，T-206）：
1. 打 “fiz”、退格、“x it”、回车：只记一条 message，文字是 “fix it”；人工介入一条；CLI 收到 “fix it”。
2. 打 “abc”、左方向键、“d”、回车：只记一条 message，文字是光标移动后的 “abdc”，content.keys 列出左方向键。
3. 打 “zzz”，按 Ctrl-C 清掉（没发出），再打 “done now” 回车：只记 “done now”；之后按 Esc 不记。
   用户 2026-10-27 补充：“只记录我发送之后的完整消息,不要每次操作都要记录”。
4. 写进终端的字节与按下的键一一对应，不因记录方式改变。

失败方式（先列再写）：
1. 仍逐键记录（修前）：一句话几十条，空格、退格各一条。
2. 攒草稿时退格、光标移动处理错，记下的文字与发出的不一致。
3. 没发出的草稿（被 Ctrl-C 清掉的）也被记下，或 Esc 之类的操作被单独记录。
4. 记录推迟后终端字节被改动、丢失或重复。
--revision 在该版本源码上跑同一场景（修前应失败）；--mutant 见 MUTANTS。
"""
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import traceback

from scripted_claude import Electron, Fixture

ROOT = Path(__file__).resolve().parents[2]
MUTANTS = {
    # Every chunk is recorded again, as before T-206.
    'record-every-key': [('src/panes.ts', '      if (!protocolReport) for (const entry of entries) await record(entry.text, entry.content);\n',
                          '      if (!protocolReport) await record(data, /[\\x00-\\x1f\\x7f]/.test(data) ? { action: "terminal-key", data } : undefined);\n')],
    # The draft ignores the cursor: the left arrow is listed but the text is appended at the end.
    'cursor-ignored': [('src/inputDraft.ts', '  if (key === "←") draft.cursor = Math.max(0, draft.cursor - 1);\n  else if', '  if')],
    # Ctrl-C does not start the draft over, so the cleared text is recorded with the next message.
    'ctrl-c-keeps-draft': [('src/inputDraft.ts', 'const CLEARS = new Set(["\\x03", "\\x04"]);', 'const CLEARS = new Set<string>();')],
}


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
        # The worker reads its task and waits; every later request is the user's next sentence.
        return 'worker', [], '收到。'

    try:
        fixture = Fixture('t206-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
        report['fixture'] = str(fixture.dir)
        (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        fixture.start(args.claude, {'README.md': 'T-206 fixture\n', 'check.py': 'raise SystemExit(0)\n'})
        electron = Electron(fixture, 't206-' + fixture.dir.name[5:])
        electron.until('项目可见', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        fixture.card('T-1', 'answer.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write',
                                     model='claude-haiku-5-5', effort='low')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        pane_status = lambda: fixture.request('pane_status', thread=attempt['thread_id'])
        idle = lambda: (lambda p: p.get('state') == 'idle' and not p.get('writing') and not p.get('active') and not p.get('queued'))(pane_status())
        fixture.wait('worker 读完派发、空闲', idle, 120)
        rows = fixture.request('sidebar_snapshot')['agents']
        launch = next(row['id'] for row in rows if row['attempt'] == attempt['attempt_id'] and row['role'] == 'worker')
        selector = '[data-agent-launch=' + json.dumps(launch) + ']'
        electron.until('worker 侧栏可见', f'!!document.querySelector({json.dumps(selector)})')
        electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
        pane = 'document.querySelector(' + json.dumps('.pane[data-launch-id=' + json.dumps(launch) + ']') + ')'
        electron.until('worker 窗格可输入', f'{pane}?.dataset.inputEnabled === "true"')

        def cdp(method, **params):
            run = subprocess.run(['node', str(ROOT / 'workbench/tests/t145_cdp.mjs'), str(electron.port), method,
                                  json.dumps(params, ensure_ascii=False)], capture_output=True, text=True, timeout=25)
            assert run.returncode == 0, run.stderr

        def focus():
            electron.evaluate(f'{pane}.querySelector("textarea.xterm-helper-textarea").focus(), true')

        def press(key, code, virtual, text=None):
            down = dict(type='keyDown', key=key, code=code, windowsVirtualKeyCode=virtual, nativeVirtualKeyCode=virtual)
            if text is not None:
                down.update(text=text, unmodifiedText=text)
            cdp('Input.dispatchKeyEvent', **down)
            cdp('Input.dispatchKeyEvent', type='keyUp', key=key, code=code, windowsVirtualKeyCode=virtual, nativeVirtualKeyCode=virtual)
            time.sleep(.12)

        def type_text(value):
            for letter in value:
                if letter == ' ':
                    press(' ', 'Space', 32, ' ')
                else:
                    press(letter, 'Key' + letter.upper(), ord(letter.upper()), letter)

        backspace = lambda: press('Backspace', 'Backspace', 8)
        left = lambda: press('ArrowLeft', 'ArrowLeft', 37)
        enter = lambda: press('Enter', 'Enter', 13, '\r')
        escape = lambda: press('Escape', 'Escape', 27)

        def ctrl_c():
            cdp('Input.dispatchKeyEvent', type='keyDown', key='c', code='KeyC', windowsVirtualKeyCode=67, nativeVirtualKeyCode=67, modifiers=2)
            cdp('Input.dispatchKeyEvent', type='keyUp', key='c', code='KeyC', windowsVirtualKeyCode=67, nativeVirtualKeyCode=67, modifiers=2)
            time.sleep(.3)

        def inputs():
            with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
                return [json.loads(row[0]) for row in db.execute(
                    "SELECT data FROM user_inputs WHERE json_extract(data,'$.target.attempt')=? ORDER BY rowid", (attempt['attempt_id'],))]

        gate_events = lambda: fixture.request('events', fixture.operator, task='demo+T-1')['events']
        reaches_cli = lambda note: any(note in json.dumps(body['messages'], ensure_ascii=False) for body in fixture.api.bodies)

        # 1. A typo fixed with Backspace, words with a space, then Enter.
        focus(); type_text('fiz'); backspace(); type_text('x it'); enter()
        fixture.wait('CLI 收到第 1 句', lambda: reaches_cli('fix it'), 60)
        fixture.wait('worker 回到空闲', idle, 60)
        first = inputs()
        report['observed']['after_1'] = [dict(form=i['form'], text=i['text'], content=i.get('content')) for i in first]
        check('one_record_for_first_message', len(first) == 1 and first[0]['form'] == 'message' and first[0]['text'] == 'fix it',
              report['observed']['after_1'])

        # 2. The cursor moves left before the last letter.
        focus(); type_text('abc'); left(); type_text('d'); enter()
        fixture.wait('CLI 收到第 2 句', lambda: reaches_cli('abdc'), 60)
        fixture.wait('worker 再次空闲', idle, 60)
        second = inputs()[len(first):]
        report['observed']['after_2'] = [dict(form=i['form'], text=i['text'], content=i.get('content')) for i in second]
        check('one_record_for_edited_message', len(second) == 1 and second[0]['form'] == 'message' and second[0]['text'] == 'abdc' and
              '←' in (second[0].get('content') or {}).get('keys', []), report['observed']['after_2'])

        # 3. A draft cleared with Ctrl-C is never sent; the next sentence is. Then Esc, an operation, not a message.
        focus(); type_text('zzz'); ctrl_c(); type_text('done now'); enter()
        fixture.wait('CLI 收到第 3 句', lambda: reaches_cli('done now'), 60)
        fixture.wait('worker 第三次空闲', idle, 60)
        escape()
        time.sleep(2)
        third = inputs()[len(first) + len(second):]
        report['observed']['after_3'] = [dict(form=i['form'], text=i['text'], content=i.get('content')) for i in third]
        check('cleared_draft_and_esc_not_recorded', len(third) == 1 and third[0]['form'] == 'message' and third[0]['text'] == 'done now' and
              'zzz' not in json.dumps(third, ensure_ascii=False), report['observed']['after_3'])

        human = [e for e in gate_events() if e['type'] == 'human_intervention' and e['attempt'] == attempt['attempt_id']]
        report['observed']['human_interventions'] = len(human)
        check('interventions_follow_records', len(human) == len(inputs()) == 3, dict(human=len(human), inputs=len(inputs())))

        # 4. The bytes written to the terminal are the keys pressed, in order, each written once.
        mine = [e for e in fixture.request('orchestration_events', task='demo+T-1')['events'] if e['launch'] == launch]
        intents = [e['data'] for e in mine if e['type'] == 'terminal_input_write_intent']
        written = {e['data']['request_id'] for e in mine if e['type'] == 'terminal_input_written'}
        stream = ''.join(i.get('data', '') for i in intents)
        report['observed']['written_stream'] = stream
        check('terminal_bytes_unchanged', all(i['request_id'] in written for i in intents) and
              stream.startswith('fiz\x7fx it\rabc') and stream.endswith('d\rzzz\x03done now\r\x1b') and stream.count('\r') == 3, stream)
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
                except BaseException as error:
                    report.setdefault('cleanup_errors', []).append(str(error))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    print(report['status'], report.get('error', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
