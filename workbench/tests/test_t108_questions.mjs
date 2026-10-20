// Contract from T-108 and installed CLI hook samples. Real signal entry, SQLite,
// PTY write boundary; supplied process identity is not a live CLI proof.
// Failures: missing/stale/auxiliary fields, duplicate answer, changed input,
// failed recorder/write, early state release, root completion swallowed.
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { OrchestrationStore } from '../src/store.ts';
import { Panes } from '../src/panes.ts';
import { agentState } from '../src/sidebar.ts';

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
const report={status:'INCOMPLETE',scope:'real signal/SQLite; supplied PTY and runtime identity',model_turns:0,checks:[]};
try {
  store.event('turn_submitted',{id:'submission'},record);
  await signal('UserPromptSubmit',{prompt:dispatch.text});
  assert.equal(state(),'running');
  await signal('PreToolUse',{tool_input:{questions}});
  assert.equal(state(),'waiting_user_answer','Structured root question must expose waiting_user_answer');
  const question=panes.questions('launch').find(q=>q.status==='waiting');
  assert.deepEqual(question.questions,questions);
  await assert.rejects(signal('PreToolUse',{prompt_id:'other',tool_input:{questions}}));
  assert.equal(state(),'waiting_user_answer','A stale hook cannot clear the root question');
  await assert.rejects(panes.answerQuestion('launch',question.id,['北区'],async()=>{},async()=>{throw new Error('revoked');}));
  assert.equal(writes.length,0);
  // A refused identity must not poison a subsequent valid write.
  pane.writes=Promise.resolve();
  await panes.answerQuestion('launch',question.id,['北区'],async(text,id)=>inputs.push({text,id}),async()=>{});
  assert.equal(inputs.length,1);assert.equal(inputs[0].id,question.id);
  assert.ok(writes.length>0,'Answer must reach the bound PTY');
  assert.equal(pane.active.id,'submission','Native question answer cannot replace the active root submission');
  assert.equal(pane.claudePromptId,'prompt');
  assert.notEqual(state(),'running','PTY write does not prove the native tool accepted an answer');
  await assert.rejects(panes.answerQuestion('launch',question.id,['北区'],async()=>{},async()=>{}));
  assert.equal(inputs.length,1,'Duplicate answer must not create another user input');
  await signal('PostToolUse',{tool_input:{questions,answers:{'选择发布区域？':'北区'}},tool_response:{questions,answers:{'选择发布区域？':'北区'}}});
  assert.equal(state(),'running');
  await signal('Stop',{stop_hook_active:false});assert.equal(pane.state,'idle');
  assert.equal(panes.questions('launch')[0].status,'answered');
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
    native:'native',nativeFile,turn:'turn',inputGeneration:0,offsets:new Map(),writes:Promise.resolve()};
  panes.panes.set(codexRecord.thread,codexPane);
  const codexSignal=(event,extra={})=>panes.signal(codexRecord.id,JSON.stringify({session_id:'native',turn_id:'turn',cwd:root,
    transcript_path:nativeFile,tool_name:'request_user_input',tool_use_id:'codex-call',hook_event_name:event,
    tool_input:{questions:[{id:'sentinel-id',question:'选择发布区域？',header:'区域',options:questions[0].options}]},...extra}),new Date().toISOString());
  const codexState=()=>agentState(panes.status(codexRecord.thread),store.read().filter(e=>e.launch===codexRecord.id),root);
  await codexSignal('PreToolUse');assert.equal(codexState(),'waiting_controller_answer');
  await codexSignal('PostToolUse',{tool_response:JSON.stringify({answers:{'sentinel-id':{answers:['北区']}}})});
  assert.equal(codexState(),'running','Confirmed Codex answer must release the native-log pending marker');
  report.checks.push('codex_worker_waits_for_controller','codex_confirmed_answer_releases_native_marker');
  pane.active={id:'second',dispatch:dispatch.id,at:'2026-10-20T00:00:00Z',nativeTurn:null};pane.claudePromptId='second-prompt';pane.state='busy';pane.writes=Promise.resolve();
  await assert.rejects(signal('PreToolUse',{prompt_id:'second-prompt',tool_use_id:'missing-fields',tool_input:{}}));
  assert.equal(state(),'unknown','Missing question fields must remain unknown');
  await assert.rejects(signal('PreToolUse',{prompt_id:'second-prompt',agent_id:'child',tool_use_id:'child',tool_input:{questions}}));
  assert.equal(panes.questions('launch').length,1,'Subagent hook must not register a root question');
  await signal('PreToolUse',{prompt_id:'second-prompt',tool_use_id:'second-call',tool_input:{questions}});
  const secondQuestion=panes.questions('launch').find(q=>q.tool_use_id==='second-call');
  pane.inputGeneration++;
  const beforeWrites=writes.length;
  await assert.rejects(panes.answerQuestion('launch',secondQuestion.id,['北区'],async()=>{},async()=>{}));
  assert.equal(writes.length,beforeWrites,'Changed native selection must reject automated keys');
  pane.writes=Promise.resolve();
  await signal('PostToolUseFailure',{prompt_id:'second-prompt',tool_use_id:'second-call',tool_input:{questions},is_interrupt:true,error:'cancelled'});
  assert.equal(panes.questions('launch').find(q=>q.id===secondQuestion.id).status,'cancelled');
  report.checks.push('missing_fields_unknown','subagent_rejected','changed_input_no_write','native_cancel_resolves_question');
  report.status='PASS';
} catch(error) {report.error=String(error);report.stack=error.stack;}
finally {store.close();report.retained_fixture=root;writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify(report));process.exitCode=report.status==='PASS'?0:1;
