"""T-159：真实 Electron、后台、门禁与受控原生 PTY；零模型调用。

失败方式（期望来自 T-159、T-139，而非实现输出）：
1. 任务分屏禁用或新终端替换原 worker，数量、方向、类型或目录不符。
2. 讨论终端被当成 worker，或其输入被记到 worker 的人工介入记录。
3. 普通终端向右/向下分屏丢原窗格、方向不对或目录不继承。
4. 布局恢复丢失明确加入的终端，或混入未选择的项目终端；关闭终端改变 worker。
5. 已批准项目主控的终端不能向右分屏，或分屏丢失原窗格、批准身份或项目目录。
--revision 跑指定版本；--mutant 恢复修前实现或仅删除入口检查。
--summary 必须是新路径；原始夹具保留，由主控按 T-088 归档。
"""
import argparse
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from scripted_claude import Electron, Fixture, ROOT, quote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['replace-worker', 'shell-input-to-worker'])
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
        if args.mutant == 'replace-worker':
            anchor = '    // The shell stays a project terminal; only its layout placement belongs to this task view.'
            patches.append(('app/main.ts', anchor,
                            "    if (context.task) { await changeView(context, project === null ? {} : { project }); relative = undefined; }"))
        elif args.mutant == 'shell-input-to-worker':
            anchor = "    return sendWindowCommand(context, pane, { command: 'window_input', data, encoding });"
            patches.append(('app/main.ts', anchor,
                            "    const recipient = context.task && pane.project !== undefined ? [...context.panes.values()].find(p => p.task === context.options.task)! : pane;\n"
                            "    return sendWindowCommand(context, recipient, { command: 'window_input', data, encoding });"))
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

        click('[data-project-id="demo"]')
        click('[data-task-option="demo+T-1"]')
        key = ready(worker)
        click('[data-agent-launch="' + worker + '"]')
        key = ready(worker)

        def task_facts():
            task = fixture.request('status', fixture.operator, task='demo+T-1')['task']
            pane = fixture.request('workbench_snapshot', task='demo+T-1', launch=worker)['pane']
            with sqlite3.connect((fixture.state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
                inputs = db.execute('SELECT id FROM user_inputs WHERE task=? ORDER BY rowid', ('demo+T-1',)).fetchall()
            events = fixture.request('events', fixture.operator, task='demo+T-1')['events']
            return dict(task={**{k: task.get(k) for k in ('state', 'current_attempt', 'fence', 'spec_rev', 'candidate_commit')}, 'paths': task['card']['paths']},
                        worker={k: pane.get(k) for k in ('state', 'lifecycle', 'failed', 'active', 'interrupted', 'input_generation')},
                        inputs=inputs, interventions=[e for e in events if e['type'] == 'human_intervention'])

        before = task_facts()
        selected_shells = set()
        shot('01-before')
        for direction, text in [('right', '向右分屏'), ('down', '向下分屏')]:
            click(f'.pane[data-launch-id="{worker}"] [aria-label="窗格菜单"]')
            menu = electron.evaluate('''[...document.querySelectorAll('.pane-menu button')].map(b=>({text:b.textContent,disabled:b.disabled}))''')
            shot('02-menu-' + direction)
            check('task_' + direction + '_split_enabled', any(b['text'] == text and not b['disabled'] for b in menu), menu)
            electron.evaluate(f'[...document.querySelectorAll(".pane-menu button")].find(b=>b.textContent==={json.dumps(text)}).click()')
            # Wait for either the correct split or the reported replacement defect, not a setup timeout.
            electron.until('任务分屏结果', f'''(async()=>{{const s=await window.a2a.selection();
                return s.paneKeys.length==={len(selected_shells)+2}||!s.paneKeys.includes({json.dumps(key)})}})()''')
            selected = electron.evaluate('window.a2a.selection()')
            for launch in selected['launches'].values():
                ready(launch)
            panes = visible()
            report['observed'][direction] = dict(menu=menu, panes=panes, selection=selected)
            shot('03-after-' + direction)
            check('task_' + direction + '_keeps_worker', selected['task'] is not None and selected['task']['task_id'] == 'demo+T-1' and
                  selected['launches'].get(key) == worker and len(panes) == len(selected_shells)+2 and
                  any(p['launch'] == worker and p['role'] == 'worker' for p in panes), panes)
            added = set(selected['launches'].values()) - selected_shells - {worker}
            check('task_' + direction + '_one_new_terminal', len(added) == 1, list(added))
            launch = added.pop()
            selected_shells.add(launch)
            original, terminal = [next(p for p in panes if p['launch'] == item) for item in (worker, launch)]
            check('task_' + direction + '_geometry', terminal['x'] > original['x'] and abs(terminal['y']-original['y']) < 2 if direction == 'right'
                  else terminal['y'] > original['y'] and abs(terminal['x']-original['x']) < 2, panes)
            record = fixture.request('workbench_snapshot', project='demo', launch=launch)['launch']
            check('task_' + direction + '_ordinary_root_terminal', terminal['role'] == 'shell' and '普通终端' in terminal['title'] and
                  record['role'] == 'shell' and all(record[k] is None for k in ('task', 'attempt', 'session', 'fence')) and
                  record['worktree'] == str(fixture.repo) and record['worktree'] != dispatched['attempt']['workspace'], record)
            sidebar = fixture.request('sidebar_snapshot')
            check('task_' + direction + '_catalog_not_worker', any(t['id'] == launch and t['role'] == 'shell' for t in sidebar['terminals']) and
                  not any(a['id'] == launch for a in sidebar['agents']) and
                  [a['id'] for a in sidebar['agents'] if a['task'] == 'demo+T-1'] == [worker])
            pane_key = next(k for k, v in selected['launches'].items() if v == launch)
            electron.until('讨论终端可输入', f'document.querySelector(\'.pane[data-launch-id="{launch}"]\')?.dataset.inputEnabled==="true"')
            destination = fixture.out / ('task-' + direction + '-pwd.txt')
            electron.evaluate(f'window.a2a.input({json.dumps(pane_key)},{json.dumps("pwd > " + quote(str(destination)) + chr(13))})')
            after = task_facts()
            check('task_' + direction + '_no_intervention', after['inputs'] == before['inputs'] and after['interventions'] == before['interventions'], after)
            check('task_' + direction + '_worker_unchanged', after['task'] == before['task'] and after['worker'] == before['worker'], after)
            fixture.wait('讨论终端实际 pwd', lambda: destination.exists() and destination.stat().st_size, 20)
            check('task_' + direction + '_actual_pwd', destination.read_text(encoding='utf-8').strip() == str(fixture.repo))
        click('[data-project-id="demo"]')
        click('[data-task-option="demo+T-1"]')
        for launch in {worker} | selected_shells:
            ready(launch)
        restored = visible()
        check('task_explicit_terminals_restored', {p['launch'] for p in restored} == {worker} | selected_shells, restored)
        # Persist the nested right/down arrangement, rather than appending every restored shell on the right.
        worker_rect = next(p for p in restored if p['launch'] == worker)
        check('task_restores_down_geometry', any(p['launch'] in selected_shells and p['y'] > worker_rect['y'] and abs(p['x']-worker_rect['x']) < 2 for p in restored), restored)
        shot('03-task-restored')
        closing = sorted(selected_shells)[0]
        click(f'.pane[data-launch-id="{closing}"] [aria-label="关闭普通终端"]')
        electron.until('讨论终端已关闭', f'(async()=>!Object.values((await window.a2a.selection()).launches).includes({json.dumps(closing)}))()')
        selected_shells.remove(closing)
        closed = fixture.request('workbench_snapshot', project='demo', launch=closing)
        check('close_discussion_preserves_worker', closed['pane']['lifecycle'] == 'ended' and task_facts() == before)

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
        for launch in selected_shells:
            ready(launch)
        check('task_return_only_explicit_terminals', {p['launch'] for p in visible()} == {worker} | selected_shells, visible())
        click('[data-agent-launch="' + shell + '"]')
        ready(shell)
        check('single_agent_only_itself', [p['launch'] for p in visible()] == [shell], visible())

        # Fixture.start requests, approves and confirms this real project terminal's role.
        # Keep the actual snapshot (role shell); do not substitute the sidebar's controller projection.
        controller = fixture.terminal_launch
        who = fixture.request('terminal_whoami', fixture.terminal)
        entry = next(a for a in fixture.request('sidebar_snapshot')['agents'] if a['id'] == controller)
        check('project_controller_approved', who.get('ok') and who.get('role') == 'executor' and
              who.get('terminal') == controller and entry['role'] == 'controller' and entry.get('terminal') is True)
        click('[data-agent-launch="' + controller + '"]')
        controller_key = ready(controller)
        before = electron.evaluate('window.a2a.selection()')
        check('project_controller_view_is_project_scoped', before['task'] is None and
              before['project']['project_id'] == 'demo' and list(before['launches'].values()) == [controller], before)
        click(f'.pane[data-launch-id="{controller}"] [aria-label="窗格菜单"]')
        menu = electron.evaluate('''(()=>{const m=document.querySelector('.pane-menu');
            const b=[...m.querySelectorAll('button')].find(b=>b.textContent==='向右分屏');
            return {enabled:!!b&&!b.disabled,explanation:m.textContent}})()''')
        report['observed']['project_controller_menu'] = menu
        shot('05-controller-menu')
        check('project_controller_right_split_enabled', menu['enabled'] and '任务视图只展示' not in menu['explanation'], menu)
        electron.evaluate('[...document.querySelectorAll(".pane-menu button")].find(b=>b.textContent==="向右分屏").click()')
        electron.until('主控终端右侧新窗格', '(async()=>Object.keys((await window.a2a.selection()).launches).length===2)()')
        selected = electron.evaluate('window.a2a.selection()')
        launches = set(selected['launches'].values())
        added_launch = (launches - {controller}).pop()
        ready(added_launch)
        panes = visible()
        report['observed']['project_controller_split'] = dict(launch=controller, panes=panes)
        check('project_controller_right_keeps_original', launches == {controller, added_launch} and
              len(panes) == 2 and {p['launch'] for p in panes} == launches and
              selected['launches'].get(controller_key) == controller and
              selected['task'] is None and selected['project']['project_id'] == 'demo', panes)
        original, added = [next(p for p in panes if p['launch'] == launch) for launch in (controller, added_launch)]
        check('project_controller_right_geometry', added['x'] > original['x'] and abs(added['y']-original['y']) < 2, panes)
        for launch in (controller, added_launch):
            record = fixture.request('workbench_snapshot', project='demo', launch=launch)['launch']
            check('project_controller_' + launch + '_directory', record['task'] is None and
                  record['project'] == 'demo' and record['worktree'] == str(fixture.repo), record['worktree'])
        who_after = fixture.request('terminal_whoami', fixture.terminal)
        check('project_controller_role_preserved', who_after.get('role') == 'executor' and
              who_after.get('terminal') == controller)
        shot('06-controller-right-split')
        # Positive control: the same observer must detect actual input to the worker.
        click('[data-agent-launch="' + worker + '"]')
        worker_key = ready(worker)
        check('single_worker_excludes_discussion_terminals', [p['launch'] for p in visible()] == [worker], visible())
        electron.evaluate(f'window.a2a.input({json.dumps(worker_key)},{json.dumps("T159_OBSERVER_CONTROL" + chr(13))})')
        controlled = task_facts()
        check('intervention_observer_positive_control', len(controlled['inputs']) == len(before['inputs'])+1 and
              len(controlled['interventions']) == len(before['interventions'])+1, controlled)
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
