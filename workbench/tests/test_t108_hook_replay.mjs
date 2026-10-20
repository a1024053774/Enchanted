// Replay actual installed-Codex hook stdin through signal/SQLite/answer projection.
// Runtime identity and PTY are supplied boundaries; no live CLI or model is started.
import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, writeFileSync } from 'node:fs';
import { parseArgs } from 'node:util';
import { OrchestrationStore } from '../src/store.ts';
import { Panes } from '../src/panes.ts';
import { agentState } from '../src/sidebar.ts';
const {values}=parseArgs({options:{samples:{type:'string'},summary:{type:'string'},'ignore-question':{type:'boolean',default:false}}});
assert(values.samples&&values.summary);
const samples=JSON.parse(readFileSync(values.samples,'utf8'));
const pre=samples.codex.find(h=>h.hook_event_name==='PreToolUse');
const post=samples.codex.find(h=>h.hook_event_name==='PostToolUse');
const root=mkdtempSync('/private/tmp/t108-hook-replay-');
const store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
const record={id:'recorded-codex',thread:'recorded-thread',task:'replay',project:'replay',attempt:'replay-attempt',role:'worker',
  session:pre.session_id,cli:'Codex',worktree:pre.cwd};store.launch(record);
const writes=[],inputs=[];
const pane={record,native:pre.session_id,nativeFile:pre.transcript_path,turn:pre.turn_id,state:'busy',
  active:{id:'recorded-submission',dispatch:'recorded-dispatch',at:'2026-10-20T00:00:00Z',nativeTurn:pre.turn_id},
  failed:null,stopped:false,archived:false,interrupted:false,inputGeneration:0,userDraft:false,writes:Promise.resolve(),
  queue:[],writing:false,pendingInputs:0,
  pty:{write:data=>writes.push(data)}};
panes.panes.set(record.thread,pane);
// Offline replay must never query the old process tree or append/read its log.
panes.scan=()=>{};
const signal=h=>panes.signal(record.id,JSON.stringify(h),new Date().toISOString());
const state=()=>agentState(panes.status(record.thread),store.read(),record.worktree);
const report={status:'INCOMPLETE',model_calls:0,vendor_calls:0,samples:values.samples,
  scope:'recorded CLI hooks from loopback fake API; supplied runtime identity and PTY',fixture:root};
try {
  store.event('turn_submitted',{id:pane.active.id},record);
  await signal(samples.codex.find(h=>h.hook_event_name==='UserPromptSubmit'));
  if(!values['ignore-question'])await signal(pre);
  assert.equal(state(),'waiting_controller_answer');
  const q=panes.questions(record.id)[0];
  assert.equal(q.questions[0].question,'选择部署区域？');
  assert.deepEqual(q.questions[0].options.map(o=>o.label),['东区','西区']);
  await panes.answerQuestion(record.id,q.id,['西区'],async(text,id)=>inputs.push({text,id}),async()=>{});
  assert.deepEqual(writes,['\x1b[B','\r']);
  assert.equal(inputs.length,1);assert.equal(inputs[0].id,q.id);
  await signal(post);
  assert.equal(panes.questions(record.id)[0].status,'answered');assert.equal(state(),'running');
  await assert.rejects(panes.answerQuestion(record.id,q.id,['西区'],async()=>{},async()=>{}));
  report.status='PASS';report.checks=['recorded_question_and_options','waiting_controller_answer','answer_keys_and_link','recorded_native_confirmation','duplicate_refused'];
} catch(error){report.error=String(error);}
finally {store.close();writeFileSync(values.summary,JSON.stringify(report,null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify(report));process.exitCode=report.status==='PASS'?0:1;
