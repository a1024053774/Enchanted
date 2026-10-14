import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { OrchestrationStore } from "../src/store.ts";
const { Panes } = await import(process.argv[4] ?? new URL("../src/panes.ts", import.meta.url).href);
const out=resolve(process.argv[2]),materials=resolve(process.argv[3]);mkdirSync(out);
// Independent oracle: executor 111/112 approved only this captured Security notes text.
const raw=readFileSync(join(materials,"screen-after-theme-01/screen.bin"));
const approvals=[1,2,3].map(n=>JSON.parse(readFileSync(join(materials,"approvals",`theme-0${n}.json`),"utf8")));
const screens=[1,2,3].map(n=>readFileSync(join(materials,`screen-theme-0${n}/screen.bin`)));
const changed=Buffer.from(raw.toString("utf8").replace("mistakes","mistaxes"));
assert.notDeepEqual(changed,raw);
const checks:any[]=[];
async function test(name:string,fn:(f:any)=>Promise<void>,withTheme=true){
  const root=mkdtempSync("/tmp/t078-2-notice-domain-"),store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
  const record:any={id:"notice-launch",thread:"notice-thread",task:"notice-task",attempt:null,session:"native",cli:"Claude Code",role:"controller",authentication:"isolated fake API only",worktree:join(root,"repo")};
  store.launch(record);mkdirSync(join(root,"traces",record.id),{recursive:true});
  const file=join(root,"traces",record.id,"pty.raw"),writes:string[]=[];
  const pane:any={record,state:"unknown",active:null,failed:null,stopped:false,archived:false,writing:false,queue:[],pendingInputs:0,userDraft:false,writes:Promise.resolve(),pty:{pid:1,write:(s:string)=>writes.push(s)}};
  panes.panes.set(record.thread,pane);panes.processInfo=async()=>({leader:2,failed:null}) as any;
  const send=(bytes:Buffer=raw,changes={},observed=bytes)=>{
    writeFileSync(file,observed);
    return panes.screenKey(record.thread,{screen_id:"notice-01",purpose:"onboarding-notice",key:"Enter",selected_label:"Continue",authorization_ref:"controller-112-explicit",screen_base64:bytes.toString("base64"),...changes},"executor");
  };
  try{
    if(withTheme)for(let n=0;n<3;n++){
      const a=approvals[n];writeFileSync(file,screens[n]);
      await panes.screenKey(record.thread,{screen_id:a.screen_id,purpose:a.purpose,key:a.key,selected_label:a.selected_label,authorization_ref:a.approval_ref,screen_base64:screens[n].toString("base64")},"executor");
    }
    await fn({send,writes,pane,store});checks.push({name,status:"PASS",written:writes});
  }catch(error){checks.push({name,status:"INCOMPLETE",error:String(error),written:writes});}
  finally{store.close();}
}
await test("captured_notice_enter_is_recorded_and_written",async({send,writes,store})=>{
  await send();assert.deepEqual(writes,["\x1b[A","\x1b[B","\r","\r"]);
  const intent=store.read().find(e=>e.type==="controller_screen_key_intent"&&e.data.purpose==="onboarding-notice")!;
  assert.equal(intent.data.screen_base64,raw.toString("base64"));assert.equal(intent.data.key,"Enter");
  assert.equal(intent.data.authorization_ref,"controller-112-explicit");assert.equal(intent.data.source,"executor");
});
await test("different_notice_letter_is_denied",async({send,writes})=>{
  await assert.rejects(send(changed),(e:any)=>e.code==="notice_text_mismatch");assert.equal(writes.length,3);
});
await test("additional_prompt_is_denied",async({send,writes})=>{
  await assert.rejects(send(Buffer.concat([raw,Buffer.from("\rAnother approval is required")])),(e:any)=>e.code==="notice_text_mismatch");assert.equal(writes.length,3);
});
await test("printable_whitespace_change_is_denied",async({send,writes})=>{
  await assert.rejects(send(Buffer.from(raw.toString("utf8").replace("Claude can","Claude  can"))),(e:any)=>e.code==="notice_text_mismatch");assert.equal(writes.length,3);
});
await test("incomplete_control_sequence_is_denied",async({send,writes})=>{
  await assert.rejects(send(Buffer.concat([raw,Buffer.from("\x1b[")])),(e:any)=>e.code==="notice_text_mismatch");assert.equal(writes.length,3);
});
await test("color_only_change_preserves_notice_text",async({send,writes})=>{
  await send(Buffer.concat([raw,Buffer.from("\x1b[32m\x1b[0m")]));assert.equal(writes.at(-1),"\r");assert.equal(writes.length,4);
});
await test("notice_direction_key_is_denied",async({send,writes})=>{
  await assert.rejects(send(raw,{key:"ArrowDown"}),(e:any)=>e.code==="invalid_screen_key");assert.equal(writes.length,3);
});
await test("same_screen_new_id_is_denied",async({send,writes})=>{
  await send();await assert.rejects(send(raw,{screen_id:"notice-02"}),(e:any)=>e.code==="screen_key_already_used");assert.equal(writes.length,4);
});
await test("notice_repaint_cannot_be_confirmed_twice",async({send,writes})=>{
  await send();await assert.rejects(send(Buffer.concat([raw,Buffer.from("\x1b[0m")]),{screen_id:"notice-02"}),(e:any)=>e.code==="onboarding_notice_already_used");assert.equal(writes.length,4);
});
await test("raw_snapshot_change_is_denied",async({send,writes})=>{
  await assert.rejects(send(raw,{},Buffer.concat([raw,Buffer.from("\x1b[0m")])),(e:any)=>e.code==="screen_changed");assert.equal(writes.length,3);
});
await test("real_login_record_is_denied",async({send,writes,pane})=>{
  pane.record.authentication="normal user login";
  await assert.rejects(send(),(e:any)=>e.code==="screen_operator_required");assert.equal(writes.length,3);
});
await test("notice_without_theme_confirmation_is_denied",async({send,writes})=>{
  await assert.rejects(send(),(e:any)=>e.code==="notice_requires_theme_confirmation");assert.deepEqual(writes,[]);
},false);
const result={status:checks.every(c=>c.status==="PASS")?"PASS":"INCOMPLETE",checks,materials,argv:process.argv,
  expected_source:"Controller 111/112; immutable 08c captured notice and actual theme approvals",
  scope:"Domain only; synthetic PTY/process identity; no CLI/API/UI/model starts"};
writeFileSync(join(out,"results.json"),JSON.stringify(result,null,2));console.log(JSON.stringify(result));process.exitCode=result.status==="PASS"?0:1;
