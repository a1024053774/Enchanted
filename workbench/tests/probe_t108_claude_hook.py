"""Installed interactive CLI against loopback scripted API. No vendor/model calls.

Failure modes: missing tool in advertised schema, missing PreToolUse fields,
input keys answer a different widget, PostToolUse lacks the chosen answer.
Never reads credentials or inherits provider configuration.
"""
import argparse, fcntl, json, os, pty, select, signal, struct, subprocess, sys, tempfile, termios, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
p.add_argument('--cli', default='/Users/luckye/.local/bin/claude')
p.add_argument('--mode', choices=['choice','free','multi','batch'], default='choice')
args = p.parse_args()
root = Path(tempfile.mkdtemp(prefix='t108-cli-', dir='/private/tmp'))
repo = root/'repo'; repo.mkdir()
config = root/'config'; config.mkdir()
(root/'home').mkdir()
(config/'settings.json').write_text(json.dumps({'theme':'dark'}))
(config/'.claude.json').write_text(json.dumps({'hasCompletedOnboarding':True,'projects':{str(repo):{'hasTrustDialogAccepted':True}}}))
question = {'questions':[{'question':'选择部署区域？','header':'区域','options':[{'label':'东区','description':'第一个区域'},{'label':'西区','description':'第二个区域'}],'multiSelect':False}]}
if args.mode=='multi': question['questions'][0]['multiSelect']=True
if args.mode=='batch': question['questions'].append({**question['questions'][0],'question':'选择备份区域？','header':'备份'})
hook_script = root/'hook.py'
hook_script.write_text('import sys,json\nfrom pathlib import Path\nv=sys.stdin.read()\nwith Path('+repr(str(root/'hooks.jsonl'))+').open("a") as f:f.write(v.strip()+"\\n")\nprint("{}")\n')
command = '/usr/bin/python3 '+str(hook_script)
settings = {'hooks':{name:[{'matcher':'AskUserQuestion','hooks':[{'type':'command','command':command,'timeout':3}]}] for name in ['PreToolUse','PostToolUse','PostToolUseFailure']}}
requests = []
root_requests = []
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.path.split('?')[0]=='/v1/messages/count_tokens':
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"input_tokens":128}'); return
        assert self.path.split('?')[0]=='/v1/messages', self.path
        requests.append(body)
        with (root/'requests.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(body,ensure_ascii=False)+'\n')
        root_call=any(tool.get('name')=='AskUserQuestion' for tool in body.get('tools',[]))
        if root_call: root_requests.append(body)
        if len(root_requests)>2 or len(requests)>8: self.send_error(409); return
        self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.end_headers()
        def emit(t,v): self.wfile.write(('event: '+t+'\ndata: '+json.dumps({'type':t,**v})+'\n\n').encode()); self.wfile.flush()
        emit('message_start',{'message':{'id':'msg_probe_'+str(len(requests)),'type':'message','role':'assistant','model':'claude-haiku-5-5','content':[],'stop_reason':None,'usage':{'input_tokens':128,'output_tokens':0}}})
        if root_call and len(root_requests)==1:
            emit('content_block_start',{'index':0,'content_block':{'type':'tool_use','id':'toolu_t108_question','name':'AskUserQuestion','input':{}}})
            emit('content_block_delta',{'index':0,'delta':{'type':'input_json_delta','partial_json':json.dumps(question,ensure_ascii=False)}})
            reason='tool_use'
        else:
            emit('content_block_start',{'index':0,'content_block':{'type':'text','text':''}})
            emit('content_block_delta',{'index':0,'delta':{'type':'text_delta','text':'已收到答复。'}}); reason='end_turn'
        emit('content_block_stop',{'index':0})
        emit('message_delta',{'delta':{'stop_reason':reason,'stop_sequence':None},'usage':{'output_tokens':20}})
        emit('message_stop',{})
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
env={k:v for k,v in os.environ.items() if k in ['PATH','SYSTEMROOT']}
env.update(HOME=str(root/'home'),CLAUDE_CONFIG_DIR=str(config),TERM='xterm-256color',SHELL='/bin/zsh',
           ANTHROPIC_BASE_URL='http://127.0.0.1:'+str(server.server_port),ANTHROPIC_AUTH_TOKEN='a2a-fixture-key-not-a-secret',
           CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',DISABLE_AUTOUPDATER='1')
env['CLAUDE_CODE_DISABLE_BACKGROUND_TASKS']='1'
argv=[args.cli,'--model','claude-haiku-5-5','--effort','low','--settings',json.dumps(settings),'--setting-sources','',
      '--tools','AskUserQuestion','--permission-mode','manual','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--disable-slash-commands','--debug-file',str(root/'debug.log')]
master,slave=pty.openpty(); fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',40,120,0,0))
child=subprocess.Popen(argv,cwd=repo,env=env,stdin=slave,stdout=slave,stderr=slave,start_new_session=True); os.close(slave)
screen=bytearray(); hooks=[]
def pump(seconds):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        if select.select([master],[],[],.05)[0]:
            try:
                chunk=os.read(master,65536); screen.extend(chunk)
                if b'\x1b[6n' in chunk: os.write(master,b'\x1b[1;1R')
                if b'\x1b[c' in chunk: os.write(master,b'\x1b[?1;2c')
            except OSError: return
def read_hooks():
    return [json.loads(x) for x in (root/'hooks.jsonl').read_text().splitlines()] if (root/'hooks.jsonl').exists() else []
result={'status':'INCOMPLETE','model_turns':0,'model_calls':0,'vendor_calls':0,'argv':argv,'fixture':str(root),'pid':child.pid}
try:
    pump(3); os.write(master,b'Please ask the region question.\r')
    for _ in range(100):
        pump(.1); hooks=read_hooks()
        if hooks: break
    assert hooks and hooks[0]['hook_event_name']=='PreToolUse','No question hook; diagnostic retained'
    result['question_screen_tail']=screen[-6000:].decode('utf-8','replace')
    pump(.5)
    if args.mode=='free':
        os.write(master,b'\x1b[B');pump(.15);os.write(master,b'\x1b[B');pump(.15)
        os.write(master,'\x1b[200~第三个区域\x1b[201~'.encode());pump(.15);os.write(master,b'\r');pump(.5)
    elif args.mode=='multi':
        os.write(master,b' ');pump(.15);os.write(master,b'\x1b[B');pump(.15);os.write(master,b' ');pump(.15);os.write(master,b'\r');pump(.5)
    else:
        os.write(master,b'\x1b[B'); pump(.15); os.write(master,b'\r'); pump(.5)
        if args.mode=='batch':os.write(master,b'\x1b[B');pump(.15);os.write(master,b'\r');pump(.5)
    result['after_selection_tail']=screen[-3000:].decode('utf-8','replace')
    os.write(master,b'\r')
    for _ in range(100):
        pump(.1); hooks=read_hooks()
        if any(x['hook_event_name']=='PostToolUse' for x in hooks): break
    result['hooks']=hooks
    result['api_tool_results']=[part for body in requests for msg in body.get('messages',[]) for part in msg.get('content',[]) if isinstance(part,dict) and part.get('type')=='tool_result']
    assert any(x['hook_event_name']=='PostToolUse' for x in hooks),'No resolution hook'
    response=next(x['tool_response'] for x in hooks if x['hook_event_name']=='PostToolUse')
    expected='第三个区域' if args.mode=='free' else '东区, 西区' if args.mode=='multi' else '西区'
    assert all(response['answers'].get(q['question'])==expected for q in question['questions']), response
    result['status']='PASS'
except Exception as error: result['error']=str(error)
finally:
    result['hooks']=read_hooks(); result['final_screen_tail']=screen[-4000:].decode('utf-8','replace')
    result['request_count']=len(requests)
    (root/'api-requests.json').write_text(json.dumps(requests,ensure_ascii=False,indent=2))
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    os.killpg(child.pid,signal.SIGTERM)
    try: child.wait(timeout=3)
    except subprocess.TimeoutExpired: os.killpg(child.pid,signal.SIGKILL); child.wait(timeout=3)
    os.close(master); server.shutdown(); server.server_close()
    print(json.dumps({k:v for k,v in result.items() if k not in ['question_screen_tail','after_selection_tail','final_screen_tail','argv']},ensure_ascii=False))
sys.exit(0 if result['status']=='PASS' else 1)
