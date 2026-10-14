import assert from "node:assert/strict";
import {mkdtempSync,mkdirSync,readFileSync,writeFileSync} from "node:fs";
import {join} from "node:path";
import {OrchestrationStore} from "../src/store.ts";
const {Panes}=await import(process.argv[4]??new URL("../src/panes.ts",import.meta.url).href);
const out=process.argv[2];mkdirSync(out);
const ups=JSON.parse(readFileSync(join(process.argv[3],"UserPromptSubmit.stdin.bin"),"utf8"));
const stop=JSON.parse(readFileSync(join(process.argv[3],"Stop.stdin.bin"),"utf8"));
assert.equal(ups.prompt_id,stop.prompt_id);
const checks:any[]=[];
async function test(name:string,body:(f:any)=>Promise<void>,limit=2){
  const root=mkdtempSync("/tmp/t078-epochs-"),store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
  const record:any={id:"epoch-launch",thread:"epoch-thread",task:"epoch-task",attempt:null,role:"controller",session:ups.session_id,cli:"Claude Code",turn_limit:limit};
  store.launch(record);const first=store.register(record.id,ups.prompt.slice("⟦主控 #1⟧\n".length));assert.equal(first.text,ups.prompt);
  const active={id:"submission-1",dispatch:first.id,at:"2026-10-13T00:00:00Z",nativeTurn:null};store.event("turn_submit_intent",active,record);
  const writes:string[]=[];
  const pane:any={record,native:ups.session_id,task:{},attempt:null,state:"busy",failed:null,stopped:false,archived:false,interrupted:false,stopInProgress:false,
    active,claudePromptId:null,claudePromptIds:new Set(),queue:[],writing:false,writes:Promise.resolve(),pendingInputs:0,userDraft:false,pty:{pid:1,write:(v:string)=>writes.push(v)}};
  panes.panes.set(record.thread,pane);panes.processInfo=async()=>({leader:2,failed:null}) as any;
  const signal=(v:any,transfer?:any)=>panes.signal(record.id,JSON.stringify(v),new Date().toISOString(),transfer);
  try{await body({panes,pane,store,signal,writes,record});checks.push({name,status:"PASS",written:writes});}
  catch(e){checks.push({name,status:"INCOMPLETE",error:String(e),written:writes});}
  finally{store.close();}
}
await test("observed_prompt_id_binds_submission",async({signal,pane})=>{await signal(ups);assert.equal(pane.claudePromptId,ups.prompt_id);});
await test("esc_retires_active_without_waiting_for_stop",async({signal,panes,pane,writes})=>{
  await signal(ups);await panes.userInput(pane.record.id,"\x1b",{request_id:"esc"},async()=>{},async()=>{});
  assert.equal(pane.active,null);assert.equal(pane.claudePromptId,null);assert.equal(pane.interrupted,true);assert.equal(pane.state,"busy");assert.deepEqual(writes,["\x1b"]);
},1);
await test("user_release_delivers_second_nonce_with_new_prompt_id",async({signal,panes,pane,store,writes})=>{
  await signal(ups);const second=await panes.dispatch(pane,"09A_SECOND_NONCE");assert.equal(writes.length,0);
  await panes.userInput(pane.record.id,"\x1b",{request_id:"esc"},async()=>{},async()=>{});
  assert.equal(pane.queue.length,1);await panes.releaseByUser(pane.record.thread,"explicit user release",async()=>{},async()=>{});
  const id="00000000-0000-4000-8000-000000000002";await signal({...ups,prompt:second.text,prompt_id:id});
  const current=pane.active;assert.ok(current);assert.equal(pane.claudePromptId,id);
  await signal(stop);assert.equal(pane.active,current);assert.equal(pane.state,"busy");
  await signal({...stop,prompt_id:id,last_assistant_message:"09A_ACK_2"});assert.equal(pane.active,null);assert.equal(pane.state,"idle");
  assert.equal(store.read().filter(e=>e.type==="pane_idle").length,1);
  assert.deepEqual(writes,["\x1b","\x1b[200~"+second.text+"\x1b[201~","\r"]);
});
await test("old_stop_cannot_finish_current_prompt",async({signal,pane,store})=>{
  pane.claudePromptId="00000000-0000-4000-8000-000000000002";const current=pane.active;
  await signal(stop);assert.equal(pane.active,current);assert.equal(pane.state,"busy");assert.equal(store.read().filter(e=>e.type==="pane_idle").length,0);
},1);
await test("missing_prompt_id_cannot_bind_submission",async({signal})=>{
  const value={...ups};delete value.prompt_id;await assert.rejects(signal(value),(e:any)=>e.code==="claude_prompt_id_required");
});
await test("reused_prompt_id_cannot_bind_second_submission",async({signal,pane})=>{
  pane.claudePromptIds.add(ups.prompt_id);await assert.rejects(signal(ups),(e:any)=>e.code==="claude_prompt_id_reused");
});
await test("stop_transfer_cannot_clear_a_replacement_submission",async({signal,panes,pane})=>{
  await signal(ups);let started!:()=>void,release!:()=>void;
  const begun=new Promise<void>(r=>started=r),barrier=new Promise<void>(r=>release=r);
  const finishing=signal(stop,async()=>{started();await barrier;});await begun;
  await panes.userInput(pane.record.id,"\x1b",{request_id:"esc"},async()=>{},async()=>{});
  const second=await panes.dispatch(pane,"09A_REPLACEMENT_NONCE");await panes.releaseByUser(pane.record.thread,"explicit release",async()=>{},async()=>{});
  const id="00000000-0000-4000-8000-000000000002";await signal({...ups,prompt:second.text,prompt_id:id});const active=pane.active;
  release();await finishing;assert.equal(pane.active,active);assert.equal(pane.claudePromptId,id);
});
const result={status:checks.every(c=>c.status==="PASS")?"PASS":"INCOMPLETE",checks,argv:process.argv,
  expected_source:"Controller 116, 08e actual hook payloads and PLAN-09; second ID/redraw/PTY are synthetic",
  scope:"Domain only, no CLI/API/socket/UI/model"};writeFileSync(join(out,"results.json"),JSON.stringify(result,null,2));console.log(JSON.stringify(result));process.exitCode=result.status==="PASS"?0:1;
