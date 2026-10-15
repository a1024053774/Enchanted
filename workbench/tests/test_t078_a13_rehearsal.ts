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
mkdirSync(output, { recursive: false });
const scratch = realpathSync(mkdtempSync("/private/tmp/t078-2-a13-rehearsal-"));
const state = join(scratch, "state");
const requestDir = join(scratch, "roles", "ideation", "requests");
mkdirSync(state, { recursive: true });
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

async function run(argv: string[], input = ""): Promise<CommandResult> {
  const number = ++commandNumber;
  const result = await new Promise<CommandResult>((resolveResult, reject) => {
    const child = spawn(process.execPath, argv, { env: { ...process.env }, stdio: ["pipe", "pipe", "pipe"] });
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
  writeFileSync(join(output, `command-${number}.json`), JSON.stringify({ argv, input, ...result }, null, 2) + "\n");
  return result;
}

const gateCli = resolve("workbench/src/gates/cli.ts");
async function signal(value: Record<string, unknown>, launch = ideation.record.id) {
  return run([gateCli, "--state", state, "signal", "--launch", launch], JSON.stringify(value));
}

const task: any = {
  task_id: "a13-rehearsal-task", project_id: "a13-rehearsal-project", repo: scratch,
  spec_rev: 1, state: "registered", current_attempt: null,
};
const makeController = (preset: "ideation" | "executor") => {
  const record: any = {
    id: randomUUID(), task: task.task_id, thread: randomUUID(), project: task.project_id,
    preset, session: randomUUID(), spec_rev: 1, role: "controller", cli: "Claude Code",
    attempt: null, turn_limit: 2, env: { A2A_REQUEST_DIR: requestDir },
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
}, 30_000);

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
  executor = makeController("executor");
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
  writeFileSync(body, "A13 rehearsal stop body\n");
  const inboxCommand = [
    resolve("workbench/bin/inbox"), "--state", state, "send", "--from", "executor",
    "--to", "executor", "--kind", "stop", "--body-file", body,
    "--ref", `thread:${executor.record.thread}`,
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
  let entries: any[] = [];
  let wrongLaunchExit: number | undefined;
  await check("Stop hook converts request into an ideation-authored entry and wakes executor", async () => {
    const result = await signal(stop);
    equal("Stop exit code", result.code, 0);
    entries = stopEntries();
    equal("Stop entry count", entries.length, 1);
    equal("Stop entry from", entries[0]?.from, "ideation");
    equal("Stop entry target", entries[0]?.to, "executor");
    truthy("Stop entry thread ref", entries[0]?.refs?.includes(`thread:${executor.record.thread}`));
    const deliveryRow = panes.store.db.prepare("SELECT data FROM inbox_deliveries WHERE entry=? ORDER BY seq DESC LIMIT 1").get(entries[0].id);
    truthy("executor delivery receipt", deliveryRow);
    const delivery = JSON.parse(deliveryRow.data);
    truthy("executor wake state", ["queued", "delivered"].includes(delivery.state));
    truthy("executor wake thread", delivery.thread === executor.record.thread);
    const wake = panes.store.read().find((event: any) => event.type === "dispatch_queued" && event.data?.source === "inbox");
    truthy("executor dispatch wake event", wake);
  });
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
