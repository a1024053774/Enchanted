"""T-177（L04）：侧栏堆积与启动默认选中已结束终端。
真实后台、门禁、终端主控，真实 Claude Code worker 与审查员（模型是本地脚本化接口），真实 Electron 窗口经 DevTools 协议操作。
期望值来自 T-177 ticket：已结束/已作废 attempt 的会话默认折叠为“历史 N 个”，可展开、可一键清理（只从列表隐藏，不删证据，
不改门禁记录）；已集成任务名下仍空闲的 worker 给出“回收”入口（走门禁 reclaim，不自动关）；应用启动时默认选中最近活跃的会话
或空项目页，不选已结束终端。

场景（期望按场景手算）：
- T-1：a1、a2 各被修订作废并回收，a3 交付、审查通过、集成；a3 的 worker 集成后仍空闲。
  侧栏 T-1 当前只显示 a3 的 worker；历史 3 个（a1、a2 的 worker 与已回收的审查员）。只有 a3 的 worker 有“回收”。
- T-2：a1 被修订作废并回收，a2 派出后空闲（未交付、未集成）。当前显示 a2 的 worker，历史 1 个，没有“回收”。
- 终端主控（执行主控）是当前会话，不进历史。
- 用户在独立终端区开一个终端并 exit，它成为已结束终端；重启应用后不能默认选中它。

失败方式（先列再写）：
1. 作废 attempt 的会话与当前会话平铺在一起（L04 原样），没有“历史 N 个”。
2. 历史放得太宽：当前 attempt 的空闲 worker 或在任的主控被折进历史。
3. 清理删了证据或门禁记录（launch 记录、门禁事件变少），或能把仍在运行的会话从列表藏掉。
4. 清理后重启又回来了。
5. 回收入口出现在未集成任务上，或集成后自动关掉了 worker；回收不经门禁（门禁里没有该 attempt 的 reclaimed 事件）。
6. 启动时默认选中已结束终端。
--revision 在该版本源码上跑同一场景（修前应复现 1、4、5、6）；--mutant 跑已知坏实现。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory, review_steps  # noqa: E402

FILES = {'T-1': 'one.txt', 'T-2': 'two.txt'}
MUTANTS = {
    # Every session of the task, current or not, counted as history once the task has an older attempt.
    'history-too-wide': [('src/sidebar.ts', "const superseded = Boolean(record.attempt && current !== undefined && current.attempt !== record.attempt);",
                          "const superseded = Boolean(record.attempt && current !== undefined);")],
    # Cleanup hides any launch, including a live one.
    'hide-live': [('src/daemon.ts', "if (!rows.every(row => row?.state === 'ended')) throw new Refusal('session_not_ended');", '')],
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
            fields = dict(verdict='可合并', findings=[], report={'结论': '候选只改了 one.txt，满足任务卡。',
                                                                '完成条件与变异检查': '变异：删除 one.txt，完成条件退出 1。'})
            return 'reviewer', review_steps(body, [('Bash', dict(command='rm one.txt; python3 check_T-1.py; echo "mutation rc=$?"', description='mutation'))], fields), '已提交审查结论。'
        cwd = working_directory(body)
        task, attempt = re.search(r'/(T-\d)-a(\d)$', cwd).groups()
        if task == 'T-1' and attempt == '3':
            submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
            return 'worker:T-1-a3', [('Write', dict(file_path=f'{cwd}/one.txt', content='one\n')),
                                     ('Bash', dict(command='git add one.txt', description='stage')),
                                     ('Bash', dict(command=f'git commit -q -m {quote("T-1 fixture change")}', description='commit')),
                                     ('Bash', dict(command=submit, description='submit'))], '已交付。'
        # Every other attempt reads the card and stops: the controller revises the card before it delivers.
        return f'worker:{task}-a{attempt}', [('Bash', dict(command='ls', description='look'))], '卡里的完成条件要先改，我停下等修订。'

    fixture = Fixture('t177-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, []))
    report['fixture'] = str(fixture.dir)
    electron = None

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    def status(task):
        return fixture.request('status', fixture.operator, task=task)['task']

    def idle(thread):
        return (lambda p: p.get('state') == 'idle' and p.get('writing') is False and not p.get('failed') and not p.get('active') and not p.get('queued'))(
            fixture.request('pane_status', fixture.operator, thread=thread))

    def dispatch(task):
        result = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
        assert result.get('ok'), result
        return result['attempt']

    def revise(task, attempt, version):
        fixture.wait(f'{task} {attempt["attempt_id"][:8]} 回合结束', lambda: idle(attempt['thread_id']), 120)
        card = json.loads((fixture.out / f'{task}.json').read_text(encoding='utf-8'))
        card['goal'] += f'（v{version}）'
        (fixture.out / f'{task}-v{version}.json').write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
        for command, data in [('card_save', dict(card=str(fixture.out / f'{task}-v{version}.json'), expected_version=version - 1)),
                              ('revise', dict(spec_rev=version, card_version=version)), ('reclaim', dict(attempt=attempt['attempt_id']))]:
            result = fixture.request(command, fixture.terminal, task=task, **data)
            assert result.get('ok'), (command, result)

    def database(query, *values):
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(query, values)]

    def visible_rows():
        return electron.evaluate("[...document.querySelectorAll('[data-agent-launch]')].filter(n => !n.closest('[hidden]')).map(n => n.dataset.agentLaunch)")

    def history(task):
        return electron.evaluate(f"""(() => {{ const g = document.querySelector('[data-history-task="{task}"]');
          return g ? {{ count: Number(g.dataset.historyCount), text: g.querySelector('[data-history-toggle]')?.textContent ?? null,
            expanded: g.querySelector('[data-history-toggle]')?.getAttribute('aria-expanded') ?? null,
            rows: [...g.querySelectorAll('[data-agent-launch]')].map(n => n.dataset.agentLaunch) }} : null; }})()""")

    try:
        fixture.start(args.claude, {'README.md': 'demo\n',
                                    'check_T-1.py': 'import pathlib, sys\nsys.exit(0 if pathlib.Path("one.txt").read_text() == "one\\n" else 1)\n',
                                    'check_T-2.py': 'import pathlib, sys\nsys.exit(0 if pathlib.Path("two.txt").is_file() else 1)\n'})
        for task in FILES:
            fixture.card(task, FILES[task], f'check_{task}.py')
        attempts = {'T-1': [dispatch('T-1')], 'T-2': [dispatch('T-2')]}
        revise('T-1', attempts['T-1'][0], 2); attempts['T-1'].append(dispatch('T-1'))
        revise('T-2', attempts['T-2'][0], 2); attempts['T-2'].append(dispatch('T-2'))
        revise('T-1', attempts['T-1'][1], 3); attempts['T-1'].append(dispatch('T-1'))
        fixture.wait('T-1 a3 交付', lambda: status('T-1')['state'] == 'submitted', 180)
        verified = fixture.request('verify', fixture.terminal, task='T-1')
        assert verified.get('ok'), verified
        fixture.wait('T-1 审查通过', lambda: (lambda s: s['state'] == 'verified' and s.get('review', {}).get('state') == 'passed')(status('T-1')), 240)
        fixture.wait('T-1 审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in fixture.request('events', fixture.operator, task='T-1')['events']), 60)
        score = fixture.out / 'score.json'
        score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='夹具', engineering_taste=3,
                                         engineering_reason='夹具', notes='T-177 fixture'), ensure_ascii=False), encoding='utf-8')
        integrated = fixture.request('integrate', fixture.terminal, task='T-1', score_file=str(score))
        assert integrated.get('ok'), integrated
        fixture.wait('T-2 a2 回合结束', lambda: idle(attempts['T-2'][1]['thread_id']), 120)
        fixture.wait('T-1 a3 回合结束', lambda: idle(attempts['T-1'][2]['thread_id']), 120)

        catalog = fixture.request('sidebar_snapshot')
        rows = {row['id']: row for row in catalog['agents']}
        by_attempt = {(row['task'], row['attempt'], row['role']): row['id'] for row in catalog['agents'] if row['task']}
        task_id = lambda name: f'demo+{name}'
        worker = {f'{name}-a{i + 1}': by_attempt[(task_id(name), attempt['attempt_id'], 'worker')]
                  for name in FILES for i, attempt in enumerate(attempts[name])}
        reviewer = next(row['id'] for row in catalog['agents'] if row['role'] == 'reviewer')
        controller = fixture.terminal_launch
        report['observed']['launches'] = dict(worker=worker, reviewer=reviewer, controller=controller,
                                              states={key: rows[value]['state'] for key, value in worker.items()} | {'reviewer': rows[reviewer]['state']})

        electron = Electron(fixture, 't177-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        # The user opens a terminal in the standalone area and exits it.
        electron.evaluate("document.querySelector('.free-terminals').click()")
        electron.until('独立终端区', "document.querySelector('.free-terminals')?.getAttribute('aria-current') === 'page'", 30)
        before = set(electron.evaluate("window.a2a.selection().then(s => Object.values(s.launches))", 30) or [])
        electron.evaluate("window.dispatchEvent(new KeyboardEvent('keydown', { key: 't', metaKey: true })) || true")
        home = electron.until('新终端', f"window.a2a.selection().then(s => Object.entries(s.launches).find(([k, l]) => !{json.dumps(sorted(before))}.includes(l)) ?? null)", 30)
        home_key, home_launch = home
        electron.until('终端连接', f"window.a2a.snapshot({json.dumps(home_key)}).then(() => true, () => false)", 30)
        electron.evaluate(f"window.a2a.input({json.dumps(home_key)}, 'exit\\r').then(() => true)")
        fixture.wait('独立终端结束', lambda: any(row['id'] == home_launch and row['state'] == 'ended' for row in fixture.request('sidebar_snapshot')['terminals']), 30)
        report['observed']['home_terminal'] = home_launch
        # Counted after the standalone terminal exists: cleanup must not remove anything from here on.
        evidence_before = dict(launches=len(database('SELECT id FROM launch_records')),
                               gate_events={name: len(fixture.request('events', fixture.operator, task=task_id(name))['events']) for name in FILES})
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('侧栏有 worker', f"!!document.querySelector('[data-agent-launch=\"{worker['T-2-a2']}\"]')", 30)
        electron.screenshot(fixture.out / '01-sidebar.png')

        shown = visible_rows()
        report['observed']['visible_rows'] = shown
        # 1: only the current attempts' sessions are shown; older ones are folded.
        check('t1_shows_only_current_worker', worker['T-1-a3'] in shown and not {worker['T-1-a1'], worker['T-1-a2'], reviewer} & set(shown), shown)
        check('t2_shows_only_current_worker', worker['T-2-a2'] in shown and worker['T-2-a1'] not in shown, shown)
        h1, h2 = history(task_id('T-1')), history(task_id('T-2'))
        report['observed']['history_before'] = dict(T1=h1, T2=h2)
        check('t1_history_three_folded', h1 is not None and h1['count'] == 3 and h1['text'] == '历史 3 个' and h1['expanded'] == 'false' and
              set(h1['rows']) == {worker['T-1-a1'], worker['T-1-a2'], reviewer}, h1)
        check('t2_history_one_folded', h2 is not None and h2['count'] == 1 and set(h2['rows']) == {worker['T-2-a1']}, h2)
        # 2: the controller in office stays out of history.
        check('controller_not_history', controller in shown, shown)
        # Expanding shows the folded rows.
        electron.evaluate(f"document.querySelector('[data-history-task=\"{task_id('T-1')}\"] [data-history-toggle]')?.click() ?? null")
        opened = electron.until('历史展开', f"(() => {{ const rows = [...document.querySelectorAll('[data-agent-launch]')].filter(n => !n.closest('[hidden]')).map(n => n.dataset.agentLaunch); return {json.dumps(worker['T-1-a1'])} && rows.includes({json.dumps(worker['T-1-a1'])}) ? rows : null; }})()", 10) \
            if h1 else None
        check('t1_history_expands', bool(opened), opened)
        electron.screenshot(fixture.out / '02-history-open.png')

        # 5: reclaim only for the integrated task's idle worker, through the gate.
        reclaim_buttons = electron.evaluate("[...document.querySelectorAll('[data-reclaim-launch]')].map(n => n.dataset.reclaimLaunch)")
        report['observed']['reclaim_buttons'] = reclaim_buttons
        check('reclaim_only_on_integrated_idle_worker', reclaim_buttons == [worker['T-1-a3']], reclaim_buttons)
        check('integrated_worker_not_auto_closed', rows[worker['T-1-a3']]['state'] == 'idle', rows[worker['T-1-a3']]['state'])
        if reclaim_buttons == [worker['T-1-a3']]:
            electron.evaluate(f"document.querySelector('[data-reclaim-launch=\"{worker['T-1-a3']}\"]').click()")
            reclaimed = fixture.wait('门禁回收 a3', lambda: [e for e in fixture.request('events', fixture.operator, task=task_id('T-1'))['events']
                                                          if e['type'] == 'reclaimed' and e.get('attempt') == attempts['T-1'][2]['attempt_id']], 60)
            report['observed']['reclaimed_event'] = dict(type=reclaimed[-1]['type'], attempt=reclaimed[-1].get('attempt'), source=reclaimed[-1].get('source'))
            check('reclaim_through_gate', bool(reclaimed), report['observed']['reclaimed_event'])
            folded = electron.until('回收后进历史', f"(() => {{ const g = document.querySelector('[data-history-task=\"{task_id('T-1')}\"]'); return g && Number(g.dataset.historyCount) === 4 ? g.dataset.historyCount : null; }})()", 30)
            check('reclaimed_worker_into_history', folded == '4', folded)
        else:
            check('reclaim_through_gate', False, '没有回收入口')

        # 3: a live session cannot be hidden.
        refused = fixture.request('sidebar_hide', fixture.operator, launches=[worker['T-2-a2']])
        report['observed']['hide_live'] = dict(ok=refused.get('ok'), error=refused.get('error'))
        check('live_session_cannot_be_hidden', not refused.get('ok'), report['observed']['hide_live'])
        # Cleanup hides T-1's history from the list only.
        cleared = electron.evaluate(f"(() => {{ const b = document.querySelector('[data-history-task=\"{task_id('T-1')}\"] [data-history-clear]'); if (!b) return false; b.click(); return true; }})()")
        gone = electron.until('清理后消失', f"!document.querySelector('[data-history-task=\"{task_id('T-1')}\"]') && !document.querySelector('[data-agent-launch=\"{worker['T-1-a1']}\"]')", 30) if cleared else False
        check('cleanup_hides_t1_history', bool(gone), cleared)
        check('cleanup_keeps_t2_history', (history(task_id('T-2')) or {}).get('count') == 1, history(task_id('T-2')))
        evidence_after = dict(launches=len(database('SELECT id FROM launch_records')),
                              gate_events={name: len(fixture.request('events', fixture.operator, task=task_id(name))['events']) for name in FILES})
        report['observed']['evidence'] = dict(before=evidence_before, after=evidence_after)
        # The reclaim added gate events to T-1; cleanup removes nothing.
        check('cleanup_keeps_evidence', evidence_after['launches'] == evidence_before['launches'] and
              evidence_after['gate_events']['T-2'] == evidence_before['gate_events']['T-2'] and
              evidence_after['gate_events']['T-1'] >= evidence_before['gate_events']['T-1'] and
              fixture.request('launch_show', fixture.operator, launch=worker['T-1-a1']).get('ok') is True, report['observed']['evidence'])
        electron.screenshot(fixture.out / '03-after-cleanup.png')

        # 4 and 6: restart the application.
        electron.stop()
        electron = Electron(fixture, 't177b-' + fixture.dir.name[5:])
        electron.until('重启后项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.until('重启后读完', "document.querySelector('.project-list')?.getAttribute('aria-busy') === 'false'", 30)
        start = electron.evaluate("window.a2a.selection().then(s => ({ task: s.task?.task_id ?? null, project: s.project?.project_id ?? null, launches: Object.values(s.launches), focus: s.focus ?? null }))", 30)
        snapshot = fixture.request('sidebar_snapshot')
        live = {row['id'] for row in snapshot['agents'] + snapshot['terminals'] if row['state'] != 'ended'}
        report['observed']['startup'] = dict(start, live=sorted(live))
        check('startup_not_ended_terminal', home_launch not in start['launches'] and all(launch in live for launch in start['launches']), start)
        check('startup_selects_session_or_project', bool(start['launches']) and start['focus'] in live or start['project'] == 'demo', start)
        current = electron.evaluate("document.querySelector('[data-agent-launch][aria-current=\"true\"]')?.dataset.agentLaunch ?? null")
        report['observed']['startup_current_row'] = current
        check('startup_sidebar_marks_selection', current == start['focus'] if start['focus'] else True, current)
        electron.screenshot(fixture.out / '04-restarted.png')
        after_restart = visible_rows()
        check('cleanup_survives_restart', not {worker['T-1-a1'], worker['T-1-a2'], reviewer} & set(electron.evaluate(
            "[...document.querySelectorAll('[data-agent-launch]')].map(n => n.dataset.agentLaunch)")) and
              (history(task_id('T-2')) or {}).get('count') == 1, after_restart)
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
