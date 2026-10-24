"""T-168：只读窗格文字重叠。真实 Electron、后台、门禁及受控 PTY；不调用模型。

失败方式（先列再写）：
1. 只读窗格把 xterm 拉伸到容器宽度，却不改 PTY 尺寸；CLI 按 PTY 列数做相对光标重绘
   （上移若干行再清屏重画），落在另一宽度的 xterm 上会擦掉别的行或留下残行（T-164 N02）。
2. 只修回放、不修实时输出，或反之。
3. 修法改动了 reviewer 的 PTY 尺寸（只读查看不应改变被查看程序的环境）。
4. 可写窗格不再按容器宽度适配，或只读窗格开始申请焦点、出现输入错误（T-161 回归）。

期望来自终端语义：同一字节流在 PTY 自身的列数下应得到的屏幕内容。样式行分两段：
159 列的行在 160 列下占一行，较窄的视图会多出残行；161 列的行在 160 列下占两行，
较宽的视图会把上一行擦掉。两段都正确才算文字不重叠。
--revision 在指定源码版本上运行；--mutant 在隔离副本中注入已知坏实现。
"""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys

from scripted_claude import Electron, Fixture, ROOT


PEER = r'''import json, os, re, subprocess, sys, time, uuid
from pathlib import Path
settings = json.loads(os.environ['T093_FIXTURE_SETTINGS'])
prompt_id = str(uuid.uuid4())
transcript = Path(os.environ['HOME']) / '.claude' / 'projects' / 't168-controlled-pty' / (os.environ['A2A_NATIVE_SESSION'] + '.jsonl')
transcript.parent.mkdir(parents=True, exist_ok=True)
transcript.touch(exist_ok=True)
def hook(name, **extra):
    command = settings['hooks'][name][0]['hooks'][0]['command']
    payload = dict(hook_event_name=name, session_id=os.environ['A2A_NATIVE_SESSION'],
                   cwd=os.getcwd(), transcript_path=str(transcript), prompt_id=prompt_id, **extra)
    result = subprocess.run(command, shell=True, input=json.dumps(payload), text=True, capture_output=True)
    print(result.stdout, result.stderr, flush=True)
    assert result.returncode == 0, (name, result.returncode)
def pattern(tag):
    # Relative redraws as a TUI computes them for a 160-column PTY.
    # The fixture PTY does not translate newlines, so lines end in CRLF as a TUI writes them.
    sys.stdout.write(tag + '_ABOVE\r\n' + 'N' * 159 + '\r\n\x1b[1A\r\x1b[J' + tag + '_NARROW_OK\r\n' +
                     tag + '_MID\r\n' + 'W' * 161 + '\r\n\x1b[2A\r\x1b[J' + tag + '_WIDE_OK\r\n')
    sys.stdout.flush()
if sys.argv[2] == '0':
    hook('SessionStart', source='startup')
else:
    text = sys.argv[1]
    # Protocol test double: this identity names this deterministic driver, never a vendor model.
    with transcript.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(type='user', sessionId=os.environ['A2A_NATIVE_SESSION'],
                                    promptId=prompt_id, message=dict(role='user', content=text))) + '\n')
    hook('UserPromptSubmit', prompt=text)
    with transcript.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(type='assistant', sessionId=os.environ['A2A_NATIVE_SESSION'],
                                    promptId=prompt_id, effort='low', message=dict(role='assistant',
                                    model='t168-controlled-pty-no-model', content=[dict(type='text',
                                    text='T168 deterministic PTY fixture; no model inference.')]))) + '\n')
    if os.environ['A2A_ROLE'] == 'worker':
        Path('T-review.txt').write_text('candidate\n', encoding='utf-8')
        subprocess.run(['git', 'add', 'T-review.txt'], check=True)
        subprocess.run(['git', 'commit', '-m', 'T168 controlled candidate'], check=True)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1)
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        result = subprocess.run(submit.replace('FULL_COMMIT_SHA', commit), shell=True, check=True, capture_output=True, text=True)
        print(result.stdout, result.stderr, flush=True)
        hook('Stop', stop_hook_active=False, effort=dict(level='low'))
    else:
        # Reviewer: one block before the view opens (replay), one after the test signals (live).
        pattern('REPLAY')
        go = Path(os.environ['T168_LIVE_SIGNAL'])
        while not go.exists():
            time.sleep(0.1)
        pattern('LIVE')
        time.sleep(3600)
'''

