import { DatabaseSync } from "node:sqlite";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
export type DispatchSource = "executor" | "gate" | "inbox";
export type DispatchItem = { id: string; seq: number; source: DispatchSource; text: string; registered_at: string;
  inbox_entry?: string; sender?: string; context?: { kind: string; rejection_id: string } };

// The gate owns its existing tables. All new orchestration records share its file.
export class OrchestrationStore {
  readonly db: DatabaseSync;
  constructor(root: string) {
    this.db = new DatabaseSync(join(root, "state.sqlite3"));
    this.db.exec(`PRAGMA busy_timeout=5000; PRAGMA journal_mode=WAL;
      CREATE TABLE IF NOT EXISTS launch_records (id TEXT PRIMARY KEY, task TEXT NOT NULL, attempt TEXT, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS dispatch_records (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, launch TEXT NOT NULL, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS orchestration_events (seq INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL, type TEXT NOT NULL, launch TEXT, task TEXT, attempt TEXT, data TEXT NOT NULL);`);
    const oldAttempt = this.db.prepare("PRAGMA table_info(launch_records)").all().find(row => row.name === "attempt");
    if (oldAttempt?.notnull) {
      this.db.exec("BEGIN IMMEDIATE");
      try {
        this.db.exec(`CREATE TABLE launch_records_nullable (id TEXT PRIMARY KEY, task TEXT NOT NULL, attempt TEXT, data TEXT NOT NULL);
          INSERT INTO launch_records_nullable SELECT id,task,attempt,data FROM launch_records ORDER BY rowid;
          DROP TABLE launch_records;
          ALTER TABLE launch_records_nullable RENAME TO launch_records;
          CREATE TRIGGER launch_records_no_update BEFORE UPDATE ON launch_records BEGIN SELECT RAISE(ABORT,'append only'); END;
          CREATE TRIGGER launch_records_no_delete BEFORE DELETE ON launch_records BEGIN SELECT RAISE(ABORT,'append only'); END;`);
        this.event("launch_schema_migrated", { change: "controller_attempt_nullable" });
        this.db.exec("COMMIT");
      } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }
    }
    for (const table of ["launch_records", "dispatch_records", "orchestration_events"]) {
      for (const operation of ["UPDATE", "DELETE"]) this.db.exec(
        `CREATE TRIGGER IF NOT EXISTS ${table}_no_${operation.toLowerCase()} BEFORE ${operation} ON ${table} BEGIN SELECT RAISE(ABORT,'append only'); END;`);
    }
    this.db.exec("CREATE UNIQUE INDEX IF NOT EXISTS dispatch_inbox_entry ON dispatch_records(json_extract(data,'$.inbox_entry')) WHERE json_extract(data,'$.inbox_entry') IS NOT NULL");
  }
  event(type: string, data: unknown, binding?: { id: string; task: string; attempt?: string | null }) {
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
  // The open set is a projection of the existing append-only event stream.
  // Launch/profile records remain the sole source of launch configuration.
  hasPaneLayout(task?: string) {
    return Boolean(this.db.prepare(`SELECT 1 FROM orchestration_events
      WHERE type IN ('pane_layout_opened','pane_layout_closed')${task ? " AND task=?" : ""} LIMIT 1`)
      .get(...(task ? [task] : [])));
  }
  openPanes(task?: string) {
    const opened = new Map<string, { launch: string; task: string; position: number; native_session: string | null; resume_argv: string[] | null }>();
    const rows = this.db.prepare(`SELECT type,launch,task,data FROM orchestration_events
      WHERE type IN ('pane_layout_opened','pane_layout_closed','pane_native_session') ORDER BY seq`).all();
    for (const row of rows) {
      const id = String(row.launch), data = JSON.parse(String(row.data));
      if (row.type === "pane_layout_closed") opened.delete(id);
      else if (row.type === "pane_layout_opened") opened.set(id, { launch: id, task: String(row.task), ...data });
      else if (opened.has(id)) Object.assign(opened.get(id)!, data);
    }
    return [...opened.values()].filter(p => !task || p.task === task).sort((a, b) => a.position - b.position);
  }
  lastEvent(launch: string, types: string[]) {
    const row = this.db.prepare(`SELECT seq,time,type,data FROM orchestration_events WHERE launch=? AND type IN (${types.map(() => "?").join(",")}) ORDER BY seq DESC LIMIT 1`)
      .get(launch, ...types);
    return row ? { seq: Number(row.seq), time: String(row.time), type: String(row.type), data: JSON.parse(String(row.data)) } : null;
  }
  private dispatchItem(row: any): DispatchItem {
    const data = JSON.parse(String(row.data));
    return { ...data, id: String(row.id), seq: Number(row.seq), text: `⟦${data.source === "gate" ? "门禁" : "主控"} #${row.seq}⟧\n${data.text}` };
  }
  inboxDispatch(entry: string): (DispatchItem & { launch: string }) | undefined {
    const row = this.db.prepare("SELECT * FROM dispatch_records WHERE json_extract(data,'$.inbox_entry')=?").get(entry);
    return row ? { ...this.dispatchItem(row), launch: String(row.launch) } : undefined;
  }
  dispatchRecord(id: string): (DispatchItem & { launch: string }) | undefined {
    const row = this.db.prepare("SELECT * FROM dispatch_records WHERE id=?").get(id);
    return row ? { ...this.dispatchItem(row), launch: String(row.launch) } : undefined;
  }
  register(launch: string, text: string, source: DispatchSource = "executor", context?: { kind: string; rejection_id: string }, inbox?: { id: string; sender: string }): DispatchItem {
    const id = randomUUID();
    const registered_at = new Date().toISOString();
    // Claude's UserPromptSubmit payload removes terminal line breaks from a
    // bracketed-paste submission. Keep the durable registration in that same
    // canonical form while preserving all internal whitespace exactly.
    const canonicalText = text.replace(/[\r\n]+$/, "");
    const seq = Number(this.db.prepare("INSERT INTO dispatch_records(id,launch,data) VALUES (?,?,?)")
      .run(id, launch, JSON.stringify({ text: canonicalText, registered_at, source, ...(context ? { context } : {}),
        ...(inbox ? { inbox_entry: inbox.id, sender: inbox.sender } : {}) })).lastInsertRowid);
    return { id, seq, source, text: `⟦${source === "gate" ? "门禁" : "主控"} #${seq}⟧\n${canonicalText}`, registered_at, ...(context ? { context } : {}),
      ...(inbox ? { inbox_entry: inbox.id, sender: inbox.sender } : {}) };
  }
  read(task?: string) {
    const rows = this.db.prepare(`SELECT * FROM orchestration_events${task ? " WHERE task=?" : ""} ORDER BY seq`).all(...(task ? [task] : []));
    return rows.map(({ data, ...row }) => ({ ...row, data: JSON.parse(String(data)) }));
  }
  close() { this.db.close(); }
}
