// Real CLI + Git/SQLite lifecycle evidence. Only the native thread boundary is controlled; no models.
// Failure modes: reclaim persists ended but loses its event; replay hides that loss;
// manual remove/re-add resets lifecycle; reclaim changes a delivery task; running sessions close.
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { main } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/cli.ts";
import { A2AGates, type GateRuntime } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts";
import { A2AMembership } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/membership.ts";
const root = mkdtempSync("/Volumes/WD-Elements/dev-cache/synara/instances/t044/fixtures/lifecycle-");
const repo = join(root, "repo"), state = join(root, "state");
mkdirSync(repo);
const git = (...args: string[]) => execFileSync("git", ["-C", repo, ...args], {encoding: "utf8",
  env: {...process.env, GIT_CONFIG_NOSYSTEM: "1", GIT_CONFIG_GLOBAL: "/dev/null", GIT_TERMINAL_PROMPT: "0"}}).trim();
git("init"); git("config", "user.name", "T-044 lifecycle"); git("config", "user.email", "t044@example.invalid");
git("config", "commit.gpgsign", "false"); writeFileSync(join(repo,"input.txt"), "Lifecycle sentinel\n");
git("add", "input.txt"); git("-c", "core.hooksPath=/dev/null", "commit", "-m", "Independent fixture");
writeFileSync(join(root,"oracle.py"), "raise SystemExit(0)\n"); writeFileSync(join(root,"instructions.txt"), "Review sentinel.\n");
const threads = new Map<string, any>();
const runtime: GateRuntime = {
  ensureProject: async () => {}, createThread: async () => {}, startThread: async () => {},
  createAttachedThread: async (task, attachment) => { threads.set(attachment.thread_id, {workspace: task.repo,
    provider: attachment.modelSelection.provider, turn: null, running: false, stopped: false, archived: false}); },
  readThread: async thread => structuredClone(threads.get(thread)),
  stopThread: async thread => {threads.get(thread).stopped = true;},
  archiveThread: async thread => {threads.get(thread).archived = true;},
};
async function cli(command: string, ...args: string[]) {
  const argv = ["--state", state, command, "--task", "lifecycle", ...args];
  const original = process.stdout.write;
  let output = "";
  process.stdout.write = function(chunk: any, ...rest: any[]) {
    output += String(chunk); const callback = rest.find(value => typeof value === "function"); callback?.(); return true;
  } as any;
  let exit: number;
  try { exit = await main(argv, runtime); } finally {process.stdout.write = original;}
  const result = JSON.parse(output);
  console.log(JSON.stringify({argv, exit, output: result}));
  return result;
}
console.log(JSON.stringify({fixture_root: root, mode: process.argv[2]}));
assert.equal((await cli("create", "--project", "lifecycle-project", "--title", "Lifecycle sentinel", "--repo", repo,
  "--base", git("rev-parse","HEAD"), "--oracle", join(root,"oracle.py"), "--instructions", join(root,"instructions.txt"))).ok, true);
const attachment = (await cli("attach", "--role", "reviewer", "--model-selection", JSON.stringify({provider: "codex",model:"sentinel",options:{reasoningEffort:"high"}}),
  "--runtime-mode", "approval-required", "--instructions", join(root,"instructions.txt"))).attachment;
const db = new DatabaseSync(join(state, "state.sqlite3"));
if (process.argv[2] === "event") {
  db.exec("CREATE TRIGGER reject_reclaim_event BEFORE INSERT ON events WHEN NEW.type='attachment_reclaimed' BEGIN SELECT RAISE(ABORT,'independent event-write failure'); END");
  const rejected = await cli("reclaim", "--thread", attachment.thread_id);
  assert.equal(rejected.ok, false);
  const persisted = JSON.parse(String(db.prepare("SELECT data FROM attachments WHERE id=?").get(attachment.thread_id)!.data));
  assert.equal(persisted.state, "active", "A failed event write must not commit ended and permit a false successful replay");
  db.exec("DROP TRIGGER reject_reclaim_event");
}
assert.equal((await cli("reclaim", "--thread", attachment.thread_id)).ok, true);
const store = new A2AMembership(state);
const membership = store.list()[0]!;
assert.ok(membership.members[0]!.endedAt);
const events = (await cli("events")).events;
assert.equal(events.filter((event: any) => event.type === "attachment_reclaimed").length, 1);
assert.equal(events.find((event: any) => event.type === "attachment_reclaimed").attempt, null);
assert.equal((await cli("status")).task.state, "ready");
const gates = new A2AGates(state, runtime);
try {
  const removed = gates.saveMembership({...membership, members: []});
  const restored = gates.saveMembership({...removed, members: [{threadId: attachment.thread_id, role: "reviewer"}]});
  assert.equal(restored.members[0]!.endedAt, membership.members[0]!.endedAt, "Re-add must retain the durable ended lifecycle");
} finally {gates.close();store.close();db.close();}
console.log("PASS lifecycle persistence and manual correction");
