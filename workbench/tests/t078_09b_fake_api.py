"""Loopback-only 09B API stage process; no forwarding, model or business writes."""
import argparse, json, os, signal, sys, time, uuid, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from t078_raw_retention import HttpExchange
from t078_09b_protocol_core import anthropic_sse, normalize_anthropic_request, validate_request, ProtocolRefusal

DISPATCH_STATES={}
PROTOCOL_TAG='rev2-raw-c-profile-v1'
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
        capture=HttpExchange(ROOT,sequence,'POST',self.path,self.headers.get('Content-Type'),body,ROLE)
        request_log={'sequence':sequence,'path':self.path,'body_bytes':len(body),
                     'body_raw':body.decode('utf-8','replace'),'at':time.time()}
        headers_sent=False; status=409; content_type='application/json'
        try:
            if self.path.split('?')[0] != '/v1/messages':
                raise ProtocolRefusal('unapproved_HTTP_path')
            if not PROTOCOL:
                raise ProtocolRefusal('09B_STAGE_B_NOT_APPROVED')
            request=json.loads(body); registry=json.loads((ROOT/'protocol-registry.json').read_bytes())
            phase=None
            if 'phase_plan' in registry:
                from t078_09b_phase_registry import resolve_request
                registry,phase=resolve_request(request,registry,ROOT,ROLE)
            registry['messages_used']=sequence
            normalized,anthropic=normalize_anthropic_request(request,registry,ROLE)
            if not normalized.get('request_id'):
                normalized['request_id']=self.headers.get('X-Request-Id') or uuid.uuid4().hex
            dispatch_id=normalized['dispatch_id']; state=DISPATCH_STATES.get(dispatch_id)
            if state == 'settled' or (state == 'tool_sent' and not normalized.get('tool_result')):
                raise ProtocolRefusal('dispatch_replayed')
            result=validate_request(normalized,registry)
            if normalized.get('tool_result'):
                if state != 'tool_sent': raise ProtocolRefusal('tool_result_without_tool_use')
                DISPATCH_STATES[dispatch_id]='settled'
            else:
                DISPATCH_STATES[dispatch_id]='tool_sent' if result.get('tool_use') else 'settled'
            request_log.update({'dispatch_id':dispatch_id,'dispatch_seq':normalized['dispatch_seq'],
                'request_id':normalized['request_id'],'stop_id':normalized.get('stop_id'),'attempt':normalized.get('attempt'),
                'session':normalized.get('session'),'fence':normalized.get('fence'),'anthropic':anthropic,
                'message_kind':'tool_result' if normalized.get('tool_result') else ('tool_use' if result.get('tool_use') else 'text'),
                'phase':phase})
            if normalized.get('tool_result_payload'): request_log['tool_result_payload']=normalized['tool_result_payload']
            if normalized.get('tool_result_block'): request_log['tool_use_id']=normalized['tool_result_block'].get('tool_use_id')
            with (ROOT/'requests.ndjson').open('a',encoding='utf-8') as f:f.write(json.dumps(request_log,ensure_ascii=False)+'\n')
            events=anthropic_sse(result,normalized.get('model'),normalized['request_id']) if anthropic else result['sse']
            def encoded(event):
                return ((('event: '+event['type']+'\n') if anthropic else '')+'data: '+json.dumps(event,ensure_ascii=False)+'\n\n').encode()
            status=200; content_type='text/event-stream'
            self.send_response(status); self.send_header('Content-Type',content_type); self.end_headers(); headers_sent=True
            if phase == 'C-E1':
                # One actual POST remains open. Heartbeats are SSE comments,
                # not Messages, tool calls or an artificial ack.
                from t078_09b_phase_registry import stop_entry
                from t078_09c_driver import created_ms
                plan=json.loads(Path(registry['phase_plan']).read_bytes()); stop=stop_entry(plan)
                capture.write(self.wfile,encoded(events[0]))
                while not (ROOT/'hold-release.json').is_file():
                    if time.time()*1000-created_ms(stop['created_at']) >= 150000:
                        raise ProtocolRefusal('C_executor_hold_deadline')
                    capture.write(self.wfile,b': held; no acknowledgement\n\n'); time.sleep(.25)
                release=json.loads((ROOT/'hold-release.json').read_bytes())
                if release != {'stop_id':stop['id'],'source_revision':plan['source_revision']}:
                    raise ProtocolRefusal('C_hold_release_binding_mismatch')
                payload=b''.join(encoded(event) for event in events[1:])
            else:
                payload=b''.join(encoded(event) for event in events)
            capture.write(self.wfile,payload)
            capture.finish(status,content_type,True,dispatch_id=dispatch_id,request_id=normalized['request_id'],phase=phase,
                           stop_id=normalized.get('stop_id'))
            with (ROOT/'responses.ndjson').open('a',encoding='utf-8') as f:f.write(json.dumps({'dispatch_id':dispatch_id,
                'request_id':normalized['request_id'],'stop_id':normalized.get('stop_id'),'events':len(events),'at':time.time()},ensure_ascii=False)+'\n')
        except Exception as error:
            request_log['error']=str(error)
            with (ROOT/'requests.ndjson').open('a',encoding='utf-8') as f:f.write(json.dumps(request_log,ensure_ascii=False)+'\n')
            if headers_sent:
                capture.finish(status,content_type,False,error=str(error))
                self.close_connection=True
            else:
                response=json.dumps({'ok':False,'error':str(error)},ensure_ascii=False).encode()
                try:
                    self.send_response(409); self.send_header('Content-Type','application/json'); self.end_headers()
                    capture.write(self.wfile,response)
                finally:
                    capture.finish(409,'application/json',capture.meta['wire_bytes_confirmed']==len(response),error=str(error))


def configure(root, role, protocol):
    global ROOT, ROLE, PROTOCOL, REQUEST_SEQ, DISPATCH_STATES
    if role not in ('ideation','executor'): raise ValueError('fixture_role_required')
    ROOT=Path(root).resolve(); ROLE=role; PROTOCOL=protocol
    ROOT.mkdir(parents=True,exist_ok=True); REQUEST_SEQ=0; DISPATCH_STATES={}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--role',choices=['ideation','executor'],required=True)
    parser.add_argument('--port',type=int,default=0)
    parser.add_argument('--protocol',action='store_true')
    args=parser.parse_args(); configure(args.root,args.role,args.protocol)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    ready=ROOT/'api-ready.json'; pending=ROOT/'api-ready.json.pending'
    value={'host':'127.0.0.1','port':server.server_port,
        'api_url':f'http://127.0.0.1:{server.server_port}','pid':os.getpid(),'role':ROLE,'stage':'A',
        'model_turns':0,'protocol':PROTOCOL_TAG if PROTOCOL else None,
        'fixture_profile':'rev2-registered-raw-v1' if PROTOCOL else None}
    with pending.open('x',encoding='utf-8') as stream:stream.write(json.dumps(value)+'\n')
    os.link(pending,ready);pending.unlink()
    def stop(*_):
        # Never call shutdown on the serve_forever thread (A05 deadlock).
        raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    try: server.serve_forever()
    finally: server.server_close()


if __name__ == '__main__': main()
