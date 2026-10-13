// T-075-4 / controller #44: offline rollout and SQLite are real; PTY callbacks
// are simulated. Failure modes: no read at exit, pre-kill-only read, duplicate
// ingestion, missing/truncated/malformed/partial log silently ignored, another
// session read as the bound one, or post-stop queries ingesting later bytes.
import assert from "node:assert/strict";
import { appendFileSync, chmodSync, mkdirSync, mkdtempSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createRequire } from "node:module";
import { randomUUID } from "node:crypto";
const { Panes } = await import(process.env.A2A_PANE_MODULE ?? "../src/panes.ts");
import { OrchestrationStore } from "../src/store.ts";

const require = createRequire(import.meta.url);
const output = process.argv[2]!; mkdirSync(output);
const results = [];
for (const scenario of ["exit", "terminate", "shutdown", "reclaim", "missing", "truncated", "malformed", "partial", "unbound"]) {
  const root = mkdtempSync("/tmp/a4-final-native-");
  const home = join(root, "home"); mkdirSync(join(home, "sessions"), { recursive: true });
  const executable = join(root, "version-only");
  writeFileSync(executable, '#!/bin/sh\nprintf "codex-cli 0.162.1\\n"\n'); chmodSync(executable, 0o755);
  const role = join(root, "role.txt"); writeFileSync(role, "offline fixture; no model");
  const store = new OrchestrationStore(root);
  const native = randomUUID(), turn = randomUUID();
  const file = join(home, "sessions", "rollout-" + native + ".jsonl");
  const prefix = [{ type: "session_meta", payload: { id: native, source: "cli" } },
    { type: "event_msg", payload: { type: "task_started", turn_id: turn } }];
  const context = { type: "turn_context", payload: { turn_id: turn, model: "fixture-model-" + randomUUID(),
    effort: "fixture-effort", approval_policy: "never", sandbox_policy: { network_access: false } } };
  const encode = (items: unknown[]) => items.map((item) => JSON.stringify(item) + "\n").join("");
  const exits: ((event: any) => void)[] = [];
  let beforeExit = () => {};
  const emitExit = () => { beforeExit(); for (const callback of [...exits]) callback({ exitCode: 129, signal: 1 }); };
  require.cache[require.resolve("node-pty")] = { exports: { spawn: () => ({ pid: 123,
    onData: () => {}, onExit: (callback: any) => { exits.push(callback); }, write: () => {},
    kill: (signal: string) => { assert.equal(signal, "SIGHUP"); emitExit(); },
  }) } } as any;
  const observerFailures: string[] = [];
  const panes = new Panes(root, store, { codex_bin: executable, codex_home: home, role_card: role,
    code_revision: "offline", role_card_revision: "offline", hook_authorization: "offline", turn_limit: 1 },
    (reason: string) => observerFailures.push(reason));
  let failure: string | null = null;
  try {
    await panes.createThread({ task_id: "fixture", project_id: "fixture", card: { executor: { cli: "Codex", model: "gpt-6.1-sol", effort: "xhigh" } } } as any,
      { attempt_id: "attempt", session_id: "session", thread_id: "thread", runtime_mode: "workspace-write", workspace: root } as any);
    const pane = panes.get("thread");
    if (scenario !== "unbound") {
      writeFileSync(file, encode(prefix));
      await panes.signal(pane.record.id, JSON.stringify({ hook_event_name: "UserPromptSubmit", session_id: native, turn_id: turn }), new Date().toISOString());
      assert.equal(pane.native, native);
      assert.equal(store.read().filter((row) => row.type === "native_record").length, 2);
    }
    beforeExit = () => {
      // These bytes appear only after the pre-stop read, as a CLI flush at
      // interruption would. The next hook never arrives.
      if (scenario === "unbound") return;
      if (scenario === "missing") renameSync(file, file + ".preserved");
      else if (scenario === "truncated") { renameSync(file, file + ".preserved"); writeFileSync(file, ""); }
      else {
        appendFileSync(file, encode([context]));
        if (scenario === "malformed") appendFileSync(file, "not-json\n");
        if (scenario === "partial") appendFileSync(file, '{"unfinished":');
        // A newly discovered, unrelated CLI session must not be adopted.
        writeFileSync(join(home, "sessions", "other-cli.jsonl"), encode([
          { type: "session_meta", payload: { source: "cli", id: "unrelated" } }]));
      }
    };
    if (scenario === "terminate") await panes.terminate(pane, "offline_stop");
    else if (scenario === "shutdown") await panes.shutdown();
    else if (scenario === "reclaim") { pane.state = "idle"; await panes.stopThread("thread"); }
    else emitExit();
    const events = store.read();
    const records = events.filter((row) => row.type === "native_record");
    const successful = ["exit", "terminate", "shutdown", "reclaim"].includes(scenario);
    if (successful || ["partial", "malformed"].includes(scenario)) {
      assert.deepEqual(records.map((row) => row.data.record), [...prefix, context], "The bound session must include the last complete context exactly once");
      assert.equal(readFileSync(join(root, "traces", pane.record.id, "native.jsonl"), "utf8"), encode([...prefix, context]));
    } else assert.deepEqual(records.map((row) => row.data.record), scenario === "unbound" ? [] : prefix);
    const final = events.filter((row) => row.type === (successful ? "native_final_read" : "native_final_read_failed"));
    assert.equal(final.length, 1, "A final read must have one explicit outcome, including unavailable bytes");
    const exit = events.filter((row) => row.type === "pane_exit");
    assert.equal(exit.length, 1); assert.ok(final[0]!.seq < exit[0]!.seq);
    assert.equal(pane.stopped, true); assert.equal(pane.state, "unknown");
    assert.equal(pane.native, scenario === "unbound" ? null : native);
    const count = events.length;
    writeFileSync(file, encode([...prefix, context, { type: "post_stop_sentinel" }]));
    assert.equal(panes.status("thread").lifecycle, "interrupted");
    panes.launchInfo(pane.record.id);
    await panes.shutdown();
    assert.equal(store.read().length, count, "Stopped queries and repeated shutdown cannot import new bytes or duplicate the final read");
    assert.deepEqual(observerFailures, []);
  } catch (error) { failure = String(error); }
  writeFileSync(join(output, scenario + ".json"), JSON.stringify({ scenario, root, native, expected_context: context,
    failure, observerFailures, events: store.read() }, null, 2) + "\n");
  store.close(); results.push({ scenario, root, failure });
}
writeFileSync(join(output, "results.json"), JSON.stringify({ model_turns: 0, pty: "simulated callbacks", results }, null, 2) + "\n");
console.log(JSON.stringify(results, null, 2));
process.exitCode = results.some((row) => row.failure) ? 1 : 0;