EXPECTED = ['_ABOVE', '_NARROW_OK', '_MID', '_WIDE_OK']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['readonly-fits-view', 'readonly-resizes-pty'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，请换新路径'
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    report = dict(status='INCOMPLETE', phase='setup', argv=sys.argv, checks=[], observed={}, model_calls=0,
                  red_reproduced=False, code_version=subprocess.check_output(['git', 'rev-parse', args.revision or 'HEAD'], cwd=ROOT, text=True).strip())
    fixture = electron = None

    def check(name, passed, detail=None):
        report['checks'].append(dict(name=name, passed=bool(passed), detail=detail))

    try:
        patches = [('app/renderer.tsx', 'term.open(mount.current!);',
                    'term.open(mount.current!); (mount.current as any).__t168Terminal = term;')]
        if args.mutant == 'readonly-fits-view':
            patches.append(('app/renderer.tsx', 'if (!writable && ptySize) {', 'if (false && ptySize) {'))
        elif args.mutant == 'readonly-resizes-pty':
            patches.append(('app/renderer.tsx', 'if (writable && dimensions !== next) {', 'if (dimensions !== next) {'))
            patches.append(('app/renderer.tsx', 'if (!writable && ptySize) {', 'if (false && ptySize) {'))
        fixture = Fixture('t168-', lambda _: (_ for _ in ()).throw(AssertionError('禁止模型请求')),
                          revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        signal = fixture.dir / 'live-signal'
        fake = fixture.dir / 'controlled-claude'
        subprocess.run(['cc', str(ROOT / 'workbench/tests/t093_fake_claude.c'), '-o', str(fake)], check=True, capture_output=True)
        (fixture.dir / 'fake-login-peer.py').write_text(PEER.replace("os.environ['T168_LIVE_SIGNAL']", repr(str(signal))), encoding='utf-8')
        fixture.start(str(fake), {'README.md': 'T168 controlled PTY\n', 'check.py': 'raise SystemExit(0)\n'})
        fixture.card('T-review', 'T-review.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-review', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        fixture.wait('候选完成 Stop 交付', lambda: fixture.request('status', fixture.operator, task='demo+T-review')['task']['state'] == 'submitted', 40)
        verified = fixture.request('verify', fixture.terminal, task='T-review')
        assert verified.get('ok'), verified
        reviewer = fixture.wait('门禁启动审查员', lambda: next((a['id'] for a in fixture.request('sidebar_snapshot')['agents']
                               if a['role'] == 'reviewer'), None), 40)

        def raw_output():
            raw = fixture.request('pane_output', launch=reviewer, offset=0, max_bytes=65536)
            return base64.b64decode(raw['data_base64']).decode('utf-8', errors='replace')

        fixture.wait('审查员已输出回放段', lambda: 'REPLAY_WIDE_OK' in raw_output(), 40)
        report['phase'] = 'electron'
        electron = Electron(fixture, fixture.dir.name)
        electron.until('项目出现', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        selector = '[data-agent-launch="' + reviewer + '"]'
        electron.until('审查员侧栏可见', f'!!document.querySelector({json.dumps(selector)})')
        electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
        electron.until('审查员窗格恢复', f'''(()=>{{const p=document.querySelector('.pane[data-launch-id="{reviewer}"]');
            return p&&p.getClientRects().length&&p.querySelector('[data-restoring=false]')&&p.dataset.paneKey}})()''')
        screen_js = f'''(()=>{{const p=document.querySelector('.pane[data-launch-id="{reviewer}"]');
            const t=p.querySelector('.terminal-mount').__t168Terminal, b=t.buffer.active, lines=[];
            for(let i=0;i<b.length;i++)lines.push(b.getLine(i).translateToString(true));
            const box=p.querySelector('.terminal-scroll').getBoundingClientRect(), screen=p.querySelector('.xterm-screen').getBoundingClientRect();
            return {{cols:t.cols, rows:t.rows, lines, input:p.dataset.inputEnabled,
              bottom_visible:screen.bottom<=box.bottom+1&&screen.bottom>box.top, view:[box.width,box.height], screen:[screen.width,screen.height],
              errors:[...p.querySelectorAll('[role=alert]')].map(e=>e.textContent), focused:p.contains(document.activeElement)}}}})()'''

        def judge(tag, screen):
            lines = [line.strip() for line in screen['lines']]
            want = [tag + suffix for suffix in EXPECTED]
            index = [lines.index(item) if item in lines else -1 for item in want]
            consecutive = all(i >= 0 for i in index) and index == list(range(index[0], index[0] + 4))
            leftovers = [line for line in lines if line and set(line) <= {'N', 'W'}]
            return dict(consecutive=consecutive, index=index, leftovers=len(leftovers))

        replay = electron.evaluate(screen_js)
        report['observed']['replay_view'] = dict(cols=replay['cols'], rows=replay['rows'])
        electron.screenshot(args.summary.with_name(args.summary.stem + '-replay.png'))
        signal.write_text('go\n', encoding='utf-8')
        fixture.wait('审查员已输出实时段', lambda: 'LIVE_WIDE_OK' in raw_output(), 20)
        live = electron.until('实时段已显示', screen_js.replace('return {cols', 'if(!lines.some(l=>l.trim()==="LIVE_WIDE_OK"))return null;return {cols'), 20)
        electron.screenshot(args.summary.with_name(args.summary.stem + '-live.png'))
        pane = fixture.request('pane_status', thread=next(a['thread'] for a in fixture.request('sidebar_snapshot')['agents'] if a['id'] == reviewer))
        report['observed']['pane_size'] = pane.get('size')
        report['observed']['live_view'] = dict(cols=live['cols'], rows=live['rows'])
        report['observed']['replay'] = judge('REPLAY', live)
        report['observed']['live'] = judge('LIVE', live)
        report['observed']['screen_tail'] = [line for line in live['lines'] if line.strip()][-14:]
        check('replay_text_not_overlapping', report['observed']['replay']['consecutive'] and not report['observed']['replay']['leftovers'], report['observed']['replay'])
        check('live_text_not_overlapping', report['observed']['live']['consecutive'] and not report['observed']['live']['leftovers'], report['observed']['live'])
        # The newest rows sit at the bottom of the PTY screen; a view that clips them hides the current work.
        check('newest_rows_visible', live['bottom_visible'], dict(view=live['view'], screen=live['screen']))
        check('reviewer_pty_size_unchanged', pane.get('size') == {'cols': 160, 'rows': 45}, pane.get('size'))
        check('reviewer_readonly_no_focus_no_error', live['input'] == 'false' and not live['errors'] and not live['focused'],
              dict(input=live['input'], errors=live['errors'], focused=live['focused']))
        # Red as seen in T-164 N02: the read-only view width differs from the PTY's and redraws land on other lines.
        report['red_reproduced'] = bool(live['cols'] != 160 and not report['observed']['replay']['consecutive'] and
                                        not report['observed']['live']['consecutive'])
        check('zero_model_requests', fixture.api.snapshot()['requests'] == 0, fixture.api.snapshot())
        report['status'] = 'PASS' if all(c['passed'] for c in report['checks']) else 'INCOMPLETE'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        for resource in (electron, fixture):
            if resource:
                try:
                    resource.stop()
                except Exception as error:
                    report.setdefault('cleanup_errors', []).append(str(error))
                    report['status'] = 'INCOMPLETE'
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status=report['status'], red_reproduced=report['red_reproduced'], summary=str(args.summary),
                          error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
