"""Exercise the actual fake-API POST handler without HTTP sockets or a CLI."""
import argparse
import ast
import io
import json
import tempfile
import time
from email.message import Message
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(); args.output.mkdir()
source = Path(__file__).with_name('t078_fake_messages.py').read_bytes()
tree = ast.parse(source)
handler = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Handler')

class MemoryHTTP:
    def send_error(self, status): self.status = status
    def send_response(self, status): self.status = status
    def send_header(self, *args): pass
    def end_headers(self): pass

cases = [
    ('bearer_accepted', {'Authorization': 'Bearer a2a-fixture-key-not-a-secret'}, 200),
    ('api_key_without_bearer_rejected', {'x-api-key': 'a2a-fixture-key-not-a-secret'}, 401),
    ('wrong_bearer_rejected', {'Authorization': 'Bearer wrong', 'x-api-key': 'a2a-fixture-key-not-a-secret'}, 401),
    ('mixed_credentials_rejected', {'Authorization': 'Bearer a2a-fixture-key-not-a-secret', 'x-api-key': 'a2a-fixture-key-not-a-secret'}, 401),
]
results = []
for name, headers, expected in cases:
    root = Path(tempfile.mkdtemp(prefix='t078-2-handler-', dir='/tmp')).resolve()
    # Release is a fixture file only; the server's real lifecycle is not run.
    (root / 'api-release').write_text('fixture', encoding='utf-8')
    context = {'BaseHTTPRequestHandler': MemoryHTTP, 'root': root, 'messages': 0,
               'nonce': 'P1_AUTH_SENTINEL', 'json': json, 'time': time}
    exec(compile(ast.Module(body=[handler], type_ignores=[]), 'actual_fake_api_handler', 'exec'), context)
    request = context['Handler']()
    request.headers = Message()
    for key, value in headers.items(): request.headers[key] = value
    body = json.dumps({'stream': True, 'messages': [{'role': 'user', 'content': 'P1_AUTH_SENTINEL'}]}).encode()
    request.headers['Content-Length'] = str(len(body)); request.path = '/v1/messages'
    request.rfile = io.BytesIO(body); request.wfile = io.BytesIO(); request.status = None
    request.do_POST()
    accepted = (root / 'api-request.json').exists()
    passed = request.status == expected and accepted == (expected == 200)
    results.append({'name': name, 'status': 'PASS' if passed else 'INCOMPLETE', 'expected_status': expected,
                    'observed_status': request.status, 'request_recorded': accepted, 'root': str(root)})
record = {'status': 'PASS' if all(r['status'] == 'PASS' for r in results) else 'INCOMPLETE', 'checks': results,
          'argv': __import__('sys').argv, 'scope': 'Actual POST method with in-memory streams; no HTTP transport or CLI proof',
          'real_cli_starts': 0, 'api_starts': 0, 'real_vendor_model_turns': 0}
with (args.output / 'results.json').open('x', encoding='utf-8') as output:
    json.dump(record, output, ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False)); raise SystemExit(0 if record['status'] == 'PASS' else 1)
