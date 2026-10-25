"""T-178（L05）：流程页在项目视图下显示别的项目的任务、标题重复为“T-1 · T-1”。
真实后台、门禁、两个项目各有经角色申请批准的终端主控，真实 Electron 窗口经 DevTools 协议操作；不派 worker，不调用模型。
期望值来自 T-178 ticket：项目视图下的流程页置顶是本项目任务（其他项目明确分组折叠）；任务标题不重复显示。

场景：项目 a2a 有 T-138（没写标题），项目 demo 有 T-1（没写标题）和 T-2（标题“导出 CSV”）。按任务号排序 a2a+T-138 在最前，
正是 L05 的现场。

失败方式（先列再写）：
1. 在 demo 下打开流程页，置顶展开的是 a2a 的 T-138（L05 原样），或 demo 的任务被挤到后面。
2. 别的项目的任务被直接删掉看不到：应在一个折叠的“其他项目的任务 N 张”里，展开可见。
3. 标题没写时显示“T-1 · T-1”；写了标题的被吞掉（应显示“T-2 · 导出 CSV”）。
4. 换到 a2a 项目后仍显示 demo 的任务在前（按第一次打开的项目定死）。
--revision 在该版本源码上跑同一场景（修前应复现 1、3）；--mutant 跑已知坏实现。
"""
import argparse
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture  # noqa: E402

