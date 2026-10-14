import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { execFileSync } from "node:child_process";
import { OrchestrationStore } from "../src/store.ts";
const { Panes } = await import(process.argv[4] ?? new URL("../src/panes.ts", import.meta.url).href);

const out = resolve(process.argv[2]), materials = resolve(process.argv[3]);
mkdirSync(out);
const approvals = [1, 2, 3].map(n => JSON.parse(readFileSync(join(materials, "approvals", `theme-0${n}.json`), "utf8")));
const screens = [1, 2, 3].map(n => readFileSync(join(materials, `screen-theme-0${n}`, "screen.bin")));
// The answer key is the executor's recorded navigation, not a value derived from screenKey.
assert.deepEqual(approvals.map(a => [a.key, a.selected_label]), [
  ["ArrowUp", "Auto (match terminal)"], ["ArrowDown", "Dark mode"], ["Enter", "Dark mode"],
]);
const checks: any[] = [];
async function test(name: string, body: (f: any) => Promise<void>) {
  const root = mkdtempSync("/tmp/t078-2-theme-domain-"), store = new OrchestrationStore(root);
  const panes = new Panes(root, store, {}, () => {});
  const record: any = { id: "theme-launch", thread: "theme-thread", task: "theme-task", attempt: null,
    session: "native", cli: "Claude Code", role: "controller", authentication: "isolated fake API only", worktree: join(root, "repo") };
  store.launch(record); mkdirSync(join(root, "traces", record.id), { recursive: true });
  const file = join(root, "traces", record.id, "pty.raw"), writes: string[] = [];
  const pane: any = { record, state: "unknown", active: null, failed: null, stopped: false, archived: false,
    writing: false, queue: [], pendingInputs: 0, userDraft: false, writes: Promise.resolve(), pty: { pid: 1,
      write: (s: string) => { assert.ok(store.read().some(e => e.type === "controller_screen_key_intent")); writes.push(s); } } };
  panes.panes.set(record.thread, pane); panes.processInfo = async () => ({ leader: 2, failed: null }) as any;
  const send = (n: number, changes = {}) => {
    const a = approvals[n]; writeFileSync(file, screens[n]);
    return panes.screenKey(record.thread, { key: a.key, purpose: a.purpose, screen_id: a.screen_id,
      selected_label: a.selected_label, screen_base64: screens[n].toString("base64"), authorization_ref: a.approval_ref, ...changes }, "executor");
  };
  try { await body({ send, writes }); checks.push({ name, status: "PASS", written: writes }); }
  catch (error) { checks.push({ name, status: "INCOMPLETE", error: String(error), written: writes }); }
  finally { store.close(); }
}
await test("recorded_08b_target_labels_confirm_dark", async ({ send, writes }) => {
  await send(0); await send(1); await send(2);
  assert.deepEqual(writes, ["\x1b[A", "\x1b[B", "\r"]);
});
await test("direct_default_enter_is_denied_without_write", async ({ send, writes }) => {
  await assert.rejects(send(2), (e: any) => e.code === "theme_selection_not_explicit");
  assert.deepEqual(writes, []);
});
await test("old_pre_key_labels_do_not_authorize_confirmation", async ({ send, writes }) => {
  await send(0, { selected_label: "Dark mode" });
  await send(1, { selected_label: "Auto (match terminal)" });
  await assert.rejects(send(2), (e: any) => e.code === "theme_selection_not_explicit");
  assert.deepEqual(writes, ["\x1b[A", "\x1b[B"]);
});
await test("missing_auto_navigation_is_denied", async ({ send, writes }) => {
  await send(1);
  await assert.rejects(send(2), (e: any) => e.code === "theme_selection_not_explicit");
  assert.deepEqual(writes, ["\x1b[B"]);
});
const result = { status: checks.every(c => c.status === "PASS") ? "PASS" : "INCOMPLETE", checks,
  expected_source: "Controller #109 and the immutable 08b approvals and screen bytes", materials,
  code_revision: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(), argv: process.argv,
  scope: "Domain replay only; synthetic PTY/process identity, no CLI, service or real screen key" };
writeFileSync(join(out, "results.json"), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result)); process.exitCode = result.status === "PASS" ? 0 : 1;
