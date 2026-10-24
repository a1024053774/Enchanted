"""T-159：真实 Electron、后台、门禁与受控原生 PTY；零模型调用。

失败方式（期望来自 T-159、T-139，而非实现输出）：
1. 任务 worker 的分屏菜单未经说明就创建项目普通终端，原 worker 消失。
2. 仅禁用菜单，直接 IPC 仍能切走任务并创建终端。
3. 普通终端向右/向下分屏丢原窗格、方向不对、目录不继承或混进任务。
4. 切回任务/单 agent 后混入项目终端；拒绝操作修改了保存布局或启动记录。
--revision 跑指定版本；--mutant 恢复修前实现或仅删除入口检查。
--summary 必须是新路径；原始夹具保留，由主控按 T-088 归档。
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from scripted_claude import Electron, Fixture, ROOT, quote


BASELINE = 'c01742804961214ed025b6c9fb9924a1ea49ee2d'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['old-task-split', 'missing-split-guard'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，请使用新路径'
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    report = dict(status='INCOMPLETE', argv=sys.argv, checks=[], observed={}, model_calls=0,
                  code_version=subprocess.check_output(['git', 'rev-parse', args.revision or 'HEAD'], cwd=ROOT, text=True).strip())
    fixture = electron = None

    def check(name, condition, detail=None):
        report['checks'].append(dict(name=name, passed=bool(condition), detail=detail))
        assert condition, name + ': ' + str(detail)

    try:
        patches = []
        if args.mutant == 'old-task-split':
            for name in ('main.ts', 'renderer.tsx'):
                path = 'app/' + name
                patches.append((path, (ROOT / 'workbench' / path).read_text(encoding='utf-8'),
                                subprocess.check_output(['git', 'show', BASELINE + ':workbench/' + path], cwd=ROOT, text=True)))
        elif args.mutant == 'missing-split-guard':
            patches.append(('app/main.ts', "  if (relative && relative.project === undefined) throw new Error('任务视图只展示 Agent 会话。请在普通终端中分屏。');\n", ''))
        fixture = Fixture('t159-', lambda _: (_ for _ in ()).throw(AssertionError('禁止模型请求')), revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        # Reuse the existing compiled PTY driver, with a task-local hook peer.
        # The driver stays the foreground process; no vendor CLI or model runs.
        fake = fixture.dir / 'controlled-claude'
        built = subprocess.run(['cc', str(ROOT / 'workbench/tests/t093_fake_claude.c'), '-o', str(fake)], capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        (fixture.dir / 'fake-login-peer.py').write_text('''import json, os, subprocess, sys
if sys.argv[2] == '0':
    settings = json.loads(os.environ['T093_FIXTURE_SETTINGS'])
    command = settings['hooks']['SessionStart'][0]['hooks'][0]['command']
    payload = dict(hook_event_name='SessionStart', session_id=os.environ['A2A_NATIVE_SESSION'], cwd=os.getcwd(), source='startup')
    result = subprocess.run(command, shell=True, input=json.dumps(payload), text=True, capture_output=True)
    print(result.stdout, result.stderr, flush=True)
    raise SystemExit(result.returncode)
''', encoding='utf-8')
        fixture.start(str(fake), {'README.md': 'T-159 controlled PTY\n', 'check.py': 'raise SystemExit(0)\n'})
        fixture.card('T-1', 'a.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        worker = dispatched['attempt']['runtime_identity']['launch']
        fixture.wait('受控 worker 已启动', lambda: fixture.request('workbench_snapshot', task='demo+T-1', launch=worker).get('pane', {}).get('active'), 30)
        report['observed']['worker'] = worker
        electron = Electron(fixture, fixture.dir.name)
        electron.until('项目出现', '!!document.querySelector(\'[data-project-id="demo"]\')')

        def click(selector):
            electron.until('可点击 ' + selector, f'!!document.querySelector({json.dumps(selector)})')
            electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')

        def ready(launch):
            return electron.until('窗格恢复', f'''(()=>{{const p=document.querySelector('.pane[data-launch-id="{launch}"]');
                return p&&p.getClientRects().length&&p.querySelector('[data-restoring=false]')&&p.dataset.paneKey}})()''')

        def visible():
            return electron.evaluate('''[...document.querySelectorAll('.pane')].filter(p=>p.getClientRects().length).map(p=>{
                const r=p.getBoundingClientRect();return {launch:p.dataset.launchId,key:p.dataset.paneKey,role:p.dataset.role,
                x:r.x,y:r.y,w:r.width,h:r.height,title:p.querySelector('.pane-header').textContent}})''')

        def shot(name):
            path = args.summary.parent / (args.summary.stem + '-' + name + '.png')
            electron.screenshot(path)
            report.setdefault('screenshots', []).append(str(path))

        def catalog():
            value = fixture.request('sidebar_snapshot')
            assert value.get('ok'), value
            return sorted(row['id'] for row in value['terminals'])

        click('[data-project-id="demo"]')
        click('[data-task-option="demo+T-1"]')
        key = ready(worker)
        before_layout = fixture.request('pane_layout', task='demo+T-1')
        before_terminals = catalog()
        shot('01-before')
        for direction, text in [('right', '向右分屏'), ('down', '向下分屏')]:
            click(f'.pane[data-launch-id="{worker}"] [aria-label="窗格菜单"]')
            menu = electron.evaluate('''[...document.querySelectorAll('.pane-menu button')].map(b=>({text:b.textContent,disabled:b.disabled}))''')
            explanation = electron.evaluate('document.querySelector(".pane-menu").textContent')
            shot('02-menu-' + direction)
            electron.evaluate(f'[...document.querySelectorAll(".pane-menu button")].find(b=>b.textContent==={json.dumps(text)}).click()')
            # An enabled faulty action must finish before capturing the red state.
            if any(b['text'] == text and not b['disabled'] for b in menu):
                electron.until('操作结束', f'''(async()=>{{const s=await window.a2a.selection();
                    return !s.paneKeys.includes({json.dumps(key)})}})()''')
            electron.until('窗格快照', '(()=>{const p=[...document.querySelectorAll(".pane")].filter(p=>p.getClientRects().length);return p.length&&p.every(p=>p.dataset.launchId)})()')
            after = visible()
            report['observed'][direction] = dict(menu=menu, explanation=explanation, panes=after,
                                               terminals=catalog(), selection=electron.evaluate('window.a2a.selection()'))
            shot('03-after-' + direction)
            check('task_' + direction + '_explains_before_action', any(b['text'] == text and b['disabled'] for b in menu) and
                  '任务' in explanation and '普通终端' in explanation, report['observed'][direction])
            keyboard = electron.evaluate('''(()=>{const menu=document.querySelector('.pane-menu');menu.querySelector('button').focus();
                menu.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true}));
                const rect=menu.getBoundingClientRect();return {focused:document.activeElement.textContent,
                fits:rect.top>=0&&rect.left>=0&&rect.bottom<=innerHeight&&rect.right<=innerWidth}})()''')
            check('task_' + direction + '_keyboard_skips_disabled_and_help_fits', keyboard['focused'] == '放大' and keyboard['fits'], keyboard)
            check('task_' + direction + '_preserves_worker_and_terminals', [p['launch'] for p in after] == [worker] and catalog() == before_terminals, after)
            refused = electron.evaluate(f'window.a2a.paneAction({json.dumps(key)},{{type:"split",direction:{json.dumps(direction)}}}).then(()=>({{refused:false}}),e=>({{refused:true,message:String(e)}}))')
            check('task_' + direction + '_ipc_refused_with_explanation', refused['refused'] and '任务' in refused.get('message', '') and '普通终端' in refused.get('message', ''), refused)
            check('task_' + direction + '_layout_unchanged', fixture.request('pane_layout', task='demo+T-1') == before_layout and catalog() == before_terminals)
            electron.evaluate('document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}))')
            # Close the menu through its own keyboard handler.
            electron.evaluate('document.querySelector(".pane-menu")?.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}))')

        # Both supported split directions run on a real shell in a nested directory.
        child = fixture.repo / 'child'
        child.mkdir()
        shell = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(child))['launch']['id']
        click('[data-agent-launch="' + shell + '"]')
        ready(shell)
        expected = {shell}
        for direction, text in [('right', '向右分屏'), ('down', '向下分屏')]:
            click(f'.pane[data-launch-id="{shell}"] [aria-label="窗格菜单"]')
            electron.evaluate(f'[...document.querySelectorAll(".pane-menu button")].find(b=>b.textContent==={json.dumps(text)}).click()')
            electron.until('新窗格', f'(async()=>Object.keys((await window.a2a.selection()).launches).length==={len(expected)+1})()')
            selected = electron.evaluate('window.a2a.selection()')
            launches = set(selected['launches'].values())
            new = (launches - expected).pop()
            ready(new)
            panes = visible()
            check('shell_' + direction + '_keeps_original', launches == expected | {new} and all(p['role'] == 'shell' for p in panes), panes)
            original, added = [next(p for p in panes if p['launch'] == launch) for launch in (shell, new)]
            check('shell_' + direction + '_geometry', (added['x'] > original['x'] and abs(added['y']-original['y']) < 2) if direction == 'right'
                  else (added['y'] > original['y'] and abs(added['x']-original['x']) < 2), panes)
            for launch in (shell, new):
                snapshot = fixture.request('workbench_snapshot', project='demo', launch=launch)
                check(direction + '_' + launch + '_type_directory', snapshot['launch']['role'] == 'shell' and snapshot['launch']['task'] is None and snapshot['launch']['worktree'] == str(child), snapshot['launch']['worktree'])
                destination = fixture.out / (direction + '-' + launch + '-pwd.txt')
                pane_key = next(k for k, v in selected['launches'].items() if v == launch)
                electron.until('输入可用', f'document.querySelector(\'.pane[data-launch-id="{launch}"]\')?.dataset.inputEnabled==="true"')
                electron.evaluate(f'window.a2a.input({json.dumps(pane_key)},{json.dumps("pwd > " + quote(str(destination)) + chr(13))})')
                fixture.wait('实际 pwd', lambda: destination.exists() and destination.stat().st_size, 20)
                check(direction + '_' + launch + '_actual_pwd', destination.read_text(encoding='utf-8').strip() == str(child))
            expected.add(new)
            shot('04-shell-' + direction)
        click('[data-task-option="demo+T-1"]')
        ready(worker)
        check('task_return_excludes_project_terminals', [p['launch'] for p in visible()] == [worker], visible())
        click('[data-agent-launch="' + shell + '"]')
        ready(shell)
        check('single_agent_only_itself', [p['launch'] for p in visible()] == [shell], visible())
        check('zero_model_requests', fixture.api.snapshot()['requests'] == 0, fixture.api.snapshot())
        report['status'] = 'PASS'
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
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
