"""Loopback-only 09B API stage process; no forwarding, model or business writes."""
import argparse, json, os, signal, sys, time, uuid, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from t078_09b_protocol_core import anthropic_sse, normalize_anthropic_request, validate_request, ProtocolRefusal

DISPATCH_STATES={}
PROTOCOL_TAG='a07-registered-anthropic-v1'
REQUEST_SEQ=0
REQUEST_LOCK=threading.Lock()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        if self.path != '/health': self.send_error(404); return
        self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok":true,"stage":"A","model_turns":0}')
    def do_POST(self):
        size=int(self.headers.get('Content-Length','0')); body=self.rfile.read(size)
        global REQUEST_SEQ
        with REQUEST_LOCK:
            REQUEST_SEQ += 1; sequence=REQUEST_SEQ
        exchange=ROOT/'http-exchanges'; exchange.mkdir(exist_ok=True)
        (exchange/f'{sequence:04d}.request.bin').write_bytes(body)
        request_log={'path':self.path,'headers':{'authorization':bool(self.headers.get('Authorization'))},
                     'body_bytes':len(body),'body_raw':body.decode('utf-8','replace'),'at':time.time()}
        if not PROTOCOL:
            with (ROOT/'requests.ndjson').open('a',encoding='utf-8') as f:f.write(json.dumps(request_log)+'\n')
            response=b'{"ok":false,"error":"09B_STAGE_B_NOT_APPROVED","model_turns":0}'; (exchange/f'{sequence:04d}.response.bin').write_bytes(response)
            self.send_response(409); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(response); return
        try:
            request=json.loads(body); registry=json.loads((ROOT/'protocol-registry.json').read_bytes())
            normalized,anthropic=normalize_anthropic_request(request,registry,ROLE)
            if not normalized.get('request_id'):
                normalized['request_id']=self.headers.get('X-Request-Id') or uuid.uuid4().hex
            dispatch_id=normalized['dispatch_id']
            state=DISPATCH_STATES.get(dispatch_id)
            if state == 'settled' or (state == 'tool_sent' and not normalized.get('tool_result')):
                raise ProtocolRefusal('dispatch_replayed')
            result=validate_request(normalized,registry)
            if normalized.get('tool_result'):
                if state != 'tool_sent':
                    raise ProtocolRefusal('tool_result_without_tool_use')
                DISPATCH_STATES[dispatch_id]='settled'
            else:
                DISPATCH_STATES[dispatch_id]='tool_sent' if result.get('tool_use') else 'settled'
            request_log.update({'dispatch_id':dispatch_id,'dispatch_seq':normalized['dispatch_seq'],'request_id':normalized['request_id'],'stop_id':normalized.get('stop_id'),'attempt':normalized.get('attempt'),'session':normalized.get('session'),'fence':normalized.get('fence'),'anthropic':anthropic})
            request_log['message_kind']='tool_result' if normalized.get('tool_result') else ('tool_use' if result.get('tool_use') else 'text')
            if normalized.get('tool_result_block'):
                request_log['tool_use_id']=normalized['tool_result_block'].get('tool_use_id')
            with (ROOT/'requests.ndjson').open('a',encoding='utf-8') as f:f.write(json.dumps(request_log,ensure_ascii=False)+'\n')
            events=anthropic_sse(result,normalized.get('model'),normalized['request_id']) if anthropic else result['sse']
            payload=b''.join(((('event: '+event['type']+'\n') if anthropic else '')+'data: '+json.dumps(event,ensure_ascii=False)+'\n\n').encode() for event in events)
            (exchange/f'{sequence:04d}.response.bin').write_bytes(payload)
            (exchange/f'{sequence:04d}.response.raw').write_bytes(payload)
            (exchange/f'{sequence:04d}.meta.json').write_text(json.dumps({'status':200,'dispatch_id':dispatch_id,'request_id':normalized['request_id'],'stop_id':normalized.get('stop_id'),'role':ROLE},ensure_ascii=False,indent=2)+'\n')
            self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.end_headers()
            self.wfile.write(payload); self.wfile.flush()
            with (ROOT/'responses.ndjson').open('a',encoding='utf-8') as f:f.write(json.dumps({'dispatch_id':dispatch_id,'request_id':normalized['request_id'],'stop_id':normalized.get('stop_id'),'events':len(events),'at':time.time()},ensure_ascii=False)+'\n')
        except Exception as error:
            request_log['error']=str(error)
            with (ROOT/'requests.ndjson').open('a',encoding='utf-8') as f:f.write(json.dumps(request_log,ensure_ascii=False)+'\n')
            response=json.dumps({'ok':False,'error':str(error)},ensure_ascii=False).encode(); (exchange/f'{sequence:04d}.response.bin').write_bytes(response); (exchange/f'{sequence:04d}.response.raw').write_bytes(response); (exchange/f'{sequence:04d}.meta.json').write_text(json.dumps({'status':409,'error':str(error),'role':ROLE},ensure_ascii=False,indent=2)+'\n')
            self.send_response(409); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(response)

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--role',required=True);parser.add_argument('--port',type=int,default=0);parser.add_argument('--protocol',action='store_true');a=parser.parse_args();ROOT=a.root.resolve();PROTOCOL=a.protocol;ROOT.mkdir(parents=True,exist_ok=True)
ROLE=a.role
server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);ready=ROOT/'api-ready.json';ready.write_text(json.dumps({'host':'127.0.0.1','port':server.server_port,'api_url':f'http://127.0.0.1:{server.server_port}','pid':os.getpid(),'role':a.role,'stage':'A','model_turns':0,'protocol':PROTOCOL_TAG if PROTOCOL else None})+'\n')
def stop(*_):
    # A Python signal handler runs on the serve_forever thread. Calling
    # server.shutdown() there waits for serve_forever to return and deadlocks
    # in socketserver's condition variable. Exit the fixture directly; the
    # owning cleanup path already closes and archives its private root.
    raise SystemExit(0)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);server.serve_forever()
