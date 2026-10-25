"""T-145: real Electron/CDP -> daemon -> managed worker PTY/gate/records page.

The CLI is t145_mouse_receiver.c (native deterministic receiver, no vendor/model).
Failure modes (listed before implementation):
1. Mouse motion/wheel/focus creates user_inputs or human_intervention events.
2. Filtering swallows/changes bytes, so the CLI loses its requested mouse events.
3. Actual text, cursor keys, Enter, or literal protocol-looking paste is lost.
4. Old erroneous records are deleted/reclassified rather than retained.
5. Tests inject input through a bridge instead of CDP, or a report never occurs.
6. Input.insertText alone has no keypress and is ignored by xterm's enabled
   screenReaderMode; a failed injection must not look like lost PTY bytes.
7. Waiting for the optional accessibility tree times out when T-143 leaves
   screen reader support off; observe visible rendered rows in either mode.
--revision runs the same assertions on the specified production tree; --mutant
recreates recording or drops reports before the PTY. Summary paths are exclusive.
"""
import argparse
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import traceback
import uuid

from scripted_claude import Electron, Fixture, ROOT


class NativeFixture(Fixture):
    def run_cli(self, *arguments):
        if arguments[0] == 'daemon_start':
            config = Path(arguments[arguments.index('--launch-config') + 1])
            value = json.loads(config.read_text(encoding='utf-8'))
            value.update(codex_bin=str(self.dir / 'mouse-cli'), codex_home=str(self.dir / 'receiver-home'))
            config.write_text(json.dumps(value), encoding='utf-8')
        return super().run_cli(*arguments)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['record-reports', 'drop-reports'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  runtime='real Electron/daemon/gate/node-pty; native fixture CLI, zero model calls', checks=[])
    patches = {
        'record-reports': [('src/panes.ts', 'if (!protocolReport) await record(text, control);', 'await record(text, control);')],
        'drop-reports': [('src/panes.ts', 'pane.pty.write(binary ? bytes : data);', 'if (!protocolReport) pane.pty.write(binary ? bytes : data);')],
    }.get(args.mutant, [])
    fixture = None
    electron = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    try:
        def no_model(body):
            raise AssertionError('native receiver must not call a model')
        fixture = NativeFixture('t145-', no_model, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        home = fixture.dir / 'receiver-home'
        home.mkdir()
        compiled = subprocess.run(['/usr/bin/clang', '-Wall', '-Wextra', '-Werror', '-std=c11',
                                   str(ROOT / 'workbench/tests/t145_mouse_receiver.c'), '-o', str(fixture.dir / 'mouse-cli')],
                                  capture_output=True, text=True, timeout=60)
        assert compiled.returncode == 0, compiled.stderr
        fixture.start(str(fixture.dir / 'mouse-cli'), {'value.txt': 'unchanged\n'})
        card = fixture.out / 'card.json'
        card.write_text(json.dumps(dict(id='T-1', source=None, goal='只验证终端输入，不交付或集成', non_goals=['无模型'],
            paths=dict(allow=['value.txt'], deny=[]), oracle_paths=['value.txt'],
            completion_conditions=[dict(argv=['python3', '-c', 'raise SystemExit(0)'])], red_commands=[], task_type='后端逻辑',
            repair_target=None, complexity='S', executor=dict(cli='Codex', model='fixture-no-model', effort='high'), base_commit=None, writer=None)), encoding='utf-8')
        assert fixture.request('card_save', fixture.terminal, task='T-1', card=str(card), expected_version=0)['ok']
        assert fixture.request('create', fixture.terminal, task='T-1', project='demo', repo=str(fixture.repo), branch='refs/heads/main', card_version=1)['ok']
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        launch = attempt['runtime_identity']['launch']
        report['attempt'] = attempt
        fixture.wait('受管 receiver 就绪并收到派发', lambda: (home / 'received.bin').exists() and b'\x1b[201~\r' in (home / 'received.bin').read_bytes(), 30)
        native = fixture.request('pane_process_info', fixture.operator, thread=attempt['thread_id'])
        report['receiver_identity'] = {key: native.get(key) for key in ('ok', 'leader', 'native_session', 'failed')}
        check('receiver_native_identity_bound', native.get('ok') and native.get('leader') and
              native.get('native_session') == '00000000-0145-4000-8000-000000000001' and not native.get('failed'), report['receiver_identity'])

        def inputs():
            with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
                return [json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]

        def events():
            result = fixture.request('events', fixture.operator, task='T-1')
            assert result.get('ok'), result
            return [row for row in result['events'] if row['type'] == 'human_intervention']

        # Seed historical fixture data, before observing the production path;
        # subsequent UI input must leave both immutable historical rows alone.
        historical = dict(id=str(uuid.uuid4()), schema=1, form='action', text='\x1b[<35;9;3M',
                          target=dict(project='demo', task=attempt['task_id'], attempt=attempt['attempt_id'],
                                      thread=attempt['thread_id'], turn=None, message=None, request=None),
                          channel='terminal-window', certainty='observed', created_at='2026-10-22T00:00:00.000Z',
                          source_ref=dict(command_id='historical-t145'))
        with sqlite3.connect(fixture.state / 'state.sqlite3') as db:
            db.execute('INSERT INTO user_inputs(id,task,message,data) VALUES (?,?,?,?)',
                       (historical['id'], attempt['task_id'], None, json.dumps(historical)))
            db.execute('INSERT INTO events(time,task,attempt,type,details) VALUES (?,?,?,?,?)',
                       (historical['created_at'], attempt['task_id'], attempt['attempt_id'], 'human_intervention',
                        json.dumps(dict(input_id=historical['id'], fixture='historical false intervention'))))
        before = inputs()
        before_events = events()
        report['before_inputs'] = before

        electron = Electron(fixture, 't145-' + uuid.uuid4().hex[:10])
        electron.until('项目', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        electron.until('worker', f'!!document.querySelector(\'[data-agent-launch="{launch}"]\')')
        electron.evaluate(f'document.querySelector(\'[data-agent-launch="{launch}"]\').click()')
        pane_selector = f'[data-pane-key][data-launch-id="{launch}"]'
        textarea = json.dumps(pane_selector + ' .xterm-helper-textarea')
        electron.until('终端可输入', f'(()=>{{const p=document.querySelector({json.dumps(pane_selector + "[data-input-enabled=true]")});return !!p?.getClientRects().length && !!p.querySelector("[data-restoring=false]") && !!p.querySelector(".xterm-helper-textarea")}})()')
        (home / 'enable-mouse').touch(exist_ok=False)
        # T-175: the WebGL renderer draws on a canvas, so the ready line is read from the PTY record; the pane must be visible.
        fixture.wait('鼠标模式输出已到终端', lambda: 'T145_MOUSE_READY' in (fixture.state / 'traces' / launch / 'pty.raw').read_text(encoding='utf-8', errors='replace'), 60)
        electron.until('终端画面可见', f'!!document.querySelector({json.dumps(pane_selector + " .xterm-screen")})?.getClientRects().length')
        time.sleep(.5)
        rect = electron.evaluate(f'(()=>{{const r=document.querySelector({json.dumps(pane_selector + " .xterm-screen")}).getBoundingClientRect();return {{x:r.x,y:r.y,w:r.width,h:r.height}}}})()')
        x, y = round(rect['x'] + min(80, rect['w'] / 2)), round(rect['y'] + min(55, rect['h'] / 2))

        def cdp(method, **params):
            run = subprocess.run(['node', str(ROOT / 'workbench/tests/t145_cdp.mjs'), str(electron.port), method, json.dumps(params)],
                                 capture_output=True, text=True, timeout=25)
            assert run.returncode == 0, run.stderr

        offset = (home / 'received.bin').stat().st_size
        size = json.loads((home / 'mouse-ready').read_text(encoding='utf-8'))
        expected_motion = b''.join(f'\x1b[<35;{int((x + dx - rect["x"]) / (rect["w"] / size["cols"])) + 1};'
                                   f'{int((y - rect["y"]) / (rect["h"] / size["rows"])) + 1}M'.encode()
                                   for dx in (0, 18, 37))
        for dx in (0, 18, 37):
            cdp('Input.dispatchMouseEvent', type='mouseMoved', x=x + dx, y=y, button='none')
        fixture.wait('三次移动均到 PTY', lambda: (home / 'received.bin').stat().st_size >= offset + len(expected_motion), 10)
        observed_motion = (home / 'received.bin').read_bytes()[offset:]
        check('motion_bytes_match_coordinates_exactly', observed_motion == expected_motion,
              dict(expected_hex=expected_motion.hex(), actual_hex=observed_motion.hex(), rect=rect, size=size))
        cdp('Input.dispatchMouseEvent', type='mouseWheel', x=x + 37, y=y, deltaX=0, deltaY=96)
        # Switch actual DOM focus via CDP clicks, including the terminal and a
        # nonterminal control; existing 1004 interception is intentionally kept.
        cdp('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button='left', clickCount=1)
        cdp('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button='left', clickCount=1)
        electron.evaluate('document.querySelector("[data-records-tab]").focus()')
        electron.evaluate(f'document.querySelector({textarea}).focus()')
        time.sleep(.8)
        mouse = (home / 'received.bin').read_bytes()[offset:]
        report['mouse_bytes_hex'] = mouse.hex()
        # Expected SGR grammar and button codes come from the mouse protocol.
        check('cli_receives_motion', bool(re.search(rb'\x1b\[<35;[0-9]+;[0-9]+M', mouse)), repr(mouse))
        check('cli_receives_wheel', bool(re.search(rb'\x1b\[<6[45];[0-9]+;[0-9]+M', mouse)), repr(mouse))
        check('cli_receives_only_complete_reports', bool(re.fullmatch(rb'(?:\x1b\[<[0-9]+;[0-9]+;[0-9]+[Mm])+', mouse)), repr(mouse))
        check('mouse_focus_do_not_create_records', inputs() == before, inputs())
        check('mouse_focus_do_not_create_interventions', events() == before_events, events())

        # Focus mode is intercepted by the existing renderer. Exercise focus and
        # device reports directly through the same authenticated window entry as
        # well, proving exact forwarding even when a client emits these reports.
        window = fixture.request('window_open', fixture.operator, launch=launch, task=attempt['task_id'])
        assert window.get('ok'), window
        replies = ['\x1b[I', '\x1b[O', '\x1b[12;34R', '\x1b[?1;2c']
        reply_offset = (home / 'received.bin').stat().st_size
        for sequence, reply in enumerate(replies, 1):
            sent = fixture.request('window_input', window['identity'], sequence=sequence, request_id=str(uuid.uuid4()), data=reply)
            assert sent.get('ok'), sent
        expected_replies = ''.join(replies).encode()
        fixture.wait('焦点和设备回复到 PTY', lambda: (home / 'received.bin').stat().st_size >= reply_offset + len(expected_replies), 10)
        check('focus_device_reports_forwarded_exactly', (home / 'received.bin').read_bytes()[reply_offset:] == expected_replies)
        check('focus_device_reports_unrecorded', inputs() == before and events() == before_events)

        # One printable native key => one xterm onData => one input/intervention.
        # Input.insertText emits only an input event, which xterm deliberately
        # ignores in screenReaderMode. A char event follows its keypress path.
        typed = chr(ord('A') + uuid.uuid4().int % 26)
        report['typed'] = typed
        typing_focused = electron.evaluate(f'''(()=>{{
          const el=document.querySelector({textarea}); el.focus();
          window.__t145KeyboardEvents=[];
          for (const type of ['keypress','beforeinput','input']) el.addEventListener(type,event=>{{
            window.__t145KeyboardEvents.push({{type:event.type,isTrusted:event.isTrusted,
              key:event.key??null,charCode:event.charCode??null,data:event.data??null,inputType:event.inputType??null}});
          }},true);
          return document.activeElement===el;
        }})()''')
        check('native_typing_target_focused', typing_focused)
        text_offset = (home / 'received.bin').stat().st_size
        cdp('Input.dispatchKeyEvent', type='char', key=typed, text=typed, unmodifiedText=typed)
        report['keyboard_events'] = electron.evaluate('window.__t145KeyboardEvents')
        check('native_printable_keypress_received', any(event['type'] == 'keypress' and event['isTrusted'] and
              event['charCode'] == ord(typed) for event in report['keyboard_events']), report['keyboard_events'])
        try:
            fixture.wait('真实打字到 PTY', lambda: typed.encode() in (home / 'received.bin').read_bytes()[text_offset:], 10)
        finally:
            report['typed_bytes_hex'] = (home / 'received.bin').read_bytes()[text_offset:].hex()
            report['inputs_after_typing'] = inputs()
        check('typed_bytes_forwarded_exactly_once', (home / 'received.bin').read_bytes()[text_offset:] == typed.encode(), report['typed_bytes_hex'])
        after = inputs()
        check('one_real_input_creates_one_record', len(after) == len(before) + 1 and after[-1]['text'] == typed, after)
        check('one_real_input_creates_one_intervention', len(events()) == len(before_events) + 1, events())
        check('historical_record_unchanged', next(row for row in after if row['id'] == historical['id']) == next(row for row in before if row['id'] == historical['id']))
        electron.evaluate('document.querySelector("[data-records-tab]").click()')
        electron.until('记录页', f'document.querySelectorAll(".user-input-page tr[data-input-id]").length === {len(after)}')
        shown = electron.evaluate('[...document.querySelectorAll(".user-input-page tr[data-input-id]")].map(r=>({id:r.dataset.inputId,text:r.innerText,marked:!!r.dataset.intervention}))')
        report['records_rows'] = shown
        check('records_page_retains_history_and_only_new_typing', {row['id'] for row in shown} == {row['id'] for row in after} and
              any(row['id'] == after[-1]['id'] and typed in row['text'] and row['marked'] for row in shown), shown)
        electron.screenshot(fixture.out / 'records.png')
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        try:
            if electron:
                electron.stop()
            if fixture:
                fixture.stop()
            report['cleanup_complete'] = True
        except Exception as error:
            report.update(status='INCOMPLETE', cleanup_error=str(error))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
