"""T-138：真实 Electron/CDP → renderer → 后台 → PTY 字节。

失败方式（先列再写，期望来自 T-138 的“打出”及任务卡）：
1. 行中间 composition 提交了 textarea 的末尾文字，而非刚输入的“打出”。
2. 第一次正确，但连续三次中间插入、回车后再次插入发生错位或重复。
3. 只测默认读屏关闭，漏掉设置中可用的读屏开启状态。
4. 绕过浏览器输入直接调用 a2a.input，或直接改 textarea.value 制造红态。
5. Electron/后台未启动、没有可信 composition 事件，却误称已复现。
6. 只修了固定的两字词；普通键入后第一次中间 IME 提交仍然错位。
7. 只在 onData 发送前清空，导致 xterm 读不到提交文字；或组合中途被清空。

原始输入仅由 CDP imeSetComposition/insertText/dispatchKeyEvent 注入。
DOM 只用于导航、聚焦和观察，不赋值 textarea，不改 xterm 私有对象。
--revision 指定生产版本；summary 独占创建，不覆盖证据。
CDP 回传中 compositionend.isTrusted=false（开始、更新、输入为 true）。
保留各事件原始标志；要求可信开始/更新/输入及实际结束，不注入补偿事件。
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
import uuid

from scripted_claude import Electron, Fixture, ROOT, quote


RECEIVER = '''import os, sys, termios, tty
from pathlib import Path
output = Path(sys.argv[1])
previous = termios.tcgetattr(0)
try:
    tty.setraw(0)
    with output.open('xb', buffering=0) as stream:
        os.write(1, b'\\r\\nT138_READY\\r\\n')
        while True:
            data = os.read(0, 4096)
            if not data:
                break
            stream.write(data)
            os.write(1, data.replace(b'\\r', b'\\r\\n'))
finally:
    termios.tcsetattr(0, termios.TCSANOW, previous)
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['retain-input'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，必须换新路径'
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, harness_version=2,
                  code_version=subprocess.check_output(['git', 'rev-parse', args.revision or 'HEAD'], cwd=ROOT, text=True).strip(),
                  runtime='real Electron/daemon/node-pty, native raw receiver; zero model calls',
                  checks=[], cases=[], defect_reproduced=False)
    fixture = electron = None
    try:
        def no_model(body):
            raise AssertionError('本测试不应调用模型')
        patches = [('app/renderer.tsx',
                    "if (!composing) clearInputTimer = setTimeout(() => { term.textarea!.value = ''; }, 0);",
                    '/* T-138 mutant: retain submitted textarea contents. */')] if args.mutant else []
        fixture = Fixture('t138-', no_model, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        fixture.start('/usr/bin/false', {'README.md': 'IME byte receiver fixture\n'})
        receiver = fixture.dir / 'receiver.py'
        receiver.write_text(RECEIVER, encoding='utf-8')
        received = fixture.out / 'received.bin'
        window = fixture.request('window_open', fixture.operator, project='demo', launch=fixture.terminal_launch)
        assert window.get('ok'), window
        result = fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()),
                                 data=f'python3 -u {quote(str(receiver))} {quote(str(received))}\r')
        assert result.get('ok'), result
        fixture.wait('raw PTY receiver 就绪', received.exists, 20)
        fixture.request('window_close', window['identity'])
        electron = Electron(fixture, 't138-' + uuid.uuid4().hex[:10])
        electron.until('项目', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        launch = fixture.terminal_launch
        electron.until('普通终端', f'!!document.querySelector(\'[data-agent-launch="{launch}"]\')')
        electron.evaluate(f'document.querySelector(\'[data-agent-launch="{launch}"]\').click()')
        selector = f'.pane[data-launch-id="{launch}"]'
        textarea = json.dumps(selector + ' .xterm-helper-textarea')
        electron.until('终端可输入', f'''(()=>{{const p=document.querySelector({json.dumps(selector)});
          return !!p?.getClientRects().length && p.dataset.inputEnabled==='true' && !!p.querySelector('[data-restoring=false]');}})()''')
        electron.evaluate(f'''(()=>{{const el=document.querySelector({textarea}); el.focus(); window.__t138Events=[];
          for(const type of ['compositionstart','compositionupdate','compositionend','input','keydown','keyup'])
            el.addEventListener(type,e=>window.__t138Events.push({{type:e.type,trusted:e.isTrusted,
              data:e.data??null,key:e.key??null,value:el.value,start:el.selectionStart,end:el.selectionEnd}}));
        }})()''')

        def cdp(method, **params):
            run = subprocess.run(['node', str(ROOT / 'workbench/tests/t145_cdp.mjs'), str(electron.port), method,
                                  json.dumps(params, ensure_ascii=False)], capture_output=True, text=True, timeout=25)
            assert run.returncode == 0, run.stderr

        def state():
            return electron.evaluate(f'''(()=>{{const el=document.querySelector({textarea});return {{
              value:el.value,start:el.selectionStart,end:el.selectionEnd,focused:document.activeElement===el}}}})()''')

        def key(name, code):
            cdp('Input.dispatchKeyEvent', type='keyDown', key=name, code=name, windowsVirtualKeyCode=code, nativeVirtualKeyCode=code)
            cdp('Input.dispatchKeyEvent', type='keyUp', key=name, code=name, windowsVirtualKeyCode=code, nativeVirtualKeyCode=code)
            time.sleep(.15)

        def compose(text):
            cdp('Input.imeSetComposition', text='dachu' if text == '打出' else text,
                selectionStart=5 if text == '打出' else len(text), selectionEnd=5 if text == '打出' else len(text))
            cdp('Input.imeSetComposition', text=text, selectionStart=len(text), selectionEnd=len(text))
            cdp('Input.insertText', text=text)
            time.sleep(.5)

        def type_ascii(text):
            for letter in text:
                cdp('Input.dispatchKeyEvent', type='char', key=letter, text=letter, unmodifiedText=letter)
            time.sleep(.5)

        def sample(name, action, expected, mode):
            offset = received.stat().st_size
            before = state()
            event_offset = electron.evaluate('window.__t138Events.length')
            action()
            time.sleep(.3)
            actual = received.read_bytes()[offset:]
            events = electron.evaluate(f'window.__t138Events.slice({event_offset})')
            case = dict(name=name, screen_reader=mode, before=before, after=state(),
                        expected=expected, actual=actual.decode('utf-8', errors='replace'),
                        expected_hex=expected.encode().hex(), actual_hex=actual.hex(), events=events,
                        passed=actual == expected.encode())
            report['cases'].append(case)
            if name.startswith('middle') and actual == '怪了'.encode() and expected == '打出':
                report['defect_reproduced'] = True
            return case

        # Both are product-supported settings. Real settings UI changes the mode.
        for mode in (False, True):
            if mode:
                electron.evaluate('document.querySelector(\'[aria-label="设置"]\').click()')
                electron.until('设置打开', 'document.querySelector(".settings-dialog").open')
                electron.evaluate('document.querySelector(\'[aria-labelledby="settings-terminal-accessibility"] input\').click()')
                electron.evaluate('document.querySelector(\'[aria-label="关闭设置"]\').click()')
            electron.until('读屏设置已应用',
                           f'Boolean(document.querySelector({json.dumps(selector + " .xterm-accessibility")})) === {str(mode).lower()}')
            report['checks'].append(dict(name='screen_reader_mode_applied', mode=mode, passed=True))
            electron.evaluate(f'document.querySelector({textarea}).focus()')
            key('Enter', 13)
            seed = sample('seed', lambda: compose('前面怪了'), '前面怪了', mode)
            assert seed['passed'], f'种子输入未成功，不能称作中间插入红态：{seed}'
            for number in range(1, 4):
                key('ArrowLeft', 37)
                key('ArrowLeft', 37)
                sample(f'middle-{number}', lambda: compose('打出'), '打出', mode)
            enter = sample('enter', lambda: key('Enter', 13), '\r', mode)
            assert enter['passed'], enter
            seed = sample('seed-after-enter', lambda: compose('前面怪了'), '前面怪了', mode)
            assert seed['passed'], seed
            key('ArrowLeft', 37)
            key('ArrowLeft', 37)
            sample('middle-after-enter', lambda: compose('打出'), '打出', mode)
            key('Enter', 13)
            ascii_seed = sample('ascii-seed', lambda: type_ascii('prefix-tail'), 'prefix-tail', mode)
            assert ascii_seed['passed'], ascii_seed
            key('ArrowLeft', 37)
            key('ArrowLeft', 37)
            sentinel = '新词' + uuid.uuid4().hex[:4]
            sample('middle-sentinel-after-ascii', lambda: compose(sentinel), sentinel, mode)
            electron.screenshot(args.summary.with_name(args.summary.stem + f'-screen-reader-{mode}.png'))
        compositions = [case for case in report['cases'] if case['name'] not in ('enter', 'ascii-seed')]
        report['checks'].append(dict(name='trusted_composition_input_and_observed_end', passed=all(
            all(any(event['type'] == kind and event['trusted'] for event in case['events'])
                for kind in ('compositionstart', 'compositionupdate', 'input')) and
            any(event['type'] == 'compositionend' for event in case['events'])
            for case in compositions), end_trusted=[
                dict(name=case['name'], screen_reader=case['screen_reader'], trusted=event['trusted'])
                for case in compositions for event in case['events'] if event['type'] == 'compositionend']))
        report['status'] = 'PASS' if all(case['passed'] for case in report['cases']) and all(c['passed'] for c in report['checks']) else 'NO_GO'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        cleanup = []
        for resource in (electron, fixture):
            if resource:
                try:
                    resource.stop()
                except Exception as error:
                    cleanup.append(str(error))
        report['cleanup_errors'] = cleanup
        if cleanup:
            report['status'] = 'INCOMPLETE'
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps({key: report[key] for key in ('status', 'defect_reproduced', 'cases')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
