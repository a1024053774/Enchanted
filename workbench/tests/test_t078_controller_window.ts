import assert from "node:assert/strict";
import {readFileSync,mkdirSync,writeFileSync} from "node:fs";
import {join} from "node:path";
import {Refusal} from "../src/gates/core.ts";
const out=process.argv[2];mkdirSync(out);
// Exercise the exact production closure without starting serve()/Unix sockets.
const source=readFileSync(process.argv[3]??new URL("../src/daemon.ts",import.meta.url),"utf8");
const marker="      const assertCurrent = async () => {",end="\n      };\n      const recordInput";
assert.equal(source.split(marker).length,2);const start=source.indexOf(marker)+marker.length;const finish=source.indexOf(end,start);assert.ok(finish>start);
const create=new Function("windows","window","gates","record","panes","Refusal","return async()=>{"+source.slice(start,finish)+"}");
const record:any={id:"controller-launch",thread:"controller-thread",task:"task",attempt:null,role:"controller",cli:"Claude Code",session:"native",spec_rev:1};
const window={id:"window",launch:record.id},windows=new Map([[window.id,window]]);
const pane:any={record,native:"native",failed:null,stopped:false,archived:false};let leader:number|null=2;
let task:any={task_id:"task",spec_rev:1,current_attempt:null};
const gates={call:async()=>({task}),userInputObserverStatus:()=>({state:"healthy"})};
const panes={get:()=>pane,processInfo:async()=>({leader,failed:pane.failed})};
const check=create(windows,window,gates,record,panes,Refusal);const checks:any[]=[];
async function test(name:string,f:()=>Promise<void>){try{await f();checks.push({name,status:"PASS"});}catch(e){checks.push({name,status:"INCOMPLETE",error:String(e)});}}
await test("live_nullable_controller_window_is_allowed",async()=>await check());
await test("controller_identity_change_is_denied",async()=>{leader=null;await assert.rejects(check());leader=2;});
await test("controller_spec_change_is_denied",async()=>{task.spec_rev=2;await assert.rejects(check());task.spec_rev=1;});
await test("window_revocation_is_denied",async()=>{windows.clear();await assert.rejects(check(),(e:any)=>e.code==="invalid_window_identity");windows.set(window.id,window);});
await test("worker_stale_attempt_is_still_denied",async()=>{
  record.role="worker";record.attempt="a1";record.fence=1;task.current_attempt={attempt_id:"a2",session_id:"native",fence:1,reclaimed:false};
  await assert.rejects(check(),(e:any)=>e.code==="stale_attempt");
});
const result={status:checks.every(c=>c.status==="PASS")?"PASS":"INCOMPLETE",checks,argv:process.argv,
  scope:"Exact window verifier closure with simulated status/liveness; credentials, sockets and UI not exercised"};
writeFileSync(join(out,"results.json"),JSON.stringify(result,null,2));console.log(JSON.stringify(result));process.exitCode=result.status==="PASS"?0:1;
