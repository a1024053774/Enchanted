import { DatabaseSync } from "node:sqlite";
import { join } from "node:path";
import { randomUUID } from "node:crypto";

// The gate owns its existing tables. All new orchestration records share its file.
export class OrchestrationStore {
  readonly db: DatabaseSync;
  constructor(root: string) {
    this.db = new DatabaseSync(join(root, "state.sqlite3"));
    this.db.exec(`PRAGMA busy_timeout=5000; PRAGMA journal_mode=WAL;
      CREATE TABLE IF NOT EXISTS launch_records (id TEXT PRIMARY KEY, task TEXT NOT NULL, attempt TEXT NOT NULL, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS dispatch_records (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, launch TEXT NOT NULL, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS orchestration_events (seq INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL, type TEXT NOT NULL, launch TEXT, task TEXT, attempt TEXT, data TEXT NOT NULL);`);
    for (const table of ["launch_records", "dispatch_records", "orchestration_events"]) {
      for (const operation of ["UPDATE", "DELETE"]) this.db.exec(
        `CREATE TRIGGER IF NOT EXISTS ${table}_no_${operation.toLowerCase()} BEFORE ${operation} ON ${table} BEGIN SELECT RAISE(ABORT,'append only'); END;`);
    }
  }
  event(type: string, data: unknown, binding?: { id: string; task: string; attempt: string }) {
    return Number(this.db.prepare("INSERT INTO orchestration_events(time,type,launch,task,attempt,data) VALUES (?,?,?,?,?,?)")
      .run(new Date().toISOString(), type, binding?.id ?? null, binding?.task ?? null, binding?.attempt ?? null, JSON.stringify(data)).lastInsertRowid);
  }
  launch(data: Record<string, any>) {
    this.db.prepare("INSERT INTO launch_records(id,task,attempt,data) VALUES (?,?,?,?)")
      .run(data.id, data.task, data.attempt, JSON.stringify(data));
  }
  launches(): Record<string, any>[] {
    return this.db.prepare("SELECT data FROM launch_records ORDER BY rowid").all().map((row) => JSON.parse(String(row.data)));
  }
  launchRecord(id: string): Record<string, any> | undefined {
    const row = this.db.prepare("SELECT data FROM launch_records WHERE id=?").get(id);
    return row ? JSON.parse(String(row.data)) : undefined;
  }
  threadLaunch(thread: string): Record<string, any> | undefined {
    const row = this.db.prepare("SELECT data FROM launch_records WHERE json_extract(data,'$.thread')=? ORDER BY rowid DESC LIMIT 1").get(thread);
    return row ? JSON.parse(String(row.data)) : undefined;
  }
  lastEvent(launch: string, types: string[]) {
    const row = this.db.prepare(`SELECT seq,time,type,data FROM orchestration_events WHERE launch=? AND type IN (${types.map(() => "?").join(",")}) ORDER BY seq DESC LIMIT 1`)
      .get(launch, ...types);
    return row ? { seq: Number(row.seq), time: String(row.time), type: String(row.type), data: JSON.parse(String(row.data)) } : null;
  }
  register(launch: string, text: string, source: "executor" | "gate" = "executor") {
    const id = randomUUID();
    const registered_at = new Date().toISOString();
    const seq = Number(this.db.prepare("INSERT INTO dispatch_records(id,launch,data) VALUES (?,?,?)")
      .run(id, launch, JSON.stringify({ text, registered_at, source })).lastInsertRowid);
    return { id, seq, source, text: `⟦${source === "gate" ? "门禁" : "主控"} #${seq}⟧\n${text}`, registered_at };
  }
  read(task?: string) {
    const rows = this.db.prepare(`SELECT * FROM orchestration_events${task ? " WHERE task=?" : ""} ORDER BY seq`).all(...(task ? [task] : []));
    return rows.map(({ data, ...row }) => ({ ...row, data: JSON.parse(String(data)) }));
  }
  close() { this.db.close(); }
}
