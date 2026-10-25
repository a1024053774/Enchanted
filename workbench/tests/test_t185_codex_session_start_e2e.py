"""T-185：Codex 项目终端开局就拿到 Enchanted 的开局说明（SessionStart 钩子），与 Claude 插件给的是同一份。真实后台、
项目终端（zsh 与包装脚本）、真实 Codex（交互模式，模型是本地脚本化的 Responses 接口），真实 Electron 窗口。夹具用户的
Codex 在隔离 home 里（不碰用户的 ~/.codex），自己的 hooks.json 里也有一个 SessionStart 钩子。

用户原话（2026-10-25，逐字）：“1. 查明一下 3.装上钩子  5.发新 release,产品页也更新  新票:增加 antigravity,opencode 的支持吧,
按理说应该不限 cli 的,但应该还要实测一下,”。ticket 验收：开局说明进入上下文；用户自己传的 -c 或配置仍优先。

场景（期望来自 ticket 与 T-181 的开局说明要点，不读被测代码的输出）：
1. 终端 A 里 `codex`。夹具用户信任钩子（隔离 home 里的一次性选择）后提交一句主控请求。Codex 发给模型的第一个请求里有
   开局说明（`a2a help`、`a2a request executor`、“Enchanted 工作台的项目终端”）；用户自己 hooks.json 的 SessionStart
   钩子也照常运行。
2. 终端 B 里用户自己传 `-c hooks.SessionStart=[…]`（他自己的开局钩子）。用户的这一项优先：他的钩子运行，Enchanted
   的开局说明不进上下文；Enchanted 的其他钩子不受影响（提交的主控请求照样被后台看到不在本测试范围）。

失败方式（先列再写）：
1. 包装脚本没把 SessionStart 交给 Codex：模型上下文里没有开局说明（修前 main 即如此）。
2. 钩子输出格式 Codex 不认：钩子跑了，内容没进上下文。
3. Enchanted 的 SessionStart 顶掉了用户 hooks.json 里自己的开局钩子。
4. 用户自己的 -c hooks.SessionStart 被 Enchanted 的同名项覆盖（变异 ours-after-user）。
5. 不是 Enchanted 终端（没有终端身份）时也往上下文里塞说明：已由 session-context 只在有身份时输出保证，T-181 已测。
--revision 在该版本源码上跑；--mutant 跑已知坏实现。
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import shutil
import sys
import threading
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture  # noqa: E402
from t112_native_api import message_events, request_source  # noqa: E402

PROMPT = '你来当执行主控，派两个 worker 并行做：一个生成 restock.md，一个在 README 里加用法说明。'
MODEL = 'gpt-6.1-sol'
USER_OWN = 'T185 用户自己的开局钩子'
USER_FLAG = 'T185 用户用 -c 传的开局钩子'
ORIENTATION = ('a2a help', 'a2a request executor', 'Enchanted 工作台的项目终端')


def start_hook(text):
    """A SessionStart hook of the user's own that adds `text` to the context."""
    payload = json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': text}}, ensure_ascii=False)
    return {'type': 'command', 'command': f"printf '%s\\n' '{payload}'", 'timeout': 10}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['ours-after-user'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[], failed=[], observed={})
    patches = {
        # Enchanted's SessionStart comes after the user's arguments, so it replaces the user's own -c of the same key.
        'ours-after-user': [('terminal/bin/codex', '  -c "hooks.PreToolUse=[{matcher=\\"request_user_input_async\\",hooks=[$hook]}]" "$@"',
                             '  -c "hooks.PreToolUse=[{matcher=\\"request_user_input_async\\",hooks=[$hook]}]" "$@" -c "hooks.SessionStart=[{hooks=[$start]}]"')],
    }.get(args.mutant, [])
    api = dict(bodies=[], error=None)

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
                    events = message_events(json.dumps({'title': 'T-185'}), body['model'])
                else:
                    api['bodies'].append(body)
                    events = message_events('好的。', body['model'])
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for sequence, (name, payload) in enumerate(events):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api['error'] = f'responses: {type(error).__name__}: {error}'
                self.send_error(500)

    fixture = Fixture('t185-', lambda body: ('unused', [], ''), revision=args.revision, patches=patches)
    report['fixture'] = str(fixture.dir)
    responses = ThreadingHTTPServer(('127.0.0.1', 0), Responses)
    threading.Thread(target=responses.serve_forever, daemon=True).start()
    electron = None

    def check(name, condition, detail=None):
        report['checks'].append(dict(name=name, ok=bool(condition), detail=detail))
        if not condition:
            report['failed'].append(name)

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

    TRUST = 'Trustallandcontinue'

    def first_request(term, command):
        """Start codex with `command`, trust the hooks as the fixture user, submit PROMPT; the model request it sends."""
        type_in(term, command + '\r')
        # New or changed hooks: Codex asks for review first. Hooks it already trusts (same definition): no question.
        fixture.wait(f'{term["name"]} 的 Codex 提示审查钩子或就绪', lambda: '2.Trustallandcontinue' in screen(term) or
                     ('AskCodextodoanything' in screen(term) and 'Codex(v' in screen(term) and 'loading' not in screen(term)[-300:]), 60)
        time.sleep(3)
        term['trust_asked'] = '2.Trustallandcontinue' in screen(term)
        if term['trust_asked']:
            # Codex 0.164 lists 1. Review hooks  2. Trust all and continue  3. Continue without trusting: the fixture user picks 2.
            type_in(term, '2')
            fixture.wait(f'{term["name"]} 选中“Trust all and continue”', lambda: '›2.Trustallandcontinue' in screen(term), 20)
            type_in(term, '\r')
            fixture.wait(f'{term["name"]} 的 Codex 就绪', lambda: 'AskCodextodoanything' in screen(term).split('Continuewithouttrusting')[-1], 60)
        count = len(api['bodies'])
        type_in(term, PROMPT); time.sleep(1); type_in(term, '\r')
        fixture.wait(f'{term["name"]} 的模型请求', lambda: any(PROMPT in json.dumps(b, ensure_ascii=False) for b in api['bodies'][count:]), 60)
        body = next(b for b in api['bodies'][count:] if PROMPT in json.dumps(b, ensure_ascii=False))
        (fixture.out / f'request-{term["name"]}.json').write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding='utf-8')
        return json.dumps(body, ensure_ascii=False)

    try:
        fixture.start(args.claude, {'README.md': 'demo\n'})
        codex_home = fixture.home / '.codex'
        codex_home.mkdir()
        (codex_home / 'config.toml').write_text(
            'model_provider = "t185"\ncli_auth_credentials_store = "file"\ncheck_for_update_on_startup = false\n'
            f'model = "{MODEL}"\nmodel_reasoning_effort = "low"\n'
            f'[model_providers.t185]\nname = "T185 fixture"\nbase_url = "http://127.0.0.1:{responses.server_port}/v1"\n'
            f'wire_api = "responses"\nrequires_openai_auth = false\n[projects.{json.dumps(str(fixture.repo))}]\ntrust_level = "trusted"\n',
            encoding='utf-8')
        (codex_home / 'hooks.json').write_text(json.dumps({'hooks': {'SessionStart': [{'hooks': [start_hook(USER_OWN)]}]}}, ensure_ascii=False),
                                               encoding='utf-8')

        electron = Electron(fixture, 't185-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")

        # 1. Plain `codex`.
        a = first_request(terminal('A'), 'codex --sandbox danger-full-access -a never')
        report['observed']['A_orientation'] = {k: k in a for k in ORIENTATION}
        check('orientation_in_codex_context', all(k in a for k in ORIENTATION), report['observed']['A_orientation'])
        check('user_hooks_json_session_start_still_runs', USER_OWN in a, USER_OWN in a)

        # 2. The user's own -c hooks.SessionStart wins over Enchanted's.
        flag_output = fixture.out / 'user-flag-start.json'
        flag_output.write_text(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': USER_FLAG}},
                                          ensure_ascii=False), encoding='utf-8')
        flag = f'hooks.SessionStart=[{{hooks=[{{type="command",command="cat {flag_output}",timeout=10}}]}}]'
        b = first_request(terminal('B'), 'codex --sandbox danger-full-access -a never -c ' + "'" + flag.replace("'", "'\\''") + "'")
        report['observed']['B'] = dict(user_flag=USER_FLAG in b, orientation={k: k in b for k in ORIENTATION})
        check('user_flag_session_start_runs', USER_FLAG in b, report['observed']['B'])
        check('user_flag_replaces_enchanted_session_start', 'Enchanted 工作台的项目终端' not in b, report['observed']['B'])
        electron.screenshot(fixture.out / 'finished.png')
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        report['api_error'] = api['error']
        if electron:
            electron.stop()
        fixture.stop()
        responses.shutdown()
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(dict(status=report['status'], failed=report['failed'], error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
