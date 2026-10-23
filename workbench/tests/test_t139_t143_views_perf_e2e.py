"""T-139/T-143：同一真实 Electron、后台与真实 Claude CLI 的联合验证。

失败方式（先列再写；期望来自两张 ticket）：
1. 任务视图混入项目终端或另一任务，agent 视图混入其他会话。
2. 项目只显示普通终端，没有每任务一格的导航。
3. 切换重复创建输入凭据；ended 会话拿到输入权限；布局丢失。
4. 回放偏移倒退、重复或丢失，切换后焦点或输入错路由。
5. 性能测量绕过真实 PTY，或基线与候选的负载、测量命令不同。

只在夹具副本插入 xterm 观察引用（不改变输出或计时路径）。
每次保留夹具和截图；--summary 不覆盖旧证据。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, prompt_text, working_directory, quote


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    parser.add_argument('--revision')
    parser.add_argument('--mutant', choices=['task-includes-project-terminal', 'duplicate-replay'])
    parser.add_argument('--experiment', choices=['screen-reader-off', 'poll-16ms'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，请换新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, checks=[], failures=[], metrics={}, observed={})
    patches = [('app/renderer.tsx', 'term.open(mount.current!);',
                'term.open(mount.current!); (mount.current as any).__testTerminal = term;')]
    if args.experiment == 'screen-reader-off':
        patches.append(('app/renderer.tsx', 'screenReaderMode: true', 'screenReaderMode: false'))
    if args.experiment == 'poll-16ms':
        patches.append(('app/renderer.tsx', 'setTimeout(resolve, 100)', 'setTimeout(resolve, 16)'))
    if args.mutant == 'task-includes-project-terminal':
        anchor = '  return { task: snapshot.task, project: null, saved, panes, ...restoreArrangement(panes, arrangement) };'
        patches.append(('app/main.ts', anchor,
                        "  const shells = await request(options.state, { command: 'pane_layout', project: snapshot.task.project_id });\n"
                        "  for (const shell of shells.panes.filter(p => p.task === null)) panes.push({ key: randomUUID(), launch: shell.launch, project: snapshot.task.project_id, sequence: 0, inputQueue: Promise.resolve(), pendingRelease: null });\n" + anchor))
    if args.mutant == 'duplicate-replay':
        patches.append(('app/renderer.tsx', 'await writeOutput(decoder.decode(bytes, { stream: true }));',
                        'const decoded = decoder.decode(bytes, { stream: true }); await writeOutput(decoded); await writeOutput(decoded);'))

    def plan(body):
        cwd = working_directory(body)
        task = next(t for t in ('T-A', 'T-B') if cwd.endswith('/' + t + '-a1'))
        return task, [('Bash', dict(command='printf "WORKER_READY_' + task + '\\n"', description='fixture ready'))], '等待下一步。'

    fixture = None
    electron = None

    def check(name, condition, detail=None):
        report['checks'].append(dict(name=name, passed=bool(condition), detail=detail))
        if not condition:
            report['failures'].append(name)

    try:
        fixture = Fixture('t139-', plan, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        fixture.start(args.claude, {'README.md': 'demo\n', 'check_A.py': 'raise SystemExit(0)\n', 'check_B.py': 'raise SystemExit(0)\n'})
        workers = {}
        for suffix in ('A', 'B'):
            task = 'T-' + suffix
            fixture.card(task, suffix + '.txt', 'check_' + suffix + '.py')
            result = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
            assert result.get('ok'), result
            workers[task] = result['attempt']['runtime_identity']['launch']
        fixture.wait('两个真实 CLI 都调用模型', lambda: len(fixture.api.snapshot()['results']) >= 2, 120)
        electron = Electron(fixture, 't139-' + fixture.dir.name[5:])
        electron.until('项目', "!!document.querySelector('[data-project-id=\"demo\"]')")

        def click(selector):
            electron.until('可点击 ' + selector, f"(()=>{{const b=document.querySelector({json.dumps(selector)});return b&&!b.disabled}})()", 30)
            electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')

        def ready(launch):
            return electron.until('终端恢复 ' + launch, f"(()=>{{const p=document.querySelector('.pane[data-launch-id=\"{launch}\"]');return p&&p.getClientRects().length&&p.querySelector('[data-restoring=false]')&&p.dataset.paneKey}})()", 60)

        def visible():
            return electron.evaluate("[...document.querySelectorAll('.pane')].filter(p=>p.getClientRects().length).map(p=>p.dataset.launchId)")

        def shot(name):
            path = args.summary.parent / (args.summary.stem + '-' + name + '.png')
            electron.screenshot(path)

        click('[data-project-id="demo"]')
        # Red-state assertion collected before the project assertion, matching the reported defect.
        click('[data-task-option="demo+T-A"]')
        key_a = ready(workers['T-A'])
        check('task_A_only_its_agents', visible() == [workers['T-A']], visible())
        shot('02-task-A')
        click('[data-agent-launch="' + workers['T-A'] + '"]')
        ready(workers['T-A'])
        check('worker_only_itself', visible() == [workers['T-A']], visible())
        shot('03-worker')
        click('[data-agent-launch="' + fixture.terminal_launch + '"]')
        shell_key = ready(fixture.terminal_launch)
        check('controller_only_itself', visible() == [fixture.terminal_launch], visible())
        shot('04-controller')

        # Real shell PTY supplies a stable, numbered, 5000-line backlog for every measurement.
        command = "python3 -c 'for i in range(5000): print(\"BENCH_%05d\" % i)'\r"
        electron.evaluate(f'window.a2a.input({json.dumps(shell_key)}, {json.dumps(command)})')
        mount = f"document.querySelector('.pane[data-launch-id=\"{fixture.terminal_launch}\"] .terminal-mount')"
        buffer = f"(()=>{{const t={mount}?.__testTerminal;return t&&Array.from({{length:t.buffer.active.length}},(_,i)=>t.buffer.active.getLine(i).translateToString(true)).join('\\n')}})()"
        electron.until('真实 PTY 的完整编号输出', f'{buffer}?.includes("BENCH_04999")', 60)
        before = electron.evaluate(buffer)
        # Numbered complete lines, not shell echo of the command.
        expected = [f'BENCH_{i:05d}' for i in range(5000)]
        check('numbered_output_once_before_switch', re.findall(r'^BENCH_\d{5}$', before, re.M) == expected)
        fps = []
        for _ in range(3):
            fps.append(electron.evaluate(f"""new Promise(resolve=>{{const t={mount}.__testTerminal; t.scrollToBottom();
              const frames=[]; let last=performance.now();
              const step=now=>{{frames.push(now-last);last=now;t.scrollLines(frames.length%40<20?-9:9);
                if(frames.length<120)requestAnimationFrame(step);else resolve({{fps:120000/frames.reduce((a,b)=>a+b,0),
                  p95_ms:[...frames].sort((a,b)=>a-b)[113],frames}})}};requestAnimationFrame(step)}})""", timeout=25))
        report['metrics']['scroll'] = fps
        report['metrics']['scroll_fps_median'] = statistics.median(x['fps'] for x in fps)
        report['metrics']['scroll_p95_ms_median'] = statistics.median(x['p95_ms'] for x in fps)
        latencies = []
        # Alternating sidebar clicks include IPC, snapshot, replay and reveal, but exclude CDP process startup.
        for launch in [workers['T-A'], fixture.terminal_launch] * 4:
            latencies.append(electron.evaluate(f"""new Promise((resolve,reject)=>{{const start=performance.now();
              document.querySelector('[data-agent-launch="{launch}"]').click();
              const tick=()=>{{const p=document.querySelector('.pane[data-launch-id="{launch}"]');
                if(p&&p.getClientRects().length&&p.querySelector('[data-restoring=false]')&&p.querySelector('textarea')===document.activeElement)
                  return requestAnimationFrame(()=>resolve(performance.now()-start));
                if(performance.now()-start>12000)return reject(new Error('switch timeout')); requestAnimationFrame(tick)}};tick()}})""", timeout=20))
        report['metrics']['switch_ms'] = latencies
        report['metrics']['switch_ms_median'] = statistics.median(latencies)
        shell_key = ready(fixture.terminal_launch)
        after = electron.evaluate(buffer)
        check('numbered_output_once_after_switch', re.findall(r'^BENCH_\d{5}$', after, re.M) == expected)
        check('controller_focus_after_switch', electron.evaluate(f'{mount}.__testTerminal.textarea===document.activeElement'))
        offset = electron.evaluate(f"Number(document.querySelector('.pane[data-launch-id=\"{fixture.terminal_launch}\"] [data-output-offset]').dataset.outputOffset)")
        raw = fixture.request('pane_output', launch=fixture.terminal_launch, offset=offset)
        check('output_offset_at_live_end', raw['next_offset'] == offset == raw['total_bytes'],
              {k: v for k, v in raw.items() if k != 'data_base64'})
        # Request output while the pane is not selected, then return and verify catch-up exactly once.
        click('[data-agent-launch="' + workers['T-A'] + '"]')
        ready(workers['T-A'])
        terminal_window = fixture.request('window_open', fixture.operator, project='demo', launch=fixture.terminal_launch)
        assert terminal_window['ok'], terminal_window
        marker = fixture.out / 'input-route.txt'
        sent = fixture.request('window_input', terminal_window['identity'], sequence=1, request_id='t139-route',
                               data=f'printf "HIDDEN_OUTPUT_139\\n"; print correct > {quote(str(marker))}\r')
        assert sent['ok'], sent
        fixture.wait('后台终端输入', lambda: marker.exists(), 20)
        fixture.request('window_close', terminal_window['identity'])
        click('[data-agent-launch="' + fixture.terminal_launch + '"]')
        shell_key = ready(fixture.terminal_launch)
        electron.until('隐藏期间输出追平', f'{buffer}.includes("HIDDEN_OUTPUT_139")')
        check('hidden_output_once', electron.evaluate(buffer).splitlines().count('HIDDEN_OUTPUT_139') == 1)
        # Input through the currently focused xterm must reach this shell, not a worker.
        destination = fixture.out / 'focused-input.txt'
        electron.evaluate(f'{mount}.__testTerminal.input({json.dumps("print focused > " + quote(str(destination)) + chr(13))}, true)')
        fixture.wait('焦点输入到主控终端', lambda: destination.exists(), 20)
        check('focused_input_routes_correctly', destination.read_text().strip() == 'focused')

        click('[data-project-id="demo"]')
        tasks = electron.evaluate("[...document.querySelectorAll('[data-task-tile]')].filter(n=>n.getClientRects().length).map(n=>n.dataset.taskTile).sort()")
        check('project_two_task_tiles', tasks == ['demo+T-A', 'demo+T-B'], tasks)
        check('project_does_not_mix_terminals', visible() == [], visible())
        shot('01-project')
        if tasks:
            click('[data-task-tile="demo+T-A"]')
            key = ready(workers['T-A'])
            renamed = electron.evaluate(f'window.a2a.paneAction({json.dumps(key)}, {{type:"rename",name:"任务 A worker"}})')
            assert renamed['names'][key] == '任务 A worker'
            click('[data-project-id="demo"]')
            click('[data-task-tile="demo+T-A"]')
            ready(workers['T-A'])
            current = electron.evaluate('window.a2a.selection()')
            check('layout_name_persisted', list(current['names'].values()) == ['任务 A worker'], current)
            first_key = ready(workers['T-A'])
            first_window = electron.evaluate(f'window.a2a.snapshot({json.dumps(first_key)})')['window_id']
            click('[data-agent-launch="' + workers['T-A'] + '"]')
            second_key = ready(workers['T-A'])
            second_window = electron.evaluate(f'window.a2a.snapshot({json.dumps(second_key)})')['window_id']
            check('same_agent_does_not_reissue_credential', first_key == second_key and first_window == second_window)
        # Reclaim a real, idle, isolated CLI through the gate, then inspect its ended pane.
        click('[data-agent-launch="' + workers['T-B'] + '"]')
        ready(workers['T-B'])
        fixture.wait('B 的真实 CLI 已空闲', lambda: fixture.request('workbench_snapshot', task='demo+T-B',
                     launch=workers['T-B']).get('pane', {}).get('state') == 'idle', 60)
        reclaimed = fixture.request('reclaim', fixture.terminal, task='T-B')
        assert reclaimed.get('ok'), reclaimed
        click('[data-project-id="demo"]')
        click('[data-agent-launch="' + workers['T-B'] + '"]')
        ended_key = ready(workers['T-B'])
        ended = electron.evaluate(f'window.a2a.snapshot({json.dumps(ended_key)})')
        denied = electron.evaluate(f'window.a2a.input({json.dumps(ended_key)}, "must-not-write").then(()=>false,()=>true)')
        check('ended_has_no_input_credential_and_rejects_input', not ended['input_enabled'] and not ended.get('window_id') and denied, ended)
        # An ordinary terminal must remain reachable when leaving its own view.
        ordinary = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
        present = electron.evaluate(f"""new Promise(resolve=>{{const start=performance.now();const tick=()=>{{
          if(document.querySelector('[data-agent-launch="{ordinary}"]'))return resolve(true);
          if(performance.now()-start>7000)return resolve(false);setTimeout(tick,100)}};tick()}})""")
        check('ordinary_terminal_reachable', present)
        if present:
            click('[data-agent-launch="' + ordinary + '"]')
            ready(ordinary)
            check('ordinary_terminal_only_itself', visible() == [ordinary], visible())
            shot('05-ordinary-terminal')
        report['observed']['api'] = fixture.api.snapshot()
        report['status'] = 'PASS' if not report['failures'] else 'NO_GO'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        if electron:
            try:
                electron.screenshot(args.summary.parent / (args.summary.stem + '-failure.png'))
            except Exception as screenshot_error:
                report['screenshot_error'] = str(screenshot_error)
    finally:
        try:
            if electron:
                electron.stop()
            if fixture:
                fixture.stop()
        except Exception as error:
            report['cleanup_error'] = str(error)
            report['status'] = 'INCOMPLETE'
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], summary=str(args.summary), error=report.get('error'), failures=report['failures']), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
