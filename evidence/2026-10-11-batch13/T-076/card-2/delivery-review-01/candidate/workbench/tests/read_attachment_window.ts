// Independent read-only connection; no gate helpers or state reconstruction.
import { DatabaseSync } from "node:sqlite";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const [state, boundary, output] = process.argv.slice(2);
if (!state || !boundary || !output) throw new Error("state, boundary and output are required");
const marker = JSON.parse(readFileSync(boundary, "utf8"));
const db = new DatabaseSync(join(state, "state.sqlite3"), { readOnly: true });
let observation: any;
try {
  db.exec("BEGIN");
  const row = db.prepare("SELECT id,data FROM attachments WHERE id=?").get(marker.thread);
  const events = db.prepare("SELECT seq,time,task,attempt,type,details FROM events WHERE task=? ORDER BY seq").all(marker.task);
  observation = { marker, independently_visible: Boolean(row), attachment: row ? JSON.parse(String(row.data)) : null,
    events: events.map((event) => ({ ...event, details: JSON.parse(String(event.details)) })) };
  db.exec("COMMIT");
} finally { db.close(); }
writeFileSync(output, JSON.stringify(observation, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify({ phase: marker.phase, visible: observation.independently_visible,
  attachment_state: observation.attachment?.state, events: observation.events.length }));
