// Actual drain scheduling. A Stop response/paste is not the feedback submit receipt.
import assert from 'node:assert/strict';
import {mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';import {join,resolve} from 'node:path';
import {Panes} from '../src/panes.ts';import {OrchestrationStore} from '../src/store.ts';
const out=resolve(process.argv[2]);mkdirSync(out);const waitSubmitted=process.argv[3]==='--wait-submitted';
const store=new OrchestrationStore(mkdtempSync('/tmp/t78-feedback-wait-')),panes=new Panes(store.root,store,{},()=>{});
const record:any={id:'feedback-launch',task:'feedback-task',attempt:null,role:'controller',cli:'Claude Code',turn_limit:2};store.launch(record);
store.event('turn_submit_intent',{id:'first-root'},record);
const feedback=store.register(record.id,'INDEPENDENT_FEEDBACK_SENTINEL','gate');
const writes=[],pane:any={record,state:'idle',writing:false,pendingInputs:0,userDraft:false,interrupted:false,failed:null,
 queue:[feedback],sending:null,active:null,writes:Promise.resolve(),pty:{write:data=>writes.push(data)}};
const drain=panes.drain(pane);
async function until(predicate){const end=Date.now()+3000;while(!predicate()){assert.ok(Date.now()<end,'Receipt deadline exceeded');await new Promise(r=>setTimeout(r,5));}}
const snapshot=()=>({writes:[...writes],state:pane.state,writing:pane.writing,active:pane.active,events:store.read()});
await until(()=>store.read().some(e=>e.type==='paste_written'));const atPaste=snapshot();
let error,atAssertion;
try{
 if(waitSubmitted)await until(()=>store.read().some(e=>e.type==='turn_submitted' && e.data.dispatch===feedback.id));
 atAssertion=snapshot();assert.equal(writes[1],'\r');assert.equal(pane.state,'busy');assert.equal(pane.active.dispatch,feedback.id);
 assert.equal(store.read().filter(e=>e.type==='turn_submit_intent').length,2);
}catch(e){error=String(e);}finally{await drain;}
const result={status:error?'INCOMPLETE':'PASS',error,wait_submitted:waitSubmitted,argv:process.argv,at_paste:atPaste,
 at_assertion:atAssertion,settled:snapshot(),scope:'Production drain and journal; simulated PTY; no daemon/socket/vendor CLI',real_model_turns:0};
writeFileSync(join(out,'results.json'),JSON.stringify(result,null,2));store.close();console.log(JSON.stringify({status:result.status,error}));process.exitCode=error?1:0;
