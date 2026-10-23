"""T-133 方案 A 的 Codex 一侧与 T-107 #4：项目终端里由用户自己启动、经角色申请批准的 Codex 主控。真实后台、门禁、
项目终端（zsh 与包装脚本），终端里跑真实 Codex（交互模式，模型是本地脚本化的 Responses 接口），真实 Electron 窗口经
DevTools 协议操作。夹具用户的 Codex 在隔离 home 里（不碰用户的 ~/.codex），自己带一个 hooks.json 钩子。

用户决定（2026-10-22，逐字）：“1. A 2. 一二都要.”——Codex 一侧选 A：用户在自己的 Codex 里信任一次 Enchanted 的钩子，
信任由 Codex 写进用户配置，a2a 不写。接法依据 codex-hook-probe 的 probe-04～06。

场景（期望来自 ticket、用户决定与探针记录，不读被测代码的输出）：
1. 终端 I 里启动 codex。Codex 提示有钩子要审查；此前 a2a 没有改过用户的 config.toml。用户选“Trust all and continue”，
   Codex 把信任写进 config.toml。用户自己 hooks.json 里的钩子照常运行。
2. 用户提交 REQUEST_IDEATION；模型运行 `a2a request ideation`，用户在界面批准。这条在批准之前提交，不记。回合结束后
   侧栏是“空闲”。
3. 用户提交 IDEA_PROMPT（批准之后）。模型用 request_user_input_async 问用户，然后等（clock.sleep）。侧栏是“等待用户
   回答”，工具立刻返回 accepted 之后也保持。用户在终端里用 ⇧← 打开问题、回车选第一项；之后模型跑 15 秒的命令，侧栏
   是“运行中”；回合结束后是“空闲”。
4. 终端 X 里再启动 codex，不再提示审查钩子（定义没变，信任一直有效）。用户提交 REQUEST_EXECUTOR，批准时上级默认是
   终端 I 的构思主控；侧栏里执行主控挂在构思主控下。
5. 用户在终端 I 让它放弃身份（`a2a release`），之后再提交 AFTER_RELEASE。记录页列出 IDEA_PROMPT、对问题的答复、
   RELEASE（主控终端提交、构思主控），不列 REQUEST_IDEATION、REQUEST_EXECUTOR 与 AFTER_RELEASE。

失败方式（先列再写）：
1. 包装脚本没把钩子交给 Codex：不提示信任，什么都不记，状态一直未知。
2. 用户选择之前配置里已有信任（a2a 写了用户的 Codex 配置）；或 Enchanted 的钩子顶掉了用户自己的钩子。
3. 批准前、身份结束后的提示词被记下；批准后的整句没记或文字不对。
4. 用户对问题的答复记成一条普通消息，或没记；记下的不是“问题：答复”。
5. 问题工具立刻返回 accepted 时状态就回到“运行中”，用户还没答。
6. 换一个终端又要信任一次。
7. 批准时选的上级没保存，执行主控进“未归属”。
8. 钩子往回合里输出东西（模型看到钩子输出）。
--revision 在该版本源码上跑（修前包装脚本没有钩子）；--mutant 跑已知坏实现。
夹具用户启动 Codex 时用 `--sandbox danger-full-access -a never`：这里只看钩子与记录，不看 Codex 自己的沙箱与审批。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture  # noqa: E402
from t112_native_api import message_events, request_source, request_tools, shell_item, tool_events as custom_events  # noqa: E402

REQUEST_IDEATION = 'T-133 Codex：请申请构思主控'
REQUEST_EXECUTOR = 'T-133 Codex：请申请执行主控'
IDEA_PROMPT = 'T-133 Codex 用户对构思主控说：先看看哪些 ticket 就绪了'
QUESTION = '先做哪一个？'
CHOICE = 'T-1 先做'
RELEASE = 'T-133 Codex：请放弃构思主控身份'
AFTER_RELEASE = 'T-133 Codex：放弃身份之后说的话'
MODEL = 'gpt-6.1-sol'


def function_events(item, model):
    response = dict(id='resp_' + uuid.uuid4().hex, object='response', status='completed', model=model,
                    output=[item], usage={'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15})
    return [('response.created', {'response': dict(response, status='in_progress', output=[])}),
            ('response.output_item.added', {'output_index': 0, 'item': dict(item, arguments='', status='in_progress')}),
            ('response.function_call_arguments.delta', {'output_index': 0, 'item_id': item['id'], 'delta': item['arguments']}),
            ('response.function_call_arguments.done', {'output_index': 0, 'item_id': item['id'], 'arguments': item['arguments']}),
            ('response.output_item.done', {'output_index': 0, 'item': dict(item, status='completed')}),
            ('response.completed', {'response': response})]


def function_call(namespace, name, arguments):
    return dict(type='function_call', id='fc_' + uuid.uuid4().hex, call_id='call_t133_' + uuid.uuid4().hex,
                namespace=namespace, name=name, arguments=json.dumps(arguments, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['hooks-not-passed', 'post-hook-passed', 'reply-as-message'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[], observed={})
    patches = {
        # The shim starts Codex without Enchanted's hooks, as before.
        'hooks-not-passed': [('terminal/bin/codex', 'set -- -c "hooks.UserPromptSubmit=', 'true || set -- -c "hooks.UserPromptSubmit=')],
        # The shim also hands Codex a PostToolUse hook for the ask tool, as Claude's plugin does for AskUserQuestion: its
        # immediate {"accepted":true} then ends the wait before the user answers.
        'post-hook-passed': [('terminal/bin/codex', '-c "hooks.PreToolUse=', '-c "hooks.PostToolUse=[{matcher=\\"request_user_input_async\\",hooks=[$hook]}]" -c "hooks.PreToolUse=')],
        # The user's reply kept as an ordinary message.
        'reply-as-message': [('src/daemon.ts', 'const reply = codex ? codexQuestionReply(payload.prompt) : null;', 'const reply = null as any;')],
    }.get(args.mutant, [])

    api = dict(bodies=[], error=None, turns={})

    def user_texts(item):
        return '\n'.join(part.get('text', '') for part in item.get('content', []) if isinstance(part, dict))

    def plan(body):
        """One scripted step: the newest user message names the turn, the calls after it say how far it got."""
        items = body['input']
        users = [index for index, item in enumerate(items) if item.get('type') == 'message' and item.get('role') == 'user']
        text = user_texts(items[users[-1]])
        calls = [item for item in items[users[-1] + 1:] if item.get('type') in ('function_call', 'custom_tool_call')]
        tools = request_tools(body)

        def shell(command):
            item = shell_item(tools, command, fixture.repo)
            # `a2a request` waits for the user's decision; the cell must not yield before it returns.
            item['input'] = '// @exec: {"yield_time_ms": 120000}\n' + item['input'].replace('10000', '120000')
            return item

        for key, role in ((REQUEST_IDEATION, 'ideation'), (REQUEST_EXECUTOR, 'executor')):
            if key in text:
                return key, shell(f'a2a request {role}') if not calls else '已获批。'
        if IDEA_PROMPT in text:
            if not calls:
                return 'idea', function_call('functions', 'request_user_input_async', dict(questions=[dict(title=QUESTION, options=[CHOICE, 'T-2 先做'])]))
            return 'idea', function_call('clock', 'sleep', dict(duration_ms=300000))
        if CHOICE in text:
            return 'reply', shell('sleep 15') if not calls else '好的，先做 T-1。'
        if RELEASE in text:
            return 'release', shell('a2a release') if not calls else '已放弃。'
        assert AFTER_RELEASE in text, text[-300:]
        return 'after', '好的。'

    class Responses(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_GET(self):
            payload = json.dumps({'object': 'list', 'data': [{'id': MODEL, 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if request_source(body) == 'thread_title':
                    events = message_events(json.dumps({'title': 'T-133 Codex'}), body['model'])
                else:
                    api['bodies'].append(body)
                    key, step = plan(body)
                    api['turns'].setdefault(key, []).append(step if isinstance(step, str) else step.get('name'))
                    events = (message_events(step, body['model']) if isinstance(step, str) else
                              function_events(step, body['model']) if step['type'] == 'function_call' else
                              custom_events(step, body['model']))
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for sequence, (name, payload) in enumerate(events):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api['error'] = f'responses: {type(error).__name__}: {error}'
                self.send_error(500)

    fixture = Fixture('t133c-', lambda body: ('unused', [], ''), revision=args.revision, patches=patches)
    report['fixture'] = str(fixture.dir)
    responses = ThreadingHTTPServer(('127.0.0.1', 0), Responses)
    threading.Thread(target=responses.serve_forever, daemon=True).start()
    electron = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def wait(label, predicate, timeout=90):
        def probe():
            assert not api['error'], api['error']
            return predicate()
        return fixture.wait(label, probe, timeout)

    def database(query, *values):
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(query, values)]

    def terminal(name):
        launch = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        return dict(name=name, launch=launch, identity=window['identity'], sequence=0)

    def type_in(term, data):
        term['sequence'] += 1
        sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    def screen(term):
        raw = (fixture.state / 'traces' / term['launch'] / 'pty.raw').read_text(encoding='utf-8', errors='replace')
        return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

    # Codex draws its input box before the hook review, and redraws parts of lines in place, so the stripped screen
    # is matched on whole words that survive that ("Trust all and continue", the input box placeholder).
    TRUST = 'Trustallandcontinue'

    def ready(term, since=0):
        return 'AskCodextodoanything' in screen(term)[since:]

    def submit(term, text):
        type_in(term, text)
        time.sleep(1)
        type_in(term, '\r')

    def approve(card):
        electron.until('批准', f"(()=>{{const b=[...document.querySelectorAll('[data-role-request=\"{card}\"] button')].find(b=>b.textContent==='批准');"
                       "if(!b||b.disabled)return false;b.click();return true})()", 20)

    def agent(launch):
        return electron.evaluate(f"(()=>{{const r=document.querySelector('.agent-row[data-agent-launch=\"{launch}\"]');"
                                 "return r&&{state:r.dataset.agentState,parent:r.dataset.agentParent,level:r.dataset.agentLevel,role:r.querySelector('.agent-role').textContent}})()")

    def state_is(launch, value):
        return f"document.querySelector('.agent-row[data-agent-launch=\"{launch}\"]')?.dataset.agentState === {json.dumps(value)}"

    def seen(text):
        return any(text in json.dumps(body['input'], ensure_ascii=False) for body in api['bodies'])

    try:
        fixture.start(args.claude, {'README.md': 'demo\n'})
        # The fixture's own socket-only executor gives its role back, so the user's CLI can ask for it.
        assert fixture.request('role_release', fixture.terminal)['ok']
        # The fixture user's own Codex: its model provider, the project trusted, and a hook of their own.
        codex_home = fixture.home / '.codex'
        codex_home.mkdir()
        config = codex_home / 'config.toml'
        config.write_text('model_provider = "t133"\ncli_auth_credentials_store = "file"\ncheck_for_update_on_startup = false\n'
                          f'model = "{MODEL}"\nmodel_reasoning_effort = "low"\n'
                          f'[model_providers.t133]\nname = "T133 fixture"\nbase_url = "http://127.0.0.1:{responses.server_port}/v1"\n'
                          f'wire_api = "responses"\nrequires_openai_auth = false\n[projects.{json.dumps(str(fixture.repo))}]\ntrust_level = "trusted"\n',
                          encoding='utf-8')
        own_hook = fixture.out / 'user-own-hook.jsonl'
        (codex_home / 'hooks.json').write_text(json.dumps({'hooks': {'UserPromptSubmit': [{'hooks': [
            {'type': 'command', 'command': f"{{ cat; echo; }} >> '{own_hook}'", 'timeout': 10}]}]}}), encoding='utf-8')
        original_config = config.read_text(encoding='utf-8')

        electron = Electron(fixture, 't133c-' + fixture.dir.name[6:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")

        ideation = terminal('I')
        type_in(ideation, 'codex --sandbox danger-full-access -a never\r')
        wait('终端 I 的 Codex 启动', lambda: ready(ideation), 60)
        time.sleep(5)
        # Enchanted's hooks join the user's own one, all new to this Codex home: more than one hook to review
        # (with the user's hook alone, Codex says "1 hook is new or changed").
        asked = TRUST in screen(ideation) and 'hooksareneworchanged' in screen(ideation)
        before = config.read_text(encoding='utf-8')
        report['observed']['first_screen'] = screen(ideation)[-600:]
        check('codex_asks_to_trust_the_hooks', asked, report['observed']['first_screen'])
        # Codex itself appends its own UI state on start ([tui] screen_reader_detection_done); no trust exists before the user's choice.
        check('no_trust_before_the_user_chooses', before.startswith(original_config) and 'hooks' not in before, before)
        mark = len(screen(ideation))
        type_in(ideation, '\x1b[B')
        time.sleep(1)
        type_in(ideation, '\r')
        wait('终端 I 的 Codex 就绪', lambda: ready(ideation, mark), 30)
        trusted = config.read_text(encoding='utf-8')
        report['observed']['config_after_trust'] = trusted
        check('codex_keeps_the_trust_itself', all(f'[hooks.state."/<session-flags>/config.toml:{event}:0:0"]' in trusted
                                                  for event in ('user_prompt_submit', 'stop', 'pre_tool_use')), trusted)

        submit(ideation, REQUEST_IDEATION)
        request_card = electron.until('构思主控申请出现', "document.querySelector('[data-role-request]')?.dataset.roleRequest ?? null", 60)
        approve(request_card)
        electron.until('构思主控出现', f"!!document.querySelector('.agent-row[data-agent-launch=\"{ideation['launch']}\"]')", 40)
        electron.until('构思主控回合结束：空闲', state_is(ideation['launch'], 'idle'), 60)
        check('ideation_idle_after_first_turn', True)

        submit(ideation, IDEA_PROMPT)
        electron.until('问用户：等待用户回答', state_is(ideation['launch'], 'waiting_user_answer'), 60)
        # The ask tool returned accepted and the model went to sleep: the user has still not answered.
        wait('模型开始等待', lambda: 'sleep' in api['turns'].get('idea', []), 30)
        time.sleep(4)
        held = agent(ideation['launch'])
        electron.screenshot(fixture.out / '01-waiting-user-answer.png')
        check('still_waiting_after_accepted', held['state'] == 'waiting_user_answer', held)
        wait('问题显示在终端', lambda: QUESTION.replace(' ', '') in screen(ideation), 30)
        type_in(ideation, '\x1b[1;2D')
        time.sleep(2)
        type_in(ideation, '\r')
        time.sleep(2)
        if not seen(CHOICE):
            type_in(ideation, '\r')
        electron.until('答完跑命令：运行中', state_is(ideation['launch'], 'running'), 40)
        electron.screenshot(fixture.out / '02-running.png')
        check('ideation_running_after_answer', True)
        electron.until('回合结束：空闲', state_is(ideation['launch'], 'idle'), 60)
        check('ideation_idle_after_turn', True)

        executor = terminal('X')
        type_in(executor, 'codex --sandbox danger-full-access -a never\r')
        wait('终端 X 的 Codex 就绪', lambda: ready(executor), 60)
        time.sleep(5)
        report['observed']['second_screen'] = screen(executor)[-600:]
        check('trust_not_asked_again', TRUST not in screen(executor), report['observed']['second_screen'])
        submit(executor, REQUEST_EXECUTOR)
        request_card = electron.until('执行主控申请出现', "document.querySelector('[data-role-request]')?.dataset.roleRequest ?? null", 60)
        offered = electron.evaluate(f"(()=>{{const s=document.querySelector('[data-role-request-parent=\"{request_card}\"]');"
                                    "return s&&{value:s.value,options:[...s.options].map(o=>o.value)}})()")
        report['observed']['parent_choice'] = offered
        check('approval_offers_ideation_as_parent', offered and offered['value'] == ideation['launch'], offered)
        approve(request_card)
        electron.until('执行主控出现', f"!!document.querySelector('.agent-row[data-agent-launch=\"{executor['launch']}\"]')", 40)
        electron.until('执行主控回合结束', state_is(executor['launch'], 'idle'), 60)
        rows = {launch: agent(launch) for launch in (ideation['launch'], executor['launch'])}
        report['observed']['rows'] = rows
        electron.screenshot(fixture.out / '03-tree.png')
        check('executor_under_ideation', rows[executor['launch']]['parent'] == ideation['launch'] and rows[executor['launch']]['level'] == '1' and
              rows[ideation['launch']]['role'] == '构思主控' and rows[executor['launch']]['role'] == '执行主控', rows)

        submit(ideation, RELEASE)
        wait('身份已放弃', lambda: not any(a['id'] == ideation['launch'] for a in fixture.request('sidebar_snapshot')['agents']), 60)
        wait('放弃身份的回合结束', lambda: '已放弃。' in api['turns'].get('release', []), 30)
        time.sleep(3)
        submit(ideation, AFTER_RELEASE)
        wait('放弃之后的话送到模型', lambda: seen(AFTER_RELEASE), 60)
        time.sleep(3)

        stored = [json.loads(row['data']) for row in database("SELECT data FROM user_inputs WHERE json_extract(data,'$.target.project')='demo' ORDER BY rowid")]
        report['observed']['stored'] = [dict(id=i['id'], form=i['form'], channel=i['channel'], text=i['text'], reply_to=i['reply_to']) for i in stored]
        terminal_rows = [i for i in stored if i['channel'] == 'controller-terminal']
        check('only_approved_prompts_recorded', [(i['form'], i['text']) for i in terminal_rows] ==
              [('message', IDEA_PROMPT), ('answer', f'{QUESTION}：{CHOICE}'), ('message', RELEASE)] and
              not any(text in i['text'] for i in stored for text in (REQUEST_IDEATION, REQUEST_EXECUTOR, AFTER_RELEASE)), report['observed']['stored'])
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('记录页签', "!!document.querySelector('[data-records-tab]')", 20)
        electron.evaluate("document.querySelector('[data-records-tab]').click()")
        electron.until('记录表', f"document.querySelectorAll('.user-input-page tr[data-input-id]').length === {len(stored)}", 30)
        electron.screenshot(fixture.out / '04-records.png')
        listed = {row['id']: row['text'] for row in electron.evaluate("[...document.querySelectorAll('.user-input-page tr[data-input-id]')].map(r=>({id:r.dataset.inputId,text:r.innerText}))")}
        report['observed']['records_rows'] = listed
        check('records_page_shows_controller_prompts', all(i['id'] in listed and '主控终端提交' in listed[i['id']] and '构思主控' in listed[i['id']] and
                                                           i['text'].splitlines()[-1] in listed[i['id']] for i in terminal_rows), listed)

        own = [json.loads(line) for line in own_hook.read_text(encoding='utf-8').splitlines() if line.strip()] if own_hook.exists() else []
        report['observed']['user_own_hook_prompts'] = [row.get('prompt') for row in own]
        check('users_own_hook_still_runs', all(any(row.get('prompt') == text for row in own) for text in (REQUEST_IDEATION, IDEA_PROMPT, AFTER_RELEASE)),
              report['observed']['user_own_hook_prompts'])
        bodies = json.dumps([body['input'] for body in api['bodies']], ensure_ascii=False)
        check('hooks_do_not_touch_the_turn', IDEA_PROMPT in bodies and AFTER_RELEASE in bodies and 'hook_event_name' not in bodies, None)
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api_turns'] = api['turns']
        report['api_error'] = api['error']
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
            try:
                fixture.stop()
            finally:
                responses.shutdown()
                args.summary.parent.mkdir(parents=True, exist_ok=True)
                args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
