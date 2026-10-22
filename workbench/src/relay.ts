import { Refusal } from "./gates/core.ts";
import type { RelayFile } from "./relayFiles.ts";
import { OrchestrationStore } from "./store.ts";
import { reviewRequest } from "./gates/qualityProtocol.ts";
import { taskIdPattern } from "./contracts/a2aMembership.ts";
import type { A2AInboxDelivery } from "./contracts/a2aInbox.ts";

export function isPendingInboxResult(result: any): boolean {
  return result?.ok === true && typeof result.entry?.id === "string" &&
    result.delivery?.entry_id === result.entry.id && result.delivery.state === "pending" &&
    result.delivery.reason === "role_session_missing" && !result.delivery.thread && !result.delivery.message;
}

interface AttemptRelayBinding {
  id: string; task: string; attempt: string; session: string; fence: number; spec_rev: number;
  role: "worker" | "reviewer";
  review_id?: string;
}
interface ControllerRelayBinding {
  id: string; task: string; session: string; spec_rev: number; role: "controller";
  project: string; preset: "ideation" | "executor"; native_session: string; prompt_id: string;
}
export type RelayBinding = AttemptRelayBinding | ControllerRelayBinding;
const keyPattern = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/;

// Intent is durable before gate execution. A missing outcome is unknown, never
// authorization to repeat an operation after an interrupted transfer.
export class RequestRelay {
  readonly store: OrchestrationStore;
  constructor(store: OrchestrationStore) {
    this.store = store;
    store.db.exec(`CREATE TABLE IF NOT EXISTS relay_requests (
      key TEXT PRIMARY KEY, launch TEXT NOT NULL, task TEXT NOT NULL, attempt TEXT,
      request_id TEXT, input TEXT NOT NULL, created_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS relay_results (key TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT NOT NULL);`);
    if (store.db.prepare("PRAGMA table_info(relay_requests)").all().find(row => row.name === "attempt")?.notnull) {
      store.db.exec("BEGIN IMMEDIATE");
      try {
        store.db.exec(`CREATE TABLE relay_requests_nullable (key TEXT PRIMARY KEY, launch TEXT NOT NULL, task TEXT NOT NULL, attempt TEXT,
          request_id TEXT, input TEXT NOT NULL, created_at TEXT NOT NULL);
          INSERT INTO relay_requests_nullable SELECT * FROM relay_requests ORDER BY rowid;
          DROP TABLE relay_requests; ALTER TABLE relay_requests_nullable RENAME TO relay_requests;`);
        store.event("relay_schema_migrated", { change: "controller_without_attempt" });
        store.db.exec("COMMIT");
      } finally { if (store.db.isTransaction) store.db.exec("ROLLBACK"); }
    }
    for (const table of ["relay_requests", "relay_results"]) {
      for (const operation of ["UPDATE", "DELETE"]) store.db.exec(
        `CREATE TRIGGER IF NOT EXISTS ${table}_no_${operation.toLowerCase()} BEFORE ${operation} ON ${table} BEGIN SELECT RAISE(ABORT,'append only'); END;`);
    }
  }
  deferredInboxFeedback() {
    return this.store.db.prepare("SELECT q.key,q.launch,q.request_id,r.data FROM relay_requests q JOIN relay_results r ON r.key=q.key ORDER BY q.rowid")
      .all().map(row => ({ key: String(row.key), launch: String(row.launch), request_id: row.request_id, result: JSON.parse(String(row.data)) }))
      .filter(receipt => isPendingInboxResult(receipt.result) && !this.store.db.prepare(
        "SELECT 1 FROM orchestration_events WHERE type='relay_feedback_intent' AND json_extract(data,'$.key')=?").get(receipt.key));
  }
  claimDeliveredFeedback(key: string, delivery: A2AInboxDelivery): boolean {
    const row = this.store.db.prepare("SELECT data FROM relay_results WHERE key=?").get(key);
    const result = row && JSON.parse(String(row.data));
    if (!isPendingInboxResult(result) || delivery.entry_id !== result.entry.id || delivery.state !== "delivered") return false;
    if (this.store.db.prepare("SELECT 1 FROM orchestration_events WHERE type='relay_feedback_intent' AND json_extract(data,'$.key')=?").get(key)) return false;
    // Reserve synchronously before dispatch can yield. After a crash this
    // intent is unknown, never authorization to inject the I2 root twice.
    this.store.event("relay_feedback_intent", { key, entry_id: delivery.entry_id, delivery });
    return true;
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
    const fileKey = `file:${binding.id}:${file.name}`;
    const canonical = input && typeof input === "object" && !Array.isArray(input)
      ? JSON.stringify(Object.fromEntries(Object.entries(input).sort(([a], [b]) => a.localeCompare(b))))
      : JSON.stringify({ raw: file.raw ?? null, error: file.error ?? null });
    // Request IDs belong to a launch. Resolve persisted intents by their owner,
    // so existing keys and outcomes remain authoritative without rewriting them.
    const previous = requestId
      ? this.store.db.prepare("SELECT * FROM relay_requests WHERE launch=? AND request_id=?").get(binding.id, requestId)
      : this.store.db.prepare("SELECT * FROM relay_requests WHERE key=?").get(fileKey);
    const key = previous ? String(previous.key) : requestId ? `id:${binding.id}:${requestId}` : fileKey;
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
      .run(key, binding.id, binding.task, binding.role === "controller" ? null : binding.attempt, requestId, canonical, new Date().toISOString());
    this.store.event("relay_received", { key, file, input }, binding);
    let result: any;
    try {
      if (parseError || !input || typeof input !== "object" || Array.isArray(input)) throw new Refusal("invalid_relay_request", parseError);
      if (!["worker", "reviewer", "controller"].includes(binding.role)) throw new Refusal("relay_role_required");
      const controller = binding.role === "controller";
      const base = controller ? ["schema", "request_id", "command", "launch", "preset", "project", "task", "session", "spec_rev", "native_session", "prompt_id"]
        : ["schema", "request_id", "command", "task", "attempt", "session", "fence", "spec_rev"];
      const allowed: Record<string, string[]> = binding.role === "reviewer"
        ? { review_submit: ["review_id", "candidate_commit", "verdict", "findings", "review_requirements", "report"] }
        : {
        submit: ["commit"], status: [], issue: ["title", "body", "blocking", "refs"],
        inbox_send: ["from", "to", "kind", "reply_to", "refs", "body", "title", "blocking", "action", "reason", "basis", "bundle_id"],
        inbox_list: ["role"], inbox_ack: ["id", "role", "body"], inbox_ready: ["project"],
        ...(controller ? { stop: ["thread", "stop_id", "actor"] } : {}),
      };
      const extra = allowed[input.command];
      if ((controller && !["inbox_send", "inbox_list", "inbox_ack", "inbox_ready", "stop"].includes(input.command)) ||
          input.schema !== (controller ? 2 : 1) || !requestId || !extra || base.some((field) => !Object.hasOwn(input, field)) ||
          Object.keys(input).some((field) => ![...base, ...extra].includes(field)) ||
          !(controller ? [input.session, input.launch, input.project, input.native_session, input.prompt_id] : [input.attempt, input.session])
            .every((value) => typeof value === "string" && keyPattern.test(value)) ||
          !(typeof input.task === "string" && taskIdPattern.test(input.task)) ||
          (!controller && !Number.isSafeInteger(input.fence)) || !Number.isSafeInteger(input.spec_rev) || input.spec_rev < 1) throw new Refusal("invalid_relay_request");
      const expected = controller ? { task: binding.task, session: binding.session, spec_rev: binding.spec_rev,
        launch: binding.id, project: binding.project, preset: binding.preset, native_session: binding.native_session, prompt_id: binding.prompt_id }
        : { task: binding.task, attempt: binding.attempt, session: binding.session, fence: binding.fence, spec_rev: binding.spec_rev };
      for (const [field, value] of Object.entries(expected)) {
        if (input[field] !== value) throw new Refusal("relay_identity_mismatch", { field });
      }
      if (input.command === "review_submit") {
        reviewRequest(file.raw);
        if (input.review_id !== binding.review_id) throw new Refusal("relay_review_mismatch");
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
