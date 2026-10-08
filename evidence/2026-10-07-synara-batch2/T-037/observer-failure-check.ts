// Real Synara engine, journal, projection, gate service and client schema.
// The provider reactor is absent and ProviderService has no model-start method.
import http from "node:http";
import { DatabaseSync } from "node:sqlite";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { Effect, Exit, Layer, ManagedRuntime, Scope, Stream } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/node_modules/effect/dist/index.js";
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
const NodeHttpServer = await import(require.resolve("@effect/platform-node/NodeHttpServer"));
const HttpRouter = await import(require.resolve("effect/unstable/http/HttpRouter"));
const { a2aGateRouteLayer } = await import("/Users/luckye/Documents/Code/synara/apps/server/src/a2a/httpRoute.ts");
const { ServerAuth } = await import("/Users/luckye/Documents/Code/synara/apps/server/src/auth/Services/ServerAuth.ts");
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
 // Hold the real gate database write transaction. The separate Synara journal
 // remains writable and receives a valid user input. No model or production DB.
 const blocker=new DatabaseSync(join(config.stateDir,"a2a-gates","state.sqlite3"));
 blocker.exec("PRAGMA busy_timeout=0; BEGIN IMMEDIATE");
 try {
  await runtime.runPromise(engine.dispatch(Schema.decodeUnknownSync(ClientOrchestrationCommand)(command(attempt.thread_id)) as any));
  await new Promise(r=>setTimeout(r,50));
 } finally {blocker.close();}
 const status=await gates.call({command:"status",task:"native-service"});
 const eventResult=await gates.call({command:"events",task:"native-service"});
 await runtime.runPromise(engine.dispatch(Schema.decodeUnknownSync(ClientOrchestrationCommand)(command(attempt.thread_id)) as any));
 await new Promise(r=>setTimeout(r,50));
 const afterLater=await gates.call({command:"events",task:"native-service"});
 const createdAfter=await gates.call({command:"create",task:"after-observer-failure",project:"literal-project",repo,base:head,oracle,instructions});
 const commandInputs=[
  {command:"claim",task:"native-service",owner:"later-owner"},
  {command:"revoke",task:"native-service",reason:"later-revoke"},
  {command:"revise",task:"native-service",spec_rev:2},
  {command:"dispatch",task:"native-service",runtimeMode:"approval-required"},
  {command:"run",task:"native-service",runtimeMode:"approval-required",wait_seconds:2},
  {command:"submit",task:"native-service",attempt:attempt.attempt_id,session:attempt.session_id,fence:attempt.fence,spec_rev:attempt.spec_rev,commit:head},
  ...["verify","integrate","reclaim"].map(command=>({command,task:"native-service",attempt:attempt.attempt_id})),
 ];
 const blocked=[];for(const input of commandInputs)blocked.push({input,result:await gates.call(input)});
 const afterBlocked=await gates.call({command:"status",task:"native-service"});
 const eventsAfterBlocked=await gates.call({command:"events",task:"native-service"});
 // Serve the actual authenticated gate GET segment on an owned ephemeral
 // loopback listener. This does not start an app instance or a provider reactor.
 const httpScope=await Effect.runPromise(Scope.make("sequential"));let nodeServer:any;
 let getResponse:any;
 try {
  await Effect.runPromise(Scope.provide(Effect.gen(function*(){
    const server=yield* NodeHttpServer.make(()=>{nodeServer=http.createServer();return nodeServer;},{port:0,host:"127.0.0.1"});
    yield* server.serve(yield* HttpRouter.toHttpEffect(a2aGateRouteLayer));
  }).pipe(Effect.provide(Layer.mergeAll(
    Layer.succeed(ServerConfig,{...config,host:"127.0.0.1",authToken:undefined,publicUrl:undefined}),
    Layer.succeed(A2AGateService,gates),Layer.succeed(ServerAuth,{authenticateWebSocketUpgrade:()=>Effect.die("No remote auth in isolated loopback probe")} as any),NodeHttpServer.layerHttpServices,
  ))),httpScope));
  const address=nodeServer.address();const url=`http://127.0.0.1:${address.port}/api/a2a?thread=${attempt.thread_id}`;
  const response=await fetch(url);getResponse={url,status:response.status,body:await response.json()};
 }finally{await Effect.runPromise(Scope.close(httpScope,Exit.void));}
 const observation={status,eventResult,afterLater,createdAfter,blocked,afterBlocked,getResponse,fixture_root:root};console.log(JSON.stringify(observation));
 writeFileSync(join(root,"observer-failure-observation.json"),JSON.stringify(observation,null,2));
 assert.equal(status.ok,true,"Read-only status remains available");assert.equal(eventResult.ok,true,"Read-only events remain available");
 assert.equal((status as any).human_input_observer?.state,"failed","BUSINESS_RED recording stopped without a visible failure");
 assert.equal((eventResult as any).human_input_observer?.state,"failed");
 assert.equal(getResponse.status,200);assert.equal(getResponse.body.ok,true);assert.equal(getResponse.body.human_input_observer.state,"failed");assert.equal(getResponse.body.human_input_observer.failure.event_id,(status as any).human_input_observer.failure.event_id);
 assert.ok((status as any).human_input_observer.failure.event_id);assert.ok((status as any).human_input_observer.failure.reason.includes("locked"));
 assert.equal(createdAfter.ok,false,"Failed observation must reject new mutations");assert.equal(createdAfter.error,"human_input_observer_failed");
 for(const entry of blocked){assert.equal(entry.result.ok,false,entry.input.command);assert.equal(entry.result.error,"human_input_observer_failed",entry.input.command);}
 assert.deepEqual(afterBlocked.task,status.task,"Rejected commands retain the original task and attempt");assert.deepEqual(eventsAfterBlocked.events,eventResult.events,"Rejected commands do not claim a persisted write after recording failed");
 assert.equal(afterLater.events!.filter(e=>e.type==="human_intervention").length,1,"No message may be silently marked as recorded");
 // Restart the recorder against the retained state and the actual engine log.
 const replayCore=new A2AGates(join(config.stateDir,"a2a-gates"));
 try {
  await Effect.runPromise(Effect.scoped(installHumanInputRecording(replayCore,engine)));
  const recovered=await replayCore.call({command:"events",task:"native-service"});
  assert.equal(recovered.events!.filter(e=>e.type==="human_intervention").length,3,"Restart replays both missed messages exactly once");
  console.log(JSON.stringify({recovered}));
 }finally{replayCore.close();}
 console.log(JSON.stringify({status:"PASS",fixture_root:root,cases:["real-sqlite-write-lock","visible-failure","read-only-status-and-events","reject-mutations","restart-replays-missed-input"]}));
} finally {await runtime.dispose();}
