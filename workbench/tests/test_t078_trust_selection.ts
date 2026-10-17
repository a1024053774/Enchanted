import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { OrchestrationStore } from "../src/store.ts";
const {Panes}=await import(process.argv[4] ?? new URL("../src/panes.ts",import.meta.url).href);
const out=resolve(process.argv[2]),materials=resolve(process.argv[3]);mkdirSync(out);
const raw=readFileSync(join(materials,"screen-after-notice-01/screen.bin"));
const prior=JSON.parse(readFileSync(join(materials,"key-notice-01/result.json"),"utf8")).events.filter((e:any)=>["controller_screen_key_intent","controller_screen_key_written"].includes(e.type));
const yes="Yes, I trust this folder";
// Only the No/default frame is real. This redraw is a domain fixture, not a CLI observation.
const redraw=Buffer.from("\r\x1b[2K  No, exit\r\x1b[1B\x1b[2K❯ Yes, I trust this folder\r");
const selected=Buffer.concat([raw,redraw]);
const checks:any[]=[];
async function test(name:string,body:(f:any)=>Promise<void>){
  const root=mkdtempSync("/tmp/t078-2-trust-domain-"),store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
  const record:any={id:"trust-launch",thread:"trust-thread",task:"trust-task",attempt:null,session:"native",cli:"Claude Code",role:"controller",authentication:"isolated fake API only",worktree:join(root,"repo")};
  store.launch(record);mkdirSync(join(root,"traces",record.id),{recursive:true});
  // Replay the actual preceding theme/notice actions, bound to this domain fixture launch.
  for(const e of prior)store.event(e.type,e.data,record);
  const file=join(root,"traces",record.id,"pty.raw"),writes:string[]=[];
  const pane:any={record,state:"unknown",active:null,failed:null,stopped:false,archived:false,writing:false,queue:[],pendingInputs:0,userDraft:false,writes:Promise.resolve(),pty:{pid:1,write:(s:string)=>{
    assert.equal(store.read().at(-1)?.type,"controller_screen_key_intent");writes.push(s);
  }}};
  panes.panes.set(record.thread,pane);panes.processInfo=async()=>({leader:2,failed:null}) as any;
  const send=(id:string,key:string,bytes:Buffer,changes={},observed=bytes)=>{
    writeFileSync(file,observed);
    return panes.screenKey(record.thread,{screen_id:id,key,purpose:"workspace-trust",selected_label:yes,authorization_ref:"controller-113-explicit",screen_base64:bytes.toString("base64"),...changes},"executor");
  };
  try{await body({send,writes,store,pane});checks.push({name,status:"PASS",written:writes});}
  catch(error){checks.push({name,status:"INCOMPLETE",error:String(error),written:writes});}
  finally{store.close();}
}
await test("explicit_arrowdown_then_confirm_yes",async({send,writes,store})=>{
  await send("trust-select","ArrowDown",raw);await send("trust-confirm","Enter",selected);
  assert.deepEqual(writes,["\x1b[B","\r"]);
  const intents=store.read().filter(e=>e.type==="controller_screen_key_intent"&&e.data.purpose==="workspace-trust");
  assert.deepEqual(intents.map(e=>[e.data.key,e.data.selected_label]),[["ArrowDown",yes],["Enter",yes]]);
  assert.equal(intents[0].data.screen_base64,raw.toString("base64"));
});
await test("direct_default_enter_is_denied",async({send,writes})=>{
  await assert.rejects(send("default","Enter",raw),(e:any)=>e.code==="trust_selection_not_explicit");assert.deepEqual(writes,[]);
});
await test("digit1_is_denied_without_write",async({send,writes})=>{
  await assert.rejects(send("digit","Digit1",raw),(e:any)=>e.code==="invalid_screen_key");assert.deepEqual(writes,[]);
});
await test("two_trust_confirmations_are_denied",async({send,writes})=>{
  await send("select-1","ArrowDown",raw);await send("confirm-1","Enter",selected);
  const again=Buffer.concat([selected,Buffer.from("\rNo, exit\rYes, I trust this folder\r")]);
  await assert.rejects(async()=>{
    await send("select-2","ArrowDown",again);await send("confirm-2","Enter",Buffer.concat([again,redraw]));
  },(e:any)=>e.code==="workspace_trust_already_used");assert.deepEqual(writes,["\x1b[B","\r"]);
});
await test("wrong_navigation_target_is_denied",async({send,writes})=>{
  await assert.rejects(send("wrong-target","ArrowDown",raw,{selected_label:"No, exit"}),(e:any)=>e.code==="trust_selection_not_explicit");assert.deepEqual(writes,[]);
});
await test("intervening_other_purpose_cannot_authorize_trust",async({send,writes})=>{
  await send("trust-nav","ArrowDown",raw);
  await send("other","ArrowUp",selected,{purpose:"onboarding-theme",selected_label:"Auto (match terminal)"});
  await assert.rejects(send("confirm","Enter",Buffer.concat([selected,Buffer.from("\rFresh readback")])),(e:any)=>e.code==="trust_selection_not_explicit");assert.deepEqual(writes,["\x1b[B","\x1b[A"]);
});
await test("confirmation_must_continue_the_navigation_trace",async({send,writes})=>{
  await send("trust-nav","ArrowDown",raw);const changed=Buffer.from(selected);changed[0]=90;
  await assert.rejects(send("confirm","Enter",changed),(e:any)=>e.code==="trust_screen_not_continued");assert.deepEqual(writes,["\x1b[B"]);
});
await test("changed_approved_snapshot_is_denied",async({send,writes})=>{
  await send("trust-nav","ArrowDown",raw);
  await assert.rejects(send("confirm","Enter",selected,{},Buffer.concat([selected,Buffer.from("\x1b[0m")])),(e:any)=>e.code==="screen_changed");assert.deepEqual(writes,["\x1b[B"]);
});
await test("same_navigation_screen_with_new_id_is_denied",async({send,writes})=>{
  await send("trust-nav","ArrowDown",raw);
  await assert.rejects(send("trust-new-id","ArrowDown",raw),(e:any)=>e.code==="screen_key_already_used");assert.deepEqual(writes,["\x1b[B"]);
});
await test("normal_login_record_cannot_use_this_entry",async({send,writes,pane})=>{
  pane.record.authentication="normal user login";
  await assert.rejects(send("trust-nav","ArrowDown",raw),(e:any)=>e.code==="screen_operator_required");assert.deepEqual(writes,[]);
});
const result={status:checks.every(c=>c.status==="PASS")?"PASS":"INCOMPLETE",checks,materials,argv:process.argv,
  expected_source:"Controller 113 and immutable 08d default-No trust screen",
  scope:"Domain only; real captured initial bytes, synthetic Yes redraw, PTY and process identity; no CLI/API/UI/model started"};
writeFileSync(join(out,"results.json"),JSON.stringify(result,null,2));console.log(JSON.stringify(result));process.exitCode=result.status==="PASS"?0:1;
