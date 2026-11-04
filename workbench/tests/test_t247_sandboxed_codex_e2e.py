"""T-247：普通终端里以 Codex 沙箱模式（workspace-write、read-only）运行的交互式 Codex，钩子照样报来自己的会话与回合状态。
真实后台、私有 hc core、真实 Codex；模型是本地脚本化的 Responses 接口；Codex 在夹具的隔离 home 里（不碰用户的 ~/.codex）。
预期来自 Codex 自己的记录：rollout 首行 session_meta 的 id（含本次唯一标记的那份）。

失败方式（先列再写）：
1. 钩子在沙箱里读不到进程关系（ps 不能执行），认不出是哪个 CLI：链接不可用、native_session 为空。
2. 回合结束后后台给这个终端的回合状态不是空闲（hook_turn）。
3. 退出后链接仍给出这次会话。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Fixture  # noqa: E402
from t112_native_api import message_events, tool_events  # noqa: E402

MODEL = 'gpt-6.1-sol'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    parser.add_argument('--sandbox', choices=['workspace-write', 'read-only'], required=True)
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, sandbox=args.sandbox, checks=[], observed={})
    marker = 'T247S-' + uuid.uuid4().hex[:12]
    api = dict(error=None, kinds=[])

    def texts(body):
        return json.dumps(body.get('input', []), ensure_ascii=False)

    def plan(body):
        assert marker in texts(body), texts(body)[-300:]
        return '沙箱里完成。'

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
                    events = message_events(json.dumps({'title': 'T-247 Codex'}), body['model'])
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

    fixture = Fixture('t247s-', lambda body: ('unused', [], ''), revision=args.revision)
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
            'model_provider = "t247"\ncli_auth_credentials_store = "file"\ncheck_for_update_on_startup = false\n'
            f'model = "{MODEL}"\nmodel_reasoning_effort = "low"\n'
            f'[model_providers.t247]\nname = "T247 fixture"\nbase_url = "http://127.0.0.1:{responses.server_port}/v1"\n'
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

        def sessions_with(text):
            # Codex's own records: the rollout that carries this text; its first line's session_meta names the thread.
            found = set()
            for path in (codex_home / 'sessions').rglob('rollout-*.jsonl'):
                content = path.read_text(encoding='utf-8')
                first = json.loads(content.splitlines()[0])
                if text in content and first.get('type') == 'session_meta':
                    found.add(first['payload']['id'])
            return sorted(found)

        TRUST = 'Trustallandcontinue'
        type_in(f'codex --sandbox {args.sandbox} -a never\r')
        wait('外层 Codex 启动', lambda: 'AskCodextodoanything' in screen(), 60)
        time.sleep(5)
        if TRUST in screen():
            mark = len(screen())
            type_in('\x1b[B')
            time.sleep(1)
            type_in('\r')
            wait('外层 Codex 信任钩子后就绪', lambda: 'AskCodextodoanything' in screen()[mark:], 30)
        type_in(f'只回复一句。{marker}')
        time.sleep(1)
        type_in('\r')
        wait('回复', lambda: screen().split(marker, 1)[-1].count('沙箱里完成。') >= 1, 90)
        session = wait('会话写进记录', lambda: (lambda found: found[0] if len(found) == 1 else None)(sessions_with(marker)), 30)
        report['observed']['session'] = session
        turn = wait('回合状态回到空闲', lambda: (lambda value: value if value and value.get('state') == 'idle' else None)(
            fixture.request('pane_status', thread=shell['thread']).get('hook_turn')), 15)
        report['observed']['hook_turn'] = turn
        check('turn_idle_after_reply', turn['cli'] == 'codex', turn)
        after = link()
        report['observed'].update(after_link=after, after_native=native())
        check('link_is_the_session', after.get('available') and after.get('session') == session, after)
        check('native_is_the_session', report['observed']['after_native'] == session, report['observed']['after_native'])

        fixture.run_cli('daemon_stop')
        (fixture.dir / 'operator.json').rename(fixture.dir / 'operator-before-restart.json')
        fixture.run_cli('daemon_start', '--launch-config', str(fixture.dir / 'launch-config.json'))
        fixture.wait('后台恢复结束', lambda: fixture.request('pane_layout').get('recovering') is False, 30)
        fixture.operator = json.loads((fixture.dir / 'operator.json').read_text(encoding='utf-8'))
        restarted = link()
        report['observed'].update(restarted_link=restarted, restarted_native=native())
        check('after_restart_link_is_the_session', restarted.get('available') and restarted.get('session') == session, restarted)
        check('after_restart_native_is_the_session', report['observed']['restarted_native'] == session, report['observed']['restarted_native'])

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
        report['observed']['request_kinds'] = api['kinds']
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
