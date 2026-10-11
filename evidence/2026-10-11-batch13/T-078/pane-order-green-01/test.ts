// No CLI, real PTY, socket, ps, signal, or Claude fixture runs in this test.
// The PTY/process boundary is a spy. This proves state/write ordering only.
// Failures: duplicate wake writes twice; queue admission is called delivery;
// Esc/late Stop releases a queue; release omits a user action; interruption
// kills/archives a pane; recorder failure writes bytes; controller needs a fake
// attempt; old launch rows or append-only constraints are lost in migration.
// Additional failures: awaiting the input recorder admits an injection or
// reorders later keys; a second pane consumes this pane's budget; a repeated
// Stop unlocks another turn; recovery silently replays a pending wake.
import assert from "node:assert/strict";
import { appendFileSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { Panes } from "../src/panes.ts";
import { OrchestrationStore } from "../src/store.ts";
import { A2AGates } from "../src/gates/core.ts";

const output=resolve(process.argv[2]!);mkdirSync(output);
const checks:any[]=[];
const actor={address:"executor",assertActive:async()=>{}};
function fixture() {
  const root=mkdtempSync('/tmp/t78-pane-');
  const home=join(root,'home');mkdirSync(join(home,'sessions'),{recursive:true});
  const store=new OrchestrationStore(root);
  const panes=new Panes(root,store,{codex_home:home,turn_limit:5},()=>{});
  const gates=new A2AGates(root,panes);
  const attempt={task_id:'unit-task',attempt_id:'unit-attempt',session_id:'unit-session',fence:1,spec_rev:1,
    thread_id:'unit-thread',workspace:root,turn_id:'turn-0',reclaimed:false};
  const task={task_id:'unit-task',project_id:'unit-project',repo:root,state:'claimed',spec_rev:1,current_attempt:attempt};
  store.db.prepare('INSERT INTO tasks(id,data) VALUES (?,?)').run(task.task_id,JSON.stringify(task));
  store.db.prepare('INSERT INTO attempts(id,data) VALUES (?,?)').run(attempt.attempt_id,JSON.stringify(attempt));
  const record={id:'unit-launch',thread:'unit-thread',task:'unit-task',attempt:'unit-attempt',role:'worker',
    project:'unit-project',session:'unit-session',fence:1,spec_rev:1,turn_limit:5,worktree:root};
  store.launch(record);mkdirSync(join(root,'traces',record.id),{recursive:true});
  const writes:any[]=[],kills:any[]=[];
  const pane:any={record,task,attempt,token:'unit-only',pty:{pid:321,write:(data:string|Buffer)=>writes.push({
    data:Buffer.isBuffer(data)?data.toString('hex'):data,
    registrations:store.db.prepare('SELECT count(*) AS n FROM dispatch_records').get()!.n,
  }),kill:(signal:string)=>kills.push(signal)},
    state:'busy',stopped:false,archived:false,failed:null,leader:321,native:'unit-native',turn:'turn-0',
    active:{id:'first-submission',dispatch:'seed',at:'2026-10-11T00:00:00Z',nativeTurn:'turn-0'},
    queue:[],writing:false,stopInProgress:false,writes:Promise.resolve(),pendingInputs:0,userDraft:false,interrupted:false,
    offsets:new Map(),model:'unknown',effort:'unknown',terminalBuffer:''};
  panes.panes.set(record.thread,pane);
  panes.processInfo=async()=>({leader:321,failed:null,shell_pid:321,native_session:'unit-native',processes:[]});
  const native=join(home,'sessions','rollout-unit-native.jsonl');
  writeFileSync(native,JSON.stringify({type:'session_meta',payload:{id:'unit-native',source:'cli'}})+'\n'+
    JSON.stringify({type:'event_msg',payload:{type:'task_started',turn_id:'turn-0'}})+'\n');
  const signal=(turn:string)=>panes.signal(record.id,JSON.stringify({session_id:'unit-native',hook_event_name:'Stop',turn_id:turn}),new Date().toISOString());
  let inputCount=0;
  const action=async(actionName:string)=>{
    const id='user-action-'+(++inputCount);
    gates.appendUserInput({id,schema:1,form:'action',text:actionName,
      target:{project:'unit-project',task:'unit-task',attempt:'unit-attempt',thread:'unit-thread',turn:null,message:null},
      channel:'terminal-window',reply_to:null,source_ref:{command_id:id},certainty:'observed',created_at:new Date().toISOString()},id);
  };
  const issue=(id:string)=>{
    const entry={id,schema:1,kind:'issue',from:'worker:unit-thread',to:'executor',reply_to:null,refs:[],
      created_at:new Date().toISOString(),body:'固定问题',title:'固定问题',blocking:false};
    store.db.prepare('INSERT INTO inbox_records(id,data) VALUES (?,?)').run(id,JSON.stringify(entry));
  };
  return {root,store,panes,gates,pane,record,task,writes,kills,native,signal,action,issue,
    close(name:string){
      writeFileSync(join(output,name+'.json'),JSON.stringify({root,writes,kills,events:store.read(),
        inputs:store.db.prepare('SELECT data FROM user_inputs').all()},null,2)+'\n');gates.close();store.close();
    }};
}
async function test(name:string,run:(f:ReturnType<typeof fixture>)=>Promise<void>) {
  const f=fixture();
  try {await run(f);checks.push({name,status:'PASS'});}
  catch(error){checks.push({name,status:'INCOMPLETE',kind:'contract',error:String(error)});}
  finally{f.close(name);}
}
await test('wake_queue_delivery_and_duplicate',async f=>{
  f.issue('issue-1');
  const ack:any=await f.gates.call({command:'inbox_ack',id:'issue-1',body:'ACK_ONE'},undefined,actor);
  assert.equal(ack.ok,true);assert.equal(ack.delivery.state,'queued');assert.equal(f.writes.length,0);
  const duplicate:any=await f.gates.call({command:'inbox_ack',id:'issue-1'},undefined,actor);
  assert.equal(duplicate.entry.id,ack.entry.id);assert.equal(duplicate.delivery.message,ack.delivery.message);
  await f.signal('turn-0');await f.panes.drain(f.pane);
  assert.equal(f.writes.length,2);assert.equal(f.writes[0].registrations,1);
  assert.ok(f.writes[0].data.startsWith('\x1b[200~⟦主控 #1⟧'));
  assert.ok(f.writes[0].data.includes('ACK_ONE'));assert.equal(f.writes[1].data,'\r');
  const delivered:any=await f.gates.call({command:'inbox_ack',id:'issue-1'},undefined,actor);
  assert.equal(delivered.delivery.state,'delivered');assert.equal(f.writes.length,2);
  assert.equal(f.store.db.prepare('SELECT count(*) AS n FROM user_inputs').get()!.n,0);
});
await test('escape_late_stop_and_user_release',async f=>{
  await f.panes.dispatch(f.pane,'AFTER_ESCAPE');
  await f.panes.userInput(f.record.id,'\x1b',{request_id:'escape'},async()=>f.action('escape'),async()=>{});
  const before=f.store.read().at(-1)!.seq;
  await f.signal('turn-0');await f.panes.drain(f.pane);
  assert.deepEqual(f.writes.map(x=>x.data),['\x1b']);assert.equal(f.pane.state,'busy');
  assert.equal(f.store.read().filter(x=>x.seq>before&&x.type==='pane_idle').length,0,'Held completion cannot claim idle');
  assert.equal(typeof (f.panes as any).releaseByUser,'function','User release must be implemented');
  await (f.panes as any).releaseByUser(f.record.thread,'用户放行',()=>f.action('queue_release'),async()=>{});
  assert.equal(f.writes.length,3);assert.equal(f.writes[2].data,'\r');assert.equal(f.pane.state,'busy');
  const inputs=f.store.db.prepare('SELECT data FROM user_inputs').all().map(row=>JSON.parse(String(row.data)));
  assert.deepEqual(inputs.map(x=>x.text),['escape','queue_release']);
});
await test('interrupt_only_esc_not_reclaim',async f=>{
  const stop={id:'stop-1',schema:1,kind:'stop',from:'ideation',to:'executor',reply_to:null,
    refs:['thread:unit-thread','input:requested-stop'],body:'URGENT 停止 unit-thread',created_at:new Date().toISOString()};
  f.store.db.prepare('INSERT INTO inbox_records(id,data) VALUES (?,?)').run(stop.id,JSON.stringify(stop));
  const result=await f.gates.call({command:'stop',thread:'unit-thread',stop_id:'stop-1',actor:'user'},undefined,actor);
  assert.equal(result.ok,true);assert.deepEqual(f.writes.map(x=>x.data),['\x1b']);assert.deepEqual(f.kills,[]);
  assert.equal(f.pane.stopped,false);assert.equal(f.pane.archived,false);assert.equal(f.pane.state,'busy');
  assert.equal(JSON.parse(String(f.store.db.prepare('SELECT data FROM tasks').get()!.data)).state,'claimed');
  const event=f.store.db.prepare("SELECT details FROM events WHERE type='emergency_interrupt_requested'").get()!;
  assert.equal(JSON.parse(String(event.details)).actor,'executor');
});
await test('recorder_failure_has_no_pty_write',async f=>{
  await assert.rejects(f.panes.userInput(f.record.id,'禁止写出',{request_id:'failed-record'},async()=>{throw new Error('fixture recorder failure');},async()=>{}));
  assert.equal(f.writes.length,0);
});
function barrier() {
  let release!:()=>void;
  const promise=new Promise<void>(resolve=>{release=resolve;});
  return {promise,release};
}
await test('input_admission_holds_injection',async f=>{
  f.pane.state='idle';f.pane.active=null;
  const entered=barrier(),held=barrier();
  const input=f.panes.userInput(f.record.id,'人工草稿',{request_id:'first'},async()=>{
    entered.release();await held.promise;
  },async()=>{});
  await entered.promise;
  const injected=f.panes.dispatch(f.pane,'不得混入草稿');
  const before=f.writes.slice();
  held.release();await Promise.all([input,injected]);
  assert.deepEqual(before,[],'A pending user record must reserve the pane');
  assert.deepEqual(f.writes.map(x=>x.data),['人工草稿']);assert.equal(f.pane.queue.length,1);
});
await test('input_recording_cannot_reorder_keys',async f=>{
  const entered=barrier(),held=barrier();
  const first=f.panes.userInput(f.record.id,'字',{request_id:'first'},async()=>{
    entered.release();await held.promise;
  },async()=>{});
  await entered.promise;
  const later=f.panes.userInput(f.record.id,'\r',{request_id:'second'},async()=>{},async()=>{});
  // Finish one event-loop turn while the first record is held. No clock race.
  await new Promise<void>(resolve=>setImmediate(resolve));
  const before=f.writes.slice();held.release();await Promise.all([first,later]);
  assert.deepEqual(before,[],'A later Enter cannot overtake an earlier key');
  assert.deepEqual(f.writes.map(x=>x.data),['字','\r']);
});
await test('escape_during_paste_suppresses_submit',async f=>{
  f.pane.state='idle';f.pane.active=null;
  const pasted=barrier();const write=f.pane.pty.write;
  f.pane.pty.write=(data:string)=>{write(data);if(data.startsWith('\x1b[200~'))pasted.release();};
  const injection=f.panes.dispatch(f.pane,'尚未提交的注入');await pasted.promise;
  await f.panes.userInput(f.record.id,'\x1b',{request_id:'cancel-paste'},async()=>{},async()=>{});
  await injection;
  assert.equal(f.writes.length,2);assert.equal(f.writes[1].data,'\x1b');
  assert.equal(f.store.read().some(x=>x.type==='turn_submitted'),false);
  assert.equal(f.pane.state,'busy');assert.equal(f.pane.interrupted,true);
});
await test('turn_budget_is_bound_to_launch',async f=>{
  f.pane.state='idle';f.pane.active=null;
  for(let n=0;n<5;n++)f.store.event('turn_submit_intent',{id:'other-'+n},{id:'other-launch',task:'other-task',attempt:'other-attempt'});
  await f.panes.dispatch(f.pane,'本窗格仍有额度');
  assert.equal(f.writes.length,2);assert.equal(f.writes[1].data,'\r');
});
await test('duplicate_stop_does_not_release_next_submission',async f=>{
  await f.panes.dispatch(f.pane,'下一回合');await f.signal('turn-0');await f.panes.drain(f.pane);
  const next=f.pane.active.id;
  await f.signal('turn-0');assert.equal(f.pane.state,'busy');assert.equal(f.pane.active.id,next);
  assert.equal(f.writes.length,2);
});
await test('recovery_retains_unknown_without_replay',async f=>{
  const item=await f.panes.dispatch(f.pane,'重启前排队','inbox',{id:'restart-wake',sender:'executor'});
  f.panes.panes.clear();f.panes.recover('next-daemon');
  assert.equal(f.panes.status(f.record.thread).state,'unknown');
  assert.equal((await f.panes.readWakeDelivery(f.record.thread,item.id)).state,'unknown');
  assert.deepEqual(f.writes,[]);
});
// Storage-only controller record. This is not a controller/Claude execution.
const migrationRoot=mkdtempSync('/tmp/t78-launch-schema-');
const old=new DatabaseSync(join(migrationRoot,'state.sqlite3'));
old.exec('CREATE TABLE launch_records(id TEXT PRIMARY KEY,task TEXT NOT NULL,attempt TEXT NOT NULL,data TEXT NOT NULL)');
const prior=JSON.stringify({id:'worker-old',task:'task',attempt:'attempt',role:'worker'});
old.prepare('INSERT INTO launch_records VALUES (?,?,?,?)').run('worker-old','task','attempt',prior);old.close();
const migrated=new OrchestrationStore(migrationRoot);
try {
  migrated.launch({id:'controller',task:'task',attempt:null,role:'ideation'});
  assert.equal(migrated.db.prepare("SELECT data FROM launch_records WHERE id='worker-old'").get()!.data,prior);
  assert.equal(migrated.launchRecord('controller')!.attempt,null);
  for(const statement of ['UPDATE launch_records SET data=\'changed\'','DELETE FROM launch_records']) assert.throws(()=>migrated.db.exec(statement),/append only/);
  checks.push({name:'nullable_controller_attempt_preserves_history',status:'PASS'});
} catch(error){checks.push({name:'nullable_controller_attempt_preserves_history',status:'INCOMPLETE',kind:'contract',error:String(error)});}
finally{migrated.close();}
for(const name of ['panes.ts','store.ts'])writeFileSync(join(output,name),readFileSync(new URL('../src/'+name,import.meta.url)));
writeFileSync(join(output,'test.ts'),readFileSync(new URL(import.meta.url)));
const result={status:checks.every(x=>x.status==='PASS')?'PASS':'INCOMPLETE',scope:'isolated state and storage; no real process identity verification',
  real_model_turns:0,claude_fixture:false,argv:process.argv,checks,migrationRoot};
writeFileSync(join(output,'results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
process.exitCode=result.status==='PASS'?0:1;
