"""One controller tool slice on loopback; no forwarding or request-file writes."""
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from t078_slice1_protocol import validate_request, response_events


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        global messages
        responding = False
        try:
            if self.headers.get('Authorization') != 'Bearer a2a-fixture-key-not-a-secret' or self.headers.get('x-api-key') is not None:
                raise ValueError('Only the public fixture bearer is accepted; headers are not recorded.')
            size = int(self.headers['Content-Length'])
            if not 0 < size <= 2 * 1024 * 1024:
                raise ValueError('Request body size is outside the declared limit.')
            body = json.loads(self.rfile.read(size))
            path = self.path.split('?', 1)[0]
            with lock:
                with (root / 'api.jsonl').open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps({'path': path, 'body': body, 'at': time.time()}, ensure_ascii=False) + '\n')
                if path != '/v1/messages/count_tokens':
                    messages += 1
                number = messages
            if path == '/v1/messages/count_tokens':
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(b'{"input_tokens":128}')
                return
            if path != '/v1/messages':
                raise ValueError('Unexpected endpoint; no forwarding.')
            facts = validate_request(body, number, scenario)
            with (root / f'api-request-{number}.json').open('x', encoding='utf-8') as stream:
                json.dump(body, stream, ensure_ascii=False, indent=2)
            if number == 2:
                with (root / 'actual-tool-result.json').open('x', encoding='utf-8') as stream:
                    json.dump(facts, stream, ensure_ascii=False, indent=2)
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
            responding = True
            # Each emitted byte comes from the frozen script, not a vendor model.
            with (root / f'api-response-{number}.sse').open('xb') as trace:
                for event, value in response_events(number, scenario, f'msg_t078_{manifest["launch"]}_{number}'):
                    packet = ('event: ' + event + '\ndata: ' + json.dumps(value) + '\n\n').encode('utf-8')
                    trace.write(packet); trace.flush(); self.wfile.write(packet); self.wfile.flush()
            with (root / f'api-finished-{number}.json').open('x', encoding='utf-8') as stream:
                json.dump({'number': number, 'finished_at': time.time()}, stream)
        except Exception as error:
            with lock:
                if not (root / 'api-error.json').exists():
                    with (root / 'api-error.json').open('x', encoding='utf-8') as stream:
                        json.dump({'reason': str(error), 'at': time.time(), 'traceback': traceback.format_exc()}, stream)
            self.close_connection = True
            # Protocol errors terminate this fixture; never retry or fabricate a result.
            if not responding:
                self.send_error(400)


def main():
    global root, manifest, scenario, messages, lock
    root = Path(sys.argv[1])
    manifest = json.loads((root / 'input.json').read_bytes())
    scenario = json.loads((root / 'scenario.json').read_bytes())
    budgets={'slice1-inbox-red':(1,2),'slice1-inbox-green':(2,3)}
    expected=budgets.get(scenario['name'])
    if (expected is None or manifest['api_url'] != 'http://127.0.0.1:0' or scenario['schema'] != 1
            or manifest['turn_limit'] != expected[0] or scenario['root_submit_budget'] != expected[0]
            or scenario['messages_request_budget'] != expected[1]):
        raise RuntimeError('The frozen red or green slice budgets are required.')
    messages = 0; lock = threading.Lock()
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    with (root / 'api-ready.tmp').open('x', encoding='utf-8') as stream:
        json.dump({'host': '127.0.0.1', 'port': server.server_port,
                   'api_url': 'http://127.0.0.1:' + str(server.server_port), 'pid': os.getpid(),
                   'launch': manifest['launch'], 'session': manifest['session']}, stream)
    os.link(root / 'api-ready.tmp', root / 'api-ready.json'); (root / 'api-ready.tmp').unlink()
    server.serve_forever()


if __name__ == '__main__':
    main()
