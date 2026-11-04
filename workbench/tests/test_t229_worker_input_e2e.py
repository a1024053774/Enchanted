"""T-229：受管 worker 窗格里的用户输入只记最终发出的那一条，文字取 CLI 实际提交的全文，不记按键。
真实 Electron 窗口（CDP 发原生按键给 xterm）、真实后台与门禁；worker 是真实 Claude Code 或 Codex，
模型换成本地脚本化接口（Claude 走 Messages，Codex 走 Responses），零真实模型调用。

预期来自需求（用户 2026-11-01：“在终端输入的算是用户输入的,然后只记录我发送之后的完整的这一条,
不要把输入过程中的操作以及其他琐碎的东西记录进去,只记录最终的我发的话”，T-229）：
1. 打 “abc”、左方向键、“d”、回车：只记一条 message，文字是 CLI 收到的 “abdc”，记录里没有按键（没有 content）。
2. 按 ↑ 调出上一句、回车：再记一条，文字仍是 CLI 实际提交的 “abdc”，没有 text_uncertain；同一段文字第二次提交照记。
3. 任务书与主控派发进去的正文不进用户输入。
4. 用户自己贴入一条已被认领的派发全文再发送：记为用户输入（每条派发只认领一次）。
5. 每条用户输入照旧产生一条人工介入。
--case record-fails：用户输入记不下来时，这次提交被阻断，CLI 不把它交给模型（T-206 的 fail-closed），失败记在 request_rejected，
用户输入观察标为失败。各失败场景的阻断都由钩子命令（gates/cli.ts）在后台没确认记下时给出。
--case diagnostic-fails：记录失败后，连记下这次失败的 request_rejected 也写不进去（同一个库坏了），提交仍被阻断。
--case query-fails：认领前的查询失败，提交被阻断，用户输入观察标为失败（第三轮审查 P2）。
--case request-fails：后台在钩子请求进到窗格之前就失败（写不进 request_received），钩子命令自己阻断这次提交（第三轮审查 P1）。
--case request-hangs：后台把这次钩子请求压住 30 秒，超过 CLI 自己的钩子限时（10 秒）；钩子命令在限时前放弃等待并阻断（第四轮审查 P1），后台之后拒绝这条过期请求，不记录也不开回合（第五轮审查 P1）。
各失败场景之后窗格仍是空闲（回合在后台确认 UPS 后才开）；用户输入观察仍正常时，派发等用户的下一次提交后送进 CLI（第六轮审查 P1）。

失败方式（先列再写）：
1. 记录里仍带 content.keys（修前）。
2. ↑ 调历史后 attach 拼出的是空串或别的字，记录缺失、文字与实际提交不一致，或标 text_uncertain（修前）。
3. 后台自己派发进去的正文（任务书、主控派发）被钩子当成用户提交记下。
4. 认领把用户第二次提交的同一段文字吞掉（一条派发被认领多次，或用户正文被当成派发）。
5. 一次提交记了两条（attach 一条、钩子一条）。
6. 人工介入不再产生，或与记录条数不符。
7. 记录失败只报错，CLI 照样执行这条提交，留下没有记录、没有人工介入的回合（第一轮审查 P1）。
8. 旧派发（早已提交、没有认领事件）在之后的提交里仍能被认领，吞掉用户输入（第一轮审查 P1）。本测试造不出这种旧数据，
   只按代码核对：可认领的只有最近一次粘贴、之后还没有任何提交的那条派发。
9. 阻断依赖诊断事件写入成功：诊断写失败时异常冒出钩子，CLI 照样执行（第二轮审查 P1）。
10. 阻断依赖钩子请求外围的事件写入：请求本身失败时钩子只报错，CLI 照样执行（第三轮审查 P1）。
11. 查询或认领失败时没标观察失败，窗格之后照样接收输入（第三轮审查 P2）。
12. 后台不响应时钩子一直等，被 CLI 按自己的钩子限时杀掉，CLI 照样执行（第四轮审查 P1）。
13. 钩子放弃等待并阻断后，后台仍处理这条请求：记下被阻断的提交、派生人工介入，Claude 窗格停在没有真实回合的忙状态（第五轮审查 P1）。
14. 被阻断的提交，回车已把窗格标成忙（Codex 还建了回合），之后没有 Stop，窗格一直忙、派发送不进去（第六轮审查 P1）。
15. 回车到后台确认 UPS 之间，派发粘进用户的草稿；或被阻断后派发永远等不到（第八轮审查后改为由 UPS 开回合）。
16. 成功的 UPS 把它之后才输入、还没发出的草稿也一并释放，派发粘到这段草稿上（第九轮审查 P1）；回车后刚开始、还没上屏的输入法组合也一样（第十轮审查 P1）。
17. 记录已提交，同一请求之后的写入失败让钩子阻断：库里留着一条 CLI 没执行的用户输入（第七至九轮审查 P1）。
18. Codex：Esc 打断后用户自己发出的新回合，沿用被打断回合的提交（rollout 扫描已把它的 nativeTurn 改成新回合），
    新回合的工具钩子按“被打断”拒收，回合结束不可信（第十一轮审查 P1）。
--revision 在该版本源码上跑（修前应失败）；--mutant 见 MUTANTS。
"""
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from scripted_claude import Electron, Fixture
from scripted_claude import MARKETPLACE_SKIPPED  # T-245  # noqa: E402
from t112_native_api import message_events, request_source, request_tools, shell_item, tool_events

