"""T-204：关闭一个有待批角色申请的普通终端，界面不得把关闭过程中的 resize 当成“输入尚未确认”报错。
真实后台、socket、Electron 窗口（CDP 驱动），终端是真实 zsh，零模型调用。

预期来自需求（T-204 与第 2 轮试用的现象）：用户点“关闭窗格”后窗格消失，申请随终端关闭而结束；整个过程中界面任何
role=alert 里都不出现内部错误（`Error invoking remote method …`，如 `a2a:resize` 的 `Window is not available for input`、
`a2a:snapshot` 的 `Task view changed`） / “输入尚未确认”，也不出现“关闭窗格未确认”。

失败方式（先列再写）：
1. 关闭过程中申请横幅消失、窗格变高，正在关闭的窗格照常发 resize，主进程以“窗格正在关闭”拒绝，界面当输入错误显示（试用原样）；
   正在关闭的窗格继续轮询快照，窗格被移走后报 Task view changed。前台程序收到挂断后要过一会儿才退出（试用里是 Claude Code），
   后台在等它退出的这几秒里申请已结束、横幅已消失，这是复现的条件（空闲 zsh 立即退出，复现不出来）。
2. 修法把关闭之外的 resize 也停了：剩下的终端变大后 PTY 不跟着变（另一个终端在关闭后必须收到新的尺寸）。
3. 关闭后再批准这份申请必须仍被拒绝（不变）。
4. 修法吞掉错误让关闭本身失败或卡住：窗格没有消失、或显示“关闭窗格未确认”。
5. 报错一闪而过、窗格随即卸载，事后读 DOM 看不到：用 MutationObserver 记下关闭过程中出现过的所有 alert。
--revision 在该版本的源码上跑同一场景（修前应在第 1 条失败）；--mutant 去掉修复的守护。
"""
import argparse
import json
from pathlib import Path
import socket
import sys
import time
import traceback
import uuid

from scripted_claude import Electron, Fixture

