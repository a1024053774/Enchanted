// Contract from T-108 and installed CLI hook samples. Real signal entry, SQLite,
// PTY write boundary; supplied process identity is not a live CLI proof.
// Failures: missing/stale/auxiliary fields, duplicate answer, changed input,
// failed recorder/write, early state release, root completion swallowed.
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { OrchestrationStore } from '../src/store.ts';
import { Panes } from '../src/panes.ts';
import { agentState } from '../src/sidebar.ts';
import { answerLifecycleContracts } from './t108_answer_lifecycle_contracts.mjs';
import { hookFailureContracts } from './t108_hook_failure_contracts.mjs';

const output=process.argv[2];
const root=mkdtempSync('/private/tmp/t108-question-contract-');
const store=new OrchestrationStore(root), panes=new Panes(root,store,{},()=>{});
const record={id:'launch',thread:'thread',task:'task',project:'project',attempt:null,role:'controller',preset:'ideation',
  session:'native',cli:'Claude Code',turn_limit:1,worktree:root};
store.launch(record);
const dispatch=store.register(record.id,'Ask region.');
const writes=[],inputs=[];
const pane={record,native:'native',state:'busy',failed:null,stopped:false,archived:false,interrupted:false,
  stopInProgress:false,active:{id:'submission',dispatch:dispatch.id,at:'2026-10-20T00:00:00Z',nativeTurn:null},
  claudePromptId:null,claudePromptIds:new Set(),queue:[],writing:false,writes:Promise.resolve(),pendingInputs:0,
  userDraft:false,inputGeneration:0,pty:{write:data=>writes.push(data)}};
