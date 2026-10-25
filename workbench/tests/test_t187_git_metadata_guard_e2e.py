"""T-187（ready_rev 2）：Git 元数据守护。真实后台、门禁、经角色申请批准的终端主控，真实 Claude Code worker 与审查员
（模型是本地脚本化接口）。worker 交付之后、验收之前，测试从外面改动 Git 元数据，扮演没有操作系统沙箱的 worker
（agy 以 --dangerously-skip-permissions 运行时的处境）。

用户 2026-10-25 选“C 两者都作 worker”，选项原文：“agy 用 --dangerously-skip-permissions 全放开，只靠门禁事后检查；Git
元数据可能被改，每次派发写一次 ~/.gemini”。ticket 验收：“Git 元数据守护：反例中 worker 改动 worktree 的 HEAD/refs/hooks，
门禁拒绝交付；正例通过。”ticket 正文另列 config。

案例（期望来自 ticket，不读被测代码的输出）：
- hooks：在仓库的 hooks 目录放一个可执行的 post-merge。期望拒绝交付，并点名 hooks/post-merge。
- config：在仓库 config 里设 core.fsmonitor。期望拒绝交付，并点名 config。
- head：worktree 的 HEAD 从任务分支改为分离状态（同一提交，不建新 ref）。期望拒绝交付，并点名 HEAD。
- refs：把候选提交挂到一个新分支 leak，并把已有标签 release 移到候选提交上。期望拒绝交付，并点名这两个 ref。
- clean：干净交付，其间用户自己在主 checkout 里建分支、提交、来回切换。期望通过审查并集成，不误拒。

失败方式（先列再写）：
1. 门禁不看 Git 元数据（修前）：四个反例都被验收。
2. 只看一部分：例如只看 HEAD，不看 hooks、config 或 refs。
3. 把用户自己的分支、提交和切换当成 worker 的改动，误拒正例。
4. 拒绝后仍跑完成条件、审查或集成，或集成分支被移动。
5. 拒绝没记成一次打回（不回写 worker），或拒绝原因不点名改动的项目。
--revision 在该版本源码上跑（修前应复现 1）；--mutant 跑已知坏实现。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Fixture, prompt_text, quote, working_directory  # noqa: E402

GUARD = 'src/gates/core.ts'
MUTANTS = {
    # Only the worktree's HEAD and files; refs are not looked at.
    'refs-ignored': [(GUARD, '    if (first.length) {\n', '    if (false) {\n')],
    'head-ignored': [(GUARD, '    if (after.head !== before.head) changed.push("HEAD");\n', '')],
    'config-ignored': [(GUARD, '    if (after.config !== before.config) changed.push("config");\n', '')],
    # Every ref holding a worker commit counts, the attempt's own branch too.
    'own-branch-counted': [(GUARD, 'ref && ref !== own && !ref.startsWith("refs/a2a/")', 'ref && !ref.startsWith("refs/a2a/")')],
}
CASES = ['hooks', 'config', 'head', 'refs', 'clean']
FILES = {'README.md': 'fixture\n', 'check.py': 'from pathlib import Path\nassert Path("done.txt").read_text() == "done\\n"\n'}


def plan(body):
    text = prompt_text(body)
    if '审查这一次交付' in text:
        shape = json.loads(text[text.rindex('{\n  "schema": 1'):])
        shape.update(verdict='可合并', findings=[], report={'结论': '候选只改了 done.txt，满足任务卡。',
                                                            '完成条件与变异检查': '变异：删除 done.txt，完成条件失败。'})
        return 'reviewer', [('Bash', dict(command='rm done.txt; python3 check.py; echo "mutation rc=$?"', description='mutation'))], \
            json.dumps(shape, ensure_ascii=False)
    cwd = working_directory(body)
    submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
    # A gate repair message later in the same session gets no tool calls: the steps are counted per session.
    return 'worker', [('Write', dict(file_path=f'{cwd}/done.txt', content='done\n')),
                      ('Bash', dict(command='git add done.txt', description='stage')),
                      ('Bash', dict(command=f'git commit -q -m {quote("T-1 fixture change")}', description='commit')),
                      ('Bash', dict(command=submit, description='submit'))], '已交付。'


def run_case(name, args, out):
    report = dict(case=name, status='INCOMPLETE', checks=[], failed=[], observed={})

    def check(label, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=label, detail=detail))

    fixture = Fixture('t187g-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, []))
    report['fixture'] = str(fixture.dir)

    def git(*argv, cwd=None):
        return subprocess.run(['git', '-C', str(cwd or fixture.repo), *argv], check=True, capture_output=True, text=True,
                              env=fixture.env).stdout.strip()

    def status():
        return fixture.request('status', fixture.operator, task='demo+T-1')['task']

    def events():
        return fixture.request('events', fixture.operator, task='demo+T-1')['events']

    try:
        fixture.start(args.claude, FILES)
        if name == 'refs':
            git('tag', 'release')
        fixture.card('T-1', 'done.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        fixture.wait('交付', lambda: status()['state'] == 'submitted', 180)
        task = status()
        workspace, candidate = Path(task['current_attempt']['workspace']), task['candidate_commit']
        common = Path(git('rev-parse', '--path-format=absolute', '--git-common-dir'))
        main_before = git('rev-parse', 'refs/heads/main')
        if name == 'hooks':
            hook = common / 'hooks' / 'post-merge'
            hook.write_text('#!/bin/sh\necho planted\n', encoding='utf-8')
            hook.chmod(0o755)
        elif name == 'config':
            git('config', '--local', 'core.fsmonitor', 'echo planted')
        elif name == 'head':
            git('switch', '-q', '--detach', cwd=workspace)
        elif name == 'refs':
            git('branch', 'leak', candidate)
            git('tag', '-f', 'release', candidate)
        else:
            git('switch', '-q', '-c', 'user-side')
            (fixture.repo / 'notes.txt').write_text('user\n', encoding='utf-8')
            git('add', 'notes.txt')
            git('commit', '-q', '-m', 'user work meanwhile')
            git('switch', '-q', 'main')
        before = len(events())
        verified = fixture.request('verify', fixture.terminal, task='T-1')
        report['observed']['verify'] = {k: verified.get(k) for k in ('ok', 'error', 'details')}
        if name != 'clean':
            expected = {'hooks': ['hooks/post-merge'], 'config': ['config'], 'head': ['HEAD'],
                        'refs': ['refs/heads/leak', 'refs/tags/release']}[name]
            changed = (verified.get('details') or {}).get('changed') or []
            check('refused', verified.get('ok') is False and verified.get('error') == 'git_metadata_changed', report['observed']['verify'])
            check('names_what_changed', sorted(changed) == sorted(expected), dict(expected=expected, changed=changed))
            later = [e['type'] for e in events()[before:]]
            report['observed']['events'] = later
            task = status()
            check('counted_as_rejection', 'delivery_rejected' in later and (task.get('repair') or {}).get('check') == 'path_boundary', task.get('repair'))
            check('nothing_after_refusal', not any(t in later for t in ('completion_intent', 'completion_check', 'review_requested', 'integrated'))
                  and git('rev-parse', 'refs/heads/main') == main_before, later)
        else:
            check('verify_started', verified.get('ok') is True, report['observed']['verify'])
            fixture.wait('审查通过', lambda: (lambda s: s['state'] == 'verified' and s.get('review', {}).get('state') == 'passed')(status()), 240)
            fixture.wait('审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in events()), 60)
            score = fixture.out / 'score.json'
            score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='夹具', engineering_taste=3,
                                             engineering_reason='夹具', notes='T-187 guard fixture'), ensure_ascii=False), encoding='utf-8')
            integrated = fixture.request('integrate', fixture.terminal, task='T-1', score_file=str(score))
            report['observed']['integrate'] = {k: integrated.get(k) for k in ('ok', 'error', 'details')}
            check('integrated', integrated.get('ok') is True and status()['state'] == 'accepted'
                  and git('show', 'refs/heads/main:done.txt') == 'done', report['observed']['integrate'])
            check('not_rejected', not any(e['type'] == 'delivery_rejected' for e in events()))
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()[-2000:]
    finally:
        fixture.stop()
        if report['status'] == 'PASS':
            shutil.rmtree(fixture.dir, ignore_errors=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    parser.add_argument('--case', choices=CASES, action='append')
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=MUTANTS)
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    cases = [run_case(name, args, args.summary.parent) for name in args.case or CASES]
    failed = [f"{c['case']}:{f['name']}" for c in cases for f in c['failed']] + [f"{c['case']}:error" for c in cases if c.get('error')]
    summary = dict(status='PASS' if not failed else 'INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                   real_model_turns=0, failed=failed, cases=cases)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(status=summary['status'], failed=failed), ensure_ascii=False))
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
