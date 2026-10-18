"""Protected U/D/S/M fixtures; never a vendor CLI or real auth source."""
import argparse
import errno
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import TCPServer

HERE = Path(__file__).resolve().parent

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value

runtime = module('login_session', HERE.parent / 'src/claudeLoginSession.py')
probe = module('parent_probe', HERE / 'probe_t093_parent_sandbox.py')
checks = module('parallel_probe', HERE / 'probe_t093_parallel_profiles.py')

class LocalServer(HTTPServer):
    def server_bind(self):
        TCPServer.server_bind(self)
        self.server_name = 'local-fixture'; self.server_port = self.server_address[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--role', choices=('U','F','D','S','M'), required=True)
    args = parser.parse_args()
    session = runtime.read(args.session)
    runtime.arm_deadline(session['deadline'] + 5)
    fixture = runtime.read(Path(session['private_root']) / 'fixture.json')
    root, role = Path(fixture['root']), args.role
    own = {'pid': os.getpid(), 'ppid': os.getppid(), 'pgrp': os.getpgrp(), 'profile': role}
    guard = probe.attempt(Path(session['real_home']))
    if role in ('S','M'):
        synthetic = probe.attempt(root / 'synthetic-home')
        primary = None if synthetic['denied'] and synthetic['absent_after'] else 'home_write_must_be_denied'
        runtime.save(root / role / 'result.json', {**own, 'real_home_write': guard, 'synthetic_write': synthetic, 'primary_failure': primary})
        return 2 if primary else 0
    directory = Path(session['metadata_directory']) if role == 'D' else Path(session['forwarder_directory']) if role == 'F' else root / 'U'
    security = checks.mach_denials()
    fork = checks.fork_denied()
    runtime.save(directory / ('python-guards.json' if role == 'F' else 'guards.json'), {**own, 'real_home_write': guard, 'security': security, 'fork': fork})
    # The real cleanup owner must run even when a boundary assertion will
    # fail. C judges these observations before dispatching any fixture turn.
    if role == 'D': return runtime.metadata_service(session)
    if not guard['denied'] or not checks.security_denied(security) or not fork['denied']:
        return 2
    if role == 'F':
        os.execve(runtime.NODE, [runtime.NODE, str(HERE / 't093_forwarder_guard.ts'), str(args.session)], {'PATH':'/usr/bin:/bin','LANG':'C'})
    token = runtime.read(Path(session['private_root']) / 'home/.claude/.credentials.json')['claudeAiOauth']['accessToken']
    received = []
    ledger = Path(session['forwarder_directory']) / 'journal/requests.jsonl'
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            sequence = len(received) + 1
            rows = [json.loads(line) for line in ledger.read_text().splitlines() if line]
            count = sum(row.get('kind') == 'request' for row in rows)
            size = int(self.headers.get('content-length', '0'))
            body = self.rfile.read(min(size, 1024 * 1024 + 1))
            valid = size <= 1024 * 1024 and isinstance(json.loads(body).get('messages'), list)
            status = 400 if sequence == 1 else 200
            received.append({'sequence': sequence, 'method': self.command, 'path': self.path,
                             'bearer_matches_copy': self.headers.get('authorization') == 'Bearer ' + token,
                             'messages_present': valid, 'prompt_matches_fixture': valid and json.loads(body)['messages'][0].get('content') == fixture['prompt'], 'recorded_before_receipt': count == sequence,
                             'ledger_request_count_at_receipt': count, 'status': status})
            # The receipt is independent of the forwarding implementation. A
            # missing row is reported by C's business assertion, not hidden by
            # an unrelated fixture exception or an early failed model response.
            (root / 'U/received.json').write_text(json.dumps(received))
            self.send_response(status); self.send_header('Content-Length','2'); self.end_headers(); self.wfile.write(b'{}')
        def log_message(self, *args): pass
    servers = []
    try:
        for port in (fixture['upstream_port'], fixture['other_port']):
            server = LocalServer(('127.0.0.1', port), Handler); server.timeout = 2; servers.append(server)
        runtime.save(root / 'U/ready.json', own)
        while not (root / 'U/stop').exists() and time.time() < session['deadline']:
            ready,_,_ = select.select(servers,[],[],.03)
            for server in ready: server.handle_request()
    finally:
        for server in servers: server.server_close()
    runtime.save(root / 'U/closed.json', {**own, 'received': received})
    return 0

if __name__ == '__main__': raise SystemExit(main())
