// Isolated failure injection: a PTY callback cannot safely be made to fail in a
// paid model run. Cover trace I/O failure and trace+event-store failure separately.
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync } from "node:fs";
import { join } from "node:path";
import { createRequire } from "node:module";
import { Panes } from "../src/panes.ts";
import { OrchestrationStore } from "../src/store.ts";

const require = createRequire(import.meta.url);
const output = process.argv[2]!;
mkdirSync(output, { recursive: false });
const results = [];
for (const failEvents of [false, true]) {
  const root = mkdtempSync("/tmp/a2a-trace-failure-");
  const home = join(root, "isolated"); mkdirSync(home);
  const executable = join(root, "codex-version");
  writeFileSync(executable, '#!/bin/sh\nprintf "codex-cli 0.162.1\\n"\n'); chmodSync(executable, 0o755);
  const role = join(root, "role.txt"); writeFileSync(role, "fixture worker");
  let onData: (data: string) => void = () => { throw Error("callback missing"); };
  require.cache[require.resolve("node-pty")] = { exports: { spawn: () => ({
    pid: 123, onData: (callback: typeof onData) => { onData = callback; }, onExit: () => {}, write: () => {},
  }) } } as any;
  const store = new OrchestrationStore(root);
  let observerFailure: unknown = null;
  const panes = new Panes(root, store, { codex_bin: executable, codex_home: home, role_card: role,
    code_revision: "fixture", role_card_revision: "fixture", hook_authorization: "test-only", turn_limit: 1 },
    (error: unknown) => { observerFailure = error; });
  let failure: string | null = null;
  try {
    await panes.createThread({ task_id: "fixture", project_id: "fixture", card: { executor: { cli: "Codex", model: "gpt-6-astra", effort: "xhigh" } } } as any,
      { task_id: "fixture", attempt_id: "attempt", session_id: "session", fence: 1, spec_rev: 1,
        runtime_mode: "workspace-write", thread_id: "thread", workspace: root, base_commit: "baseline" } as any);
    const pane = panes.get("thread");
    mkdirSync(join(root, "traces", pane.record.id, "pty.raw")); // appendFile fails with EISDIR.
    if (failEvents) store.db.exec("PRAGMA query_only=ON");
    onData("trace must be recorded");
    assert.equal(pane.state, "unknown");
    if (failEvents) {
      assert.ok(observerFailure, "event write failure must disable gate mutation");
      assert.match(pane.failed!, /event_write_failed/);
    } else {
      const events = store.read("fixture").filter((event) => event.type === "trace_write_failed");
      assert.equal(events.length, 1, "trace failure must be an append-only event");
      assert.equal(events[0]!.attempt, "attempt");
    }
  } catch (error) { failure = String(error); }
  finally { store.close(); }
  results.push({ failEvents, root, failure });
}
writeFileSync(join(output, "results.json"), JSON.stringify({ results }, null, 2) + "\n");
console.log(JSON.stringify(results, null, 2));
process.exitCode = results.some((result) => result.failure) ? 1 : 0;
