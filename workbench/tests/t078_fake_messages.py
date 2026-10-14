"""Isolated scripted Messages endpoint. Never forward requests or record headers."""
import json,os,socket,sys,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

def failure(reason,**detail):
    with lock:
        if not (root/'api-error.json').exists():
            with (root/'api-error.json').open('x',encoding='utf-8') as f:json.dump({'reason':reason,**detail},f)

def packet(kind,data):return ('event: '+kind+'\ndata: '+json.dumps(data)+'\n\n').encode()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        global messages
        if self.headers.get('Authorization')!='Bearer a2a-fixture-key-not-a-secret' or self.headers.get('x-api-key') is not None:
            failure('Request did not use only the public fixture bearer token; headers not recorded');self.send_error(401);return
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        path=self.path.split('?',1)[0]
        with lock:
            with (root/'api.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'path':path,'body':body,'at':time.time()},ensure_ascii=False)+'\n')
            if path!='/v1/messages/count_tokens':messages+=1
            number=messages
        if path=='/v1/messages/count_tokens':
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"input_tokens":128}');return
        if path!='/v1/messages' or number>len(scenario['requests']):
            failure('Unexpected path or request budget',path=path,messages=number);self.send_error(400);return
        planned=scenario['requests'][number-1];expected=f'⟦主控 #{number}⟧\n'+planned['nonce']
        texts=[part.get('text') for message in body.get('messages',[]) if message.get('role')=='user' for part in message.get('content',[]) if isinstance(part,dict) and part.get('type')=='text']
        if body.get('model')!='claude-haiku-5-5' or body.get('stream') is not True or not texts or texts[-1]!=expected:
            failure('Request did not match declared model, stream and exact input',number=number);self.send_error(400);return
        with (root/f'api-request-{number}.json').open('x',encoding='utf-8') as f:json.dump(body,f,ensure_ascii=False)
        self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
        mid=f'msg_t078_{manifest["launch"]}_{number}'
        def cancelled(reason):
            with (root/f'api-cancelled-{number}.json').open('x',encoding='utf-8') as f:json.dump({'number':number,'observed_at':time.time(),'reason':reason},f)
        with (root/f'api-response-{number}.sse').open('xb') as trace:
            def emit(kind,data):
                payload=packet(kind,data);trace.write(payload);trace.flush();self.wfile.write(payload);self.wfile.flush()
            try:
                emit('message_start',{'type':'message_start','message':{'id':mid,'type':'message','role':'assistant','model':'claude-haiku-5-5','content':[],
                    'stop_reason':None,'stop_sequence':None,'usage':{'input_tokens':128,'output_tokens':0}}})
            except (BrokenPipeError,ConnectionResetError):
                if planned['mode']=='cancel':cancelled('Peer closed during response start')
                else:failure('Client closed a response declared to complete',number=number)
                return
            if planned['mode']=='cancel':
                self.connection.settimeout(.05);deadline=time.monotonic()+90
                while time.monotonic()<deadline:
                    try:received=self.connection.recv(1,socket.MSG_PEEK)
                    except socket.timeout:continue
                    except ConnectionResetError:received=b''
                    if received==b'':cancelled('Peer closed/reset');return
                    failure('Unexpected data on held response connection',number=number);return
                failure('Peer cancellation deadline; no retry',number=number);return
            deadline=time.monotonic()+60
            while not (root/f'api-release-{number}').exists():
                if time.monotonic()>deadline:failure('Response release deadline; no retry',number=number);return
                time.sleep(.02)
            try:
                emit('content_block_start',{'type':'content_block_start','index':0,'content_block':{'type':'text','text':''}})
                emit('content_block_delta',{'type':'content_block_delta','index':0,'delta':{'type':'text_delta','text':planned['ack']+' '+planned['nonce']}})
                emit('content_block_stop',{'type':'content_block_stop','index':0})
                emit('message_delta',{'type':'message_delta','delta':{'stop_reason':'end_turn','stop_sequence':None},'usage':{'output_tokens':16}})
                emit('message_stop',{'type':'message_stop'})
            except (BrokenPipeError,ConnectionResetError):failure('Client closed a response declared to complete',number=number);return
        with (root/f'api-finished-{number}.json').open('x',encoding='utf-8') as f:json.dump({'number':number,'id':mid},f)

def main():
    global root,manifest,scenario,messages,lock
    root=Path(sys.argv[1]);manifest=json.loads((root/'input.json').read_text());scenario=json.loads((root/'scenario.json').read_text())
    if manifest['api_url']!='http://127.0.0.1:0' or scenario['schema']!=1 or len(scenario['requests'])!=manifest['turn_limit']:raise RuntimeError('Invalid approved endpoint/budget template')
    expected_modes=['echo'] if scenario['name']=='single' else ['cancel','echo'] if scenario['name']=='esc-two' else []
    if [x['mode'] for x in scenario['requests']]!=expected_modes:raise RuntimeError('Unsupported declared scenario')
    messages=0;lock=threading.Lock();server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    with (root/'api-ready.tmp').open('x',encoding='utf-8') as f:json.dump({'host':'127.0.0.1','port':server.server_port,'api_url':'http://127.0.0.1:'+str(server.server_port),
        'pid':os.getpid(),'launch':manifest['launch'],'session':manifest['session']},f)
    os.link(root/'api-ready.tmp',root/'api-ready.json');(root/'api-ready.tmp').unlink();server.serve_forever()

if __name__=='__main__':main()
