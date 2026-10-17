// Real daemon, relay, inbox client and Stop hook. No Claude/API/model process.
//
// The rehearsal deliberately uses the same native hook entry as a controller
// launch. PTYs are deterministic spies: they record a wake write but never
// start a provider process.
import {
  copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync,
  realpathSync, rmSync, writeFileSync,
} from "node:fs";
import { join, resolve } from "node:path";
import { randomUUID } from "node:crypto";
import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import { serve } from "../src/daemon.ts";
import { A2AGates } from "../src/gates/core.ts";
import { createOperatorCredential, readOperatorCredential } from "../src/credentials.ts";
import { request } from "../src/transport.ts";

type Check = {
  name: string; status: "PASS" | "INCOMPLETE"; observed?: unknown;
  expected?: unknown; error?: string;
};
type CommandResult = {
  code: number; signal: string | null; stdout: string; stderr: string; timed_out?: boolean;
};

const output = resolve(process.argv[2]);
const offlineRecipient = process.argv[3] === "--recipient-offline";
const ambiguousRecipient = process.argv[3] === "--recipient-ambiguous";
const startupMaterials = process.argv[4] ? resolve(process.argv[4]) : null;
if (process.argv.length > 5 || (process.argv[3] && !offlineRecipient && !ambiguousRecipient) ||
    (startupMaterials && !offlineRecipient)) throw new Error("unknown rehearsal scenario");
mkdirSync(output, { recursive: false });
const scratch = realpathSync(mkdtempSync("/private/tmp/t078-2-a13-rehearsal-"));
const state = join(scratch, "state");
const requestDir = join(scratch, "roles", "ideation", "requests");
mkdirSync(state, { recursive: true });
mkdirSync(join(scratch, "repo"));
mkdirSync(join(scratch, "roles", "ideation", "hooks"), { recursive: true });
mkdirSync(requestDir, { recursive: true });

process.env.A2A_OPERATOR_CREDENTIAL = join(scratch, "operator.json");
createOperatorCredential(state);
const operator = readOperatorCredential(state)!;
let panes: any;
let gates: any;
let daemonStopped = false;
let commandNumber = 0;
const checks: Check[] = [];
let currentStep = "setup";

const display = (value: unknown): unknown => value === undefined ? "<undefined>" : value;
function fail(name: string, observed: unknown, expected: unknown): never {
  const error = `${name}: observed=${JSON.stringify(display(observed))} expected=${JSON.stringify(display(expected))}`;
  throw Object.assign(new Error(error), {
    rehearsalStep: name, observed: display(observed), expected: display(expected),
  });
}
function equal(name: string, observed: unknown, expected: unknown) {
  if (!Object.is(observed, expected)) fail(name, observed, expected);
}
function truthy(name: string, observed: unknown) {
  if (!observed) fail(name, observed, "truthy");
}
function different(name: string, observed: unknown, expected: unknown) {
  if (Object.is(observed, expected)) fail(name, observed, `not ${JSON.stringify(expected)}`);
}
async function check(name: string, fn: () => Promise<void> | void) {
  currentStep = name;
  try {
    await fn();
    checks.push({ name, status: "PASS" });
  } catch (error) {
    const value = error as any;
    checks.push({
      name, status: "INCOMPLETE", observed: display(value?.observed),
      expected: display(value?.expected), error: String(error),
    });
    throw Object.assign(error instanceof Error ? error : new Error(String(error)), {
      rehearsalStep: name,
    });
  }
}

