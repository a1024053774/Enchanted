// Independent requirements: wrong identity/incomplete files never reach the gate;
// repeated or in-flight requests never execute twice. No model/runtime is mocked
// as successful: this is only the request boundary, paired with real CLI/E2E runs.
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { OrchestrationStore } from "../src/store.ts";
const { RequestRelay } = await import(process.env.A2A_RELAY_MODULE ?? "../src/relay.ts");

const output = process.argv[2]!; mkdirSync(output);
const root = mkdtempSync("/tmp/a2a-relay-core-");
const store = new OrchestrationStore(root); const relay = new RequestRelay(store);
const binding = { id: "launch", task: "fixture", attempt: "attempt", session: "session", fence: 1, spec_rev: 1 };
const base = { schema: 1, request_id: "delivery", command: "submit", task: "fixture", attempt: "attempt",
  session: "session", fence: 1, spec_rev: 1, commit: "a".repeat(40) };
const file = (value: any, name = "request.json") => ({ name, raw: JSON.stringify(value) });
const effects: any[] = [];
const perform = async (value: any) => { effects.push(value); return { ok: true, command: value.command }; };
let failure: string | null = null;
try {
  const original = await relay.receive(binding, file(base), true, perform);
  assert.equal(original.result.ok, true);
  assert.equal(effects.length, 1);
  const duplicate = await relay.receive(binding, file(base, "copy.json"), true, perform);
  assert.equal(duplicate.replayed, true);
  assert.equal(effects.length, 1, "a repeated request must not execute again");
  assert.deepEqual(duplicate.result, original.result);
  const mismatch = await relay.receive(binding, file({ ...base, request_id: "wrong-identity", fence: 2 }), true, perform);
  assert.equal(mismatch.result.error, "relay_identity_mismatch");
  const incomplete = { ...base, request_id: "incomplete" }; delete (incomplete as any).commit;
  assert.equal((await relay.receive(binding, file(incomplete), true, perform)).result.error, "invalid_relay_request");
  assert.equal((await relay.receive(binding, { name: "partial.json", raw: '{"schema":' }, true, perform)).result.error, "invalid_relay_request");
  assert.equal(effects.length, 1, "invalid files must not reach the gate");
  const changedFile = file({ ...base, commit: "b".repeat(40) });
  const changed = await relay.receive(binding, changedFile, true, perform);
  assert.equal(changed.result.error, "relay_request_id_reused");
  assert.equal(changed.replayed, false, "a changed request needs one explicit refusal notice");
  assert.equal((await relay.receive(binding, changedFile, true, perform)).replayed, true, "the same refusal must not start a notice loop");
  assert.equal((await relay.receive(binding, file({ ...base, request_id: "old-stop" }), false, perform)).result.error, "relay_requires_current_stop");
  assert.equal(effects.length, 1);
  assert.equal((await relay.receive(binding, file({ ...base, request_id: "old-stop" }), true, perform)).result.ok, true,
    "a stale Stop must not consume a request intended for the current Stop");
  const { commit: _commit, ...common } = base;
  assert.equal((await relay.receive(binding, file({ ...common, command: "status", request_id: "read-status" }), true, perform)).result.ok, true);
  assert.equal((await relay.receive(binding, file({ ...common, command: "issue", request_id: "report-issue", title: "Test issue", body: "Fixture only", blocking: false, refs: [] }), true, perform)).result.ok, true);
  let complete!: (value: any) => void;
  const pending = { ...base, request_id: "in-flight" };
  const first = relay.receive(binding, file(pending), true, async (value: any) => {
    effects.push(value); return await new Promise((resolve) => { complete = resolve; });
  });
  const replay = await relay.receive(binding, file(pending), true, perform);
  assert.equal(replay.result.error, "relay_outcome_unknown");
  assert.equal(effects.length, 5, "an in-flight transfer must not execute again");
  complete({ ok: true }); await first;
  const events = store.read("fixture");
  assert.ok(events.some((event) => event.type === "relay_replayed"));
  assert.ok(events.some((event) => event.type === "relay_rejected" && event.data.result.error === "relay_identity_mismatch"));
  assert.ok(events.some((event) => event.type === "relay_rejected" && event.data.result.error === "invalid_relay_request"));
  for (const table of ["relay_requests", "relay_results"]) {
    assert.throws(() => store.db.exec(`UPDATE ${table} SET ${table === "relay_requests" ? "input" : "data"}='{}'`), /append only/);
    assert.throws(() => store.db.exec(`DELETE FROM ${table}`), /append only/);
  }
} catch (error) { failure = String(error); }
writeFileSync(join(output, "results.json"), JSON.stringify({ root, failure, effects, events: store.read("fixture") }, null, 2) + "\n");
store.close(); console.log(JSON.stringify({ root, failure, effect_count: effects.length }));
process.exitCode = failure ? 1 : 0;
