"""Run one pure text code-mode tool through the installed interactive CLI.
Only local fake responses; no credentials, shell command or global writes. Python 3.9.
"""
import argparse,fcntl,json,os,pty,select,shutil,struct,subprocess,sys,signal,tempfile,termios,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
source=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(source/'workbench/tests'))
from t112_native_api import request_source,request_tools,shell_item,tool_events,message_events
p=argparse.ArgumentParser();p.add_argument('--summary',type=Path,required=True);args=p.parse_args();assert not args.summary.exists()
root=Path(tempfile.mkdtemp(prefix='t112-request-capture-',dir='/private/tmp'))
for name in ['home','codex','candidate']:(root/name).mkdir()
nonce='T112_PROTOCOL_'+__import__('uuid').uuid4().hex
emitted=None
report={'status':'INCOMPLETE','scope':'actual installed CLI custom-tool protocol; pure text JavaScript only, no shell or sandbox proof','requests':[],'cleanup':[]}
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  data=self.rfile.read(int(self.headers['Content-Length']))
  body=json.loads(data)
  entry={'path':self.path,'headers':{k:self.headers.get(k) for k in ['Content-Type','Content-Encoding']},'body':body}
  report['requests'].append(entry)
  (root/'captured.json').write_text(json.dumps(report,ensure_ascii=False),encoding='utf-8')
  global emitted
  kind=request_source(body)
  entry['thread_source']=kind
  if kind=='thread_title':
   self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
   for ordinal,(event,payload) in enumerate(message_events(json.dumps({'title':'T112 protocol probe'}),body['model'])):
    self.wfile.write(('event: '+event+'\ndata: '+json.dumps({'type':event,'sequence_number':ordinal,**payload})+'\n\n').encode());self.wfile.flush()
   return
  assert kind=='user'
  if emitted is None:
   emitted=shell_item(request_tools(body),'unused shell command',root/'candidate')
   emitted['input']='text('+json.dumps(nonce)+');'
   report['emitted_tool_call']=emitted
   self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
   for ordinal,(event,payload) in enumerate(tool_events(emitted,body['model'])):
    self.wfile.write(('event: '+event+'\ndata: '+json.dumps({'type':event,'sequence_number':ordinal,**payload})+'\n\n').encode());self.wfile.flush()
  else:
   outputs=[item for item in body['input'] if item.get('type')=='custom_tool_call_output' and item.get('call_id')==emitted['call_id']]
   report['native_tool_outputs']=outputs
   report['expected_output']=nonce
   self.send_response(400);self.send_header('Content-Type','application/json');self.end_headers()
   self.wfile.write(b'{"error":{"message":"T112_PROTOCOL_COMPLETE_STOP","type":"invalid_request_error"}}')

server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
config='model_provider="t112_fixture"\ncli_auth_credentials_store="file"\n[model_providers.t112_fixture]\nname="capture only"\nbase_url="http://127.0.0.1:'+str(server.server_port)+'/v1"\nwire_api="responses"\nrequires_openai_auth=false\n[projects.'+json.dumps(str(root/'candidate'))+']\ntrust_level="trusted"\n'
(root/'codex/config.toml').write_text(config,encoding='utf-8')
env={k:v for k,v in os.environ.items() if k in ['PATH','LANG','LC_CTYPE','TMPDIR','USER','LOGNAME']}
env.update(HOME=str(root/'home'),CODEX_HOME=str(root/'codex'),LC_ALL='C',TERM='xterm-256color')
argv=['/Users/luckye/.codex/packages/app-server-daemon/releases/0.162.1-aarch64-apple-darwin/bin/codex','--no-daemon','--no-alt-screen','-C',str(root/'candidate'),'-m','gpt-6.1-sol','-a','never','--sandbox','workspace-write','-c','check_for_update_on_startup=false','-c','model_reasoning_effort="xhigh"','-c','sandbox_workspace_write.exclude_slash_tmp=true','-c','sandbox_workspace_write.exclude_tmpdir_env_var=true','仅验证本地请求格式，不执行工具。']
report.update(argv=argv,isolated_config=config)
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',40,120,0,0))
child=None;screen=bytearray()
try:
 child=subprocess.Popen(argv,env=env,cwd=root/'candidate',stdin=slave,stdout=slave,stderr=slave,start_new_session=True);os.close(slave)
 report['child_pid']=child.pid
 (root/'child.json').write_text(json.dumps({'pid':child.pid,'argv':argv}),encoding='utf-8')
 end=time.monotonic()+40
 while not report.get('native_tool_outputs'):
  assert child.poll() is None,'CLI exited before capture'
  assert time.monotonic()<end,'Request capture deadline'
  if select.select([master],[],[],.05)[0]:
   data=os.read(master,65536);screen.extend(data)
   for query,reply in [(b'\x1b[6n',b'\x1b[1;1R'),(b'\x1b[c',b'\x1b[?1;2c'),(b'\x1b[>c',b'\x1b[>0;0;0c'),(b'\x1b[?u',b'\x1b[?0u')]:
    if query in data:os.write(master,reply)
 outputs=report['native_tool_outputs']
 assert len(outputs)==1 and outputs[0]['call_id']==emitted['call_id'], 'Native code tool result identity differs'
 blocks=outputs[0]['output']
 assert any(block.get('type')=='input_text' and block.get('text')==nonce for block in blocks), 'Native code tool did not return the exact sentinel text'
 assert any(block.get('type')=='input_text' and block.get('text','').startswith('Script completed\n') for block in blocks), 'Native code tool did not complete successfully'
 report['status']='PASS'
except Exception as error:report['error']=str(error)
finally:
 # Popen owns this unreaped direct child and its new session. Signal only
 # that newly created group while the direct child is still alive; no ps scan.
 if child and child.poll() is None:
  assert os.getpgid(child.pid)==child.pid
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:
   assert child.poll() is None and os.getpgid(child.pid)==child.pid
   os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
  report['cleanup'].append({'pid':child.pid,'status':'direct_child_reaped','scope':'private start_new_session process group'})
 os.close(master);server.shutdown();server.server_close();report['terminal_tail']=screen[-3000:].decode('utf-8',errors='replace')
 if not report.get('cleanup_errors'):shutil.rmtree(root);report['fixture_removed']=not root.exists()
 else:report['retained_fixture']=str(root)
 args.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':report['status'],'keys':[list(r['body']) for r in report['requests']],'summary':str(args.summary)}))
raise SystemExit(0 if report['status']=='PASS' else 1)