async function run(argv: string[], input = "", environment = process.env): Promise<CommandResult> {
  const number = ++commandNumber;
  const started = Date.now();
  const result = await new Promise<CommandResult>((resolveResult, reject) => {
    const child = spawn(process.execPath, argv, { env: { ...environment }, stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "", stderr = "", settled = false, closed = false;
    const hard = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill("SIGTERM");
      setTimeout(() => { if (!closed) child.kill("SIGKILL"); }, 250).unref();
      resolveResult({ code: 124, signal: "SIGTERM", stdout, stderr, timed_out: true });
    }, 5_000);
    child.stdout.on("data", bytes => { stdout += bytes; });
    child.stderr.on("data", bytes => { stderr += bytes; });
    child.on("error", error => {
      if (!settled) { settled = true; clearTimeout(hard); reject(error); }
    });
    child.on("close", (code, signal) => {
      closed = true;
      if (settled) return;
      settled = true; clearTimeout(hard);
      resolveResult({ code: code ?? -1, signal, stdout, stderr });
    });
    child.stdin.end(input);
  });
  writeFileSync(join(output, `command-${number}.json`), JSON.stringify({ argv, input, ...result, duration_ms: Date.now() - started }, null, 2) + "\n");
  return result;
}

const gateCli = resolve("workbench/src/gates/cli.ts");
async function signal(value: Record<string, unknown>, launch = ideation.record.id) {
  return run([gateCli, "--state", state, "signal", "--launch", launch], JSON.stringify(value));
}

const task: any = {
  task_id: "a13-rehearsal-task", project_id: "a13-rehearsal-project", repo: join(scratch, "repo"),
  spec_rev: 1, state: "registered", current_attempt: null,
};
const makeController = (preset: "ideation" | "executor") => {
  const record: any = {
    id: randomUUID(), task: task.task_id, thread: randomUUID(), project: task.project_id,
    preset, session: randomUUID(), spec_rev: 1, role: "controller", cli: "Claude Code",
    attempt: null, turn_limit: offlineRecipient ? 4 : 2, env: { A2A_REQUEST_DIR: requestDir },
  };
  panes.store.launch(record);
  const writes: string[] = [];
  const pane: any = {
    record, task, attempt: null, token: randomUUID(),
    pty: { pid: preset === "ideation" ? 11001 : 11002, write: (data: string) => writes.push(data) },
    state: preset === "executor" ? "idle" : "busy", native: record.session, active: null,
    claudePromptId: null, claudePromptIds: new Set(), failed: null, stopped: false,
    archived: false, stopInProgress: false, interrupted: false, writes: Promise.resolve(),
    pendingInputs: 0, inputGeneration: 0, userDraft: false, queue: [], writing: false,
    sending: null, offsets: new Map(), writes_readback: writes,
  };
  panes.panes.set(record.thread, pane);
  gates.registerController(record.thread);
  return { record, pane, writes };
};
const stopEntries = () => panes.store.db.prepare("SELECT data FROM inbox_records").all()
  .map((row: any) => JSON.parse(row.data)).filter((entry: any) => entry.kind === "stop");

let ideation: ReturnType<typeof makeController>;
let executor: ReturnType<typeof makeController>;
let failure: any;

async function shutdownAndArchive() {
  if (!daemonStopped) {
    try {
      await request(state, { command: "daemon_stop" }, operator);
      const deadline = Date.now() + 5_000;
      while (existsSync(join(state, "daemon.pid")) && Date.now() < deadline) {
        await new Promise(resolveDelay => setTimeout(resolveDelay, 20));
      }
      daemonStopped = !existsSync(join(state, "daemon.pid"));
    } catch (error) {
      checks.push({ name: "daemon-stop", status: "INCOMPLETE", error: String(error) });
    }
  }
  // If transport shutdown failed, close in-process handles as a bounded fallback.
  if (!daemonStopped) {
    try { gates?.beginShutdown?.(); } catch { /* preserve primary failure */ }
    try { gates?.close?.(); } catch { /* preserve primary failure */ }
    try { panes?.store?.close?.(); } catch { /* preserve primary failure */ }
  }
  // Checkpoint while a store handle is available. If another SQLite
  // connection keeps a WAL open, copy all sidecars below instead.
  try { panes?.store?.db?.exec("PRAGMA wal_checkpoint(TRUNCATE)"); } catch { /* sidecars are copied */ }
  for (const name of ["state.sqlite3", "state.sqlite3-wal", "state.sqlite3-shm"]) {
    const source = join(state, name);
    if (existsSync(source)) copyFileSync(source, join(output, name));
  }
  rmSync(scratch, { recursive: true, force: true });
}

