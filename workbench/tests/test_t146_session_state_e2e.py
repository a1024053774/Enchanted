"""T-146：真实 Electron、后台、门禁与 Claude Code（本地脚本化 Messages 接口）。

失败方式（先列再写；期望来自 T-146 任务卡）：
1. Reflect 将空闲会话的生命周期当作运行状态，与侧栏/流程不同。
2. 关闭经角色申请的主控终端后，Reflect 仍显示运行中。
3. worker 经门禁回收后仍显示运行中，或结束会话被页面遗漏。
4. 仍在执行一个真实 Bash 工具的 worker 被错误标成已结束/空闲。
5. 修前版本或恢复 Reflect 旧状态算法的变异没有被拒绝。

测试先保存所有页面观察，再断言；缺失项与状态不同分别保留，不能把隐藏解释为 ended。
--revision 运行指定版本；--mutant reflect-lifecycle 恢复 Reflect 的旧计算。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import ROOT, Electron, Fixture, prompt_text, quote, working_directory


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
        reflect = electron.evaluate("[...document.querySelectorAll('.reflect-node')].map(n=>({launch:n.dataset.reflectLaunch,state:n.dataset.reflectState,text:n.innerText}))")
        electron.evaluate("[...document.querySelectorAll('.task-header nav button')].find(b=>b.textContent==='流程').click()")
        electron.until('流程数据', "document.querySelectorAll('[data-flow-agent]').length > 0", 30)
        flow = electron.evaluate("[...document.querySelectorAll('[data-flow-agent]')].map(n=>({launch:n.dataset.flowAgent,state:n.dataset.flowState,text:n.innerText}))")
        sidebar = electron.evaluate("[...document.querySelectorAll('[data-agent-launch]')].map(n=>({launch:n.dataset.agentLaunch,state:n.dataset.agentState,text:n.innerText}))")
        value = dict(reflect=reflect, flow=flow, sidebar=sidebar,
                     api_reflect=fixture.request('reflect_tree', project='demo'),
                     api_sidebar=fixture.request('sidebar_snapshot'), api_flow=fixture.request('flow_snapshot'))
        report['observed'][label] = value
        electron.screenshot(fixture.out / f'{label}.png')
        return value

    def state(view, launch):
        return next((row['state'] for row in view if row['launch'] == launch), 'MISSING')

    try:
        patches = []
        if args.mutant:
            current = (ROOT / 'workbench/src/reflect.ts').read_text(encoding='utf-8')
            original = subprocess.check_output(['git', 'show', 'ebbae7bd0:workbench/src/reflect.ts'], cwd=ROOT, text=True)
            assert current != original, '当前仍是修前实现；先运行 --revision，修复后才能验证回退变异'
            patches = [('src/reflect.ts', current, original)]
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
        reclaimed = fixture.request('reclaim', executor, task='T-done')
        assert reclaimed.get('ok'), reclaimed
        closed = fixture.request('shell_close', fixture.operator, launch=fixture.terminal_launch)
        assert closed.get('ok'), closed
        # Wait for each page's polling cycle and the ended Reflect node before recording.
        electron.evaluate("document.querySelector('[data-reflect-tab]').click()")
        electron.until('Reflect 收到终端结束', f"[...document.querySelectorAll('.reflect-node')].some(n=>n.dataset.reflectLaunch==={json.dumps(fixture.terminal_launch)}&&n.dataset.reflectState==='ended')", 30)
        after = snapshot('02-after-close')
        for view in ('sidebar', 'reflect', 'flow'):
            check(f'{view}_idle', state(before[view], launches['T-done']) == 'idle', before[view])
            check(f'{view}_running', state(after[view], launches['T-live']) == 'running', after[view])
            check(f'{view}_worker_ended', state(after[view], launches['T-done']) == 'ended', after[view])
            check(f'{view}_controller_ended', state(after[view], fixture.terminal_launch) == 'ended', after[view])
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
