"""T-133 用户输入记录页、T-134 指标页。真实后台、门禁、终端主控，真实 Claude Code worker 与审查员（模型是本地
脚本化接口），真实 Electron 窗口经 DevTools 协议操作。

场景（期望值按场景手算，不读被测代码的输出）：
- T-1（文档）：一次交付通过，没人插手。打分 边界 3、品味 3。
- T-2（文档）：worker 先上报一条非阻塞问题，用户经桌面应用的问题入口答复；交付后用户在它的窗格里粘贴一段字并回车。
  打分 边界 2、品味 1。
- T-3（测试）：第一次交付内容不对，完成条件不过，门禁打回（completion）；worker 改好重交后通过。打分 边界 3、品味 2。
由此：集成 3 个，一次到位 1 个（T-2 有人介入，T-3 交付两轮且有打回），比例 0.333；打回 completion 1 次，其余 0；
注意力：T-2 答题 1、介入 1（一次回车提交），其余为 0；worker 与审查员会话的模型是接口实际回的模型，不是卡上请求的；
终端主控会话没有回合记录，模型记 unknown。打分汇总：文档 2 个 attempt，边界 2.5、品味 2；测试 1 个，边界 3、品味 2。
记录页的期望来自库里的 user_inputs 与门禁规则（落在受管 attempt 会话里的输入记为人工介入）。

失败方式（先列再写）：
1. 记录页没有、条数与库不符，或人工介入标错（T-133）。
2. 派发给 worker 的文字出现在记录里。
3. 指标把请求模型当实际模型；把有人介入的交付算作一次到位；打回原因、注意力、打分均值与手算不符（T-134）。
4. 没有数据时显示 0 而不是“无数据”。
5. 读取失败时显示为空。
--revision 在该版本源码上跑（修前没有这两页与命令）；--mutant 跑已知坏实现。
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import SERVED_MODEL, Electron, Fixture, gate_line, prompt_text, quote, working_directory, review_steps  # noqa: E402

FILES = {'T-1': 'a.txt', 'T-2': 'b.txt', 'T-3': 'c.txt'}
TYPES = {'T-1': '文档', 'T-2': '文档', 'T-3': '测试'}
SCORES = {'T-1': (3, 3), 'T-2': (2, 1), 'T-3': (3, 2)}
ANSWER = '先按卡做，内容格式以后再说。'
TYPED = 'T-133：请确认 b.txt 结尾有换行'
SET_VALUE = ("var set=(el,v)=>{const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;"
             "Object.getOwnPropertyDescriptor(proto,'value').set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));};")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['intervention-unmarked', 'requested-as-observed', 'intervention-ignored', 'error-shown-as-empty', 'range-by-created-only'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[])
    patches = {
        # T-133: the records page loses the intervention mark.
        'intervention-unmarked': [('src/userInputRecords.ts', 'intervention: interventions.get(input.id) ?? null,', 'intervention: null,')],
        # T-134: the model a session was asked for, reported as the one it ran.
        'requested-as-observed': [('src/metrics.ts', "model: facts ? [...facts.models].join(' / ') : 'unknown',", "model: record.model_requested ?? 'unknown',")],
        # T-134: a delivery somebody intervened in counted as first-time.
        'intervention-ignored': [('src/metrics.ts', 'score.facts.delivery_rounds === 1 && score.facts.human_interventions === 0 &&', 'score.facts.delivery_rounds === 1 &&')],
        # Review 01: a session counted only when it started in the range.
        'range-by-created-only': [('src/metrics.ts', ".filter(record => (!range.project || record.project === range.project) && (inTime(record.created_at) || observed.has(record.id)))",
                                   ".filter(record => (!range.project || record.project === range.project) && inTime(record.created_at))")],
        # A failed read shown as no data.
        'error-shown-as-empty': [('app/MetricsPage.tsx', "(reason: unknown) => { if (mounted) setError('指标读取失败：' + String(reason)); }",
                                  "(reason: unknown) => { if (mounted) setMetrics({ model_use: { sessions: [], by_model: [] }, first_time: { integrated: 0, first_time: 0, rate: null, rejections: {} }, attention: [], scores: [] }); }")],
    }.get(args.mutant, [])

    def plan(body):
        text = prompt_text(body)
        if '审查这一次交付' in text:
            named = [task for task in FILES if f'demo+{task}' in text]
            assert len(named) == 1, named
            task = named[0]
            fields = dict(verdict='可合并', findings=[], report={'结论': f'候选只改了 {FILES[task]}，满足任务卡。',
                                                                '完成条件与变异检查': f'变异：删除 {FILES[task]}，完成条件退出 1。'})
            return 'reviewer:' + task, review_steps(body, [('Bash', dict(command=f'rm {FILES[task]}; python3 check_{task}.py; echo "mutation rc=$?"', description='mutation'))], fields), '已提交审查结论。'
        cwd = working_directory(body)
        task = next(name for name in FILES if cwd.endswith(f'/{name}-a1'))
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        deliver = lambda content, message: [
            ('Write', dict(file_path=f'{cwd}/{FILES[task]}', content=content)),
            ('Bash', dict(command=f'git add {FILES[task]}', description='stage')),
            ('Bash', dict(command=f'git commit -q -m {quote(message)}', description='commit')),
            ('Bash', dict(command=submit, description='submit'))]
        if task == 'T-1':
            return 'worker:T-1', deliver('a\n', 'T-1 fixture change'), '已交付。'
        if task == 'T-2':
            issue = gate_line(body, f"'issue' '--task' '{{task}}' '--title' {quote('b.txt 的格式没写')} '--body' {quote('卡里没说 b.txt 的格式；先按纯文本做。')} '--blocking' 'false'")
            return 'worker:T-2', [('Bash', dict(command=issue, description='issue'))] + deliver('b\n', 'T-2 fixture change'), '已交付。'
        # T-3: the first delivery fails its completion condition; after the gate's repair prompt the worker fixes it.
        prompts = sum(1 for message in body['messages'] if message['role'] == 'user' and
                      (isinstance(message['content'], str) or any(isinstance(part, dict) and part.get('type') == 'text' for part in message['content'])))
        steps = deliver('wrong\n', 'T-3 first try') + (deliver('ok\n', 'T-3 repair') if prompts >= 2 else [])
        return 'worker:T-3', steps, '已交付。'

    fixture = Fixture('t133-', plan, revision=args.revision, patches=patches)
    report['fixture'] = str(fixture.dir)
    electron = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def status(task):
        return fixture.request('status', fixture.operator, task=task)['task']

    def gate_events(task):
        return fixture.request('events', fixture.operator, task=task)['events']

    def database(query, *values):
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(query, values)]

    def run_task(task, between=None):
        dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        fixture.wait(f'{task} 交付', lambda: status(task)['state'] == 'submitted', 180)
        if between:
            between(dispatched)
        verified = fixture.request('verify', fixture.terminal, task=task)
        if task == 'T-3':
            assert not verified.get('ok') and verified.get('error') == 'oracle_failed', verified
            first = status(task)['candidate_commit']
            fixture.wait('T-3 改好重交', lambda: (lambda s: s['state'] == 'submitted' and s['candidate_commit'] != first)(status(task)), 180)
            verified = fixture.request('verify', fixture.terminal, task=task)
        assert verified.get('ok'), verified
        fixture.wait(f'{task} 审查通过', lambda: (lambda s: s['state'] == 'verified' and s.get('review', {}).get('state') == 'passed')(status(task)), 240)
        fixture.wait(f'{task} 审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in gate_events(task)), 60)
        boundary, taste = SCORES[task]
        score = fixture.out / f'score-{task}.json'
        score.write_text(json.dumps(dict(result='通过', boundary_discipline=boundary, boundary_reason='夹具', engineering_taste=taste,
                                         engineering_reason='夹具', notes='T-133/T-134 fixture'), ensure_ascii=False), encoding='utf-8')
        integrated = fixture.request('integrate', fixture.terminal, task=task, score_file=str(score))
        assert integrated.get('ok'), integrated
        return dispatched

    def t2_inputs(dispatched):
        # The user answers the worker's issue through the desktop's issue entry, then types in the worker's pane.
        # From here on is the range of the range check: T-2's worker started before it and has turns after it.
        report['t_mid'] = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        views = fixture.wait('T-2 问题进门禁', lambda: fixture.request('issues', fixture.operator, task='T-2')['issues'], 60)
        answered = fixture.request('answer_issue', fixture.operator, task='T-2', issue=views[0]['issue']['id'], answer=ANSWER)
        assert answered.get('ok'), answered
        fixture.wait('答复送到 worker', lambda: any(ANSWER in json.dumps(b['messages'], ensure_ascii=False) for b in fixture.api.bodies if b['key'] == 'worker:T-2'), 120)
        worker = dispatched['attempt']['runtime_identity']['launch']
        window = fixture.request('window_open', fixture.operator, launch=worker, task=dispatched['attempt']['task_id'])
        assert window['ok'], window
        for sequence, data in enumerate(['\x1b[200~' + TYPED + '\x1b[201~', '\r'], 1):
            sent = fixture.request('window_input', window['identity'], sequence=sequence, request_id=str(uuid.uuid4()), data=data)
            assert sent['ok'], sent
            time.sleep(.5)
        fixture.wait('键入送到 worker', lambda: any(TYPED in json.dumps(b['messages'], ensure_ascii=False) for b in fixture.api.bodies if b['key'] == 'worker:T-2'), 120)
        fixture.wait('T-2 回合结束', lambda: status('T-2')['state'] == 'submitted', 30)

    try:
        files = {'README.md': 'demo\n',
                 'check_T-1.py': 'import pathlib, sys\nsys.exit(0 if pathlib.Path("a.txt").is_file() else 1)\n',
                 'check_T-2.py': 'import pathlib, sys\nsys.exit(0 if pathlib.Path("b.txt").is_file() else 1)\n',
                 'check_T-3.py': 'import pathlib, sys\np = pathlib.Path("c.txt")\nsys.exit(0 if p.is_file() and p.read_text() == "ok\\n" else 1)\n'}
        fixture.start(args.claude, files)
        for task, name in FILES.items():
            fixture.card(task, name, f'check_{task}.py', TYPES[task])
        run_task('T-1')
        t2_worker = run_task('T-2', t2_inputs)['attempt']['runtime_identity']['launch']
        run_task('T-3')

        # T-134: the daemon's read command against the hand-computed values.
        metrics = fixture.request('metrics', fixture.operator, project='demo')
        assert metrics.get('ok'), metrics
        report['metrics'] = metrics
        first = metrics['first_time']
        check('first_time_rate_counts_interventions_and_rounds', first['integrated'] == 3 and first['first_time'] == 1 and first['rate'] == 0.333 and
              first['rejections'] == dict(identity_version=0, path_boundary=0, oracle=0, completion=1, red_state=0, rule_checks=0,
                                          independent_review=0, commit_trailers=0), first)
        attention = {row['task'].split('+')[1]: (row['answers'], row['approvals'], row['interventions'], row['stops']) for row in metrics['attention']}
        check('attention_per_integrated_task', attention == {'T-1': (0, 0, 0, 0), 'T-2': (1, 0, 1, 0), 'T-3': (0, 0, 0, 0)}, attention)
        sessions = metrics['model_use']['sessions']
        managed = [s for s in sessions if s['role'] in ('worker', 'reviewer')]
        controller = [s for s in sessions if s['role'] == 'executor']
        check('model_use_is_observed_not_requested', len(managed) == 6 and all(s['model'] == SERVED_MODEL and s['requested_model'] == 'claude-haiku-5-5'
              and s['turns'] > 0 for s in managed) and len(controller) == 1 and controller[0]['model'] == 'unknown', sessions)
        by_model = {(row['model'], row['task_type']): row['sessions'] for row in metrics['model_use']['by_model']}
        check('model_use_by_model_and_task_type', by_model == {(SERVED_MODEL, '文档'): 4, (SERVED_MODEL, '测试'): 2, ('unknown', '项目级'): 1}, by_model)
        scores = {row['task_type']: (row['model'], row['attempts'], row['results'], row['boundary_discipline'], row['engineering_taste']) for row in metrics['scores']}
        check('scores_by_executor_and_task_type', scores == {'文档': (SERVED_MODEL, 2, {'通过': 2}, 2.5, 2), '测试': (SERVED_MODEL, 1, {'通过': 1}, 3, 2)}, scores)
        later = fixture.request('metrics', fixture.operator, project='demo', since=report['t_mid'])
        whole = next(s for s in sessions if s['launch'] == t2_worker)
        part = [s for s in later['model_use']['sessions'] if s['launch'] == t2_worker]
        report['range_check'] = dict(whole_turns=whole['turns'], part=part)
        check('range_counts_turns_in_range', len(part) == 1 and 1 <= part[0]['turns'] < whole['turns'], report['range_check'])
        empty = fixture.request('metrics', fixture.operator, project='demo', since='2099-01-01T00:00:00.000Z')
        check('no_data_is_null_not_zero', empty.get('ok') and empty['first_time']['rate'] is None and not empty['attention'] and not empty['scores']
              and not empty['model_use']['sessions'], empty)

        # T-133: the records read against the stored user inputs and the gate's intervention rule.
        stored = [json.loads(row['data']) for row in database("SELECT data FROM user_inputs WHERE json_extract(data,'$.target.project')='demo' ORDER BY rowid")]
        expected_marked = {i['id'] for i in stored if i['target'].get('attempt') and i['channel'] != 'ui-derived' and i['form'] != 'gap'}
        report['stored_inputs'] = [dict(form=i['form'], channel=i['channel'], text=i['text'][:80], attempt=i['target'].get('attempt')) for i in stored]
        typed = [i for i in stored if i['text'] == TYPED]
        answer = [i for i in stored if i['form'] == 'answer' and ANSWER in i['text']]
        assert len(typed) == 1 and len(answer) == 1, report['stored_inputs']

        electron = Electron(fixture, 't133-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('记录页签', "!!document.querySelector('[data-records-tab]')", 20)
        electron.evaluate("document.querySelector('[data-records-tab]').click()")
        electron.until('记录表', f"document.querySelectorAll('.user-input-page tr[data-input-id]').length === {len(stored)}", 30)
        electron.screenshot(fixture.out / '01-records.png')
        rows = electron.evaluate("[...document.querySelectorAll('.user-input-page tr[data-input-id]')].map(r=>({id:r.dataset.inputId,"
                                 "marked:!!r.dataset.intervention,badge:!!r.querySelector('.record-intervention'),text:r.innerText}))")
        report['records_rows'] = rows
        check('records_page_matches_stored_inputs', [r['id'] for r in rows] == [i['id'] for i in stored], rows)
        check('interventions_marked_by_gate_rule', {r['id'] for r in rows if r['marked'] and r['badge']} == expected_marked and
              typed[0]['id'] in expected_marked and answer[0]['id'] in expected_marked, dict(rows=rows, expected=sorted(expected_marked)))
        # T-206: the paste and its Enter are one sent message; the Enter is not a record of its own.
        enter = [i for i in stored if i['text'] == '\r']
        check('enter_not_separate_record', not enter and any(r['id'] == typed[0]['id'] and TYPED in r['text'] for r in rows), rows)
        check('dispatch_text_not_recorded', not any('显式交付' in r['text'] or '审查这一次交付' in r['text'] for r in rows), rows)
        # The project terminal's own input (the fixture printed its token there) is not recorded: T-133's open gap.
        report['terminal_input_recorded'] = any('A2A_TERMINAL_TOKEN' in i['text'] for i in stored)

        electron.evaluate("document.querySelector('[data-metrics-tab]').click()")
        electron.until('指标页', "!!document.querySelector('.metrics-page [data-rate]')", 30)
        electron.screenshot(fixture.out / '02-metrics.png')
        shown = electron.evaluate("({rate:document.querySelector('.metrics-page [data-rate]').dataset.rate,"
                                  "sections:[...document.querySelectorAll('.metric-section')].map(s=>s.dataset.metric),"
                                  "models:[...document.querySelectorAll('[data-metric=\"model-use\"] tr[data-model]')].map(r=>r.dataset.model+'|'+r.dataset.taskType),"
                                  "none:document.querySelectorAll('.metrics-page .metric-none').length})")
        report['metrics_page'] = shown
        check('metrics_page_shows_four_views', shown['rate'] == '0.333' and shown['sections'] == ['model-use', 'first-time', 'attention', 'scores'] and
              sorted(shown['models']) == sorted([f'{SERVED_MODEL}|文档', f'{SERVED_MODEL}|测试', 'unknown|项目级']) and shown['none'] == 0, shown)
        electron.evaluate(SET_VALUE + "set(document.querySelector('.metrics-page input[type=date]'),'2099-01-01');")
        electron.until('无数据', "document.querySelectorAll('.metrics-page .metric-none').length >= 4", 20)
        electron.screenshot(fixture.out / '03-metrics-no-data.png')
        check('metrics_page_says_no_data', not electron.evaluate("!!document.querySelector('.metrics-page [data-rate]')"))

        fixture.stop()
        electron.until('读取失败提示', "document.querySelector('.metrics-page [role=\"alert\"]')?.textContent.includes('指标读取失败') ?? false", 30)
        electron.screenshot(fixture.out / '04-metrics-read-failed.png')
        check('metrics_read_failure_is_not_no_data', True)
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
