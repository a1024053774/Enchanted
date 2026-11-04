"""T-246（Codex 一侧）：普通终端的原生会话报告只属于报告它的进程。终端里的 Codex（外层，交互模式）用 shell 工具运行另一个
Codex（内层 `codex exec`，同样经过包装脚本、带 Enchanted 钩子）；内层的钩子带着内层的进程号和会话号到达后台，不能顶替外层的。
真实后台、私有 hc core、真实 Codex；模型是本地脚本化的 Responses 接口（没有真实模型回合），内层的模型请求由测试扣住。
夹具用户的 Codex 在隔离 home 里（不碰用户的 ~/.codex），信任钩子由用户在 Codex 自己的提示里选（同 T-133）。

预期来自 Codex 自己的记录：rollout 首行 session_meta 的 id；外层是含外层唯一标记的那份，内层是含内层标记而不含外层标记的那份。

失败方式（先列再写）：
1. 内层运行时，“复制深度链接”不可用或给出内层的会话。
2. 内层运行时，后台给这个终端的 native_session 是内层的会话。
3. 内层结束后仍是 1 或 2。
4. 后台重启后，按记录恢复出来的报告不是外层的。
5. 外层退出后，链接或终端状态仍给出外层的会话。
6.（T-247）外层交互式 Codex 的钩子根本报不来会话（钩子环境里没有 CODEX_THREAD_ID，按环境认不出是哪个 CLI）：失败于 1。
另记：内层 `codex exec` 的钩子到没到后台（到了才算测到了“内层报告”这一路）。

--mutant last-report 改为取最后到达的报告（应失败于 1）；--revision 跑修前版本；--probe 让钩子把它认出的 CLI、进程号、
CODEX_THREAD_ID 与最近四层祖先写进报告（只作诊断）。
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
from scripted_claude import Fixture  # noqa: E402
from t112_native_api import message_events, request_tools, shell_item, tool_events  # noqa: E402

MODEL = 'gpt-6.1-sol'
LAST_REPORT = [('src/byProcess.ts', 'const report = this.front && this.byPid.get(this.front.pid);', 'const report = [...this.byPid.values()].at(-1);'),
               ('src/byProcess.ts', 'return report && report.at >= this.front!.started ? report.value : null;', 'return report ? report.value : null;')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['last-report'])
    parser.add_argument('--probe', action='store_true', help='hooks also write what they resolved to <fixture>/hook-probe.jsonl')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[], observed={})
    marker = 'T246C-' + uuid.uuid4().hex[:12]
    outer_marker, inner_marker = marker + '-outer', marker + '-inner'
    api = dict(error=None, kinds=[])
    hold = threading.Event()
    held = []

    def texts(body):
        return json.dumps(body.get('input', []), ensure_ascii=False)

    def plan(body):
        items = body['input']
        users = [index for index, item in enumerate(items) if item.get('type') == 'message' and item.get('role') == 'user']
        calls = [item for item in items[users[-1] + 1:] if item.get('type') in ('function_call', 'custom_tool_call')]
        if outer_marker in texts(body):
            if calls:
                return '外层完成。'
            item = shell_item(request_tools(body), f"codex exec --skip-git-repo-check --sandbox danger-full-access '{inner_marker} 只回复 ok' < /dev/null",
                              fixture.repo)
            # The inner CLI runs until the test lets its turn reply; the cell must not yield before it returns.
            item['input'] = '// @exec: {"yield_time_ms": 180000}\n' + item['input'].replace('10000', '180000')
            return item
        assert inner_marker in texts(body), texts(body)[-300:]
        held.append(time.time())
        hold.wait(150)
        return 'ok'

    class Responses(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_GET(self):
            payload = json.dumps({'object': 'list', 'data': [{'id': MODEL, 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                metadata = json.loads(body.get('client_metadata', {}).get('x-codex-turn-metadata', '{}'))
                api['kinds'].append([metadata.get('request_kind'), metadata.get('thread_source')])
                if metadata.get('thread_source') == 'thread_title':
                    events = message_events(json.dumps({'title': 'T-246 Codex'}), body['model'])
                else:
                    step = plan(body)
                    events = message_events(step, body['model']) if isinstance(step, str) else tool_events(step, body['model'])
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for sequence, (name, payload) in enumerate(events):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api['error'] = f'responses: {type(error).__name__}: {error}'
                self.send_error(500)

    probe = Path('/private/tmp/t246c-hook-probe.jsonl')
    ANCHOR = '      if (socket && launch && token) await requestAt(socket, { command: "terminal_hook",'
    PROBE = [('src/terminalCli.ts', ANCHOR, f'      (await import("node:fs")).appendFileSync({json.dumps(str(probe))}, JSON.stringify({{ cli, pid, thread: process.env.CODEX_THREAD_ID ?? null, '
              'event: JSON.parse(Buffer.concat(chunks).toString("utf8")).hook_event_name, ancestors: ancestors().slice(0, 4) }) + "\\n");\n' + ANCHOR)]
    if args.probe:
        probe.unlink(missing_ok=True)
    fixture = Fixture('t246c-', lambda body: ('unused', [], ''), revision=args.revision,
                      patches=(LAST_REPORT if args.mutant else []) + (PROBE if args.probe else []))
    report['fixture'] = str(fixture.dir)
    responses = ThreadingHTTPServer(('127.0.0.1', 0), Responses)
    threading.Thread(target=responses.serve_forever, daemon=True).start()

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def wait(label, predicate, timeout=90):
        def probe():
            assert not api['error'], api['error']
            return predicate()
        return fixture.wait(label, probe, timeout)

    def strip(raw):
        return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

    try:
        fixture.start(args.claude, {'README.md': 'demo\n'})
        assert fixture.request('role_release', fixture.terminal)['ok']
        codex_home = fixture.home / '.codex'
        codex_home.mkdir()
        (codex_home / 'config.toml').write_text(
            'model_provider = "t246"\ncli_auth_credentials_store = "file"\ncheck_for_update_on_startup = false\n'
            f'model = "{MODEL}"\nmodel_reasoning_effort = "low"\n'
            f'[model_providers.t246]\nname = "T246 fixture"\nbase_url = "http://127.0.0.1:{responses.server_port}/v1"\n'
            f'wire_api = "responses"\nrequires_openai_auth = false\n[projects.{json.dumps(str(fixture.repo))}]\ntrust_level = "trusted"\n',
            encoding='utf-8')
        shell = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']
        launch = shell['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        sequence = 0

        def type_in(data):
            nonlocal sequence
            sequence += 1
            sent = fixture.request('window_input', window['identity'], sequence=sequence, request_id=str(uuid.uuid4()), data=data)
            assert sent['ok'], sent

        def screen():
            return strip((fixture.state / 'traces' / launch / 'pty.raw').read_text(encoding='utf-8', errors='replace'))

        def link():
            answer = fixture.request('native_link', fixture.operator, launch=launch)
            assert answer.get('ok'), answer
            return answer['link']

        def native():
            return fixture.request('pane_status', thread=shell['thread']).get('native_session')

        def sessions_with(text, without=None):
            # Codex's own records: the rollouts that carry this text; their first line's session_meta names the thread.
            found = set()
            for path in (codex_home / 'sessions').rglob('rollout-*.jsonl'):
                content = path.read_text(encoding='utf-8')
                if text in content and (without is None or without not in content):
                    first = json.loads(content.splitlines()[0])
                    if first.get('type') == 'session_meta':
                        found.add(first['payload']['id'])
            return sorted(found)

        def reported(session):
            with sqlite3.connect('file:' + str(fixture.state / 'state.sqlite3') + '?mode=ro', uri=True) as db:
                rows = db.execute("SELECT data FROM orchestration_events WHERE launch=? AND type='shell_native_session'", (launch,)).fetchall()
            return any(json.loads(row[0]).get('session') == session for row in rows)

        TRUST = 'Trustallandcontinue'
        type_in('codex --sandbox danger-full-access -a never\r')
        wait('外层 Codex 启动', lambda: 'AskCodextodoanything' in screen(), 60)
        time.sleep(5)
        if TRUST in screen():
            mark = len(screen())
            type_in('\x1b[B')
            time.sleep(1)
            type_in('\r')
            wait('外层 Codex 信任钩子后就绪', lambda: 'AskCodextodoanything' in screen()[mark:], 30)
        type_in(f'运行内层 Codex。{outer_marker}')
        time.sleep(1)
        type_in('\r')
        wait('内层的模型请求到了', lambda: held, 90)
        outer = wait('外层会话写进记录', lambda: (lambda found: found[0] if len(found) == 1 else None)(sessions_with(outer_marker)), 30)
        inner = wait('内层会话写进记录', lambda: (lambda found: found[0] if len(found) == 1 else None)(sessions_with(inner_marker, outer_marker)), 30)
        report['observed'].update(outer=outer, inner=inner)
        report['observed']['inner_hook_reached'] = bool(wait('内层的钩子到了后台', lambda: reported(inner), 30))

        during = link()
        report['observed'].update(during_link=during, during_native=native())
        check('during_inner_link_is_outer', during.get('available') and during.get('session') == outer, during)
        check('during_inner_native_is_outer', report['observed']['during_native'] == outer, report['observed']['during_native'])

        hold.set()
        wait('外层回复', lambda: screen().split(outer_marker, 1)[-1].count('外层完成。') >= 1, 120)
        time.sleep(2)
        after = link()
        report['observed'].update(after_link=after, after_native=native())
        check('after_inner_link_is_outer', after.get('available') and after.get('session') == outer, after)
        check('after_inner_native_is_outer', report['observed']['after_native'] == outer, report['observed']['after_native'])

        fixture.run_cli('daemon_stop')
        (fixture.dir / 'operator.json').rename(fixture.dir / 'operator-before-restart.json')
        fixture.run_cli('daemon_start', '--launch-config', str(fixture.dir / 'launch-config.json'))
        fixture.wait('后台恢复结束', lambda: fixture.request('pane_layout').get('recovering') is False, 30)
        fixture.operator = json.loads((fixture.dir / 'operator.json').read_text(encoding='utf-8'))
        restarted = link()
        report['observed'].update(restarted_link=restarted, restarted_native=native())
        check('after_restart_link_is_outer', restarted.get('available') and restarted.get('session') == outer, restarted)
        check('after_restart_native_is_outer', report['observed']['restarted_native'] == outer, report['observed']['restarted_native'])

        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        sequence = 0
        type_in('/exit')
        time.sleep(1)
        type_in('\r')
        exit_typed = time.time()
        fixture.wait('外层会话从终端状态清掉', lambda: native() is None, 30)
        report['observed']['native_cleared_after_s'] = round(time.time() - exit_typed, 2)
        check('native_cleared_within_recheck', report['observed']['native_cleared_after_s'] <= 10, report['observed']['native_cleared_after_s'])
        exited = fixture.wait('外层退出后前台为空', lambda: (lambda value: value if value['cli'] is None else None)(link()), 30)
        check('after_exit_unavailable', exited['available'] is False, exited)
        report['status'] = 'PASS'
    except Exception as error:
        report.update(status='INCOMPLETE', error=f'{type(error).__name__}: {error}')
        try:
            report['observed']['last_screen'] = screen()[-1500:]
        except Exception as screen_error:  # the screen is evidence only; its absence must not hide the first error
            report['observed']['last_screen_error'] = repr(screen_error)
    finally:
        hold.set()
        report['observed']['request_kinds'] = api['kinds']
        if args.probe and probe.exists():
            report['observed']['hook_probe'] = [json.loads(line) for line in probe.read_text(encoding='utf-8').splitlines()]
            probe.unlink()
        try:
            fixture.stop()
            report['core_cleanup'] = fixture.core_cleanup
        except AssertionError as error:
            report.update(status='INCOMPLETE', residue=str(error))
        responses.shutdown()
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        if report['status'] == 'PASS':
            shutil.rmtree(fixture.dir)
    print(json.dumps({'status': report['status'], 'checks': report['checks'], 'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
