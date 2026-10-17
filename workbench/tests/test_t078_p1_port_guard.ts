import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, realpathSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { createRequire } from "node:module";
import { Panes } from "../src/panes.ts";
import { OrchestrationStore } from "../src/store.ts";

const output = process.argv[2]!; mkdirSync(output);
const root = realpathSync(mkdtempSync("/tmp/t078-2-port-"));
for (const name of ["state", "repo", "home", "claude"]) mkdirSync(join(root, name));
writeFileSync(join(root, "role.md"), "Static port guard fixture\n");
const store = new OrchestrationStore(join(root, "state"));
const panes = new Panes(join(root, "state"), store, {}, () => {});
const task: any = { task_id: "port-fixture", project_id: "port-project", repo: join(root, "repo"), spec_rev: 1, base_commit: "a".repeat(40) };
const input: any = { schema: 1, root, state: join(root, "state"), task: task.task_id, preset: "ideation",
  launch: randomUUID(), session: randomUUID(), thread: randomUUID(), executable: "/Users/luckye/.local/share/claude/versions/2.1.296",
  role_file: join(root, "role.md"), code_revision: "a".repeat(40), source_snapshot: join(root, "source.tar.gz"), api_url: "http://127.0.0.1:0" };
const pty = createRequire(import.meta.url)("node-pty");
const original = pty.spawn; let attempted = 0;
pty.spawn = () => { attempted++; throw new Error("No real PTY or CLI is allowed in this pure test"); };
let passed = false, error: string | null = null;
try {
  assert.throws(() => panes.startController(task, input), (e: any) => e.code === "messages_api_not_bound");
  assert.equal(attempted, 0); assert.equal(store.launches().length, 0); passed = true;
} catch (e) { error = String(e); }
finally { pty.spawn = original; }
const result = { status: passed ? "PASS" : "INCOMPLETE", error, pty_calls: attempted,
  launch_records: store.launches().length, real_cli_starts: 0, real_pty_starts: 0, argv: process.argv,
  scope: "Real production entry and SQLite; PTY spawn is replaced by a throwing sentinel." };
writeFileSync(join(output, "results.json"), JSON.stringify(result, null, 2)); store.close();
console.log(JSON.stringify(result)); process.exitCode = passed ? 0 : 1;
