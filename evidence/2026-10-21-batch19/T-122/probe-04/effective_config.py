"""T-122 probe 04: record the sandbox filesystem config Claude Code reports in its own system
prompt, through a local endpoint that answers end_turn. Usage: [PROBE_SOURCES=<value>] effective_config.py <run dir> <settings.json>"""
import json, os, re, subprocess, sys, threading, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
run, settings = sys.argv[1], open(sys.argv[2]).read()
seen = []
class Api(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.path.startswith('/v1/messages/count_tokens'):
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"input_tokens":1}'); return
        seen.append(body)
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
        for kind, value in [('message_start', {'message': {'id': 'm', 'type': 'message', 'role': 'assistant', 'model': body['model'], 'content': [], 'stop_reason': None, 'usage': {'input_tokens': 1, 'output_tokens': 0}}}),
                            ('content_block_start', {'index': 0, 'content_block': {'type': 'text', 'text': ''}}),
                            ('content_block_delta', {'index': 0, 'delta': {'type': 'text_delta', 'text': 'ok'}}),
                            ('content_block_stop', {'index': 0}),
                            ('message_delta', {'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 1}}),
                            ('message_stop', {})]:
            self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps({'type': kind, **value}) + '\n\n').encode())
server = ThreadingHTTPServer(('127.0.0.1', 0), Api); threading.Thread(target=server.serve_forever, daemon=True).start()
env = dict(os.environ, ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}', ANTHROPIC_AUTH_TOKEN='probe-not-a-secret')
env.pop('ANTHROPIC_API_KEY', None)
result = subprocess.run(['claude', '-p', '--session-id', str(uuid.uuid4()), '--model', 'claude-haiku-5-5', '--permission-mode', 'dontAsk',
                '--setting-sources', os.environ.get('PROBE_SOURCES', 'local'), '--strict-mcp-config', '--settings', settings, 'hi'], cwd=f'{run}/wt', env=env, capture_output=True, timeout=120)
print('exit', result.returncode, result.stderr.decode()[-300:], file=sys.stderr)
text = json.dumps(seen, ensure_ascii=False)
found = re.search(r'Filesystem: (\{.*?\}\})', text.replace('\\"', '"'))
print(json.dumps(json.loads(found.group(1)) if found else None, indent=1, ensure_ascii=False))
