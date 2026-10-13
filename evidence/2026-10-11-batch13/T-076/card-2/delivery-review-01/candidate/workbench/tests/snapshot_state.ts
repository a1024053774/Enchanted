// Test artifact preservation through SQLite backup, including committed WAL.
import { DatabaseSync, backup } from "node:sqlite";
import { mkdirSync, realpathSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
const [input, output] = process.argv.slice(2);
if (!input || !output) throw new Error("state and new output directory are required");
const state = realpathSync(input), destination = resolve(output);
mkdirSync(destination);
const files = [];
for (const name of ["state.sqlite3", "membership.sqlite3"]) {
  const db = new DatabaseSync(join(state, name), { readOnly: true });
  try { await backup(db, join(destination, name)); }
  finally { db.close(); }
  files.push({ input: join(state, name), snapshot: join(destination, name) });
}
writeFileSync(join(destination, "snapshot.json"), JSON.stringify({ state, files, phase: "before-host-stop" }, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify({ snapshot: destination, files }));
