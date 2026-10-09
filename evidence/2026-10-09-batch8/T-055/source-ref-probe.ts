// Focused durable-reference contract. Real gate entry/Git/SQLite; controlled
// native transport only. The real Codex/UI proof remains a separate scenario.
import assert from "node:assert/strict";
import { mkdirSync, writeFileSync, mkdtempSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join } from "node:path";
const { A2AGates, Refusal } = await import("/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts");
const mode=process.argv[3]??"delivered";
const root=mkdtempSync("/Volumes/WD-Elements/dev-cache/synara/instances/t055-source-");
const repo=join(root,"repo");mkdirSync(repo);
const git=(...args:string[])=>execFileSync("git",["-C",repo,...args],{encoding:"utf8",env:{...process.env,GIT_CONFIG_GLOBAL:"/dev/null",GIT_CONFIG_NOSYSTEM:"1"}}).trim();
git("init");git("config","user.name","isolated T055");git("config","user.email","fixture@example.invalid");git("config","commit.gpgsign","false");
writeFileSync(join(repo,"input.txt"),"independent fixture\n");git("add","input.txt");git("-c","core.hooksPath=/dev/null","commit","-m","Fixture");
writeFileSync(join(root,"oracle.py"),"pass\n");writeFileSync(join(root,"instructions.txt"),"Controlled native boundary, no model.\n");
let attempt:any;
const core=new A2AGates(join(root,"state"),{
 ensureProject:async()=>{},createThread:async(_task:any,value:any)=>{attempt=value;},startThread:async()=>{},
 readThread:async()=>({workspace:attempt.workspace,provider:"codex",turn:"active-turn",running:true,stopped:false,archived:false}),
 stopThread:async()=>{},archiveThread:async()=>{},sendUserAnswer:async()=>{
  if(mode==="ended")throw new Refusal("session_ended");
  if(mode==="unknown")throw new Refusal("run_external_unknown");
 },
});
const artifact={root,source:"controlled native boundary"} as any;
try {
 assert.equal((await core.call({command:"create",task:"source",project:"source-project",repo,base:git("rev-parse","HEAD"),oracle:join(root,"oracle.py"),instructions:join(root,"instructions.txt")})).ok,true);
 assert.equal((await core.call({command:"dispatch",task:"source",runtimeMode:"full-access"})).ok,true);
 const issue=await core.raiseIssue({title:"independent source sentinel",body:"",blocking:false,refs:[]},{thread:attempt.thread_id,turn:"active-turn",assertActive:async()=>{}});
 const result=await core.call({command:"answer_issue",task:"source",issue:issue.id,answer:"  保留开头空格。 \n"});
 assert.equal(result.ok,mode!=="unknown");
 if(mode==="unknown")assert.equal(result.error,"run_external_unknown");
 const event=(await core.call({command:"events",task:"source"})).events!.find((e:any)=>e.type==="issue_answer")!;
 const chain=await core.call({command:"issues",task:"source"});
 artifact.input=chain.user_inputs![0];artifact.answerEvent=event;artifact.result=result;artifact.chain=chain;artifact.mode=mode;
 if(mode==="ended")assert.ok(chain.records!.some((r:any)=>r.action==="forward"&&r.body==="session-ended"&&r.to==="executor"));
 if(mode==="unknown")assert.ok(!chain.records!.some((r:any)=>r.kind==="disposition"));
 // Failure list: absent event identity/sequence, wrong journal row, altered
 // answer whitespace. Expected source fields come from spec section 3.
 assert.equal(artifact.input.source_ref.event_id,event.details.id);
 assert.equal(artifact.input.source_ref.source_sequence,event.seq);
 assert.equal(artifact.input.text,"  保留开头空格。");
} finally {writeFileSync(process.argv[2],JSON.stringify(artifact,null,2)+"\n");core.close();}
