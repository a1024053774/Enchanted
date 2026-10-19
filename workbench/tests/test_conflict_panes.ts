// Isolated production Panes checks. No real process, socket, PTY or provider.
import assert from "node:assert/strict";
import childProcess from "node:child_process";
import { syncBuiltinESMExports } from "node:module";
import { promisify } from "node:util";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [productFlag, productArg, outputFlag, output] = process.argv.slice(2);
assert.equal(productFlag, "--product"); assert.equal(outputFlag, "--output");
assert(productArg && output && process.argv.length === 6);
const product = resolve(productArg);
let processRows = "101 1 101 102 /bin/zsh\n102 101 102 102 /fixture/codex\n";
const externalCalls: unknown[] = [];
const fakeExec = Object.assign(() => { throw new Error("Unconfigured callback-style process execution"); }, {
  [promisify.custom]: async (file: string, args: string[]) => {
    assert.equal(file, "/usr/bin/python3");
    assert.deepEqual(args.slice(0,3), ["-I", "-S", "-B"]);
    assert.equal(args[3], join(product,"workbench/src/processSnapshot.py"));
    assert.equal(args[4], "101");
    externalCalls.push({ file, args, stdout: processRows });
    const rows=processRows.trim().split("\n").map(line=>{
      const [pid,ppid,pgid,tpgid,command]=line.split(" ");
      return {pid:Number(pid),ppid:Number(ppid),pgid:Number(pgid),tpgid:Number(tpgid),command};
    });
    return { stdout: JSON.stringify({schema:1,root_pid:101,method:"macOS libproc",rows}), stderr: "" };
  },
});
childProcess.execFile = fakeExec as any;
syncBuiltinESMExports();
const { Panes } = await import(pathToFileURL(join(product, "workbench/src/panes.ts")).href);
const { OrchestrationStore } = await import(pathToFileURL(join(product, "workbench/src/store.ts")).href);
const root = mkdtempSync("/tmp/s3-pane-");
const results: { name: string; pass: boolean; assertion?: boolean; failure?: string }[] = [];
async function check(name: string, action: () => Promise<void>) {
  try { await action(); results.push({ name, pass: true }); }
  catch (error) { results.push({ name, pass: false, assertion: error instanceof assert.AssertionError, failure: String(error) }); }
}
function fixture(name: string) {
  const state = join(root, name); mkdirSync(state);
  const home = join(state, "home"); mkdirSync(join(home, "sessions"), { recursive: true });
  const workspace = join(state, "worker"); mkdirSync(workspace);
  const store = new OrchestrationStore(state);
  const writes: string[] = [];
  const pane: any = { record: { id: name, task: "conflict-task", attempt: "attempt-1", role: "worker",
    env: { CODEX_HOME: home }, argv: ["/fixture/codex"], executable_path: "/fixture/codex" },
    token: "fixture-token", task: {}, attempt: { workspace, thread_id: "thread-1" },
    pty: { pid: 101, write: (text: string) => writes.push(text) }, state: "idle", stopped: false, archived: false,
    failed: null, leader: 102, native: "native-1", turn: "turn-1", nativeEnded: false,
    active: null, queue: [], writing: false, stopInProgress: false, offsets: new Map(),
    writes: Promise.resolve(), pendingInputs: 0, userDraft: false, interrupted: false, sending: null,
    inputGeneration: 0, interruption: null,
    model: "unknown", effort: "unknown", terminalBuffer: "" };
  const panes = new Panes(state, store, { codex_home: home, turn_limit: 4 }, (reason: string) => { throw new Error(reason); });
  panes.panes.set("thread-1", pane);
  mkdirSync(join(state, "traces", name), { recursive: true });
  return { state, home, workspace, store, pane, panes, writes };
}
await check("archived_slot_released_but_live_slot_is_retained", async () => {
  const f = fixture("slot");
  try {
    f.pane.stopped = true; f.pane.archived = true;
    // Invalid runtime mode stops before launch configuration or spawning. The
    // observed refusal proves whether the old slot was released first.
    let code: string | null = null;
    try { await f.panes.createThread({}, { runtime_mode: "approval-required" }); }
    catch (error: any) { code = error.code; }
    assert.equal(code, "worker_requires_workspace_write");
    f.pane.archived = false;
    await assert.rejects(() => f.panes.createThread({}, { runtime_mode: "approval-required" }), { code: "single_worker_slice" });
  } finally { f.store.close(); }
});
await check("new_attempt_binds_only_its_own_rollout", async () => {
  const f = fixture("logs");
  try {
    f.pane.native = null;
    const metadata = (id: string, cwd: string) => JSON.stringify({ type: "session_meta", payload: { id, cwd, source: "cli" } }) + "\n";
    writeFileSync(join(f.home, "sessions/01-old.jsonl"), metadata("old-native", join(f.state, "old-worker")));
    writeFileSync(join(f.home, "sessions/02-native-1.jsonl"), metadata("native-1", f.workspace));
    let failure: unknown = null;
    try { f.panes.scan(f.pane); } catch (error) { failure = String(error); }
    assert.equal(failure, null);
    assert.equal(f.pane.native, "native-1");
    assert.equal(f.pane.offsets.size, 1);
    writeFileSync(join(f.home, "sessions/03-other-native.jsonl"), metadata("other-native", f.workspace));
    assert.throws(() => f.panes.scan(f.pane), { code: "ambiguous_native_session" });
  } finally { f.store.close(); }
});
await check("known_session_end_is_distinct_from_helpers_and_replacement", async () => {
  const f = fixture("lifecycle");
  try {
    processRows = "101 1 101 102 /bin/zsh\n102 101 102 102 /fixture/codex\n103 102 102 102 /bin/sh\n";
    let live = await f.panes.readThread("thread-1");
    assert.equal(live.error, undefined);
    assert.notEqual(live.session_ended, true);
    processRows = "101 1 101 101 /bin/zsh\n";
    live = await f.panes.readThread("thread-1");
    assert.equal(live.session_ended, true);
    assert.equal(live.running, false);
    assert.equal(live.error, undefined);
    assert.equal(f.store.read().filter((row: any) => row.type === "native_session_ended").length, 1);
    await f.panes.readThread("thread-1");
    assert.equal(f.store.read().filter((row: any) => row.type === "native_session_ended").length, 1);
    processRows = "101 1 101 104 /bin/zsh\n104 101 104 104 /fixture/codex\n";
    live = await f.panes.readThread("thread-1");
    assert(live.error, "A replacement after end cannot authorize stopping or messaging the new leader");
  } finally { f.store.close(); }
});
await check("gate_feedback_uses_existing_queue_and_gate_origin", async () => {
  const f = fixture("feedback");
  try {
    processRows = "101 1 101 102 /bin/zsh\n102 101 102 102 /fixture/codex\n";
    f.pane.state = "busy";
    f.pane.active = { id: "active-turn", dispatch: "original", at: new Date().toISOString(), nativeTurn: "turn-1" };
    assert.equal(typeof f.panes.sendGateFeedback, "function");
    await f.panes.sendGateFeedback("thread-1", "repair-message", "独立夹具的冲突说明");
    assert.deepEqual(f.writes, []);
    assert.equal(f.pane.queue.length, 1);
    assert.equal(f.pane.queue[0].source, "gate");
    assert.equal(f.pane.queue[0].text, "⟦门禁 #1⟧\n独立夹具的冲突说明");
    assert.equal(f.store.read().filter((row: any) => row.type === "gate_feedback_registered").length, 1);
    f.pane.state = "idle"; f.pane.active = null;
    await f.panes.drain(f.pane);
    assert.deepEqual(f.writes, ["\x1b[200~⟦门禁 #1⟧\n独立夹具的冲突说明\x1b[201~", "\r"]);
    assert.equal(f.pane.queue.length, 0);
  } finally { f.store.close(); }
});
const pass = results.every((r) => r.pass);
writeFileSync(output, JSON.stringify({ status: pass ? "PASS" : "INCOMPLETE", product, root,
  argv: process.argv, evidence_layer: "isolated-Panes-with-controlled-process-observation", real_codex_turns: 0,
  tests: results, externalCalls }, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify({ status: pass ? "PASS" : "INCOMPLETE", tests: results }));
process.exitCode = pass ? 0 : 1;
