"""Loopback-only 09B API stage process; no forwarding, model or business writes."""
import argparse, json, os, signal, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from t078_09b_protocol_core import validate_request, ProtocolRefusal

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        if self.path != '/health': self.send_error(404); return
        self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok":true,"stage":"A","model_turns":0}')
    def do_POST(self):
        size=int(self.headers.get('Content-Length','0')); body=self.rfile.read(size)
        with (ROOT/'requests.ndjson').open('a',encoding='utf-8') as f:
            f.write(json.dumps({'path':self.path,'headers':{'authorization':bool(self.headers.get('Authorization'))},'body_bytes':len(body),'at':time.time()})+'\n')
        if not PROTOCOL:
            self.send_response(409); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(b'{"ok":false,"error":"09B_STAGE_B_NOT_APPROVED","model_turns":0}'); return
        try:
            request=json.loads(body); registry=json.loads((ROOT/'protocol-registry.json').read_bytes()); result=validate_request(request,registry)
            self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.end_headers()
            for event in result['sse']: self.wfile.write(('data: '+json.dumps(event,ensure_ascii=False)+'\n\n').encode()); self.wfile.flush()
        except Exception as error:
            self.send_response(409); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps({'ok':False,'error':str(error)}).encode())

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--role',required=True);parser.add_argument('--port',type=int,default=0);parser.add_argument('--protocol',action='store_true');a=parser.parse_args();ROOT=a.root.resolve();PROTOCOL=a.protocol;ROOT.mkdir(parents=True,exist_ok=True)
server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);ready=ROOT/'api-ready.json';ready.write_text(json.dumps({'host':'127.0.0.1','port':server.server_port,'api_url':f'http://127.0.0.1:{server.server_port}','pid':os.getpid(),'role':a.role,'stage':'A','model_turns':0})+'\n')
def stop(*_):
    # A Python signal handler runs on the serve_forever thread. Calling
    # server.shutdown() there waits for serve_forever to return and deadlocks
    # in socketserver's condition variable. Exit the fixture directly; the
    # owning cleanup path already closes and archives its private root.
    raise SystemExit(0)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);server.serve_forever()
