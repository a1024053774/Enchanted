"""第六轮：真实 Claude/Codex + 本地接口、私有 hc、真实终端钩子。
失败方式先列：
1. ↑ 历史提交只有方向键，候选误丢 UserPromptSubmit。
2. @ 文件补全后原文不同于 attach 字符，候选误丢完整提示词。
3. 系统投递混入用户输入；尚未送出的派发误吞无关用户输入。
4. 一条已送派发重复认领，用户再次提交相同正文被吞；重启丢认领。
5. intent 落库但实际 RPC 未发就退出，重启后用户相同正文被误认系统。
6. 实际已送但 hc 返回尚未落库即退出，重启后迟到的系统 UPS 误记用户。
第七轮按执行主控决定改第 5 条的期望：派发正文以唯一的 ⟦主控 #序号⟧ 开头并带收件箱 UUID，
意图已写、未认领的派发全文被提交时认领为系统；RPC 未发即退出、用户之后逐字提交同一全文，
这一相反窗口记为系统是主控接受的代价。第六轮的 unsent 红绿态证据原样保留。
--revision 跑基线；--mutant attach-only 恢复已知坏判断；--mutant require-hc-return 恢复第六轮
“须有发送中 RPC 或 hc 成功返回才认领”，第 6 条应失败。own-hooks.jsonl 是 CLI 独立钩子原文。
"""
import argparse,json,re,shutil,sys,threading,time,uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from scripted_claude import Fixture,quote,gate_line,source_tree
from t112_native_api import message_events,request_source,request_tools,shell_item,tool_events


