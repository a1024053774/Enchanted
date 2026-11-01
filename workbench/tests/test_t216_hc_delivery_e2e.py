"""T-216 hc 投递：真实后台/socket/门禁/私有 hc；替身只替换终端里的供应商 CLI。

先列失败方式（期望来自第五轮任务书）：
1. idle 不带 if 原子条件，done 错用 if:idle；wait 误认独立 working 为送入确认。
2. agy/opencode 因无 native session 被排除；目标 CLI/终端/批准角色已换仍收件。
3. blocked 被误答：只去掉后台过滤仍应由 hc 拒绝；再加 force 则应被测试拒绝。
4. 忙时送入；idle 在送入前变 working 未被 hc 拒绝；恢复后丢失/重排/重复。
5. 用户草稿混入系统提交，草稿清空/提交后不恢复；重接丢草稿，混入系统文字。
6. hc 已送入但没开始回合仍称 delivered；未知自动重发，CLI 收到两次。
7. 系统投递混入 user_inputs/人工介入，或缺 dispatch/终端/hc 返回/确认记录。
8. UI 不显示未知；队列只数登记却没数替身自己实际读到的提交。
9. 重启丢掉未送的队列；送入 intent 与确认之间后台退出，界面却无未知，或重复送入。
10. 未知永久堵住后续投递；没等 CLI 消费遗留文字就送下一条，混在同次提交；重启丢恢复事实。

替身通过产品 shim 运行，argv 为 node <...>/agy 或 opencode（产品 cliProgram 的真实识别入口）；
按 T-211 报 OSC 7501，逐条保存实际回车提交，不导入产品代码/模板作为 oracle。
--case basic 可在修前候选取得 agy/opencode 红态；--source 运行冻结源码。
变异只在测试自建源码副本，--race 的屏障也仅插入副本的 RPC 边界，hc 与断言不变。
"""
import argparse,json,os,shutil,subprocess,sys,time,uuid
from pathlib import Path
from scripted_claude import Fixture,Electron,gate_line,prompt_text,quote,source_tree
from test_t212_shell_hc_e2e import stop_private_core

