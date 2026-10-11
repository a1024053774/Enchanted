import { Refusal } from "./gates/core.ts";
import type { RelayFile } from "./relayFiles.ts";
import { OrchestrationStore } from "./store.ts";

export interface RelayBinding {
  id: string; task: string; attempt: string; session: string; fence: number; spec_rev: number;
}
const keyPattern = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/;

// Intent is durable before gate execution. A missing outcome is unknown, never
// authorization to repeat an operation after an interrupted transfer.
export class RequestRelay {
  readonly store: OrchestrationStore;
  constructor(store: OrchestrationStore) {
    this.store = store;
    store.db.exec(`CREATE TABLE IF NOT EXISTS relay_requests (
      key TEXT PRIMARY KEY, launch TEXT NOT NULL, task TEXT NOT NULL, attempt TEXT NOT NULL,
      request_id TEXT, input TEXT NOT NULL, created_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS relay_results (key TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT NOT NULL);`);
    for (const table of ["relay_requests", "relay_results"]) {
      for (const operation of ["UPDATE", "DELETE"]) store.db.exec(
        `CREATE TRIGGER IF NOT EXISTS ${table}_no_${operation.toLowerCase()} BEFORE ${operation} ON ${table} BEGIN SELECT RAISE(ABORT,'append only'); END;`);
    }
  }
  async receive(binding: RelayBinding, file: RelayFile, matchedStop: boolean,
    perform: (input: Record<string, any>) => Promise<any>) {
    let input: any = null;
    let parseError: string | null = file.error ?? null;
    if (!parseError) {
      try { input = JSON.parse(file.raw!); }
      catch (error) { parseError = String(error); }
    }
    const requestId = input && typeof input.request_id === "string" && keyPattern.test(input.request_id) ? input.request_id : null;
    const key = requestId ? "id:" + requestId : `file:${binding.id}:${file.name}`;
    const canonical = input && typeof input === "object" && !Array.isArray(input)
      ? JSON.stringify(Object.fromEntries(Object.entries(input).sort(([a], [b]) => a.localeCompare(b))))
      : JSON.stringify({ raw: file.raw ?? null, error: file.error ?? null });
    const previous = this.store.db.prepare("SELECT * FROM relay_requests WHERE key=?").get(key);
    if (previous) {
      if (previous.launch !== binding.id || previous.input !== canonical) {
        const result = { ok: false, error: "relay_request_id_reused" };
        const seen = this.store.db.prepare("SELECT 1 FROM orchestration_events WHERE launch=? AND type='relay_rejected' AND json_extract(data,'$.key')=? AND json_extract(data,'$.canonical')=? LIMIT 1")
          .get(binding.id, key, canonical);
        this.store.event("relay_rejected", { key, file, canonical, result }, binding);
        return { key, request_id: requestId, replayed: Boolean(seen), result };
      }
      const row = this.store.db.prepare("SELECT data FROM relay_results WHERE key=?").get(key);
      const result = row ? JSON.parse(String(row.data)) : { ok: false, error: "relay_outcome_unknown" };
      this.store.event("relay_replayed", { key, file: file.name, result }, binding);
      return { key, request_id: requestId, replayed: true, result };
    }
    if (!matchedStop) {
      const result = { ok: false, error: "relay_requires_current_stop" };
      this.store.event("relay_rejected", { key, request_id: requestId, file, result }, binding);
      return { key, request_id: requestId, replayed: false, result };
    }
    this.store.db.prepare("INSERT INTO relay_requests(key,launch,task,attempt,request_id,input,created_at) VALUES (?,?,?,?,?,?,?)")
      .run(key, binding.id, binding.task, binding.attempt, requestId, canonical, new Date().toISOString());
    this.store.event("relay_received", { key, file, input }, binding);
    let result: any;
    try {
      if (parseError || !input || typeof input !== "object" || Array.isArray(input)) throw new Refusal("invalid_relay_request", parseError);
      const base = ["schema", "request_id", "command", "task", "attempt", "session", "fence", "spec_rev"];
      const allowed: Record<string, string[]> = { submit: ["commit"], status: [], issue: ["title", "body", "blocking", "refs"] };
      const extra = allowed[input.command];
      if (input.schema !== 1 || !requestId || !extra || base.some((field) => !Object.hasOwn(input, field)) ||
          Object.keys(input).some((field) => ![...base, ...extra].includes(field)) ||
          ![input.task, input.attempt, input.session].every((value) => typeof value === "string" && keyPattern.test(value)) ||
          !Number.isSafeInteger(input.fence) || !Number.isSafeInteger(input.spec_rev)) throw new Refusal("invalid_relay_request");
      for (const field of ["task", "attempt", "session", "fence", "spec_rev"] as const) {
        if (input[field] !== binding[field]) throw new Refusal("relay_identity_mismatch", { field });
      }
      if (input.command === "submit" && (typeof input.commit !== "string" || !/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(input.commit))) {
        throw new Refusal("invalid_relay_request", { field: "commit" });
      }
      if (input.command === "issue" && (typeof input.title !== "string" || !input.title.trim() || typeof input.body !== "string" ||
        (input.blocking !== undefined && typeof input.blocking !== "boolean") ||
        (input.refs !== undefined && (!Array.isArray(input.refs) || !input.refs.every((value: unknown) => typeof value === "string"))))) {
        throw new Refusal("invalid_relay_request", { field: "issue" });
      }
      const { schema: _schema, request_id: _id, ...command } = input;
      result = await perform(command);
    } catch (error) {
      result = { ok: false, error: error instanceof Refusal ? error.code : "relay_outcome_unknown",
        details: error instanceof Refusal ? error.details : String(error) };
    }
    this.store.db.prepare("INSERT INTO relay_results(key,data,created_at) VALUES (?,?,?)")
      .run(key, JSON.stringify(result), new Date().toISOString());
    this.store.event(result.ok ? "relay_processed" : "relay_rejected", { key, request_id: requestId, result }, binding);
    return { key, request_id: requestId, replayed: false, result };
  }
}
