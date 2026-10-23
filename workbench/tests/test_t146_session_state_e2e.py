"""T-146：真实 Electron、后台、门禁与 Claude Code（本地脚本化 Messages 接口）。

失败方式（先列再写；期望来自 T-146 任务卡）：
1. Reflect 将空闲会话的生命周期当作运行状态，与侧栏/流程不同。
2. 关闭经角色申请的主控终端后，Reflect 仍显示运行中。
3. 结束会话在 Reflect 被遗漏/未标结束，或侧栏/流程仍将它显示为运行中。
4. 仍在执行一个真实 Bash 工具的 worker 被错误标成已结束/空闲。
5. 修前版本或恢复 Reflect 旧状态算法的变异没有被拒绝。
6. worker CLI 自然退出但 zsh 终端仍存活时，三处仍显示运行中/空闲。
7. DOM 尚未收到一次轮询后的结果就读取，误将旧侧栏状态当作产品结果。

按主控 #4 暂行规则：Reflect 保留结束会话；侧栏/流程允许不出现或显示 ended。
每阶段先保存页面观察，再断言；缺失项记录 MISSING，不冒充 ended。
--revision 运行指定版本；--mutant reflect-lifecycle 恢复 Reflect 的旧计算。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--revision')
    mode.add_argument('--mutant', choices=['reflect-lifecycle'])
    args = parser.parse_args()
    assert not args.summary.exists(), '必须使用新证据路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  observed={}, checks=[])
    fixture = None
    electron = None
    release = None

    def plan(body):
        text, cwd = prompt_text(body), working_directory(body)
        task = 'T-live' if cwd.endswith('/T-live-a1') else 'T-done'
        if task == 'T-live':
            # Real CLI stays inside a real tool until the test releases it; no fixed sleep race.
            command = ("python3 -c " + quote('import pathlib,time; '
                       f'p=pathlib.Path({str(release)!r}); '
                       'exec("while not p.exists(): time.sleep(0.2)")'))
            return task, [('Bash', dict(command=command, timeout=600000, description='等待测试释放'))], '执行完毕。'
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return task, [('Write', dict(file_path=f'{cwd}/done.txt', content='done\n')),
                      ('Bash', dict(command='git add done.txt', description='stage')),
                      ('Bash', dict(command='git commit -q -m fixture-done', description='commit')),
                      ('Bash', dict(command=submit, description='submit'))], '已交付。'

    def check(name, condition, detail):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def snapshot(label):
        # Refresh through page navigation, then read the DOM of all three views.
        electron.evaluate("document.querySelector('[data-reflect-tab]').click()")
        electron.until('Reflect 数据', "document.querySelectorAll('.reflect-node').length >= 3", 30)
        api_reflect = fixture.request('reflect_tree', project='demo')
        expected = {n['launch']: n['state'] for n in api_reflect['nodes']}
        # Synchronize transport only: API and DOM states are both checked against the independent contract below.
        electron.until('Reflect 轮询已刷新', "JSON.stringify(Object.fromEntries([...document.querySelectorAll('.reflect-node')].map(n=>[n.dataset.reflectLaunch,n.dataset.reflectState])))==="
                       + json.dumps(json.dumps(expected, separators=(',', ':'))), 30)
        reflect = electron.evaluate("[...document.querySelectorAll('.reflect-node')].map(n=>({launch:n.dataset.reflectLaunch,state:n.dataset.reflectState,label:n.querySelector('.record-state').textContent,text:n.innerText}))")
        electron.evaluate("[...document.querySelectorAll('.task-header nav button')].find(b=>b.textContent==='流程').click()")
        electron.until('流程数据', "document.querySelectorAll('[data-flow-agent]').length > 0", 30)
        api_flow = fixture.request('flow_snapshot')
        agents = api_flow['unassigned'] + [a for lane in api_flow['lanes'] for a in lane['agents'] + lane['monitors']]
        expected_flow = {a['id']: a['state'] for a in agents}
        electron.until('流程轮询已刷新', "JSON.stringify(Object.fromEntries([...document.querySelectorAll('[data-flow-agent]')].map(n=>[n.dataset.flowAgent,n.dataset.flowState]).sort()))==="
                       + json.dumps(json.dumps(dict(sorted(expected_flow.items())), separators=(',', ':'))), 30)
        flow = electron.evaluate("[...document.querySelectorAll('[data-flow-agent]')].map(n=>({launch:n.dataset.flowAgent,state:n.dataset.flowState,label:[...n.querySelectorAll('small')].at(-1).textContent.trim(),text:n.innerText}))")
        api_sidebar = fixture.request('sidebar_snapshot')
        expected_sidebar = {a['id']: a['state'] for a in api_sidebar['agents']}
        electron.until('侧栏轮询已刷新', "JSON.stringify(Object.fromEntries([...document.querySelectorAll('[data-agent-launch]')].map(n=>[n.dataset.agentLaunch,n.dataset.agentState]).sort()))==="
                       + json.dumps(json.dumps(dict(sorted(expected_sidebar.items())), separators=(',', ':'))), 30)
        sidebar = electron.evaluate("[...document.querySelectorAll('[data-agent-launch]')].map(n=>({launch:n.dataset.agentLaunch,state:n.dataset.agentState,label:n.querySelector('.agent-state').textContent,text:n.innerText}))")
        value = dict(reflect=reflect, flow=flow, sidebar=sidebar,
                     api_reflect=api_reflect, api_sidebar=api_sidebar, api_flow=api_flow)
        report['observed'][label] = value
        electron.screenshot(fixture.out / f'{label}.png')
        return value

    def state(view, launch):
        return next((row['state'] for row in view if row['launch'] == launch), 'MISSING')

    try:
        patches = []
        if args.mutant:
            patches = [('src/reflect.ts', "row.state === 'ended' ? 'ended' : sessionStates.get(row.launch) ?? 'unknown'",
                        "row.state === 'ended' ? 'ended' : 'running'"),
                       ('src/reflect.ts', "state: sessionStates.get(record.id) ?? 'unknown'",
                        "state: archived.has(record.id) ? 'ended' : 'running'")]
        fixture = Fixture('t146-', plan, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        release = fixture.out / 'release-live'
        (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        fixture.start(args.claude, {'README.md': 'fixture\n',
            'check.py': 'from pathlib import Path\nassert Path("done.txt").is_file()\n'})
        executor = fixture.terminal
        fixture.card('T-done', 'done.txt', 'check.py')
        fixture.card('T-live', 'live.txt', 'check.py')
        launches = {}
        for task in ('T-done', 'T-live'):
            result = fixture.request('dispatch', executor, task=task, runtimeMode='workspace-write')
            assert result.get('ok'), result
            launches[task] = result['attempt']['runtime_identity']['launch']
        report['launches'] = dict(executor=fixture.terminal_launch, **launches)
        fixture.wait('worker 交付', lambda: fixture.request('status', fixture.operator, task='demo+T-done')['task']['state'] == 'submitted', 180)
        fixture.wait('worker 真正空闲', lambda: any(a['id'] == launches['T-done'] and a['state'] == 'idle'
                     for a in fixture.request('sidebar_snapshot')['agents']), 60)
        fixture.wait('另一个 worker 真正在运行', lambda: any(a['id'] == launches['T-live'] and a['state'] == 'running'
                     for a in fixture.request('sidebar_snapshot')['agents']), 60)
        electron = Electron(fixture, fixture.dir.name)
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('Reflect 页签', "!!document.querySelector('[data-reflect-tab]')", 20)
        before = snapshot('01-before-close')
        for view in ('reflect', 'sidebar', 'flow'):
            for name, launch, expected, label in [('idle', launches['T-done'], 'idle', '空闲'),
                                                  ('running', launches['T-live'], 'running', '运行中'),
                                                  ('unknown_controller', fixture.terminal_launch, 'unknown', '未知')]:
                check(f'{view}_{name}', state(before[view], launch) == expected, before[view])
                check(f'{view}_{name}_label', next(row['label'] for row in before[view] if row['launch'] == launch).endswith(label), before[view])
        # /exit is a real CLI command. Keep its zsh alive and independently observe that only zsh remains.
        record = next(a for a in before['api_sidebar']['agents'] if a['id'] == launches['T-done'])
        pane = fixture.request('pane_status', thread=record['thread'])
        window = fixture.request('window_open', fixture.operator, launch=launches['T-done'], task='demo+T-done')
        assert window.get('ok'), window
        sent = fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()), data='/exit\r')
        assert sent.get('ok'), sent

        def shell_without_cli():
            pid = str(pane['shell_pid'])
            shell = subprocess.run(['/bin/ps', '-p', pid, '-o', 'comm='], capture_output=True, text=True, timeout=10)
            children = subprocess.run(['/usr/bin/pgrep', '-P', pid], capture_output=True, text=True, timeout=10)
            assert 'Operation not permitted' not in shell.stderr + children.stderr, 'OS process probe denied by sandbox'
            return (dict(shell_pid=int(pid), shell=shell.stdout.strip(), child_pids=children.stdout.strip())
                    if shell.returncode == 0 and shell.stdout.strip().endswith('zsh') and children.returncode == 1 else None)

        report['native_exit_observation'] = fixture.wait('CLI 已退出且 zsh 仍存活', shell_without_cli, 40)
        native_exit = snapshot('02-after-cli-exit')
        for view in ('reflect', 'sidebar', 'flow'):
            actual = state(native_exit[view], launches['T-done'])
            check(f'{view}_natural_cli_exit', actual == 'ended' if view == 'reflect' else actual in ('ended', 'MISSING'), native_exit[view])
            if actual != 'MISSING':
                check(f'{view}_natural_cli_exit_label', next(row['label'] for row in native_exit[view] if row['launch'] == launches['T-done']).endswith('已结束'), native_exit[view])
            check(f'{view}_other_worker_still_running', state(native_exit[view], launches['T-live']) == 'running', native_exit[view])
        reclaimed = fixture.request('reclaim', executor, task='T-done')
        assert reclaimed.get('ok'), reclaimed
        closed = fixture.request('shell_close', fixture.operator, launch=fixture.terminal_launch)
        assert closed.get('ok'), closed
        # Wait for each page's polling cycle and the ended Reflect node before recording.
        electron.evaluate("document.querySelector('[data-reflect-tab]').click()")
        electron.until('Reflect 收到终端结束', f"[...document.querySelectorAll('.reflect-node')].some(n=>n.dataset.reflectLaunch==={json.dumps(fixture.terminal_launch)}&&n.dataset.reflectState==='ended')", 30)
        after = snapshot('03-after-close')
        for view in ('reflect', 'sidebar', 'flow'):
            check(f'{view}_running', state(after[view], launches['T-live']) == 'running', after[view])
            for name, launch in [('worker_ended', launches['T-done']), ('controller_ended', fixture.terminal_launch)]:
                actual = state(after[view], launch)
                check(f'{view}_{name}', actual == 'ended' if view == 'reflect' else actual in ('ended', 'MISSING'), after[view])
                if actual != 'MISSING':
                    check(f'{view}_{name}_label', next(row['label'] for row in after[view] if row['launch'] == launch).endswith('已结束'), after[view])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        if fixture:
            report['api_snapshot'] = fixture.api.snapshot()
        raise
    finally:
        if release:
            release.touch()
        try:
            if electron:
                electron.stop()
        finally:
            try:
                if fixture:
                    fixture.stop()
            finally:
                args.summary.parent.mkdir(parents=True, exist_ok=True)
                with args.summary.open('x', encoding='utf-8') as output:
                    output.write(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n')


if __name__ == '__main__':
    main()
