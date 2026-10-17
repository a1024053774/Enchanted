"""Exercise the production HTTP handler with in-memory IO; never bind a socket."""
import argparse,ast,io,json,socket,tempfile,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler
p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args();args.output.mkdir()
source=Path(__file__).with_name('t078_fake_messages.py');tree=ast.parse(source.read_bytes())
root=Path(tempfile.mkdtemp(prefix='t078-api-domain-'));(root/'api-release').write_text('legacy single reply')
(root/'api-release-2').write_text('second approved reply')
nonces=['INDEPENDENT_FIRST_NONCE','INDEPENDENT_SECOND_NONCE']
scenario={'schema':1,'name':'esc-two','requests':[{'nonce':nonces[0],'mode':'cancel','ack':'P1_ACK'},{'nonce':nonces[1],'mode':'echo','ack':'P2_ACK'}]}
namespace={'__name__':'fixture','BaseHTTPRequestHandler':BaseHTTPRequestHandler,'root':root,'nonce':nonces[0],
           'messages':0,'lock':threading.Lock(),'manifest':{'launch':'domain','session':'domain','turn_limit':2},'scenario':scenario,
           'json':json,'time':time,'socket':socket,'Path':Path}
nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and getattr(n,'name','')!='main']
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),namespace)
statuses=[]
class Peer:
    def settimeout(self,value):pass
    def recv(self,*args):return b''  # Synthetic first client cancellation, not a real observation.
try:
    for n in range(2):
        body={'stream':True,'model':'claude-haiku-5-5','messages':[{'role':'user','content':[{'type':'text','text':f'⟦主控 #{n+1}⟧\n'+nonces[n]}]}]}
        data=json.dumps(body).encode();h=object.__new__(namespace['Handler']);h.path='/v1/messages'
        h.headers={'Authorization':'Bearer a2a-fixture-key-not-a-secret','Content-Length':str(len(data))}
        h.rfile=io.BytesIO(data);h.wfile=io.BytesIO();h.connection=Peer()
        h.send_response=lambda code:statuses.append(code);h.send_header=lambda *args:None;h.end_headers=lambda:None;h.send_error=lambda code:statuses.append(code)
        h.do_POST()
    assert statuses==[200,200],statuses
    assert (root/'api-cancelled-1.json').exists() and (root/'api-finished-2.json').exists()
    r={'status':'PASS','http_statuses':statuses}
except Exception as error:r={'status':'INCOMPLETE','error':repr(error),'http_statuses':statuses}
r.update(argv=__import__('sys').argv,scope='Production handler, synthetic peer and memory IO; no API/CLI/model process or socket')
with (args.output/'results.json').open('x',encoding='utf-8') as f:json.dump(r,f,indent=2)
print(json.dumps(r));raise SystemExit(0 if r['status']=='PASS' else 1)
