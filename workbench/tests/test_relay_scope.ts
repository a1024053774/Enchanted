// Independent request-boundary contracts; real relay and SQLite, counted gate
// effects only. Full daemon/CLI coverage is a separate controlled experiment.
// Failure modes: cross-owner ID collision, same-owner duplicate effects,
// payload substitution, replay of a pending intent, or forgotten legacy intent.
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { OrchestrationStore } from "../src/store.ts";
const [modulePath, output] = process.argv.slice(2);
assert(modulePath && output && process.argv.length === 4);
mkdirSync(output);
const { RequestRelay } = await import(pathToFileURL(modulePath).href);
const results: any[] = [];
const first = { id: "launch-one", task: "fixture", attempt: "attempt-one", session: "session-one", fence: 1, spec_rev: 1, role: "worker" };
const next = { id: "launch-two", task: "fixture", attempt: "attempt-two", session: "session-two", fence: 2, spec_rev: 1, role: "worker" };
function input(binding: any, request_id = "delivery", commit = "a".repeat(40)) {
  const { id: _id, role: _role, ...identity } = binding;
  return { schema: 1, request_id, command: "submit", ...identity, commit };
}
function file(value: any, name = "delivery.json") { return { name, raw: JSON.stringify(value) }; }
async function check(name: string, body: (relay: any, store: any, effects: any[], perform: any) => Promise<void>) {
  const root = mkdtempSync("/tmp/t077-relay-scope-");
  const store = new OrchestrationStore(root), relay = new RequestRelay(store), effects: any[] = [];
  const perform = async (command: any) => { effects.push(command); return { ok: true, applied: command.commit }; };
  let failure: any = null;
  try { await body(relay, store, effects, perform); }
  catch (error) { failure = { assertion: error instanceof assert.AssertionError, text: String(error) }; }
  const tables = Object.fromEntries(["relay_requests", "relay_results"].map((name) => [name, store.db.prepare("SELECT * FROM " + name).all()]));
  results.push({ name, root, pass: !failure, failure, effects, tables, events: store.read() });
  store.close();
}
await check("new_attempt_same_id_is_new_delivery", async (relay, store, effects, perform) => {
  assert.equal((await relay.receive(first, file(input(first)), true, perform)).result.ok, true);
  const original = store.db.prepare("SELECT * FROM relay_requests WHERE launch=?").get(first.id);
  const delivered = await relay.receive(next, file(input(next, "delivery", "b".repeat(40))), true, perform);
  assert.equal(delivered.result.ok, true, "A new attempt's explicit delivery is a new request");
  assert.equal(delivered.replayed, false); assert.equal(effects.length, 2);
  assert.deepEqual(store.db.prepare("SELECT * FROM relay_requests WHERE launch=?").get(first.id), original);
  const replay = await relay.receive(next, file(input(next, "delivery", "b".repeat(40)), "copy.json"), true, perform);
  assert.equal(replay.replayed, true); assert.equal(effects.length, 2);
  assert.deepEqual(replay.result, delivered.result);
});
await check("another_task_same_id_is_independent", async (relay, _store, effects, perform) => {
  const other = { ...next, task: "other-task", fence: 1 };
  await relay.receive(first, file(input(first)), true, perform);
  assert.equal((await relay.receive(other, file(input(other)), true, perform)).result.ok, true);
  assert.equal(effects.length, 2);
});
await check("same_launch_duplicate_change_and_pending_are_fenced", async (relay, _store, effects, perform) => {
  const request = input(first);
  const delivered = await relay.receive(first, file(request), true, perform);
  const replay = await relay.receive(first, file(request, "copy.json"), true, perform);
  assert.equal(replay.replayed, true); assert.deepEqual(replay.result, delivered.result); assert.equal(effects.length, 1);
  const changed = file(input(first, "delivery", "c".repeat(40)));
  assert.equal((await relay.receive(first, changed, true, perform)).result.error, "relay_request_id_reused");
  assert.equal((await relay.receive(first, changed, true, perform)).replayed, true);
  assert.equal(effects.length, 1);
  let finish!: (value: any) => void;
  const pending = input(first, "pending");
  const running = relay.receive(first, file(pending), true, async (command: any) => {
    effects.push(command); return new Promise((resolve) => { finish = resolve; });
  });
  assert.equal((await relay.receive(first, file(pending), true, perform)).result.error, "relay_outcome_unknown");
  assert.equal(effects.length, 2); finish({ ok: true }); await running;
});
await check("legacy_result_and_pending_intent_remain_authoritative", async (relay, store, effects, perform) => {
  const legacy = (id: string, result: any) => {
    const request = input(first, id), key = "id:" + id;
    const canonical = JSON.stringify(Object.fromEntries(Object.keys(request).sort().map((key) => [key, (request as any)[key]])));
    store.db.prepare("INSERT INTO relay_requests(key,launch,task,attempt,request_id,input,created_at) VALUES (?,?,?,?,?,?,?)")
      .run(key, first.id, first.task, first.attempt, id, canonical, "recorded-before-upgrade");
    if (result) store.db.prepare("INSERT INTO relay_results(key,data,created_at) VALUES (?,?,?)")
      .run(key, JSON.stringify(result), "recorded-before-upgrade");
    return request;
  };
  const complete = legacy("old-complete", { ok: true, receipt: "original-result" });
  const pending = legacy("old-pending", null);
  assert.deepEqual((await relay.receive(first, file(complete), true, perform)).result, { ok: true, receipt: "original-result" });
  assert.equal((await relay.receive(first, file(pending), true, perform)).result.error, "relay_outcome_unknown");
  assert.equal(effects.length, 0, "Existing intents must not execute again after the key fix");
  assert.equal(store.db.prepare("SELECT count(*) AS n FROM relay_requests").get().n, 2);
});
await check("foreign_payload_is_not_old_success", async (relay, _store, effects, perform) => {
  await relay.receive(first, file(input(first)), true, perform);
  const wrong = await relay.receive(next, file(input(first)), true, perform);
  assert.equal(wrong.result.ok, false); assert.equal(effects.length, 1);
});
const report = { status: results.every((r) => r.pass) ? "PASS" : "INCOMPLETE", module: modulePath,
  scope: "Controlled request boundary with counted effects; not provider or daemon evidence", argv: process.argv,
  tests: results, real_codex_turns: 0 };
writeFileSync(join(output, "run.json"), JSON.stringify(report, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify({ status: report.status, tests: results.map(({ name, pass, failure }) => ({ name, pass, failure })) }));
process.exitCode = report.status === "PASS" ? 0 : 1;
