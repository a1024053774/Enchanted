"""Codex interactive question probe, private HOME and local Responses fixture.
No credential copying, model calls, screen classification or global config writes.
"""
import argparse, fcntl, json, os, pty, select, signal, struct, subprocess, sys, tempfile, termios, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); p.add_argument('--sync',action='store_true'); p.add_argument('--free',action='store_true'); args=p.parse_args()
root=Path(tempfile.mkdtemp(prefix='t108-codex-',dir='/private/tmp'))
repo=root/'repo'; repo.mkdir(); home=root/'home'; home.mkdir(); config=root/'codex'; config.mkdir()
script=root/'hook.py'; script.write_text('import sys\nfrom pathlib import Path\nwith Path('+repr(str(root/'hooks.jsonl'))+').open("a") as f:f.write(sys.stdin.read().strip()+"\\n")\nprint("{}")\n')
question={'questions':[{'title':'选择部署区域？','options':['东区','西区']}]}
if args.sync: question={'questions':[{'id':'region','header':'区域','question':'选择部署区域？','options':[{'label':'东区','description':'第一个区域'},{'label':'西区','description':'第二个区域'}]}]}
requests=[]
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        requests.append(body)
        with (root/'requests.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(body,ensure_ascii=False)+'\n')
        if len(requests)>2:self.send_error(409);return
        names=[t.get('name') for t in body.get('tools',[])]
        name='request_user_input' if args.sync else 'request_user_input_async'
        item={'type':'function_call','id':'fc_t108','call_id':'call_t108','name':name,'arguments':json.dumps(question,ensure_ascii=False)}
        if len(requests)>1:item={'type':'message','id':'msg_done','role':'assistant','content':[{'type':'output_text','text':'已收到答复。','annotations':[]}]}
        response={'id':'resp_t108_'+str(len(requests)),'object':'response','created_at':int(time.time()),'status':'completed','output':[item],
                  'usage':{'input_tokens':128,'output_tokens':20,'total_tokens':148}}
        self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
        events=[{'type':'response.created','response':{**response,'status':'in_progress','output':[]}},
                {'type':'response.output_item.added','output_index':0,'item':item},
                {'type':'response.output_item.done','output_index':0,'item':item},
                {'type':'response.completed','response':response}]
        for event in events:self.wfile.write(('data: '+json.dumps(event,ensure_ascii=False)+'\n\n').encode());self.wfile.flush()
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
env={'PATH':os.environ['PATH'],'HOME':str(home),'CODEX_HOME':str(config),'TERM':'xterm-256color','OPENAI_API_KEY':'fixture-not-a-secret'}
argv=['/Users/luckye/.local/bin/codex','--no-daemon','--no-alt-screen','-m','gpt-6.1-sol','-c','model_reasoning_effort="high"',
      '-c','check_for_update_on_startup=false','-c','model_provider="fixture"','-c',
      'model_providers.fixture={name="fixture",base_url="http://127.0.0.1:'+str(server.server_port)+'",wire_api="responses",env_key="OPENAI_API_KEY"}',
      '-c','projects.'+json.dumps(str(repo))+'.trust_level="trusted"','--dangerously-bypass-hook-trust']
for event in ['PreToolUse','PostToolUse','UserPromptSubmit','Stop']:
    argv+=['-c','hooks.'+event+'=[{hooks=[{type="command",command='+json.dumps('/usr/bin/python3 '+str(script))+',timeout=3}]}]']
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',40,120,0,0))
child=subprocess.Popen(argv,cwd=repo,env=env,stdin=slave,stdout=slave,stderr=slave,start_new_session=True);os.close(slave)
screen=bytearray()
def pump(seconds):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        if select.select([master],[],[],.05)[0]:
            try:chunk=os.read(master,65536);screen.extend(chunk)
            except OSError:return
            for query,reply in [(b'\x1b[6n',b'\x1b[1;1R'),(b'\x1b[c',b'\x1b[?1;2c'),(b'\x1b[>c',b'\x1b[>0;0;0c'),(b'\x1b[?u',b'\x1b[?0u')]:
                if query in chunk:os.write(master,reply)
def hooks():return [json.loads(x) for x in (root/'hooks.jsonl').read_text().splitlines()] if (root/'hooks.jsonl').exists() else []
result={'status':'INCOMPLETE','fixture':str(root),'pid':child.pid,'model_turns':0,'model_calls':0,'vendor_calls':0,'argv':argv}
try:
    pump(3);os.write(master,b'/plan');pump(.2);os.write(master,b'\r');pump(1)
    os.write(master,b'Ask the region question.');pump(.2);os.write(master,b'\r')
    for _ in range(100):
        pump(.1)
        if any(x.get('tool_name','').startswith('request_user_input') for x in hooks()):break
    result['question_screen_tail']=screen[-3500:].decode('utf-8','replace')
    assert any(x.get('tool_name','').startswith('request_user_input') for x in hooks()),'No question hook'
    pump(.5);os.write(master,b'\x1b[B');pump(.2)
    if args.free:
        os.write(master,b'\x1b[B');pump(.2);os.write(master,b'\t');pump(.2);os.write(master,'\x1b[200~第三个区域\x1b[201~'.encode());pump(.2)
    os.write(master,b'\r');pump(.5)
    for _ in range(100):
        pump(.1)
        if any(x.get('hook_event_name')=='PostToolUse' for x in hooks()):break
    assert any(x.get('hook_event_name')=='PostToolUse' for x in hooks()),'No resolution hook'
    if args.sync:
        answer=next(x for x in hooks() if x.get('hook_event_name')=='PostToolUse')['tool_response']
        assert json.loads(answer)['answers']['region']['answers']==(['None of the above','user_note: 第三个区域'] if args.free else ['西区']),answer
    result['status']='PASS'
except Exception as error:result['error']=str(error)
finally:
    result['hooks']=hooks();result['final_screen_tail']=screen[-4000:].decode('utf-8','replace');result['requests']=len(requests)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
    os.close(master);server.shutdown();server.server_close()
    print(json.dumps({k:v for k,v in result.items() if k not in ['argv','question_screen_tail','final_screen_tail']},ensure_ascii=False))
sys.exit(0 if result['status']=='PASS' else 1)
