// T-123 migration, gate library only (no daemon, no CLI): the states a start can meet. Expected ids follow the
// ticket's rule `<project>+<old id>`, the project taken from the row's own record.
// Usage: node --experimental-strip-types tests/test_t123_migration_resume.ts OUTPUT.json [CORE_TS]
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { pathToFileURL } from "node:url";

const [output, core = resolve(import.meta.dirname, "../src/gates/core.ts")] = process.argv.slice(2);
const { A2AGates } = await import(pathToFileURL(resolve(core)).href);
// The daemon's own store and relay create their tables, as a real library has them.
const { OrchestrationStore } = await import(pathToFileURL(resolve(core, "../../store.ts")).href);
const { RequestRelay } = await import(pathToFileURL(resolve(core, "../../relay.ts")).href);
const checks: string[] = [];
const result: Record<string, unknown> = { status: "INCOMPLETE", core, checks };

function library(tasks: Array<[string, string]>, memberships: Array<[string, string]>, relay?: string) {
  const root = mkdtempSync("/tmp/t123-migration-");
  const store = new OrchestrationStore(root);
  new RequestRelay(store);
  new A2AGates(root).close();
  store.close();
  const state = new DatabaseSync(join(root, "state.sqlite3"));
  for (const [id, project] of tasks)
    state.prepare("INSERT INTO tasks VALUES (?,?)").run(id, JSON.stringify({ task_id: id, project_id: project, title: id, state: "registered", current_attempt: null }));
  if (relay !== undefined)
    state.prepare("INSERT INTO relay_requests VALUES (?,?,?,?,?,?,?)").run("k", "launch", relay, "attempt", "request",
      JSON.stringify({ schema: 1, command: "submit", task: relay }), "2026-10-22T00:00:00Z");
  state.close();
  const membership = new DatabaseSync(join(root, "membership.sqlite3"));
  for (const [id, project] of memberships)
    membership.prepare("INSERT INTO memberships VALUES (?,?)").run(id, JSON.stringify({ taskId: id, projectId: project, title: id, revision: 0 }));
  membership.close();
  return root;
}
function read(root: string) {
  const state = new DatabaseSync(join(root, "state.sqlite3"), { readOnly: true });
  const membership = new DatabaseSync(join(root, "membership.sqlite3"), { readOnly: true });
  const value = {
    tasks: state.prepare("SELECT id, data FROM tasks ORDER BY id").all().map(row => [row.id, JSON.parse(String(row.data)).task_id]),
    relay: state.prepare("SELECT task, input FROM relay_requests").all().map(row => [row.task, JSON.parse(String(row.input)).task]),
    memberships: membership.prepare("SELECT id, data FROM memberships ORDER BY id").all().map(row => [row.id, JSON.parse(String(row.data)).taskId]),
  };
  state.close(); membership.close();
  return value;
}
function check(name: string, run: () => void) { run(); checks.push(name); }

try {
  // 1: a library written before T-123: a task with its membership and a relay request.
  const old = library([["T-0", "p"]], [["T-0", "p"]], "T-0");
  new A2AGates(old).close();
  const migrated = read(old);
  result.old = migrated;
  check("old_library_migrated", () => assert.deepEqual(migrated, {
    tasks: [["p+T-0", "p+T-0"]], relay: [["p+T-0", "p+T-0"]], memberships: [["p+T-0", "p+T-0"]] }));
  // 2: a start interrupted after the task library committed and before the membership library did.
  const interrupted = library([["p+T-0", "p"]], [["T-0", "p"]]);
  new A2AGates(interrupted).close();
  const resumed = read(interrupted);
  result.interrupted = resumed;
  check("interrupted_migration_finished_on_next_start", () => assert.deepEqual(resumed.memberships, [["p+T-0", "p+T-0"]]));
  // 3: a later start finds nothing to migrate and changes nothing.
  new A2AGates(interrupted).close();
  check("second_start_changes_nothing", () => assert.deepEqual(read(interrupted), resumed));
  result.status = "PASS";
} catch (error) {
  result.error = String(error);
}
writeFileSync(output, JSON.stringify(result, null, 2) + "\n");
process.exitCode = result.status === "PASS" ? 0 : 1;