FAKE = r'''#!/usr/bin/env node
const fs=require('fs'),cp=require('child_process'),path=require('path');
const root=process.env.T216_FAKE_ROOT,cli=path.basename(__filename),end=cli==='agy'?'done':'idle';
process.env.OPENCODE_SESSION_ID='fixture-native-id';
const file=(name)=>path.join(root,name);
function osc(state,kind){process.stdout.write('\x1b]7501;state='+state+(kind?':kind='+kind:'')+'\x07');}
process.stdin.setRawMode(true);process.stdin.resume();process.stdout.write('\x1b[?2004h');
let line='',paste=false,carry='',last=null,mode='normal';
function commit(){fs.appendFileSync(file('submissions.jsonl'),JSON.stringify({id:require('crypto').randomUUID(),text:line,at:Date.now()})+'\n');line='';osc('working');if(mode!=='consume-working')setTimeout(()=>osc(end),300);}
function control(){
 if(!fs.existsSync(file('control.json')))return;
 const text=fs.readFileSync(file('control.json'),'utf8');if(text===last)return;last=text;
 const v=JSON.parse(text);mode=v.mode||'normal';if(mode==='exit')process.exit(0);if(v.state)osc(v.state,v.kind);
 if(v.consume)commit();
 if(v.request)cp.spawn('a2a',['request',v.request],{stdio:['ignore',fs.openSync(file('role-next.log'),'a'),fs.openSync(file('role-next.log'),'a')]});
 fs.writeFileSync(file('ack.json'),text);
}
osc('blocked','auth');
const ask=cp.spawn('a2a',['request','executor'],{stdio:['ignore',fs.openSync(file('role.log'),'a'),fs.openSync(file('role.log'),'a')]});
ask.on('exit',code=>{fs.writeFileSync(file('approved'),String(code));control();});
setInterval(control,20);
process.stdin.on('data',chunk=>{
 carry+=chunk.toString('utf8');
 while(carry){
  if(carry.startsWith('\x1b[200~')){paste=true;carry=carry.slice(6);continue;}
  if(carry.startsWith('\x1b[201~')){paste=false;carry=carry.slice(6);continue;}
  if(carry[0]==='\x1b' && carry.length<6)break;
  const c=carry[0];carry=carry.slice(1);
  if(!paste && c==='\r'){
   if(mode==='hold'){fs.writeFileSync(file('held.txt'),line);continue;}
   fs.appendFileSync(file('submissions.jsonl'),JSON.stringify({id:require('crypto').randomUUID(),text:line,at:Date.now()})+'\n');line='';
   if(mode!=='silent'){osc('working');setTimeout(()=>osc(end),300);}
  }else if(!paste && (c==='\x03'||c==='\x15'))line='';
  else if(!paste && (c==='\x7f'||c==='\b'))line=line.slice(0,-1);
  else line+=c;
 }
});
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--cli',choices=['agy','opencode','codex'],required=True)
 p.add_argument('--case',choices=['basic','states','unknown','race','identity','role-change','restart-draft','restart-queue','restart-unknown','recover-unknown','recover-restart'],default='basic');p.add_argument('--summary',type=Path,required=True)
 p.add_argument('--source',type=Path);p.add_argument('--gui',action='store_true')
 p.add_argument('--mutant',choices=['allow-blocked','force-blocked','allow-working','resend-unknown','skip-unknown-wait'])
 a=p.parse_args();assert not a.summary.exists()
 r=dict(status='INCOMPLETE',command=sys.argv,checks=[],real_supplier_calls=0)
 nonce=uuid.uuid4().hex;current={'name':'basic','blocking':False}
 def plan(body):
  assert '显式交付' in prompt_text(body)
  cmd=gate_line(body,"'issue' '--task' '{task}' '--title' "+quote(current['name']+'-'+nonce)+" '--body' "+quote('原文-'+nonce)+" '--blocking' '"+str(current['blocking']).lower()+"'")
  return current['name'],[('Bash',dict(command=cmd,description='report issue'))],'已上报，等待主控。'
 f=Fixture('t216-hc-',plan,source=a.source);r['fixture']=str(f.dir);electron=None
 def check(name,ok,detail=None):
  r['checks'].append(dict(name=name,passed=bool(ok),detail=detail));assert ok,(name,detail)
 def events():return f.request('orchestration_events')['events']
 def rows():
  path=f.out/'submissions.jsonl'
  return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
 def received(issue):return [row for row in rows() if '\n收件箱 issue '+issue['id']+'\n' in row['text']]
 def control(state,mode='normal',kind=None,consume=False):
  obj=dict(state=state,mode=mode,kind=kind,consume=consume);(f.out/'control.json').write_text(json.dumps(obj))
  f.wait('替身状态',lambda:(f.out/'ack.json').exists() and json.loads((f.out/'ack.json').read_text())==obj,10)
  # Poll real hc to know the emitted status is actually parsed; no product state is fabricated.
  f.wait('hc 状态',lambda:hc('terminal.get',terminal=address)['result'].get('status',{}).get('state')==state,10)
 def hc(method,**params):
  import socket
  with socket.socket(socket.AF_UNIX) as c:
   c.settimeout(20);c.connect(manifest['socket']);c.sendall((json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))+'\n').encode());raw=b''
   while b'\n' not in raw:raw+=c.recv(65536)
   return json.loads(raw.split(b'\n')[0])
 def send(text):
  nonlocal sequence
  sequence+=1;x=f.request('window_input',window,sequence=sequence,request_id=str(uuid.uuid4()),data=text);assert x['ok'],x
 def issue(name,blocking=False):
  current.update(name=name,blocking=blocking)
  task='T-'+str(len(raised)+1);f.card(task,task+'.txt','check.py')
  assert f.request('dispatch',f.terminal,task=task,runtimeMode='workspace-write')['ok']
  view=f.wait('问题上报',lambda:(lambda x:x['issues'][0] if x['issues'] else None)(f.request('issues',f.operator,task=task)),120)
  raised.append(view['issue']);return view['issue']
 def delivery(i):
  x=f.request('inbox_list',f.operator,role='executor')
  return next((v.get('delivery') for v in x.get('entries',[]) if v['entry']['id']==i['id']),None)
 def no_input(i,name):
  time.sleep(6)
  check(name,not received(i),dict(submissions=rows(),delivery=delivery(i)))
 def one(i):
  f.wait('CLI 实际提交',lambda:received(i),20)
  f.wait('已确认收件',lambda:(lambda d:d and d['state']=='delivered')(delivery(i)),20)
  time.sleep(.5);check('actual_submit_once_'+i['title'],len(received(i))==1,received(i))
  check('original_content_'+i['title'],'原文-'+nonce in received(i)[0]['text'] and '问题 ' in received(i)[0]['text'],received(i))
 raised=[]
 try:
  # Production mutants are exact textual changes in a fixture copy, never in the worktree.
  patches=[]
  if a.mutant in ['allow-blocked','force-blocked']:
   patches.append(('src/panes.ts','if (!["idle", "done"].includes(state ?? "")) return;','if (!["idle", "done", "blocked"].includes(state ?? "")) return;'))
  if a.mutant=='force-blocked':patches.append(('src/panes.ts','text: item.text, caller: terminal.address, wait: true as const, timeout: 1,','text: item.text, caller: terminal.address, wait: true as const, timeout: 1, force: true,'))
  if a.mutant=='allow-working':patches.append(('src/panes.ts','if (!["idle", "done"].includes(state ?? "")) return;','if (!["idle", "done", "working"].includes(state ?? "")) return;'))
  if a.mutant=='resend-unknown':patches.append(('src/panes.ts','// Unknown is final: the text may already be in the CLI. Never resend.','await (pane.pty as HcTerminal).send(params); // mutant: resend'))
  if a.mutant=='skip-unknown-wait':patches.append(('src/panes.ts','if (pane.inboxUnknown && !this.shellUnknownConsumed(pane)) return;','// mutant: ignore retained unknown input'))
  if a.case=='race':
   patches.append(('src/hc.ts','  send(params: { terminal: string; text: string; caller: string; wait: true; timeout: number; if?: "idle" }) {','  async send(params: { terminal: string; text: string; caller: string; wait: true; timeout: number; if?: "idle" }) {'))
   patches.append(('src/hc.ts',"return this.connection.call('terminal.send',",'''await import('node:fs/promises').then(async fs => {
      if (process.env.T216_SEND_BARRIER) {
        await fs.writeFile(process.env.T216_SEND_BARRIER + '.ready', 'ready');
        while (!(await fs.access(process.env.T216_SEND_BARRIER + '.release').then(() => true, () => false))) await new Promise(r => setTimeout(r, 20));
      }
    });
    return this.connection.call('terminal.send','''))
   f.env['T216_SEND_BARRIER']=str(f.out/'barrier')
  if patches:
   assert not a.source,'不要组合 source 与变异'
   f.source=source_tree(f.dir,patches=patches);f.cli=f.source/'workbench/src/gates/cli.ts'
  fakebin=f.dir/'fakebin';fakebin.mkdir();program=fakebin/a.cli;program.write_text(FAKE);program.chmod(0o755)
  f.env['PATH']=str(fakebin)+':'+f.env['PATH'];f.env['T216_FAKE_ROOT']=str(f.out)
  f.start(shutil.which('claude'),{'check.py':'raise SystemExit(0)\n'})
  manifest=json.loads((f.state/'hc-runtime.json').read_text());r['hc']=manifest
  shell=next(e for e in events() if e['type']=='shell_created' and e['launch']==f.terminal_launch);address=shell['data']['hc_terminal']
  assert f.request('role_release',f.terminal)['ok']
  view=f.request('window_open',f.operator,launch=f.terminal_launch,project=f.project);window=view['identity'];sequence=0
  # codex fixture is recognized through its argv and role environment, like the other shims.
  if a.cli=='codex':
   s=program.read_text().replace("process.env.OPENCODE_SESSION_ID='fixture-native-id';","process.env.CODEX_THREAD_ID='00000000-0000-4000-8000-000000000001';")
   program.write_text(s)
  send(a.cli+'\r')
  pending=f.wait('替身实际 a2a request',lambda:f.request('sidebar_snapshot').get('role_requests'),30)
  assert f.request('role_request_decide',f.operator,role_request=pending[0]['id'],approved=True)['ok']
  f.wait('批准送回替身',lambda:(f.out/'approved').exists(),20)
  held=f.request('terminal_whoami',f.terminal);r['role']=held
  check('actual_cli_role',held['role']=='executor' and held['role_requests'][-1]['cli']==a.cli,held)
  if a.case=='basic':
   control('done' if a.cli=='agy' else 'idle')
   i=issue('basic');time.sleep(8)
   check('issue_reaches_cli',len(received(i))==1,dict(actual=received(i),delivery=delivery(i),events=events()[-12:]))
   one(i)
  elif a.case=='states':
   i=issue('auth',True);no_input(i,'startup_auth_no_input')
   control('done' if a.cli=='agy' else 'idle');one(i)
   control('working');i=issue('busy');no_input(i,'working_no_input')
   control('done' if a.cli=='agy' else 'idle');one(i)
   control('blocked',kind='question');i=issue('question');no_input(i,'blocked_question_no_input')
   if a.mutant in ['allow-blocked','force-blocked']:
    check('hc_rejected_blocked',any(e['type']=='hc_send_rejected' and e['data'].get('error',{}).get('data',{}).get('kind')=='blocked' for e in events()),events()[-20:])
   control('done' if a.cli=='agy' else 'idle');one(i)
   send('用户未完成-'+nonce);i=issue('draft');no_input(i,'draft_no_input')
   send('\r');one(i)
   user=[v for v in rows() if v['text']=='用户未完成-'+nonce]
   check('draft_separate_submission',len(user)==1 and not any('收件箱' in v['text'] and '用户未完成' in v['text'] for v in rows()),rows())
   send('需要清空');i=issue('clear');no_input(i,'draft_before_clear_no_input')
   send('\x03');one(i)
  elif a.case=='unknown':
   control('idle',mode='silent');i=issue('silent')
   f.wait('实际收件但没开始',lambda:received(i),20)
   f.wait('未知回执',lambda:(lambda d:d and d['state']=='unknown')(delivery(i)),25)
   time.sleep(8);check('unknown_never_resent',len(received(i))==1,dict(rows=rows(),delivery=delivery(i)))
   event=next(e for e in events() if e['type']=='hc_send_result' and e['data'].get('dispatch'))
   check('unknown_hc_receipt',event['data']['result'].get('started') is False and event['data']['result']['wait']['reason']=='not_started',event)
   if a.gui:
    electron=Electron(f,'t216-hc-'+uuid.uuid4().hex[:8]);electron.until('项目','!!document.querySelector(\'[data-project-id="demo"]\')');electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
    # Sidebar and terminal surface must show unknown, with the dispatch still inspectable.
    electron.until('未知可见','document.body.innerText.includes("投递确认未知")')
    shot=a.summary.with_suffix('.png');electron.screenshot(shot);r['screenshot']=str(shot)
    check('electron_unknown_visible',True)
  elif a.case=='race':
   control('idle');i=issue('race')
   f.wait('RPC 前屏障',lambda:(f.out/'barrier.ready').exists(),20)
   control('working');(f.out/'barrier.release').write_text('release')
   f.wait('原子拒绝',lambda:any(e['type']=='hc_send_rejected' for e in events()),20)
   no_input(i,'atomic_idle_mismatch_no_input')
   reject=next(e for e in events() if e['type']=='hc_send_rejected')
   check('hc_status_mismatch',reject['data']['error']['data']['kind']=='status_mismatch',reject)
   control('idle');one(i)
  elif a.case in ['recover-unknown','recover-restart']:
   control('idle',mode='hold');i=issue('held-unknown')
   f.wait('遗留未提交文字',lambda:(f.out/'held.txt').exists(),20)
   f.wait('未知回执',lambda:(lambda d:d and d['state']=='unknown')(delivery(i)),25)
   j=issue('after-unknown');time.sleep(8)
   r['hc_retained_before_consumption']=hc('terminal.get',terminal=address)
   r['intents_before_consumption']=[e for e in events() if e['type']=='hc_send_intent']
   if a.case=='recover-restart':
    # The consumption fact exists before daemon restart; its durable OSC events must suffice after reattach.
    control('working',mode='consume-working',consume=True)
    f.wait('原始未知文字被 CLI 消费',lambda:received(i),10)
    f.wait('working 已持久化',lambda:any(e['type']=='shell_osc7501' and e['data']['state']=='working' and e['seq']>next(v['seq'] for v in events() if v['type']=='dispatch_unknown') for e in events()),10)
    f.run_cli('daemon_stop');f.running=False;f.wait('后台退出',lambda:not (f.state/'control.sock').exists(),15)
    f.env['A2A_OPERATOR_CREDENTIAL']=str(f.dir/('operator-'+uuid.uuid4().hex+'.json'))
    f.run_cli('daemon_start','--launch-config',str(f.dir/'launch-config.json'));f.running=True
    f.wait('重接',lambda:f.request('pane_layout').get('recovering') is False,20);f.operator=json.loads(Path(f.env['A2A_OPERATOR_CREDENTIAL']).read_text())
    window=f.request('window_open',f.operator,launch=f.terminal_launch,project='demo')['identity'];sequence=0;control('idle')
   else:control('working',mode='normal',consume=True)
   time.sleep(10)
   r['hc_after_consumption']=hc('terminal.get',terminal=address)
   check('separate_submissions',not any(i['id'] in v['text'] and j['id'] in v['text'] for v in rows()),rows())
   check('unknown_waits_for_consumption',len(r['intents_before_consumption'])==1,r['intents_before_consumption'])
   check('later_dispatch_resumes',len(received(j))==1,dict(rows=rows(),delivery=delivery(j)))
   check('unknown_original_never_resent',len(received(i))==1 and len([e for e in events() if e['type']=='hc_send_intent' and e['data']['dispatch']==next(v['data']['dispatch'] for v in events() if v['type']=='dispatch_unknown')])==1,rows())
   check('original_remains_unknown',delivery(i)['state']=='unknown',delivery(i));one(j)
  elif a.case in ['restart-queue','restart-unknown']:
   if a.case=='restart-queue':
    control('working');i=issue('queued-1');time.sleep(2);j=issue('queued-2');no_input(i,'both_queued_before_restart')
   else:
    control('idle',mode='silent');i=issue('sent-before-restart')
    f.wait('hc 实际已送、尚未确认',lambda:received(i) and not any(e['type']=='hc_send_result' for e in events()),20)
   old=f.request('daemon_status');assert old['root']==str(f.state) and old['pid']==int((f.state/'daemon.pid').read_text())
   import signal
   if a.case=='restart-unknown':
    os.kill(old['pid'],signal.SIGKILL);f.running=False
    f.wait('仅自有后台已退出',lambda:not subprocess.run(['/bin/ps','-p',str(old['pid']),'-o','stat='],capture_output=True,text=True).stdout.strip(),10)
   else:
    f.run_cli('daemon_stop');f.running=False;f.wait('原后台退出',lambda:not (f.state/'control.sock').exists(),15)
   f.env['A2A_OPERATOR_CREDENTIAL']=str(f.dir/('operator-'+uuid.uuid4().hex+'.json'))
   f.run_cli('daemon_start','--launch-config',str(f.dir/'launch-config.json'));f.running=True
   f.wait('新后台重接',lambda:f.request('pane_layout').get('recovering') is False,20)
   f.operator=json.loads(Path(f.env['A2A_OPERATOR_CREDENTIAL']).read_text())
   window=f.request('window_open',f.operator,launch=f.terminal_launch,project='demo')['identity'];sequence=0
   if a.case=='restart-queue':
    control('idle');time.sleep(10)
    check('restart_queue_preserved',len(received(i))==1 and len(received(j))==1,dict(rows=rows(),first=delivery(i),second=delivery(j)))
    check('restart_queue_order',[v['text'] for v in rows() if any(x['id'] in v['text'] for x in [i,j])]==[received(i)[0]['text'],received(j)[0]['text']],rows())
   else:
    time.sleep(8)
    snapshot=f.request('sidebar_snapshot');agent=next(v for v in snapshot['agents'] if v['id']==f.terminal_launch)
    check('restart_unconfirmed_shows_unknown',bool(agent.get('inbox_unknown')) and delivery(i)['state']=='unknown',dict(agent=agent,delivery=delivery(i)))
    check('restart_unconfirmed_never_resent',len(received(i))==1,rows())
    if a.gui:
     electron=Electron(f,'t216-hc-'+uuid.uuid4().hex[:8]);electron.until('项目','!!document.querySelector(\'[data-project-id="demo"]\')');electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
     electron.until('中断后未知可见','document.body.innerText.includes("投递确认未知")');shot=a.summary.with_suffix('.png');electron.screenshot(shot);r['screenshot']=str(shot);check('restart_electron_unknown',True)
  elif a.case=='role-change':
   control('working');i=issue('original-executor');no_input(i,'queue_while_original_busy')
   assert f.request('role_release',f.terminal)['ok']
   def role(name):
    (f.out/'control.json').write_text(json.dumps(dict(state='working',request=name,nonce=str(uuid.uuid4()))))
    pending=f.wait('新角色申请',lambda:f.request('sidebar_snapshot').get('role_requests'),20)
    assert f.request('role_request_decide',f.operator,role_request=pending[0]['id'],approved=True)['ok']
    f.wait('新角色生效',lambda:f.request('terminal_whoami',f.terminal).get('role')==name,20)
   role('ideation');control('done');no_input(i,'executor_queue_not_ideation')
   assert f.request('role_release',f.terminal)['ok']
   role('executor');control('done');one(i)
  elif a.case=='restart-draft':
   control('idle');send('重启前草稿-'+nonce)
   f.run_cli('daemon_stop');f.running=False;f.wait('原后台退出',lambda:not (f.state/'control.sock').exists(),15)
   f.env['A2A_OPERATOR_CREDENTIAL']=str(f.dir/'operator-restart.json')
   f.run_cli('daemon_start','--launch-config',str(f.dir/'launch-config.json'));f.running=True
   f.wait('后台重接',lambda:f.request('pane_layout').get('recovering') is False,20)
   f.operator=json.loads(Path(f.env['A2A_OPERATOR_CREDENTIAL']).read_text())
   window=f.request('window_open',f.operator,launch=f.terminal_launch,project='demo')['identity'];sequence=0
   i=issue('restart-draft');no_input(i,'restart_preserves_draft_reservation')
   send('\r');one(i)
   check('restart_draft_separate',len([v for v in rows() if v['text']=='重启前草稿-'+nonce])==1,rows())
  elif a.case=='identity':
   assert a.cli=='agy','反例：已批准 agy 的终端换成 opencode'
   control('idle')
   (f.out/'control.json').write_text(json.dumps(dict(mode='exit')))
   time.sleep(1)
   other=fakebin/'opencode';other.write_text(FAKE);other.chmod(0o755)
   (f.out/'control.json').write_text(json.dumps(dict(state='idle',mode='normal')))
   send('opencode\r')
   f.wait('前台换成 opencode',lambda:any(v['id']==f.terminal_launch and v.get('cli')=='agy' for v in f.request('sidebar_snapshot')['agents']),10)
   time.sleep(3)
   i=issue('different-foreground');no_input(i,'different_cli_never_receives')
   check('approved_terminal_still_alive',f.request('terminal_whoami',f.terminal).get('role')=='executor')
   check('different_cli_not_delivered',delivery(i)['state']!='delivered',delivery(i))
  all_events=events();r['events']=[e for e in all_events if e['type'].startswith('hc_') or e['type'] in ['dispatch_queued','dispatch_unknown','shell_osc7501']]
  r['submissions']=rows();r['issues']=raised
  input_result=f.request('user_input_records',f.operator,project='demo');assert input_result['ok'],input_result
  inputs=input_result['records']
  check('system_not_user_input',not any(i['id'] in json.dumps(inputs,ensure_ascii=False) for i in raised),inputs)
  check('system_not_intervention',not any(e['type']=='human_intervention' and any(i['id'] in json.dumps(e) for i in raised) for e in all_events))
  r['status']='PASS'
 except BaseException as e:
  import traceback
  r['error']=repr(e);r['traceback']=traceback.format_exc()
  print(r['traceback'])
 finally:
  if electron:electron.stop()
  try:f.stop()
  except Exception as error:r['stop_error']=repr(error)
  finally:r['cleanup']=stop_private_core(f.dir,f.env)
  a.summary.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(status=r['status'],checks=len(r['checks']),summary=str(a.summary))))
 return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
