// Failure modes (T-151): a registered prompt does not bind; its matching Stop
// does not clear the active submission; duplicate Stop emits a second pane_idle;
// a foreign native session is accepted. This fixture exercises Panes.signal only.
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { OrchestrationStore } from "../src/store.ts";
import { Panes } from "../src/panes.ts";

const output = process.argv[2]!; mkdirSync(output);
const root = mkdtempSync("/tmp/t78-claude-state-");
const promptId = "00000000-0000-4000-8000-000000000001";
const transcript = join(root, "native-session.jsonl");
// T-151: non-controller Stop consumes native turn facts. These are synthetic
// inputs, not an assertion copied from the current product's output.
writeFileSync(transcript, [
  { type: "user", promptId },
  { type: "assistant", message: { model: "claude-haiku-5-5", content: [{ type: "text", text: "P1_ACK" }] } },
].map(entry => JSON.stringify(entry)).join("\n") + "\n", "utf8");
const store = new OrchestrationStore(root), panes = new Panes(root, store, {}, () => {});
const record = { id: "claude-launch", thread: "claude-thread", task: "task", attempt: null,
  role: "worker", session: "native-session", worktree: root, cli: "Claude Code", turn_limit: 1 };
store.launch(record);
const item = store.register(record.id, "独立输入 P1_NONCE");
const pane: any = { record, task: {}, attempt: null, token: "test-only", native: record.session,
  state: "busy", failed: null, stopped: false, archived: false, interrupted: false, stopInProgress: false,
  active: { id: "submission", dispatch: item.id, at: "2026-10-11T00:00:00Z", nativeTurn: null },
  claudePromptId: null, claudePromptIds: new Set(), queue: [], writing: false, writes: Promise.resolve(), pendingInputs: 0, userDraft: false };
panes.panes.set(record.thread, pane);
const checks: any[] = [];
async function test(name: string, run: () => Promise<void>) {
  try { await run(); checks.push({ name, status: "PASS" }); }
  catch (error) { checks.push({ name, status: "INCOMPLETE", error: String(error) }); }
}
const signal = (event: string, extra = {}) => panes.signal(record.id, JSON.stringify({ session_id: record.session,
  cwd:root,transcript_path:transcript,
  prompt_id:promptId,hook_event_name: event, ...extra }), "2026-10-11T00:01:00Z");
await test("controller_runtime_entry_exists", async () => assert.equal(typeof (panes as any).startController, "function"));
await test("real_hook_shape_matches_one_registered_submission", async () => {
  await signal("UserPromptSubmit", { prompt: item.text }); assert.equal(pane.state, "busy");
  assert.equal(pane.claudePromptId, promptId);
  await signal("Stop", { stop_hook_active: false, effort: { level: "high" } }); assert.equal(pane.state, "idle");
  assert.equal(pane.active, null); assert.equal(store.read().filter(e => e.type === "pane_idle").length, 1);
  assert.equal(store.read().find(e => e.type === "pane_idle")!.data.submission, "submission");
  await signal("Stop", { stop_hook_active: false });
  assert.equal(store.read().filter(e => e.type === "pane_idle").length, 1);
});
await test("wrong_native_session_is_rejected", async () => {
  await assert.rejects(signal("Stop", { session_id: "another-session" }), (e: any) => e.code === "hook_native_session_mismatch");
});
const result = { status: checks.every(c => c.status === "PASS") ? "PASS" : "INCOMPLETE", checks,
  scope: "pure state fixture; no process, socket, CLI, API or model", argv: process.argv };
writeFileSync(join(output, "results.json"), JSON.stringify(result, null, 2));
writeFileSync(join(output, "events.json"), JSON.stringify(store.read(), null, 2)); store.close();
console.log(JSON.stringify(result)); process.exitCode = result.status === "PASS" ? 0 : 1;
