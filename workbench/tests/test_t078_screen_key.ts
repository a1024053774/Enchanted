import assert from "node:assert/strict";
import { mkdtempSync,mkdirSync,writeFileSync } from "node:fs";
import { join } from "node:path";
import { OrchestrationStore } from "../src/store.ts";
const {Panes}=await import(process.argv[3] ?? new URL("../src/panes.ts",import.meta.url).href);
const out=process.argv[2];mkdirSync(out);
const root=mkdtempSync("/tmp/t078-2-screen-test-"),store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
const record:any={id:"screen-launch",thread:"screen-thread",task:"screen-task",attempt:null,session:"native",cli:"Claude Code",role:"controller",authentication:"isolated fake API only",worktree:join(root,"repo")};
store.launch(record);mkdirSync(join(root,"traces",record.id),{recursive:true});
const file=join(root,"traces",record.id,"pty.raw"),writes:string[]=[],screens:string[]=[];
const pane:any={record,state:"unknown",active:null,failed:null,stopped:false,archived:false,writing:false,queue:[],pendingInputs:0,userDraft:false,writes:Promise.resolve(),pty:{pid:1,write:(s:string)=>{assert.ok(store.read().some(e=>e.type==="controller_screen_key_intent"));writes.push(s);}}};
panes.panes.set(record.thread,pane);panes.processInfo=async()=>({leader:2,failed:null}) as any;
const setScreen=(s:string)=>{writeFileSync(file,s);screens.push(s);};
const input=(id:string,key:string,purpose="onboarding-theme",selected="Dark mode")=>({screen_id:id,key,purpose,selected_label:selected,screen_base64:Buffer.from(screens.at(-1)!).toString("base64"),authorization_ref:"controller-106-explicit"});
const checks:any[]=[];
async function test(name:string,fn:()=>Promise<void>){try{await fn();checks.push({name,status:"PASS"});}catch(e){checks.push({name,status:"INCOMPLETE",error:String(e)});}}
setScreen("Initial Dark cursor");
await test("default_enter_and_theme_digit_are_denied",async()=>{
  await assert.rejects((panes as any).screenKey(record.thread,input("initial","Enter"),"executor"),(e:any)=>e.code==="theme_selection_not_explicit");
  await assert.rejects((panes as any).screenKey(record.thread,input("initial","Digit2"),"executor"),(e:any)=>e.code==="invalid_screen_key");assert.deepEqual(writes,[]);
});
await test("explicit_navigation_then_dark_confirmation",async()=>{
  assert.equal(typeof (panes as any).screenKey,"function");
  await (panes as any).screenKey(record.thread,input("theme-dark","ArrowUp","onboarding-theme","Auto (match terminal)"),"executor");
  setScreen("Auto cursor after ArrowUp");
  await (panes as any).screenKey(record.thread,input("theme-auto","ArrowDown","onboarding-theme","Dark mode"),"executor");
  setScreen("Dark cursor after explicit ArrowDown");
  await (panes as any).screenKey(record.thread,input("theme-confirm","Enter"),"executor");
  assert.deepEqual(writes,["\x1b[A","\x1b[B","\r"]);assert.equal(pane.state,"unknown");
});
await test("same_snapshot_cannot_use_a_new_id",async()=>{
  await assert.rejects((panes as any).screenKey(record.thread,input("forged-new-id","ArrowUp"),"executor"),(e:any)=>e.code==="screen_key_already_used");
});
await test("workspace_trust_separate_once",async()=>{
  // New real screen and a fresh serialization lane; rejected operations remain closed.
  pane.writes=Promise.resolve();setScreen("Reviewed workspace trust screen");
  await (panes as any).screenKey(record.thread,input("trust-1","Digit1","workspace-trust","Yes, I trust this folder"),"executor");
  pane.writes=Promise.resolve();setScreen("Changed trust repaint");
  await assert.rejects((panes as any).screenKey(record.thread,input("trust-2","Digit1","workspace-trust","Yes, I trust this folder"),"executor"),(e:any)=>e.code==="workspace_trust_already_used");
});
const r={status:checks.every(c=>c.status==="PASS")?"PASS":"INCOMPLETE",checks,written:writes,argv:process.argv,scope:"Domain fixture only; no UI or actual trust/theme selection"};writeFileSync(join(out,"results.json"),JSON.stringify(r,null,2));store.close();console.log(JSON.stringify(r));process.exitCode=r.status==="PASS"?0:1;