MUTANTS = {
    # The closing pane keeps sending resize.
    'resize-while-closing': [('app/renderer.tsx', 'if (writable && !closingRef.current && dimensions !== next) {', 'if (writable && dimensions !== next) {')],
    # The closing pane keeps polling its snapshot.
    'poll-while-closing': [('app/renderer.tsx', 'if (!visibility.current.active || closingRef.current) { await delay(); continue; }',
                            'if (!visibility.current.active) { await delay(); continue; }')],
    # Failure mode 2: the fix stops every resize, so the remaining terminal keeps its old size.
    'no-resize': [('app/renderer.tsx', 'if (writable && !closingRef.current && dimensions !== next) {', 'if (false && dimensions !== next) {')],
}
BAD = ('Error invoking remote method', 'Window is not available for input', '输入尚未确认', '关闭窗格未确认')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  runtime='real Electron/daemon/zsh; zero model calls', checks=[])
    fixture = electron = asker = None

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    try:
        def no_model(body):
            raise AssertionError('T-204 不调用模型')
        fixture = Fixture('t204-', no_model, revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
        report['fixture'] = str(fixture.dir)
        fixture.start('/usr/bin/false', {'README.md': 't204\n'})
        project = fixture.project
        # A second ordinary terminal asks for the executor role; the request stays pending.
        launch = fixture.run_cli('shell_start', '--project', project, '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project=project)
        assert window['ok'], window
        token_file = fixture.out / 'token2.txt'
        assert fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()),
                               data=f'print -r -- $A2A_TERMINAL_TOKEN > {token_file}\r')['ok']
        fixture.wait('第二个终端写出令牌', lambda: token_file.exists() and token_file.read_text().strip(), 30)
        # Like the Claude Code of the trial, the foreground program takes a while to exit after the hangup, so the
        # daemon is still confirming the exit while the request ends and its banner goes away.
        slow = fixture.out / 'slow-started'
        assert fixture.request('window_input', window['identity'], sequence=2, request_id=str(uuid.uuid4()),
                               data="python3 -c 'import signal,time,pathlib\nsignal.signal(signal.SIGHUP,lambda *a:(time.sleep(3),exit()))\n"
                                    f"pathlib.Path(\"{slow}\").touch()\ntime.sleep(600)'\r")['ok']
        fixture.wait('前台程序已启动', slow.exists, 20)
        assert fixture.request('window_close', window['identity'])['ok']
        identity = dict(kind='terminal', launch=launch, token=token_file.read_text().strip())
        asker = socket.socket(socket.AF_UNIX)
        asker.connect(str(fixture.state / 'control.sock'))
        asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role='ideation', wait_seconds=120),
                                       identity=identity)) + '\n').encode())
        pending = fixture.wait('申请待批', lambda: [r for r in fixture.request('sidebar_snapshot').get('role_requests', []) if r['launch'] == launch], 20)
        report['pending_request'] = pending[0]['id']

        electron = Electron(fixture, 't204-' + uuid.uuid4().hex[:10])
        electron.until('项目', f'!!document.querySelector(\'[data-project-id="{project}"]\')')
        electron.evaluate(f'document.querySelector(\'[data-project-id="{project}"]\').click()')
        electron.until('终端行', f'!!document.querySelector(\'[data-agent-launch="{launch}"]\')')
        electron.evaluate(f'document.querySelector(\'[data-agent-launch="{launch}"]\').click()')
        pending_pane = f'section.pane[data-launch-id="{launch}"]'
        electron.until('终端可输入', f'!!document.querySelector(\'{pending_pane}[data-input-enabled="true"]\')?.getClientRects().length')
        check('pending_banner_shown', electron.until('申请横幅', '!!document.querySelector(".role-requests")'))
        # Split right from that pane, as a user does: the new terminal on the right takes the space freed by the close.
        electron.evaluate(f'document.querySelector(\'{pending_pane} button.pane-menu-trigger\').click()')
        electron.until('窗格菜单', f'!![...document.querySelectorAll(\'{pending_pane} [role="menuitem"]\')].find(n=>n.textContent==="向右分屏")')
        electron.evaluate(f'[...document.querySelectorAll(\'{pending_pane} [role="menuitem"]\')].find(n=>n.textContent==="向右分屏").click()')
        other = electron.until('分屏终端可输入', f'''(()=>{{const p=[...document.querySelectorAll('section.pane[data-input-enabled="true"]')]
          .find(n=>n.dataset.launchId&&n.dataset.launchId!=="{launch}"&&n.getClientRects().length);return p?p.dataset.launchId:null}})()''', 30)
        report['other_launch'] = other
        electron.screenshot(fixture.out / 'before-close.png')
        electron.evaluate('''(()=>{window.__t204=[];const seen=n=>{for(const a of n.querySelectorAll?.('[role="alert"]')??[])window.__t204.push(a.textContent);
          if(n.matches?.('[role="alert"]'))window.__t204.push(n.textContent);};
          new MutationObserver(list=>{for(const m of list){if(m.type==='characterData'){const a=m.target.parentElement?.closest('[role="alert"]');if(a)window.__t204.push(a.textContent);}
            for(const n of m.addedNodes)seen(n.nodeType===1?n:n.parentElement??document.createElement('i'));
            if(m.type==='childList'){const a=m.target.closest?.('[role="alert"]');if(a)window.__t204.push(a.textContent);}}})
          .observe(document.body,{subtree:true,childList:true,characterData:true});return true;})()''')
        time.sleep(1)
        size_before = electron.until('分屏终端尺寸', f'''(async()=>{{const p=document.querySelector('section.pane[data-launch-id="{other}"]');
          return (await window.a2a.snapshot(p.dataset.paneKey)).pane?.size??null}})()''')
        report['remaining_size_before'] = size_before
        electron.evaluate(f'document.querySelector(\'section.pane[data-launch-id="{launch}"] button.pane-close\').click()')
        electron.until('窗格消失', f'!document.querySelector(\'section.pane[data-launch-id="{launch}"]\')', 30)
        electron.until('横幅消失', '!document.querySelector(".role-requests")', 30)
        time.sleep(3)
        electron.screenshot(fixture.out / 'after-close.png')
        alerts = electron.evaluate('[...new Set([...window.__t204, ...[...document.querySelectorAll(\'[role="alert"]\')].map(n=>n.textContent)])]')
        report['alerts_seen'] = alerts
        check('no_internal_error_on_close', not [a for a in alerts if any(word in a for word in BAD)], alerts)
        check('request_ended_with_terminal', not [r for r in fixture.request('sidebar_snapshot').get('role_requests', []) if r['launch'] == launch])
        late = fixture.request('role_request_decide', fixture.operator, role_request=report['pending_request'], approved=True)
        check('approve_after_close_refused', not late.get('ok'), late)
        check('remaining_terminal_still_writable', electron.evaluate(
            f'!!document.querySelector(\'section.pane[data-launch-id="{other}"][data-input-enabled="true"]\')'))
        # The remaining terminal took the freed space; its PTY follows the new width (failure mode 2).
        size_after = electron.until('剩下的终端变宽', f'''(async()=>{{const p=document.querySelector('section.pane[data-launch-id="{other}"]');
          const s=(await window.a2a.snapshot(p.dataset.paneKey)).pane?.size;return s&&s.cols>{size_before['cols']}?s:null}})()''', 15)
        report['remaining_size_after'] = size_after
        check('remaining_terminal_pty_follows_view', size_after['cols'] > size_before['cols'], (size_before, size_after))
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
        if asker:
            asker.close()
        for stop in (electron, fixture):
            if stop:
                try:
                    stop.stop()
                except Exception as error:
                    report.setdefault('cleanup_errors', []).append(str(error))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(report['status'], report.get('error', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
