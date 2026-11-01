"""T-216 真实主控最小确认。
失败方式先列：真实 CLI 未申请/获批；blocked/trust 被误当 ready；替身绿态不能替代原生计数；
供应商/登录失败被写成通过；系统消息被重复提交或记用户；邮箱/认证文件进入公开证据。
agy/opencode 使用本机安装和真实 HOME，仅申请角色然后每次只回复 T216_OK；worker 仍为本地脚本化 Claude。
Codex 默认用现有 Responses 工装；--vendor 则仅复制 auth.json 到测试 CODEX_HOME，结束删除整个 home。
原生计数：agy steps 的用户 step_type（由本次申请提示所在步骤识别），opencode session_message 的 user 消息，
Codex 自己 rollout 的 response_item/user；不是 hc 或产品的队列计数。
"""
import argparse,json,os,re,shutil,subprocess,sys,threading,time,uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from scripted_claude import Fixture,gate_line,quote
from test_t212_shell_hc_e2e import stop_private_core
from t112_native_api import message_events,request_source,request_tools,shell_item,tool_events

PROMPT='这是一次 T216 最小确认。只执行 a2a request executor 申请执行主控；批准后只回复 T216_OK。以后收到收件箱问题也只回复 T216_OK，不调用工具、不修改文件、不派任务。'

