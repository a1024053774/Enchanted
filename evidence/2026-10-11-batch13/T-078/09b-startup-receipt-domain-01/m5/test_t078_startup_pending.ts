// Main #308 regression: startup keys are permitted while one inbox item waits.
// Real Panes/store and captured A14 screens; PTY/process boundaries are spies.
import assert from "node:assert/strict";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";
import { OrchestrationStore } from "../src/store.ts";
import { Panes } from "../src/panes.ts";
import { A2AGates } from "../src/gates/core.ts";

const out = resolve(process.argv[2]), materials = resolve(process.argv[3]);
mkdirSync(out);
const fixture = JSON.parse(readFileSync(join(materials, "fixture.json"), "utf8"));
assert.deepEqual(fixture.frames.map((frame: any) => [frame.key, frame.purpose, frame.selected_label]), [
  ["ArrowUp", "onboarding-theme", "Auto (match terminal)"], ["ArrowDown", "onboarding-theme", "Dark mode"],
  ["Enter", "onboarding-theme", "Dark mode"], ["Enter", "onboarding-notice", "Continue"],
  ["ArrowDown", "workspace-trust", "Yes, I trust this folder"], ["Enter", "workspace-trust", "Yes, I trust this folder"],
]);
const checks: any[] = [];
async function test(name: string, body: (value: any) => Promise<void>) {
  const root = mkdtempSync("/private/tmp/t078-2-startup-domain-"), store = new OrchestrationStore(root);
  const panes = new Panes(root, store, {}, () => {});
  const gates = new A2AGates(root, panes);
  const record: any = { id: randomUUID(), thread: randomUUID(), task: "startup-pending-domain", attempt: null,
    session: randomUUID(), cli: "Claude Code", role: "controller", preset: "executor", turn_limit: 6,
    authentication: "isolated fake API only", worktree: join(root, "repo") };
  store.launch(record);
  const original = fixture.state.queue[0];
  const queued = store.register(record.id, original.text.slice(original.text.indexOf("\n") + 1), "inbox", undefined,
                                { id: original.inbox_entry, sender: "ideation" });
  const entry = fixture.entry;
  assert.equal(entry.id, original.inbox_entry);
  gates.db.prepare("INSERT INTO inbox_records(id,data) VALUES (?,?)").run(entry.id, JSON.stringify(entry));
  gates.db.prepare("INSERT INTO inbox_deliveries(entry,data) VALUES (?,?)").run(entry.id, JSON.stringify({
    entry_id: entry.id, state: "queued", thread: record.thread, message: queued.id, created_at: queued.registered_at,
  }));
  const file = join(root, "traces", record.id, "pty.raw"); mkdirSync(join(root, "traces", record.id), { recursive: true });
  const writes: string[] = [];
  const pane: any = { record, state: "unknown", active: null, failed: null, stopped: false, archived: false, writing: false,
    queue: [queued], pendingInputs: 0, userDraft: false, interrupted: false, inputGeneration: 0,
    native: record.session, turn: null, writes: Promise.resolve(), pty: { pid: 1, write: (text: string) => writes.push(text) } };
  panes.panes.set(record.thread, pane);
  panes.processInfo = async () => ({ leader: 2, failed: null }) as any;
  const screen = readFileSync(join(materials, "executor-s1.bin")); writeFileSync(file, screen);
  const input = { screen_id: "executor-s1", key: "ArrowUp", purpose: "onboarding-theme",
    selected_label: "Auto (match terminal)", screen_base64: screen.toString("base64"), authorization_ref: "Main #308 offline captured-screen replay" };
  const send = (changes = {}, source = "executor") => panes.screenKey(record.thread, { ...input, ...changes }, source);
  const receiptRefreshes: any[] = [];
  const assertQueuedReceipt = async (label: string) => {
    // Use the gate's real refresh path, not the old unrefreshed queued row.
    const refreshed = await gates.inboxDeliveryStatus(entry.id);
    const history = gates.db.prepare("SELECT data FROM inbox_deliveries WHERE entry=? ORDER BY seq").all(entry.id)
      .map(row => JSON.parse(String(row.data)));
    const i2 = store.read().filter(event => (event.type === "relay_feedback_intent" && event.data.entry_id === entry.id) ||
      (event.type === "dispatch_queued" && event.data.source === "gate"));
    receiptRefreshes.push({ label, entry_id: entry.id, refreshed, history, i2, state: pane.state,
      active: pane.active, queue: pane.queue.map((item: any) => item.id), writes: [...writes] });
    assert.equal(refreshed?.entry_id, entry.id, "refresh queries the original inbox entry");
    assert.equal(refreshed?.thread, record.thread); assert.equal(refreshed?.message, queued.id);
    assert.equal(refreshed?.state, "queued", "startup refreshed receipt remains queued: " + label);
    assert.equal(history.filter(row => row.state === "delivered").length, 0, "startup has no delivered history: " + label);
    assert.equal(i2.length, 0, "startup has no I2: " + label);
  };
  try {
    await body({ pane, panes, gates, store, record, queued, entry, writes, send, file, assertQueuedReceipt });
    checks.push({ name, status: "PASS", writes, queue: pane.queue.map((item: any) => item.id), state: pane.state, receipt_refreshes: receiptRefreshes });
  } catch (error) {
    checks.push({ name, status: "INCOMPLETE", error: String(error), code: (error as any).code, writes,
      queue: pane.queue.map((item: any) => item.id), state: pane.state, receipt_refreshes: receiptRefreshes });
  } finally {
    gates.close();
    store.db.exec("PRAGMA wal_checkpoint(TRUNCATE)"); store.close();
    const saved = join(out, name); mkdirSync(saved);
    for (const suffix of ["", "-wal", "-shm"]) {
      const path = join(root, "state.sqlite3" + suffix);
      if (existsSync(path)) copyFileSync(path, join(saved, "state.sqlite3" + suffix));
    }
    rmSync(root, { recursive: true });
  }
}

