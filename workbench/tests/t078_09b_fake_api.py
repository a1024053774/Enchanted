"""Loopback-only 09B API stage process; no forwarding, model or business writes."""
import argparse, json, os, signal, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        if self.path != '/health': self.send_error(404); return
        self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok":true,"stage":"A","model_turns":0}')
    def do_POST(self):
        size=int(self.headers.get('Content-Length','0')); body=self.rfile.read(size)
        with (ROOT/'requests.ndjson').open('a',encoding='utf-8') as f:
            f.write(json.dumps({'path':self.path,'headers':{'authorization':bool(self.headers.get('Authorization'))},'body_bytes':len(body),'at':time.time()})+'\n')
        self.send_response(409); self.send_header('Content-Type','application/json'); self.end_headers()
        self.wfile.write(b'{"ok":false,"error":"09B_STAGE_B_NOT_APPROVED","model_turns":0}')

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--role',required=True);parser.add_argument('--port',type=int,default=0);a=parser.parse_args();ROOT=a.root.resolve();ROOT.mkdir(parents=True,exist_ok=True)
server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);ready=ROOT/'api-ready.json';ready.write_text(json.dumps({'host':'127.0.0.1','port':server.server_port,'api_url':f'http://127.0.0.1:{server.server_port}','pid':os.getpid(),'role':a.role,'stage':'A','model_turns':0})+'\n')
def stop(*_): server.shutdown()
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);server.serve_forever()
