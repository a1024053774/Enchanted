// Independent oracle: T-108 unknown-state contract and review-02 counterexamples.
// Real signal/SQLite/projection and answer path; supplied runtime identity/PTY.
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { OrchestrationStore } from '../src/store.ts';
import { Panes } from '../src/panes.ts';
import { agentState } from '../src/sidebar.ts';

export async function hookFailureContracts() {
  const results=[];
  const scenarios=[
    {name:'pending_missing_tool_name',pending:true,event:'PostToolUse',extra:{tool_name:undefined}},
    {name:'pending_invalid_response',pending:true,event:'PostToolUse',extra:{tool_response:'{'}},
    {name:'running_stop_missing_active',pending:false,event:'Stop',extra:{stop_hook_active:undefined}},
    {name:'pending_stop_missing_active',pending:true,event:'Stop',extra:{stop_hook_active:undefined}},
    {name:'pending_stop_invalid_active',pending:true,event:'Stop',extra:{stop_hook_active:'false'}},
    {name:'answer_recording_invalidated',pending:true,event:'PostToolUse',extra:{tool_response:'{'},duringRecord:true},
    {name:'answer_first_key_invalidated',pending:true,event:'PostToolUse',extra:{tool_name:undefined},guardCall:2,expectedKeys:0},
    {name:'answer_later_key_invalidated',pending:true,event:'PostToolUse',extra:{tool_response:'{'},guardCall:3,expectedKeys:1},
  ];
  for (const scene of scenarios) {
    const root=mkdtempSync('/private/tmp/t108-hook-failure-');
    const store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
    const record={id:'launch',thread:'thread',task:'task',project:'project',attempt:null,role:'controller',preset:'ideation',
      session:'native',cli:'Claude Code',turn_limit:1,worktree:root};
    store.launch(record);
    const dispatch=store.register(record.id,'Ask the sentinel question.');
    const writes=[],inputs=[],transfers=[];
    const pane={record,native:'native',state:'busy',failed:null,stopped:false,archived:false,interrupted:false,
      stopInProgress:false,active:{id:'submission',dispatch:dispatch.id,at:'2026-10-20T00:00:00Z',nativeTurn:null},
      claudePromptId:null,claudePromptIds:new Set(),queue:[],writing:false,writes:Promise.resolve(),pendingInputs:0,
      userDraft:false,inputGeneration:0,pty:{write:data=>writes.push(data)}};
    panes.panes.set(record.thread,pane);
    const questions=[{question:'选择备份区域？',header:'区域',options:[{label:'山区',description:'山地'},
      {label:'海区',description:'沿海'}],multiSelect:false}];
    const base={session_id:'native',prompt_id:'prompt',cwd:root,transcript_path:root+'/native.jsonl',
      tool_name:'AskUserQuestion',tool_use_id:'toolu_sentinel',tool_input:{questions}};
    const signal=(event,extra={})=>panes.signal(record.id,JSON.stringify({...base,hook_event_name:event,
      ...(event==='Stop'?{tool_name:undefined,tool_use_id:undefined,tool_input:undefined}:{}),...extra}),
      new Date().toISOString(),async(...args)=>transfers.push(args));
    const state=()=>agentState(panes.status(record.thread),store.read(),root);
    const result={name:scene.name,status:'INCOMPLETE',fixture:root};
    try {
      store.event('turn_submitted',{id:'submission'},record);
      await signal('UserPromptSubmit',{prompt:dispatch.text});
      if(scene.pending)await signal('PreToolUse');
      assert.equal(state(),scene.pending?'waiting_user_answer':'running');
      // Foreign/stale errors cannot revoke a valid current question.
      for(const extra of (scene.pending?[{prompt_id:'old'},{session_id:'foreign'},{agent_id:'child'}]:[{session_id:'foreign'}])) {
        await assert.rejects(signal('PostToolUse',{tool_name:undefined,...extra}));
        assert.equal(state(),scene.pending?'waiting_user_answer':'running');
      }
      await signal('PreToolUse',{tool_name:'Read',tool_input:{file_path:root+'/sentinel'}});
      await signal('Stop',{prompt_id:'old',stop_hook_active:false});
      await signal('Stop',{prompt_id:'old'});
      await signal('Stop',{stop_hook_active:true});
      assert.equal(state(),scene.pending?'waiting_user_answer':'running');
      assert.equal(transfers.length,0,'Unmatched Stops must not transfer delivery');
      const before=store.read().length;
      let refusal;
      try {
        if(scene.duringRecord || scene.guardCall) {
          let guards=0;
          await panes.answerQuestion(record.id,'launch:toolu_sentinel',['海区'],async(...args)=>{
            inputs.push(args);
            if(scene.duringRecord)await assert.rejects(signal(scene.event,scene.extra));
          },async()=>{
            if(++guards===scene.guardCall)await assert.rejects(signal(scene.event,scene.extra));
          });
        } else await signal(scene.event,scene.extra);
      } catch(error) { refusal=error; }
      result.observed=state();
      assert.equal(result.observed,'unknown',scene.name+': malformed current hook must revoke positive state');
      assert.ok(refusal,scene.name+': malformed current hook must be rejected');
      const failure=store.read().slice(before).find(e=>e.type==='native_question_unverified');
      assert.ok(failure,'Malformed current hook must persist an unknown fact');
      assert.equal(failure.data.session_id,'native');assert.equal(failure.data.submission,'submission');
      assert.equal(failure.data.turn,'prompt');
      if(scene.pending) {
        assert.equal(failure.data.question,'launch:toolu_sentinel');
        assert.equal(panes.questions(record.id)[0].status,'unknown');
        await assert.rejects(panes.answerQuestion(record.id,'launch:toolu_sentinel',['海区'],
          async(...args)=>inputs.push(args),async()=>{}));
      }
      assert.equal(writes.length,scene.expectedKeys??0,'No further PTY keys may follow invalidation');
      assert.equal(inputs.length,scene.duringRecord||scene.guardCall?1:0,'Only an answer begun before invalidation may have an input record');
      assert.equal(transfers.length,0,'Malformed Stop must not invoke delivery transfer');
      assert.equal(pane.active.id,'submission');assert.equal(pane.claudePromptId,'prompt');
      assert.equal(pane.stopInProgress,false);assert.equal(pane.state,'busy');
      assert.equal(store.read().filter(e=>['pane_idle','pane_completion_held'].includes(e.type)).length,0);
      // A later unrelated tool cannot repair the lost question evidence.
      await signal('PostToolUse',{tool_name:'Read',tool_input:{file_path:root+'/sentinel'},tool_response:'{'});
      assert.equal(state(),'unknown');
      result.status='PASS';
    } catch(error) {result.error=String(error);result.stack=error.stack;}
    finally {store.close();results.push(result);}
  }
  return results;
}
