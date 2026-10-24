"""T-162：真实后台、项目终端与 Electron；此脚本不启动原生模型。

失败方式（先列再写）：
1. 用户点击批准或拒绝后，统一 user_inputs 表与记录页缺条目，或无法关联申请和决定事件。
2. 同角色其他申请的自动拒绝被误记为用户拒绝；重复决定失败却增加输入记录。
3. 无原生回合计数证据的主控被显示为 0；模型汇总把未知会话也加成已知的零。
4. 逐会话行没有计数来源，页面没有说明覆盖范围，用户误把它当全局总回合。
5. 输入记录写入失败后角色决定仍生效；批准过期又被记成一次用户拒绝。

期望来自 T-162 与主控 #30：两次用户点击产生两条输入，自动拒绝不产生用户输入；
没有回合事实的项目终端主控为未知/未覆盖。事件序号仅用于核对关联，不作为期望计数。
--revision 在指定版本运行同一场景；--mutant 在隔离源码中运行已知坏实现。
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import sqlite3
import sys
import traceback
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['unknown-as-zero', 'decision-unrecorded', 'non-atomic-decision'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  checks=[], observed={}, real_model_turns=0)
    fixture = electron = None
    askers = []

    def check(name, condition, detail=None):
        report['checks'].append(dict(name=name, status='PASS' if condition else 'FAIL', detail=detail))

    try:
        patches = {
            'unknown-as-zero': [('src/metrics.ts', 'turns: facts?.turns ?? null,', 'turns: facts?.turns ?? 0,')],
            'decision-unrecorded': [('src/roleRequests.ts',
                'this.store.db.prepare("INSERT INTO user_inputs(id,task,message,data) VALUES (?,NULL,NULL,?)").run(inputId, JSON.stringify(input));', 'void input;')],
            'non-atomic-decision': [('src/roleRequests.ts', 'this.store.db.exec("BEGIN IMMEDIATE");', ''),
                                    ('src/roleRequests.ts', 'this.store.db.exec("COMMIT");', '')],
        }.get(args.mutant, [])
        fixture = Fixture('t162-', lambda body: (_ for _ in ()).throw(AssertionError('本场景禁止模型请求')),
                          revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        # The helper opens a project and approves an executor without starting the supplied executable.
        fixture.start('/usr/bin/true', {'README.md': '# T-162 isolated project\n'})
        electron = Electron(fixture, 't162-' + uuid.uuid4().hex[:12])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")

        def terminal(name):
            launch = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
            opened = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
            assert opened['ok'], opened
            token = fixture.out / (name + '-token.txt')
            sent = fixture.request('window_input', opened['identity'], sequence=1, request_id=str(uuid.uuid4()),
                                   data=f'print -r -- $A2A_TERMINAL_TOKEN > {token}\r')
            assert sent['ok'], sent
            fixture.wait('隔离终端就绪', lambda: token.exists() and token.read_text(encoding='utf-8').strip(), 30)
            return dict(kind='terminal', launch=launch, token=token.read_text(encoding='utf-8').strip())

        def ask(identity):
            connection = socket.socket(socket.AF_UNIX)
            connection.settimeout(30)
            connection.connect(str(fixture.state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), identity=identity,
                input=dict(command='role_request', role='ideation', cli='claude', wait_seconds=180))) + '\n').encode())
            askers.append(connection)
            request = fixture.wait('申请出现', lambda: next((row for row in fixture.request('sidebar_snapshot').get('role_requests', [])
                                  if row['launch'] == identity['launch']), None), 20)
            return request['id'], connection

        def reply(connection):
            response = b''
            while b'\n' not in response:
                part = connection.recv(65536)
                assert part, '申请连接在回执前断开'
                response += part
            connection.close()
            askers.remove(connection)
            return json.loads(response.split(b'\n', 1)[0])

        def decide(request, approved):
            label = '批准' if approved else '拒绝'
            electron.until(label, f"(()=>{{const b=[...document.querySelectorAll('[data-role-request=\"{request}\"] button')]"
                           f".find(b=>b.textContent==={json.dumps(label)});if(!b||b.disabled)return false;b.click();return true}})()", 30)

        winner, rival = terminal('winner'), terminal('rival')
        approved, first = ask(winner)
        automatic, second = ask(rival)
        decide(approved, True)
        granted = reply(first)
        assert granted.get('ok'), granted
        confirmed = fixture.request('role_request_confirm', winner, role_request=approved)
        assert confirmed.get('ok'), confirmed
        refused = reply(second)
        assert refused.get('ok') is False and refused['role_request']['state'] == 'rejected', refused
        released = fixture.request('role_release', winner)
        assert released.get('ok'), released
        denied, third = ask(winner)
        decide(denied, False)
        refusal = reply(third)
        assert refusal.get('ok') is False and refusal['role_request']['state'] == 'rejected', refusal
        duplicate = fixture.request('role_request_decide', fixture.operator, role_request=denied, approved=False)
        assert duplicate.get('ok') is False, duplicate

        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
            stored = [json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
            decisions = {json.loads(data)['role_request']: seq for seq, data in db.execute(
                "SELECT seq,data FROM orchestration_events WHERE type='role_request_decided' ORDER BY seq")}
        # The target is an existing contract field. It identifies the role request that the user answered.
        selected = [row for row in stored if row['target'].get('request') in (approved, denied, automatic)]
        report['observed']['stored_role_inputs'] = selected
        report['observed']['decisions'] = decisions
        check('two_explicit_decisions_are_user_inputs',
              sorted((row['target']['request'], row['form']) for row in selected) == sorted([(approved, 'approval'), (denied, 'denial')]), selected)
        check('decision_event_is_linked', len(selected) == 2 and all(
            row['source_ref'].get('source_sequence') == decisions[row['target']['request']] and
            row['certainty'] == 'observed' and row['target']['project'] == 'demo' and
            row['target']['task'] is None and row['target']['attempt'] is None for row in selected), selected)

        electron.until('记录页签', "!!document.querySelector('[data-records-tab]')")
        electron.evaluate("document.querySelector('[data-records-tab]').click()")
        electron.until('记录页读取结束', "!!document.querySelector('.user-input-page') && !document.querySelector('.user-input-page [role=status]')")
        rows = electron.evaluate("[...document.querySelectorAll('.user-input-page tr[data-input-id]')].map(r=>({id:r.dataset.inputId,text:r.innerText}))")
        report['observed']['record_rows'] = rows
        check('record_page_shows_decisions_and_event_sources', len(selected) == 2 and all(
            any(shown['id'] == row['id'] and row['target']['request'] in shown['text'] and
                str(decisions[row['target']['request']]) in shown['text'] for shown in rows) for row in selected), rows)
        electron.screenshot(fixture.out / '01-role-records.png')

        result = fixture.request('metrics', fixture.operator, project='demo')
        assert result.get('ok'), result
        report['observed']['metrics'] = result
        session = next(row for row in result['model_use']['sessions'] if row['launch'] == winner['launch'])
        check('controller_without_native_count_is_unknown', session.get('turns') is None, session)
        check('unknown_is_not_summed_as_zero', all(row.get('turns') is None for row in result['model_use']['by_model']), result['model_use']['by_model'])
        electron.evaluate("document.querySelector('[data-metrics-tab]').click()")
        electron.until('指标会话行', f"!!document.querySelector('[data-launch=\"{winner['launch']}\"]')")
        shown = electron.evaluate(f"document.querySelector('[data-launch=\"{winner['launch']}\"]').innerText")
        text = electron.evaluate("document.querySelector('.metrics-page').innerText")
        report['observed']['metric_row'] = shown
        report['observed']['metric_text'] = text
        check('metrics_page_labels_unknown_and_source', ('未知' in shown or '未覆盖' in shown) and '来源' in text, shown)
        check('metrics_page_explains_coverage', '全局' in text and '复盘' in text and '项目终端' in text, text)
        electron.screenshot(fixture.out / '02-metrics-unknown.png')

        # Independent event fixtures exercise the real metrics API and UI for a known zero and two recorded turns.
        # They do not claim that these synthetic sessions ran a CLI or that native-log collection is complete.
        zero_launch, counted_launch = 'fixture-zero-' + uuid.uuid4().hex, 'fixture-counted-' + uuid.uuid4().hex
        nonce = 'sentinel-' + uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        with sqlite3.connect(fixture.state / 'state.sqlite3') as db:
            for launch in (zero_launch, counted_launch):
                record = dict(id=launch, thread=launch, role='worker', project='demo', task=None, attempt=None,
                              session=None, worktree=str(fixture.repo), cli='Claude Code', model_requested='requested-only', created_at=now)
                db.execute('INSERT INTO launch_records(id,task,attempt,data) VALUES (?,NULL,NULL,?)', (launch, json.dumps(record)))
            sources = []
            for launch, time, prompt in [(zero_launch, '2099-01-01T00:00:00.000Z', 'outside-' + nonce),
                                          (counted_launch, now, 'first-' + nonce), (counted_launch, now, 'second-' + nonce)]:
                cursor = db.execute('INSERT INTO orchestration_events(time,type,launch,task,attempt,data) VALUES (?,\'native_turn_facts\',?,NULL,NULL,?)',
                                    (time, launch, json.dumps(dict(model='served-fixture', effort='high', prompt_id=prompt))))
                sources.append(dict(sequence=cursor.lastrowid, launch=launch, prompt=prompt))
        end = electron.evaluate('(()=>{const d=new Date();return new Date(d.getFullYear(),d.getMonth(),d.getDate()+1).toISOString()})()')
        ranged = fixture.request('metrics', fixture.operator, project='demo', until=end)
        counted = {row['launch']: row for row in ranged['model_use']['sessions']}
        check('event_fixtures_distinguish_zero_unknown_and_recorded',
              [counted[zero_launch]['turns'], counted[winner['launch']]['turns'], counted[counted_launch]['turns']] == [0, None, 2], counted)
        electron.evaluate("(()=>{const d=new Date();const value=[d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');"
                          "const el=document.querySelectorAll('.metrics-page input[type=date]')[1];"
                          "Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,value);el.dispatchEvent(new Event('input',{bubbles:true}));})()")
        electron.until('已记录零与两个回合', f"document.querySelector('[data-launch=\"{zero_launch}\"] [data-turn-count]')?.textContent==='0' && "
                       f"document.querySelector('[data-launch=\"{counted_launch}\"] [data-turn-count]')?.textContent==='2'")
        electron.evaluate(f"document.querySelector('[data-launch=\"{counted_launch}\"] summary').click()")
        shown_sources = electron.evaluate(f"document.querySelector('[data-launch=\"{counted_launch}\"]').innerText")
        check('recorded_sources_are_visible_and_replayable', all(
            str(row['sequence']) in shown_sources and row['prompt'] in shown_sources for row in sources if row['launch'] == counted_launch), shown_sources)
        report['observed']['event_fixture_sources'] = sources
        electron.screenshot(fixture.out / '03-metrics-sources.png')

        # A user approval remains an input even if the CLI never confirms it. Expiry is not a second user decision.
        expiring, fourth = ask(winner)
        decide(expiring, True)
        assert reply(fourth).get('ok'), '过期场景没有收到批准'
        fixture.wait('批准过期', lambda: any(row['id'] == expiring for row in
                     fixture.request('sidebar_snapshot').get('unconfirmed_role_requests', [])), 30)
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
            expired_inputs = [json.loads(row[0]) for row in db.execute(
                "SELECT data FROM user_inputs WHERE json_extract(data,'$.target.request')=?", (expiring,))]
        check('expiry_does_not_add_a_user_denial', len(expired_inputs) == 1 and expired_inputs[0]['form'] == 'approval', expired_inputs)

        # Deliberate local storage failure: the request must remain pending, with neither half of the decision committed.
        failed_request, fifth = ask(winner)
        database = fixture.state / 'state.sqlite3'
        with sqlite3.connect(database) as db:
            db.execute("CREATE TRIGGER t162_input_failure BEFORE INSERT ON user_inputs WHEN "
                       f"json_extract(NEW.data,'$.target.request')='{failed_request}' BEGIN SELECT RAISE(ABORT,'t162_storage_failure'); END")
        try:
            failed = fixture.request('role_request_decide', fixture.operator, role_request=failed_request, approved=True)
            with sqlite3.connect(database) as db:
                decided = db.execute("SELECT count(*) FROM orchestration_events WHERE type='role_request_decided' "
                                     "AND json_extract(data,'$.role_request')=?", (failed_request,)).fetchone()[0]
                inputs = db.execute("SELECT count(*) FROM user_inputs WHERE json_extract(data,'$.target.request')=?", (failed_request,)).fetchone()[0]
            pending = any(row['id'] == failed_request for row in fixture.request('sidebar_snapshot').get('role_requests', []))
            check('decision_and_input_roll_back_together', failed.get('ok') is False and decided == 0 and inputs == 0 and pending,
                  dict(response=failed, decisions=decided, inputs=inputs, pending=pending))
        finally:
            with sqlite3.connect(database) as db:
                db.execute('DROP TRIGGER t162_input_failure')
            fifth.close()
            askers.remove(fifth)

        assert fixture.api.requests == 0, '本场景不能消耗真实模型回合'
        report['status'] = 'PASS' if all(row['status'] == 'PASS' for row in report['checks']) else 'NO_GO'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        if electron:
            try:
                electron.screenshot(fixture.out / 'failure.png')
            except BaseException as shot_error:
                report['screenshot_error'] = str(shot_error)
    finally:
        for connection in askers:
            connection.close()
        try:
            if electron:
                electron.stop()
            if fixture:
                fixture.stop()
        except BaseException as error:
            report['cleanup_error'] = str(error)
            report['status'] = 'INCOMPLETE'
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status=report['status'], summary=str(args.summary)), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
