"""Protected U/D/S/M fixtures; never a vendor CLI or real auth source."""
import argparse
import errno
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
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

def inspect_request(body,expected,raw_prompt):
    try:payload=json.loads(body)
    except (ValueError,UnicodeError):return {'messages_present':False,'prompt_matches_fixture':False,'structure':{'json_valid':False,'body_bytes':len(body)}}
    messages=payload.get('messages') if isinstance(payload,dict) else None
    first=messages[0] if isinstance(messages,list) and messages and isinstance(messages[0],dict) else {}
    content=first.get('content');expected_content=expected['messages'][0]['content']
    valid=len(body)<=1024*1024 and isinstance(messages,list)
    return {'messages_present':valid,'prompt_matches_fixture':valid and payload==expected,
            'structure':{'json_valid':True,'body_keys_exact':isinstance(payload,dict) and payload.keys()==expected.keys(),
                         'message_count':len(messages) if isinstance(messages,list) else None,
                         'first_message_keys_exact':first.keys()==expected['messages'][0].keys(),
                         'role_exact':first.get('role')==expected['messages'][0]['role'],
                         'content_type':type(content).__name__,'content_exact':content==expected_content,
                         'unwrapped_content_exact':content==raw_prompt,
                         'content_codepoints':len(content) if isinstance(content,str) else None,
                         'expected_content_codepoints':len(expected_content),'body_bytes':len(body),
                         'expected_body_bytes':len(json.dumps(expected).encode('utf-8'))}}


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
    guards={**own, 'real_home_write': guard, 'security': security, 'fork': fork}
    if role=='D':
        denied={'denied':False,'bytes_read':0}
        try:
            descriptor=os.open(root/'source-home/.claude/.credentials.json',os.O_RDONLY|os.O_NOFOLLOW)
            os.close(descriptor)
        except OSError as error:denied.update(denied=error.errno in (errno.EPERM,errno.EACCES),errno=error.errno)
        guards['source_content_read']=denied
    runtime.save(directory / ('python-guards.json' if role == 'F' else 'guards.json'), guards)
    # The real cleanup owner must run even when a boundary assertion will
    # fail. C judges these observations before dispatching any fixture turn.
    if role == 'D':
        code=runtime.metadata_service(session)
        runtime.arm_deadline(session['deadline']+30)
        source=root/'source-home';directory=Path(session['metadata_directory'])
        # The C driver must durably publish its primary checkpoint before
        # this independent owner removes the C-protected authentication source.
        while not (directory/'source-cleanup-permit.json').exists():time.sleep(.03)
        permit=runtime.read(directory/'source-cleanup-permit.json')
        checkpoint=runtime.read(fixture['output'])
        if permit.get('output')!=fixture['output'] or permit.get('candidate')!=fixture['candidate'] or checkpoint.get('candidate')!=fixture['candidate'] or checkpoint.get('fixture_root')!=str(root) or checkpoint.get('phase')!='cleanup_pending':
            raise ValueError('source_cleanup_requires_durable_checkpoint')
        result={**own,'profile':'D test source cleanup','source_home':str(source),'removed':False,'credential_body_read':False,'checkpoint_sequence':checkpoint.get('checkpoint_sequence')}
        if source.parent!=root or root.parent!=Path('/private/tmp') or not root.name.startswith('t093-chain-') or source.is_symlink() or Path(session['credential_home'])!=source:raise ValueError('synthetic_source_scope_required')
        try:shutil.rmtree(source);result['removed']=not source.exists()
        except OSError as error:result.update(error_type=type(error).__name__,errno=error.errno,path=error.filename)
        runtime.save(directory/'source-home-removed.json',result)
        return code if result['removed'] else 2
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
            inspected=inspect_request(body,fixture['expected_request_body'],fixture['prompt'])
            status = 400 if sequence == 1 else 200
            received.append({'sequence': sequence, 'method': self.command, 'path': self.path,
                             'bearer_matches_copy': self.headers.get('authorization') == 'Bearer ' + token,
                             **inspected,'recorded_before_receipt': count == sequence,
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
