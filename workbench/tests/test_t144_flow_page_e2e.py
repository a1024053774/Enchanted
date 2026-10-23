"""T-144：真实后台、门禁、Electron 与 Claude Code（claude-haiku-5-5 脚本化接口）。

失败方式（期望来自 T-144 任务卡；先列再实现）：
1. 标题显示 UUID，未使用角色与实际任务名；UUID 不在悬停提示。
2. 主控按终端的 task 字段归属，没有按它实际派发的 worker 归属。
3. 两个任务的主控串到对方泳道，或真无关联的主控混入任务。
4. 未归属主控没有逐项原因，主目录或额外目录被吞掉。
5. 修前版本或标题、归属两个变异未被拒绝。
6. 页面尚未加载就作断言，或 CLI 没有完成真实交付就冒称通过。

隔离夹具均保留；--summary 必须是新路径，截图与摘要同目录。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, prompt_text, working_directory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--revision')
    mode.add_argument('--mutant', choices=['uuid-title', 'terminal-task'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  checks=[], failures=[], observed={})
    fixture = electron = None
    suffix = uuid.uuid4().hex[:6]
    tasks = [f'T-left-{suffix}', f'T-right-{suffix}']

    def plan(body):
        text, cwd = prompt_text(body), working_directory(body)
        task = next(task for task in tasks if cwd.endswith(f'/{task}-a1'))
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return task, [('Write', dict(file_path=f'{cwd}/done.txt', content=task + '\n')),
                      ('Bash', dict(command='git add done.txt', description='stage')),
                      ('Bash', dict(command='git commit -q -m fixture-done', description='commit')),
                      ('Bash', dict(command=submit, description='submit'))], '已交付。'

    def check(name, condition, detail):
        report['checks'].append(dict(name=name, passed=bool(condition)))
        if not condition:
            report['failures'].append(dict(name=name, detail=detail))

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
            pending = fixture.wait('执行主控申请', lambda: [r for r in fixture.request('sidebar_snapshot')['role_requests']
                                                         if r['launch'] == launch], 20)
            decided = fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)
            assert decided.get('ok'), decided
            response = b''
            while b'\n' not in response:
                part = asker.recv(65536)
                assert part, '角色申请回执前断开'
                response += part
        granted = json.loads(response.split(b'\n', 1)[0])
        confirmed = fixture.request('role_request_confirm', identity, role_request=granted['role_request']['id'])
        assert confirmed.get('ok'), confirmed
        return identity

    try:
        patches = {
            'uuid-title': [('app/FlowPage.tsx', '<strong>{agent.role_label ?? agent.role}{agent.task_name && ` · ${agent.task_name}`}</strong>',
                            '<strong>{agent.id}</strong>')],
            'terminal-task': [('src/flow.ts', "agent.preset === 'executor' && bound.some(child => child.role === 'worker' && child.parent === agent.id)",
                              "agent.preset === 'executor' && agent.task === task.task_id")],
        }.get(args.mutant, [])
        fixture = Fixture('t144-', plan, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        files = {'README.md': 'fixture\n', 'check.py': 'from pathlib import Path\nassert Path("done.txt").is_file()\n'}
        fixture.start(args.claude, files)
        # Roles are exclusive within a project. Use independent projects so
        # each controller is genuinely approved through the normal entry point.
        repos = [fixture.repo, fixture.dir / 'other']
        for project in ('other', 'unrelated'):
            repo = fixture.dir / project
            repo.mkdir()
            for name, content in files.items():
                (repo / name).write_text(content, encoding='utf-8')
            for command in (['git', 'init', '-q', '-b', 'main', str(repo)], ['git', '-C', str(repo), 'add', '.'],
                            ['git', '-C', str(repo), 'commit', '-q', '-m', 'fixture-init']):
                subprocess.run(command, check=True, env=fixture.env)
            assert fixture.request('project_open', fixture.operator, repo=str(repo)).get('ok')
        projects = ['demo', 'other']
        controllers = [fixture.terminal, executor('other', repos[1])]
        loose = executor('unrelated', fixture.dir / 'unrelated')
        extra = fixture.dir / 'extra-directory'
        extra.mkdir()
        saved = fixture.request('project_settings_save', fixture.operator, project='demo', extra_directories=[str(extra)])
        assert saved.get('ok'), saved
        workers = []
        for task, controller, project, repo in zip(tasks, controllers, projects, repos):
            card = fixture.out / (task + '.json')
            card.write_text(json.dumps(dict(id=task, source=None, goal='写 done.txt', non_goals=['不改其他文件'],
                paths=dict(allow=['done.txt'], deny=[]), oracle_paths=['check.py'],
                completion_conditions=[dict(argv=['python3', 'check.py'])], red_commands=[], task_type='测试', repair_target=None,
                complexity='S', executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None)), encoding='utf-8')
            assert fixture.request('card_save', controller, task=task, card=str(card), expected_version=0).get('ok')
            assert fixture.request('create', controller, task=task, project=project, repo=str(repo),
                                   branch='refs/heads/main', card_version=1).get('ok')
            dispatched = fixture.request('dispatch', controller, task=task, runtimeMode='workspace-write')
            assert dispatched.get('ok'), dispatched
            workers.append(dispatched['attempt']['runtime_identity']['launch'])
        report['inputs'] = dict(tasks=tasks, projects=projects, controllers=[c['launch'] for c in controllers], workers=workers,
                                unrelated=loose['launch'], paths=[[str(fixture.repo), str(extra)], [str(repos[1])]])
        for task, project in zip(tasks, projects):
            fixture.wait('真实 Claude 交付 ' + task, lambda: fixture.request('status', fixture.operator,
                         task=project + '+' + task)['task']['state'] == 'submitted', 180)
        report['observed']['api_flow'] = fixture.request('flow_snapshot')
        report['observed']['sidebar'] = fixture.request('sidebar_snapshot')
        report['observed']['model_api'] = fixture.api.snapshot()
        electron = Electron(fixture, fixture.dir.name)
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('流程页签', "[...document.querySelectorAll('.task-header nav button')].some(b=>b.textContent==='流程')")
        electron.evaluate("[...document.querySelectorAll('.task-header nav button')].find(b=>b.textContent==='流程').click()")
        electron.until('两条泳道和全部会话', "document.querySelectorAll('[data-flow-task]').length===2 && document.querySelectorAll('[data-flow-agent]').length===5", 30)
        dom = electron.evaluate("({lanes:[...document.querySelectorAll('[data-flow-task]')].map(n=>({task:n.dataset.flowTask,"
            "paths:[...n.querySelectorAll('.flow-paths li')].map(p=>p.textContent),agents:[...n.querySelectorAll('[data-flow-agent]')].map(a=>({"
            "id:a.dataset.flowAgent,title:a.querySelector('strong').textContent,tooltip:a.title,role:a.dataset.flowRole,text:a.innerText}))})),"
            "unassigned:[...document.querySelectorAll('.flow-unassigned [data-flow-agent]')].map(a=>({id:a.dataset.flowAgent,"
            "title:a.querySelector('strong').textContent,tooltip:a.title,reason:a.querySelector('.flow-unassigned-reason')?.textContent,text:a.innerText}))})")
        report['observed']['dom'] = dom
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        shot = args.summary.with_suffix('.png')
        assert not shot.exists(), '截图路径必须新建'
        electron.screenshot(shot)
        report['screenshot'] = str(shot)
        for index, (task, controller, worker, project) in enumerate(zip(tasks, controllers, workers, projects)):
            lane = next(lane for lane in dom['lanes'] if lane['task'] == project + '+' + task)
            check(task + '_isolated_members', {a['id'] for a in lane['agents']} == {controller['launch'], worker}, lane)
            check(task + '_paths', lane['paths'] == report['inputs']['paths'][index], lane['paths'])
            by = {a['id']: a for a in lane['agents']}
            check(task + '_worker_title', by.get(worker, {}).get('title') == 'worker · ' + task, lane)
            check(task + '_controller_title', by.get(controller['launch'], {}).get('title') == '执行主控 · ' + task, lane)
        all_agents = dom['unassigned'] + [a for lane in dom['lanes'] for a in lane['agents']]
        uuid_pattern = r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'
        check('uuid_only_in_tooltip', all(not re.search(uuid_pattern, a['text'], re.I) and a['id'] in a['tooltip']
                                        for a in all_agents), all_agents)
        check('only_unrelated_controller_unassigned', [a['id'] for a in dom['unassigned']] == [loose['launch']], dom['unassigned'])
        check('unrelated_controller_reason', any(a['id'] == loose['launch'] and a.get('reason') and
              'worker' in a['reason'] for a in dom['unassigned']), dom['unassigned'])
        assert not report['failures'], report['failures']
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        if fixture:
            report['observed']['model_api_at_failure'] = fixture.api.snapshot()
            if fixture.running:
                try:
                    report['observed']['sidebar_at_failure'] = fixture.request('sidebar_snapshot')
                    report['observed']['native_output_at_failure'] = {
                        agent['id']: fixture.request('pane_output', launch=agent['id'], offset=0, max_bytes=6000)
                        for agent in report['observed']['sidebar_at_failure'].get('agents', []) if agent['role'] == 'worker'}
                except Exception as diagnostic_error:
                    report['diagnostic_error'] = str(diagnostic_error)
        raise
    finally:
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
