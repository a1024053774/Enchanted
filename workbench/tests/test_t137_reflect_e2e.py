"""T-137 Reflect 页。真实后台、门禁、项目终端，真实 Claude Code worker、审查员与复盘会话（模型是本地脚本化接口），
真实 Electron 窗口经 DevTools 协议操作。

场景（期望来自 ticket 与用户决定，不读被测代码的输出）：
1. 全新数据目录：定期复盘是关闭的；注入时钟到下一个周一 9:00（默认时间点），不启动。
2. 终端 E 先当了一阵执行主控（E1）后放弃；终端 I 成为构思主控；终端 E 再次申请执行主控（E2），批准时上级选 I。
   E2 派 T-1、T-2 两个 worker；T-1 经审查员审查后集成并打分（边界 3、品味 2，各有理由）；T-2 交付后不打分。之后 I 放弃身份。
3. Reflect 页：I（已结束）在第一层，E2（运行中）在它下面，T-1、T-2 的 worker 与审查员在 E2 下面；E1（已结束、没有
   下属）也列出来；T-1 的 worker 上显示结果、两项分数与理由，与门禁的打分记录一致，T-2 的 worker 没有分数。
4. 在 Reflect 页开启定期复盘，把执行者改成 Claude Code · claude-haiku-5-5 · low 并保存；注入时钟到下一个时间点，启动一次，
   用的是刚选的模型与强度。
5. 在 Reflect 页选模型与强度点“立即复盘”，报告进 findings/，建议出现在页面上。原“复盘”页签不再出现。
6. 后台重启后，保存过的周期设置不变（出厂默认只在设置表为空时写入）。
（审查 01 后补充：E2 还给 T-2 挂了一个监视器，挂在 E2 下；T-3 由桌面的操作员身份派出、没有主控，进“未归属”。）

失败方式（先列再写）：
1. 默认开启，到点自己启动。
2. 已结束的主控或会话不列。
3. 从同一终端先后拿到的两个角色混为一个，下属挂到已结束的那个（E1）上。
4. 打分挂错会话（挂到没打分的 worker 或审查员上），或数字、理由与门禁记录不一致。
5. 页面选的执行者没存，定期复盘用的还是旧的。
6. 还有“复盘”页签，或复盘入口不在 Reflect 页。
--revision 在该版本源码上跑（修前没有 Reflect 页）；--mutant 跑已知坏实现。
"""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import shutil
import socket
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory  # noqa: E402

