// Real daemon/window socket and hook CLI. Only vendor liveness and PTY are spies.
// Oracles: answer 20261014T120839Z and FAILURE-MODES-09A3, fixed independent bytes.
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, writeFileSync, existsSync, realpathSync, readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import { join, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';
import { spawn } from 'node:child_process';
import { serve } from '../src/daemon.ts';
import { A2AGates } from '../src/gates/core.ts';
import { createOperatorCredential, readOperatorCredential } from '../src/credentials.ts';
import { request } from '../src/transport.ts';

const output=resolve(process.argv[2]); mkdirSync(output);
const fixtureRoot=realpathSync(mkdtempSync('/tmp/t078-2-declaration-'));
const root=join(fixtureRoot,'state');mkdirSync(root);mkdirSync(join(fixtureRoot,'hooks'));mkdirSync(join(fixtureRoot,'requests'));
process.env.A2A_OPERATOR_CREDENTIAL=join(root,'operator.json');createOperatorCredential(root);
const operator=readOperatorCredential(root)!;
let panes:any,gates:any;
await serve(root,{},(r,p)=>{panes=p;gates=new A2AGates(r,p);return gates;});
panes.processInfo=async()=>({leader:2,failed:null});panes.shutdown=async()=>{};
const checks:any[]=[];
let dispatchCounter=0;
let barrier: {entered:()=>void; wait:Promise<void>} | undefined;
const callOriginal=gates.call.bind(gates);
gates.call=async (...args:any[])=>{if(barrier && args[0].command==='status'){const b=barrier;barrier=undefined;b.entered();await b.wait;}return callOriginal(...args);};
function fixture(){
  const id=randomUUID(),record:any={id,thread:randomUUID(),task:randomUUID(),project:'fixture',attempt:null,
    role:'controller',preset:'ideation',session:randomUUID(),spec_rev:1,cli:'Claude Code',turn_limit:2,worktree:root};
  const task={task_id:record.task,project_id:'fixture',repo:root,spec_rev:1,current_attempt:null};
  panes.store.db.prepare('INSERT INTO tasks(id,data) VALUES (?,?)').run(record.task,JSON.stringify(task));
  panes.store.launch(record);
  const writes:any[]=[];
  const pane:any={record,task,attempt:null,token:randomUUID(),pty:{pid:1,write:(v:any)=>writes.push(Buffer.isBuffer(v)?{base64:v.toString('base64')}:v)},
    state:'busy',native:record.session,failed:null,stopped:false,archived:false,active:null,queue:[],writing:false,stopInProgress:false,
    writes:Promise.resolve(),pendingInputs:0,userDraft:false,interrupted:false,sending:null,offsets:new Map(),terminalBuffer:'',claudePromptId:null,claudePromptIds:new Set(),
    inputGeneration:0,interruption:null};
  const first=panes.store.register(id,'FIRST_FIXED_NONCE');pane.active={id:randomUUID(),dispatch:first.id,at:new Date().toISOString(),nativeTurn:null};
  panes.store.event('turn_submit_intent',pane.active,record);panes.panes.set(record.thread,pane);
  const expectedFirst=`⟦主控 #${++dispatchCounter}⟧\nFIRST_FIXED_NONCE`;
  assert.equal(first.text,expectedFirst);
  return {pane,record,writes,first,expectedFirst,expectedSecond:''};
}
async function windowFor(f:any){
  const opened=await request(root,{command:'window_open',task:f.record.task,launch:f.record.id},operator);assert.equal(opened.ok,true);
  let sequence=0;return {identity:opened.identity,send:(command:string,rest:any={})=>request(root,{command,sequence:++sequence,request_id:randomUUID(),...rest},opened.identity)};
}
function declaration(f:any){return {statement:'用户声明输入框已空',launch:f.record.id,window_id:f.statementWindow,interruption:f.pane.interruption,input_generation:f.pane.inputGeneration};}
async function interrupt(f:any,w:any){assert.equal((await w.send('window_input',{data:'\x1b'})).ok,true);f.expectedSecond=`⟦主控 #${++dispatchCounter}⟧\nSECOND_FIXED_NONCE`;await panes.dispatch(f.pane,'SECOND_FIXED_NONCE');}
async function hook(f:any,value:any){
  const cli=resolve('workbench/src/gates/cli.ts');const env:any={PATH:process.env.PATH,A2A_LAUNCH:f.record.id,A2A_CAPABILITY:f.pane.token,
    A2A_NATIVE_SESSION:f.record.session,A2A_HOOK_TRACE_DIR:join(fixtureRoot,'hooks'),A2A_REQUEST_DIR:join(fixtureRoot,'requests')};
  const args=[cli,'--state',root,'signal','--launch',f.record.id];
  return await new Promise<any>((done,fail)=>{
    const child=spawn(process.execPath,args,{env,stdio:['pipe','pipe','pipe']});let stdout='',stderr='';
    child.stdout.on('data',v=>stdout+=v);child.stderr.on('data',v=>stderr+=v);child.on('error',fail);
    child.on('close',exit_code=>done({exit_code,stdout,stderr,input:value}));child.stdin.end(JSON.stringify(value));
  });
}
async function test(name:string,body:(f:any,w:any)=>Promise<void>){
  const f=fixture(),w=await windowFor(f);f.statementWindow=w.identity.window;
  try{await body(f,w);checks.push({name,status:'PASS'});}catch(e){checks.push({name,status:'INCOMPLETE',error:String(e)});}
  finally{writeFileSync(join(output,name+'.json'),JSON.stringify({writes:f.writes,events:panes.store.read(f.record.task),inputs:gates.db.prepare('SELECT data FROM user_inputs WHERE json_extract(data,\'$.target.task\')=?').all(f.record.task)},null,2));}
}
await test('missing_declaration_rejected',async(f,w)=>{await interrupt(f,w);const n=f.writes.length;const r=await w.send('window_release');assert.equal(r.ok,false);assert.equal(f.writes.length,n);assert.equal(f.pane.queue.length,1);});
await test('wrong_interruption_rejected',async(f,w)=>{await interrupt(f,w);const d=declaration(f);d.interruption={request_id:'other'};const r=await w.send('window_release',{declaration:d});assert.equal(r.ok,false);assert.deepEqual(f.writes,['\x1b']);});
await test('new_input_invalidates_declaration',async(f,w)=>{await interrupt(f,w);const d=declaration(f);await w.send('window_input',{data:'用户新草稿'});assert.equal((await w.send('window_release',{declaration:d})).ok,false);assert.deepEqual(f.writes,['\x1b','用户新草稿']);});
await test('composition_without_text_invalidates_declaration',async(f,w)=>{await interrupt(f,w);const d=declaration(f);await w.send('window_composition');assert.equal((await w.send('window_release',{declaration:d})).ok,false);assert.deepEqual(f.writes,['\x1b']);});
await test('second_window_invalidates_declaration',async(f,w)=>{await interrupt(f,w);const d=declaration(f),w2=await windowFor(f);await w2.send('window_input',{data:'第二窗口'});assert.equal((await w.send('window_release',{declaration:d})).ok,false);assert.deepEqual(f.writes,['\x1b','第二窗口']);});
await test('binary_input_invalidates_declaration',async(f,w)=>{await interrupt(f,w);const d=declaration(f);await w.send('window_input',{data:'\xff',encoding:'binary'});assert.equal((await w.send('window_release',{declaration:d})).ok,false);assert.deepEqual(f.writes,['\x1b',{base64:'/w=='}]);});
await test('old_launch_or_window_declaration_rejected',async(f,w)=>{
  await interrupt(f,w);const d=declaration(f);assert.equal((await w.send('window_release',{declaration:{...d,launch:'old'}})).ok,false);
  assert.equal((await w.send('window_release',{declaration:{...d,window_id:'old'}})).ok,false);assert.deepEqual(f.writes,['\x1b']);
});
await test('input_during_identity_await_rejects_release',async(f,w)=>{
  await interrupt(f,w);const d=declaration(f),w2=await windowFor(f);let entered!:()=>void,finish!:()=>void;
  const begun=new Promise<void>(r=>entered=r),wait=new Promise<void>(r=>finish=r);barrier={entered,wait};
  const releasing=w.send('window_release',{declaration:d});await begun;const typing=w2.send('window_input',{data:'竞态草稿'});await typing;finish();
  assert.equal((await releasing).ok,false);assert.deepEqual(f.writes,['\x1b','竞态草稿']);
});
await test('input_during_second_identity_await_rejects_release',async(f,w)=>{
  await interrupt(f,w);const d=declaration(f),w2=await windowFor(f);let entered!:()=>void,finish!:()=>void;
  const begun=new Promise<void>(r=>entered=r),wait=new Promise<void>(r=>finish=r);let calls=0;
  const original=panes.processInfo;panes.processInfo=async(...args:any[])=>{if(++calls===3){entered();await wait;}return original(...args);};
  const releasing=w.send('window_release',{declaration:d});await begun;
  const typing=w2.send('window_input',{data:'写入前草稿'});await new Promise(r=>setTimeout(r,30));finish();
  assert.equal((await releasing).ok,false);await typing;panes.processInfo=original;assert.deepEqual(f.writes,['\x1b','写入前草稿']);
});
await test('same_window_main_queue_does_not_hide_new_input',async(f,w)=>{
  await interrupt(f,w);const d=declaration(f);let entered!:()=>void,finish!:()=>void;
  const begun=new Promise<void>(r=>entered=r),wait=new Promise<void>(r=>finish=r);
  const source=readFileSync(new URL('../app/main.ts',import.meta.url),'utf8');
  const start=source.indexOf('  const sendWindowCommand ='),end=source.indexOf("  ipcMain.handle('a2a:input'",start);
  assert.ok(start>0 && end>start);
  const code=stripTypeScriptTypes('function create(){let sequence=1; let inputQueue=Promise.resolve(); let pendingRelease=null;'+source.slice(start,end)+'; return sendWindowCommand;}');
  const send=new Function('request','options','identity','closing','randomUUID',code+';return create();')(request,{state:root},w.identity,false,randomUUID);
  barrier={entered,wait};
  const releasing=send({command:'window_release',declaration:d});await begun;
  const typing=send({command:'window_input',data:'声明后的窗口键入'});await new Promise(r=>setTimeout(r,30));finish();
  assert.equal((await releasing).ok,false);await typing;assert.deepEqual(f.writes,['\x1b','声明后的窗口键入']);
});
await test('valid_declaration_preserves_bytes_and_records_statement',async(f,w)=>{
  await interrupt(f,w);const d=declaration(f);const r=await w.send('window_release',{declaration:d});assert.equal(r.ok,true);
  assert.deepEqual(f.writes,['\x1b','\x1b[200~'+f.expectedSecond+'\x1b[201~','\r']);
  const rows=gates.db.prepare('SELECT data FROM user_inputs WHERE json_extract(data,\'$.target.task\')=?').all(f.record.task).map((r:any)=>JSON.parse(r.data));
  const actions=rows.filter((r:any)=>r.content?.action==='queue-release');assert.equal(actions.length,1);assert.equal(actions[0].text,'用户声明输入框已空');assert.deepEqual(actions[0].content.declaration,d);
  assert.equal((await w.send('window_release',{declaration:d})).ok,false);assert.equal(f.writes.length,3);
});
await test('controls_are_actions_not_messages',async(f,w)=>{
  for(const data of ['\x03','\x15','\x13','\x1b[A'])assert.equal((await w.send('window_input',{data})).ok,true);
  const rows=gates.db.prepare('SELECT data FROM user_inputs WHERE json_extract(data,\'$.target.task\')=?').all(f.record.task).map((r:any)=>JSON.parse(r.data));
  assert.deepEqual(rows.map((r:any)=>[r.form,r.content?.action,r.content?.data]),[['action','terminal-key','\x03'],['action','terminal-key','\x15'],['action','terminal-key','\x13'],['action','terminal-key','\x1b[A']]);
  assert.deepEqual(f.writes,['\x03','\x15','\x13','\x1b[A']);
});
await test('injected_mismatch_blocks_actual_hook_output',async(f)=>{
  const v={session_id:f.record.session,hook_event_name:'UserPromptSubmit',prompt_id:randomUUID(),prompt:'OLD_DRAFT'+f.first.text};
  const r=await hook(f,v);writeFileSync(join(output,'mismatch-hook.json'),JSON.stringify(r,null,2));
  assert.ok(r.exit_code===2 || (r.exit_code===0 && JSON.parse(r.stdout).decision==='block'),'Hook must actually block, exit 1 is nonblocking');
  assert.ok(panes.store.read(f.record.task).some((e:any)=>e.type==='injected_prompt_blocked' && e.data.prompt===v.prompt));assert.equal(f.pane.claudePromptId,null);assert.equal(f.writes.length,0);
});
await test('hand_typed_marker_is_allowed',async(f,w)=>{
  await w.send('window_input',{data:'⟦主控 #1⟧\nFIRST_FIXED_NONCE'});await w.send('window_input',{data:'\r'});
  const r=await hook(f,{session_id:f.record.session,hook_event_name:'UserPromptSubmit',prompt_id:randomUUID(),prompt:'⟦主控 #1⟧\nFIRST_FIXED_NONCE'});assert.equal(r.exit_code,0);assert.deepEqual(JSON.parse(r.stdout),{});
});
await test('exact_injection_and_stop_contract_unchanged',async(f)=>{
  const id=randomUUID(),ups=await hook(f,{session_id:f.record.session,hook_event_name:'UserPromptSubmit',prompt_id:id,prompt:f.first.text});assert.equal(ups.exit_code,0);
  assert.equal((await hook(f,{session_id:'wrong',hook_event_name:'Stop',prompt_id:id,stop_hook_active:false})).exit_code,1);
  assert.equal((await hook(f,{session_id:f.record.session,hook_event_name:'Stop',prompt_id:'old',stop_hook_active:false})).exit_code,0);assert.ok(f.pane.active);
  assert.equal((await hook(f,{session_id:f.record.session,hook_event_name:'Stop',prompt_id:id,stop_hook_active:false})).exit_code,0);assert.equal(f.pane.state,'idle');
});
await test('no_active_injection_hand_typed_is_allowed',async(f)=>{
  f.pane.active=null;const r=await hook(f,{session_id:f.record.session,hook_event_name:'UserPromptSubmit',prompt_id:randomUUID(),prompt:f.expectedFirst});assert.equal(r.exit_code,0);
  assert.ok(!panes.store.read(f.record.task).some((e:any)=>e.type==='injected_prompt_blocked'));
});
const result={status:checks.every(c=>c.status==='PASS')?'PASS':'INCOMPLETE',checks,argv:process.argv,root,
  expected_source:'20261014T120839Z-ideation-answer-001 / FAILURE-MODES-09A3',scope:'Real daemon/window transport/hook CLI; synthetic vendor liveness and PTY; no vendor CLI/API/Electron/model',real_model_turns:0};
writeFileSync(join(output,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
await request(root,{command:'daemon_stop'},operator);while(existsSync(join(root,'daemon.pid')))await new Promise(r=>setTimeout(r,20));
process.exitCode=result.status==='PASS'?0:1;
