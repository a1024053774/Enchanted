"""T-167 事实探针：真实 Codex CLI 在额度接近上限时，回合结束后是否弹出换模型提示，
提示期间写入的粘贴与回车是否被提示吃掉、不开始新回合。

真实 Codex CLI（隔离 /tmp CODEX_HOME，不复制 auth.json），模型端为本地脚本化 Responses，
响应头带 x-codex-primary-used-percent。不调用厂商模型，不读写用户 ~/.codex。
--hide-nudge 在启动参数加 notice.hide_rate_limit_model_nudge=true（候选修法）。
用法：python3 probe_codex_nudge.py --out <新目录> [--used 94] [--hide-nudge]
"""
import argparse
import json
import os
from pathlib import Path
import pty
import re
import select
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'workbench/tests'))
from t112_native_api import message_events, request_source  # noqa: E402

MODEL = 'gpt-6.1-sol'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--used', type=int, default=94)
    parser.add_argument('--hide-nudge', action='store_true')
    parser.add_argument('--codex', default=shutil.which('codex'))
    args = parser.parse_args()
    args.out.mkdir(parents=True)
    root = Path(os.path.realpath('/private/tmp')) / ('t167-probe-' + args.out.name)
    root.mkdir()
    home, repo = root / 'codex-home', root / 'repo'
    home.mkdir(); repo.mkdir()
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    bodies = []

    class Responses(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_GET(self):
            payload = json.dumps({'object': 'list', 'data': [{'id': MODEL, 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if request_source(body) != 'thread_title':
                bodies.append(body)
            text = 'T167 收到第 %d 条。' % len(bodies)
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('x-codex-primary-used-percent', str(args.used))
            self.send_header('x-codex-primary-window-minutes', '10080')
            self.send_header('x-codex-primary-reset-at', str(int(time.time()) + 86400))
            self.end_headers()
            for sequence, (name, payload) in enumerate(message_events(text, body.get('model', MODEL))):
                self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
            self.wfile.flush()

    server = ThreadingHTTPServer(('127.0.0.1', 0), Responses)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    (home / 'config.toml').write_text(
        f'model_provider = "t167"\nmodel = "{MODEL}"\nmodel_reasoning_effort = "high"\ncheck_for_update_on_startup = false\n'
        f'[model_providers.t167]\nname = "T167 fixture"\nbase_url = "http://127.0.0.1:{server.server_port}/v1"\n'
        f'wire_api = "responses"\nrequires_openai_auth = false\n[projects.{json.dumps(str(repo))}]\ntrust_level = "trusted"\n', encoding='utf-8')
    argv = [args.codex, '-c', 'check_for_update_on_startup=false']
    if args.hide_nudge:
        argv += ['-c', 'notice.hide_rate_limit_model_nudge=true']
    env = dict(os.environ, CODEX_HOME=str(home), TERM='xterm-256color')
    report = dict(argv=argv, used_percent=args.used, codex_version=subprocess.check_output([args.codex, '--version'], text=True).strip(),
                  model_backend='local scripted Responses', vendor_model_turns=0, writes=[], checks={})
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(repo)
        os.execvpe(argv[0], argv, env)
    import fcntl, termios, struct
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', 45, 160, 0, 0))
    screen = bytearray()

    def pump(seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            ready, _, _ = select.select([fd], [], [], 0.05)
            if ready:
                try:
                    data = os.read(fd, 65536)
                except OSError:
                    return
                screen.extend(data)
                # Answer terminal queries the way xterm.js would, so the TUI starts.
                if b'\x1b[6n' in data:
                    os.write(fd, b'\x1b[1;1R')
                if b'\x1b[c' in data or b'\x1b[0c' in data:
                    os.write(fd, b'\x1b[?62;22c')

    def text():
        return re.sub(r'\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b.', '', screen.decode('utf-8', 'replace'))

    def write(label, data):
        report['writes'].append(dict(label=label, at=time.time(), data=data[:80]))
        os.write(fd, data.encode())

    def wait_for(predicate, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            pump(0.2)
            if predicate():
                return True
        return False

    try:
        report['checks']['tui_ready'] = wait_for(lambda: 'T167' in text() or '›' in text() or 'context left' in text(), 30)
        pump(2)
        write('first-paste', '\x1b[200~第一条任务\x1b[201~')
        pump(0.3)
        write('first-enter', '\r')
        report['checks']['first_turn_answered'] = wait_for(lambda: len(bodies) >= 1 and 'T167 收到第 1 条' in text(), 30)
        mark = len(screen)
        # As drain() does at Stop: paste the gate receipt at once, then Enter 300 ms later.
        write('receipt-paste', '\x1b[200~⟦门禁 #3⟧ 请仅确认收到并结束。\x1b[201~')
        pump(0.3)
        write('receipt-enter', '\r')
        report['checks']['receipt_turn_started'] = wait_for(lambda: len(bodies) >= 2, 15)
        after = re.sub(r'\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b.', '', screen[mark:].decode('utf-8', 'replace'))
        report['checks']['nudge_shown'] = 'Approaching rate limits' in text() or 'lower credit usage' in text()
        report['requests'] = [dict(model=b.get('model'), effort=(b.get('reasoning') or {}).get('effort')) for b in bodies]
        report['screen_after_receipt_tail'] = after[-3000:]
    finally:
        try:
            os.kill(pid, 9)
        except ProcessLookupError:
            pass
        server.shutdown()
        (args.out / 'pty.raw').write_bytes(bytes(screen))
        (args.out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        sessions = sorted((home / 'sessions').rglob('*.jsonl')) if (home / 'sessions').exists() else []
        for index, path in enumerate(sessions):
            shutil.copy(path, args.out / f'rollout-{index}.jsonl')
        shutil.rmtree(root)
    print(json.dumps(dict(checks=report['checks'], requests=report.get('requests')), ensure_ascii=False))


if __name__ == '__main__':
    main()
