"""T-251：worker 的一回合被判“不可信”以后，交付被静默丢下、窗格永远“在回合中”、旧 worker 回收不了、新 worker 派不出去。
真实后台与门禁，worker 是真实 Claude Code（模型换成本地脚本化接口，零真实模型调用）。不开 Electron。

期望来自需求（T-251 票；用户 2026-11-07：“现在这样的问题得修复,而且为什么旧 worker 不回收就派发不了新 worker”）：
场景 cd：worker 在 Bash 里 `cd sub` 后，后面的钩子报的工作目录是工作区的子目录。这仍是本会话：回合结束时交付被受理（submitted），
  这个 worker 没有任何钩子被判为身份不符。前提核对：钩子里确实出现过子目录（否则场景没有触到缺陷）。
场景 compact：回合中途 Claude Code 压缩上下文，发来 source 为 compact 的 SessionStart（形状照 2026-11-07 18:57Z T-249 worker 的真实钩子）。
  这仍是本会话：回合不因此被判不可信，交付照常受理。
场景 untrusted：回合中途进来一个工作区以外的钩子（工作区外的 cwd，经同一个钩子入口），回合确实不可信。门禁仍不受理这一回合的交付
  （不放宽身份核对），但是：回合结束后窗格不再算“在回合中”；执行主控的 status 能看到一条阻塞问题，写明交付没被受理和原因，
  这条问题交给收件箱、发给派发这个 worker 的执行主控（有送达回执）；旧 attempt 能回收，回收后同一任务能派出新 worker。
场景 untrusted-online：同 untrusted，但执行主控是项目终端里真实运行的 Claude Code（照 T-216 的做法经 a2a request 申请并批准），
  这条问题要实际送进它的 CLI（主控收到的消息里有这条问题的编号），送达回执为 delivered。

失败方式（先列再写）：
1. 修前：子目录钩子被判不符，回合不可信，交付搁在队列里，任务停在 claimed，没有任何提醒；窗格一直“在回合中”，回收返回 worker_working。
2. 修过头：工作区以外的钩子也被当成本会话，不可信回合的交付被执行。
3. 不可信回合结束了窗格却还算“在回合中”（回收不了）；或结束了但没有任何地方告诉主控（静默）。
4. 压缩钩子被拒并记成身份不符，污染当前回合。
5. 测试本身：钩子里没出现过子目录、伪造钩子没被判不符，场景就没触到要测的路径——列为前提核对，不满足判 INCOMPLETE 而不是 PASS。
--revision 在该版本源码上跑；--mutant 见 MUTANTS。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
import traceback
import uuid

from scripted_claude import Fixture, prompt_text, quote, working_directory, gate_line

ROOT = Path(__file__).resolve().parents[2]
MUTANTS = {
    # The workspace rule goes back to exact equality.
    'cwd-exact': [('src/questions.ts', "return relative === '' || relative !== '..' && !relative.startsWith('../') && !isAbsolute(relative);",
                   "return relative === '';")],
    # A compact SessionStart is refused again.
    'compact-refused': [('src/panes.ts', 'if (value.source === "compact" && pane.started) {', 'if (false) {')],
    # The untrusted turn's requests are executed after all.
    'untrusted-executes': [('src/panes.ts', 'if (transfer) await transfer(pane, value, true, refusal);',
                            'if (transfer) await transfer(pane, value, true);')],
    # The untrusted turn ends, but nobody is told.
    'no-issue': [('src/daemon.ts', 'if (refusal && pane.record.role === "worker") await gates.turnRefused(',
                  'if (false) await gates.turnRefused(')],
    # The issue is recorded and listed, but never sent to the executor.
    'no-delivery': [('src/gates/core.ts', 'return { id: issueId, delivery: await this.deliverInbox(issue) };',
                     'return { id: issueId, delivery: null };')],
    # The refusal is reported, but the pane stays in its turn.
    'turn-stays-busy': [('src/panes.ts', "pane.state = pane.interrupted || pane.claudeQueuedPrompts?.length ? 'busy' : 'idle';",
                         "pane.state = refusal || pane.interrupted || pane.claudeQueuedPrompts?.length ? 'busy' : 'idle';")],
}
SCENARIOS = ('cd', 'compact', 'untrusted', 'untrusted-online')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=SCENARIOS, required=True)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, scenario=args.scenario, revision=args.revision, mutant=args.mutant,
                  runtime='real daemon/gate/Claude Code; scripted Messages API; zero vendor model calls; no Electron',
                  checks=[], preconditions=[], observed={})
    fixture = None
    holder = {}

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        (report['checks'] if condition else report.setdefault('failed', [])).append(name)

    def precondition(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        (report['preconditions'] if condition else report.setdefault('preconditions_unmet', [])).append(name)

    def last_hook(event_name):
        """The newest hook this worker's Claude Code really sent, as it sent it."""
        rows = holder['fixture'].request('orchestration_events', task='demo+T-1')['events']
        for event in reversed(rows):
            raw = event['data'].get('raw_stdin') if event['type'] == 'hook_received' else None
            if raw and json.loads(raw).get('hook_event_name') == event_name:
                return json.loads(raw)
        raise AssertionError('还没有 ' + event_name + ' 钩子')

    def forged(body, payload):
        # The same hook entry Claude Code calls (the gate CLI's signal), with this launch's own identity from the env.
        return 'printf %s ' + quote(json.dumps(payload)) + ' | ' + gate_line(body, "'signal' '--launch' \"$A2A_LAUNCH\"") + ' || true'

    def plan(body):
        text = prompt_text(body)
        if 'T251_CONTROLLER' in text:
            return 'controller', [('Bash', dict(command='a2a request executor', description='request executor role'))], '主控就位 T251。'
        cwd = working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        step = sum(1 for message in body['messages'] if message['role'] == 'assistant' and isinstance(message['content'], list)
                   and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in message['content']))
        # Only the cd scenario changes directory: in the others a subdirectory cwd would be a second cause on the old code.
        first = [('Bash', dict(command='mkdir -p sub && cd sub && pwd' if args.scenario == 'cd' else 'pwd', description='start'))]
        if args.scenario == 'cd':
            middle = [('Bash', dict(command='pwd && ls ..', description='work in the subdirectory'))]
        elif step < 1:
            middle = [('Bash', dict(command='true', description='placeholder'))]
        else:
            hook = last_hook('PostToolUse')
            if args.scenario == 'compact':
                # Shape of the real 2026-11-07T18:57:07Z hook of the T-249 worker (Claude Code 2.1.319).
                payload = dict(session_id=hook['session_id'], transcript_path=hook['transcript_path'], cwd=cwd,
                               prompt_id=hook['prompt_id'], hook_event_name='SessionStart', source='compact', model=hook.get('model', 'x'))
            else:
                payload = {**hook, 'cwd': '/private/tmp', 'tool_use_id': 'toolu_t251_outside'}
            middle = [('Bash', dict(command=forged(body, payload), description='a hook from ' + args.scenario))]
        return 'worker', first + middle + [
            ('Write', dict(file_path=f'{cwd}/answer.txt', content='accepted')),
            ('Bash', dict(command='git add -A', description='stage')),
            ('Bash', dict(command='git commit -q -m ' + quote('T251 fixture candidate'), description='commit')),
            ('Bash', dict(command=submit, description='submit'))], '已交付。'

    try:
        fixture = Fixture('t251-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
        holder['fixture'] = fixture
        report['fixture'] = str(fixture.dir)
        fixture.start(args.claude, {'README.md': 'T-251 fixture\n', 'check.py':
            'from pathlib import Path\nassert Path("answer.txt").read_text() == "accepted"\n'})
        fixture.card('T-1', 'answer.txt', 'check.py')
        if args.scenario == 'untrusted-online':
            # T-216's setup: the user starts Claude Code in the project terminal and it asks for the executor role.
            assert fixture.request('role_release', fixture.terminal)['ok']
            config = fixture.home / '.claude.json'
            value = json.loads(config.read_text(encoding='utf-8'))
            value.update(hasSeenAutoDefaultNudge=True, projects={str(fixture.repo): {'hasTrustDialogAccepted': True}})
            config.write_text(json.dumps(value), encoding='utf-8')
            window = fixture.request('window_open', fixture.operator, launch=fixture.terminal_launch, project='demo')
            command = (f'claude --model claude-haiku-5-5 --effort low --permission-mode dontAsk --allowedTools Bash '
                       f'--session-id {uuid.uuid4()} T251_CONTROLLER')
            assert fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()), data=command + '\r')['ok']
            pending = fixture.wait('主控申请角色', lambda: fixture.request('sidebar_snapshot').get('role_requests'), 90)
            assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)['ok']
            fixture.wait('主控角色生效', lambda: fixture.request('terminal_whoami', fixture.terminal).get('role') == 'executor', 30)
            fixture.wait('主控结束初始回合', lambda: '主控就位 T251。' in (fixture.state / 'traces' / fixture.terminal_launch / 'pty.raw')
                         .read_text(encoding='utf-8', errors='replace'), 45)
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        report['observed']['attempt'] = attempt['attempt_id']
        status = lambda: fixture.request('status', fixture.operator, task='demo+T-1')
        pane_status = lambda: fixture.request('pane_status', thread=attempt['thread_id'])
        rows = fixture.request('sidebar_snapshot')['agents']
        launch = next(row['id'] for row in rows if row['attempt'] == attempt['attempt_id'] and row['role'] == 'worker')
        events = lambda: [e for e in fixture.request('orchestration_events', task='demo+T-1')['events'] if e['launch'] == launch]

        def submit_turn_ended():
            seen = events()
            submitted = [e['seq'] for e in seen if e['type'] == 'hook_received' and '"hook_event_name":"PostToolUse"' in
                         e['data'].get('raw_stdin', '') and "'submit'" in e['data'].get('raw_stdin', '')]
            # The Stop hook as Claude Code sent it: the old code rejects a subdirectory Stop before it records turn_end_signal.
            return submitted and any(e['type'] == 'hook_received' and '"hook_event_name":"Stop"' in e['data'].get('raw_stdin', '')
                                     and e['seq'] > submitted[0] for e in seen)
        fixture.wait('交付的回合结束', submit_turn_ended, 180)
        if not args.scenario.startswith('untrusted'):
            try:
                fixture.wait('门禁已交付', lambda: status()['task']['state'] == 'submitted', 20)
            except BaseException as error:
                report['observed']['wait_submitted'] = str(error)
        else:
            # The gate's receipt makes the worker take one more short turn; wait for it to settle.
            try:
                fixture.wait('窗格不在回合中', lambda: pane_status().get('state') == 'idle' and time.sleep(3) is None and
                             pane_status().get('state') == 'idle', 60)
            except BaseException as error:
                report['observed']['wait_idle'] = str(error)
        mine = events()
        hooks = [json.loads(e['data']['raw_stdin']) for e in mine if e['type'] == 'hook_received']
        unverified = [dict(seq=e['seq'], reason=e['data'].get('reason'), hook=e['data'].get('hook_event_name'))
                      for e in mine if e['type'] == 'native_question_unverified']
        current = status()
        state = current['task']['state']
        report['observed'].update(gate_state=state, pane=pane_status(), unverified=unverified,
                                  hook_cwds=sorted({h.get('cwd') for h in hooks if h.get('cwd')}),
                                  relay=[dict(seq=e['seq'], type=e['type'], error=(e['data'].get('result') or {}).get('error'))
                                         for e in mine if e['type'].startswith('relay_')],
                                  # status lists issue views; the record itself is under 'issue'.
                                  issues=[dict(title=v['issue'].get('title'), blocking=v['issue'].get('blocking'), from_=v['issue'].get('from'),
                                               to=v['issue'].get('to'), state=v.get('state'), body=str(v['issue'].get('body'))[:900])
                                          for v in current.get('issues', [])])
        worktree = attempt.get('workspace') or ''
        if args.scenario == 'cd':
            precondition('hooks_reported_the_subdirectory', any(h.get('cwd', '').endswith('/sub') for h in hooks),
                          report['observed']['hook_cwds'])
            check('delivered_at_turn_end', state == 'submitted', state)
            check('no_hook_judged_foreign', not unverified, unverified)
        elif args.scenario == 'compact':
            precondition('compact_hook_reached_the_daemon', any(h.get('hook_event_name') == 'SessionStart' and h.get('source') == 'compact'
                                                                for h in hooks), None)
            check('delivered_at_turn_end', state == 'submitted', state)
            check('no_hook_judged_foreign', not unverified, unverified)
        else:
            precondition('outside_hook_judged_foreign', any(u['hook'] == 'PostToolUse' for u in unverified), unverified)
            check('untrusted_delivery_not_executed', state == 'claimed' and not current['task'].get('candidate_commit'), state)
            pane_now = pane_status()
            check('turn_ended_not_running', pane_now.get('state') == 'idle', pane_now.get('state'))
            reasons = [i for i in report['observed']['issues'] if i['blocking'] and i['to'] == 'executor'
                       and 'current_turn_untrusted' in i['body'] and '"submit"' in i['body']]
            check('controller_status_shows_reason', bool(reasons), report['observed']['issues'])
            # Not only listed: handed to the inbox for the executor that dispatched the worker (T-216). The receipts are read
            # from the store itself. The inbox sends only to an approved controller terminal whose CLI is in the foreground;
            # this fixture's terminal runs no CLI, so the receipt the inbox defines for that is pending/role_session_missing,
            # delivered when the executor's CLI is ready (resumeControllerInbox). The send itself is T-216's path, not shown here.
            sent = [v['issue'] for v in current.get('issues', []) if v['issue'].get('blocking') and v['issue'].get('to') == 'executor'
                    and 'current_turn_untrusted' in str(v['issue'].get('body'))]
            store = sqlite3.connect(f"file:{fixture.dir / 'state' / 'state.sqlite3'}?mode=ro", uri=True)
            try:
                receipts = [dict(entry=entry, **json.loads(data)) for entry, data in store.execute(
                    'SELECT entry, data FROM inbox_deliveries ORDER BY seq') if entry in {issue['id'] for issue in sent}]
            finally:
                store.close()
            last = receipts[-1] if receipts else {}
            report['observed']['inbox_receipts'] = receipts
            if args.scenario == 'untrusted-online':
                ids = {issue['id'] for issue in sent}

                def received():
                    return [b for b in fixture.api.bodies if b['key'] == 'controller' and any(
                        i in json.dumps(m, ensure_ascii=False) for i in ids for m in b['messages'] if m['role'] == 'user')]
                try:
                    fixture.wait('执行主控的 CLI 收到问题', lambda: ids and received(), 60)
                except BaseException as error:
                    report['observed']['wait_received'] = str(error)
                store = sqlite3.connect(f"file:{fixture.dir / 'state' / 'state.sqlite3'}?mode=ro", uri=True)
                try:
                    receipts = [dict(entry=entry, **json.loads(data)) for entry, data in store.execute(
                        'SELECT entry, data FROM inbox_deliveries ORDER BY seq') if entry in ids]
                finally:
                    store.close()
                report['observed']['inbox_receipts'] = receipts
                check('issue_reached_executor_cli', bool(ids) and bool(received()) and receipts and receipts[-1].get('state') == 'delivered',
                      dict(receipts=receipts, controller_requests=len(received())))
            check('issue_sent_through_inbox', bool(sent) and all(issue.get('controller_launch') == fixture.terminal['launch'] for issue in sent)
                  and (last.get('state') in ('queued', 'delivered') or (last.get('state') == 'pending' and last.get('reason') == 'role_session_missing')),
                  dict(controller_launch=[issue.get('controller_launch') for issue in sent], terminal=fixture.terminal['launch'], receipts=receipts))
            reclaimed = fixture.request('reclaim', fixture.terminal, task='T-1', attempt=attempt['attempt_id'])
            report['observed']['reclaim'] = {k: reclaimed.get(k) for k in ('ok', 'error', 'details')}
            check('old_attempt_reclaimed', bool(reclaimed.get('ok')), report['observed']['reclaim'])
            again = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
            report['observed']['redispatch'] = {k: again.get(k) for k in ('ok', 'error', 'details')}
            check('new_worker_dispatched', bool(again.get('ok')) and again['attempt']['attempt_id'] != attempt['attempt_id'],
                  report['observed']['redispatch'])
        if report.get('preconditions_unmet'):
            report['status'] = 'INCOMPLETE'
        elif report.get('failed'):
            raise AssertionError('未通过：' + '、'.join(report['failed']))
        else:
            report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
        if fixture:
            try:
                fixture.stop()
            except BaseException as cleanup:
                report.setdefault('cleanup_errors', []).append(str(cleanup))
            report['api'] = fixture.api.snapshot()
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
        if fixture and report['status'] == 'PASS':
            shutil.rmtree(fixture.dir, ignore_errors=True)
    print(report['status'], report.get('error', ''), report.get('preconditions_unmet', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
