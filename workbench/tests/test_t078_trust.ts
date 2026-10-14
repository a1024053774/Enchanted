import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { OrchestrationStore } from "../src/store.ts";
const {Panes}=await import(process.argv[3] ?? new URL("../src/panes.ts",import.meta.url).href);
const output=process.argv[2];mkdirSync(output);
const root=mkdtempSync("/tmp/t078-2-trust-");const store=new OrchestrationStore(root),panes=new Panes(root,store,{},()=>{});
const record:any={id:"trust-launch",thread:"trust-thread",task:"trust-task",attempt:null,session:"native",cli:"Claude Code",role:"controller",worktree:join(root,"repo")};
store.launch(record);mkdirSync(join(root,"traces",record.id),{recursive:true});const screen=Buffer.from("Exact reviewed trust screen\r\n");writeFileSync(join(root,"traces",record.id,"pty.raw"),screen);
const writes:string[]=[];const pane:any={record,pty:{pid:1,write:(s:string)=>writes.push(s)},state:"unknown",active:null,failed:null,stopped:false,archived:false,writing:false,queue:[],pendingInputs:0,userDraft:false,interrupted:false,writes:Promise.resolve()};
panes.panes.set(record.thread,pane);panes.processInfo=async()=>({leader:2,failed:null}) as any;
const checks:any[]=[];
async function check(name:string,fn:()=>Promise<void>){try{await fn();checks.push({name,status:"PASS"});}catch(e){checks.push({name,status:"INCOMPLETE",error:String(e)});}}
await check("enter_and_wrong_actor_are_rejected",async()=>{
  await assert.rejects((panes as any).trustKey(record.thread,"Enter",screen.toString("base64"),"answer:20261014T011751Z","executor"),(e:any)=>e.code==="invalid_trust_key");
  await assert.rejects((panes as any).trustKey(record.thread,"Digit1",screen.toString("base64"),"answer:20261014T011751Z","worker:spoof"),(e:any)=>e.code==="trust_operator_required");assert.deepEqual(writes,[]);
});
await check("reviewed_digit1_is_registered_before_write",async()=>{
  assert.equal(typeof (panes as any).trustKey,"function");
  await (panes as any).trustKey(record.thread,"Digit1",screen.toString("base64"),"answer:20261014T011751Z","executor");
  assert.deepEqual(writes,["1"]);assert.equal(pane.state,"unknown");assert.equal(pane.active,null);
  const e=store.read().find(e=>e.type==="controller_trust_key_intent");assert.equal(e?.data.source,"executor");assert.equal(e?.data.directory,record.worktree);
});
await check("second_trust_key_is_rejected",async()=>{
  await assert.rejects((panes as any).trustKey(record.thread,"Digit1",screen.toString("base64"),"answer:20261014T011751Z","executor"),(e:any)=>e.code==="trust_key_already_used");assert.deepEqual(writes,["1"]);
});
await check("stale_screen_is_rejected",async()=>{
  const stale={...record,id:"stale-launch",thread:"stale-thread"};store.launch(stale);
  mkdirSync(join(root,"traces",stale.id),{recursive:true});writeFileSync(join(root,"traces",stale.id,"pty.raw"),screen);
  panes.panes.set(stale.thread,{...pane,record:stale,writes:Promise.resolve()} as any);
  await assert.rejects((panes as any).trustKey(stale.thread,"Digit1",Buffer.from("stale").toString("base64"),"answer:20261014T011751Z","executor"),(e:any)=>e.code==="trust_screen_changed");assert.deepEqual(writes,["1"]);
});
const r={status:checks.every(c=>c.status==="PASS")?"PASS":"INCOMPLETE",checks,written:writes,argv:process.argv,scope:"Domain fixture; no PTY, process or actual trust UI"};writeFileSync(join(output,"results.json"),JSON.stringify(r,null,2));store.close();console.log(JSON.stringify(r));process.exitCode=r.status==="PASS"?0:1;
