// Domain/request boundary only. Native process and PTY observations are spies.
import assert from 'node:assert/strict';import {mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';import {join,resolve} from 'node:path';
import {Panes} from '../src/panes.ts';import {OrchestrationStore} from '../src/store.ts';import {RequestRelay} from '../src/relay.ts';import {A2AGates} from '../src/gates/core.ts';
const out=resolve(process.argv[2]);mkdirSync(out);const checks=[];
function fixture(){const root=mkdtempSync('/tmp/t78-ctl-relay-'),store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{}),gates=new A2AGates(root,panes),relay=new RequestRelay(store);
 const record:any={id:'controller-launch',thread:'controller-thread',task:'controller-task',project:'controller-project',preset:'ideation',session:'controller-session',spec_rev:1,role:'controller',cli:'Claude Code',attempt:null,turn_limit:2};
 const task={task_id:record.task,project_id:record.project,repo:root,spec_rev:1,state:'registered',current_attempt:null};store.db.prepare('INSERT INTO tasks VALUES (?,?)').run(task.task_id,JSON.stringify(task));store.launch(record);
 const active={id:'submission',dispatch:'dispatch',at:new Date().toISOString(),nativeTurn:null};
 const pane:any={record,task,attempt:null,token:'private',pty:{pid:11,write:()=>{}},state:'busy',native:record.session,claudePromptId:'prompt-1',active,stopInProgress:true,stopped:false,archived:false,failed:null,interrupted:false};
 panes.panes.set(record.thread,pane);panes.processInfo=async()=>({leader:12,shell_pid:11,native_session:record.session,failed:null});gates.registerController(record.thread);
 const binding={id:record.id,task:record.task,project:record.project,preset:'ideation' as const,session:record.session,spec_rev:1,role:'controller' as const,native_session:record.session,prompt_id:'prompt-1'};
 const request={schema:2,request_id:'unique',command:'inbox_list',launch:record.id,task:record.task,project:record.project,preset:'ideation',session:record.session,spec_rev:1,native_session:record.session,prompt_id:'prompt-1',role:'executor'};
 const identity={launch:record.id,token:'private',native_session:record.session,prompt_id:'prompt-1'};
 for(const [id,to] of [['ideation-sentinel','ideation'],['foreign-sentinel','executor']])store.db.prepare('INSERT INTO inbox_records VALUES (?,?)').run(id,JSON.stringify({id,schema:1,kind:'report',from:'executor',to,body:'independent-'+id,reply_to:null,refs:[],created_at:'2026-10-14T00:00:00Z'}));
 let effects=0;const perform=async command=>{effects++;const caller=await panes.caller(identity);await caller.assertActive();return gates.call(command,caller);};
 return {root,store,panes,gates,relay,record,pane,task,binding,request,identity,perform,get effects(){return effects;},close(){gates.close();store.close();}};}
