"""Capture one installed interactive CLI request; fake endpoint returns HTTP 400.
No model response, credentials, shell tool or global configuration. Python 3.9.
"""
import argparse,fcntl,json,os,pty,select,shutil,struct,subprocess,sys,signal,tempfile,termios,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
source=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--summary',type=Path,required=True);args=p.parse_args();assert not args.summary.exists()
root=Path(tempfile.mkdtemp(prefix='t112-request-capture-',dir='/private/tmp'))
for name in ['home','codex','candidate']:(root/name).mkdir()
report={'status':'INCOMPLETE','scope':'actual installed CLI request capture only; local HTTP400, no model or tool response','requests':[],'cleanup':[]}
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  data=self.rfile.read(int(self.headers['Content-Length']))
  report['requests'].append({'path':self.path,'headers':{k:self.headers.get(k) for k in ['Content-Type','Content-Encoding']},'body':json.loads(data)})
  (root/'captured.json').write_text(json.dumps(report,ensure_ascii=False),encoding='utf-8')
  self.send_response(400);self.send_header('Content-Type','application/json');self.end_headers()
  self.wfile.write(b'{"error":{"message":"T112_CAPTURE_ONLY_STOP","type":"invalid_request_error"}}')
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
 while not report['requests']:
  assert child.poll() is None,'CLI exited before capture'
  assert time.monotonic()<end,'Request capture deadline'
  if select.select([master],[],[],.05)[0]:
   data=os.read(master,65536);screen.extend(data)
   for query,reply in [(b'\x1b[6n',b'\x1b[1;1R'),(b'\x1b[c',b'\x1b[?1;2c'),(b'\x1b[>c',b'\x1b[>0;0;0c'),(b'\x1b[?u',b'\x1b[?0u')]:
    if query in data:os.write(master,reply)
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
