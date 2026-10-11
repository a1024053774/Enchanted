// Isolated state contract. Real PTY delivery and initial release were observed
// in outside-probe-01; this test injects races without paid model turns.
// Failures: unknown/busy write, registration after bytes, duplicate/stale Stop,
// auxiliary identity unlocking, or writing after a durable recorder failure.
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync, appendFileSync } from "node:fs";
import { join } from "node:path";
import { createRequire } from "node:module";
const { Panes } = await import(process.env.A2A_PANE_MODULE ?? "../src/panes.ts");
import { OrchestrationStore } from "../src/store.ts";

const require = createRequire(import.meta.url);
const output = process.argv[2]!; mkdirSync(output);
const root = mkdtempSync("/tmp/a2a-pane-state-");
const home = join(root, "isolated"); mkdirSync(join(home, "sessions"), { recursive: true });
const executable = join(root, "version"); writeFileSync(executable, '#!/bin/sh\nprintf "codex-cli 0.162.1\\n"\n'); chmodSync(executable, 0o755);
const role = join(root, "role.txt"); writeFileSync(role, "test role");
const store = new OrchestrationStore(root);
const writes: { data: string; registrations: number; submitIntents: number }[] = [];
require.cache[require.resolve("node-pty")] = { exports: { spawn: () => ({ pid: 123,
  onData: () => {}, onExit: () => {}, write: (data: string) => {
    writes.push({ data, registrations: Number(store.db.prepare("SELECT count(*) AS n FROM dispatch_records").get()!.n),
      submitIntents: Number(store.db.prepare("SELECT count(*) AS n FROM orchestration_events WHERE type='turn_submit_intent'").get()!.n) });
  },
}) } } as any;
const panes = new Panes(root, store, { codex_bin: executable, codex_home: home, role_card: role,
  code_revision: "fixture", role_card_revision: "fixture", hook_authorization: "fixture", turn_limit: 2 }, () => {});
let failure: string | null = null;
let sending: Promise<void> | undefined;
try {
  await panes.createThread({ task_id: "fixture", project_id: "fixture", card: { executor: { cli: "Codex", model: "gpt-6-astra", effort: "xhigh" } } } as any,
    { attempt_id: "attempt", session_id: "session", thread_id: "thread", runtime_mode: "workspace-write", workspace: root } as any);
  const pane = panes.get("thread");
  await panes.dispatch(pane, "第一条\n有两行");
  assert.equal(writes.length, 0, "unknown state queues without bytes");
  pane.state = "idle"; // Fixture state; not a substitute for the production process-info release.
  sending = panes.drain(pane);
  assert.equal(panes.status("thread").writing, true, "paste/CR transaction remains visible while writing");
  assert.equal((await panes.readThread("thread")).running, true, "a pane being written cannot be reclaimed as idle");
  await sending;
  assert.deepEqual(writes.map((row) => row.data), ["\x1b[200~⟦主控 #1⟧\n第一条\n有两行\x1b[201~", "\r"]);
  assert.equal(writes[0]!.registrations, 1);
  assert.equal(writes[1]!.submitIntents, 1);
  assert.equal(pane.state, "busy");
  await panes.dispatch(pane, "第二条");
  assert.equal(writes.length, 2, "busy queues even before start hook arrives");
  const native = join(home, "sessions", "rollout-native.jsonl");
  writeFileSync(native, JSON.stringify({ type: "session_meta", payload: { source: "cli", id: "native", cwd: root } }) + "\n"
    + JSON.stringify({ type: "event_msg", payload: { type: "task_started", turn_id: "turn-1" } }) + "\n");
  const signal = (event: string, turn: string, session = "native") => panes.signal(pane.record.id,
    JSON.stringify({ session_id: session, turn_id: turn, hook_event_name: event }), new Date().toISOString());
  await signal("UserPromptSubmit", "turn-1");
  assert.equal(pane.state, "busy");
  await assert.rejects(signal("Stop", "turn-1", "auxiliary"));
  assert.equal(pane.state, "busy");
  await signal("Stop", "stale-turn");
  assert.equal(pane.state, "busy");
  let finishTransfer!: () => void;
  const stopPayload = JSON.stringify({ session_id: "native", turn_id: "turn-1", hook_event_name: "Stop" });
  const firstStop = panes.signal(pane.record.id, stopPayload, new Date().toISOString(), async (_pane: any, _stop: any, matched: boolean) => {
    assert.equal(matched, true);
    await new Promise<void>((resolve) => { finishTransfer = resolve; });
  });
  let duplicateMatched: boolean | null = null;
  await panes.signal(pane.record.id, stopPayload, new Date().toISOString(), async (_pane: any, _stop: any, matched: boolean) => { duplicateMatched = matched; });
  assert.equal(duplicateMatched, false, "a concurrent Stop cannot own the active transfer");
  assert.equal(pane.state, "busy", "the first transfer still owns completion");
  finishTransfer(); await firstStop;
  assert.equal(pane.state, "idle");
  await panes.drain(pane);
  appendFileSync(native, JSON.stringify({ type: "event_msg", payload: { type: "task_started", turn_id: "turn-2" } }) + "\n");
  await signal("Stop", "turn-1");
  assert.equal(pane.state, "busy", "old Stop cannot unlock the new submission");
  await signal("Stop", "turn-2");
  assert.equal(pane.state, "idle");
  const before = writes.length;
  store.db.exec("PRAGMA query_only=ON");
  await assert.rejects(panes.dispatch(pane, "不得写入"));
  assert.equal(writes.length, before, "failed registration cannot send bytes");
} catch (error) { failure = String(error); }
try { if (sending) await sending; }
catch (error) { failure = `${failure ?? ""}; pending write: ${String(error)}`; }
writeFileSync(join(output, "results.json"), JSON.stringify({ root, failure, writes, events: store.read("fixture") }, null, 2) + "\n");
store.close();
console.log(JSON.stringify({ root, failure }));
process.exitCode = failure ? 1 : 0;
