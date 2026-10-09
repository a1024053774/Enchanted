// Independent permission contract: same valid delivery, reviewer refused, current worker accepted.
// Real tool handler/Git/SQLite; active native caller frames are controlled, not a signed Gateway test.
import assert from "node:assert/strict";
import {execFileSync} from "node:child_process";
import {mkdirSync,mkdtempSync,writeFileSync} from "node:fs";
import {join} from "node:path";
import {A2AGates,type GateRuntime} from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts";
import {a2aSubmitTool} from "/Users/luckye/Documents/Code/synara/apps/server/src/a2a/tools.ts";
import {Effect} from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/node_modules/effect/dist/index.js";
const root=mkdtempSync('/Volumes/WD-Elements/dev-cache/synara/instances/t044/fixtures/permission-');
const repo=join(root,'repo');mkdirSync(repo);
const git=(...args:string[])=>execFileSync('git',['-C',repo,...args],{encoding:'utf8',env:{...process.env,GIT_CONFIG_GLOBAL:'/dev/null',GIT_CONFIG_NOSYSTEM:'1'}}).trim();
git('init');git('config','user.name','T-044 permissions');git('config','user.email','t044@example.invalid');git('config','commit.gpgsign','false');
writeFileSync(join(repo,'input.txt'),'Independent permission input\n');git('add','input.txt');git('-c','core.hooksPath=/dev/null','commit','-m','Fixture');
const base=git('rev-parse','HEAD');writeFileSync(join(root,'instructions.txt'),'Caller permission fixture, no model calls.\n');writeFileSync(join(root,'oracle.py'),'raise SystemExit(0)\n');
const threads=new Map<string,any>();
const runtime:GateRuntime={ensureProject:async()=>{},createThread:async(_task,a)=>{threads.set(a.thread_id,{workspace:a.workspace,provider:'codex',turn:'active-worker-turn',running:true,stopped:false,archived:false,blocked:false});},
 startThread:async()=>{},createAttachedThread:async(task,a)=>{threads.set(a.thread_id,{workspace:task.repo,provider:'codex',turn:'active-reviewer-turn',running:true,stopped:false,archived:false,blocked:false});},
 readThread:async thread=>({...threads.get(thread)}),stopThread:async()=>{},archiveThread:async()=>{}};
const gates=new A2AGates(join(root,'state'),runtime);const task='permissions';
console.log(JSON.stringify({fixture_root:root,caller_boundary:'controlled active native frames'}));
try{
 assert.equal((await gates.call({command:'create',task,project:'permission-project',repo,base,oracle:join(root,'oracle.py'),instructions:join(root,'instructions.txt')})).ok,true);
 const dispatched=await gates.call({command:'dispatch',task,runtimeMode:'approval-required'});assert.equal(dispatched.ok,true);
 const a=dispatched.attempt!;const attached=await gates.call({command:'attach',task,role:'reviewer',modelSelection:{provider:'codex',model:'gpt-6.1-sol'},runtimeMode:'approval-required',instructions:join(root,'instructions.txt')});assert.equal(attached.ok,true);
 assert.deepEqual(attached.task,dispatched.task,'Ordinary attach cannot replace a delivery attempt');
 const before=(await gates.call({command:'status',task})).task;
 const args={task,attempt:a.attempt_id,session:a.session_id,fence:a.fence,spec_rev:a.spec_rev,commit:base};
 const context=(thread:string,turn:string)=>({callerThreadId:thread,callerTurnId:turn,assertCallerTurnActive:()=>Effect.void} as any);
 const reviewer=attached.attachment!.thread_id;
 const denied=await Effect.runPromise(a2aSubmitTool(gates).handler(args,context(reviewer,'active-reviewer-turn')));
 const deniedBody=JSON.parse((denied.content[0] as any).text);assert.equal(denied.isError,true);assert.equal(deniedBody.error,'stale_thread');assert.deepEqual((await gates.call({command:'status',task})).task,before);
 const accepted=await Effect.runPromise(a2aSubmitTool(gates).handler(args,context(a.thread_id,'active-worker-turn')));
 const acceptedBody=JSON.parse((accepted.content[0] as any).text);assert.equal(acceptedBody.ok,true);assert.equal(acceptedBody.task.state,'submitted');
 const submitted=(await gates.call({command:'status',task})).task;
 const caller={thread:reviewer,turn:'active-reviewer-turn',assertActive:async()=>{}};
 const refusals=[];
 for(const request of [{command:'revoke',task,reason:'unauthorized'},{command:'revise',task,spec_rev:2},{command:'verify',task,attempt:a.attempt_id},
  {command:'integrate',task,attempt:a.attempt_id},{command:'reclaim',task,attempt:a.attempt_id},{command:'run',task,runtimeMode:'approval-required',wait_seconds:2}]){
  const result=await gates.call(request,caller);assert.equal(result.error,'stale_thread');assert.deepEqual((await gates.call({command:'status',task})).task,submitted);refusals.push({request,result});
 }
 console.log(JSON.stringify({args,reviewer,worker:a.thread_id,denied:deniedBody,positive_control:acceptedBody,refusals,status:'PASS'}));
}finally{gates.close();}
