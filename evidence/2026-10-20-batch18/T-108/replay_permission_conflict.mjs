// Historical #26 blanket-permission diagnostic. Superseded by controller #28;
// use replay_permission_same_question.mjs for the current acceptance contract.
// Observe the exact normal-path hook sequence already recorded by the controller.
// No CLI, model, credentials, source mutation or current user terminal is used.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { Panes } from '../../../workbench/src/panes.ts';
import { OrchestrationStore } from '../../../workbench/src/store.ts';
import { agentState } from '../../../workbench/src/sidebar.ts';
const [original, output] = process.argv.slice(2);
assert(original && output);
const source = JSON.parse(readFileSync(original,'utf8'));
assert.equal(source.status,'PASS');
const hooks=source.hooks, first=hooks.find(h=>h.hook_event_name==='UserPromptSubmit');
const root=mkdtempSync('/private/tmp/t108-permission-conflict-');
const store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
const record={id:'original-replay',thread:'original-replay',task:'T108-replay',attempt:null,role:'controller',preset:'ideation',
  cli:'Claude Code',session:first.session_id,turn_limit:1,worktree:first.cwd};
store.launch(record);
const writes=[],answers=[],states=[];
const pane={record,native:first.session_id,state:'busy',failed:null,stopped:false,archived:false,interrupted:false,
  active:{id:'original-submission',dispatch:'input:original',at:'2026-10-20T00:00:00Z',nativeTurn:null},
  claudePromptId:null,claudePromptIds:new Set(),queue:[],writing:false,writes:Promise.resolve(),pendingInputs:0,
  inputGeneration:0,userDraft:false,stopInProgress:false,pty:{write:value=>writes.push(value)}};
panes.panes.set(record.thread,pane);
const report={status:'INCOMPLETE',original,original_status:source.status,scope:'exact recorded normal CLI hooks through signal/SQLite; supplied PTY',
  model_calls:0,vendor_calls:0,fixture:root,states};
try {
  store.event('turn_submitted',{id:pane.active.id},record);
  for (const hook of hooks) {
    if(!['UserPromptSubmit','PreToolUse','PermissionRequest'].includes(hook.hook_event_name))continue;
    await panes.signal(record.id,JSON.stringify(hook),new Date().toISOString());
    states.push({event:hook.hook_event_name,tool:hook.tool_name,state:agentState(panes.status(record.thread),store.read(),record.worktree),
      questions:panes.questions(record.id).map(q=>({id:q.id,status:q.status}))});
    if(hook.hook_event_name==='PermissionRequest')break;
  }
  assert.equal(states.at(-2).state,'waiting_user_answer');
  assert.equal(states.at(-1).tool,'AskUserQuestion');
  assert.equal(states.at(-1).state,'unknown');
  const question=panes.questions(record.id)[0];
  let refused;
  try {await panes.answerQuestion(record.id,question.id,['西区'],async(...a)=>answers.push(a),async()=>{});}catch(error){refused=String(error);}
  assert(refused);assert.equal(answers.length,0);assert.equal(writes.length,0);
  Object.assign(report,{status:'PASS',answer_refusal:refused,answer_records:answers.length,pty_writes:writes.length,
    decision_required:'Normal AskUserQuestion emits PermissionRequest too; #26 blanket refusal blocks the original app answer path.'});
} catch(error){report.error=String(error);report.stack=error.stack;}
finally {store.close();writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify(report));process.exitCode=report.status==='PASS'?0:1;