def main():
 p=argparse.ArgumentParser();p.add_argument('--cli',choices=['claude','codex'],required=True);p.add_argument('--revision');p.add_argument('--mutant',choices=['attach-only','require-hc-return']);p.add_argument('--case',choices=['history','completion','provenance','never-sent','delayed-hook'],default='history');p.add_argument('--summary',type=Path,required=True);a=p.parse_args();assert not a.summary.exists()
 r=dict(status='INCOMPLETE',command=sys.argv,checks=[],supplier_calls=0);nonce=uuid.uuid4().hex;REQUEST='T216_REQUEST_'+nonce;HISTORY='T216_HISTORY_'+nonce;filename='T216_completion_'+nonce+'.txt'
 def plan(body):
  text=json.dumps(body['messages'],ensure_ascii=False)
  if '显式交付' in text:
   return 'worker',[('Bash',dict(command=gate_line(body,"'issue' '--task' '{task}' '--title' '来源核对' '--body' "+quote('系统正文-'+nonce)+" '--blocking' 'false'"),description='report'))],'已上报。'
  if REQUEST in text:return 'controller',[('Bash',dict(command='a2a request executor',description='role'))],'T216_READY'
  return 'user',[],'T216_OK'
 f=Fixture('t216-r6-prompt-',plan,revision=a.revision);r['fixture']=str(f.dir);responses=None;api={'error':None,'bodies':[]};sequence=0
 def check(name,ok,detail=None):
  r['checks'].append(dict(name=name,passed=bool(ok),detail=detail));assert ok,(name,detail)
 def send(data):
  nonlocal sequence
  sequence+=1;x=f.request('window_input',window,sequence=sequence,request_id=str(uuid.uuid4()),data=data);assert x['ok'],x
 def raw():return (f.state/'traces'/f.terminal_launch/'pty.raw').read_text(encoding='utf-8',errors='replace')
 def screen():return re.sub(r'\s+','',''.join(re.split(r'\x1b\[[0-9;?<>=]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)',raw())))
 def hooks():
  path=f.out/'own-hooks.jsonl'
  return [json.loads(s) for s in path.read_text().splitlines() if s.strip()] if path.exists() else []
 def inputs():return f.request('user_input_records',f.operator,project='demo')['records']
 def submitted():return [v for v in hooks() if v.get('hook_event_name')=='UserPromptSubmit']
 def done(after):
  f.wait('原生 Stop',lambda:sum(v.get('hook_event_name')=='Stop' for v in hooks())>after,60)
  time.sleep(1)
 def submit(text):
  before=sum(v.get('hook_event_name')=='Stop' for v in hooks());send(text);time.sleep(.4);send('\r');done(before)
 def count(text):return len([v for v in inputs() if v.get('text')==text])
 try:
  if a.revision:
   # Only provide the same pinned released hc, avoiding download in the old source copy.
   cache=f.source/'workbench/hc';cache.mkdir()
   for name in ['herdr-core','LICENSE','THIRD-PARTY-NOTICES']:shutil.copy2(Path('/private/tmp/t216-r2-rklei589/state/hc/bin')/name,cache/name)
  patches=[]
  if a.mutant=='attach-only':
   # Restore only the old provenance gate, including its exact attach composition; never patch the oracle.
   patches+=[('src/daemon.ts','!panes.claimShellInboxPrompt(terminal.id, payload.prompt)','panes.terminalUserPrompt(terminal.id, payload.prompt)'),
    ('src/panes.ts','  shellOscSequence?: number;','  shellUserPrompts?: string[];\n  shellOscSequence?: number;'),
    ('src/panes.ts','      feedInput(pane.draft, data,','      const prompts = feedInput(pane.draft, data,'),
    ('src/panes.ts','      pane.userDraft = Boolean(pane.draft.chars.length || pane.draft.uncertain);','      if (this.approvedController?.(pane.record.thread)) (pane.shellUserPrompts ??= []).push(...prompts.map(prompt => prompt.text));\n      pane.userDraft = Boolean(pane.draft.chars.length || pane.draft.uncertain);'),
    ('src/panes.ts','  claimShellInboxPrompt(launch: string, prompt: unknown): boolean {','''  terminalUserPrompt(launch: string, prompt: unknown): boolean {
    const pane = this.byLaunch(launch), text = typeof prompt === "string" ? claudeSubmittedText(prompt) : null;
    const index = pane.shellUserPrompts?.findIndex(value => claudeSubmittedText(value) === text) ?? -1;
    if (index < 0) return false;
    pane.shellUserPrompts!.splice(index, 1); return true;
  }
  claimShellInboxPrompt(launch: string, prompt: unknown): boolean {''')]
  if a.mutant=='require-hc-return':
   # Round 6's claim rule: a live synchronous RPC or a persisted hc success return was required.
   patches+=[('src/panes.ts','      if (latest?.type === "hc_send_rejected" || item.text !== text) continue;',
     '''      const returned = this.store.db.prepare(`SELECT 1 FROM orchestration_events WHERE launch=?
        AND type='hc_send_result' AND json_extract(data,'$.dispatch')=?`).get(launch, id);
      if (latest?.type === "hc_send_rejected" || !(pane.sending === id || returned) || item.text !== text) continue;''')]
  if a.case=='never-sent':
   assert not a.revision and not a.mutant
   f.env['T216_SEND_BARRIER']=str(f.out/'before-send')
   patches+=[('src/hc.ts','  send(params: { terminal: string; text: string; caller: string; wait: true; timeout: number; if?: "idle" }) {','  async send(params: { terminal: string; text: string; caller: string; wait: true; timeout: number; if?: "idle" }) {'),
     ('src/hc.ts',"return this.connection.call('terminal.send',",'''await import('node:fs/promises').then(async fs => {
      await fs.writeFile(process.env.T216_SEND_BARRIER, 'RPC not yet sent');
      await new Promise(() => {});
    });
    return this.connection.call('terminal.send',''')]
  if a.case=='delayed-hook':
   assert not a.revision and a.mutant in (None,'require-hc-return')
   f.env['T216_LATE_HOOK']=str(f.out/'late-hook')
   patches+=[('src/terminalCli.ts','      // T-195: which CLI process runs this hook,','''      const packet = JSON.parse(Buffer.concat(chunks).toString("utf8"));
      if (packet.hook_event_name === "UserPromptSubmit" && packet.prompt?.includes("收件箱 issue")) {
        const fs = await import('node:fs/promises'), base = process.env.T216_LATE_HOOK!;
        await fs.writeFile(base + '.ready', Buffer.concat(chunks));
        while (!(await fs.access(base + '.release').then(() => true, () => false))) await new Promise(r => setTimeout(r, 20));
      }
      // T-195: which CLI process runs this hook,'''),
     ('terminal/plugin/enchanted-a2a/hooks/hooks.json','"UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "\\\"$A2A_TERMINAL_BIN/a2a\\\" hook", "timeout": 10 }] }]','"UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "\\\"$A2A_TERMINAL_BIN/a2a\\\" hook", "timeout": 30 }] }]')]
  if patches:f.source=source_tree(f.dir,patches=patches);f.cli=f.source/'workbench/src/gates/cli.ts'
  if a.cli=='codex':
   class Responses(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
     self.send_response(200);self.end_headers();self.wfile.write(b'{"data":[{"id":"gpt-6.1-sol"}]}')
    def do_POST(self):
     try:
      body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));api['bodies'].append(body)
      if request_source(body)=='thread_title':events=message_events('{"title":"T216"}',body['model'])
      else:
       items=body['input'];at=max(n for n,v in enumerate(items) if v.get('type')=='message' and v.get('role')=='user');text=json.dumps(items[at],ensure_ascii=False);calls=[v for v in items[at+1:] if v.get('type') in ['custom_tool_call','function_call']]
       if REQUEST in text and not calls:
        item=shell_item(request_tools(body),'a2a request executor',f.repo);item['input']='// @exec: {"yield_time_ms": 120000}\n'+item['input'].replace('10000','120000');events=tool_events(item,body['model'])
       else:events=message_events('T216_OK',body['model'])
      self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
      for seq,(name,data) in enumerate(events):self.wfile.write(('event: '+name+'\ndata: '+json.dumps(dict(type=name,sequence_number=seq,**data))+'\n\n').encode())
      self.wfile.flush()
     except Exception as error:api['error']=repr(error);self.send_error(500)
   responses=ThreadingHTTPServer(('127.0.0.1',0),Responses);threading.Thread(target=responses.serve_forever,daemon=True).start()
   home=f.home/'.codex';home.mkdir();(home/'config.toml').write_text('model="gpt-6.1-sol"\nmodel_provider="t216"\ncheck_for_update_on_startup=false\ncli_auth_credentials_store="file"\n'+f'[projects.{json.dumps(str(f.repo))}]\ntrust_level="trusted"\n[model_providers.t216]\nname="T216 fixture"\nbase_url="http://127.0.0.1:{responses.server_port}/v1"\nwire_api="responses"\nrequires_openai_auth=false\n',encoding='utf-8')
   (home/'hooks.json').write_text(json.dumps({'hooks':{name:[{'hooks':[dict(type='command',command=f"{{ cat; echo; }} >> '{f.out}/own-hooks.jsonl'",timeout=10)]}] for name in ['UserPromptSubmit','Stop']}}),encoding='utf-8')
  f.start(shutil.which('claude'),{'check.py':'raise SystemExit(0)\n',filename:'completion fixture\n'})
  r['hc']=json.loads((f.state/'hc-runtime.json').read_text());assert f.request('role_release',f.terminal)['ok']
  window=f.request('window_open',f.operator,launch=f.terminal_launch,project='demo')['identity']
  if a.cli=='claude':
   config=f.home/'.claude.json';value=json.loads(config.read_text());value.update(hasSeenAutoDefaultNudge=True,projects={str(f.repo):{'hasTrustDialogAccepted':True}});config.write_text(json.dumps(value),encoding='utf-8')
   settings=f.out/'settings.json';settings.write_text(json.dumps(dict(hooks={name:[dict(hooks=[dict(type='command',command=f"{{ cat; echo; }} >> '{f.out}/own-hooks.jsonl'",timeout=10)])] for name in ['UserPromptSubmit','Stop']})),encoding='utf-8')
   send('claude --model claude-haiku-5-5 --effort low --permission-mode dontAsk --allowedTools Bash --settings '+quote(str(settings))+' '+REQUEST+'\r')
  else:
   send('codex --sandbox danger-full-access -a never\r');f.wait('钩子信任',lambda:'2.Trustallandcontinue' in screen(),90);send('2');f.wait('明确选中信任全部',lambda:'›2.Trustallandcontinue' in screen(),20);send('\r');time.sleep(3);send(REQUEST);time.sleep(.5);send('\r')
  pending=f.wait('原生角色申请',lambda:f.request('sidebar_snapshot').get('role_requests'),90);assert f.request('role_request_decide',f.operator,role_request=pending[0]['id'],approved=True)['ok'];done(0)
  if a.case=='history':
   submit(HISTORY);check('first_prompt_recorded',count(HISTORY)==1,inputs());submit('\x1b[A')
   own=[v for v in submitted() if v.get('prompt')==HISTORY];check('native_history_submitted_twice',len(own)==2,submitted());time.sleep(1);check('history_user_recorded_twice',count(HISTORY)==2,inputs())
  elif a.case=='completion':
   before=sum(v.get('hook_event_name')=='Stop' for v in hooks());send('@T216_comp');time.sleep(2);send('\t');time.sleep(2);send(' say OK');time.sleep(.5);send('\r');done(before)
   own=submitted()[-1];r['completion_hook']=own;r['completion_typed']='@T216_comp<Tab> say OK';check('native_completed_filename',filename in own.get('prompt',''),own);check('completion_user_recorded',any(v.get('text')==own['prompt'] for v in inputs()),inputs())
  elif a.case in ['never-sent','delayed-hook']:
   import os,signal,subprocess
   f.card('T-1','done.txt','check.py');assert f.request('dispatch',f.terminal,task='T-1',runtimeMode='workspace-write')['ok']
   f.wait('原生迟到钩子屏障' if a.case=='delayed-hook' else '发送之前屏障',lambda:(f.out/('late-hook.ready' if a.case=='delayed-hook' else 'before-send')).exists(),120)
   intent=next(e for e in f.request('orchestration_events')['events'] if e['type']=='hc_send_intent');r['intent']=intent
   check('system_actual_received_before_crash' if a.case=='delayed-hook' else 'no_native_system_submission_before_crash',bool(any('收件箱 issue' in v.get('prompt','') for v in submitted()))==(a.case=='delayed-hook'),submitted())
   check('hc_result_not_persisted_before_crash',not any(e['type']=='hc_send_result' for e in f.request('orchestration_events')['events']))
   old=f.request('daemon_status');assert old['root']==str(f.state) and old['pid']==int((f.state/'daemon.pid').read_text());os.kill(old['pid'],signal.SIGKILL);f.running=False
   f.wait('仅自有后台退出',lambda:not subprocess.run(['/bin/ps','-p',str(old['pid']),'-o','stat='],capture_output=True,text=True).stdout.strip(),10)
   f.env['A2A_OPERATOR_CREDENTIAL']=str(f.dir/('operator-'+uuid.uuid4().hex+'.json'));f.run_cli('daemon_start','--launch-config',str(f.dir/'launch-config.json'));f.running=True
   f.wait('重接完成',lambda:f.request('pane_layout').get('recovering') is False,20);f.operator=json.loads(Path(f.env['A2A_OPERATOR_CREDENTIAL']).read_text());window=f.request('window_open',f.operator,launch=f.terminal_launch,project='demo')['identity'];sequence=0
   if a.case=='delayed-hook':
    before=sum(v.get('hook_event_name')=='Stop' for v in hooks());(f.out/'late-hook.release').write_text('release',encoding='utf-8');done(before)
    check('late_system_not_user',not any('收件箱 issue' in v.get('text','') for v in inputs()),inputs())
    check('late_system_claim_once',len([e for e in f.request('orchestration_events')['events'] if e['type']=='hc_inbox_prompt_claimed'])==1)
   else:
    # Executor decision (round 7): the unique label and inbox UUID make this text ours; it is claimed as system.
    text=intent['data']['text'];submit('\x1b[200~'+text+'\x1b[201~')
    check('unsent_body_claimed_as_system',not any('收件箱 issue' in v.get('text','') for v in inputs()),inputs())
    check('intent_only_claimed_once',len([e for e in f.request('orchestration_events')['events'] if e['type']=='hc_inbox_prompt_claimed'])==1)
    # The same full text submitted a second time is the user's.
    submit('\x1b[200~'+text+'\x1b[201~')
    check('second_identical_submit_is_user',len([v for v in inputs() if '收件箱 issue' in v.get('text','')])==1,inputs())
  else:
   # Force a draft reservation via attach, then dispatch through the real gate. It must stay unsent.
   send('USER_UNRELATED_'+nonce);f.card('T-1','done.txt','check.py');assert f.request('dispatch',f.terminal,task='T-1',runtimeMode='workspace-write')['ok']
   view=f.wait('上报',lambda:(lambda v:v['issues'][0] if v['issues'] else None)(f.request('issues',f.operator,task='T-1')),120);issue=view['issue'];time.sleep(2)
   check('queued_not_sent',not any(e['type']=='hc_send_intent' for e in f.request('orchestration_events')['events']))
   before=sum(v.get('hook_event_name')=='Stop' for v in hooks());send('\r');done(before)
   check('unrelated_user_recorded',count('USER_UNRELATED_'+nonce)==1,inputs())
   f.wait('系统投递钩子',lambda:any(issue['id'] in v.get('prompt','') for v in submitted()),60);time.sleep(3)
   system=next(v['prompt'] for v in submitted() if issue['id'] in v.get('prompt',''));check('system_not_user',not any(issue['id'] in v.get('text','') for v in inputs()),inputs())
   # Real CLI history recalls exactly that same system body; this is a second native submission, now by the user.
   submit('\x1b[A');own=[v for v in submitted() if v.get('prompt')==system];r['replayed_native_count']=len(own)
   check('same_system_body_second_native_submit',len(own)==2,submitted());check('same_body_claim_once',len([v for v in inputs() if issue['id'] in v.get('text','')])==1,inputs())
  check('local_api_healthy',not api['error'] and not f.api.error,api['error']);r['status']='PASS'
 except BaseException as error:
  import traceback
  r['error']=repr(error);r['traceback']=traceback.format_exc();print(r['traceback'])
 finally:
  r['hooks']=hooks()
  if f.running:r['inputs']=inputs()
  try:f.stop()
  finally:
   r['cleanup']=getattr(f,'core_cleanup',None)  # Fixture.stop stops the private core (T-232)
   if responses:responses.shutdown()
   a.summary.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(status=r['status'],summary=str(a.summary),error=r.get('error')),ensure_ascii=False));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
