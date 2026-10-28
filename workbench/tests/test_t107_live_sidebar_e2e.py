"""T-107 复验（多 worker 之后）：真实后台、门禁、两个经角色申请批准的项目终端主控（构思、执行），同一项目里同时跑的
两个真实 Claude Code worker 与一个审查员（模型是本地脚本化接口），第二个项目，真实 Electron 侧栏。

期望来自 ticket 与场景本身：执行主控派出的 worker 和审查员挂在执行主控下（层级来自启动记录里的父 launch）；T-1 的 worker
在跑命令时是“运行中”，T-2 的 worker 交付后是“空闲”，两者同时在侧栏；审查员审查时挂在执行主控下，回收后是“已结束”；
项目终端主控没有结构化回合信号，显示“未知”（反例：不上调成运行中或空闲）；两个项目的分支与领先/落后数与
`git rev-list --left-right --count` 一致；点击 worker 行聚焦它。

已知、本测试只记录不判通过的：构思主控与执行主控都是项目终端时，两者之间没有保存的关系，执行主控进“未归属”。

失败方式（先列再写）：
1. 第二个 worker 或审查员没挂在执行主控下，或挂错层。
2. 状态上调：信号不全的会话显示成运行中或空闲；或跑命令的 worker 不是运行中。
3. 两个 worker 不能同时出现在侧栏。
4. 分支领先/落后数与 git 不一致。
5. 点击不聚焦。
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
from scripted_claude import Electron, Fixture, prompt_text, working_directory, review_steps  # noqa: E402

FILES = {'T-1': 'a.txt', 'T-2': 'b.txt'}
# Claude Code 2.1.310 blocks a standalone `sleep 45` tool call; a real long command keeps the worker running.
SLEEP = 'python3 -c "import time; time.sleep(45)"'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['terminal-shown-idle', 'parent-launch-ignored'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[], observed={})
    patches = {
        # A terminal controller without turn signals shown as idle instead of unknown.
        # (Since T-107 #4 the state comes from the terminal's hook events; these terminals were approved over the socket and have none.)
        'terminal-shown-idle': [('src/sidebar.ts', "const state: AgentState = last ?? (roleRequest.cli === 'claude' && roleRequest.native_session ? 'running' : 'unknown');",
                                 "const state: AgentState = 'idle';")],
        # The saved parent launch not used for the tree.
        'parent-launch-ignored': [('src/sidebar.ts', "    if (typeof record.parent_launch === 'string') senders.add(record.parent_launch);\n", '')],
    }.get(args.mutant, [])

    def plan(body):
        text = prompt_text(body)
        if '审查这一次交付' in text:
            task = next(task for task in FILES if f'demo+{task}' in text)
            fields = dict(verdict='可合并', findings=[], report={'结论': f'候选只改了 {FILES[task]}，满足任务卡。',
                                                                '完成条件与变异检查': f'变异：删除 {FILES[task]}，完成条件退出 1。'})
            return 'reviewer:' + task, review_steps(body, [('Bash', dict(command='sleep 20', description='read slowly')),
                                        ('Bash', dict(command=f'rm {FILES[task]}; python3 check_{task}.py; echo "mutation rc=$?"', description='mutation'))], fields), \
                '已提交审查结论。'
        cwd = working_directory(body)
        task = next(name for name in FILES if cwd.endswith(f'/{name}-a1'))
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        steps = [('Write', dict(file_path=f'{cwd}/{FILES[task]}', content='x\n')),
                 ('Bash', dict(command=f'git add {FILES[task]}', description='stage')),
                 ('Bash', dict(command=f'git commit -q -m "{task} fixture change"', description='commit')),
                 ('Bash', dict(command=submit, description='submit'))]
        if task == 'T-1':
            steps.insert(0, ('Bash', dict(command=SLEEP, description='a long command')))
        return 'worker:' + task, steps, '已交付。'

    fixture = Fixture('t107-', plan, revision=args.revision, patches=patches)
    report['fixture'] = str(fixture.dir)
    electron = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def git(repo, *arguments):
        return subprocess.check_output(['git', '-C', str(repo), *arguments], text=True, env=fixture.env).strip()

    def status(task):
        return fixture.request('status', fixture.operator, task=task)['task']

    def approve_terminal(project, repo, role):
        launch = fixture.run_cli('shell_start', '--project', project, '--cwd', str(repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project=project)
        assert window['ok'], window
        token_file = fixture.out / f'token-{role}.txt'
        assert fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()),
                               data=f'print -r -- $A2A_TERMINAL_TOKEN > {token_file}\r')['ok']
        fixture.wait('终端写出令牌', lambda: token_file.exists() and token_file.read_text().strip(), 30)
        identity = dict(kind='terminal', launch=launch, token=token_file.read_text().strip())
        asker = socket.socket(socket.AF_UNIX)
        asker.connect(str(fixture.state / 'control.sock'))
        asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role=role, wait_seconds=60),
                                       identity=identity)) + '\n').encode())
        pending = fixture.wait('角色申请出现', lambda: [r for r in fixture.request('sidebar_snapshot').get('role_requests', []) if r['launch'] == launch], 20)
        assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)['ok']
        response = b''
        while b'\n' not in response:
            response += asker.recv(65536)
        asker.close()
        granted = json.loads(response.split(b'\n', 1)[0])
        assert fixture.request('role_request_confirm', identity, role_request=granted['role_request']['id'])['ok']
        return launch

    def upstream(repo, name):
        remote = fixture.dir / f'{name}.git'
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(remote)], check=True, env=fixture.env)
        git(repo, 'remote', 'add', 'origin', str(remote))
        git(repo, 'push', '-q', '-u', 'origin', 'main')
        return remote

    def counts(repo):
        ahead, behind = git(repo, 'rev-list', '--left-right', '--count', 'HEAD...@{u}').split()
        return dict(branch=git(repo, 'rev-parse', '--abbrev-ref', 'HEAD'), ahead=int(ahead), behind=int(behind),
                    status_sb=git(repo, 'status', '-sb').splitlines()[0])

    def snapshot():
        return fixture.request('sidebar_snapshot')

    def rows():
        return electron.evaluate("[...document.querySelectorAll('.agent-row')].map(r=>({launch:r.dataset.agentLaunch,parent:r.dataset.agentParent,"
                                 "level:r.dataset.agentLevel,state:r.dataset.agentState,role:r.querySelector('.agent-role').textContent,"
                                 "meta:r.querySelector('.agent-meta').textContent,current:r.getAttribute('aria-current')}))")

    try:
        fixture.start(args.claude, {'README.md': 'demo\n', **{f'check_{t}.py': f'import pathlib, sys\nsys.exit(0 if pathlib.Path("{f}").is_file() else 1)\n' for t, f in FILES.items()}})
        executor = fixture.terminal_launch
        ideation = approve_terminal('demo', fixture.repo, 'ideation')
        upstream(fixture.repo, 'demo-remote')
        # The demo project one commit ahead of its upstream.
        (fixture.repo / 'NOTES.md').write_text('notes\n', encoding='utf-8')
        git(fixture.repo, 'add', 'NOTES.md')
        git(fixture.repo, 'commit', '-q', '-m', 'local change')
        # A second project, one commit behind its upstream.
        other = fixture.dir / 'other'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(other)], check=True, env=fixture.env)
        (other / 'README.md').write_text('other\n', encoding='utf-8')
        git(other, 'add', '.')
        git(other, 'commit', '-q', '-m', 'init')
        remote = upstream(other, 'other-remote')
        clone = fixture.dir / 'other-clone'
        subprocess.run(['git', 'clone', '-q', str(remote), str(clone)], check=True, env=fixture.env)
        (clone / 'NEWS.md').write_text('news\n', encoding='utf-8')
        git(clone, 'add', '.')
        git(clone, 'commit', '-q', '-m', 'upstream change')
        git(clone, 'push', '-q')
        git(other, 'fetch', '-q')
        assert fixture.request('project_open', fixture.operator, repo=str(other))['ok']

        for task, name in FILES.items():
            fixture.card(task, name, f'check_{task}.py')
        workers = {}
        for task in FILES:
            dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
            assert dispatched.get('ok'), dispatched
            workers[task] = dispatched['attempt']['runtime_identity']['launch']
        report['observed']['launches'] = dict(executor=executor, ideation=ideation, **workers)
        fixture.wait('T-2 交付', lambda: status('T-2')['state'] == 'submitted', 180)
        electron = Electron(fixture, 't107-' + fixture.dir.name[5:])
        electron.until('侧栏 agent', f"document.querySelectorAll('.agent-row').length >= 4", 30)
        both = electron.until('两个 worker 同时可见：一个运行中、一个空闲', f"""(()=>{{const s=Object.fromEntries([...document.querySelectorAll('.agent-row')].map(r=>[r.dataset.agentLaunch,r.dataset.agentState]));
            return s[{json.dumps(workers['T-1'])}]==='running'&&s[{json.dumps(workers['T-2'])}]==='idle'&&s}})()""", 40)
        seen = rows()
        electron.screenshot(fixture.out / '01-two-workers.png')
        report['observed']['rows_two_workers'] = seen
        by = {row['launch']: row for row in seen}
        check('workers_under_executor', all(by[workers[t]]['parent'] == executor and by[workers[t]]['level'] == '1' and by[workers[t]]['role'] == 'worker' for t in FILES) and
              by[executor]['level'] == '0' and by[executor]['role'] == '执行主控', seen)
        check('two_workers_at_once_running_and_idle', both[workers['T-1']] == 'running' and both[workers['T-2']] == 'idle', both)
        check('terminal_controllers_unknown_not_upgraded', by[executor]['state'] == 'unknown' and by[ideation]['state'] == 'unknown', seen)
        report['observed']['ideation_executor_link'] = dict(executor_parent=by[executor]['parent'],
            unassigned_label=electron.evaluate("[...document.querySelectorAll('.agent-task-label')].map(e=>e.textContent)"))

        # Branch facts against git itself.
        expected = {'demo': counts(fixture.repo), 'other': counts(other)}
        shown = {p['project_id']: p['git'] for p in snapshot()['projects']}
        titles = electron.evaluate("Object.fromEntries([...document.querySelectorAll('.project-row[data-project-id]')].map(r=>[r.dataset.projectId,r.title]))")
        report['observed']['git'] = dict(expected=expected, snapshot=shown, titles=titles)
        check('branch_counts_match_git', all(shown[p]['branch'] == expected[p]['branch'] and shown[p]['ahead'] == expected[p]['ahead'] and
                                             shown[p]['behind'] == expected[p]['behind'] and f"领先 {expected[p]['ahead']} / 落后 {expected[p]['behind']}" in titles[p]
                                             for p in expected) and expected['demo']['ahead'] == 1 and expected['other']['behind'] == 1, report['observed']['git'])

        # Clicking a worker focuses it.
        electron.evaluate(f"document.querySelector('.agent-row[data-agent-launch=\"{workers['T-2']}\"]').click()")
        electron.until('聚焦', f"document.querySelector('.agent-row[data-agent-launch=\"{workers['T-2']}\"]').getAttribute('aria-current')==='true'", 20)
        check('click_focuses_worker', True)

        # The reviewer of T-2 appears under the executor while it reviews, and ends when reclaimed.
        verified = fixture.request('verify', fixture.terminal, task='T-2')
        assert verified.get('ok'), verified
        reviewer = fixture.wait('审查员启动', lambda: next((a['id'] for a in snapshot()['agents'] if a['role'] == 'reviewer'), None), 60)
        electron.until('审查员出现', f"!!document.querySelector('.agent-row[data-agent-launch=\"{reviewer}\"]')", 30)
        row = next(r for r in rows() if r['launch'] == reviewer)
        electron.screenshot(fixture.out / '02-reviewer.png')
        report['observed']['reviewer_row'] = row
        check('reviewer_under_executor', row['parent'] == executor and row['level'] == '1' and row['role'] == '审查员', row)
        fixture.wait('T-2 审查通过', lambda: (lambda s: s['state'] == 'verified' and s.get('review', {}).get('state') == 'passed')(status('T-2')), 240)
        ended = electron.until('审查员已结束', f"document.querySelector('.agent-row[data-agent-launch=\"{reviewer}\"]')?.dataset.agentState==='ended'", 90)
        electron.screenshot(fixture.out / '03-reviewer-ended.png')
        check('reclaimed_reviewer_ended', ended)
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api_snapshot'] = fixture.api.snapshot()
        if electron:
            try:
                electron.screenshot(fixture.out / 'failure.png')
            except BaseException:
                pass
        raise
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