def main():
 p=argparse.ArgumentParser();p.add_argument('--cli',choices=['agy','opencode','codex'],required=True);p.add_argument('--vendor',action='store_true');p.add_argument('--quota-warning',action='store_true');p.add_argument('--summary',type=Path,required=True);a=p.parse_args();assert not a.summary.exists()
 assert a.cli=='codex' or a.vendor,'真实 agy/opencode 必须显式 --vendor'
 assert not a.quota_warning or (a.cli=='codex' and not a.vendor),'--quota-warning 只用于本地 Responses 的 Codex'
 r=dict(status='INCOMPLETE',command=sys.argv,checks=[],model='unknown',effort='unknown',supplier_authorized=a.vendor)
 nonce=uuid.uuid4().hex
 def plan(body):
  return 'worker',[('Bash',dict(command=gate_line(body,"'issue' '--task' '{task}' '--title' "+quote('真实确认-'+nonce)+" '--body' "+quote('原文-'+nonce+'。本次只回复 T216_OK，不执行处置命令或任何工具。')+" '--blocking' 'false'"),description='report'))],'上报完成。'
 f=Fixture('t216-real-',plan);r['fixture']=str(f.dir);codex_home=None;responses=None;api={'bodies':[],'error':None}
 def check(name,value,detail=None):
  r['checks'].append(dict(name=name,passed=bool(value),detail=detail));assert value,(name,detail)
 def send(data):
  nonlocal sequence
  sequence+=1;x=f.request('window_input',window,sequence=sequence,request_id=str(uuid.uuid4()),data=data);assert x['ok'],x
 def raw():return (f.state/'traces'/f.terminal_launch/'pty.raw').read_text(encoding='utf-8',errors='replace')
 def screen():return re.sub(r'\s+','',''.join(re.split(r'\x1b\[[0-9;?<>=]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)',raw())))
 def native():
  if a.cli=='codex':
   rows=[]
   for file in (codex_home/'sessions').rglob('rollout-*.jsonl'):
    for line in file.read_text(encoding='utf-8').split('\n')[:-1]:
     if not line:continue
     v=json.loads(line);item=v.get('payload',{})
     if v.get('type')=='response_item' and item.get('type')=='message' and item.get('role')=='user':
      text='\n'.join(c.get('text','') for c in item.get('content',[]) if isinstance(c,dict))
      rows.append(dict(file=str(file),timestamp=v.get('timestamp'),text=text))
   return rows
  reader=f.out/'native-read.mjs'
  run=subprocess.run(['node',str(reader),a.cli,str(f.repo),str(native_start),PROMPT],capture_output=True,text=True,timeout=20)
  assert run.returncode==0,run.stderr
  return json.loads(run.stdout)
 try:
  reader=r'''import{DatabaseSync}from'node:sqlite';import{readdirSync,statSync}from'node:fs';import{homedir}from'node:os';
const[cli,cwd,since,prompt]=process.argv.slice(2);let rows=[];
if(cli==='opencode'){
 const file=homedir()+'/.local/share/opencode/opencode.db',db=new DatabaseSync(file,{readOnly:true});
 for(const s of db.prepare('select id,model from session_v2 where directory=? and time_created>=?').all(cwd,Number(since))){
  for(const v of db.prepare('select id,type,data from session_message where session_id=? order by seq').all(s.id)){
   const data=JSON.parse(v.data);rows.push({file,session:s.id,id:v.id,type:v.type,model:s.model,data});
  }
 }db.close();
}else{
 const dir=homedir()+'/.gemini/antigravity-cli/conversations';
 for(const name of readdirSync(dir).filter(n=>n.endsWith('.db')&&statSync(dir+'/'+n).mtimeMs>=Number(since))){
  const file=dir+'/'+name,db=new DatabaseSync(file,{readOnly:true});
  const meta=db.prepare("select data from trajectory_metadata_blob where id='main'").get();
  if(!meta||!Buffer.from(meta.data).includes(Buffer.from(cwd))){db.close();continue;}
  const steps=db.prepare('select idx,step_type,step_payload from steps order by idx').all();
  const user=steps.find(s=>s.step_payload&&Buffer.from(s.step_payload).includes(Buffer.from(prompt)));
  if(user)for(const s of steps.filter(s=>s.step_type===user.step_type))rows.push({file,idx:s.idx,step_type:s.step_type,text:Buffer.from(s.step_payload??[]).toString('utf8')});
  db.close();
 }
}console.log(JSON.stringify(rows));'''
  (f.out/'native-read.mjs').write_text(reader,encoding='utf-8')
  if a.cli=='codex' and not a.vendor:
   class Responses(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
     payload=json.dumps(dict(object='list',data=[dict(id='gpt-6.1-sol',object='model',owned_by='fixture')])).encode();self.send_response(200);self.end_headers();self.wfile.write(payload)
    def do_POST(self):
     try:
      body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));api['bodies'].append(body)
      if request_source(body)=='thread_title':events=message_events('{"title":"T216"}',body['model'])
      else:
       items=body['input'];users=[n for n,v in enumerate(items) if v.get('type')=='message' and v.get('role')=='user'];at=users[-1]
       text=json.dumps(items[at],ensure_ascii=False);calls=[v for v in items[at+1:] if v.get('type') in ['custom_tool_call','function_call']]
       if '最小确认' in text and '收件箱 issue' not in text and not calls:
        item=shell_item(request_tools(body),'a2a request executor',f.repo);item['input']='// @exec: {"yield_time_ms": 120000}\n'+item['input'].replace('10000','120000');events=tool_events(item,body['model'])
       else:events=message_events('T216_OK',body['model'])
      self.send_response(200);self.send_header('Content-Type','text/event-stream')
      if a.quota_warning:
       # Round 7: the vendor run that lost its notification showed Codex's weekly-limit banner. Codex 0.164 reads
       # x-codex-{primary,secondary}-{used-percent,window-minutes,reset-at} (binary strings); 92% used is below 10% left.
       for k,v in [('primary-used-percent','10'),('primary-window-minutes','300'),('primary-reset-at',str(int(time.time())+3600)),
                   ('secondary-used-percent','92'),('secondary-window-minutes','10080'),('secondary-reset-at',str(int(time.time())+259200))]:
        self.send_header('x-codex-'+k,v)
      self.end_headers()
      for sequence,(name,data) in enumerate(events):self.wfile.write(('event: '+name+'\ndata: '+json.dumps(dict(type=name,sequence_number=sequence,**data))+'\n\n').encode())
      self.wfile.flush()
     except Exception as error:api['error']=repr(error);self.send_error(500)
   responses=ThreadingHTTPServer(('127.0.0.1',0),Responses);threading.Thread(target=responses.serve_forever,daemon=True).start()
  f.start(shutil.which('claude'),{'check.py':'raise SystemExit(0)\n'});f.card('T-1','done.txt','check.py')
  assert f.request('role_release',f.terminal)['ok']
  window=f.request('window_open',f.operator,launch=f.terminal_launch,project='demo')['identity'];sequence=0
  r['hc']=json.loads((f.state/'hc-runtime.json').read_text());r['version']=subprocess.check_output([shutil.which(a.cli),'--version'],text=True).strip()
  if a.cli=='codex':
   codex_home=f.dir/'codex-home';codex_home.mkdir(mode=0o700)
   if a.vendor:
    shutil.copy2(Path.home()/'.codex/auth.json',codex_home/'auth.json')
    (codex_home/'rules').mkdir()
    (codex_home/'rules/default.rules').write_text('prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n',encoding='utf-8')
   config='model="gpt-6.1-sol"\nmodel_reasoning_effort="high"\ncli_auth_credentials_store="file"\ncheck_for_update_on_startup=false\n'+f'[projects.{json.dumps(str(f.repo))}]\ntrust_level="trusted"\n'
   if responses:config+='\n[model_providers.t216]\nname="T216 fixture"\nbase_url="http://127.0.0.1:'+str(responses.server_port)+'/v1"\nwire_api="responses"\nrequires_openai_auth=false\n'
   (codex_home/'config.toml').write_text(config,encoding='utf-8')
   cmd='CODEX_HOME='+quote(str(codex_home))+' codex '+('--sandbox danger-full-access -a never' if responses else '--sandbox workspace-write -a on-request')+' -c check_for_update_on_startup=false'+(' -c model_provider="t216"' if responses else '')
  else:
   cmd='/usr/bin/env -u ANTHROPIC_BASE_URL -u ANTHROPIC_AUTH_TOKEN HOME='+quote(str(Path.home()))+' '+a.cli+(' --dangerously-skip-permissions' if a.cli=='agy' else ' --auto')
  native_start=int(time.time()*1000)-1000;r['start_ms']=native_start;r['controller_command']=cmd
  gemini=Path.home()/'.gemini/antigravity-cli/settings.json';before=json.loads(gemini.read_text()) if a.cli=='agy' else None
  send(cmd+'\r')
  if a.cli=='codex':
   f.wait('Codex hooks 信任',lambda:'2.Trustallandcontinue' in screen(),90);send('2');f.wait('明确选中第二项',lambda:'›2.Trustallandcontinue' in screen(),20);send('\r')
  # Trust handling follows T-187: verify this folder and the selected Yes before Enter; verify exactly one new trust entry.
  trust=False
  deadline=time.monotonic()+120
  while True:
   reports=re.findall(r'\x1b\]7501;([^\x07\x1b]*)',raw())
   if reports and reports[-1].startswith(('state=idle','state=done')):break
   if a.cli=='agy' and not trust and 'Doyoutrustthecontentsofthisproject?' in screen():
    text=screen();check('trust_own_folder_only',str(f.repo).replace(' ','') in text and '>Yes,Itrustthisfolder' in text)
    send('\r');trust=True
   assert time.monotonic()<deadline,'CLI 没有可接收状态'
   time.sleep(.3)
  if before is not None:
   after=json.loads(gemini.read_text());old=before.get('trustedWorkspaces',[]);now=after.get('trustedWorkspaces',[])
   check('trust_exact_write',dict(before,trustedWorkspaces=now)==after and all(v in now for v in old) and [v for v in now if v not in old]==([str(f.repo)] if trust else []))
   r['trust_entries_written']=len([v for v in now if v not in old])
  time.sleep(3) # T-211/T-187: opencode's first idle precedes its input cursor.
  send('\x1b[200~'+PROMPT+'\x1b[201~');time.sleep(1);send('\r')
  def pending_role():
   # The fixture user may allow only this exact one-shot local role request. Never select the prefix grant.
   if a.cli=='codex' and a.vendor and not r.get('command_approval') and '$a2arequestexecutor›1.Yes,proceed(y)' in screen()[-1800:]:
    send('\r');r['command_approval']='a2a request executor, one call only'
   return f.request('sidebar_snapshot').get('role_requests')
  pending=f.wait('真实 CLI 申请',pending_role,180)
  check('native_cli_requested_role',pending[0]['cli']==a.cli,pending[0]['cli']);assert f.request('role_request_decide',f.operator,role_request=pending[0]['id'],approved=True)['ok']
  f.wait('批准生效',lambda:f.request('terminal_whoami',f.terminal).get('role')=='executor',60)
  f.wait('申请回合完成',lambda:(lambda v:v and v[-1].startswith(('state=idle','state=done')))(re.findall(r'\x1b\]7501;([^\x07\x1b]*)',raw())),120)
  initial=native();r['initial_native']=initial
  assert f.request('dispatch',f.terminal,task='T-1',runtimeMode='workspace-write')['ok']
  issue=f.wait('worker 上报',lambda:(lambda v:v['issues'][0]['issue'] if v['issues'] else None)(f.request('issues',f.operator,task='T-1')),120);r['issue']=issue
  def actual():
   data=native()
   if a.cli=='opencode':return [v for v in data if v.get('type')=='user' and issue['id'] in json.dumps(v['data'],ensure_ascii=False)]
   return [v for v in data if '\n收件箱 issue '+issue['id']+'\n' in v.get('text','')]
  f.wait('CLI 原生记录收件',lambda:actual(),120)
  f.wait('hc 关联确认',lambda:any(e['type']=='hc_send_result' and e['data'].get('confirmation')=='confirmed' for e in f.request('orchestration_events')['events']),30)
  time.sleep(8);count=actual();r['actual_submissions']=count
  check('native_actual_once',len(count)==1,count)
  check('original_body',nonce in json.dumps(count,ensure_ascii=False))
  inp=f.request('user_input_records',f.operator,project='demo');assert inp['ok'];check('system_not_user',issue['id'] not in json.dumps(inp['records']))
  r['events']=[e for e in f.request('orchestration_events')['events'] if e['type'].startswith('hc_')]
  r['api_error']=api['error'];check('local_api_healthy',not api['error'])
  r['status']='PASS'
 except BaseException as error:
  import traceback
  r['error']=repr(error);r['traceback']=traceback.format_exc();print(r['traceback'])
 finally:
  try:f.stop()
  finally:
   r['cleanup']=stop_private_core(f.dir,f.env)
   if responses:responses.shutdown()
   if codex_home:
    # Keep own rollout only, never auth/config; then remove the entire isolated CODEX_HOME.
    if (codex_home/'sessions').exists():shutil.copytree(codex_home/'sessions',f.out/'codex-sessions')
    shutil.rmtree(codex_home);r['codex_home_removed']=not codex_home.exists()
   # Publish only redacted terminal text; no agy screenshots (account email).
   trace=f.state/'traces'/str(f.terminal_launch)/'pty.raw'
   if trace.exists():
    text=trace.read_text(encoding='utf-8',errors='replace');text=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '<email>',text)
    (f.out/'terminal-redacted.txt').write_text(text,encoding='utf-8')
   clean=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','<email>',json.dumps(r,ensure_ascii=False,indent=2))
   a.summary.write_text(clean+'\n',encoding='utf-8')
 print(json.dumps(dict(status=r['status'],error=r.get('error'),summary=str(a.summary)),ensure_ascii=False))
 return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
