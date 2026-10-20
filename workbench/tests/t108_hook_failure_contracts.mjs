// Independent oracle: T-108 unknown-state contract and review-02 counterexamples.
// Real signal/SQLite/projection and answer path; supplied runtime identity/PTY.
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
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
  // Controller #26: shared association fields, every subscribed hook, and
  // independent complete/current, explicitly old, foreign and child controls.
  for (const cli of ['Claude Code','Codex']) for (const event of ['PreToolUse','PostToolUse','PostToolUseFailure','Stop','PermissionRequest','UserPromptSubmit']) {
    for (const field of ['cwd','transcript_path',cli==='Codex'?'turn_id':'prompt_id','session_id',
      ...(['PreToolUse','PostToolUse','PostToolUseFailure'].includes(event)?['tool_name','tool_use_id','tool_input']:event==='PermissionRequest'?['tool_name','tool_input']:[])]) {
      for (const control of ['missing','complete','old','foreign','child']) {
        scenarios.push({name:`matrix_${cli}_${event}_${field}_${control}`,cli,pending:true,event,field,control,
          extra:control==='complete'?{}:{[field]:undefined,...(control==='old'?{[cli==='Codex'?'turn_id':'prompt_id']:'old'}:
            control==='foreign'?{session_id:'foreign'}:control==='child'?{agent_id:'child'}:{})}});
      }
    }
  }
  for (const cli of ['Claude Code','Codex']) for (const field of ['cwd','transcript_path',cli==='Codex'?'turn_id':'prompt_id','session_id']) {
    scenarios.push({name:`running_${cli}_Stop_${field}_missing`,cli,pending:false,event:'Stop',extra:{[field]:undefined}});
  }
  scenarios.push({name:'pending_malformed_json',pending:true,event:'Stop',extra:{},raw:'{'},
    {name:'pending_invalid_received_at',pending:true,event:'Stop',extra:{},receivedAt:'invalid'});
  scenarios.push({name:'permission_answer_first_key',pending:true,event:'PermissionRequest',extra:{},permission:true,guardCall:2,expectedKeys:0},
    {name:'permission_answer_later_key',pending:true,event:'PermissionRequest',extra:{},permission:true,guardCall:3,expectedKeys:1},
    {name:'pending_unrecognized_hook',pending:true,event:'Notification',extra:{}},
    {name:'pending_unverified_response',pending:true,event:'PostToolUse',extra:{tool_response:null}});
  scenarios.push({name:'permission_after_pending_question',pending:true,event:'PermissionRequest',extra:{},permission:true});
  // #28: a PermissionRequest for the very same AskUserQuestion remains
  // answerable; every independent or unverifiable request revokes the old one.
  for (const mode of ['full','matching_id','no_content','sending']) scenarios.push({
    name:'permission_self_'+mode,pending:true,event:'PermissionRequest',self:true,mode,extra:{}});
  for (const mode of ['wrong_id','wrong_text','wrong_option','wrong_header','wrong_turn','null_id','invalid_content']) scenarios.push({
    name:'permission_self_'+mode,pending:true,event:'PermissionRequest',selfMismatch:true,mode,extra:{}});
  for (const field of ['cwd','transcript_path','prompt_id','session_id']) scenarios.push({
    name:'permission_self_missing_'+field,pending:true,event:'PermissionRequest',selfMismatch:true,extra:{[field]:undefined}});
  for (const scene of scenarios) {
    const codex=scene.cli==='Codex', turnField=codex?'turn_id':'prompt_id';
    const waiting=codex?'waiting_controller_answer':'waiting_user_answer';
    const root=mkdtempSync('/private/tmp/t108-hook-failure-');
    const store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
    const record={id:'launch',thread:'thread',task:'task',project:'project',attempt:codex?'attempt':null,role:codex?'worker':'controller',preset:'ideation',
      session:'native',cli:scene.cli??'Claude Code',turn_limit:1,worktree:root,env:{CODEX_HOME:root}};
    store.launch(record);
    const dispatch=store.register(record.id,'Ask the sentinel question.');
    const writes=[],inputs=[],transfers=[];
    const pane={record,attempt:codex?{workspace:root}:null,native:'native',state:'busy',failed:null,stopped:false,archived:false,interrupted:false,
      stopInProgress:false,active:{id:'submission',dispatch:dispatch.id,at:'2026-10-20T00:00:00Z',nativeTurn:codex?'prompt':null},
      claudePromptId:null,claudePromptIds:new Set(),queue:[],writing:false,writes:Promise.resolve(),pendingInputs:0,
      nativeFile:root+'/native.jsonl',turn:codex?'prompt':null,offsets:new Map(),
      userDraft:false,inputGeneration:0,pty:{write:data=>writes.push(data)}};
    if(codex){mkdirSync(root+'/traces/launch',{recursive:true});writeFileSync(pane.nativeFile,[
      {type:'session_meta',payload:{id:'native',source:'cli',cwd:root}},
      {type:'event_msg',payload:{type:'task_started',turn_id:'prompt'}}].map(JSON.stringify).join('\n')+'\n');}
    panes.panes.set(record.thread,pane);
    const questions=[{...(codex?{id:'sentinel'}:{}),question:'选择备份区域？',header:'区域',options:[{label:'山区',description:'山地'},
      {label:'海区',description:'沿海'}],multiSelect:false}];
    const base={session_id:'native',[turnField]:'prompt',cwd:root,transcript_path:root+'/native.jsonl',
      tool_name:codex?'request_user_input':'AskUserQuestion',tool_use_id:'toolu_sentinel',tool_input:{questions}};
    const signal=(event,extra={},receivedAt=new Date().toISOString())=>panes.signal(record.id,JSON.stringify({...base,hook_event_name:event,
      ...(event==='Stop'?{tool_name:undefined,tool_use_id:undefined,tool_input:undefined,stop_hook_active:false}:{}),
      ...(event==='PermissionRequest'?{tool_name:'Bash',tool_use_id:undefined,tool_input:{command:'printf sentinel'}}:{}),
      ...(event==='PostToolUse'?{tool_response:{answers:codex?{sentinel:{answers:['海区']}}:{'选择备份区域？':'海区'}}}:{}),
      ...(event==='UserPromptSubmit'?{prompt:dispatch.text}:{}),...extra}),
      receivedAt,async(...args)=>transfers.push(args));
    const state=()=>agentState(panes.status(record.thread),store.read(),root);
    const result={name:scene.name,status:'INCOMPLETE',fixture:root};
    try {
      store.event('turn_submitted',{id:'submission'},record);
      const initialSubmit = scene.event==='UserPromptSubmit' && scene.control==='complete';
      if(!initialSubmit)await signal('UserPromptSubmit',{prompt:dispatch.text});
      if(scene.pending && !initialSubmit)await signal('PreToolUse');
      assert.equal(state(),initialSubmit?'unknown':scene.pending?waiting:'running');
      if(!initialSubmit) {
        // Foreign/stale errors cannot revoke a valid current question.
        for(const extra of (scene.pending?[{[turnField]:'old'},{session_id:'foreign'},{agent_id:'child'}]:[{session_id:'foreign'}])) {
          await assert.rejects(signal('PostToolUse',{tool_name:undefined,...extra}));
          assert.equal(state(),scene.pending?waiting:'running');
        }
        await signal('PreToolUse',{tool_name:'Read',tool_input:{file_path:root+'/sentinel'}});
        await signal('Stop',{[turnField]:'old',stop_hook_active:false});
        await signal('Stop',{[turnField]:'old'});
        if(!codex)await signal('Stop',{stop_hook_active:true});
        assert.equal(state(),scene.pending?waiting:'running');
        assert.equal(transfers.length,0,'Unmatched Stops must not transfer delivery');
      }
      if(scene.control==='complete' && scene.event==='Stop')await signal('PostToolUse');
      if(scene.self || scene.selfMismatch) {
        scene.extra={tool_name:'AskUserQuestion',tool_input:{questions:JSON.parse(JSON.stringify(questions))},...scene.extra};
        if(scene.mode==='matching_id')scene.extra.tool_use_id='toolu_sentinel';
        if(scene.mode==='no_content')scene.extra.tool_input={};
        if(scene.mode==='wrong_id')scene.extra.tool_use_id='different-question';
        if(scene.mode==='null_id')scene.extra.tool_use_id=null;
        if(scene.mode==='wrong_turn')scene.extra.turn_id='different-turn';
        if(scene.mode==='wrong_text')scene.extra.tool_input.questions[0].question='另一个问题？';
        if(scene.mode==='wrong_option')scene.extra.tool_input.questions[0].options[0].label='别的选项';
        if(scene.mode==='wrong_header')scene.extra.tool_input.questions[0].header='别的问题头';
        if(scene.mode==='invalid_content')scene.extra.tool_input.questions=null;
      }
      const before=store.read().length;
      if(scene.self) {
        if(scene.mode==='sending') {
          let guards=0;
          await panes.answerQuestion(record.id,'launch:toolu_sentinel',['海区'],async(...args)=>inputs.push(args),async()=>{
            if(++guards===2)await signal(scene.event,scene.extra);
          });
        } else {
          await signal(scene.event,scene.extra);
          assert.equal(state(),'waiting_user_answer','Same question permission must preserve waiting');
          assert.equal(panes.questions(record.id)[0].status,'waiting');
          await panes.answerQuestion(record.id,'launch:toolu_sentinel',['海区'],async(...args)=>inputs.push(args),async()=>{});
        }
        assert.equal(inputs.length,1);assert.equal(writes.length,3);
        assert.equal(pane.active.id,'submission');assert.equal(pane.claudePromptId,'prompt');
        assert.equal(store.read().slice(before).filter(e=>['permission_wait','native_question_unverified','pane_idle','pane_completion_held'].includes(e.type)).length,0);
        assert.equal(transfers.length,0);assert.equal(pane.stopInProgress,false);
        result.status='PASS';continue;
      }

      if(scene.control && scene.control!=='missing' && !(scene.event==='PermissionRequest' && scene.control==='complete')) {
        let refusal;
        try { await signal(scene.event,{...scene.extra,...(scene.event==='PreToolUse' && scene.control==='complete'?{tool_name:'Read',tool_input:{file_path:root+'/sentinel'}}:{})}); } catch(error) { refusal=error; }
        if(scene.control==='complete') {
          if(scene.event==='PreToolUse' || scene.event==='UserPromptSubmit') {
            assert.equal(refusal,undefined);assert.equal(state(),initialSubmit?'running':waiting);
          } else if(scene.event==='Stop') {
            assert.equal(refusal,undefined);assert.equal(state(),'idle');assert.equal(transfers.length,1);

          } else {
            assert.equal(refusal,undefined);assert.equal(state(),'running');
            assert.equal(panes.questions(record.id)[0].status,scene.event==='PostToolUse'?'answered':'cancelled');
          }
        } else {
          assert.equal(state(),waiting,'Explicit noncurrent origin must not revoke current question');
          assert.equal(store.read().slice(before).filter(e=>e.type==='native_question_unverified').length,0);
          await panes.answerQuestion(record.id,'launch:toolu_sentinel',['海区'],async(...args)=>inputs.push(args),async()=>{});
          assert.equal(inputs.length,1);assert.equal(writes.length,codex?2:3);
          assert.equal(pane.active.id,'submission');assert.equal(codex?pane.turn:pane.claudePromptId,'prompt');
          assert.equal(transfers.length,0);
        }
        result.status='PASS';continue;
      }
      const permission=scene.permission || scene.event==='PermissionRequest' && scene.control==='complete';
      let refusal;
      try {
        if(scene.duringRecord || scene.guardCall) {
          let guards=0;
          await panes.answerQuestion(record.id,'launch:toolu_sentinel',['海区'],async(...args)=>{
            inputs.push(args);
            if(scene.duringRecord)await assert.rejects(signal(scene.event,scene.extra));
          },async()=>{
            if(++guards===scene.guardCall){if(permission)await signal(scene.event,scene.extra);else await assert.rejects(signal(scene.event,scene.extra));}
          });
        } else if(scene.raw)await panes.signal(record.id,scene.raw,new Date().toISOString(),async(...args)=>transfers.push(args));
        else await signal(scene.event,scene.extra,scene.receivedAt);
      } catch(error) { refusal=error; }
      result.observed=state();
      assert.equal(result.observed,'unknown',scene.name+': malformed current hook must revoke positive state');
      if(!permission)assert.ok(refusal,scene.name+': malformed current hook must be rejected');
      const failure=store.read().slice(before).find(e=>e.type===(permission?'permission_wait':'native_question_unverified'));
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
      assert.equal(pane.active.id,'submission');assert.equal(codex?pane.turn:pane.claudePromptId,'prompt');
      assert.equal(pane.stopInProgress,false);assert.equal(pane.state,codex && permission?'unknown':'busy');
      await assert.rejects(signal('Stop',{stop_hook_active:false}),'Unsafe turn cannot complete even with a later valid Stop');
      assert.equal(pane.active.id,'submission');assert.equal(transfers.length,0);
      assert.equal(pane.stopInProgress,false);
      assert.equal(store.read().filter(e=>['pane_idle','pane_completion_held'].includes(e.type)).length,0);
      // A later unrelated tool cannot repair the lost question evidence.
      const unrelated=signal('PostToolUse',{tool_name:'Read',tool_input:{file_path:root+'/sentinel'},tool_response:'{'});
      if(codex && permission)await assert.rejects(unrelated);else await unrelated;
      assert.equal(state(),'unknown');
      result.status='PASS';
    } catch(error) {result.error=String(error);result.stack=error.stack;}
    finally {store.close();results.push(result);}
  }
  return results;
}
