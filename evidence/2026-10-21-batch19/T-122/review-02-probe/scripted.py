"""Review-02 probe: claude -p against a local endpoint issuing a fixed list of tool calls.
Usage: scripted.py <cwd> <settings.json> <actions.json> <home>"""
import json, os, subprocess, sys, threading, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
cwd, settings, actions, home = sys.argv[1], open(sys.argv[2]).read(), json.load(open(sys.argv[3])), sys.argv[4]
state = {'i': 0}; lock = threading.Lock()
class Api(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.path.startswith('/v1/messages/count_tokens'):
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"input_tokens":1}'); return
        with lock:
            main = len(body.get('tools', [])) > 0
            action = actions[state['i']] if main and state['i'] < len(actions) else None
            if main: state['i'] += 1
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
        def emit(kind, value): self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps({'type': kind, **value}) + '\n\n').encode())
        emit('message_start', {'message': {'id': 'm' + uuid.uuid4().hex, 'type': 'message', 'role': 'assistant', 'model': body['model'], 'content': [], 'stop_reason': None, 'usage': {'input_tokens': 1, 'output_tokens': 0}}})
        if action:
            emit('content_block_start', {'index': 0, 'content_block': {'type': 'tool_use', 'id': 'toolu_' + uuid.uuid4().hex[:20], 'name': action[0], 'input': {}}})
            emit('content_block_delta', {'index': 0, 'delta': {'type': 'input_json_delta', 'partial_json': json.dumps(action[1])}})
            emit('content_block_stop', {'index': 0}); emit('message_delta', {'delta': {'stop_reason': 'tool_use', 'stop_sequence': None}, 'usage': {'output_tokens': 1}})
        else:
            emit('content_block_start', {'index': 0, 'content_block': {'type': 'text', 'text': ''}})
            emit('content_block_delta', {'index': 0, 'delta': {'type': 'text_delta', 'text': 'done'}})
            emit('content_block_stop', {'index': 0}); emit('message_delta', {'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 1}})
        emit('message_stop', {})
server = ThreadingHTTPServer(('127.0.0.1', 0), Api); threading.Thread(target=server.serve_forever, daemon=True).start()
env = dict(os.environ, ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}', ANTHROPIC_AUTH_TOKEN='probe-not-a-secret', HOME=home)
env.pop('ANTHROPIC_API_KEY', None)
r = subprocess.run(['claude', '-p', '--session-id', str(uuid.uuid4()), '--model', 'claude-haiku-5-5', '--effort', 'low', '--permission-mode', 'dontAsk',
    '--setting-sources', '', '--strict-mcp-config', '--settings', settings, 'go'], cwd=cwd, env=env, capture_output=True, timeout=300, stdin=subprocess.DEVNULL)
print('claude exit', r.returncode)
import glob
for f in glob.glob(home + '/.claude/projects/*/*.jsonl'):
    for l in open(f):
        e = json.loads(l)
        if e.get('type') == 'user' and isinstance(e.get('message', {}).get('content'), list):
            for c in e['message']['content']:
                if c.get('type') == 'tool_result':
                    t = c.get('content'); t = ''.join(x.get('text', '') for x in t) if isinstance(t, list) else t
                    print('ERR' if c.get('is_error') else 'ok ', t[:260].replace('\n', ' | '))
