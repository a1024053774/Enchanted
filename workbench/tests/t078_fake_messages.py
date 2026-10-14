"""P1-only local Messages endpoint; never forwards requests or records headers."""
import json,os,sys,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
root=Path(sys.argv[1]);manifest=json.loads((root/'input.json').read_text())
nonce=(root/'nonce.txt').read_text();messages=0
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        global messages
        if self.headers.get('Authorization')!='Bearer a2a-fixture-key-not-a-secret' or self.headers.get('x-api-key') is not None:
            (root/'api-error.json').write_text('{"reason":"request did not use only the public fixture bearer token; headers not recorded"}')
            self.send_error(401);return
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        path=self.path.split('?',1)[0]
        with (root/'api.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'path':path,'body':body,'at':time.time()},ensure_ascii=False)+'\n')
        if path=='/v1/messages/count_tokens':
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(b'{"input_tokens":128}');return
        messages+=1
        if path!='/v1/messages' or messages!=1 or not body.get('stream') or nonce not in json.dumps(body.get('messages',[]),ensure_ascii=False):
            (root/'api-error.json').write_text(json.dumps({'path':path,'messages':messages,'reason':'unexpected protocol/input or request budget'}))
            self.send_error(400);return
        (root/'api-request.json').write_text(json.dumps(body,ensure_ascii=False))
        deadline=time.monotonic()+60
        while not (root/'api-release').exists():
            if time.monotonic()>deadline:self.send_error(408);return
            time.sleep(.02)
        self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
        mid='msg_t078_p1'
        events=[('message_start',{'type':'message_start','message':{'id':mid,'type':'message','role':'assistant','model':'claude-haiku-5-5','content':[],'stop_reason':None,'stop_sequence':None,'usage':{'input_tokens':128,'output_tokens':0}}}),
                ('content_block_start',{'type':'content_block_start','index':0,'content_block':{'type':'text','text':''}}),
                ('content_block_delta',{'type':'content_block_delta','index':0,'delta':{'type':'text_delta','text':'P1_ACK '+nonce}}),
                ('content_block_stop',{'type':'content_block_stop','index':0}),
                ('message_delta',{'type':'message_delta','delta':{'stop_reason':'end_turn','stop_sequence':None},'usage':{'output_tokens':16}}),
                ('message_stop',{'type':'message_stop'})]
        with (root/'api-response.sse').open('xb') as trace:
            for kind,data in events:
                packet=('event: '+kind+'\ndata: '+json.dumps(data)+'\n\n').encode()
                trace.write(packet);trace.flush();self.wfile.write(packet);self.wfile.flush()
        (root/'api-finished').write_text(mid)
if manifest['api_url']!='http://127.0.0.1:0':raise RuntimeError('dynamic_endpoint_template_required')
server=HTTPServer(('127.0.0.1',0),Handler)
with (root/'api-ready.tmp').open('x',encoding='utf-8') as ready:
    json.dump({'host':'127.0.0.1','port':server.server_port,'api_url':'http://127.0.0.1:'+str(server.server_port),
               'pid':os.getpid(),'launch':manifest['launch'],'session':manifest['session']},ready)
os.link(root/'api-ready.tmp',root/'api-ready.json')
(root/'api-ready.tmp').unlink()
server.serve_forever()
