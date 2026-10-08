// Real Synara engine, journal, projection, gate service and client schema.
// The provider reactor is absent and ProviderService has no model-start method.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { Effect, Layer, ManagedRuntime, Stream } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/node_modules/effect/dist/index.js";
import { A2AGateService, A2AGateServiceLive } from "/Users/luckye/Documents/Code/synara/apps/server/src/a2a/service.ts";
import { installHumanInputRecording } from "/Users/luckye/Documents/Code/synara/apps/server/src/a2a/orchestration.ts";
import { A2AGates } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts";
import { ClientOrchestrationCommand } from "/Users/luckye/Documents/Code/synara/packages/contracts/src/orchestration.ts";
import { Schema } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/node_modules/effect/dist/index.js";
import { ServerConfig } from "/Users/luckye/Documents/Code/synara/apps/server/src/config.ts";
import { ServerSettingsService } from "/Users/luckye/Documents/Code/synara/apps/server/src/serverSettings.ts";
import { ProviderService } from "/Users/luckye/Documents/Code/synara/apps/server/src/provider/Services/ProviderService.ts";
import { OrchestrationEngineService } from "/Users/luckye/Documents/Code/synara/apps/server/src/orchestration/Services/OrchestrationEngine.ts";
import { OrchestrationEngineLive } from "/Users/luckye/Documents/Code/synara/apps/server/src/orchestration/Layers/OrchestrationEngine.ts";
import { OrchestrationProjectionPipelineLive } from "/Users/luckye/Documents/Code/synara/apps/server/src/orchestration/Layers/ProjectionPipeline.ts";
import { OrchestrationProjectionSnapshotQueryLive } from "/Users/luckye/Documents/Code/synara/apps/server/src/orchestration/Layers/ProjectionSnapshotQuery.ts";
import { ProjectionSnapshotQuery } from "/Users/luckye/Documents/Code/synara/apps/server/src/orchestration/Services/ProjectionSnapshotQuery.ts";
import { OrchestrationEventStoreLive } from "/Users/luckye/Documents/Code/synara/apps/server/src/persistence/Layers/OrchestrationEventStore.ts";
import { OrchestrationCommandReceiptRepositoryLive } from "/Users/luckye/Documents/Code/synara/apps/server/src/persistence/Layers/OrchestrationCommandReceipts.ts";
import { ProviderRuntimeEventRepositoryLive } from "/Users/luckye/Documents/Code/synara/apps/server/src/persistence/Layers/ProviderRuntimeEvents.ts";
import { SqlitePersistenceMemory } from "/Users/luckye/Documents/Code/synara/apps/server/src/persistence/Layers/Sqlite.ts";
const require = createRequire("/Users/luckye/Documents/Code/synara/apps/server/package.json");
const NodeServices = await import(require.resolve("@effect/platform-node/NodeServices"));
const root=mkdtempSync(join(tmpdir(),"a2a-t037-native-service-")); console.log(JSON.stringify({fixture_root:root}));
const repo=join(root,"repo");mkdirSync(repo);
const git=(...args:string[])=>execFileSync("git",["-C",repo,...args],{encoding:"utf8",env:{...process.env,GIT_CONFIG_NOSYSTEM:"1",GIT_CONFIG_GLOBAL:"/dev/null"}}).trim();
git("init");git("config","user.name","Independent native service fixture");git("config","user.email","fixture@example.invalid");git("config","commit.gpgsign","false");writeFileSync(join(repo,"input.txt"),"Independent original\n");git("add","input.txt");git("commit","-m","Independent original");const base=git("rev-parse","HEAD");
const oracle=join(root,"oracle.py"), instructions=join(root,"instructions.txt");writeFileSync(oracle,"raise SystemExit(0)\n");writeFileSync(instructions,"Native engine provenance acceptance\n");
const settings=ServerSettingsService.layerTest();
const queryLayer=OrchestrationProjectionSnapshotQueryLive.pipe(Layer.provide(settings));
const configLayer=ServerConfig.layerTest(repo,join(root,"server"),{homeDir:root,chatWorkspaceRoot:root,studioWorkspaceRoot:root,groupsWorkspaceRoot:root});
const engineLayer=OrchestrationEngineLive.pipe(Layer.provideMerge(OrchestrationProjectionPipelineLive),Layer.provideMerge(queryLayer),Layer.provideMerge(OrchestrationEventStoreLive),Layer.provideMerge(OrchestrationCommandReceiptRepositoryLive),Layer.provideMerge(ProviderRuntimeEventRepositoryLive),Layer.provideMerge(SqlitePersistenceMemory),Layer.provide(settings),Layer.provideMerge(configLayer),Layer.provideMerge(NodeServices.layer));
let providerSessions:any[]=[]; const stopRequests:string[]=[];
const providerLayer=Layer.succeed(ProviderService,{listSessions:()=>Effect.succeed(providerSessions),stopSession:(input:any)=>Effect.sync(()=>{stopRequests.push(input.threadId);providerSessions=[];})} as any);
const runtime=ManagedRuntime.make(A2AGateServiceLive.pipe(Layer.provideMerge(Layer.mergeAll(engineLayer,providerLayer))));
try {
 const gates=await runtime.runPromise(Effect.service(A2AGateService));
 const engine=await runtime.runPromise(Effect.service(OrchestrationEngineService));
 const query=await runtime.runPromise(Effect.service(ProjectionSnapshotQuery));
 const config=await runtime.runPromise(Effect.service(ServerConfig));
 if(process.argv.includes("--mutant-no-human-recording")) (gates as any).recordHumanInput=()=>false;
 assert.equal((await gates.call({command:"create",task:"native-service",project:"literal-project",repo,base,oracle,instructions})).ok,true);
 // Integration advances independently after registration. Dispatch must use this
 // authoritative head, not the task's stored creation base.
 writeFileSync(join(repo,"input.txt"),"Independent advanced integration\n");git("add","input.txt");git("commit","-m","Independent integration advance");const head=git("rev-parse","HEAD");git("update-ref","refs/a2a/integration",head,base);
 const dispatch=await gates.call({command:"dispatch",task:"native-service",runtimeMode:"approval-required"});assert.equal(dispatch.ok,true,JSON.stringify(dispatch));
 const attempt=dispatch.task!.current_attempt!;
 assert.equal(attempt.base_commit,head);assert.equal(execFileSync("git",["-C",attempt.workspace,"rev-parse","HEAD"],{encoding:"utf8"}).trim(),head);
 const shell:any=await runtime.runPromise(query.getThreadShellById(attempt.thread_id as any));assert.equal(shell._tag,"Some");
 assert.equal(shell.value.modelSelection.provider,"codex");assert.equal(shell.value.modelSelection.model,"gpt-6.1-sol");assert.deepEqual(shell.value.modelSelection.options,{reasoningEffort:"xhigh",fastMode:true});
 assert.equal(shell.value.envMode,"worktree");assert.equal(shell.value.worktreePath,attempt.workspace);assert.equal(shell.value.runtimeMode,"approval-required");
 let sequence=0;
 const command=(thread:string,origin?:string)=>({type:"thread.turn.start",commandId:"literal-command-"+sequence,threadId:thread,message:{messageId:"literal-message-"+sequence++,role:"user",text:"Human request: retain the current worktree",attachments:[]},runtimeMode:"approval-required",interactionMode:"default",createdAt:new Date().toISOString(),...(origin?{dispatchOrigin:origin}:{})});
 const user:any=Schema.decodeUnknownSync(ClientOrchestrationCommand)(command(attempt.thread_id,"agent"));assert.equal("dispatchOrigin" in user,false);
 await runtime.runPromise(engine.dispatch(user));
 const events=async()=> (await gates.call({command:"events",task:"native-service"})).events!;
 const deadline=performance.now()+5000;
 while(!(await events()).some(e=>e.type==="human_intervention")) {assert.ok(performance.now()<deadline,"BUSINESS_RED real client human input did not produce an intervention");await new Promise(r=>setTimeout(r,20));}
 const first=(await events()).filter(e=>e.type==="human_intervention");assert.equal(first.length,1);
 for(const origin of ["agent","automation"]) await runtime.runPromise(engine.dispatch(command(attempt.thread_id,origin) as any));
 await runtime.runPromise(engine.dispatch({type:"thread.create",commandId:"unmanaged-create",threadId:"unmanaged-thread",projectId:"literal-project",title:"Unmanaged sentinel",envMode:"local",branch:null,worktreePath:null,modelSelection:{provider:"codex",model:"gpt-6.1-sol"},runtimeMode:"approval-required",interactionMode:"default",createdAt:new Date().toISOString()} as any));
 await runtime.runPromise(engine.dispatch(Schema.decodeUnknownSync(ClientOrchestrationCommand)(command("unmanaged-thread")) as any));
 await new Promise(r=>setTimeout(r,50));assert.equal((await events()).filter(e=>e.type==="human_intervention").length,1);
 assert.equal((await gates.call({command:"status",task:"native-service"})).task!.state,"claimed");
 // Runtime worktree identity must use the actual provider session, rather than
 // trusting a thread's requested path when the provider is elsewhere.
 providerSessions=[{provider:"codex",threadId:attempt.thread_id,status:"ready",runtimeMode:"approval-required",cwd:repo,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()}];
 const beforeWrongCwd=(await gates.call({command:"status",task:"native-service"})).task;
 const wrongCwd=await gates.call({command:"reclaim",task:"native-service",attempt:attempt.attempt_id});
 console.log(JSON.stringify({wrong_cwd_result:wrongCwd,stop_requests:stopRequests}));
 assert.equal(wrongCwd.ok,false,"BUSINESS_RED runtime with an unrelated provider worktree cannot be reclaimed");assert.equal(wrongCwd.error,"identity_conflict");assert.deepEqual((await gates.call({command:"status",task:"native-service"})).task,beforeWrongCwd);assert.deepEqual(stopRequests,[]);
 providerSessions=[];
 // Revoke and replace with a local claim; human input to the historical native
 // thread must remain bound to that historical attempt, not the new owner.
 assert.equal((await gates.call({command:"revoke",task:"native-service",reason:"Independent ownership replacement"})).ok,true);
 const replacement=await gates.call({command:"claim",task:"native-service",owner:"replacement-owner"});assert.equal(replacement.ok,true);
 await runtime.runPromise(engine.dispatch(Schema.decodeUnknownSync(ClientOrchestrationCommand)(command(attempt.thread_id)) as any));
 const end=performance.now()+5000;while((await events()).filter(e=>e.type==="human_intervention").length<2){assert.ok(performance.now()<end,"Historical intervention missing");await new Promise(r=>setTimeout(r,20));}
 const interventions=(await events()).filter(e=>e.type==="human_intervention");assert.equal((interventions[1] as any).attempt,attempt.attempt_id);assert.equal((interventions[1]!.details as any).attempt_id,attempt.attempt_id);assert.notEqual((interventions[1]!.details as any).attempt_id,replacement.attempt!.attempt_id);
 // Independent recorder restarts against the same retained gate state, replaying
 // the actual engine journal. Duplicate event IDs must remain single entries.
 const replayCore=new A2AGates(join(config.stateDir,"a2a-gates"));
 try {await Effect.runPromise(Effect.scoped(installHumanInputRecording(replayCore,engine)));assert.equal((await replayCore.call({command:"events",task:"native-service"})).events!.filter(e=>e.type==="human_intervention").length,2);}finally{replayCore.close();}
 const journal=await Effect.runPromise(Stream.runCollect(engine.readEvents(0)));
 writeFileSync(join(root,"native-journal.json"),JSON.stringify(journal,null,2));writeFileSync(join(root,"gate-events.json"),JSON.stringify(await events(),null,2));
 console.log(JSON.stringify({status:"PASS",fixture_root:root,attempt,model_selection:shell.value.modelSelection,interventions,cases:["real-client-schema","real-engine-and-live-observer","agent-input-excluded","automation-input-excluded","unmanaged-input-excluded","historical-attempt-binding","observer-replay-deduplicated","dispatch-from-advanced-integration-head"]}));
} finally {await runtime.dispose();}
