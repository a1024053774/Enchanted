// Current CLI contract with a complete delivery snapshot and independent faults.
import assert from "node:assert/strict";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { DatabaseSync } from "node:sqlite";

const [sourceArg, snapshotArg, outputArg] = process.argv.slice(2);
if (!sourceArg || !snapshotArg || !outputArg) throw new Error("source, snapshot and new output are required");
const source = resolve(sourceArg), snapshot = resolve(snapshotArg), out = resolve(outputArg);
mkdirSync(out);
const results: any[] = [];
function invoke(state: string, name: string) {
  const file = join(out, name + ".json"), argv = [join(source, "workbench/src/stateConsistency.ts"), "--state", state, "--output", file];
  const process = spawnSync(globalThis.process.execPath, argv, { encoding: "utf8" });
  writeFileSync(join(out, name + ".stdout.txt"), process.stdout, { flag: "wx" });
  writeFileSync(join(out, name + ".stderr.txt"), process.stderr, { flag: "wx" });
  assert.ok(process.status === 0 || process.status === 1, process);
  const report = JSON.parse(readFileSync(file, "utf8"));
  assert.ok(report.tables.length > 0 && !report.error, report);
  results.push({ name, argv: [globalThis.process.execPath, ...argv], exit: process.status, report: file });
  return report;
}
const control = invoke(snapshot, "control");
for (const table of ["tasks", "attempts", "verifications", "runs", "attachments"]) {
  assert.equal(control.tables.find((row: any) => row.table === table)?.status, "consistent", table);
}
for (const [table, field, value] of [["tasks", "fence", 999], ["attempts", "session_id", "independent-foreign-session"],
  ["verifications", "M", "0000000000000000000000000000000000000000"]]) {
  const state = join(out, table + "-mutant"); mkdirSync(state);
  for (const name of ["state.sqlite3", "membership.sqlite3"]) copyFileSync(join(snapshot, name), join(state, name));
  const db = new DatabaseSync(join(state, "state.sqlite3"));
  let key: string, before: any[];
  try {
    before = db.prepare("SELECT * FROM events ORDER BY seq").all();
    const row = db.prepare(`SELECT id,data FROM "${table}" ORDER BY id LIMIT 1`).get()!;
    assert.ok(row, "Complete fixture must contain the mutated table");
    key = String(row.id);
    const data = JSON.parse(String(row.data)); data[String(field)] = value;
    db.prepare(`UPDATE "${table}" SET data=? WHERE id=?`).run(JSON.stringify(data), key);
    assert.deepEqual(db.prepare("SELECT * FROM events ORDER BY seq").all(), before, "Fault cannot change the replay oracle");
  } finally { db.close(); }
  const report = invoke(state, table + "-fault");
  const result = report.tables.find((row: any) => row.table === table);
  assert.equal(result.status, "inconsistent", report);
  assert.ok(result.mismatches.some((row: any) => row.row === key && row.field === field), result);
}
// A deleted historical row is not equivalent to an empty successful result.
const state = join(out, "deleted-attempt"); mkdirSync(state);
for (const name of ["state.sqlite3", "membership.sqlite3"]) copyFileSync(join(snapshot, name), join(state, name));
const db = new DatabaseSync(join(state, "state.sqlite3"));
let deleted: string;
try {
  deleted = String(db.prepare("SELECT id FROM attempts ORDER BY id LIMIT 1").get()!.id);
  db.prepare("DELETE FROM attempts WHERE id=?").run(deleted);
} finally { db.close(); }
const result = invoke(state, "deleted-attempt-fault").tables.find((row: any) => row.table === "attempts");
assert.equal(result.status, "inconsistent");
assert.ok(result.mismatches.some((row: any) => row.row === deleted && row.reason === "事件重建有行，状态表缺行"));
writeFileSync(join(out, "run.json"), JSON.stringify({ status: "PASS", real_codex_turns: 0, results,
  scope: "检查器的字段/缺行反事实；整体一致性结果另外报告，不能以反事实 PASS 覆盖不可重建表。" }, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify({ status: "PASS", checks: results.length, real_codex_turns: 0 }));
