"""T-216 contract test: real daemon, gates, approved project terminal and interactive Claude Code.
Both controller and worker use a local scripted Messages endpoint; no vendor model is called.

Failure modes (specified before assertions):
1. Plain/blocking reports never reach the executor, lose their original text/id, or arrive twice.
2. Blocking immediately counts as waiting for the user; inbox prompts become user inputs.
3. Controller answers do not reach the reporting worker, lose actor provenance or still wait for the user.
4. Controller close of blocking is rejected, loses reason/actor, or cannot be reopened by the user.
5. Escalation has no reason/actor, does not wait for the user, or the user's reply loses reply_to.
6. Without an executor the issue disappears/fails delivery instead of queuing; timeout is not 15 minutes.
7. The issue UI hides the processor or escalation reason.

The only source patch supplies the existing gate clock seam from a fixture file, equally on old/new code.
--revision runs this same scenario on an isolated historical source tree. Evidence is never overwritten.
"""
import argparse
import json
import shutil
import sys
import time
import uuid
from pathlib import Path

from scripted_claude import Electron, Fixture, gate_line, prompt_text, quote


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--gui', action='store_true')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, checks=[])
    titles = ['执行顺序确认', '必须先确认的阻塞', '重复发现的阻塞']
    bodies = ['先做卡内哪一步？保留这段完整原文。', '当前步骤需要主控确认后继续。', '主控已有证据，可关闭并写理由。']

    def plan(body):
        text = prompt_text(body)
        if 'T216_CONTROLLER' in text:
            return 'controller', [('Bash', dict(command='a2a request executor', description='request executor role'))], '已收到；等待下一条收件箱通知。'
        assert '显式交付' in text
        steps = [('Bash', dict(command=gate_line(body, f"'issue' '--task' '{{task}}' '--title' {quote(title)} '--body' {quote(content)} '--blocking' '{str(i > 0).lower()}'"), description=title))
                 for i, (title, content) in enumerate(zip(titles, bodies))]
        if "'demo+T-2'" in text:
            steps = steps[:1]
        return 'worker', steps, '已上报；等待答复。'

    fixture = Fixture('t216-', plan, revision=args.revision, patches=[('src/daemon.ts',
        'new A2AGates(root, panes)',
        'new A2AGates(root, panes, () => Date.now() + Number(readFileSync(join(root, "clock-offset"), "utf8")))')])
    (fixture.state / 'clock-offset').write_text('0', encoding='utf-8')
    report['fixture'] = str(fixture.dir)
    report['clock_seam'] = 'gate constructor now(); offset in fixture state/clock-offset, milliseconds'
    electron = None

    def check(name, condition, detail=None):
        report['checks'].append(dict(name=name, passed=bool(condition), detail=detail))
        assert condition, f'{name}: {detail}'

    def issues(task='T-1'):
        result = fixture.request('issues', fixture.operator, task=task)
        assert result['ok'], result
        return result

    def events():
        return fixture.request('orchestration_events')['events']

    def received(issue):
        marker = issue['id']
        return [b for b in fixture.api.bodies if b['key'] == 'controller' and
                any(marker in json.dumps(m, ensure_ascii=False) for m in b['messages'] if m['role'] == 'user')]

    try:
        fixture.start(args.claude, {'README.md': 'demo\n', 'check.py': 'raise SystemExit(0)\n'})
        fixture.card('T-1', 'hello.txt', 'check.py')
        fixture.card('T-2', 'other.txt', 'check.py')
        assert fixture.request('role_release', fixture.terminal)['ok']
        config = fixture.home / '.claude.json'
        value = json.loads(config.read_text(encoding='utf-8'))
        value.update(hasSeenAutoDefaultNudge=True, projects={str(fixture.repo): {'hasTrustDialogAccepted': True}})
        config.write_text(json.dumps(value), encoding='utf-8')
        window = fixture.request('window_open', fixture.operator, launch=fixture.terminal_launch, project='demo')
        command = (f'claude --model claude-haiku-5-5 --effort low --permission-mode dontAsk --allowedTools Bash '
                   f'--session-id {uuid.uuid4()} T216_CONTROLLER')
        report['controller_command'] = command
        assert fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()), data=command + '\r')['ok']
        pending = fixture.wait('原生主控申请角色', lambda: fixture.request('sidebar_snapshot').get('role_requests'), 90)
        assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)['ok']
        fixture.wait('主控角色生效', lambda: fixture.request('terminal_whoami', fixture.terminal).get('role') == 'executor', 30)
        fixture.wait('主控结束初始回合', lambda: '已收到；等待下一条收件箱通知。' in (fixture.state / 'traces' / fixture.terminal_launch / 'pty.raw').read_text(encoding='utf-8', errors='replace'), 45)
        started = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert started['ok'], started
        views = fixture.wait('三条问题上报', lambda: (lambda r: r['issues'] if len(r['issues']) == 3 else None)(issues()), 150)
        report['initial'] = views
        # Observe both requested red signals before failing; absent delivery has a finite observation window.
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not all(received(v['issue']) for v in views):
            assert not fixture.api.error, fixture.api.error
            time.sleep(.2)
        initial_states_ok = all(v['state'] == '待判断' for v in views)
        pushed = all(received(v['issue']) for v in views)
        report['red_signals'] = dict(blocking_stays_in_triage=initial_states_ok, controller_received_all=pushed)
        check('report_push_and_blocking_triage', initial_states_ok and pushed, report['red_signals'])
        for v in views:
            issue = v['issue']
            dispatches = [e['data'] for e in events() if e['type'] == 'dispatch_queued' and e['data'].get('inbox_entry') == issue['id']]
            check('one_complete_inbox_dispatch_' + str(issue['number']), len(dispatches) == 1 and dispatches[0]['source'] == 'inbox' and
                  all(s in dispatches[0]['text'] for s in [issue['id'], str(issue['number']), issue['title'], issue['body'], issue['from'], 'answer_issue', 'disposition', 'needs-user']) and
                  ('阻塞：是' if issue['blocking'] else '阻塞：否') in dispatches[0]['text'], dispatches)
        held = fixture.request('terminal_whoami', fixture.terminal)['role_requests'][-1]
        def native_submissions():
            native_rows = []
            for path in (Path(held['native_home']) / 'projects').rglob(held['native_session'] + '.jsonl'):
                for line in path.read_text(encoding='utf-8').split('\n')[:-1]:
                    if not line:
                        continue
                    row = json.loads(line)
                    content = row.get('message', {}).get('content')
                    if row.get('type') == 'user' and row.get('isSidechain') is False and row.get('sessionId') == held['native_session'] and isinstance(content, str):
                        native_rows.append(dict(file=str(path), uuid=row.get('uuid'), prompt_id=row.get('promptId'), text=content))
            return native_rows
        fixture.wait('原生记录已落盘', lambda: all(any('\n收件箱 issue ' + v['issue']['id'] + '\n' in row['text'] for row in native_submissions()) for v in views), 30)
        native_rows = native_submissions()
        report['controller_native_submissions'] = native_rows
        for v in views:
            actual = [row for row in native_rows if '\n收件箱 issue ' + v['issue']['id'] + '\n' in row['text']]
            check('native_actual_once_' + str(v['issue']['number']), len(actual) == 1, actual)
        all_inputs = fixture.request('user_input_records', fixture.operator, project='demo')['records']
        check('inbox_is_not_user_input', not any(v['issue']['id'] in json.dumps(i, ensure_ascii=False) for v in views for i in all_inputs), all_inputs)
        plain, blocking, closing = [next(v for v in views if v['issue']['title'] == title) for title in titles]
        answer_text = '按任务卡中的既定顺序执行。'
        answered = fixture.request('answer_issue', fixture.terminal, task='T-1', issue=plain['issue']['id'], answer=answer_text)
        assert answered['ok'], answered
        fixture.wait('worker 收到主控答复', lambda: any(b['key'] == 'worker' and '主控答复：' + answer_text in json.dumps(b, ensure_ascii=False) for b in fixture.api.bodies), 90)
        view = next(v for v in issues()['issues'] if v['issue']['id'] == plain['issue']['id'])
        check('controller_answer_provenance', view['state'] == '主控已答' and view['answer']['from'] == 'executor' and not view['answer'].get('input_id') and
              any(r.startswith('role-request:') for r in view['answer']['refs']), view)
        refused = fixture.request('disposition', fixture.terminal, task='T-1', issue=blocking['issue']['id'], action='needs-user')
        check('escalation_requires_reason', not refused['ok'] and refused['error'] == 'needs_user_requires_reason', refused)
        reason = '涉及验收条件变更，交给用户决定。'
        forwarded = fixture.request('disposition', fixture.terminal, task='T-1', issue=blocking['issue']['id'], action='needs-user', reason=reason)
        assert forwarded['ok'], forwarded
        view = next(v for v in forwarded['issues'] if v['issue']['id'] == blocking['issue']['id'])
        check('escalation_waits_with_actor_reason', view['state'] == '等你决定' and view['disposition']['from'] == 'executor' and view['disposition']['reason'] == reason, view)
        closed = fixture.request('disposition', fixture.terminal, task='T-1', issue=closing['issue']['id'], action='close', reason='已核对，是重复发现', basis='任务卡与现有记录')
        assert closed['ok'], closed
        view = next(v for v in closed['issues'] if v['issue']['id'] == closing['issue']['id'])
        check('controller_closes_blocking_with_actor', view['state'] == '已关闭' and view['disposition']['from'] == 'executor' and view['disposition']['reason'] == '已核对，是重复发现', view)
        if args.gui:
            electron = Electron(fixture, 't216-' + uuid.uuid4().hex[:10])
            electron.until('项目出现', '!!document.querySelector(\'[data-project-id="demo"]\')')
            electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
            electron.until('问题页签', '!!document.querySelector("[data-issues-tab]")')
            electron.evaluate('document.querySelector("[data-issues-tab]").click()')
            electron.until('处理人显示', 'document.querySelector(".issues-page")?.innerText.includes("主控已答") && document.querySelector(".issues-page")?.innerText.includes("主控已关")')
            text = electron.evaluate('document.querySelector(".issues-page").innerText')
            check('panel_processor_and_escalation_reason', reason in text and '交给你决定' in text and 'executor' in text, text)
            electron.screenshot(fixture.out / 'processor.png')
        user_answer = fixture.request('answer_issue', fixture.operator, task='T-1', issue=blocking['issue']['id'], answer='用户确认：保持当前验收条件。')
        assert user_answer['ok'], user_answer
        check('user_reply_is_user_input', any(i['reply_to'] == blocking['issue']['id'] and i['form'] == 'answer' for i in user_answer['user_inputs']), user_answer['user_inputs'])
        reopened = fixture.request('disposition', fixture.operator, task='T-1', issue=closing['issue']['id'], action='reopen')
        check('user_can_reopen_closed_issue', reopened['ok'] and any(v['issue']['id'] == closing['issue']['id'] and v['state'] == '等你决定' for v in reopened['issues']), reopened.get('error'))
        assert fixture.request('role_release', fixture.terminal)['ok']
        orphan = fixture.request('dispatch', fixture.operator, task='T-2', runtimeMode='workspace-write')
        assert orphan['ok'], orphan
        orphan_view = fixture.wait('无主控时仍保存问题', lambda: (lambda r: r['issues'][0] if r['issues'] else None)(issues('T-2')), 120)
        delivery = fixture.request('inbox_list', fixture.operator, role='executor')
        rows = delivery.get('entries', [])
        receipt = next((r.get('delivery') for r in rows if r['entry']['id'] == orphan_view['issue']['id']), None)
        check('no_controller_queues_report', orphan_view['state'] == '待判断' and receipt and receipt['state'] == 'pending' and receipt['reason'] == 'role_session_missing', receipt)
        # Give elapsed time explicitly through the existing clock dependency, without changing stored evidence.
        # Account for time since creation; use 14 minutes here to avoid a wall-clock race at the edge.
        (fixture.state / 'clock-offset').write_text('840000', encoding='utf-8')
        check('before_15_minutes_still_triage', issues('T-2')['issues'][0]['state'] == '待判断')
        (fixture.state / 'clock-offset').write_text('901000', encoding='utf-8')
        check('after_15_minutes_waits_for_user', issues('T-2')['issues'][0]['state'] == '等你决定')
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api'] = fixture.api.snapshot()
        raise
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
