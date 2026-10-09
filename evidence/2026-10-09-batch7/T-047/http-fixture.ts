// Evidence-only native thread double. Real gate core, HTTP route, server and Git;
// no provider is constructed and no model is called.
import http from "node:http";
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const fork = process.env.T047_FORK!;
const root = process.env.T047_ROOT!;
const delay = Number(process.env.T047_DELAY!);
const mode = process.env.T047_MODE ?? "complete";
const { Effect, Layer, Scope, Exit } = await import(join(fork, "apps/server/node_modules/effect/dist/index.js"));
const NodeServices = await import(join(fork, "apps/server/node_modules/@effect/platform-node/dist/NodeServices.js"));
const HttpRouter = await import(join(fork, "apps/server/node_modules/effect/dist/unstable/http/HttpRouter.js"));
const { A2AGates } = await import(join(fork, "packages/a2a-gates/src/core.ts"));
const { A2AGateService } = await import(join(fork, "apps/server/src/a2a/service.ts"));
const { a2aGateRouteLayer } = await import(join(fork, "apps/server/src/a2a/httpRoute.ts"));
const { makeBoundedNodeHttpServer } = await import(join(fork, "apps/server/src/nodeHttpServer.ts"));
const { ServerConfig } = await import(join(fork, "apps/server/src/config.ts"));
const { ServerAuth } = await import(join(fork, "apps/server/src/auth/Services/ServerAuth.ts"));
const repo = join(root, "repo");
mkdirSync(repo, { recursive: true });
const git = (cwd: string, ...args: string[]) => execFileSync("git", ["-C", cwd, ...args], {
  encoding: "utf8", env: { ...process.env, GIT_CONFIG_NOSYSTEM: "1", GIT_CONFIG_GLOBAL: "/dev/null", GIT_TERMINAL_PROMPT: "0" },
}).trim();
git(repo, "init");
git(repo, "config", "user.name", "T047 isolated fixture");
git(repo, "config", "user.email", "fixture@example.invalid");
git(repo, "config", "commit.gpgsign", "false");
writeFileSync(join(repo, "delivery.txt"), "unfinished\n");
git(repo, "add", "delivery.txt");
git(repo, "-c", "core.hooksPath=/dev/null", "commit", "-m", "Fixture baseline");
writeFileSync(join(root, "instructions.txt"), "Deliver the independent sentinel. No model invocation.\n");
writeFileSync(join(root, "oracle.py"), "from pathlib import Path\nimport sys\nassert Path(sys.argv[1], 'delivery.txt').read_text() == 'T047 independently specified delivery\\n'\nsys.stdout.buffer.write(b'control: \\x00\\x01\\x1b\\t\\r\\n')\n");
const threads = new Map<string, any>();
let gates: InstanceType<typeof A2AGates>;
const runtime = {
  ensureProject: async () => {},
  createThread: async (_task: any, attempt: any) => {
    threads.set(attempt.thread_id, { workspace: attempt.workspace, provider: "codex", turn: "fixture-turn", running: true, stopped: false, archived: false });
  },
  startThread: async (task: any, attempt: any) => {
    if (mode === "deadline") { threads.get(attempt.thread_id).running = false; return; }
    if (mode === "paused") { threads.get(attempt.thread_id).blocked = true; return; }
    setTimeout(async () => {
      try {
        writeFileSync(join(attempt.workspace, "delivery.txt"), "T047 independently specified delivery\n");
        git(attempt.workspace, "add", "delivery.txt");
        git(attempt.workspace, "-c", "core.hooksPath=/dev/null", "commit", "-m", "Controlled delivery");
        const commit = git(attempt.workspace, "rev-parse", "HEAD");
        const result = await gates.call({ command: "submit", task: task.task_id, attempt: attempt.attempt_id,
          session: attempt.session_id, fence: attempt.fence, spec_rev: task.spec_rev, commit }, {
          thread: attempt.thread_id, turn: "fixture-turn", assertActive: async () => {},
        });
        if (!result.ok) throw new Error(JSON.stringify(result));
        threads.get(attempt.thread_id).running = false;
        console.log(JSON.stringify({ fact: "submitted", commit, attempt: attempt.attempt_id }));
      } catch (error) { console.error(error); process.exitCode = 1; }
    }, delay * 1000);
  },
  readThread: async (thread: string) => ({ ...threads.get(thread) }),
  stopThread: async (thread: string) => { threads.get(thread).stopped = true; },
  archiveThread: async (thread: string) => { threads.get(thread).archived = true; },
};
gates = new A2AGates(join(root, "state"), runtime);
const scope = await Effect.runPromise(Scope.make("sequential"));
let server: http.Server;
await Effect.runPromise(Scope.provide(Effect.gen(function* () {
  const httpServer = yield* makeBoundedNodeHttpServer(() => { server = http.createServer(); return server; }, { host: "127.0.0.1", port: 0 });
  yield* httpServer.serve(yield* HttpRouter.toHttpEffect(a2aGateRouteLayer));
}).pipe(Effect.provide(Layer.mergeAll(
  Layer.succeed(A2AGateService, gates),
  ServerConfig.layerTest(repo, join(root, "server"), { host: "127.0.0.1", authToken: process.env.A2A_GATE_BEARER,
    homeDir: root, chatWorkspaceRoot: root, studioWorkspaceRoot: root, groupsWorkspaceRoot: root }),
  Layer.succeed(ServerAuth, { authenticateWebSocketUpgrade: () => Effect.die("Fixture token required") }),
).pipe(Layer.provideMerge(NodeServices.layer)))), scope));
const address = server!.address() as { port: number };
writeFileSync(join(root, "ready.json"), JSON.stringify({ origin: `http://127.0.0.1:${address.port}`,
  repo, base: git(repo, "rev-parse", "HEAD"), oracle: join(root, "oracle.py"), instructions: join(root, "instructions.txt"),
  serverTimeouts: { timeout: server!.timeout, requestTimeout: server!.requestTimeout, headersTimeout: server!.headersTimeout } }) + "\n");
console.log(JSON.stringify({ fact: "ready", pid: process.pid }));
process.on("SIGTERM", async () => {
  server!.closeAllConnections();
  await Effect.runPromise(Scope.close(scope, Exit.void));
  gates.close();
  process.exit(0);
});
