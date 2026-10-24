// Failure modes, before implementation: Enter retires the still-current turn;
// input is swallowed, rewritten, or delayed until Stop finishes; a genuine new
// native prompt is ignored; an old caller survives that prompt; an old Stop or
// duplicate old UPS clears/poisons the new turn; submit refusal facts are lost.
// Claude's busy-input UPS reuses the current prompt id, then its queued human
// transcript has a fresh id: rejecting the UPS poisons the original Stop;
// failing to bind the real dequeued turn leaves its final Stop unmatched.
// Wrong text/session/root/time or a tool result must not establish that turn.
// Oracle: controller #61 relays user ruling 20261024T030734Z-001.
// This host controls the async boundary; it does not prove real CLI/PTY timing.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [source, out] = process.argv.slice(2);
const { Panes } = await import(pathToFileURL(join(source, 'workbench/src/panes.ts')).href);
const { OrchestrationStore } = await import(pathToFileURL(join(source, 'workbench/src/store.ts')).href);
const { RequestRelay } = await import(pathToFileURL(join(source, 'workbench/src/relay.ts')).href);
const checks: any[] = [];
for (const scenario of ['input-during-stop', 'native-new-turn', 'idle-manual-prompt', 'native-queued-input']) {
  const root = join(out, scenario); mkdirSync(root);
  const store = new OrchestrationStore(root), panes = new Panes(root, store, {}, () => {}), relay = new RequestRelay(store);
  const record = { id: scenario, thread: scenario, task: 'demo+T-157', role: 'worker', cli: 'Claude Code',
    worktree: root, attempt: 'a1', session: 's1', fence: 1, spec_rev: 1, turn_limit: 6, env: {} };
  store.launch(record);
  const original = { id: 'submission-1', dispatch: 'input:first', nativeTurn: null, at: '2026-10-24T00:00:00Z' };
  const bytes: string[] = [];
  const pane: any = { record, attempt: { thread_id: scenario, workspace: root }, task: {}, token: 'test-token',
    native: 'native-session', state: 'busy', failed: null, stopped: false, archived: false, nativeEnded: false,
    interrupted: false, active: original, turn: null, claudePromptId: 'prompt-1', claudePromptIds: new Set(['prompt-1']),
    stopInProgress: false, writing: false, queue: [], writes: Promise.resolve(), pendingInputs: 0, inputGeneration: 0,
    pty: { pid: 101, write: (data: string) => bytes.push(data) } };
  panes.panes.set(record.thread, pane);
  writeFileSync(join(root, 'native-session.jsonl'), JSON.stringify({type:'assistant',message:{model:'host-only'}})+'\n');
  const envelope = (name: string, prompt: string) => ({hook_event_name:name,session_id:pane.native,prompt_id:prompt,
    cwd:root,transcript_path:join(root,'native-session.jsonl'),stop_hook_active:false,effort:{level:'low'},prompt:'下一轮说明'});
  let finishObserver=()=>{}, stopping:Promise<unknown>|undefined, pendingWrite:Promise<unknown>|undefined;
  try {
    if (scenario === 'idle-manual-prompt') {
      pane.active = null; pane.claudePromptId = null; pane.state = 'idle';
      await panes.signal(record.id, JSON.stringify(envelope('UserPromptSubmit','prompt-2')), '2026-10-24T00:02:00Z');
      assert.equal(pane.claudePromptId, 'prompt-2');
      assert.ok(pane.active, 'a native manual prompt must establish a submission');
      checks.push({name:scenario,status:'PASS'});
      continue;
    }
    let enterProcess!: () => void, finishProcess!: () => void;
    const entered = new Promise<void>(resolve => {enterProcess=resolve;});
    const finished = new Promise<void>(resolve => {finishProcess=resolve;});
    finishObserver=finishProcess;
    panes.processInfo = async () => {enterProcess();await finished;return {leader:102,failed:pane.failed};};
    const input = {schema:1,request_id:'original-submit',command:'submit',task:record.task,attempt:'a1',
      session:'s1',fence:1,spec_rev:1,commit:'1'.repeat(40)};
    let receipt: any;
    const stop = panes.signal(record.id, JSON.stringify(envelope('Stop','prompt-1')), '2026-10-24T00:01:00Z',
      async (_pane: any, value: any, matched: boolean) => {
        assert.equal(matched,true);
        receipt = await relay.receive(record as any,{name:'original-submit.json',raw:JSON.stringify(input)},matched,async()=>{
          const caller = await panes.caller({launch:record.id,token:pane.token,native_session:pane.native,prompt_id:value.prompt_id});
          await caller.assertActive();
          return {ok:true};
        });
      });
    stopping=stop;
    await entered;
    const note='输入原样 / sentinel-157\r';
    let recorded='';
    const writing=panes.userInput(record.id,note,{request_id:'manual-note'},async(text:string)=>{recorded=text;},async()=>{});
    pendingWrite=writing;
    // Input must complete while the Stop's identity observation is still held.
    await Promise.race([writing,new Promise((_,reject)=>setTimeout(()=>reject(new Error('input deferred behind Stop')),500))]);
    assert.deepEqual(bytes,[note]);
    assert.equal(recorded,note);
    assert.equal(pane.active,original,'Enter alone is not a native turn transition');
    assert.equal(pane.claudePromptId,'prompt-1');
    if (scenario === 'native-queued-input') {
      // Use a real file at the native session locator, but control the hook and
      // observer boundary. The external Electron run proves CLI provenance.
      const projects=join(root,'projects');mkdirSync(projects);
      record.env={CLAUDE_CONFIG_DIR:root};
      const file=join(projects,'native-session.jsonl');
      writeFileSync(file,JSON.stringify({type:'user',sessionId:pane.native,cwd:root,promptId:'prompt-1',
        timestamp:'2026-10-24T00:00:00Z',message:{role:'user',content:'original'}})+'\n');
      const queued={...envelope('UserPromptSubmit','prompt-1'),transcript_path:file,prompt:note.slice(0,-1)};
      await panes.signal(record.id,JSON.stringify(queued),'2026-10-24T00:01:01Z');
      assert.equal(pane.active,original,'queued UPS must not replace original Stop identity');
      assert.equal(pane.claudePromptId,'prompt-1');
      const oldCaller=await panes.caller({launch:record.id,token:pane.token,native_session:pane.native,prompt_id:'prompt-1'});
      finishProcess();await stop;
      assert.equal(receipt.result.ok,true,'original Stop remains trusted after queued UPS');
      assert.equal(pane.failed,null);
      assert.equal(pane.state,'busy','native queued input has not completed');
      assert.equal(pane.active,null);
      const actual={type:'user',isSidechain:false,sessionId:pane.native,cwd:root,promptId:'prompt-2',
        timestamp:'2026-10-24T00:01:02Z',uuid:'native-user-2',promptSource:'queued',turnOrigin:'human',origin:{kind:'human'},
        message:{role:'user',content:note.slice(0,-1)}};
      for(const wrong of [
        {...actual,isSidechain:true}, {...actual,sessionId:'foreign'}, {...actual,cwd:'/elsewhere'},
        {...actual,timestamp:'2026-10-24T00:00:00Z'}, {...actual,promptId:'prompt-1'},
        {...actual,message:{role:'user',content:'different'}},
        {...actual,message:{role:'user',content:[{type:'tool_result',content:note.slice(0,-1)}]}},
      ]) {
        writeFileSync(file,JSON.stringify(wrong)+'\n');panes.scan(pane);
        assert.equal(pane.claudePromptId,null,'unverified transcript must not establish native turn');
        assert.equal(pane.active,null);
      }
      writeFileSync(file,JSON.stringify(actual)+'\n');panes.scan(pane);
      assert.equal(pane.claudePromptId,'prompt-2');
      assert.ok(pane.active,'native dequeued human prompt establishes actual turn');
      await assert.rejects(oldCaller.assertActive(),'old caller cannot survive an actual queued native turn');
      const caller=await panes.caller({launch:record.id,token:pane.token,native_session:pane.native,prompt_id:'prompt-2'});
      await caller.assertActive();
      await assert.rejects(panes.caller({launch:record.id,token:pane.token,native_session:pane.native,prompt_id:'prompt-1'}));
      await panes.signal(record.id,JSON.stringify({...envelope('Stop','prompt-2'),transcript_path:file}),
        '2026-10-24T00:01:03Z',async(_p:any,_v:any,matched:boolean)=>assert.equal(matched,true));
      assert.equal(pane.state,'idle','the intervention turn Stop must restore idle');
      assert.equal(pane.active,null);assert.equal(pane.failed,null);
      checks.push({name:scenario,status:'PASS',receipt:receipt.result,bytes});continue;
    }
    if (scenario === 'native-new-turn') {
      await panes.signal(record.id,JSON.stringify(envelope('UserPromptSubmit','prompt-2')),'2026-10-24T00:01:01Z');
      assert.equal(pane.claudePromptId,'prompt-2','real native UPS must replace the old turn');
      assert.notEqual(pane.active,original);
    }
    finishProcess();
    await stop;
    if (scenario === 'input-during-stop') {
      assert.equal(receipt.result.ok,true);
      assert.equal(pane.active,null);
      assert.equal(pane.state,'idle');
    } else {
      assert.equal(receipt.result.error,'worker_not_active','old caller cannot survive a native new turn');
      assert.equal(pane.claudePromptId,'prompt-2','old Stop must not clear the new turn');
      const fact=panes.status(record.thread).delivery;
      assert.equal(fact?.state,'rejected');
      assert.equal(fact?.reason,'worker_not_active');
      assert.equal(fact?.attempt,'a1');
      assert.equal(fact?.native_turn_changed,true,'the refusal must carry evidence of a genuine prompt transition');
      const active=pane.active;
      let stale:any;
      await panes.signal(record.id,JSON.stringify(envelope('Stop','prompt-1')),'2026-10-24T00:01:02Z',
        async(_p:any,_v:any,matched:boolean)=>{
          assert.equal(matched,false);
          stale=await relay.receive(record as any,{name:'late.json',raw:JSON.stringify({...input,request_id:'late-submit'})},matched,
            async()=>{throw new Error('stale Stop must never execute a gate operation');});
        });
      assert.equal(stale?.result.error,'relay_requires_current_stop');
      const refused=panes.status(record.thread).delivery;
      assert.equal(refused?.native_turn_changed,true);
      assert.equal(refused?.request_id,'late-submit');
      assert.equal(refused?.state,'rejected');
      await assert.rejects(panes.signal(record.id,JSON.stringify(envelope('UserPromptSubmit','prompt-1')),'2026-10-24T00:01:03Z'));
      assert.equal(pane.active,active);
      assert.equal(pane.failed,null);
    }
    checks.push({name:scenario,status:'PASS',receipt:receipt.result,bytes});
  } catch(error) {checks.push({name:scenario,status:'INCOMPLETE',error:String(error),bytes});}
  finally {
    finishObserver();
    await Promise.allSettled([stopping,pendingWrite]);
    writeFileSync(join(root,'events.json'),JSON.stringify(store.read(),null,2)+'\n');store.close();
  }
}
const report={status:checks.every(c=>c.status==='PASS')?'PASS':'INCOMPLETE',checks,
  scope:'controlled native-hook/identity state; no real CLI, PTY, process observer or gate submit'};
writeFileSync(join(out,'results.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(report));
process.exitCode=report.status==='PASS'?0:1;
