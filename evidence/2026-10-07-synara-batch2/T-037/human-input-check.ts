// Independent native-message provenance and gate-event probe. No provider call.
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { A2AGates } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts";
import { decideOrchestrationCommand } from "/Users/luckye/Documents/Code/synara/apps/server/src/orchestration/decider.ts";
import { ClientOrchestrationCommand } from "/Users/luckye/Documents/Code/synara/packages/contracts/src/orchestration.ts";
import { Effect, Schema } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/node_modules/effect/dist/index.js";
const root = mkdtempSync(join(tmpdir(), "a2a-t037-human-input-"));
console.log(JSON.stringify({fixture_root: root}));
const repo=join(root,"repo"); mkdirSync(repo);
const git=(...args:string[])=>execFileSync("git",["-C",repo,...args],{encoding:"utf8",env:{...process.env,GIT_CONFIG_NOSYSTEM:"1",GIT_CONFIG_GLOBAL:"/dev/null"}}).trim();
git("init"); git("config","user.name","Independent human-input fixture");git("config","user.email","fixture@example.invalid");git("config","commit.gpgsign","false");
writeFileSync(join(repo,"input.txt"),"Literal independent fixture\n");git("add","input.txt");git("commit","-m","Independent baseline");
const oracle=join(root,"oracle.py"), instructions=join(root,"instructions.txt");writeFileSync(oracle,"raise SystemExit(0)\n");writeFileSync(instructions,"Native message provenance probe\n");
const threads=new Map<string, any>();
const runtime={ensureProject:async()=>{},createThread:async(_task:any,a:any)=>{threads.set(a.thread_id,{workspace:a.workspace,provider:"codex",turn:null,running:false,stopped:false,archived:false,blocked:false});},
 startThread:async(_task:any,a:any)=>{threads.get(a.thread_id).turn="owned-turn";},readThread:async(t:string)=>({...threads.get(t)}),stopThread:async(t:string)=>{threads.get(t).stopped=true;},archiveThread:async(t:string)=>{threads.get(t).archived=true;}};
const gates=new A2AGates(join(root,"state"),runtime);
try {
 const created=await gates.call({command:"create",task:"human-input",project:"project",repo,base:git("rev-parse","HEAD"),oracle,instructions});assert.equal(created.ok,true,JSON.stringify(created));
 const dispatched=await gates.call({command:"dispatch",task:"human-input",runtimeMode:"approval-required"});assert.equal(dispatched.ok,true,JSON.stringify(dispatched));
 const attempt=dispatched.task!.current_attempt!;
 const messagesBefore=(await gates.call({command:"events",task:"human-input"})).events!;
 if(typeof (gates as any).recordHumanInput !== "function") throw new Error("EXPECTED_CONTRACT_RED managed human input has no gate event recorder");
 const { recordHumanMessage }=await import("/Users/luckye/Documents/Code/synara/apps/server/src/a2a/orchestration.ts");
 const NOW="2026-10-07T12:00:00.000Z";
 const thread={id:attempt.thread_id,projectId:"project",title:"Literal fixture",modelSelection:{provider:"codex",model:"gpt-6.1-sol"},interactionMode:"default",runtimeMode:"approval-required",branch:null,worktreePath:attempt.workspace,parentThreadId:null,sidechatSourceThreadId:null,createdAt:NOW,updatedAt:NOW,latestTurn:null,handoff:null,messages:[],session:null,activities:[],proposedPlans:[],checkpoints:[],deletedAt:null};
 const readModel={snapshotSequence:1,updatedAt:NOW,spaces:[],projects:[],threads:[thread]};
 let seq=1;
 const message=async(origin:string,threadId=attempt.thread_id)=>{
  const command:any={type:"thread.turn.start",commandId:"literal-command-"+seq,threadId,message:{messageId:"literal-message-"+seq,role:"user",text:"Human correction: preserve the existing candidate",attachments:[]},createdAt:NOW,...(origin==="user"?{}:{dispatchOrigin:origin})};
  const model={...readModel,threads:[{...thread,id:threadId}]};
  const decided=await Effect.runPromise(decideOrchestrationCommand({readModel:model,command}) as any) as any;
  const event=(Array.isArray(decided)?decided:[decided]).find((e:any)=>e.type==="thread.message-sent");assert.ok(event,"Native decider must emit a message");return {...event,sequence:seq++};
 };
 const human=await message("user");assert.equal(human.payload.dispatchOrigin,"user");
 recordHumanMessage(gates,human);
 recordHumanMessage(gates,human); // Replay must not duplicate the intervention.
 const beforeIgnored=(await gates.call({command:"events",task:"human-input"})).events!;
 for(const origin of ["agent","automation"]) recordHumanMessage(gates,await message(origin));
 recordHumanMessage(gates,await message("user","unmanaged-thread"));
 recordHumanMessage(gates,{...human,eventId:"assistant-event",payload:{...human.payload,role:"assistant"}});
 const after=(await gates.call({command:"events",task:"human-input"})).events!;
 assert.deepEqual(after,beforeIgnored,"Other origins, assistant and unmanaged input must not append events");
 const interventions=after.filter(e=>e.type==="human_intervention");assert.equal(interventions.length,1);
 const detail:any=interventions[0]!.details;
 for(const [k,v] of Object.entries({task_id:"human-input",attempt_id:attempt.attempt_id,thread_id:attempt.thread_id,session_id:attempt.session_id,fence:attempt.fence,spec_rev:attempt.spec_rev,message_id:human.payload.messageId,text:human.payload.text,dispatch_origin:"user"})) assert.equal(detail[k],v,k);
 assert.deepEqual(after.slice(0,messagesBefore.length),messagesBefore,"Prior gate evidence is preserved");
 const status=await gates.call({command:"status",task:"human-input"});assert.equal(status.task!.state,"claimed");assert.equal(status.task!.candidate_commit,null);
 const client:any=Schema.decodeUnknownSync(ClientOrchestrationCommand)({type:"thread.turn.start",commandId:"spoof",threadId:attempt.thread_id,message:{messageId:"spoof-message",role:"user",text:"Spoofed agent origin",attachments:[]},createdAt:NOW,runtimeMode:"approval-required",interactionMode:"default",dispatchOrigin:"agent"});assert.equal("dispatchOrigin" in client,false,"Client cannot spoof provenance");
 console.log(JSON.stringify({status:"PASS",attempt,intervention:interventions[0],cases:["native-human","replay","agent","automation","unmanaged","assistant","no-state-progress","client-origin-stripped"]}));
} finally {gates.close();}