await test("unknown_with_one_inbox_allows_exact_ArrowUp_without_drain", async ({ pane, panes, queued, writes, send, store, assertQueuedReceipt }) => {
  await send();
  await assertQueuedReceipt("single ArrowUp");
  assert.deepEqual(writes, ["\x1b[A"]); assert.equal(pane.state, "unknown"); assert.equal(pane.active, null);
  assert.deepEqual(pane.queue.map((item: any) => item.id), [queued.id]);
  await panes.drain(pane); assert.deepEqual(writes, ["\x1b[A"]);
  assert.equal(store.read().filter(event => ["paste_intent", "turn_submit_intent", "turn_submitted"].includes(event.type)).length, 0);
});
await test("six_onboarding_keys_hold_inbox_until_initial_release", async ({ pane, panes, gates, queued, entry, writes, store, record, file, send, assertQueuedReceipt }) => {
  for (const [index, frame] of fixture.frames.entries()) {
    const raw = readFileSync(join(materials, frame.file)); writeFileSync(file, raw);
    await send({ screen_id: "recorded-s" + (index * 2 + 1), key: frame.key, purpose: frame.purpose,
                 selected_label: frame.selected_label, authorization_ref: frame.approval_ref, screen_base64: raw.toString("base64") });
    await assertQueuedReceipt("key " + index);
    assert.equal(pane.state, "unknown"); assert.equal(pane.active, null);
    assert.deepEqual(pane.queue.map((item: any) => item.id), [queued.id]);
  }
  const onboarding = ["\x1b[A", "\x1b[B", "\r", "\r", "\x1b[B", "\r"];
  assert.deepEqual(writes, onboarding); await panes.drain(pane); assert.deepEqual(writes, onboarding);
  assert.equal(store.read().filter(event => ["paste_intent", "turn_submit_intent", "turn_submitted"].includes(event.type)).length, 0);
  await panes.release(record.thread, "Main #308: all six captured startup screens reviewed");
  assert.deepEqual(writes, [...onboarding, "\x1b[200~" + queued.text + "\x1b[201~", "\r"]);
  assert.equal(pane.state, "busy"); assert.equal(pane.active.dispatch, queued.id); assert.equal(pane.queue.length, 0);
  assert.equal(store.read().filter(event => event.type === "turn_submit_intent").length, 1);
  assert.equal(store.read().filter(event => event.type === "turn_submitted").length, 1);
  assert.equal((await gates.inboxDeliveryStatus(entry.id))?.state, "delivered", "release refresh confirms the actual submission");
  await assert.rejects(send({ screen_id: "after-release" }), (error: any) => error.code === "screen_requires_startup");
});

for (const [name, patch] of [
  ["busy", { state: "busy" }], ["idle", { state: "idle" }], ["active", { active: { id: "active-submission" } }],
  ["failed", { failed: "runtime failure" }], ["stopped", { stopped: true }], ["archived", { archived: true }],
  ["writing", { writing: true }], ["draft", { userDraft: true }], ["pending_input", { pendingInputs: 1 }],
] as const) await test("queued_" + name + "_still_denied", async ({ pane, send, writes }) => {
  Object.assign(pane, patch);
  await assert.rejects(send(), (error: any) => error.code === "screen_requires_startup"); assert.deepEqual(writes, []);
});
await test("state_change_during_identity_check_is_denied", async ({ pane, panes, send, writes }) => {
  panes.processInfo = async () => { pane.userDraft = true; return { leader: 2, failed: null }; };
  await assert.rejects(send(), (error: any) => error.code === "screen_requires_startup"); assert.deepEqual(writes, []);
});
await test("queue_does_not_bypass_executor_approval", async ({ send, writes }) => {
  await assert.rejects(send({}, "user"), (error: any) => error.code === "screen_operator_required"); assert.deepEqual(writes, []);
});
await test("queue_does_not_bypass_screen_bytes", async ({ send, file, writes }) => {
  writeFileSync(file, "different screen");
  await assert.rejects(send(), (error: any) => error.code === "screen_changed"); assert.deepEqual(writes, []);
});
await test("queue_does_not_bypass_foreground_check", async ({ panes, send, writes }) => {
  panes.processInfo = async () => ({ leader: null, failed: null });
  await assert.rejects(send(), (error: any) => error.code === "foreground_claude_required"); assert.deepEqual(writes, []);
});
const result = { status: checks.every(check => check.status === "PASS") ? "PASS" : "INCOMPLETE", checks,
  base_revision: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
  product_diff: execFileSync("git", ["diff", "HEAD", "--", "workbench/src/panes.ts"], { encoding: "utf8" }), argv: process.argv,
  expected_source: "Main #308; actual A14 queue state and recorded A14 signed onboarding screens",
  scope: "Domain replay only; real Panes/store, PTY and identity spies; no daemon/API/CLI/window/key/model process",
  scratch_removed: true };
writeFileSync(join(out, "results.json"), JSON.stringify(result, null, 2) + "\n");
console.log(JSON.stringify({ status: result.status, checks: checks.length, failed: checks.filter(check => check.status !== "PASS") }));
process.exitCode = result.status === "PASS" ? 0 : 1;
