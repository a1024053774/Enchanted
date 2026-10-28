"""T-180（L07）：首次派发前主控必须停下来问用户工作分支。
真实后台、门禁、经角色申请批准的终端主控，真实 Claude Code worker 与审查员（模型是本地脚本化接口），真实 Electron 窗口经 DevTools 协议操作。
期望值来自 T-180 ticket：用户没有指定工作分支时，主控派发自动从当前分支新建 `enchanted/<名称>` 工作分支并告知用户；
用户指定了就用用户的；不动 main/master，不 push。设置页新增“工作分支前缀”（默认 `enchanted/`），改后对新任务生效。
门禁仍校验工作分支合法。名称规则（本票写明）：前缀 + 项目名；门禁要求同一仓库的任务共用一个工作分支，已有任务的项目沿用它。

场景：
- 项目 demo：主控建 T-1 不写 branch，派发、交付、验收、集成；再建 T-2 不写 branch。
- 在设置页把前缀改成 `team/`（先试一个非法前缀）；项目 other 建 T-9 不写 branch。
- 项目 spec：用户指定已存在的 `feature/x`，建 T-5 写 branch。

失败方式（先列再写）：
1. 不写 branch 时 create 被拒（L07 原样：只能问用户）。
2. 建了分支但名称不对（不是 enchanted/demo），或不是从当前分支起的，或回执没写分支名、是否新建（主控没法告诉用户）。
3. 集成写进了 main：main 头变了；或 push 了（夹具仓库没有 remote，push 会失败，这里核对 main 不动、集成落在工作分支）。
4. 同一项目第二个任务又建一个新分支，被门禁以 project_branch_conflict 拒。
5. 设置页改前缀不生效，或新前缀只在重启后生效；非法前缀被存下；改前缀后已有任务的项目被换到新分支（门禁会以 project_branch_conflict 拒）。
6. 用户指定的分支被忽略，仍建 enchanted/ 分支。
7. 门禁不再校验：用户指定一个不存在的分支也被接受。
8. （T-183）门禁拒绝了不带 branch 的 create，后台新建的分支却留下；下一次 create 回执写成“已存在”。
--revision 在该版本源码上跑同一场景（修前应复现 1）；--mutant 跑已知坏实现。
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
from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory, review_steps  # noqa: E402

MUTANTS = {
    # T-183: a refused create keeps the branch it made.
    'keep-branch-on-refusal': [('src/daemon.ts', '    if (!result?.ok && made) await dropWorkBranch(repo, made, result?.error);\n', '')],
    # The saved prefix is ignored: always enchanted/.
    'prefix-ignored': [('src/daemon.ts', 'command.project, store.workBranchPrefix(),', "command.project, 'enchanted/',")],
    # Every create gets a fresh branch even when the repo's tasks already have one.
    'no-reuse': [('src/daemon.ts', '      gates.repoWorkBranch(command.repo));', '      null);')],
}


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
        text = prompt_text(body)
        if '审查这一次交付' in text:
            fields = dict(verdict='可合并', findings=[], report={'结论': '候选只改了 done.txt，满足任务卡。',
                                                                '完成条件与变异检查': '变异：删除 done.txt，完成条件失败。'})
            return 'reviewer', review_steps(body, [('Bash', dict(command='rm done.txt; python3 check.py; echo "mutation rc=$?"', description='mutation'))], fields), '已提交审查结论。'
        cwd = working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return 'worker', [('Write', dict(file_path=f'{cwd}/done.txt', content='done\n')),
                          ('Bash', dict(command='git add done.txt', description='stage')),
                          ('Bash', dict(command=f'git commit -q -m {quote("T-1 fixture change")}', description='commit')),
                          ('Bash', dict(command=submit, description='submit'))], '已交付。'

    fixture = Fixture('t180-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, []))
    report['fixture'] = str(fixture.dir)
    electron = None
    files = {'README.md': 'fixture\n', 'check.py': 'from pathlib import Path\nassert Path("done.txt").read_text() == "done\\n"\n'}

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    def git(repo, *argv):
        result = subprocess.run(['git', '-C', str(repo), *argv], capture_output=True, text=True, env=fixture.env)
        return result.stdout.strip() if result.returncode == 0 else None

    def repo(name):
        path = fixture.dir / name
        path.mkdir()
        for file, content in files.items():
            (path / file).write_text(content, encoding='utf-8')
        for command in (['init', '-q', '-b', 'main'], ['add', '.'], ['commit', '-q', '-m', 'fixture-init']):
            subprocess.run(['git', '-C', str(path), *command], check=True, env=fixture.env)
        opened = fixture.request('project_open', fixture.operator, repo=str(path))
        assert opened.get('ok') and opened['project'] == name, opened
        return path

    def executor(project, path):
        launch = fixture.run_cli('shell_start', '--project', project, '--cwd', str(path))['launch']['id']
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

    def create(controller, project, path, task, branch=None):
        card = fixture.out / f'{project}-{task}.json'
        card.write_text(json.dumps(dict(id=task, source=None, goal='写 done.txt', non_goals=['不改其他文件'],
            paths=dict(allow=['done.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
            red_commands=[], task_type='测试', repair_target=None, complexity='S',
            executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None)), encoding='utf-8')
        assert fixture.request('card_save', controller, task=task, card=str(card), expected_version=0).get('ok')
        return fixture.request('create', controller, task=task, project=project, repo=str(path), card_version=1,
                               **({'branch': branch} if branch else {}))

    def status(task):
        return fixture.request('status', fixture.operator, task=task)['task']

    try:
        fixture.start(args.claude, files)
        demo = fixture.repo
        main_before = git(demo, 'rev-parse', 'refs/heads/main')
        # 1, 2: no branch named.
        first = create(fixture.terminal, 'demo', demo, 'T-1')
        report['observed']['demo_T-1'] = {k: first.get(k) for k in ('ok', 'error', 'details', 'work_branch')}
        check('create_without_branch_succeeds', first.get('ok') is True, first.get('error'))
        check('default_branch_named_and_reported', first.get('ok') and first['task']['integration_ref'] == 'refs/heads/enchanted/demo' and
              first.get('work_branch', {}).get('ref') == 'refs/heads/enchanted/demo' and first['work_branch'].get('created') is True,
              report['observed']['demo_T-1'])
        check('default_branch_from_current_head', git(demo, 'rev-parse', 'refs/heads/enchanted/demo') == main_before)
        if first.get('ok'):
            # The first dispatch goes through: deliver, verify, review, integrate.
            dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
            assert dispatched.get('ok'), dispatched
            fixture.wait('交付', lambda: status('demo+T-1')['state'] == 'submitted', 180)
            assert fixture.request('verify', fixture.terminal, task='T-1').get('ok')
            fixture.wait('审查通过', lambda: (lambda s: s['state'] == 'verified' and s.get('review', {}).get('state') == 'passed')(status('demo+T-1')), 240)
            fixture.wait('审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in fixture.request('events', fixture.operator, task='demo+T-1')['events']), 60)
            score = fixture.out / 'score.json'
            score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='夹具', engineering_taste=3,
                                             engineering_reason='夹具', notes='T-180 fixture'), ensure_ascii=False), encoding='utf-8')
            integrated = fixture.request('integrate', fixture.terminal, task='T-1', score_file=str(score))
            head = git(demo, 'rev-parse', 'refs/heads/enchanted/demo')
            report['observed']['integrate'] = dict(ok=integrated.get('ok'), error=integrated.get('error'), work_head=head,
                                                   main=git(demo, 'rev-parse', 'refs/heads/main'), main_before=main_before)
            # 3: integration lands on the work branch, main untouched.
            check('integrated_on_work_branch_main_untouched', integrated.get('ok') and status('demo+T-1')['state'] == 'accepted' and
                  head != main_before and git(demo, 'show', f'{head}:done.txt') == 'done' and
                  git(demo, 'rev-parse', 'refs/heads/main') == main_before, report['observed']['integrate'])
        # 4: the project's next task stays on its work branch.
        second = create(fixture.terminal, 'demo', demo, 'T-2')
        report['observed']['demo_T-2'] = {k: second.get(k) for k in ('ok', 'error', 'work_branch')}
        check('second_task_reuses_work_branch', second.get('ok') and second['task']['integration_ref'] == 'refs/heads/enchanted/demo' and
              second['work_branch'].get('created') is False, report['observed']['demo_T-2'])

        # 5: the prefix setting, through the settings page.
        electron = Electron(fixture, 't180-' + fixture.dir.name[5:])
        electron.until('窗口就绪', "!!document.querySelector('button[aria-label=\"设置\"]')")
        electron.evaluate("document.querySelector('button[aria-label=\"设置\"]').click()")
        shown = electron.until('前缀设置', "(() => { const i = document.querySelector('[data-work-branch-prefix] input'); return i && !i.disabled ? i.value : null; })()", 30)
        check('settings_default_prefix', shown == 'enchanted/', shown)

        def save(value):
            electron.evaluate(f"""(() => {{ const i = document.querySelector('[data-work-branch-prefix] input');
              Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(i, {json.dumps(value)});
              i.dispatchEvent(new Event('input', {{ bubbles: true }})); }})()""")
            electron.evaluate("document.querySelector('[data-work-branch-prefix] button').click()")
            return electron.until('保存结果', "document.querySelector('[data-work-branch-prefix] [role=status]')?.textContent || null", 20)

        bad = save('bad..prefix/')
        check('invalid_prefix_refused', '不能用作' in bad and fixture.request('work_branch_prefix', fixture.operator).get('prefix') == 'enchanted/', bad)
        good = save('team/')
        electron.evaluate("document.querySelector('[data-work-branch-prefix]').scrollIntoView({ block: 'center' })")
        electron.screenshot(fixture.out / '01-settings-prefix.png')
        check('prefix_saved', '已保存' in good and fixture.request('work_branch_prefix', fixture.operator).get('prefix') == 'team/', good)
        # 4 again: after the prefix changed, a project that has tasks keeps its work branch (the gate allows one per repo).
        third = create(fixture.terminal, 'demo', demo, 'T-3')
        report['observed']['demo_T-3'] = {k: third.get(k) for k in ('ok', 'error', 'work_branch')}
        check('project_with_tasks_keeps_branch_after_prefix_change', third.get('ok') and third['task']['integration_ref'] == 'refs/heads/enchanted/demo' and
              git(demo, 'rev-parse', '--verify', '--quiet', 'refs/heads/team/demo') is None, report['observed']['demo_T-3'])
        other = repo('other')
        ninth = create(executor('other', other), 'other', other, 'T-9')
        report['observed']['other_T-9'] = {k: ninth.get(k) for k in ('ok', 'error', 'work_branch')}
        check('new_prefix_used_for_new_project', ninth.get('ok') and ninth['task']['integration_ref'] == 'refs/heads/team/other' and
              git(other, 'rev-parse', 'refs/heads/team/other') == git(other, 'rev-parse', 'refs/heads/main'), report['observed']['other_T-9'])

        # 8 (T-183): a create the gate refuses (no saved card) leaves no branch; the next one reports it as new.
        atom = repo('atom')
        atom_controller = executor('atom', atom)
        refused = fixture.request('create', atom_controller, task='T-7', project='atom', repo=str(atom), card_version=1)
        left = git(atom, 'rev-parse', '--verify', '--quiet', 'refs/heads/team/atom')
        report['observed']['atom_refused'] = dict(ok=refused.get('ok'), error=refused.get('error'), branch_left=left)
        check('refused_create_leaves_no_branch', refused.get('ok') is not True and left is None, report['observed']['atom_refused'])
        retried = create(atom_controller, 'atom', atom, 'T-7')
        report['observed']['atom_T-7'] = {k: retried.get(k) for k in ('ok', 'error', 'work_branch')}
        check('next_create_reports_new_branch', retried.get('ok') and (retried.get('work_branch') or {}).get('created') is True and
              retried['work_branch'].get('reason') == 'default', report['observed']['atom_T-7'])

        # 6, 7: a branch the user named.
        spec = repo('spec')
        subprocess.run(['git', '-C', str(spec), 'branch', 'feature/x'], check=True, env=fixture.env)
        spec_controller = executor('spec', spec)
        missing = create(spec_controller, 'spec', spec, 'T-4', 'refs/heads/feature/missing')
        check('missing_named_branch_refused', missing.get('ok') is not True, missing.get('error'))
        named = create(spec_controller, 'spec', spec, 'T-5', 'refs/heads/feature/x')
        report['observed']['spec_T-5'] = {k: named.get(k) for k in ('ok', 'error', 'work_branch')}
        check('named_branch_used', named.get('ok') and named['task']['integration_ref'] == 'refs/heads/feature/x' and
              git(spec, 'for-each-ref', '--format=%(refname)', 'refs/heads/team', 'refs/heads/enchanted') == '', report['observed']['spec_T-5'])
        report['real_model_turns'] = 0
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
