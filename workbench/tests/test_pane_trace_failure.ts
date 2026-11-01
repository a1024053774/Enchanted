// Isolated failure injection: a PTY callback cannot safely be made to fail in a
// paid model run. Cover trace I/O failure and trace+event-store failure separately.
// T-227 failure modes: each later frame records trace_write_failed again (or event_write_failed again when the
// store is read-only); a later frame clears the failure; a later frame still reaches the native scan; later frames
// keep writing the trace once it is writable again (only the record is deduplicated, not the writing); the native
// trace (native.jsonl) bypasses the rule, so its failure throws out of the scan and the next scan records the same
// native lines again; a stopped trace also stops reading what later frames carry (native scan, OSC 7501 reports),
// which the baseline did once the file was writable again (T-227 round-2 review); a failed pane keeps failing the
// same way on every later frame (native scan with the store read-only, a terminal protocol query it can no longer
// answer) and records it, or reports the event write failure, each time; a later failure replaces the first cause
// (T-227 round-3 review).
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync, renameSync, rmdirSync, statSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { join } from "node:path";
import { createRequire } from "node:module";
import { Panes } from "../src/panes.ts";
import { OrchestrationStore } from "../src/store.ts";

const require = createRequire(import.meta.url);
const output = process.argv[2]!;
mkdirSync(output, { recursive: false });
const results = [];
for (const scenario of ["trace", "trace+events", "native"]) {
  const failEvents = scenario === "trace+events";
  const root = mkdtempSync("/tmp/a2a-trace-failure-");
  const home = join(root, "isolated"); mkdirSync(join(home, "sessions"), { recursive: true });
  const executable = join(root, "codex-version");
  writeFileSync(executable, '#!/bin/sh\nprintf "codex-cli 0.162.1\\n"\n'); chmodSync(executable, 0o755);
  const role = join(root, "role.txt"); writeFileSync(role, "fixture worker");
  let onData: (data: string) => void = () => { throw Error("callback missing"); };
  require.cache[require.resolve("node-pty")] = { exports: { spawn: () => ({
    pid: 123, onData: (callback: typeof onData) => { onData = callback; }, onExit: () => {}, write: () => {},
  }) } } as any;
  const store = new OrchestrationStore(root);
  let observerFailure: unknown = null, observerFailures = 0;
  const panes = new Panes(root, store, { codex_bin: executable, codex_home: home, role_card: role,
    code_revision: "fixture", role_card_revision: "fixture", hook_authorization: "test-only", turn_limit: 1 },
    (error: unknown) => { observerFailure = error; observerFailures++; });
  let failure: string | null = null;
  try {
    await panes.createThread({ task_id: "fixture", project_id: "fixture", card: { executor: { cli: "Codex", model: "gpt-6-astra", effort: "xhigh" } } } as any,
      { task_id: "fixture", attempt_id: "attempt", session_id: "session", fence: 1, spec_rev: 1,
        runtime_mode: "workspace-write", thread_id: "thread", workspace: root, base_commit: "baseline" } as any);
    const pane = panes.get("thread");
    const native = randomUUID(), turn = randomUUID();
    const rollout = () => {
      const now = new Date(), day = join(home, "sessions", String(now.getFullYear()), String(now.getMonth() + 1).padStart(2, "0"),
        String(now.getDate()).padStart(2, "0")); // The scan walks the CLI's dated session directories.
      mkdirSync(day, { recursive: true });
      writeFileSync(join(day, "rollout-" + native + ".jsonl"), [
        { type: "session_meta", payload: { id: native, source: "cli", cwd: root } },
        { type: "event_msg", payload: { type: "task_started", turn_id: turn } }].map((item) => JSON.stringify(item) + "\n").join(""));
    };
    if (scenario === "native") {
      rollout();
      mkdirSync(join(root, "traces", pane.record.id, "native.jsonl")); // appendFile fails with EISDIR.
      // Each PTY frame and each launch query scans the native log (panes.ts onData, launchInfo).
      const thrown: string[] = []; // Before T-227 the failed append threw out of the scan; it is kept, not dropped.
      for (let scan = 0; scan < 3; scan++) {
        onData(`frame ${scan}`);
        try { panes.launchInfo(pane.record.id); } catch (error) { thrown.push(String(error)); }
      }
      const events = store.read("fixture");
      assert.equal(events.filter((event) => event.type === "native_record").length, 2, "each native line is recorded once across scans");
      assert.equal(events.filter((event) => event.type === "trace_write_failed").length, 1, "the native trace failure is recorded once");
      assert.equal(events.filter((event) => event.type === "native_read_failed").length, 0, "a trace failure is not a native read failure");
      assert.equal(pane.native, native, "the scan still binds the native session");
      assert.match(pane.failed!, /^trace_write_failed/);
      assert.deepEqual(thrown, [], "a trace failure stops the trace, not the scan");
    } else {
      const trace = join(root, "traces", pane.record.id, "pty.raw");
      renameSync(trace, trace + ".before-fault"); // Preserve the newly created empty trace.
      mkdirSync(trace); // appendFile fails with EISDIR.
      // With the store read-only, an unread session log makes every later frame's scan fail to record it.
      if (failEvents) { rollout(); store.db.exec("PRAGMA query_only=ON"); }
      for (let frame = 0; frame < 5; frame++) onData(`trace must be recorded ${frame}`);
      // The trace becomes writable again: a pane that stopped writing leaves it untouched.
      rmdirSync(trace); renameSync(trace + ".before-fault", trace);
      for (let frame = 5; frame < 8; frame++) onData(`trace must stay stopped ${frame}`);
      assert.equal(statSync(trace).size, 0, "frames after the failure are not written to the trace");
      // Terminal protocol queries the failed pane can no longer answer.
      for (let query = 0; query < 3; query++) onData("\x1b[6n");
      await new Promise((resolve) => setTimeout(resolve, 50));
      if (!failEvents) {
        assert.equal(store.read("fixture").filter((event) => event.type === "terminal_protocol_failed").length, 1, "an unanswerable query is recorded once");
        assert.match(pane.failed!, /^trace_write_failed/, "a later failure does not replace the first cause");
        // The CLI writes its session log after the failure; the next frame still reads it.
        rollout(); onData("frame after the session log");
        assert.equal(store.read("fixture").filter((event) => event.type === "native_record").length, 2, "later frames are still read after the trace stops");
        assert.equal(pane.native, native);
      }
      assert.equal(pane.state, "unknown");
      if (failEvents) {
        assert.ok(observerFailure, "event write failure must disable gate mutation");
        assert.equal(observerFailures, 1, "a failed pane reports its event write failure once, not per frame");
        assert.match(pane.failed!, /event_write_failed/);
      } else {
        const events = store.read("fixture").filter((event) => event.type === "trace_write_failed");
        assert.equal(events.length, 1, "five frames after the failure record trace_write_failed once");
        assert.match(pane.failed!, /^trace_write_failed/, "a later frame must not clear the failure");
        assert.equal(events[0]!.attempt, "attempt");
      }
    }
  } catch (error) { failure = String(error); }
  finally { store.close(); }
  results.push({ scenario, root, failure });
}
writeFileSync(join(output, "results.json"), JSON.stringify({ results }, null, 2) + "\n");
console.log(JSON.stringify(results, null, 2));
process.exitCode = results.some((result) => result.failure) ? 1 : 0;