async function test(name,run){const f=fixture();try{await run(f);checks.push({name,status:'PASS'});}catch(e){checks.push({name,status:'INCOMPLETE',error:String(e)});}finally{f.close();}}
const file=value=>({name:'request.json',raw:JSON.stringify(value)});
await test('actual-preset-scope-and-once-execution',async f=>{const a=await f.relay.receive(f.binding,file(f.request),true,f.perform);assert.equal(a.result.ok,true);assert.deepEqual(a.result.entries.map(x=>x.entry.id),['ideation-sentinel']);
 const b=await f.relay.receive(f.binding,file(f.request),true,f.perform);assert.equal(b.replayed,true);assert.equal(f.effects,1);assert.deepEqual(a.result,b.result);
 const row=f.store.db.prepare('SELECT * FROM relay_requests').get();assert.equal(row.attempt,null);const parsed=JSON.parse(row.input);assert.equal('attempt' in parsed,false);assert.equal('fence' in parsed,false);
});
for(const key of ['launch','preset','project','task','session','native_session','spec_rev','prompt_id'])await test('reject-'+key,async f=>{
 const wrong={...f.request,[key]:key==='spec_rev'?2:'foreign'};const result=await f.relay.receive(f.binding,file(wrong),true,f.perform);assert.equal(result.result.ok,false);assert.equal(result.result.error,'relay_identity_mismatch');assert.equal(f.effects,0);
});
await test('old-Stop-does-not-admit',async f=>{const r=await f.relay.receive(f.binding,file(f.request),false,f.perform);assert.equal(r.result.error,'relay_requires_current_stop');assert.equal(f.effects,0);});
await test('missing-context-and-fake-attempt-are-rejected',async f=>{const a={...f.request};delete a.prompt_id;assert.equal((await f.relay.receive(f.binding,file(a),true,f.perform)).result.error,'invalid_relay_request');
 assert.equal((await f.relay.receive(f.binding,file({...f.request,request_id:'fake-attempt',attempt:null,fence:0}),true,f.perform)).result.error,'invalid_relay_request');assert.equal(f.effects,0);
});
for(const kind of ['revoked','native-session','preset','task-spec','task-project','prompt','replacement-active','leader-change'])await test('caller-denies-'+kind,async f=>{
 const caller=await f.panes.caller(f.identity);
 if(kind==='revoked')f.pane.stopped=true;if(kind==='native-session')f.pane.native='foreign';if(kind==='preset')f.record.preset='executor';
 if(kind==='prompt')f.pane.claudePromptId='foreign';if(kind==='replacement-active')f.pane.active={...f.pane.active,id:'replacement'};
 if(kind==='leader-change')f.panes.processInfo=async()=>({leader:99,shell_pid:11,native_session:f.record.session,failed:null});
 if(kind.startsWith('task-')){const changed={...f.task,...(kind==='task-spec'?{spec_rev:2}:{project_id:'foreign'})};f.store.db.prepare('UPDATE tasks SET data=?').run(JSON.stringify(changed));await assert.rejects(caller.assertActive());const r=await f.gates.call({command:'inbox_list'},caller);assert.equal(r.ok,false);return;}
 await assert.rejects(caller.assertActive());
});
await test('caller-rechecks-after-native-await',async f=>{const caller=await f.panes.caller(f.identity);f.panes.processInfo=async()=>{f.pane.archived=true;return{leader:12,shell_pid:11,native_session:f.record.session,failed:null};};await assert.rejects(caller.assertActive());});
await test('controller-cannot-request-worker-submit',async f=>{const r=await f.relay.receive(f.binding,file({...f.request,command:'submit',commit:'a'.repeat(40)}),true,f.perform);assert.equal(r.result.error,'invalid_relay_request');assert.equal(f.effects,0);});
await test('history-nullable-migration-keeps-data-and-triggers',async f=>{const root=mkdtempSync('/tmp/t78-relay-migration-'),store=new OrchestrationStore(root);
 store.db.exec('CREATE TABLE relay_requests(key TEXT PRIMARY KEY,launch TEXT NOT NULL,task TEXT NOT NULL,attempt TEXT NOT NULL,request_id TEXT,input TEXT NOT NULL,created_at TEXT NOT NULL)');
 store.db.prepare('INSERT INTO relay_requests VALUES (?,?,?,?,?,?,?)').run('old','old-launch','old-task','old-attempt','old-request','{"historical":true}','2026-10-14T00:00:00Z');
 const before=store.db.prepare('SELECT * FROM relay_requests').get();new RequestRelay(store);assert.deepEqual(store.db.prepare('SELECT * FROM relay_requests').get(),before);
 assert.throws(()=>store.db.exec("UPDATE relay_requests SET input='{}'"),/append only/);assert.throws(()=>store.db.exec('DELETE FROM relay_requests'),/append only/);store.close();
});
const result={status:checks.every(c=>c.status==='PASS')?'PASS':'INCOMPLETE',checks,scope:'SQLite/domain/relay and exact caller; native liveness is a spy, no transport/CLI/model',real_model_turns:0};writeFileSync(join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));process.exitCode=result.status==='PASS'?0:1;