panes.panes.set('thread',pane);
const questions=[{question:'选择发布区域？',header:'区域',options:[{label:'南区',description:'南部'},{label:'北区',description:'北部'}],multiSelect:false}];
const base={session_id:'native',prompt_id:'prompt',cwd:root,transcript_path:root+'/native.jsonl',tool_name:'AskUserQuestion',tool_use_id:'toolu_sentinel'};
const signal=(event,extra={})=>panes.signal('launch',JSON.stringify({...base,hook_event_name:event,...extra}),new Date().toISOString());
const state=()=>agentState({...panes.status('thread'),lifecycle:'running'},store.read(),root);
const report={status:'INCOMPLETE',scope:'real signal/SQLite; supplied PTY and runtime identity',model_turns:0,model_calls:0,vendor_calls:0,checks:[]};
try {
  report.failure_cases=await hookFailureContracts();
  assert.ok(report.failure_cases.every(c=>c.status==='PASS'),report.failure_cases.filter(c=>c.status!=='PASS').map(c=>c.name).join(', '));
  report.answer_lifecycle_cases=await answerLifecycleContracts();
  assert.ok(report.answer_lifecycle_cases.every(c=>c.status==='PASS'),report.answer_lifecycle_cases.filter(c=>c.status!=='PASS').map(c=>c.name).join(', '));
  store.event('turn_submitted',{id:'submission'},record);
  await signal('UserPromptSubmit',{prompt:dispatch.text});
  assert.equal(state(),'running');
  const unverified=()=>store.read().filter(e=>e.type==='native_question_unverified').length;
  for (const event of ['PreToolUse','PostToolUse','PostToolUseFailure']) {
    const before=unverified();
    await signal(event,{tool_name:'Read',tool_input:{file_path:root+'/sentinel'}});
    assert.equal(state(),'running','A valid unrelated tool must remain ignored');
    assert.equal(unverified(),before);
    assert.equal(panes.questions('launch').length,0);
  }
  // Independent review F1: valid root identity and payload, absent tool_name.
  // Observe projection before checking rejection, so the old candidate fails
  // on the user-visible running != unknown defect rather than a harness error.
  for (const event of ['PreToolUse','PostToolUse','PostToolUseFailure']) {
    const before=unverified();let refusal;
    try { await signal(event,{tool_name:undefined,tool_input:{questions}}); } catch(error) { refusal=error; }
    assert.equal(state(),'unknown','Hook with missing tool_name must not promote the session to running');
    assert.ok(refusal,'Malformed tool hook must be rejected');
    assert.match(String(refusal),/question_tool_name_required/);
    assert.equal(unverified(),before+1,'Malformed tool hook must append a projectable unknown fact');
    assert.equal(panes.questions('launch').length,0);
  }
  for (const fields of [{tool_name:''},{tool_name:' '},{tool_name:null},{tool_name:7},{tool_use_id:undefined},
    {tool_name:'Read',tool_input:undefined},{tool_name:'Read',tool_input:null},{tool_name:'Read',tool_input:[]}]) {
    const before=unverified();
    await assert.rejects(signal('PreToolUse',{tool_input:{questions},...fields}));
    assert.equal(state(),'unknown');assert.equal(unverified(),before+1);
  }
  report.checks.push('valid_unrelated_tools_ignored','missing_tool_name_unknown_and_rejected','malformed_tool_envelope_unknown');
  await signal('PreToolUse',{tool_input:{questions},tool_use_id:'quarantined'});
  assert.equal(state(),'unknown','A new tool cannot repair an untrusted submission');
  await assert.rejects(panes.answerQuestion('launch','launch:quarantined',['北区'],async()=>{},async()=>{}));
  pane.active={...pane.active,id:'verified-submission'};pane.claudePromptId=null;
  store.event('turn_submitted',{id:'verified-submission'},record);
  // Old unresolved entries are retained; the new submission is independent.
  await signal('UserPromptSubmit',{prompt:dispatch.text,prompt_id:'verified-prompt'});
  base.prompt_id='verified-prompt';
  await signal('PreToolUse',{tool_input:{questions}});
  assert.equal(state(),'waiting_user_answer','Structured root question must expose waiting_user_answer');
  const question=panes.questions('launch').find(q=>q.status==='waiting');
  assert.deepEqual(question.questions,questions);
  await assert.rejects(signal('PreToolUse',{prompt_id:'other',tool_input:{questions}}));
  assert.equal(state(),'waiting_user_answer','A stale hook cannot clear the root question');
  await assert.rejects(signal('PreToolUse',{prompt_id:'other',tool_name:undefined,tool_input:{questions}}));
  await assert.rejects(signal('PreToolUse',{session_id:'other',tool_name:undefined,tool_input:{questions}}));
  assert.equal(state(),'waiting_user_answer','Malformed stale or foreign hooks cannot replace the current question');
  await assert.rejects(panes.answerQuestion('launch',question.id,['北区'],async()=>{},async()=>{throw new Error('revoked');}));
  assert.equal(writes.length,0);
  // A refused identity must not poison a subsequent valid write.
  await panes.answerQuestion('launch',question.id,['北区'],async(text,id)=>inputs.push({text,id}),async()=>{});
  assert.equal(inputs.length,1);assert.equal(inputs[0].id,question.id);
  assert.ok(writes.length>0,'Answer must reach the bound PTY');
  assert.equal(pane.active.id,'verified-submission','Native question answer cannot replace the active root submission');
  assert.equal(pane.claudePromptId,'verified-prompt');
  assert.notEqual(state(),'running','PTY write does not prove the native tool accepted an answer');
  await assert.rejects(panes.answerQuestion('launch',question.id,['北区'],async()=>{},async()=>{}));
  assert.equal(inputs.length,1,'Duplicate answer must not create another user input');
  await signal('PostToolUse',{tool_input:{questions,answers:{'选择发布区域？':'北区'}},tool_response:{questions,answers:{'选择发布区域？':'北区'}}});
  assert.equal(state(),'running');
  await signal('Stop',{stop_hook_active:false});assert.equal(pane.state,'idle');
  assert.equal(panes.questions('launch').find(q=>q.id===question.id).status,'answered');
  report.checks.push('root_question_and_native_answer', 'stale_hook_is_rejected', 'revoked_identity_no_write',
    'duplicate_answer_rejected', 'answer_keeps_root_submission', 'write_waits_for_native_confirmation');
  const codexRecord={...record,id:'codex-launch',thread:'codex-thread',role:'worker',attempt:'attempt',cli:'Codex',env:{CODEX_HOME:root},worktree:root};
  store.launch(codexRecord);
  const nativeFile=root+'/sessions/native.jsonl';
  const {mkdirSync}=await import('node:fs');mkdirSync(root+'/sessions');mkdirSync(root+'/traces/codex-launch',{recursive:true});
  writeFileSync(nativeFile,[{type:'session_meta',payload:{id:'native',source:'cli',cwd:root}},
    {type:'event_msg',payload:{type:'task_started',turn_id:'turn'}},
    {type:'response_item',payload:{type:'function_call',name:'request_user_input',call_id:'codex-call'}}].map(JSON.stringify).join('\n')+'\n');
  const codexPane={...pane,record:codexRecord,attempt:{workspace:root},state:'busy',active:{id:'codex-submission',nativeTurn:'turn'},
    native:'native',nativeFile:undefined,turn:'turn',inputGeneration:0,offsets:new Map(),writes:Promise.resolve()};
  panes.panes.set(codexRecord.thread,codexPane);
  const codexSignal=(event,extra={})=>panes.signal(codexRecord.id,JSON.stringify({session_id:'native',turn_id:'turn',cwd:root,
    transcript_path:nativeFile,tool_name:'request_user_input',tool_use_id:'codex-call',hook_event_name:event,
    tool_input:{questions:[{id:'sentinel-id',question:'选择发布区域？',header:'区域',options:questions[0].options}]},...extra}),new Date().toISOString());
  const codexState=()=>agentState(panes.status(codexRecord.thread),store.read().filter(e=>e.launch===codexRecord.id),root);
  await codexSignal('PreToolUse');assert.equal(codexState(),'waiting_controller_answer');
  await codexSignal('PostToolUse',{tool_response:JSON.stringify({answers:{'sentinel-id':{answers:['北区']}}})});
  assert.equal(codexState(),'running','Confirmed Codex answer must release the native-log pending marker');
  await codexSignal('PreToolUse',{tool_name:'exec_command',tool_input:{cmd:'pwd'}});
  assert.equal(codexState(),'running','Valid unrelated Codex tool remains ignored');
  await assert.rejects(codexSignal('PreToolUse',{tool_name:undefined}));
  assert.equal(codexState(),'unknown','Missing Codex tool_name must also remain unknown');
  report.checks.push('codex_worker_waits_for_controller','codex_confirmed_answer_releases_native_marker');
  pane.active={id:'second',dispatch:dispatch.id,at:'2026-10-20T00:00:00Z',nativeTurn:null};pane.claudePromptId='second-prompt';pane.state='busy';
  await assert.rejects(signal('PreToolUse',{prompt_id:'second-prompt',tool_use_id:'missing-fields',tool_input:{}}));
  assert.equal(state(),'unknown','Missing question fields must remain unknown');
  await assert.rejects(signal('PreToolUse',{prompt_id:'second-prompt',agent_id:'child',tool_use_id:'child',tool_input:{questions}}));
  assert.equal(panes.questions('launch').length,2,'Subagent hook must not register a root question');
  pane.active={...pane.active,id:'third'};pane.claudePromptId='second-prompt';
  await signal('PreToolUse',{prompt_id:'second-prompt',tool_use_id:'second-call',tool_input:{questions}});
  const secondQuestion=panes.questions('launch').find(q=>q.tool_use_id==='second-call');
  pane.inputGeneration++;
  const beforeWrites=writes.length;
  await assert.rejects(panes.answerQuestion('launch',secondQuestion.id,['北区'],async()=>{},async()=>{}));
  assert.equal(writes.length,beforeWrites,'Changed native selection must reject automated keys');
  await signal('PostToolUseFailure',{prompt_id:'second-prompt',tool_use_id:'second-call',tool_input:{questions},is_interrupt:true,error:'cancelled'});
  assert.equal(panes.questions('launch').find(q=>q.id===secondQuestion.id).status,'cancelled');
  report.checks.push('missing_fields_unknown','subagent_rejected','changed_input_no_write','native_cancel_resolves_question');
  report.status='PASS';
} catch(error) {report.error=String(error);report.stack=error.stack;}
finally {store.close();report.retained_fixture=root;writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify(report));process.exitCode=report.status==='PASS'?0:1;
