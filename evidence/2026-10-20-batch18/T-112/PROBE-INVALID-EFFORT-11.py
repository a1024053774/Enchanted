"""Measure installed interactive CLI effort handling with a credential-free local API.
No tools, model calls or global writes. HTTP 200 is permissive, not a real API oracle.
"""
import argparse, fcntl, json, os, pty, select, shutil, signal, struct, subprocess, sys, tempfile, termios, threading, time, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
source = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(source / 'workbench/tests'))
from t112_native_api import request_source, message_events
parser = argparse.ArgumentParser()
parser.add_argument('--summary', type=Path, required=True)
args = parser.parse_args()
assert not args.summary.exists()
root = Path(tempfile.mkdtemp(prefix='t112-invalid-effort-', dir='/private/tmp'))
report = dict(status='INCOMPLETE', classification=None, http_status=200,
              model_calls_by_fixture=0, vendor_egress_observed=None, requests=[], api_errors=[])
server = child = None
master = slave = None
screen = bytearray()
marker = 'T112_INVALID_EFFORT_RESPONSE_COMPLETE'
try:
    for name in ('home', 'codex', 'candidate'):
        (root / name).mkdir()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args): pass
        def do_POST(self):
            try:
                raw = self.rfile.read(int(self.headers['Content-Length'])).decode()
                body = json.loads(raw)
                kind = request_source(body)
                report['requests'].append(dict(path=self.path, raw_body=raw, thread_source=kind))
                assert kind in ('user', 'thread_title') and len(report['requests']) <= 4
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.end_headers()
                reply = marker if kind == 'user' else json.dumps({'title': 'T112 invalid effort'})
                for index, (name, payload) in enumerate(message_events(reply, body['model'])):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=index, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                report['api_errors'].append(str(error))
                self.send_error(500)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = False
    threading.Thread(target=server.serve_forever, daemon=True).start()
    config = ('model_provider="t112_fixture"\ncli_auth_credentials_store="file"\n'
        '[model_providers.t112_fixture]\nname="local diagnostic"\nbase_url="http://127.0.0.1:' + str(server.server_port) + '/v1"\n'
        'wire_api="responses"\nrequires_openai_auth=false\n[projects.' + json.dumps(str(root / 'candidate')) + ']\ntrust_level="trusted"\n')
    (root / 'codex/config.toml').write_text(config)
    env = {key: value for key, value in os.environ.items() if key in ('PATH', 'LANG', 'LC_CTYPE', 'TMPDIR', 'USER', 'LOGNAME')}
    env.update(HOME=str(root / 'home'), CODEX_HOME=str(root / 'codex'), LC_ALL='C', TERM='xterm-256color')
    binary = '/Users/luckye/.codex/packages/app-server-daemon/releases/0.162.1-aarch64-apple-darwin/bin/codex'
    version = subprocess.run([binary, '--version'], env=env, capture_output=True, text=True)
    report['version'] = dict(argv=[binary, '--version'], exit=version.returncode, stdout=version.stdout, stderr=version.stderr)
    assert version.returncode == 0 and version.stdout.strip() == 'codex-cli 0.162.1'
    argv = [binary, '--no-daemon', '--no-alt-screen', '-C', str(root / 'candidate'), '-m', 'gpt-6.1-sol', '-a', 'never', '--sandbox', 'workspace-write',
            '-c', 'check_for_update_on_startup=false', '-c', 'model_reasoning_effort="unsupported-t112"',
            '只回答固定文本，不执行工具；本地假 API 协议诊断。']
    report.update(argv=argv, isolated_config=config)
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 40, 160, 0, 0))
    child = subprocess.Popen(argv, env=env, cwd=root / 'candidate', stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
    os.close(slave); slave = None
    deadline = time.monotonic() + 35
    while True:
        if select.select([master], [], [], .05)[0]:
            try: chunk = os.read(master, 65536)
            except OSError: chunk = b''
            screen.extend(chunk)
            for query, reply in [(b'\x1b[6n', b'\x1b[1;1R'), (b'\x1b[c', b'\x1b[?1;2c'), (b'\x1b[>c', b'\x1b[>0;0;0c'), (b'\x1b[?u', b'\x1b[?0u')]:
                if query in chunk: os.write(master, reply)
        assert not report['api_errors'], report['api_errors']
        if child.poll() is not None:
            report['natural_exit'] = child.returncode
            assert child.returncode != 0 and not report['requests'], 'Unexpected CLI exit'
            report['classification'] = 'cli_rejects_at_startup'
            break
        roots = [json.loads(row['raw_body']) for row in report['requests'] if row['thread_source'] == 'user']
        if roots and marker.encode() in screen:
            report['wire_effort'] = roots[0].get('reasoning', {}).get('effort')
            report['classification'] = ('cli_accepts_and_forwards_unchanged' if report['wire_effort'] == 'unsupported-t112'
                                        else 'cli_changes_or_omits_effort')
            break
        assert time.monotonic() < deadline, 'Native diagnostic deadline'
    report['status'] = 'PASS'
except Exception as error:
    report.update(error=str(error), traceback=traceback.format_exc())
finally:
    if child is not None:
        report['alive_before_cleanup'] = child.poll() is None
        if child.poll() is None:
            assert os.getpgid(child.pid) == child.pid
            os.killpg(child.pid, signal.SIGTERM)
            try: child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                assert child.poll() is None and os.getpgid(child.pid) == child.pid
                os.killpg(child.pid, signal.SIGKILL); child.wait(timeout=5)
        report['cleanup'] = dict(pid=child.pid, reaped=child.poll() is not None, exit=child.returncode)
    for fd in (master, slave):
        if fd is not None: os.close(fd)
    if server:
        server.shutdown(); server.server_close()
    report['terminal_raw'] = screen.decode('utf-8', errors='replace')
    report['native_logs'] = [dict(path=str(path.relative_to(root)), raw=path.read_text()) for path in (root / 'codex/sessions').rglob('*.jsonl')]
    if report['api_errors']: report['status'] = 'INCOMPLETE'
    shutil.rmtree(root)
    report['fixture_removed'] = not root.exists()
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], classification=report['classification'], summary=str(args.summary))))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
