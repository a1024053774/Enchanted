// The actual #175 UPS/PIRQ payload and requirement are the oracle; PTY/liveness are spies.
import assert from 'node:assert/strict';
import {mkdirSync,mkdtempSync,readFileSync,writeFileSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {Panes} from '../src/panes.ts';import {OrchestrationStore} from '../src/store.ts';
const out=resolve(process.argv[2]);mkdirSync(out);
const archive=resolve('evidence/2026-10-11-batch13/T-078/slice1-readback/hooks');
const ups=JSON.parse(readFileSync(join(archive,'52e016dd-b884-48e6-893d-136c28623ffd/stdin.bin'),'utf8'));
const permission=JSON.parse(readFileSync(join(archive,'90f6c4ee-4eb9-4a40-86fa-91de975fd056/stdin.bin'),'utf8'));
const checks=[];
async function test(name,run){const root=mkdtempSync('/tmp/t78-perm-'),store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
 const record:any={id:'permission-launch',task:'permission-task',project:'p',thread:'permission-thread',role:'controller',preset:'ideation',session:ups.session_id,attempt:null,cli:'Claude Code',turn_limit:2};store.launch(record);
 const dispatch=store.register(record.id,ups.prompt.slice('⟦主控 #1⟧\n'.length));assert.equal(dispatch.text,ups.prompt);
 const active={id:'registered-submission',dispatch:dispatch.id,at:'2026-10-14T22:00:00Z',nativeTurn:null};store.event('turn_submit_intent',active,record);
 const writes=[],actions=[];const pane:any={record,task:{},attempt:null,token:'private-fixture',state:'busy',native:ups.session_id,active,claudePromptId:null,claudePromptIds:new Set(),
  failed:null,stopped:false,archived:false,stopInProgress:false,interrupted:false,writes:Promise.resolve(),pendingInputs:0,inputGeneration:0,userDraft:false,draft:{chars:[],cursor:0,keys:[],uncertain:false},offsets:new Map(),pty:{pid:1,write:v=>writes.push(v)}};
 panes.panes.set(record.thread,pane);panes.processInfo=async()=>({leader:2,failed:null});
 try{await panes.signal(record.id,JSON.stringify(ups),new Date().toISOString());await run({pane,panes,store,active,writes,actions,record});checks.push({name,status:'PASS'});}
 catch(e){checks.push({name,status:'INCOMPLETE',error:String(e)});}finally{store.close();}}
await test('permission-Enter-preserves-registered-active-and-root-count',async f=>{
 await f.panes.signal(f.record.id,JSON.stringify(permission),new Date().toISOString());
 await f.panes.userInput(f.record.id,'\r',{request_id:'permission-enter'},async(text,control)=>f.actions.push({text,control}),async()=>{});
 assert.equal(f.pane.active,f.active);assert.equal(f.pane.claudePromptId,ups.prompt_id);
 assert.equal(f.store.read().filter(e=>e.type==='turn_submit_intent').length,1);assert.deepEqual(f.writes,['\r']);assert.deepEqual(f.actions,[]);  // T-206: a bare Enter is an operation, not a message
});
await test('ordinary-Enter-remains-a-user-submit',async f=>{
 await f.panes.userInput(f.record.id,'\r',{request_id:'normal-enter'},async()=>{},async()=>{});
 assert.notEqual(f.pane.active,f.active);assert.equal(f.store.read().filter(e=>e.type==='turn_submit_intent').length,2);
});
await test('foreign-permission-prompt-does-not-authorize-control-context',async f=>{
 await assert.rejects(f.panes.signal(f.record.id,JSON.stringify({...permission,prompt_id:'foreign'}),new Date().toISOString()));
 await f.panes.userInput(f.record.id,'\r',{request_id:'normal-after-foreign'},async()=>{},async()=>{});assert.notEqual(f.pane.active,f.active);
});
const result={status:checks.every(c=>c.status==='PASS')?'PASS':'INCOMPLETE',checks,scope:'Actual recorded native payloads and production state path; simulated PTY only',real_model_turns:0};
writeFileSync(join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));process.exitCode=result.status==='PASS'?0:1;