ROOT = Path(__file__).resolve().parents[2]
MUTANTS = {
    # Every submission the hook reports is the user's: our own dispatches are recorded too.
    'no-claim': [('src/panes.ts', 'if (ours && ours.text === text) {', 'if (ours && ours.text === text && false) {')],
    # Hook-reporting CLIs are recorded from attach as well: one submission, two records.
    'attach-too': [('src/panes.ts', 'if (!protocolReport && !submitHook(pane)) for', 'if (!protocolReport) for')],
    # A failed hook request only returns its error, as before review round 3: the CLI goes on with the submission.
    'hook-error-passes': [('src/gates/cli.ts', '(result.ok ? result.hook_output : unnoted(result.error, result.details))', '(result.ok ? result.hook_output : undefined)'),
                          ('src/gates/cli.ts', '    if (promptSubmit(request)) {', '    if (false) {')],
    # The hook waits for the daemon as long as the transport does (120 s): the CLI kills it at its own timeout and goes on.
    'no-deadline': [('src/gates/cli.ts', 'AbortSignal.timeout(PROMPT_SUBMIT_DEADLINE_MS)', 'undefined')],
    # The daemon handles a UserPromptSubmit request the hook has already given up on (review round 5, P1).
    'late-handled': [('src/daemon.ts', ' && Date.now() > input.submit_deadline)', ' && false)')],
    # The window Enter starts the turn, as before T-229 on Codex: a submission the hook blocks leaves the pane busy (review round 6, P1).
    'enter-starts-turn': [('src/panes.ts', '        if (!submitHook(pane)) {\n          pane.state = "busy"; pane.userDraft = false;', '        if (true) {\n          pane.state = "busy"; pane.userDraft = false;')],
    # A successful UserPromptSubmit releases the whole draft, input typed after its Enter included (review round 9, P1).
    'draft-released-on-submit': [('src/panes.ts', '    try { pane.userDraft = pane.inputGeneration !== pane.submitGeneration; steps(); }', '    try { pane.userDraft = false; steps(); }')],
    # A write failing after the record fails the hook request, so the hook blocks a recorded submission (review rounds 7-9, P1).
    'record-then-block': [('src/panes.ts', '    catch (error) { this.recordFailure(pane, "user_submission_bookkeeping_failed", error); }', '    catch (error) { throw error; }'),
                          ('src/daemon.ts', '            if (!promptSubmit || !result.ok) throw error;', '            throw error;')],
    # A Codex UserPromptSubmit after an interrupt keeps the interrupted turn's submission when the scan moved it (review round 11, P1).
    'esc-reuses-turn': [('src/panes.ts', ' && !(pane.interrupted && pane.active!.interruption !== pane.interruption);', ';')],
    # A failed claim lookup or record is not marked on the user-input observer (review round 3, P2).
    'no-observer-mark': [('src/panes.ts', '      this.onEventWriteFailed(`user_submission_unnoted: ${String(error)}`);\n', '')],
}
# Fault injection for the --case values other than records; each fails only on the submission "failrec".
FAULTS = {
    'record-fails': [('src/daemon.ts', 'panes.recordUserSubmission = (pane, text, received_at) => gates.appendUserInput(',
                      'panes.recordUserSubmission = (pane, text, received_at) => (text === "failrec" && (() => { throw new Error("T229 injected record failure"); })()) || gates.appendUserInput(')],
    # The claim lookup fails before any record is tried.
    'query-fails': [('src/panes.ts', '      const pasted = this.store.db.prepare(',
                     '      if (text === "failrec") throw new Error("T229 injected query failure");\n      const pasted = this.store.db.prepare(')],
    # The daemon fails on the hook request before the pane sees it (request_received cannot be written).
    'request-fails': [('src/daemon.ts', '        if (!viewing && !unlogged) store.event("request_received",',
                       '        if (envelope.input?.command === "signal" && String(envelope.input.raw_stdin).includes("failrec")) throw new Error("T229 injected request failure");\n        if (!viewing && !unlogged) store.event("request_received",')],
    # The daemon holds this hook request past the CLI's own 10 s hook timeout before handling it.
    'request-hangs': [('src/daemon.ts', '        result = await handle(envelope, authority, asker);',
                       '        if (envelope.input?.command === "signal" && String(envelope.input.raw_stdin).includes("failrec")) await new Promise(resolve => setTimeout(resolve, 30000));\n        result = await handle(envelope, authority, asker);')],
    # The daemon handles the user's submission "slowok" 3 s late (within the hook's deadline), while the user types on.
    'draft-after-enter': [('src/daemon.ts', '        result = await handle(envelope, authority, asker);',
                           '        if (envelope.input?.command === "signal" && String(envelope.input.raw_stdin).includes("slowok")) await new Promise(resolve => setTimeout(resolve, 3000));\n        result = await handle(envelope, authority, asker);')],
    # The record of "failrec" commits, then the first write after it fails.
    'after-record-fails': [('src/daemon.ts', 'panes.recordUserSubmission = (pane, text, received_at) => gates.appendUserInput(',
                            'panes.recordUserSubmission = (pane, text, received_at) => (text === "failrec" && ((globalThis as any).T229_after = true) && false) || gates.appendUserInput('),
                           ('src/panes.ts', '    try { pane.userDraft = pane.inputGeneration !== pane.submitGeneration; steps(); }',
                            '    try { pane.userDraft = pane.inputGeneration !== pane.submitGeneration; if ((globalThis as any).T229_after) { (globalThis as any).T229_after = false; throw new Error("T229 injected after-record failure"); } steps(); }')],
    # The record of "failrec" commits and its request is handled; logging the request's result fails.
    'result-fails': [('src/daemon.ts', '          try { store.event("request_result", ',
                      '          try { if (promptSubmit && String(envelope.input.raw_stdin).includes("failrec")) throw new Error("T229 injected result failure"); store.event("request_result", ')],
}
# Codex only: Esc during a long command, then the user's own turn (no fault injected).
FAULTS['esc-then-submit'] = []
# The same delay, while the user starts an IME composition instead of typing.
FAULTS['composition-after-enter'] = FAULTS['draft-after-enter']
# For --case diagnostic-fails, the record fails and the request_rejected event after it fails as well.
FAULTS['diagnostic-fails'] = FAULTS['record-fails'] + [('src/daemon.ts', '        try { if (!unlogged && !catalogCommands.has(envelope?.input?.command)) store.event("request_rejected",',
    '        try { if (String(error).includes("T229 injected")) throw new Error("T229 injected event failure");\n          if (!unlogged && !catalogCommands.has(envelope?.input?.command)) store.event("request_rejected",')]