// A stalled daemon, database operation, or child must not leave the runner
// alive indefinitely. Normal completion always clears this timer below;
// timeout cleanup is synchronous and keeps the partial result for diagnosis.
const hardDeadline = setTimeout(() => {
  const timeoutResult = {
    status: "INCOMPLETE", step: currentStep, error: "hard_timeout",
    checks, scratch_removed: false, scope: "real daemon/relay/bin-inbox/Stop signal; no Claude/API/model",
  };
  try { gates?.beginShutdown?.(); } catch { /* preserve timeout evidence */ }
  try { gates?.close?.(); } catch { /* preserve timeout evidence */ }
  try { panes?.store?.close?.(); } catch { /* preserve timeout evidence */ }
  try { writeFileSync(join(output, "result.json"), JSON.stringify(timeoutResult, null, 2) + "\n"); } catch { /* stdout is unavailable */ }
  process.exit(124);
// The extended scenario makes up to 17 serial native entry calls (5s each).
// local-02 measured several seconds per Node import under memory pressure;
// retain the per-call deadline and give the whole extended chain 90s.
// Main #312 adds six serial receipt queries, each retaining its 5s limit.
}, startupMaterials ? 160_000 : offlineRecipient ? 90_000 : 30_000);

try {
  await serve(state, {}, (root, value) => {
    panes = value;
    gates = new A2AGates(root, value);
    return gates;
  });
  // Synthetic spies must not be terminated as if they were native processes.
  // The actual daemon_stop path still closes the server and database handles.
  panes.shutdown = async () => {};
  panes.store.db.prepare("INSERT INTO tasks VALUES (?,?)").run(task.task_id, JSON.stringify(task));
  ideation = makeController("ideation");
  if (!offlineRecipient) executor = makeController("executor");
  if (ambiguousRecipient) makeController("executor");
  panes.processInfo = async (thread: string) => {
    const pane = panes.panes.get(thread);
    return { leader: pane?.pty.pid + 1, shell_pid: pane?.pty.pid,
      native_session: pane?.record.session, failed: pane?.failed ?? null };
  };

  const first = panes.store.register(ideation.record.id, "I1 protocol request");
  const active: any = { id: randomUUID(), dispatch: first.id, at: new Date().toISOString(), nativeTurn: null };
  ideation.pane.active = active;
  panes.store.event("turn_submit_intent", active, ideation.record);
  const env: NodeJS.ProcessEnv = {
    ...process.env, A2A_ROLE: "controller", A2A_PRESET: "ideation",
    A2A_PROJECT: task.project_id, A2A_TASK: task.task_id,
    A2A_SESSION: ideation.record.session, A2A_SPEC_REV: "1",
    A2A_NATIVE_SESSION: ideation.record.session, A2A_LAUNCH: ideation.record.id,
    A2A_CAPABILITY: ideation.pane.token, A2A_STATE: state, A2A_REQUEST_DIR: requestDir,
    A2A_HOOK_TRACE_DIR: join(scratch, "roles", "ideation", "hooks"),
  };
  // Keep the hook binding scoped to this rehearsal process only.
  Object.assign(process.env, env);

  const promptId = randomUUID();
  const body = join(scratch, "stop-body.txt");
  const targetThread = offlineRecipient ? randomUUID() : executor.record.thread;
  writeFileSync(body, "A13 rehearsal stop body\n");
  const inboxCommand = [
    resolve("workbench/bin/inbox"), "--state", state, "send", "--from", "executor",
    "--to", "executor", "--kind", "stop", "--body-file", body,
    "--ref", `thread:${targetThread}`,
    "--ref", "attempt:a13-attempt-runtime", "--ref", "input:a13-synthetic-input",
  ];
  const up = {
    session_id: ideation.record.session, hook_event_name: "UserPromptSubmit",
    prompt_id: promptId, prompt: first.text,
  };
  const stop = {
    session_id: ideation.record.session, hook_event_name: "Stop",
    prompt_id: promptId, stop_hook_active: false,
  };

  await check("UserPromptSubmit gate accepts current controller context", async () => {
    const result = await signal(up);
    equal("UPS exit code", result.code, 0);
    const context = JSON.parse(readFileSync(join(requestDir, "controller-context"), "utf8"));
    equal("controller-context prompt", context.prompt_id, promptId);
  });
  let queuedValue: any;
  await check("inbox send writes an undelivered queued request", async () => {
    const result = await run(inboxCommand);
    equal("inbox command exit code", result.code, 0);
    queuedValue = JSON.parse(result.stdout);
    equal("queued receipt ok", queuedValue.ok, true);
    equal("queued receipt flag", queuedValue.queued, true);
    equal("queued receipt delivery", queuedValue.delivered, false);
    truthy("queued request path", queuedValue.path);
    equal("queued request filename", queuedValue.path.endsWith(`${queuedValue.request_id}.json`), true);
  });
  await check("no Stop entry exists before Stop hook", () => {
    const count = stopEntries().length;
    equal("pre-Stop stop-entry count", count, 0);
  });
  await check("old Stop cannot transfer the queued request", async () => {
    equal("old Stop exit", (await signal({ ...stop, prompt_id: randomUUID() })).code, 0);
    equal("old Stop creates no entry", stopEntries().length, 0);
  });
  let entries: any[] = [];
  let wrongLaunchExit: number | undefined;
  await check(offlineRecipient ? "offline role keeps a visible pending receipt without feedback" : "Stop hook converts request into an ideation-authored entry and wakes executor", async () => {
    const result = await signal(stop);
    equal("Stop exit code", result.code, 0);
    entries = stopEntries();
    equal("Stop entry count", entries.length, 1);
    equal("Stop entry from", entries[0]?.from, "ideation");
    equal("Stop entry target", entries[0]?.to, "executor");
    truthy("Stop entry thread ref", entries[0]?.refs?.includes(`thread:${targetThread}`));
    const deliveryRow = panes.store.db.prepare("SELECT data FROM inbox_deliveries WHERE entry=? ORDER BY seq DESC LIMIT 1").get(entries[0].id);
    truthy("executor delivery receipt", deliveryRow);
    const delivery = JSON.parse(deliveryRow.data);
    if (ambiguousRecipient) {
      equal("ambiguous receipt is not pending", delivery.state, "undelivered");
      equal("ambiguous reason", delivery.reason, "ambiguous_role_session");
      const events = panes.store.read();
      truthy("ambiguity remains a visible rejection", events.find((e: any) => e.type === "relay_rejected" && e.data.result.error === "wake_undelivered"));
      equal("ambiguity does not dispatch to either target", events.filter((e: any) => e.type === "dispatch_queued" && e.data.source === "inbox").length, 0);
      return;
    }
    if (offlineRecipient) {
      const row = panes.store.db.prepare("SELECT data FROM relay_results WHERE key IN (SELECT key FROM relay_requests WHERE launch=? AND request_id=?)")
        .get(ideation.record.id, queuedValue.request_id);
      truthy("real relay receipt", row);
      const relay = JSON.parse(row.data);
      const events = panes.store.read();
      const feedback = events.filter((event: any) => event.launch === ideation.record.id && event.type === "dispatch_queued" && event.data?.source === "gate");
      const receiptEvents = events.filter((event: any) => ["relay_received", "relay_processed", "relay_rejected"].includes(event.type));
      const observed = { entry_count: entries.length, sender: entries[0].from, delivery: delivery.state,
        reason: delivery.reason ?? null, relay_ok: relay.ok, relay_error: relay.error ?? null, feedback_count: feedback.length };
      writeFileSync(join(output, "offline-observed.json"), JSON.stringify({ observed, receipt: relay, delivery_history:
        panes.store.db.prepare("SELECT data FROM inbox_deliveries WHERE entry=? ORDER BY seq").all(entries[0].id)
          .map((r: any) => JSON.parse(r.data)), receipt_events: receiptEvents, feedback_events: feedback,
        source: "real daemon/relay/inbox/Stop; executor session never created; native process/PTY observations are spies" }, null, 2) + "\n");
      const expected = { entry_count: 1, sender: "ideation", delivery: "pending", reason: "role_session_missing",
        relay_ok: true, relay_error: null, feedback_count: 0 };
      if (JSON.stringify(observed) !== JSON.stringify(expected)) fail("offline role contract", observed, expected);
      const event = receiptEvents.find((e: any) => e.type === "relay_processed" && e.data.request_id === queuedValue.request_id);
      equal("sender can observe pending by request id", event?.data.result.delivery.state, "pending");
      return;
    }
    truthy("executor wake state", ["queued", "delivered"].includes(delivery.state));
    truthy("executor wake thread", delivery.thread === executor.record.thread);
    const wake = panes.store.read().find((event: any) => event.type === "dispatch_queued" && event.data?.source === "inbox");
    truthy("executor dispatch wake event", wake);
  });
  if (offlineRecipient) {
    const entry = entries[0];
    const latestDelivery = () => JSON.parse(panes.store.db.prepare("SELECT data FROM inbox_deliveries WHERE entry=? ORDER BY seq DESC LIMIT 1").get(entry.id).data);
    const gateFeedback = () => panes.store.read().filter((e: any) => e.launch === ideation.record.id && e.type === "dispatch_queued" && e.data.source === "gate");
    const originalCreatedAt = entry.created_at;
    const faultIds: string[] = [];
    await check("seed uncertain historical writes without claiming delivery", () => {
      // Fault injection only: these histories model a crash during wake, not
      // new sends, and must never become authorization to resend on startup.
      for (const state of ["pending", "unknown"]) {
        const id = randomUUID(); faultIds.push(id);
        panes.store.db.prepare("INSERT INTO inbox_records(id,data) VALUES (?,?)").run(id, JSON.stringify({ ...entry, id, kind: "report", body: "uncertain write " + state }));
        panes.store.db.prepare("INSERT INTO inbox_deliveries(entry,data) VALUES (?,?)").run(id, JSON.stringify({ state, entry_id: id, created_at: originalCreatedAt }));
      }
    });
    await check("real controller_start queues without writing to unknown first screen", async () => {
      const roleRoot = join(scratch, "roles", "executor");
      for (const name of ["home", "claude", "tmp", "shell", "requests", "hooks", "user-data"]) mkdirSync(join(roleRoot, name), { recursive: true });
      writeFileSync(join(roleRoot, "role.md"), "Deterministic executor boundary spy\n");
      const input = { schema: 1, root: scratch, state, task: task.task_id, preset: "executor",
        launch: randomUUID(), session: randomUUID(), thread: randomUUID(), executable: "/Users/luckye/.local/share/claude/versions/2.1.296", version: "2.1.296",
        role_file: join(roleRoot, "role.md"), code_revision: "a".repeat(40), source_snapshot: join(scratch, "snapshot.tar.gz"), api_url: "http://127.0.0.1:1", turn_limit: 6 };
      const writes: string[] = [];
      const pty = createRequire(import.meta.url)("node-pty"), original = pty.spawn;
      pty.spawn = () => ({ pid: 11002, write: (data: string) => writes.push(data), onData: () => {}, onExit: () => {} });
      try {
        const result = await request(state, { command: "controller_start", task: task.task_id, manifest: input }, operator);
        equal("controller_start result", result.ok, true);
        const pane = panes.panes.get(input.thread);
        executor = { record: result.launch, pane, writes };
      } finally { pty.spawn = original; }
      equal("first screen state", executor.pane.state, "unknown");
      equal("first screen business bytes", executor.writes.length, 0);
      equal("registered inbox queue", executor.pane.queue.length, 1);
      equal("queue admission is not delivered", latestDelivery().state, "queued");
      equal("no I2 while target is unknown", gateFeedback().length, 0);
      await gates.resumeControllerInbox(executor.record.thread);
      equal("registration replay creates no second dispatch", executor.pane.queue.length, 1);
      for (const id of faultIds) equal("uncertain historical write not replayed", panes.store.inboxDispatch(id), undefined);
    });
    let startupWriteCount = 0;
    if (startupMaterials) await check("approved startup keys keep the pending inbox queued", async () => {
      const fixture = JSON.parse(readFileSync(join(startupMaterials, "fixture.json"), "utf8"));
      const expectedKeys = ["ArrowUp", "ArrowDown", "Enter", "Enter", "ArrowDown", "Enter"];
      equal("six actual screen approvals", fixture.frames.length, 6);
      const beforeQueue = executor.pane.queue.map((item: any) => item.id);
      const trace = join(state, "traces", executor.record.id, "pty.raw");
      const operatorEnv = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith("A2A_")));
      operatorEnv.A2A_OPERATOR_CREDENTIAL = join(scratch, "operator.json");
      for (let index = 0; index < fixture.frames.length; index++) {
        const frame = fixture.frames[index], screen = join(startupMaterials, frame.file);
        equal("recorded key " + index, frame.key, expectedKeys[index]);
        // The provider/PTY boundary is still a spy, fed immutable real screens.
        // The command, daemon, authority, screenKey, queue and writes are real.
        writeFileSync(trace, readFileSync(screen));
        const result = await run([gateCli, "--state", state, "pane_screen_key", "--thread", executor.record.thread,
          "--key", frame.key, "--purpose", frame.purpose, "--screen-id", "replay-s" + (index * 2 + 1),
          "--screen-file", screen, "--selected-label", frame.selected_label,
          "--authorization-ref", frame.approval_ref], "", operatorEnv);
        equal("startup CLI exit " + index, result.code, 0);
        equal("startup written receipt " + index, JSON.parse(result.stdout).written, true);
        const query = await run([resolve("workbench/bin/inbox"), "--state", state, "list", "--role", "executor"], "", operatorEnv);
        equal("startup receipt query exit " + index, query.code, 0);
        const listed = JSON.parse(query.stdout);
        equal("startup receipt query ok " + index, listed.ok, true);
        const refreshed = listed.entries.find((item: any) => item.entry.id === entry.id);
        const history = panes.store.db.prepare("SELECT data FROM inbox_deliveries WHERE entry=? ORDER BY seq").all(entry.id)
          .map((row: any) => JSON.parse(row.data));
        const i2 = panes.store.read().filter((event: any) =>
          (["relay_feedback_intent", "relay_feedback_registered"].includes(event.type) && event.data.entry_id === entry.id) ||
          (event.launch === ideation.record.id && event.type === "dispatch_queued" && event.data.source === "gate"));
        const observation = { key: frame.key, index, entry_id: entry.id, refreshed, history, I2: i2,
          state: executor.pane.state, active: executor.pane.active, queue: executor.pane.queue.map((item: any) => item.id),
          writes: [...executor.writes] };
        writeFileSync(join(output, `startup-receipt-${index}.json`), JSON.stringify(observation, null, 2) + "\n", { flag: "wx" });
        equal("startup receipt original entry " + index, refreshed?.entry.id, entry.id);
        equal("startup receipt original message " + index, refreshed?.delivery.message, beforeQueue[0]);
        equal("startup receipt original thread " + index, refreshed?.delivery.thread, executor.record.thread);
        equal("startup refreshed delivery " + index, refreshed?.delivery.state, "queued");
        equal("startup has no delivered history " + index, history.filter((row: any) => row.state === "delivered").length, 0);
        equal("startup has no I2 " + index, i2.length, 0);
        equal("startup remains unknown " + index, executor.pane.state, "unknown");
        equal("startup active remains null " + index, executor.pane.active, null);
        equal("startup queue unchanged " + index, JSON.stringify(executor.pane.queue.map((item: any) => item.id)), JSON.stringify(beforeQueue));
      }
      equal("only six control key writes", JSON.stringify(executor.writes), JSON.stringify(["\x1b[A", "\x1b[B", "\r", "\r", "\x1b[B", "\r"]));
      const events = panes.store.read().filter((event: any) => event.launch === executor.record.id);
      equal("no startup business paste or submission", events.filter((event: any) => ["paste_intent", "turn_submit_intent", "turn_submitted"].includes(event.type)).length, 0);
      equal("no I2 during startup navigation", gateFeedback().length, 0);
      startupWriteCount = executor.writes.length;
    });
    await check("initial release writes once then registers exactly the original I2", async () => {
      const result = await request(state, { command: "pane_release", thread: executor.record.thread, reason: "fixture first screen reviewed" }, operator);
      equal("initial release", result.ok, true);
      equal("delivered after CR", latestDelivery().state, "delivered");
      const releasedWrites = executor.writes.slice(startupWriteCount);
      equal("one bracketed paste", releasedWrites.filter(value => value.startsWith("\x1b[200~")).length, 1);
      equal("one submit CR", releasedWrites.filter(value => value === "\r").length, 1);
      equal("stop created_at unchanged", stopEntries()[0].created_at, originalCreatedAt);
      const feedback = gateFeedback(); equal("one I2", feedback.length, 1);
      const receipts = JSON.parse(feedback[0].data.text.slice(feedback[0].data.text.indexOf("\n[\n") + 1));
      equal("I2 original request", receipts[0].request_id, queuedValue.request_id);
      equal("I2 original entry", receipts[0].result.entry.id, entry.id);
      equal("I2 confirms delivered", receipts[0].result.delivery.state, "delivered");
      const submitted = panes.store.read().find((e: any) => e.launch === executor.record.id && e.type === "turn_submitted");
      const i2 = panes.store.read().find((e: any) => e.type === "relay_feedback_intent");
      truthy("I2 occurs after target turn_submitted", submitted && i2 && i2.seq > submitted.seq);
    });
    const roleSignal = async (role: typeof executor, payload: any) => run([gateCli, "--state", state, "signal", "--launch", role.record.id], JSON.stringify(payload), {
      ...process.env, ...role.record.env, A2A_LAUNCH: role.record.id, A2A_SESSION: role.record.session,
      A2A_NATIVE_SESSION: role.record.session, A2A_PRESET: role.record.preset, A2A_CAPABILITY: role.pane.token,
    });
    await check("I2 confirmation replays original request without another feedback", async () => {
      const item = panes.store.dispatchRecord(ideation.pane.active.dispatch), prompt = randomUUID();
      equal("I2 UPS", (await signal({ ...up, prompt_id: prompt, prompt: item.text })).code, 0);
      equal("I2 Stop", (await signal({ ...stop, prompt_id: prompt })).code, 0);
      equal("only original I2", gateFeedback().length, 1);
      equal("send executed once", stopEntries().length, 1);
    });
    let ackId: string;
    for (const repeat of [false, true]) await check(repeat ? "executor ack replay creates no duplicate ack or wake" : "executor acks through native inbox and real Stop", async () => {
      const item = panes.store.dispatchRecord(executor.pane.active.dispatch), prompt = randomUUID();
      equal("executor UPS", (await roleSignal(executor, { session_id: executor.record.session, hook_event_name: "UserPromptSubmit", prompt_id: prompt, prompt: item.text })).code, 0);
      const env = { ...process.env, ...executor.record.env, A2A_CAPABILITY: executor.pane.token };
      const queued = await run([resolve("workbench/bin/inbox"), "--state", state, "ack", "--role", "ideation", "--id", entry.id], "", env);
      equal("ack CLI", queued.code, 0);
      equal("ack Stop", (await roleSignal(executor, { session_id: executor.record.session, hook_event_name: "Stop", prompt_id: prompt, stop_hook_active: false })).code, 0);
      const acks = panes.store.db.prepare("SELECT data FROM inbox_records").all().map((r: any) => JSON.parse(r.data)).filter((e: any) => e.kind === "ack");
      equal("one ack", acks.length, 1); equal("actual ack sender", acks[0].from, "executor"); equal("ack reply", acks[0].reply_to, entry.id);
      if (repeat) equal("same ack id", acks[0].id, ackId!); else ackId = acks[0].id;
      const wakes = panes.store.read().filter((e: any) => e.type === "dispatch_queued" && e.data.inbox_entry === ackId);
      equal("one ack wake", wakes.length, 1);
      const deadline = Date.now() + 3_000;
      while ((!executor.pane.active || executor.pane.writing) && Date.now() < deadline) await new Promise(done => setTimeout(done, 5));
      truthy("executor feedback submission receipt", executor.pane.active && !executor.pane.writing);
    });
    await check("ideation cannot ack the executor-owned stop", async () => {
      const item = panes.store.dispatchRecord(ideation.pane.active.dispatch), prompt = randomUUID();
      equal("ideation ack UPS", (await signal({ ...up, prompt_id: prompt, prompt: item.text })).code, 0);
      const queued = await run([resolve("workbench/bin/inbox"), "--state", state, "ack", "--id", entry.id]);
      equal("foreign ack request queued", queued.code, 0);
      const id = JSON.parse(queued.stdout).request_id;
      equal("foreign ack Stop", (await signal({ ...stop, prompt_id: prompt })).code, 0);
      const row = panes.store.db.prepare("SELECT r.data FROM relay_results r JOIN relay_requests q ON q.key=r.key WHERE q.request_id=?").get(id);
      equal("foreign ack remains denied", JSON.parse(row.data).error, "recipient_required");
      const acks = panes.store.db.prepare("SELECT count(*) AS n FROM inbox_records WHERE json_extract(data,'$.kind')='ack'").get();
      equal("foreign ack creates no ack", Number(acks.n), 1);
    });
    writeFileSync(join(output, "offline-delivery.json"), JSON.stringify({ stop: stopEntries()[0], delivery: latestDelivery(),
      feedback: gateFeedback(), target_writes: executor.writes, events: panes.store.read(), created_at_unchanged: stopEntries()[0].created_at === originalCreatedAt }, null, 2) + "\n");
  }
  await check("wrong launch cannot create a second Stop entry", async () => {
    const result = await signal({ ...stop, prompt_id: randomUUID() }, randomUUID());
    wrongLaunchExit = result.code;
    different("wrong-launch exit code", result.code, 0);
    const count = stopEntries().length;
    equal("post-negative Stop-entry count", count, 1);
  });
  const delivery = JSON.parse(panes.store.db.prepare("SELECT data FROM inbox_deliveries WHERE entry=? ORDER BY seq DESC LIMIT 1").get(entries[0].id).data);
  writeFileSync(join(output, "result.json"), JSON.stringify({
    status: "PASS", checks,
    queued_receipt: { request_id: queuedValue.request_id, delivered: queuedValue.delivered },
    stop_entry: entries[0], delivery, wrong_launch_exit: wrongLaunchExit,
    stop_entry_count_after_wrong_launch: stopEntries().length,
    scope: "real daemon/relay/bin-inbox/Stop signal; PTY panes are deterministic spies; no Claude/API/model",
    real_model_turns: 0,
  }, null, 2) + "\n");
} catch (error) {
  failure = error;
  writeFileSync(join(output, "failure-context.json"), JSON.stringify({
    step: failure?.rehearsalStep ?? currentStep, observed: display(failure?.observed),
    expected: display(failure?.expected), error: String(failure), checks,
  }, null, 2) + "\n");
} finally {
  clearTimeout(hardDeadline);
  await shutdownAndArchive();
  if (failure) {
    writeFileSync(join(output, "result.json"), JSON.stringify({
      status: "INCOMPLETE", step: failure?.rehearsalStep ?? currentStep,
      observed: display(failure?.observed), expected: display(failure?.expected),
      error: String(failure), checks, scratch_removed: !existsSync(scratch),
      scope: "real daemon/relay/bin-inbox/Stop signal; no Claude/API/model",
    }, null, 2) + "\n");
  }
}
if (failure) process.exitCode = 1;
else console.log(JSON.stringify({ status: "PASS", scratch_removed: !existsSync(scratch), checks }));
