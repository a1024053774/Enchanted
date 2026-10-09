// Evidence driver. All application layers, persistence, HTTP/MCP/WS routes,
// orchestration and provider adapters are the actual product. The private
// control directory supplies setup commands; it does not implement gate tools.
import { join } from "node:path";
import { mkdirSync, readFileSync, writeFileSync, readdirSync, existsSync, renameSync } from "node:fs";
const fork = process.env.T056_FORK!;
const root = process.env.T056_ROOT!;
const dep = (name: string) => join(fork, "apps/server/node_modules", name);
const src = (name: string) => join(fork, "apps/server/src", name);
const { Effect, Layer, ManagedRuntime, Scope, Exit, Stream } = await import(dep("effect/dist/index.js"));
const NodeServices = await import(dep("@effect/platform-node/dist/NodeServices.js"));
const { ServerConfig } = await import(src("config.ts"));
const { makeServerApplicationLayers } = await import(src("serverLayers.ts"));
const Sqlite = await import(src("persistence/Layers/Sqlite.ts"));
const { ProviderSessionReaperLive } = await import(src("provider/Layers/ProviderSessionReaper.ts"));
const { ProviderRuntimeReconcilerLive } = await import(src("provider/Layers/ProviderRuntimeReconciler.ts"));
const { ProviderRuntimeEventRepositoryLive } = await import(src("persistence/Layers/ProviderRuntimeEvents.ts"));
const { ServerLive, Server } = await import(src("effectServer.ts"));
const { OpenLive } = await import(src("open.ts"));
const { NetService } = await import(join(fork,"packages/shared/src/Net.ts"));
const FetchHttpClient = await import(dep("effect/dist/unstable/http/FetchHttpClient.js"));
const { AgentGatewayCredentials } = await import(src("agentGateway/Services/AgentGatewayCredentials.ts"));
const { OrchestrationEventDeliveryRepository, PROVIDER_COMMAND_REACTOR_CONSUMER } = await import(src("persistence/Services/OrchestrationEventDeliveries.ts"));
const SqlClient = await import(dep("effect/dist/unstable/sql/SqlClient.js"));
const { OrchestrationEngineService } = await import(src("orchestration/Services/OrchestrationEngine.ts"));
const { ProjectionSnapshotQuery } = await import(src("orchestration/Services/ProjectionSnapshotQuery.ts"));
const { ProjectionPendingInteractionRepository } = await import(src("persistence/Services/ProjectionPendingInteractions.ts"));
const { ProjectionPendingInteractionRepositoryLive } = await import(src("persistence/Layers/ProjectionPendingInteractions.ts"));
const { ServerSettingsService } = await import(src("serverSettings.ts"));
const { ThreadId } = await import(join(fork,"packages/contracts/src/index.ts"));
const { DEFAULT_SERVER_SETTINGS } = await import(join(fork,"packages/contracts/src/settings.ts"));
mkdirSync(join(root,"userdata"), { recursive:true, mode:0o700 });
if (!existsSync(join(root,"userdata/settings.json"))) {
  const settings = structuredClone(DEFAULT_SERVER_SETTINGS);
  settings.enableProviderUpdateChecks = false;
  for (const value of Object.values(settings.providers) as any[]) value.enabled = false;
  writeFileSync(join(root,"userdata/settings.json"), JSON.stringify({ revision:0, migrationVersion:0, settings }));
}
const { runtimeServicesLayer, providerLayer } = makeServerApplicationLayers();
const reaper = ProviderSessionReaperLive.pipe(Layer.provideMerge(runtimeServicesLayer), Layer.provideMerge(providerLayer));
const reconciler = ProviderRuntimeReconcilerLive.pipe(Layer.provide(ProviderRuntimeEventRepositoryLive), Layer.provideMerge(runtimeServicesLayer), Layer.provideMerge(providerLayer));
const runtime = ManagedRuntime.make(Layer.empty.pipe(
  Layer.provideMerge(runtimeServicesLayer), Layer.provideMerge(providerLayer),
  Layer.provideMerge(reaper), Layer.provideMerge(reconciler), Layer.provideMerge(ServerLive),
  Layer.provideMerge(Sqlite.layerConfig),
  Layer.provideMerge(ServerConfig.layerTest(fork, root, { host:"127.0.0.1", port:Number(process.env.T056_PORT ?? 0), devUrl:process.env.T056_WEB ? new URL(process.env.T056_WEB) : undefined, noBrowser:true, homeDir:root, chatWorkspaceRoot:root, studioWorkspaceRoot:root, groupsWorkspaceRoot:root })),
  Layer.provideMerge(OpenLive), Layer.provideMerge(NetService.layer),
  Layer.provideMerge(FetchHttpClient.layer), Layer.provideMerge(NodeServices.layer),
));
const scope = await Effect.runPromise(Scope.make("sequential"));
const server = await runtime.runPromise(Scope.provide(Effect.gen(function*() { return yield* (yield* Server).start; }), scope));
const credentials = await runtime.runPromise(Effect.service(AgentGatewayCredentials));
const engine = await runtime.runPromise(Effect.service(OrchestrationEngineService));
const query = await runtime.runPromise(Effect.service(ProjectionSnapshotQuery));
const sql = await runtime.runPromise(Effect.service(SqlClient.SqlClient));
const deliveries = await runtime.runPromise(Effect.service(OrchestrationEventDeliveryRepository));
const settings = await runtime.runPromise(Effect.service(ServerSettingsService));
mkdirSync(join(root,"control"), { recursive:true, mode:0o700 });
writeFileSync(join(root,"ready.json"), JSON.stringify({ origin:`http://127.0.0.1:${server.address().port}`, pid:process.pid, source_revision:process.env.T056_SOURCE_REVISION }));
console.log("T056 ready", process.pid);
function publish(path: string, value: unknown) {
  const temporary = path + ".part";
  writeFileSync(temporary, JSON.stringify(value));
  renameSync(temporary, path);
}
const timer = setInterval(async () => {
  for (const name of readdirSync(join(root,"control")).filter((n:string)=>n.endsWith(".request.json"))) {
    const resultPath = join(root,"control",name.replace(".request.json",".result.json"));
    if (existsSync(resultPath)) continue;
    publish(resultPath, { pending: true });
    const input = JSON.parse(readFileSync(join(root,"control",name),"utf8"));
    try {
      let result;
      if (input.operation === "command") result = await runtime.runPromise(engine.dispatch(input.command));
      else if (input.operation === "pending") result = await runtime.runPromise(Effect.gen(function*() {
        const repository = yield* ProjectionPendingInteractionRepository;
        return yield* repository.listByThreadId({ threadId: ThreadId.makeUnsafe(input.thread) });
      }).pipe(Effect.provide(ProjectionPendingInteractionRepositoryLive)));
      else if (input.operation === "seed-delivery") {
        // Controlled dependency state only. The event and actual repository
        // lifecycle stay real; no user-input row is seeded by this fixture.
        await runtime.runPromise(sql`UPDATE orchestration_event_deliveries SET state='retry',
          completed_at=NULL WHERE consumer_name=${PROVIDER_COMMAND_REACTOR_CONSUMER}
          AND event_sequence=${input.sequence} AND thread_id=${input.thread}`);
        const claimOwner = "t056-controlled-failure";
        const now = new Date().toISOString();
        const claimed = await runtime.runPromise(deliveries.claim({
          consumerName: PROVIDER_COMMAND_REACTOR_CONSUMER, eventSequence: input.sequence,
          threadId: input.thread, claimOwner, claimedAt: now,
          claimExpiresAt: new Date(Date.now()+60000).toISOString(),
        }));
        if (claimed._tag !== "Some") throw new Error("fixture could not claim delivery");
        result = await runtime.runPromise(deliveries.markTerminalFailure({
          consumerName: PROVIDER_COMMAND_REACTOR_CONSUMER, eventSequence: input.sequence,
          expectedClaimOwner: claimOwner, state: "dead", error: "T056 controlled delivery failure",
          updatedAt: now,
        }));
      }
      else if (input.operation === "events") {
        const events: unknown[] = [];
        const highWater = await runtime.runPromise(engine.getEventHighWaterSequence);
        await runtime.runPromise(Stream.runForEach(engine.readEventsThrough(0,highWater), (event: unknown) => Effect.sync(() => { events.push(event); })));
        result = events;
      }
      else if (input.operation === "snapshot") result = await runtime.runPromise(query.getSnapshot());
      else if (input.operation === "thread") result = await runtime.runPromise(query.getThreadDetailById(ThreadId.makeUnsafe(input.thread)));
      else if (input.operation === "settings") result = await runtime.runPromise(settings.updateSettings(input.patch));
      else if (input.operation === "token") {
        const token = credentials.issueSessionToken(ThreadId.makeUnsafe(input.thread),"codex");
        writeFileSync(input.path, token, {mode:0o600});
        result = { issued:true, thread:input.thread };
      } else throw new Error("unknown fixture operation");
      publish(resultPath, {ok:true,result});
    } catch (error) { publish(resultPath,{ok:false,error:String(error)}); }
  }
},100);
process.on("SIGTERM", async () => {
  clearInterval(timer); server.closeAllConnections();
  await Effect.runPromise(Scope.close(scope,Exit.void)); await runtime.dispose(); process.exit(0);
});