DISPATCH = 'T229 主控派发：先看一下 README，再回复收到。'
LONG = 'T229 长命令'
PROBE = 'run probe'


def user_texts(items, key):
    """The user messages a native request carries, oldest first (Messages: messages; Responses: input)."""
    texts = []
    for item in items:
        if item.get('role') != 'user' or (key == 'input' and item.get('type') != 'message'):
            continue
        content = item.get('content')
        if isinstance(content, str):
            texts.append(content)
        else:
            texts.append(''.join(part.get('text', '') for part in content or [] if isinstance(part, dict)))
    return texts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cli', choices=['claude', 'codex'], required=True)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--case', choices=['records', *FAULTS], default='records')
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, cli=args.cli, case=args.case, revision=args.revision, mutant=args.mutant,
                  runtime='real Electron/daemon/gate and native CLI; native CDP key events; scripted model API; zero vendor model calls',
                  checks=[], observed={})
    fixture = electron = responses = None
    bodies = []

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        (report['checks'] if condition else report.setdefault('failed', [])).append(name)

    try:
        fixture = Fixture('t229-', lambda body: ('worker', [], '收到。'), revision=args.revision,
                          patches=[*MUTANTS.get(args.mutant, ()), *FAULTS.get(args.case, ())])
        report['fixture'] = str(fixture.dir)
        (fixture.home / '.claude.json').write_text(json.dumps({**MARKETPLACE_SKIPPED, 'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        launch_config, executor = None, None
        if args.cli == 'codex':
            class Responses(BaseHTTPRequestHandler):
                def log_message(self, *arguments):
                    pass

                def do_GET(self):
                    payload = json.dumps(dict(object='list', data=[dict(id='gpt-6.1-sol', object='model', owned_by='fixture')])).encode()
                    self.send_response(200); self.end_headers(); self.wfile.write(payload)

                def do_POST(self):
                    body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    bodies.append(body)
                    events = message_events('{"title":"T229"}' if request_source(body) == 'thread_title' else '收到。', body['model'])
                    if args.case == 'esc-then-submit' and request_source(body) != 'thread_title':
                        # The latest user message picks the step: a long command the user cuts off, then a short one in the
                        # user's own turn; after a tool result, a closing message.
                        items = body['input']
                        at = max(n for n, item in enumerate(items) if item.get('type') == 'message' and item.get('role') == 'user')
                        latest = json.dumps(items[at], ensure_ascii=False)
                        called = any(item.get('type') in ('custom_tool_call', 'function_call') for item in items[at + 1:])
                        command = 'sleep 120' if LONG in latest else 'printf t229-probe' if PROBE in latest else None
                        if command and not called:
                            item = shell_item(request_tools(body), command, fixture.repo)
                            item['input'] = '// @exec: {"yield_time_ms": 150000}\n' + item['input'].replace('10000', '150000')
                            events = tool_events(item, body['model'])
                    self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                    for sequence, (name, data) in enumerate(events):
                        self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **data)) + '\n\n').encode())
                    self.wfile.flush()
            responses = ThreadingHTTPServer(('127.0.0.1', 0), Responses)
            threading.Thread(target=responses.serve_forever, daemon=True).start()
            # A fixture Codex home: the local Responses provider only, no auth.json; removed with the fixture.
            home = fixture.dir / 'codex-home'; home.mkdir(mode=0o700)
            (home / 'config.toml').write_text(
                'model="gpt-6.1-sol"\nmodel_provider="t229"\ncheck_for_update_on_startup=false\n'
                f'[projects.{json.dumps(str(fixture.repo))}]\ntrust_level="trusted"\n'
                f'[model_providers.t229]\nname="T229 fixture"\nbase_url="http://127.0.0.1:{responses.server_port}/v1"\n'
                'wire_api="responses"\nrequires_openai_auth=false\n', encoding='utf-8')
            launch_config = dict(codex_bin=shutil.which('codex'), codex_home=str(home))
            executor = dict(cli='Codex', model='gpt-6.1-sol', effort='high')
        fixture.start(shutil.which('claude') or str(Path.home() / '.local/bin/claude'),
                      {'README.md': 'T-229 fixture\n', 'check.py': 'raise SystemExit(0)\n'}, launch_config)
        electron = Electron(fixture, 't229-' + fixture.dir.name[5:])
        electron.until('项目可见', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        fixture.card('T-1', 'answer.txt', 'check.py', executor=executor)
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write',
                                     **(dict(model='claude-haiku-5-5', effort='low') if args.cli == 'claude' else {}))
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        pane_status = lambda: fixture.request('pane_status', thread=attempt['thread_id'])
        idle = lambda: (lambda p: p.get('state') == 'idle' and not p.get('writing') and not p.get('active') and not p.get('queued'))(pane_status())
        fixture.wait('worker 读完任务书、空闲', idle, 180)
        rows = fixture.request('sidebar_snapshot')['agents']
        launch = next(row['id'] for row in rows if row['attempt'] == attempt['attempt_id'] and row['role'] == 'worker')
        selector = '[data-agent-launch=' + json.dumps(launch) + ']'
        electron.until('worker 侧栏可见', f'!!document.querySelector({json.dumps(selector)})')
        electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
        pane = 'document.querySelector(' + json.dumps('.pane[data-launch-id=' + json.dumps(launch) + ']') + ')'
        electron.until('worker 窗格可输入', f'{pane}?.dataset.inputEnabled === "true"')

        def cdp(method, **params):
            run = subprocess.run(['node', str(ROOT / 'workbench/tests/t145_cdp.mjs'), str(electron.port), method,
                                  json.dumps(params, ensure_ascii=False)], capture_output=True, text=True, timeout=25)
            assert run.returncode == 0, run.stderr

        def focus():
            electron.evaluate(f'{pane}.querySelector("textarea.xterm-helper-textarea").focus(), true')

        def press(key, code, virtual, text=None):
            down = dict(type='keyDown', key=key, code=code, windowsVirtualKeyCode=virtual, nativeVirtualKeyCode=virtual)
            if text is not None:
                down.update(text=text, unmodifiedText=text)
            cdp('Input.dispatchKeyEvent', **down)
            cdp('Input.dispatchKeyEvent', type='keyUp', key=key, code=code, windowsVirtualKeyCode=virtual, nativeVirtualKeyCode=virtual)
            time.sleep(.12)

        def type_text(value):
            for letter in value:
                press(letter, 'Key' + letter.upper(), ord(letter.upper()), letter)

        left = lambda: press('ArrowLeft', 'ArrowLeft', 37)
        up = lambda: press('ArrowUp', 'ArrowUp', 38)
        enter = lambda: press('Enter', 'Enter', 13, '\r')

        def inputs():
            with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
                return [json.loads(row[0]) for row in db.execute(
                    "SELECT data FROM user_inputs WHERE json_extract(data,'$.target.attempt')=? ORDER BY rowid", (attempt['attempt_id'],))]

        def native_users():
            if args.cli == 'claude':
                latest = fixture.api.bodies[-1] if fixture.api.bodies else None
                return user_texts(latest['messages'], 'messages') if latest else []
            turns = [body for body in bodies if request_source(body) != 'thread_title']
            return user_texts(turns[-1]['input'], 'input') if turns else []

        sent = lambda text, count: sum(1 for value in native_users() if value.strip() == text) >= count
        # A dispatch reaches the CLI as its labelled body (⟦主控 #n⟧ and the text).
        carried = lambda text: any(text in value for value in native_users())
        shown = lambda records: [dict(form=i['form'], text=i['text'], content=i.get('content')) for i in records]

        if args.case == 'esc-then-submit':
            assert args.cli == 'codex', 'Claude 的同一路径由 T-207 覆盖'
            events = lambda: [e for e in fixture.request('orchestration_events', task='demo+T-1')['events'] if e['launch'] == launch]
            hooks = lambda name, after: [e for e in events() if e['seq'] > after and e['type'] == 'hook_received' and
                                         f'"hook_event_name":"{name}"' in e['data'].get('raw_stdin', '')]
            # 1. A controller dispatch's turn is inside a long command; the user cuts it off with Esc.
            assert fixture.request('pane_dispatch', fixture.operator, thread=attempt['thread_id'], body=LONG + '：跑一下长命令。')['ok']
            fixture.wait('派发回合在跑长命令', lambda: hooks('PreToolUse', 0), 120)
            time.sleep(2)
            focus(); press('Escape', 'Escape', 27)
            fixture.wait('窗格被打断', lambda: pane_status().get('interrupted') is True, 30)
            time.sleep(2)
            # 2. The user sends a sentence; the model runs a short command in that new turn.
            before = max(e['seq'] for e in events())
            focus(); type_text('run'); press(' ', 'Space', 32, ' '); type_text('probe'); enter()
            submitted = lambda: next((e['seq'] for e in events() if e['seq'] > before and e['type'] == 'turn_start_signal' and
                                      PROBE in json.dumps(e['data'], ensure_ascii=False)), None)
            fixture.wait('用户回合开始', submitted, 60)
            start = submitted()
            fixture.wait('用户回合结束', lambda: any(e['type'] == 'turn_end_signal' and e['seq'] > start for e in events()), 120)
            time.sleep(2)
            mine = [e for e in events() if e['seq'] > before]
            refused = [e['data'].get('result', {}).get('error') for e in mine if e['type'] == 'request_rejected']
            intents = [e['data'] for e in mine if e['type'] == 'turn_submit_intent' and e['data'].get('origin') == 'native-hook']
            report['observed'].update(refused=refused, intents=intents, inputs=shown(inputs()), pane=pane_status(),
                                      timeline=[e['type'] for e in mine][-30:])
            check('user_turn_tool_hooks_seen', bool(hooks('PreToolUse', start)), [e['type'] for e in mine][-30:])
            # A hook judged as the interrupted turn's is refused or marked unverified; either leaves the turn untrusted.
            unverified = [e['data'].get('reason') for e in mine if e['seq'] > start and e['type'] == 'native_question_unverified']
            check('user_turn_hooks_and_stop_accepted', not unverified and
                  not [r for r in refused if r in ('question_turn_mismatch', 'current_turn_untrusted')], dict(refused=refused, unverified=unverified))
            check('user_turn_is_its_own_submission', len(intents) == 1 and intents[0].get('interruption') is not None, intents)
            check('user_sentence_recorded_once', [i['text'] for i in inputs()] == [PROBE], shown(inputs()))
            assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
            report['status'] = 'PASS'
            return
        if args.case in ('draft-after-enter', 'composition-after-enter'):
            # The user sends "slowok" and starts the next message before the daemon has handled the first one: typed
            # letters, or an IME composition that has not committed (no character reaches the pane yet).
            later = 'zq' if args.case == 'draft-after-enter' else '中'
            focus(); type_text('slowok'); enter(); time.sleep(.5)
            if args.case == 'draft-after-enter': type_text(later)
            else: cdp('Input.imeSetComposition', text=later, selectionStart=1, selectionEnd=1)
            fixture.wait('CLI 收到 slowok', lambda: sent('slowok', 1), 90)
            fixture.wait('worker 回到空闲', idle, 90)
            report['observed']['inputs'] = shown(inputs())
            check('submitted_text_recorded', [i['text'] for i in inputs()] == ['slowok'], report['observed']['inputs'])
            assert fixture.request('pane_dispatch', fixture.operator, thread=attempt['thread_id'], body=DISPATCH)['ok']
            time.sleep(10)
            check('dispatch_waits_for_later_draft', not carried(DISPATCH) and pane_status().get('user_draft') is True,
                  dict(native_users=native_users()[-2:], pane=pane_status()))
            focus()
            if args.case == 'composition-after-enter': cdp('Input.insertText', text=later); time.sleep(.5)
            enter()
            deadline = time.time() + 90
            while time.time() < deadline and not carried(DISPATCH): time.sleep(1)
            report['observed'].update(native_users_after=native_users()[-3:], inputs=shown(inputs()))
            check('later_draft_sent_alone', sent(later, 1) and carried(DISPATCH) and
                  not any(later in value and DISPATCH in value for value in native_users()), native_users()[-3:])
            assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
            report['status'] = 'PASS'
            return
        if args.case in ('after-record-fails', 'result-fails'):
            # The record is the commit point: a recorded submission runs, and the failure after it shows on the pane.
            focus(); type_text('failrec'); enter()
            time.sleep(20)
            status = pane_status()
            report['observed'].update(native_users_after=native_users()[-3:], inputs=shown(inputs()), pane=status)
            check('recorded_submission_sent_to_model', sent('failrec', 1), native_users()[-3:])
            check('one_record_for_sent_submission', [i['text'] for i in inputs()] == ['failrec'], shown(inputs()))
            reason = 'user_submission_bookkeeping_failed' if args.case == 'after-record-fails' else 'request_result_write_failed'
            check('pane_failure_visible', reason in str(status.get('failed')), status)
            assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
            report['status'] = 'PASS'
            return
        if args.case != 'records':
            focus(); type_text('failrec'); enter()
            if args.case == 'request-hangs':
                # A second Enter while the daemon holds the hook sends nothing; the pane goes back to its state before the first.
                time.sleep(1); enter()
            # The hook reply arrives within seconds (request-hangs: past the daemon's 30 s hold); a CLI that was not
            # blocked has its model turn by then as well.
            time.sleep(45 if args.case == 'request-hangs' else 20)
            events = fixture.request('orchestration_events', task='demo+T-1')['events']
            with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
                rejected = [json.loads(row[0])['result'] for row in db.execute(
                    "SELECT data FROM orchestration_events WHERE type='request_rejected' AND data LIKE '%failrec%' ORDER BY seq")]
            observer = fixture.request('workbench_snapshot', task='demo+T-1').get('user_input_observer') or {}
            report['observed'].update(rejected=rejected, observer=observer.get('state'), native_users_after=native_users()[-3:], inputs=shown(inputs()))
            check('unrecorded_submission_not_sent_to_model', not any('failrec' in value for value in native_users()), native_users()[-3:])
            check('no_record_for_blocked_submission', not inputs(), shown(inputs()))
            # The window Enter that sent the blocked submission does not leave the pane busy without a turn (review round 6):
            # the turn starts only when the daemon confirms the submission.
            check('pane_idle_after_block', idle(), pane_status())
            if observer.get('state') == 'healthy':
                # A dispatch after the block reaches the CLI (a failed observer holds the pane's input on purpose).
                assert fixture.request('pane_dispatch', fixture.operator, thread=attempt['thread_id'], body=DISPATCH)['ok']
                # The blocked submission's Enter keeps the user's draft reserved (Claude also puts the text back in its
                # prompt): the dispatch waits instead of being pasted onto it, and goes in after the user's next submission.
                time.sleep(10)
                check('dispatch_waits_for_user_draft', not carried(DISPATCH) and pane_status().get('user_draft') is True,
                      dict(native_users=native_users()[-2:], pane=pane_status()))
                focus()
                if args.cli == 'claude':
                    for _ in 'failrec': press('Backspace', 'Backspace', 8, '\x7f')
                type_text('ok'); enter()
                deadline = time.time() + 90
                while time.time() < deadline and not carried(DISPATCH): time.sleep(1)
                check('dispatch_after_block_delivered', carried(DISPATCH) and not any('failrec' in value for value in native_users()),
                      native_users()[-2:])
            if args.case == 'request-hangs':
                # The daemon reaches the held request after the hook gave up and refuses it, so nothing is recorded.
                check('late_request_refused', len(rejected) == 1 and rejected[0]['error'] == 'prompt_submit_deadline_passed', rejected)
                assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
                report['status'] = 'PASS'
                return
            if args.case != 'diagnostic-fails':
                check('failure_recorded_as_rejected_request', len(rejected) == 1 and 'T229 injected' in rejected[0]['details'], rejected)
            else:
                check('diagnostic_event_absent', not rejected, rejected)
            if args.case != 'request-fails':
                check('observer_failed_after_block', observer.get('state') == 'failed', observer)
            assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
            report['status'] = 'PASS'
            return
        # 1. The cursor moves left before the last letter.
        focus(); type_text('abc'); left(); type_text('d'); enter()
        fixture.wait('CLI 收到第 1 句', lambda: sent('abdc', 1), 90)
        fixture.wait('worker 回到空闲', idle, 90)
        time.sleep(1)
        first = inputs()
        report['observed']['after_1'] = shown(first)
        check('edited_message_one_record_without_keys', len(first) == 1 and first[0]['form'] == 'message' and
              first[0]['text'] == 'abdc' and 'content' not in first[0], report['observed']['after_1'])

        # 2. Up recalls the previous sentence from the CLI's own history; nothing is typed through attach.
        focus(); up(); time.sleep(.5); enter()
        fixture.wait('CLI 第二次收到同一句', lambda: sent('abdc', 2), 90)
        fixture.wait('worker 再次空闲', idle, 90)
        time.sleep(1)
        second = inputs()[len(first):]
        report['observed']['after_2'] = shown(second)
        check('history_recall_records_actual_text', len(second) == 1 and second[0]['form'] == 'message' and
              second[0]['text'] == 'abdc' and 'content' not in second[0], report['observed']['after_2'])

        # 3. The task brief and a controller dispatch reach the CLI but are not the user's input.
        assert fixture.request('pane_dispatch', fixture.operator, thread=attempt['thread_id'], body=DISPATCH)['ok']
        fixture.wait('CLI 收到主控派发', lambda: carried(DISPATCH), 90)
        fixture.wait('worker 第三次空闲', idle, 90)
        time.sleep(1)
        records = inputs()
        report['observed']['all'] = shown(records)
        report['observed']['native_users'] = native_users()
        brief = next(value for value in native_users() if 'T-1' in value or 'answer.txt' in value)
        check('dispatches_not_user_input', len(records) == 2 and not any(DISPATCH in r['text'] or r['text'] == brief for r in records),
              report['observed']['all'])
        # 4. The user pastes the full text of that dispatch, already claimed, and sends it: it is the user's now.
        events = fixture.request('orchestration_events', task='demo+T-1')['events']
        body = next(e['data']['text'] for e in events if e['type'] == 'dispatch_queued' and DISPATCH in e['data']['text'])
        second_window = fixture.request('window_open', fixture.operator, launch=launch, task='demo+T-1')
        assert second_window['ok'], second_window
        for number, data in enumerate(('\x1b[200~' + body + '\x1b[201~', '\r'), 1):
            assert fixture.request('window_input', second_window['identity'], sequence=number, request_id=str(uuid.uuid4()), data=data)['ok']
            time.sleep(.5)
        fixture.wait('CLI 第二次收到派发全文', lambda: sum(1 for value in native_users() if DISPATCH in value) >= 2, 90)
        fixture.wait('worker 第四次空闲', idle, 90)
        time.sleep(1)
        records = inputs()
        report['observed']['after_4'] = shown(records[2:])
        events = fixture.request('orchestration_events', task='demo+T-1')['events']
        claims = [e for e in events if e['launch'] == launch and e['type'] == 'dispatch_prompt_claimed']
        report['observed']['claims'] = len(claims)
        check('claimed_dispatch_resent_by_user_is_recorded', len(records) == 3 and records[2]['text'] == body and len(claims) == 2,
              dict(records=shown(records), claims=len(claims)))

        # 5. Each user input is still one human intervention.
        human = [e for e in fixture.request('events', fixture.operator, task='demo+T-1')['events']
                 if e['type'] == 'human_intervention' and e['attempt'] == attempt['attempt_id']]
        report['observed']['human_interventions'] = len(human)
        check('interventions_follow_records', len(human) == len(records) == 3, dict(human=len(human), inputs=len(records)))
        assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
        for resource in (electron, fixture):
            if resource:
                try:
                    resource.stop()
                except BaseException as error:
                    report.setdefault('cleanup_errors', []).append(str(error))
        if responses:
            responses.shutdown()
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    print(report['status'], report.get('error', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