FILES = {'T-1': 'a.txt', 'T-2': 'b.txt', 'T-3': 'c.txt'}
MODEL = 'claude-haiku-5-5'
SCORE = dict(result='通过', boundary_discipline=3, boundary_reason='只改了 a.txt', engineering_taste=2, engineering_reason='提交信息偏简单', notes='T-137 fixture')
REPORT = '# 复盘\n\nT-137 夹具复盘报告。\n'
SUGGESTION = 'T-137：审查前先跑一遍完成条件'
SET_VALUE = ("var set=(el,v)=>{const proto=el.tagName==='SELECT'?HTMLSelectElement.prototype:el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;"
             "Object.getOwnPropertyDescriptor(proto,'value').set.call(el,v);el.dispatchEvent(new Event(el.tagName==='SELECT'?'change':'input',{bubbles:true}));};")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['schedule-on-by-default', 'ended-not-listed', 'role-by-terminal-only', 'score-on-attempt', 'defaults-overwrite-saved'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[], observed={})
    patches = {
        'schedule-on-by-default': [('src/retrospective.ts', 'const defaults = { enabled: false,', 'const defaults = { enabled: true,')],
        # Only what is still running is listed.
        'ended-not-listed': [('src/reflect.ts', "const held = roleRequests.filter(row => row.project === project && row.confirmed_at);",
                              "const held = roleRequests.filter(row => row.project === project && row.confirmed_at && row.state !== 'ended');")],
        # A session under a terminal goes to the first role that terminal ever held.
        'role-by-terminal-only': [('src/reflect.ts', "const roleAt = (launch: string, time: string) => held.findLast(row => row.launch === launch && row.confirmed_at! <= time &&",
                                   "const roleAt = (launch: string, time: string) => held.find(row => row.launch === launch || row.confirmed_at! <= time &&")],
        # Review 01: the factory default written over the saved schedule on every start.
        'defaults-overwrite-saved': [('src/retrospective.ts', "db.prepare('INSERT INTO retrospective_schedule(data) VALUES (?)').run(JSON.stringify({ ...defaults, effective_from: new Date().toISOString() }));",
                                      "{}\n    db.prepare('INSERT INTO retrospective_schedule(data) VALUES (?)').run(JSON.stringify({ ...defaults, effective_from: new Date().toISOString() }));")],
        # The score attached by attempt to every session of it, the reviewer's included.
        'score-on-attempt': [('src/reflect.ts', "score: record.role === 'worker' ? scores.get(record.id) ?? null : null });",
                              "score: [...scores.values()].find(score => score.attempt === record.attempt) ?? null });")],
    }.get(args.mutant, [])

    def plan(body):
        text = prompt_text(body)
        dump = json.dumps(body, ensure_ascii=False)
        out = re.search(r'只能写 (/\S+) 这个目录', dump)
        if out and '做一次复盘' in dump:
            out = out.group(1)
            return 'retro:' + out, [('Write', dict(file_path=f'{out}/report.md', content=REPORT)),
                                    ('Write', dict(file_path=f'{out}/suggestions.json', content=json.dumps(
                                        [dict(title=SUGGESTION, body='T-1 的审查发现完成条件没先跑。', kind='role-card')], ensure_ascii=False)))], '复盘写完了。'
        if '角色卡：monitor' in text:
            return 'monitor', [('Bash', dict(command='git log --oneline -3', description='observe'))], '观察完毕：没有发现问题。'
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
        return 'worker:' + task, [('Write', dict(file_path=f'{cwd}/{FILES[task]}', content='x\n')),
                                  ('Bash', dict(command=f'git add {FILES[task]}', description='stage')),
                                  ('Bash', dict(command=f'git commit -q -m {quote(task + " fixture change")}', description='commit')),
                                  ('Bash', dict(command=submit, description='submit'))], '已交付。'

    fixture = Fixture('t137-', plan, revision=args.revision, patches=patches)
    # The user's project is one they already trust in their own Claude.
    (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
        'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
    report['fixture'] = str(fixture.dir)
    electron = None

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

    def ask(identity, role, parent=None):
        """A role request from a terminal, decided by the operator (with an executor's parent) and confirmed."""
        asker = socket.socket(socket.AF_UNIX)
        asker.connect(str(fixture.state / 'control.sock'))
        asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role=role, wait_seconds=60),
                                       identity=identity)) + '\n').encode())
        pending = fixture.wait('角色申请出现', lambda: [r for r in fixture.request('sidebar_snapshot').get('role_requests', []) if r['launch'] == identity['launch']], 20)
        decided = fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True,
                                  **({'parent_launch': parent} if parent else {}))
        assert decided['ok'], decided
        response = b''
        while b'\n' not in response:
            response += asker.recv(65536)
        asker.close()
        granted = json.loads(response.split(b'\n', 1)[0])
        assert fixture.request('role_request_confirm', identity, role_request=granted['role_request']['id'])['ok']
        return granted['role_request']['id']

    def terminal_identity():
        launch = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        token = fixture.out / f'token-{launch}.txt'
        assert fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()),
                               data=f'print -r -- $A2A_TERMINAL_TOKEN > {token}\r')['ok']
        fixture.wait('终端写出令牌', lambda: token.exists() and token.read_text().strip(), 30)
        return dict(kind='terminal', launch=launch, token=token.read_text().strip())

    def next_monday_nine(after):
        slot = after.replace(hour=9, minute=0, second=0, microsecond=0)
        slot += timedelta(days=(0 - slot.weekday()) % 7)
        return slot if slot > after else slot + timedelta(days=7)

    def tick(when):
        ticked = fixture.request('retrospective_tick', fixture.operator, now=when.astimezone().isoformat())
        assert ticked.get('ok'), ticked
        return ticked

    def tree():
        return electron.evaluate("[...document.querySelectorAll('.reflect-node')].map(n=>({id:n.dataset.reflectNode,parent:n.dataset.reflectParent,"
                                 "level:n.dataset.reflectLevel,state:n.dataset.reflectState,launch:n.dataset.reflectLaunch,"
                                 "role:n.querySelector('strong').textContent,text:n.innerText,"
                                 "score:n.querySelector('.reflect-score')&&{result:n.querySelector('.reflect-score').dataset.scoreResult,"
                                 "boundary:n.querySelector('[data-score-boundary]')?.textContent,taste:n.querySelector('[data-score-taste]')?.textContent}}))")

    try:
        (fixture.repo / 'findings').mkdir(parents=True)
        fixture.start(args.claude, {'README.md': 'demo\n', 'findings/README.md': '发现\n',
                                    **{f'check_{t}.py': f'import pathlib, sys\nsys.exit(0 if pathlib.Path("{f}").is_file() else 1)\n' for t, f in FILES.items()}})
        # 1: off by default; the default slot passes without a run.
        start = datetime.now().astimezone()
        slot = next_monday_nine(start)
        report['observed']['default_schedule'] = listing()['schedule']
        off = tick(slot)
        check('schedule_off_by_default', listing()['schedule']['enabled'] is False and off['started'] == [] and not listing()['runs'],
              dict(schedule=listing()['schedule'], tick=off))

        # 2: E held the executor role once (E1) and gave it back; I becomes ideation; E asks again (E2) under I.
        executor = fixture.terminal
        e1 = next(r['id'] for r in fixture.request('terminal_whoami', executor)['role_requests'] if r['state'] == 'approved')
        assert fixture.request('role_release', executor)['ok']
        ideation = terminal_identity()
        i1 = ask(ideation, 'ideation')
        e2 = ask(executor, 'executor', parent=ideation['launch'])
        for task, name in FILES.items():
            fixture.card(task, name, f'check_{task}.py')
        workers = {}
        for task in FILES:
            # T-3 is dispatched from the desktop's operator identity, with no controller: an unassigned session.
            dispatched = fixture.request('dispatch', executor if task != 'T-3' else fixture.operator, task=task, runtimeMode='workspace-write')
            assert dispatched.get('ok'), dispatched
            workers[task] = dispatched['attempt']['runtime_identity']['launch']
        instructions = fixture.out / 'monitor.txt'
        instructions.write_text('看一下项目最近的提交，写一句观察。\n', encoding='utf-8')
        attached = fixture.request('attach', executor, task='T-2', role='monitor', instructions=str(instructions), cli='Claude Code', model=MODEL, effort='low')
        assert attached.get('ok'), attached
        for task in FILES:
            fixture.wait(f'{task} 交付', lambda: status(task)['state'] == 'submitted', 180)
        verified = fixture.request('verify', executor, task='T-1')
        assert verified.get('ok'), verified
        fixture.wait('T-1 审查通过', lambda: (lambda s: s['state'] == 'verified' and s.get('review', {}).get('state') == 'passed')(status('T-1')), 240)
        fixture.wait('T-1 审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in gate_events('T-1')), 60)
        score_file = fixture.out / 'score-T-1.json'
        score_file.write_text(json.dumps(SCORE, ensure_ascii=False), encoding='utf-8')
        integrated = fixture.request('integrate', executor, task='T-1', score_file=str(score_file))
        assert integrated.get('ok'), integrated
        assert fixture.request('role_release', ideation)['ok']
        recorded = [e['details'] for e in gate_events('T-1') if e['type'] == 'score_recorded']
        report['observed']['score_recorded'] = recorded
        assert len(recorded) == 1, recorded

        # 3: the Reflect page.
        electron = Electron(fixture, 't137-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('Reflect 页签', "!!document.querySelector('[data-reflect-tab]')", 20)
        tabs = electron.evaluate("[...document.querySelectorAll('.task-header nav button, [data-reflect-tab]')].map(b=>b.textContent)")
        report['observed']['tabs'] = tabs
        check('reflect_tab_replaces_retrospective_tab', 'Reflect' in tabs and '复盘' not in tabs and
              not electron.evaluate("!!document.querySelector('[data-retrospective-tab]')"), tabs)
        electron.evaluate("document.querySelector('[data-reflect-tab]').click()")
        electron.until('会话树', f"document.querySelectorAll('.reflect-node').length >= 8", 30)
        nodes = tree()
        report['observed']['tree'] = nodes
        electron.screenshot(fixture.out / '01-reflect-tree.png')
        by = {n['id']: n for n in nodes}
        reviewers = [n for n in nodes if n['role'] == '审查员']
        monitors = [n for n in nodes if n['role'] == '监视器']
        loose = electron.evaluate("[...document.querySelectorAll('.reflect-loose .reflect-node')].map(n=>n.dataset.reflectNode)")
        report['observed']['loose'] = loose
        check('ended_controllers_listed', by.get(i1, {}).get('state') == 'ended' and by[i1]['level'] == '0' and by[i1]['role'] == '构思主控' and
              by.get(e1, {}).get('state') == 'ended' and by[e1]['role'] == '执行主控', nodes)
        check('executor_under_ended_ideation', by.get(e2, {}).get('parent') == i1 and by[e2]['level'] == '1' and by[e2]['state'] == 'running', nodes)
        check('sessions_under_the_role_held_when_they_started', all(by.get(workers[t], {}).get('parent') == e2 and by[workers[t]]['level'] == '2' for t in ('T-1', 'T-2')) and
              len(reviewers) == 1 and reviewers[0]['parent'] == e2 and reviewers[0]['state'] == 'ended' and
              len(monitors) == 1 and monitors[0]['parent'] == e2 and monitors[0]['level'] == '2' and
              not any(n['parent'] == e1 for n in nodes), nodes)
        check('score_on_scored_worker_only', by[workers['T-1']]['score'] == dict(result='通过', boundary=f"3（{SCORE['boundary_reason']}）", taste=f"2（{SCORE['engineering_reason']}）") and
              recorded[0]['data']['boundary_discipline'] == 3 and recorded[0]['data']['engineering_taste'] == 2 and recorded[0]['launch_id'] == workers['T-1'] and
              by[workers['T-2']]['score'] is None and reviewers[0]['score'] is None, nodes)

        check('session_without_controller_unassigned', by.get(workers['T-3'], {}).get('parent') == '' and loose == [workers['T-3']], dict(loose=loose, nodes=nodes))

        # 4: switch the schedule on and pick who runs it, on the Reflect page.
        electron.until('周期开关', "document.querySelector('[data-schedule-enabled]')?.checked === false", 20)
        electron.evaluate("document.querySelector('[data-schedule-enabled]').click()")
        electron.until('周期已开', "document.querySelector('[data-schedule-enabled]')?.checked === true", 20)
        electron.evaluate(SET_VALUE + "var f=document.querySelector('[data-schedule-runner]');"
                          f"set([...f.querySelectorAll('label')].find(l=>l.textContent.startsWith('模型')).querySelector('input'),{json.dumps(MODEL)});"
                          "set([...f.querySelectorAll('label')].find(l=>l.textContent.startsWith('思考强度')).querySelector('input'),'low');")
        electron.until('保存可点', "!document.querySelector('[data-schedule-runner] button').disabled", 10)
        electron.evaluate("document.querySelector('[data-schedule-runner] button').click()")
        fixture.wait('执行者已存', lambda: (lambda s: s['model'] == MODEL and s['effort'] == 'low')(listing()['schedule']), 20)
        electron.screenshot(fixture.out / '02-schedule.png')
        schedule = listing()['schedule']
        fired = tick(next_monday_nine(datetime.now().astimezone()))
        report['observed']['schedule'] = dict(saved=schedule, fired=fired['started'])
        check('schedule_on_fires_with_chosen_runner', schedule['enabled'] is True and len(fired['started']) == 1 and fired['started'][0]['trigger'] == 'schedule' and
              fired['started'][0]['cli'] == 'Claude Code' and fired['started'][0]['model'] == MODEL and fired['started'][0]['effort'] == 'low', report['observed']['schedule'])
        scheduled = fired['started'][0]
        fixture.wait('定期复盘导入', lambda: any(e['type'] == 'imported' for r in listing()['runs'] if r['id'] == scheduled['id'] for e in r['events']), 180)

        # 5: a retrospective now, from the Reflect page.
        electron.evaluate(SET_VALUE + "var p=document.querySelector('.retrospective-page');"
                          f"set([...p.querySelectorAll('label')].find(l=>l.textContent.startsWith('模型')).querySelector('input'),{json.dumps(MODEL)});"
                          "set([...p.querySelectorAll('label')].find(l=>l.textContent.startsWith('思考强度')).querySelector('input'),'low');")
        before = {r['id'] for r in listing()['runs']}
        electron.evaluate("document.querySelector('[data-start-retrospective]').click()")
        manual = fixture.wait('立即复盘开始', lambda: [r for r in listing()['runs'] if r['id'] not in before], 30)[0]
        fixture.wait('立即复盘导入', lambda: any(e['type'] == 'imported' for r in listing()['runs'] if r['id'] == manual['id'] for e in r['events']), 180)
        imported = next(e for r in listing()['runs'] if r['id'] == manual['id'] for e in r['events'] if e['type'] == 'imported')
        report['observed']['manual'] = dict(run={k: manual[k] for k in ('trigger', 'cli', 'model', 'effort')}, imported=imported['data'])
        electron.until('建议出现', f"[...document.querySelectorAll('.suggestion-card')].some(c=>c.textContent.includes({json.dumps(SUGGESTION)}))", 30)
        electron.screenshot(fixture.out / '03-retrospective.png')
        report_path = Path(imported['data']['report'])
        check('retrospective_from_reflect_page', manual['trigger'] == 'manual' and manual['model'] == MODEL and manual['effort'] == 'low' and
              report_path.parent == fixture.repo / 'findings' and report_path.read_text(encoding='utf-8') == REPORT, report['observed']['manual'])

        # 6: a restart keeps the saved schedule; the factory default only fills an empty table.
        fixture.run_cli('daemon_stop')
        fixture.run_cli('daemon_start', '--launch-config', str(fixture.dir / 'launch-config.json'))
        fixture.wait('后台恢复结束', lambda: fixture.request('pane_layout').get('recovering') is False, 30)
        kept = listing()['schedule']
        report['observed']['schedule_after_restart'] = kept
        check('saved_schedule_survives_restart', kept['enabled'] is True and kept['model'] == MODEL and kept['effort'] == 'low', kept)
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