MUTANTS = {
    # Every project's lanes in one list, as before.
    'no-scope': [('app/FlowPage.tsx', 'const mine = (item: { project: string }) => project === null || item.project === project;',
                  'const mine = (item: { project: string }) => true;')],
    # The title repeated even when it is the task name.
    'title-repeated': [('app/FlowPage.tsx', "{lane.name}{lane.title && lane.title !== lane.name && ` · ${lane.title}`}", "{lane.name} · {lane.title}")],
}
LANES = """(() => [...document.querySelectorAll('[data-flow-task]')].filter(n => !n.closest('[hidden]'))
  .map(n => ({ task: n.dataset.flowTask, title: n.querySelector('[data-flow-toggle]').textContent.trim() })))()"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=MUTANTS)
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, real_model_turns=0,
                  checks=[], failed=[], observed={})

    def plan(body):
        raise AssertionError('本场景不派 worker，不应有模型请求')

    fixture = Fixture('t178-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, []))
    report['fixture'] = str(fixture.dir)
    electron = None

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    def executor(project, repo):
        launch = fixture.run_cli('shell_start', '--project', project, '--cwd', str(repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project=project)
        assert window.get('ok'), window
        token = fixture.out / f'token-{launch}.txt'
        sent = fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()),
                               data=f'print -r -- $A2A_TERMINAL_TOKEN > {token}\r')
        assert sent.get('ok'), sent
        fixture.wait('令牌已写入', lambda: token.exists() and token.read_text().strip(), 30)
        identity = dict(kind='terminal', launch=launch, token=token.read_text().strip())
        with socket.socket(socket.AF_UNIX) as asker:
            asker.settimeout(60)
            asker.connect(str(fixture.state / 'control.sock'))
            asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role='executor', wait_seconds=60),
                                          identity=identity)) + '\n').encode())
            pending = fixture.wait('执行主控申请', lambda: [r for r in fixture.request('sidebar_snapshot')['role_requests'] if r['launch'] == launch], 20)
            assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True).get('ok')
            response = b''
            while b'\n' not in response:
                part = asker.recv(65536)
                assert part, '角色申请回执前断开'
                response += part
        granted = json.loads(response.split(b'\n', 1)[0])
        assert fixture.request('role_request_confirm', identity, role_request=granted['role_request']['id']).get('ok')
        return identity

    def create(controller, project, repo, task, title=None):
        card = fixture.out / f'{project}-{task}.json'
        card.write_text(json.dumps(dict(id=task, source=None, goal='写 done.txt', non_goals=['不改其他文件'],
            paths=dict(allow=['done.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
            red_commands=[], task_type='测试', repair_target=None, complexity='S',
            executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None)), encoding='utf-8')
        assert fixture.request('card_save', controller, task=task, card=str(card), expected_version=0).get('ok')
        created = fixture.request('create', controller, task=task, project=project, repo=str(repo), branch='refs/heads/main', card_version=1,
                                  **({'title': title} if title else {}))
        assert created.get('ok'), created

    def open_flow(project):
        electron.evaluate(f"document.querySelector('[data-project-id=\"{project}\"]').click()")
        electron.until('项目选中', f"document.querySelector('[data-project-id=\"{project}\"]')?.getAttribute('aria-current') === 'page'", 30)
        electron.until('流程页签', "!!document.querySelector('[data-flow-tab]')", 30)
        electron.evaluate("document.querySelector('[data-flow-tab]').click()")
        electron.until('泳道出现', "document.querySelectorAll('[data-flow-task]').length === 3", 30)
        return electron.evaluate(LANES)

    try:
        files = {'README.md': 'fixture\n', 'check.py': 'from pathlib import Path\nassert Path("done.txt").is_file()\n'}
        fixture.start(args.claude, files)
        other = fixture.dir / 'a2a'
        other.mkdir()
        for name, content in files.items():
            (other / name).write_text(content, encoding='utf-8')
        for command in (['git', 'init', '-q', '-b', 'main', str(other)], ['git', '-C', str(other), 'add', '.'],
                        ['git', '-C', str(other), 'commit', '-q', '-m', 'fixture-init']):
            subprocess.run(command, check=True, env=fixture.env)
        opened = fixture.request('project_open', fixture.operator, repo=str(other))
        assert opened.get('ok') and opened['project'] == 'a2a', opened
        create(executor('a2a', other), 'a2a', other, 'T-138')
        create(fixture.terminal, 'demo', fixture.repo, 'T-1')
        create(fixture.terminal, 'demo', fixture.repo, 'T-2', '导出 CSV')
        report['observed']['api_lanes'] = [lane['task'] for lane in fixture.request('flow_snapshot')['lanes']]

        electron = Electron(fixture, 't178-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]') && !!document.querySelector('[data-project-id=\"a2a\"]')")
        lanes = open_flow('demo')
        others = electron.evaluate("(() => { const s = document.querySelector('[data-flow-others]'); return s ? { count: s.dataset.flowOthers, text: s.querySelector('[data-flow-others-toggle]').textContent.trim(), expanded: s.querySelector('[data-flow-others-toggle]').getAttribute('aria-expanded') } : null; })()")
        report['observed']['demo'] = dict(lanes=lanes, others=others)
        electron.screenshot(fixture.out / '01-demo-flow.png')
        # 1: demo's own tickets first; a2a's not in view.
        check('demo_lanes_first_and_only_in_view', [lane['task'] for lane in lanes] == ['demo+T-1', 'demo+T-2'], lanes)
        # 2: a2a's ticket is in a folded group, not gone.
        check('other_project_folded', others is not None and others['count'] == '1' and others['expanded'] == 'false' and
              others['text'].endswith('其他项目的任务 1 张'), others)
        # 3: no repeated title; a real title stays.
        titles = {lane['task']: lane['title'] for lane in lanes}
        check('title_not_repeated', titles.get('demo+T-1', '').endswith('T-1') and 'T-1 · T-1' not in titles.get('demo+T-1', ''), titles)
        check('real_title_kept', titles.get('demo+T-2', '').endswith('T-2 · 导出 CSV'), titles)
        if others:
            electron.evaluate("document.querySelector('[data-flow-others-toggle]').click()")
            shown = electron.until('展开其他项目', f"(() => {{ const l = {LANES}; return l.some(x => x.task === 'a2a+T-138') ? l : null; }})()", 10)
            check('other_project_expands', [lane['task'] for lane in shown][-1] == 'a2a+T-138', shown)
            electron.evaluate("document.querySelector('#flow-others-lanes')?.scrollIntoView({ block: 'start' })")
            electron.screenshot(fixture.out / '02-demo-flow-others-open.png')
        # 4: switching project moves its own tickets to the top.
        lanes = open_flow('a2a')
        others = electron.evaluate("document.querySelector('[data-flow-others]')?.dataset.flowOthers ?? null")
        report['observed']['a2a'] = dict(lanes=lanes, others=others)
        check('a2a_lanes_first_after_switch', [lane['task'] for lane in lanes] == ['a2a+T-138'] and others == '2', report['observed']['a2a'])
        electron.screenshot(fixture.out / '03-a2a-flow.png')
        report['real_model_turns'] = fixture.api.main
        check('no_model_requests', fixture.api.main == 0, fixture.api.main)
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        if electron:
            try:
                electron.screenshot(fixture.out / 'failure.png')
            except BaseException:
                pass
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            report['out'] = str(fixture.out)
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], failed=[f['name'] for f in report['failed']], error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
