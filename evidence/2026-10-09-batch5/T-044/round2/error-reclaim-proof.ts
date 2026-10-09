// Contract from controller-decision-01: inactive error is reclaimable; active/interactive/foreign error is not.
// Failure modes: reject the inactive positive; close a present provider, live turn or pending interaction;
// accept a foreign workspace/provider/turn; let an error observation verify, integrate or report run success.
// Real CLI/Git/SQLite and production native decoder; only native session facts are controlled, no model calls.
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const { main } = await import(process.env.T044_CLI_ENTRY ?? "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/cli.ts");
import { readManagedThread } from "/Users/luckye/Documents/Code/synara/apps/server/src/a2a/orchestration.ts";
import type { GateRuntime } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts";
const root = mkdtempSync("/Volumes/WD-Elements/dev-cache/synara/instances/t044/fixtures/error-contract-");
const repo = join(root,"repo"), state=join(root,"state"); mkdirSync(repo);
const git=(...args:string[])=>execFileSync("git",["-C",repo,...args],{encoding:"utf8",env:{...process.env,
 GIT_CONFIG_NOSYSTEM:"1",GIT_CONFIG_GLOBAL:"/dev/null",GIT_TERMINAL_PROMPT:"0"}}).trim();
git("init");git("config","user.name","T-044 error contract");git("config","user.email","t044@example.invalid");
git("config","commit.gpgsign","false");writeFileSync(join(repo,"sentinel.txt"),"Independent error lifecycle input\n");
git("add","sentinel.txt");git("-c","core.hooksPath=/dev/null","commit","-m","Independent fixture");
writeFileSync(join(root,"instructions.txt"),"No models; preserve foreign sessions.\n");
writeFileSync(join(root,"oracle.py"),`from pathlib import Path\nPath(${JSON.stringify(join(root,"oracle-called"))}).touch()\n`);
const shells=new Map<string,any>();const sessions=new Map<string,any[]>();const effects:string[]=[];
function create(thread:string,workspace:string,project:string){
 shells.set(thread,{id:thread,projectId:project,worktreePath:workspace,modelSelection:{provider:"codex",model:"gpt-6.1-sol"},
  archivedAt:null,latestTurn:{turnId:"historical-turn",state:"completed"},
  session:{status:"ready",providerName:"codex",activeTurnId:null},hasPendingApprovals:false,hasPendingUserInput:false,hasActionableProposedPlan:false});
 sessions.set(thread,[]);
}
const runtime:GateRuntime={
 ensureProject:async()=>{},createThread:async(task,attempt)=>create(attempt.thread_id,attempt.workspace,task.project_id),
 startThread:async()=>{},createAttachedThread:async(task,attachment)=>create(attachment.thread_id,task.repo,task.project_id),
 readThread:async thread=>readManagedThread(shells.get(thread),sessions.get(thread)!),
 stopThread:async thread=>{effects.push("stop:"+thread);shells.get(thread).session.status="stopped";},
 archiveThread:async thread=>{effects.push("archive:"+thread);shells.get(thread).archivedAt="2026-10-09T00:00:00Z";},
};
async function cli(task:string,command:string,...args:string[]){
 const argv=["--state",state,command,"--task",task,...args];let output="";const original=process.stdout.write;
 process.stdout.write=function(chunk:any,...rest:any[]){output+=String(chunk);rest.find(v=>typeof v==="function")?.();return true;} as any;
 let exit:number;try{exit=await main(argv,runtime);}finally{process.stdout.write=original;}
 const result=JSON.parse(output);console.log(JSON.stringify({argv,exit,result}));return result;
}
async function fixture(task:string,role:"worker"|"reviewer"){
 assert.equal((await cli(task,"create","--project",task,"--repo",repo,"--base",git("rev-parse","HEAD"),
  "--oracle",join(root,"oracle.py"),"--instructions",join(root,"instructions.txt"))).ok,true);
 const response=role==="worker"?await cli(task,"dispatch","--runtime-mode","approval-required"):
  await cli(task,"attach","--role","reviewer","--model-selection",JSON.stringify({provider:"codex",model:"gpt-6.1-sol"}),
   "--runtime-mode","approval-required","--instructions",join(root,"instructions.txt"));
 assert.equal(response.ok,true);
 const thread=role==="worker"?response.attempt.thread_id:response.attachment.thread_id;
 shells.get(thread).session.status="error";
 return {thread,response,role};
}
console.log(JSON.stringify({fixture_root:root,mode:process.argv[2]}));
const negatives=["provider-present","provider-running","shell-active-turn","provider-active-turn","running-latest-turn","approval","user-input","plan","foreign-workspace","foreign-provider","foreign-turn"];
for(const role of ["worker","reviewer"] as const){
 for(const scenario of process.argv[2]==="positive"?["inactive"]:negatives){
  const task=role+"-"+scenario;const f=await fixture(task,role);const shell=shells.get(f.thread);
  const active={threadId:f.thread,cwd:shell.worktreePath,provider:"codex",status:"ready",activeTurnId:null};
  if(scenario==="provider-present")sessions.set(f.thread,[active]);
  if(scenario==="provider-running")sessions.set(f.thread,[{...active,status:"running"}]);
  if(scenario==="shell-active-turn")shell.session.activeTurnId="historical-turn";
  if(scenario==="provider-active-turn")sessions.set(f.thread,[{...active,activeTurnId:"live-turn"}]);
  if(scenario==="running-latest-turn")shell.latestTurn.state="running";
  if(scenario==="approval")shell.hasPendingApprovals=true;
  if(scenario==="user-input")shell.hasPendingUserInput=true;
  if(scenario==="plan")shell.hasActionableProposedPlan=true;
  if(scenario==="foreign-workspace")shell.worktreePath="/foreign-workspace";
  if(scenario==="foreign-provider")shell.session.providerName="claude";
  if(scenario==="foreign-turn"){
   if(role==="worker")shell.latestTurn.turnId="replacement-turn";
   else sessions.set(f.thread,[{...active,cwd:"/foreign-workspace"}]);
  }
  const before=(await cli(task,"status")).task;const prior=[...effects];
  const result=await cli(task,"reclaim",role==="worker"?"--attempt":"--thread",role==="worker"?f.response.attempt.attempt_id:f.thread);
  if(scenario==="inactive"){
   assert.equal(result.ok,true,"Inactive error must be reclaimed through the public CLI");
   assert.deepEqual(effects.slice(prior.length),["stop:"+f.thread,"archive:"+f.thread]);
  }else{
   assert.equal(result.ok,false,scenario);assert.deepEqual(effects,prior,scenario);
   assert.deepEqual((await cli(task,"status")).task,before,scenario);
  }
 }
}
// The run observer must continue refusing error; the independent oracle must never be invoked.
import { existsSync } from "node:fs";
const normalStart=runtime.startThread;
runtime.startThread=async(task,attempt,prompt)=>{await normalStart(task,attempt,prompt);shells.get(attempt.thread_id).session.status="error";};
const task="error-run";await cli(task,"create","--project",task,"--repo",repo,"--base",git("rev-parse","HEAD"),
 "--oracle",join(root,"oracle.py"),"--instructions",join(root,"instructions.txt"));
const run=await cli(task,"run","--runtime-mode","approval-required","--wait-seconds","2");
assert.equal(run.ok,false);assert.equal(run.error,"run_external_unknown");assert.notEqual(run.run?.outcome,"completed");assert.equal(existsSync(join(root,"oracle-called")),false);
assert.notEqual((await cli(task,"status")).task.state,"accepted");
console.log("PASS "+process.argv[2]+" error-contract cases and error-run refusal");
