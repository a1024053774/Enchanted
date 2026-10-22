"""T-136 复盘。真实后台、门禁、终端主控，真实 Claude Code worker、审查员与复盘会话（模型是本地脚本化接口），真实 Electron。

期望来自 ticket 与本场景：T-1（报一个问题，用户答复）集成后第一次复盘，包里只有 T-1 和它的问题、答复、审查、打分、提交尾注；
T-2 集成后第二次复盘，包从上次复盘结束开始，只有 T-2。复盘会话只写自己的 out 目录，往项目里写（Write 工具或 shell 重定向）
都被拒；报告复制到项目的 findings/，建议出现在界面上，批准后有记录。周期：到点（注入的时钟）启动一次，同一时刻再查不重复，
在界面上关掉后下一周不启动。

失败方式（先列再写）：
1. 包没按时间范围截：第二次复盘里还有 T-1，或 T-1 的问题。
2. 包内容与库对不上：任务、问题、答复、审查、打分、尾注缺项。
3. 会话能写项目：Write 工具或 shell 命令在项目里留下文件。
4. 报告没进 findings/，或建议没上界面、批准没有记录。
5. 周期：关掉后还启动，或同一个时刻启动两次。
6. 复盘会话没有启动记录（argv 里看不到所选模型）。
--revision 在该版本源码上跑（修前没有复盘）；--mutant 跑已知坏实现。
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, gate_line, prompt_text, quote, working_directory  # noqa: E402

FILES = {'T-1': 'a.txt', 'T-2': 'b.txt'}
ISSUE = 'a.txt 的格式没写'
ANSWER = '纯文本就行。'
MODEL = 'claude-haiku-5-5'
REPORT = '# 复盘\n\n范围内集成 T-1；问题 1 条已答复。\n'
SUGGESTION = '任务卡写明文件格式'
SET_VALUE = ("var set=(el,v)=>{const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;"
             "Object.getOwnPropertyDescriptor(proto,'value').set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));};")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['package-ignores-range', 'out-not-confined', 'schedule-fires-when-disabled', 'import-failure-silent', 'archive-source-not-isolated',
                                                  'archive-not-in-range', 'start-failure-silent'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[])
    patches = {
        'package-ignores-range': [('src/retrospective.ts', 'const inRange = (time: string) => (!since || time >= since) && time < until;',
                                   'const inRange = (time: string) => Boolean(time);')],
        # The session's settings without the project-directory denial: Claude's sandbox lets commands write the working directory.
        'out-not-confined': [('src/retrospective.ts', ", deny: [`Edit(/${run.repo}/**)`] }", ' }'),
                             ('src/retrospective.ts', ', denyWrite: [run.repo] }', ' }')],
        'import-failure-silent': [('src/retrospective.ts', "this.record(run, 'import_failed', { reason, error });", 'void error;')],
        # T-135 review 01 P2: one unreadable source stops the whole sweep.
        'archive-source-not-isolated': [('src/trajectoryArchive.ts', '      try { this.copy(source); }\n', '      this.copy(source); try { /* mutant */ }\n')],
        # Review 01 F1: every archived session ever, not those of the range.
        'archive-not-in-range': [('src/retrospective.ts', "FROM trajectory_archive WHERE created_at < ? GROUP BY launch, source HAVING max(created_at) >= ?')\n    .all(until, since ?? '')",
                                  "FROM trajectory_archive GROUP BY launch, source')\n    .all()")],
        # Review 01 F2: a run whose terminal never opened, left "in progress".
        'start-failure-silent': [('src/daemon.ts', 'retrospectives.record(run.id, "start_failed", { error: String(error) });', 'void error;')],
        'schedule-fires-when-disabled': [('src/retrospective.ts', '    if (!schedule.enabled) return null;\n', '')],
    }.get(args.mutant, [])

    def plan(body):
        text = prompt_text(body)
        dump = json.dumps(body['messages'], ensure_ascii=False)
        out = re.search(r'只能写 (/\S+) 这个目录', dump)
        if out and '做一次复盘' in dump:
            out = out.group(1)
            repo = str(fixture.repo)
            if out not in outs:
                outs.append(out)
            if out != outs[0]:
                # Later sessions leave a suggestions file that is not JSON; the test then checks how the import reports it.
                return 'retro:' + out, [('Write', dict(file_path=f'{out}/report.md', content=REPORT)),
                                        ('Write', dict(file_path=f'{out}/suggestions.json', content='[{"title": '))], '复盘写完了。'
            return 'retro:' + out, [
                ('Write', dict(file_path=f'{out}/report.md', content=REPORT)),
                ('Write', dict(file_path=f'{repo}/hack.md', content='越权\n')),
                ('Bash', dict(command=f'echo 越权 > {repo}/hack2.txt; echo "rc=$?"', description='write outside')),
                ('Write', dict(file_path=f'{out}/suggestions.json', content=json.dumps(
                    [dict(title=SUGGESTION, body='T-1 的 worker 为格式报了问题。', kind='role-card')], ensure_ascii=False))),
            ], '复盘写完了。'
        if '审查这一次交付' in text:
            shape = json.loads(text[text.rindex('{\n  "schema": 1'):])
            task = next(task for task in FILES if f'demo+{task}' in text)
            shape.update(verdict='可合并', findings=[], report={'结论': f'候选只改了 {FILES[task]}，满足任务卡。',
                                                                '完成条件与变异检查': f'变异：删除 {FILES[task]}，完成条件退出 1。'})
            return 'reviewer:' + task, [('Bash', dict(command=f'rm {FILES[task]}; python3 check_{task}.py; echo "mutation rc=$?"', description='mutation'))], \
                json.dumps(shape, ensure_ascii=False)
        cwd = working_directory(body)
        task = next(name for name in FILES if cwd.endswith(f'/{name}-a1'))
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        steps = [('Write', dict(file_path=f'{cwd}/{FILES[task]}', content='x\n')),
                 ('Bash', dict(command=f'git add {FILES[task]}', description='stage')),
                 ('Bash', dict(command=f'git commit -q -m {quote(task + " fixture change")}', description='commit')),
                 ('Bash', dict(command=submit, description='submit'))]
        if task == 'T-1':
            issue = gate_line(body, f"'issue' '--task' '{{task}}' '--title' {quote(ISSUE)} '--body' {quote('卡里没说格式；先按纯文本做。')} '--blocking' 'false'")
            steps.insert(0, ('Bash', dict(command=issue, description='issue')))
        return 'worker:' + task, steps, '已交付。'

    outs = []
    fixture = Fixture('t136-', plan, revision=args.revision, patches=patches)
    # The user's project is one they already trust in their own Claude (a2a never answers that question in the user's home).
    (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
        'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
    report['fixture'] = str(fixture.dir)
    electron = None
    locked = []

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def status(task):
        return fixture.request('status', fixture.operator, task=task)['task']

    def gate_events(task):
        return fixture.request('events', fixture.operator, task=task)['events']

    def listing():
        listed = fixture.request('retrospective_list', project='demo')
        assert listed.get('ok'), listed
        return listed

    def run_task(task):
        dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        fixture.wait(f'{task} 交付', lambda: status(task)['state'] == 'submitted', 180)
        if task == 'T-1':
            views = fixture.wait('T-1 问题进门禁', lambda: fixture.request('issues', fixture.operator, task='T-1')['issues'], 60)
            answered = fixture.request('answer_issue', fixture.operator, task='T-1', issue=views[0]['issue']['id'], answer=ANSWER)
            assert answered.get('ok'), answered
            fixture.wait('答复送到 worker', lambda: any(ANSWER in json.dumps(b['messages'], ensure_ascii=False) for b in fixture.api.bodies if b['key'] == 'worker:T-1'), 120)
        verified = fixture.request('verify', fixture.terminal, task=task)
        assert verified.get('ok'), verified
        fixture.wait(f'{task} 审查通过', lambda: (lambda s: s['state'] == 'verified' and s.get('review', {}).get('state') == 'passed')(status(task)), 240)
        fixture.wait(f'{task} 审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in gate_events(task)), 60)
        score = fixture.out / f'score-{task}.json'
        score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='夹具', engineering_taste=2,
                                         engineering_reason='夹具', notes='T-136 fixture'), ensure_ascii=False), encoding='utf-8')
        integrated = fixture.request('integrate', fixture.terminal, task=task, score_file=str(score))
        assert integrated.get('ok'), integrated
        return dispatched

    def retro_results(out):
        return fixture.api.results.get('retro:' + out, [])

    try:
        (fixture.repo / 'findings').mkdir(parents=True)
        fixture.start(args.claude, {'README.md': 'demo\n', 'findings/README.md': '发现\n',
                                    **{f'check_{t}.py': f'import pathlib, sys\nsys.exit(0 if pathlib.Path("{f}").is_file() else 1)\n' for t, f in FILES.items()}})
        # T-2 is created after the first retrospective, so nothing of it falls in that range.
        fixture.card('T-1', FILES['T-1'], 'check_T-1.py')
        run_task('T-1')

        # T-1's native records, made unreadable for now: archiving the retrospective session must not wait on them.
        locked += [path for path in (fixture.home / '.claude/projects').rglob('*.jsonl')]
        for path in locked:
            path.chmod(0)

        # 1: the user starts a retrospective from the desktop with Claude Code and the model they pick.
        electron = Electron(fixture, 't136-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('复盘页签', "!!document.querySelector('[data-retrospective-tab]')", 20)
        electron.evaluate("document.querySelector('[data-retrospective-tab]').click()")
        electron.until('复盘页', "!!document.querySelector('[data-start-retrospective]')", 30)
        electron.evaluate(SET_VALUE + f"set([...document.querySelectorAll('.retrospective-page label')].find(l=>l.textContent.startsWith('模型')).querySelector('input'),{json.dumps(MODEL)});")
        electron.until('模型已填', f"[...document.querySelectorAll('.retrospective-page label')].find(l=>l.textContent.startsWith('模型')).querySelector('input').value==={json.dumps(MODEL)}", 10)
        electron.evaluate("document.querySelector('[data-start-retrospective]').click()")
        first = fixture.wait('第一次复盘开始', lambda: listing()['runs'], 30)[0]
        report['first_run'] = {k: first[k] for k in ('id', 'trigger', 'since', 'until', 'cli', 'model', 'effort', 'out')}
        electron.until('复盘记录出现', f"!!document.querySelector('tr[data-run-id=\"{first['id']}\"]')", 20)
        electron.screenshot(fixture.out / '01-retrospective-started.png')

        started = [e for e in fixture.request('orchestration_events')['events'] if e['type'] == 'retrospective_started']
        argv = started[0]['data']['argv'] if started else []
        check('session_has_launch_record', len(started) == 1 and first['cli'] == 'Claude Code' and first['model'] == MODEL and
              argv[argv.index('--model') + 1] == MODEL and fixture.request('launch_show', fixture.operator, launch=started[0]['launch'])['launch']['role'] == 'shell',
              dict(run=report['first_run'], argv=argv[:12]))

        # 2: the package the script prepared, against this scenario.
        package = json.loads(Path(first['package']).read_text(encoding='utf-8'))
        report['first_package'] = {k: package[k] for k in ('since', 'until', 'tasks', 'issues', 'panel', 'reviews', 'rejections')}
        report['first_package']['commit_trailers'] = package['commit_trailers']
        tasks1 = [t['task'] for t in package['tasks']]
        check('package_matches_scenario', first['trigger'] == 'manual' and first['since'] is None and len(tasks1) == 1 and tasks1[0].endswith('+T-1') and
              package['tasks'][0]['task_type'] == '测试' and
              [i['title'] for i in package['issues']] == [ISSUE] and
              any(p['kind'] == 'answer' and p['body'] == ANSWER for p in package['panel']) and
              any(u['text'] == ANSWER for u in package['user_inputs']) and
              [r['verdict'] for r in package['reviews']] == ['可合并'] and
              [s['data']['result'] for s in package['scores']] == ['通过'] and package['rejections'] == [] and
              any(c['trailers'].get('Task', '').endswith('+T-1') for c in package['commit_trailers']['commits']) and
              package['commit_trailers']['without_trailers'] >= 1 and
              package['metrics']['first_time']['integrated'] == 1, report['first_package'])

        # 3: the session writes its report and suggestions, and nothing in the project.
        out = first['out']
        fixture.wait('复盘会话写完', lambda: (Path(out) / 'suggestions.json').exists(), 180)
        results = retro_results(out)
        report['session_results'] = results
        # The minute timer may already have imported the report into findings/; that copy is a2a's, not the session's.
        changed = [line for line in fixture.git('status', '--porcelain', '--untracked-files=all').splitlines()
                   if not re.fullmatch(r'\?\? findings/\d{4}-\d\d-\d\d-retrospective-[0-9a-f]{8}\.md', line)]
        check('session_writes_outside_refused', not (fixture.repo / 'hack.md').exists() and not (fixture.repo / 'hack2.txt').exists() and
              len(results) >= 3 and results[1]['is_error'] and 'rc=0' not in results[2]['text'] and changed == [],
              dict(results=results, changed=changed))

        # 4: imported: report in findings/, the suggestion on the page; the user approves it there.
        ticked = fixture.request('retrospective_tick', fixture.operator)
        assert ticked.get('ok'), ticked
        imported = fixture.wait('导入', lambda: next((e for e in next(r for r in listing()['runs'] if r['id'] == first['id'])['events'] if e['type'] == 'imported'), None), 30)
        destination = Path(imported['data']['report'])
        check('report_in_findings', destination.parent == fixture.repo / 'findings' and destination.read_text(encoding='utf-8') == REPORT, str(destination))
        card = electron.until('建议出现', f"(c=>c&&{{id:c.dataset.suggestionId,state:c.dataset.suggestionState,text:c.textContent}})([...document.querySelectorAll('.suggestion-card')].find(c=>c.textContent.includes({json.dumps(SUGGESTION)})))", 20)
        electron.screenshot(fixture.out / '02-suggestion-open.png')
        electron.evaluate(f"[...document.querySelector('.suggestion-card[data-suggestion-id=\"{card['id']}\"]').querySelectorAll('button')].find(b=>b.textContent==='批准').click()")
        electron.until('建议已批准', f"document.querySelector('.suggestion-card[data-suggestion-id=\"{card['id']}\"]')?.dataset.suggestionState==='approved'", 20)
        electron.screenshot(fixture.out / '03-suggestion-approved.png')
        decided = [s for s in listing()['suggestions'] if s['id'] == card['id']]
        check('suggestion_on_page_and_approved', card['state'] == 'open' and decided and decided[0]['decision']['approved'] is True, decided)

        # The session's own native record is archived like any other (T-135).
        native = started[0]['data']['native_session']
        def archived():
            with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as connection:
                try:
                    return [row for row in connection.execute('SELECT source, end FROM trajectory_archive WHERE launch=?', (started[0]['launch'],))
                            if Path(row[0]).name == f'{native}.jsonl' and row[1] > 0]
                except sqlite3.OperationalError:
                    return []
        archived_rows = fixture.wait('复盘会话归档', archived, 45)
        failed = [e for e in fixture.request('orchestration_events')['events'] if e['type'] == 'trajectory_archive_failed']
        for path in locked:
            path.chmod(0o600)
        report['archive_failures'] = [dict(source=e['data'].get('source'), error=e['data'].get('error')) for e in failed]
        locked_failed = {e['data'].get('source') for e in failed}
        check('session_archived_despite_unreadable_source', archived_rows and locked_failed and
              locked_failed <= {str(path) for path in locked} and len(failed) == len(locked_failed), dict(locked=[str(p) for p in locked], failed=report['archive_failures']))

        # 5: the second retrospective starts where the first ended and holds only T-2.
        fixture.card('T-2', FILES['T-2'], 'check_T-2.py')
        run_task('T-2')
        second = fixture.request('retrospective_start', fixture.operator, project='demo', cli='Claude Code', model=MODEL, effort='low')
        assert second.get('ok'), second
        package2 = json.loads(Path(second['run']['package']).read_text(encoding='utf-8'))
        tasks2 = [t['task'] for t in package2['tasks']]
        report['second_package'] = {k: package2[k] for k in ('since', 'until', 'tasks', 'issues', 'panel', 'trajectory_archive')}
        # Sessions archived during the second range, read straight from the index (T-136 review 01 F1).
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as connection:
            archived_in_range = {row[0] for row in connection.execute('SELECT launch FROM trajectory_archive WHERE created_at >= ? AND created_at < ?',
                                                                    (package2['since'], package2['until']))}
            archived_before = {row[0] for row in connection.execute('SELECT launch FROM trajectory_archive WHERE created_at < ?', (package2['until'],))}
        report['archive_range'] = dict(in_range=sorted(archived_in_range), any_before_until=sorted(archived_before))
        check('second_package_archive_in_range', {a['launch'] for a in package2['trajectory_archive']} == archived_in_range and
              archived_before - archived_in_range,
              dict(package=[a['launch'] for a in package2['trajectory_archive']], in_range=sorted(archived_in_range)))
        check('second_package_only_in_range', second['run']['since'] == first['until'] and len(tasks2) == 1 and tasks2[0].endswith('+T-2') and
              package2['issues'] == [] and package2['panel'] == [] and
              not any(c['trailers'].get('Task', '').endswith('+T-1') for c in package2['commit_trailers']['commits']) and
              any(c['trailers'].get('Task', '').endswith('+T-2') for c in package2['commit_trailers']['commits']), report['second_package'])

        # A session that leaves a broken suggestions file: recorded once, shown on the run, imported once fixed.
        out2 = Path(second['run']['out'])
        fixture.wait('第二次复盘写完', lambda: (out2 / 'suggestions.json').exists(), 180)
        for _ in range(2):
            assert fixture.request('retrospective_tick', fixture.operator)['ok']
        run2 = lambda: next(r for r in listing()['runs'] if r['id'] == second['run']['id'])
        failures = [e for e in run2()['events'] if e['type'] == 'import_failed']
        shown = electron.until('导入失败显示', f"(r=>r&&r.dataset.runState==='failed'&&r.textContent)(document.querySelector('tr[data-run-id=\"{second['run']['id']}\"]'))", 20)
        electron.screenshot(fixture.out / '04-import-failed.png')
        (out2 / 'suggestions.json').write_text('[]', encoding='utf-8')
        assert fixture.request('retrospective_tick', fixture.operator)['ok']
        report['broken_suggestions'] = dict(failures=failures, shown=shown, events=[e['type'] for e in run2()['events']])
        check('broken_suggestions_reported_once_then_imported', [e['data']['reason'] for e in failures] == ['suggestions_not_json'] and
              'suggestions.json 不是合法 JSON' in shown and any(e['type'] == 'imported' for e in run2()['events']), report['broken_suggestions'])

        # 6: the schedule: a slot two days ahead fires once at its time (injected clock), not twice; switched off on the page, the next week does not.
        local = datetime.now().astimezone() + timedelta(days=2)
        slot = local.replace(hour=10, minute=0, second=0, microsecond=0)
        saved = fixture.request('retrospective_schedule_save', fixture.operator, weekday=(slot.weekday() + 1) % 7, hour=10, minute=0, model=MODEL, effort='low')
        assert saved.get('ok'), saved
        at = (slot + timedelta(minutes=1)).astimezone(timezone.utc).isoformat()
        before = fixture.request('retrospective_tick', fixture.operator, now=(slot - timedelta(minutes=1)).astimezone(timezone.utc).isoformat())
        fired = fixture.request('retrospective_tick', fixture.operator, now=at)
        again = fixture.request('retrospective_tick', fixture.operator, now=at)
        report['schedule'] = dict(saved=saved['schedule'], before=len(before['started']), fired=[r['scheduled_for'] for r in fired['started']], again=len(again['started']))
        check('schedule_fires_once_at_its_time', before['started'] == [] and len(fired['started']) == 1 and fired['started'][0]['trigger'] == 'schedule' and
              datetime.fromisoformat(fired['started'][0]['scheduled_for'].replace('Z', '+00:00')) == slot and again['started'] == [], report['schedule'])
        electron.until('周期开关', "document.querySelector('[data-schedule-enabled]')?.checked === true", 20)
        electron.evaluate("document.querySelector('[data-schedule-enabled]').click()")
        electron.until('周期已关', "document.querySelector('[data-schedule-enabled]')?.checked === false", 20)
        electron.screenshot(fixture.out / '05-schedule-off.png')
        next_week = fixture.request('retrospective_tick', fixture.operator, now=(slot + timedelta(days=7, minutes=1)).astimezone(timezone.utc).isoformat())
        report['schedule']['next_week_after_off'] = len(next_week['started'])
        check('schedule_off_does_not_fire', listing()['schedule']['enabled'] is False and next_week['started'] == [], report['schedule'])
        # 7: a run whose terminal cannot open (its project directory is gone) says so on the run (review 01 F2).
        broken = fixture.dir / 'broken'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(broken)], check=True, env=fixture.env)
        (broken / 'README.md').write_text('broken\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(broken), 'add', '.'], check=True, env=fixture.env)
        subprocess.run(['git', '-C', str(broken), 'commit', '-q', '-m', 'init'], check=True, env=fixture.env)
        assert fixture.request('project_open', fixture.operator, repo=str(broken))['ok']
        broken.rename(fixture.dir / 'broken-moved')
        refused = fixture.request('retrospective_start', fixture.operator, project='broken', cli='Claude Code', model=MODEL, effort='low')
        runs = fixture.request('retrospective_list', project='broken')['runs']
        report['start_failure'] = dict(refused=refused, events=[[e['type'] for e in r['events']] for r in runs])
        check('start_failure_recorded_on_run', not refused.get('ok') and len(runs) == 1 and
              [e['type'] for e in runs[0]['events']] == ['start_failed'], report['start_failure'])
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
        # Readable again even when the run stopped early, so the fixture can be archived.
        for path in locked:
            path.chmod(0o600)
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
