// Oracle: controller #32 and review-05. Actual signal/store/write queue; supplied
// PTY/identity. An exact native answer is success, but never a substitute for
// live identity, input generation, turn trust or a known PTY write outcome.
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { OrchestrationStore } from '../src/store.ts';
import { Panes } from '../src/panes.ts';

export async function answerLifecycleContracts() {
  const results=[];
  for(const scene of ['early','early_stop','late','after_last_key','different_answer','revoked_after_confirmation',
    'changed_after_confirmation','unknown_after_confirmation','unknown_during_answer','recorder_refused','unknown_pty','unknown_pty_queued',
    'shell_refusal','shell_unknown_pty']) {
    const root=mkdtempSync('/private/tmp/t108-answer-lifecycle-'),store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
    const record={id:'launch',thread:'thread',task:'task',attempt:null,role:'controller',preset:'ideation',session:'native',cli:'Claude Code',turn_limit:1,worktree:root};
    store.launch(record);const dispatch=store.register(record.id,'Ask region.');
    const writes=[],inputs=[],transfers=[];
    const pane={record,native:'native',state:'busy',failed:null,stopped:false,archived:false,interrupted:false,
      active:{id:'submission',dispatch:dispatch.id,at:'2026-10-20T00:00:00Z',nativeTurn:null},
      claudePromptId:null,claudePromptIds:new Set(),queue:[],writing:false,writes:Promise.resolve(),pendingInputs:0,
      userDraft:false,draft:{chars:[],cursor:0,keys:[],uncertain:false},inputGeneration:0,stopInProgress:false,pty:{write:value=>writes.push(value)}};
    panes.panes.set(record.thread,pane);
    const questions=[{question:'选择发布区域？',header:'区域',options:[{label:'南区'},{label:'北区'}],multiSelect:false}];
    const signal=(event,extra={})=>panes.signal(record.id,JSON.stringify({session_id:'native',prompt_id:'prompt',cwd:root,
      transcript_path:root+'/native.jsonl',hook_event_name:event,tool_name:'AskUserQuestion',tool_use_id:'toolu_sentinel',
      tool_input:{questions},...extra}),new Date().toISOString(),async()=>transfers.push('transfer'));
    const confirm=(answer='北区')=>signal('PostToolUse',{tool_response:{answers:{'选择发布区域？':answer}}});
    const result={name:scene,status:'INCOMPLETE',fixture:root};
    try {
      store.event('turn_submitted',{id:'submission'},record);await signal('UserPromptSubmit',{prompt:dispatch.text});await signal('PreToolUse');
      if(scene.startsWith('shell_')) {
        pane.record.role='shell';
        if(scene==='shell_unknown_pty')pane.pty.write=value=>{writes.push(value);throw new Error('PTY outcome unknown');};
        await assert.rejects(panes.shellInput(record.id,'first','utf8',async()=>{if(scene==='shell_refusal')throw new Error('Identity revoked');}));
        if(scene==='shell_refusal') {
          await panes.shellInput(record.id,'next sentinel','utf8',async()=>{});
          assert.deepEqual(writes,['next sentinel']);assert.equal(pane.failed,null);
        }else{
          assert.ok(pane.failed);await assert.rejects(panes.shellInput(record.id,'next sentinel','utf8',async()=>{}));assert.deepEqual(writes,['first']);
        }
        result.status='PASS';continue;
      }
      if(scene==='unknown_pty_queued') {
        let release,entered;const enteredPromise=new Promise(resolve=>entered=resolve),hold=new Promise(resolve=>release=resolve);
        pane.pty.write=value=>{writes.push(value);throw new Error('PTY outcome unknown');};
        const first=panes.userInput(record.id,'first\r',{request_id:'first'},async()=>{entered();await hold;},async()=>{});
        const firstRejected=assert.rejects(first);await enteredPromise;
        const second=panes.userInput(record.id,'queued\r',{request_id:'queued'},async()=>inputs.push('queued'),async()=>{});
        const secondRejected=assert.rejects(second);release();await Promise.all([firstRejected,secondRejected]);
        assert.ok(pane.failed);assert.deepEqual(writes,['first\r']);assert.equal(inputs.length,0);
        result.status='PASS';continue;
      }
      let guards=0,operationError,completion;
      if(scene==='unknown_pty')pane.pty.write=value=>{writes.push(value);throw new Error('PTY outcome unknown');};
      let nativeDuringLast;
      if(scene==='after_last_key')pane.pty.write=value=>{writes.push(value);if(writes.length===3)nativeDuringLast=confirm();};
      try {
        completion=await panes.answerQuestion(record.id,'launch:toolu_sentinel',['北区'],async(...args)=>{
          if(scene==='recorder_refused')throw new Error('Recorder refused before writing');inputs.push(args);
        },async()=>{
          guards++;
          if(scene==='unknown_during_answer' && guards===3)await assert.rejects(signal('PostToolUse',{tool_response:'{'}));
          if(['early','early_stop','different_answer','revoked_after_confirmation','changed_after_confirmation','unknown_after_confirmation'].includes(scene) && guards===4){
            await confirm(scene==='different_answer'?'南区':'北区');
            if(scene==='early_stop')await signal('Stop',{stop_hook_active:false});
            if(scene==='revoked_after_confirmation')throw new Error('Identity revoked');
            if(scene==='changed_after_confirmation')pane.inputGeneration++;
            if(scene==='unknown_after_confirmation')await assert.rejects(signal('PreToolUse',{tool_name:undefined}));
          }
        });
      }catch(error){operationError=String(error);}
      if(nativeDuringLast)await nativeDuringLast;
      if(scene==='late')await confirm();
      const bytesBeforeNext=[...writes];
      const normal=['early','early_stop','late','after_last_key'].includes(scene);
      let nextError;
      try {await panes.userInput(record.id,'next sentinel',{request_id:'next'},async()=>{},async()=>{});}catch(error){nextError=String(error);}
      Object.assign(result,{operation_error:operationError,next_error:nextError,answer_keys:bytesBeforeNext,all_keys:[...writes],completion});
      if(normal){
        assert.equal(operationError,undefined,'Native confirmation must succeed, not reject the first answer');
        assert.deepEqual(bytesBeforeNext,scene==='early'||scene==='early_stop'?['\x1b[B','\r']:['\x1b[B','\r','\r']);
        assert.equal(panes.questions(record.id)[0].status,'answered');
        assert.equal(inputs.length,1);assert.equal(completion?.confirmed,scene!=='late');
        assert.equal(nextError,undefined,'A confirmed answer must leave the original input stream usable');
        assert.deepEqual(writes,[...bytesBeforeNext,'next sentinel']);
        await assert.rejects(panes.answerQuestion(record.id,'launch:toolu_sentinel',['北区'],async()=>inputs.push('duplicate'),async()=>{}));
        assert.equal(inputs.length,1);
        assert.equal(transfers.length,scene==='early_stop'?1:0);
      }else{
        assert.ok(operationError,'Invalidation must remain an error, even after native confirmation');
        assert.equal(completion,undefined);assert.equal(bytesBeforeNext.length,scene==='recorder_refused'?0:scene==='unknown_during_answer'||scene==='unknown_pty'?1:2);
        if(scene==='unknown_pty'){
          assert.ok(pane.failed);assert.ok(nextError);assert.deepEqual(writes,bytesBeforeNext,'Unknown physical write must block further bytes');
        }else{
          assert.equal(nextError,undefined,'Ordinary refusal cannot poison later independently checked input');
          assert.deepEqual(writes,[...bytesBeforeNext,'next sentinel']);
        }
        assert.equal(store.read().filter(e=>e.type==='native_question_answer_written').length,0);
        assert.equal(transfers.length,0);assert.equal(pane.active.id,'submission');assert.equal(pane.stopInProgress,false);
      }
      result.status='PASS';
    }catch(error){result.error=String(error);result.stack=error.stack;}
    finally{store.close();results.push(result);}
  }
  return results;
}
