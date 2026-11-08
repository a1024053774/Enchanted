"""T-252：Codex、agy、opencode worker 的一回合被判“不可信”以后，Stop 被拒在窗格转空闲之前：窗格永远“在回合中”、旧 worker
回收不了、新 worker 派不出去，交付被静默丢下（T-251 只修了 Claude worker）。
真实后台与门禁，不开 Electron。Codex：真实 Codex CLI，模型换成本地脚本化 Responses 接口（照 T-140、T-229，零真实模型调用，
Codex 在夹具的隔离 home 里）。agy、opencode：T-187 的本地替身 CLI（t187_fake_cli.c 受管模式与 t187_fake_worker.py，不连模型），
回合状态照真实 CLI 用 OSC 7501 报给终端。

期望来自需求（T-252 票；用户 2026-11-07：“现在这样的问题得修复,而且为什么旧 worker 不回收就派发不了新 worker”）：
回合中途进来一个来源核对不上的钩子（经同一个钩子入口 `signal`，带本 worker 的启动身份）：Codex 是一条 cwd 在工作区以外的
PostToolUse（照真实钩子复制，只改 cwd 与工具调用号）；agy、opencode 没有按会话的钩子，进来的任何钩子都核对不上。之后 worker 照常
提交、submit、结束回合。门禁仍不受理这一回合的交付（不放宽身份核对），但是：回合结束后窗格不再算“在回合中”；执行主控的 status
能看到一条阻塞问题，写明交付没被受理和原因，问题里的回合号是这一回合的（Codex、agy、opencode 的 Stop 没有 prompt_id，取 turn_id）；
这条问题交给收件箱、发给派发这个 worker 的执行主控；旧 attempt 能回收，回收后同一任务能派出新 worker。

失败方式（先列再写）：
1. 修前：Stop 抛 current_turn_untrusted，窗格一直“在回合中”，回收返回 worker_working，再派返回 already_claimed，没有任何提醒。
2. 修过头：不可信回合的交付被执行（任务变成 submitted）。
3. 回合结束了，窗格却还算“在回合中”（回收不了）；或结束了但没有任何地方告诉主控（静默）。
4. 问题里的回合号是空的（只认 Claude 的 prompt_id）。
5. 测试本身：伪造钩子没到后台、没被判不符（Codex 沙箱挡住了入口等），场景就没触到要测的路径——列为前提核对，不满足判
   INCOMPLETE 而不是 PASS。
--launch：执行主控怎么派出 worker。dispatch 同 T-251；run 是 T-251 之后执行主控技能的默认做法（后台 run 盯到结果），run 每轮观察
都把 worker 的领导进程与原生会话号绑定到 attempt。Codex 在 dispatch 时还没开始回合，这两项是空的，之后只有 run 的观察或一次被受理的
submit 会绑定；回收要求它们已绑定（`identity_conflict`）。所以 Codex 经 dispatch 派出、交付又被拒时，回收另有一道与回合可信度无关
的拒绝（本票红态实测），另开票处理；本票 Codex 的验收用 run。用 run 时，测试在问题出现后照执行主控的做法回收、等 run 结束，再派新 worker。
--revision 在该版本源码上跑；--mutant 见 MUTANTS。
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Fixture, quote  # noqa: E402
from t112_native_api import message_events, request_source, request_tools, shell_item, tool_events  # noqa: E402

HERE = Path(__file__).resolve().parent
MODEL = 'gpt-6.1-sol'
# --launch run: long enough that the run is still following when the executor reclaims (its own deadline cleanup would reclaim too).
RUN_WAIT = 600
MUTANTS = {
    # Codex: the untrusted turn's requests are executed after all.
    'codex-untrusted-executes': [('src/panes.ts', 'if (transfer) await transfer(pane, value, matched, refusal);\n        if (!matched)',
                                  'if (transfer) await transfer(pane, value, matched);\n        if (!matched)')],
    # Codex: the refusal is reported, but the pane stays in its turn.
    'codex-turn-stays-busy': [('src/panes.ts', 'pane.active = null; pane.state = pane.failed && !protocolFailure ? "unknown" : pane.interrupted ? "busy" : "idle";\n        this.store.event(pane.state === "idle" ? "pane_idle" : "pane_completion_held", { submission: active!.id, state: pane.state, stop: value, ...(refusal',
                               'pane.active = null; pane.state = pane.failed && !protocolFailure ? "unknown" : refusal || pane.interrupted ? "busy" : "idle";\n        this.store.event(pane.state === "idle" ? "pane_idle" : "pane_completion_held", { submission: active!.id, state: pane.state, stop: value, ...(refusal')],
    # agy/opencode: the untrusted turn's requests are executed after all.
    'reported-untrusted-executes': [('src/panes.ts', 'if (transfer) await transfer(pane, value, matched, refusal);\n      if (!matched) { this.store.event("stop_not_matched", value, pane.record); return; }\n      const protocolFailure',
                                     'if (transfer) await transfer(pane, value, matched);\n      if (!matched) { this.store.event("stop_not_matched", value, pane.record); return; }\n      const protocolFailure')],
    # agy/opencode: the refusal is reported, but the pane stays in its turn.
    'reported-turn-stays-busy': [('src/panes.ts', 'pane.active = null; pane.state = pane.failed && !protocolFailure ? "unknown" : pane.interrupted ? "busy" : "idle";\n      this.store.event(pane.state === "idle" ? "pane_idle" : "pane_completion_held", { submission: active!.id, state: pane.state, stop: value, ...(refusal',
                                  'pane.active = null; pane.state = pane.failed && !protocolFailure ? "unknown" : refusal || pane.interrupted ? "busy" : "idle";\n      this.store.event(pane.state === "idle" ? "pane_idle" : "pane_completion_held", { submission: active!.id, state: pane.state, stop: value, ...(refusal')],
    # The issue names the turn only by a Claude prompt id.
    'issue-no-turn': [('src/daemon.ts', 'turn_id: stop.prompt_id ?? stop.turn_id ?? null,', 'turn_id: stop.prompt_id ?? null,')],
}
FILES = {'README.md': 'T-252 fixture\n', 'check.py': 'from pathlib import Path\nassert Path("answer.txt").read_text() == "accepted"\n'}
# The fake agy/opencode worker writes done.txt (T-187); its card allows that file.
FAKE_FILES = {'README.md': 'T-252 fixture\n', 'check.py': 'from pathlib import Path\nassert Path("done.txt").read_text() == "done\\n"\n'}
SETTINGS = {'security': {'auth': {'selectedType': 'fixture'}}, 'trustedWorkspaces': ['/already/trusted']}
# The fake worker's helper, put next to the fake CLI in place of t187_fake_worker.py: in a dispatched work turn it first
# sends one hook through this launch's own hook entry (the gate CLI's signal), then does the original turn unchanged.
FORGING_WORKER = r'''
import json, os, re, runpy, subprocess, sys, time
from pathlib import Path
here = Path(__file__).resolve().parent
if sys.argv[1] == 'work':
    text = Path(sys.argv[2]).read_text(encoding='utf-8').replace('\x1b[200~', '').replace('\x1b[201~', '')
    submit = re.search(r'显式交付：\n(.+)\n', text)
    if submit and '审查这一次交付' not in text:
        time.sleep(1)
        line = submit.group(1)
        entry = line[:line.index("'submit'")] + "'signal' '--launch' \"$A2A_LAUNCH\""
        payload = dict(hook_event_name='PostToolUse', session_id=os.environ.get('A2A_NATIVE_SESSION'), cwd='/private/tmp',
                       tool_name='Bash', tool_use_id='t252_outside', tool_input={'command': 'pwd'})
        quoted = "'" + json.dumps(payload).replace("'", "'\\''") + "'"
        run = subprocess.run(['/bin/sh', '-c', 'printf %s ' + quoted + ' | ' + entry], capture_output=True, text=True)
        (here / 't252-forged.json').write_text(json.dumps(dict(code=run.returncode, stdout=run.stdout[-2000:], stderr=run.stderr[-2000:])))
sys.argv = [str(here / 't187_fake_worker_base.py'), *sys.argv[1:]]
runpy.run_path(str(here / 't187_fake_worker_base.py'), run_name='__main__')
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', choices=['codex', 'agy', 'opencode'], required=True)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    parser.add_argument('--codex', default=shutil.which('codex') or str(Path.home() / '.local/bin/codex'))
    parser.add_argument('--launch', choices=['dispatch', 'run'], default='dispatch')
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, cli=args.cli, launch=args.launch, revision=args.revision, mutant=args.mutant,
                  runtime=('real daemon/gate/Codex CLI; scripted Responses API; zero vendor model calls; no Electron' if args.cli == 'codex'
                           else 'real daemon/gate; T-187 fake agy/opencode CLI with OSC 7501 reports; no model; no Electron'),
                  checks=[], preconditions=[], observed={})
    fixture = server = None
    api = dict(requests=0, error=None, forged=None)
    holder = {}

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        (report['checks'] if condition else report.setdefault('failed', [])).append(name)

    def precondition(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        (report['preconditions'] if condition else report.setdefault('preconditions_unmet', [])).append(name)

    def user_text(item):
        return '\n'.join(part.get('text', '') for part in item.get('content', []) if isinstance(part, dict))

    def last_post_tool_use():
        """The newest PostToolUse this Codex worker really sent, as it sent it."""
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            rows = holder['fixture'].request('orchestration_events', task='demo+T-1')['events']
            for event in reversed(rows):
                raw = event['data'].get('raw_stdin') if event['type'] == 'hook_received' else None
                if raw and json.loads(raw).get('hook_event_name') == 'PostToolUse':
                    return json.loads(raw)
            time.sleep(.2)
        raise AssertionError('还没有 PostToolUse 钩子')

    def codex_step(body):
        items = body['input']
        at = max(n for n, item in enumerate(items) if item.get('type') == 'message' and item.get('role') == 'user')
        submit = re.search(r'显式交付：\n(.+)\n', user_text(items[at]))
        # The gate's receipt arrives as its own short turn: acknowledge it.
        if not submit:
            return message_events('收到。', body['model'])
        cwd = re.search(r'<cwd>([^<]+)</cwd>', json.dumps(body, ensure_ascii=False)).group(1)
        line = submit.group(1)
        done = sum(1 for item in items[at + 1:] if item.get('type') == 'custom_tool_call')
        steps = ['pwd', 'forge', 'printf accepted > answer.txt', 'git add answer.txt', 'git commit -q -m ' + quote('T252 fixture candidate'),
                 line.replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')]
        if done >= len(steps):
            return message_events('已交付。', body['model'])
        step = steps[done]
        if step == 'forge':
            # The same hook entry Codex calls (the gate CLI's signal), with this launch's own identity from the env.
            payload = {**last_post_tool_use(), 'cwd': '/private/tmp', 'tool_use_id': 'call_t252_outside'}
            api['forged'] = payload
            entry = line[:line.index("'submit'")] + "'signal' '--launch' \"$A2A_LAUNCH\""
            step = 'printf %s ' + quote(json.dumps(payload)) + ' | ' + entry + '; echo "signal-exit=$?"'
        return tool_events(shell_item(request_tools(body), step, cwd), body['model'])

    class CodexApi(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_GET(self):
            payload = json.dumps({'object': 'list', 'data': [{'id': MODEL, 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                api['requests'] += 1
                events = (message_events(json.dumps({'title': 'T-252 fixture'}), body['model']) if request_source(body) == 'thread_title'
                          else codex_step(body))
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for sequence, (name, payload) in enumerate(events):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api['error'] = f'{type(error).__name__}: {error}'
                self.send_error(500)

    try:
        fixture = Fixture('t252-', lambda body: ('unused', [], '好的。'), revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
        holder['fixture'] = fixture
        report['fixture'] = str(fixture.dir)
        if args.cli == 'codex':
            codex_home = fixture.home / '.codex'
            (codex_home / 'rules').mkdir(parents=True)
            server = ThreadingHTTPServer(('127.0.0.1', 0), CodexApi)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            (codex_home / 'config.toml').write_text('model_provider="t252"\ncli_auth_credentials_store="file"\n'
                f'[projects.{json.dumps(str(fixture.repo.resolve()))}]\ntrust_level="trusted"\n'
                '[model_providers.t252]\nname="T252 fixture"\n'
                f'base_url="http://127.0.0.1:{server.server_port}/v1"\nwire_api="responses"\nrequires_openai_auth=false\n', encoding='utf-8')
            # The user's two Git prefix rules (AGENTS.md), nothing more.
            (codex_home / 'rules/default.rules').write_text('prefix_rule(pattern=["git","add"],decision="allow")\n'
                                                         'prefix_rule(pattern=["git","commit"],decision="allow")\n', encoding='utf-8')
            launch_config = dict(codex_bin=args.codex, codex_home=str(codex_home))
            executor = dict(cli='Codex', model=MODEL, effort='high')
            files, allow = FILES, 'answer.txt'
            report['versions'] = dict(codex=subprocess.check_output([args.codex, '--version'], text=True).strip())
        else:
            fake = fixture.dir / 'fake-bin'
            fake.mkdir()
            subprocess.run(['cc', '-O2', '-o', str(fake / 'agy'), str(HERE / 't187_fake_cli.c')], check=True)
            os.link(fake / 'agy', fake / 'opencode')
            shutil.copy2(HERE / 't187_fake_worker.py', fake / 't187_fake_worker_base.py')
            (fake / 't187_fake_worker.py').write_text(FORGING_WORKER, encoding='utf-8')
            settings = fixture.home / '.gemini/antigravity-cli/settings.json'
            settings.parent.mkdir(parents=True)
            settings.write_text(json.dumps(SETTINGS, indent=2), encoding='utf-8')
            launch_config = dict(agy_bin=str(fake / 'agy'), opencode_bin=str(fake / 'opencode'))
            executor = dict(cli=args.cli, model='fixture-model', effort='high')
            files, allow = FAKE_FILES, 'done.txt'
        fixture.start(args.claude, files, launch_config)
        fixture.card('T-1', allow, 'check.py', executor=executor)
        status = lambda: fixture.request('status', fixture.operator, task='demo+T-1')
        running = {}
        if args.launch == 'run':
            def run():
                # The run holds its request until it ends: a socket of its own, without Fixture.request's 60 s limit.
                with socket.socket(socket.AF_UNIX) as connection:
                    connection.settimeout(RUN_WAIT + 120)
                    connection.connect(str(fixture.state / 'control.sock'))
                    connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='run', task='T-1', runtimeMode='workspace-write',
                                        wait_seconds=RUN_WAIT), identity=fixture.terminal)) + '\n').encode())
                    response = b''
                    while b'\n' not in response:
                        part = connection.recv(65536)
                        assert part, 'daemon 在回执前断开'
                        response += part
                running['result'] = json.loads(response.split(b'\n', 1)[0])
            running['thread'] = threading.Thread(target=run, daemon=True)
            running['thread'].start()
            attempt = fixture.wait('run 派出 worker', lambda: (status()['task'].get('current_attempt') or {}).get('thread_id') and
                                   status()['task']['current_attempt'], 60)
        else:
            dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
            assert dispatched.get('ok'), dispatched
            attempt = dispatched['attempt']
        report['observed']['attempt'] = attempt['attempt_id']
        pane_status = lambda: fixture.request('pane_status', thread=attempt['thread_id'])
        rows = fixture.request('sidebar_snapshot')['agents']
        launch = next(row['id'] for row in rows if row['attempt'] == attempt['attempt_id'] and row['role'] == 'worker')
        events = lambda: [e for e in fixture.request('orchestration_events', task='demo+T-1')['events'] if e['launch'] == launch]

        def submit_turn_ended():
            seen = events()
            if args.cli == 'codex':
                # The Stop hook as Codex sent it, after the PostToolUse of the submit command.
                submitted = [e['seq'] for e in seen if e['type'] == 'hook_received' and '"hook_event_name":"PostToolUse"' in
                             e['data'].get('raw_stdin', '') and "'submit'" in e['data'].get('raw_stdin', '')]
                return submitted and any(e['type'] == 'hook_received' and '"hook_event_name":"Stop"' in e['data'].get('raw_stdin', '')
                                         and e['seq'] > submitted[0] for e in seen)
            # agy/opencode: the backend's own Stop from the OSC 7501 report, after the forged hook was judged.
            forged = [e['seq'] for e in seen if e['type'] == 'native_question_unverified']
            return forged and any(e['type'] == 'turn_end_signal' and e['seq'] > forged[0] for e in seen)
        fixture.wait('交付的回合结束', submit_turn_ended, 240)
        try:
            # The gate's receipt makes the worker take one more short turn; wait for it to settle.
            fixture.wait('窗格不在回合中', lambda: pane_status().get('state') == 'idle' and time.sleep(3) is None and
                         pane_status().get('state') == 'idle', 60)
        except BaseException as error:
            report['observed']['wait_idle'] = str(error)
        mine = events()
        unverified = [dict(seq=e['seq'], reason=e['data'].get('reason'), hook=e['data'].get('hook_event_name'), turn=e['data'].get('turn'))
                      for e in mine if e['type'] == 'native_question_unverified']
        current = status()
        state = current['task']['state']
        report['observed'].update(gate_state=state, pane=pane_status(), unverified=unverified,
                                  relay=[dict(seq=e['seq'], type=e['type'], error=(e['data'].get('result') or {}).get('error'))
                                         for e in mine if e['type'].startswith('relay_')],
                                  stop_failures=[dict(seq=e['seq'], type=e['type'], error=str(e['data'].get('error'))[:300])
                                                 for e in mine if e['type'] in ('stop_transfer_failed', 'pane_failed')],
                                  issues=[dict(title=v['issue'].get('title'), blocking=v['issue'].get('blocking'), from_=v['issue'].get('from'),
                                               to=v['issue'].get('to'), turn_id=v['issue'].get('turn_id'), state=v.get('state'),
                                               body=str(v['issue'].get('body'))[:900]) for v in current.get('issues', [])])
        if args.cli == 'codex':
            report['observed']['forged_hook'] = api['forged']
        else:
            forged_run = fixture.dir / 'fake-bin' / 't252-forged.json'
            report['observed']['forged_hook'] = json.loads(forged_run.read_text()) if forged_run.exists() else None
        forged = [u for u in unverified if u['hook'] == 'PostToolUse']
        precondition('outside_hook_judged_foreign', bool(forged), unverified)
        check('untrusted_delivery_not_executed', state == 'claimed' and not current['task'].get('candidate_commit'), state)
        pane_now = pane_status()
        check('turn_ended_not_running', pane_now.get('state') == 'idle', pane_now.get('state'))
        reasons = [i for i in report['observed']['issues'] if i['blocking'] and i['to'] == 'executor'
                   and 'current_turn_untrusted' in i['body'] and '"submit"' in i['body']]
        check('controller_status_shows_reason', bool(reasons), report['observed']['issues'])
        # The turn the forged hook was judged in (its binding's turn) is the turn the issue names.
        turn = forged[0]['turn'] if forged else None
        check('issue_names_the_turn', bool(turn) and bool(reasons) and all(i['turn_id'] == turn for i in reasons),
              dict(turn=turn, issues=[i['turn_id'] for i in reasons]))
        # Handed to the inbox for the executor that dispatched the worker (T-216). This fixture's terminal runs no CLI, so the
        # receipt the inbox defines for that is pending/role_session_missing (T-251 RESULTS); delivery into a live executor
        # CLI is T-251's untrusted-online scenario, the same path whatever CLI the worker runs.
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
        check('issue_sent_through_inbox', bool(sent) and all(issue.get('controller_launch') == fixture.terminal['launch'] for issue in sent)
              and (last.get('state') in ('queued', 'delivered') or (last.get('state') == 'pending' and last.get('reason') == 'role_session_missing')),
              dict(controller_launch=[issue.get('controller_launch') for issue in sent], terminal=fixture.terminal['launch'], receipts=receipts))
        report['observed']['attempt_identity'] = (status()['task'].get('current_attempt') or {}).get('runtime_identity')
        reclaimed = fixture.request('reclaim', fixture.terminal, task='T-1', attempt=attempt['attempt_id'])
        report['observed']['reclaim'] = {k: reclaimed.get(k) for k in ('ok', 'error', 'details')}
        check('old_attempt_reclaimed', bool(reclaimed.get('ok')), report['observed']['reclaim'])
        if running:
            # The executor reclaimed the attempt the run follows; the run ends (superseded) before the next dispatch.
            running['thread'].join(90)
            result = running.get('result') or {}
            report['observed']['run'] = dict(ended=not running['thread'].is_alive(), ok=result.get('ok'), error=result.get('error'),
                                             outcome=(result.get('run') or {}).get('outcome'))
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
        if server:
            server.shutdown()
        report['api'] = dict(requests=api['requests'], error=api['error'])
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
        if fixture and report['status'] == 'PASS':
            shutil.rmtree(fixture.dir, ignore_errors=True)
    print(report['status'], report.get('error', ''), report.get('preconditions_unmet', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
