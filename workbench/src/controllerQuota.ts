import { closeSync, existsSync, fstatSync, openSync, readSync, readdirSync } from "node:fs";
import { join } from "node:path";
import type { OrchestrationStore } from "./store.ts";
import type { RoleRequest } from "./roleRequests.ts";

// T-124: a terminal controller whose CLI hits its usage limit is announced in the
// workbench, and the work it started carries on. The fact comes from the CLI's own
// session log, never from screen text: Claude Code writes an API error record whose
// quotaLimits.status is "rejected"; Codex ends the turn with codex_error_info
// "usage_limit_exceeded". The session id and home are what the controller's `a2a request`
// reported from its CLI's environment (CLAUDE_CODE_SESSION_ID, CODEX_THREAD_ID); only
// that one file is read, and only records written after the user approved the role.
export type QuotaState = { role_request: string; launch: string; project: string; role: string; cli: string;
  limit: string | null; resets_at: string | null; since: string };

// looked: when the file was last searched for; a missing file is searched again at most every 30 s.
type Reading = { file: string | null; looked: number; offset: number; exhausted: QuotaState | null; failed: boolean };

export class ControllerQuota {
  private readings = new Map<string, Reading>();
  private store: OrchestrationStore;
  constructor(store: OrchestrationStore) { this.store = store; }

  exhausted(roleRequest: string) { return this.readings.get(roleRequest)?.exhausted ?? null; }
  current() { return [...this.readings.values()].flatMap(reading => reading.exhausted ? [reading.exhausted] : []); }

  // Called on a timer with the approved roles; a role that ended drops out with its notice.
  tick(approved: RoleRequest[]) {
    const live = new Set(approved.map(roleRequest => roleRequest.id));
    for (const id of this.readings.keys()) if (!live.has(id)) this.readings.delete(id);
    for (const roleRequest of approved) {
      if (!roleRequest.native_session || !roleRequest.native_home || !roleRequest.cli || !roleRequest.decided_at) continue;
      const reading = this.readings.get(roleRequest.id) ?? { file: null, looked: 0, offset: 0, exhausted: null, failed: false };
      this.readings.set(roleRequest.id, reading);
      try { this.read(roleRequest, reading); }
      catch (error) {
        if (!reading.failed) this.store.event("controller_quota_unreadable", { role_request: roleRequest.id, reason: String(error) },
          { id: roleRequest.launch, task: null });
        reading.failed = true;
      }
    }
  }

  private read(roleRequest: RoleRequest, reading: Reading) {
    if (!reading.file) {
      if (Date.now() - reading.looked < 30_000) return;
      reading.looked = Date.now();
      reading.file = sessionFile(roleRequest);
      if (!reading.file) return;
    }
    const descriptor = openSync(reading.file, "r");
    let bytes: Buffer;
    try {
      const size = fstatSync(descriptor).size;
      if (size <= reading.offset) return;
      bytes = Buffer.alloc(size - reading.offset);
      readSync(descriptor, bytes, 0, bytes.length, reading.offset);
    } finally { closeSync(descriptor); }
    const end = bytes.lastIndexOf(10);
    if (end < 0) return;
    reading.offset += end + 1;
    const approvedAt = Date.parse(roleRequest.decided_at!);
    for (const line of bytes.subarray(0, end).toString("utf8").split("\n")) {
      // Only complete lines are parsed; one that is not JSON fails the read and is recorded (controller_quota_unreadable).
      const record = JSON.parse(line);
      if (!(Date.parse(record?.timestamp) >= approvedAt)) continue;
      const fact = roleRequest.cli === "claude" ? claudeQuota(record) : codexQuota(record);
      if (fact === "restored" && reading.exhausted) {
        this.store.event("controller_quota_restored", { role_request: roleRequest.id, at: record.timestamp }, { id: roleRequest.launch, task: null });
        reading.exhausted = null;
      } else if (fact && fact !== "restored" && !reading.exhausted) {
        reading.exhausted = { role_request: roleRequest.id, launch: roleRequest.launch, project: roleRequest.project, role: roleRequest.role,
          cli: roleRequest.cli!, limit: fact.limit, resets_at: fact.resets_at, since: record.timestamp };
        this.store.event("controller_quota_exhausted", { ...reading.exhausted, native_session: roleRequest.native_session },
          { id: roleRequest.launch, task: null });
      }
    }
  }
}

type Fact = { limit: string | null; resets_at: string | null } | "restored" | null;

function claudeQuota(record: any): Fact {
  if (record?.isApiErrorMessage === true && record.quotaLimits?.status === "rejected") {
    const resets = Number(record.quotaLimits.resetsAt);
    return { limit: typeof record.quotaLimits.rateLimitType === "string" ? record.quotaLimits.rateLimitType : null,
      resets_at: Number.isFinite(resets) && resets > 0 ? new Date(resets * 1000).toISOString() : null };
  }
  return record?.type === "assistant" && record.isApiErrorMessage !== true ? "restored" : null;
}

function codexQuota(record: any): Fact {
  const payload = record?.type === "event_msg" && record.payload?.type === "task_complete" ? record.payload : null;
  if (!payload) return null;
  return payload.error?.codex_error_info === "usage_limit_exceeded" ? { limit: null, resets_at: null } : payload.error ? null : "restored";
}

function sessionFile(roleRequest: RoleRequest): string | null {
  const home = roleRequest.native_home!, session = roleRequest.native_session!;
  if (roleRequest.cli === "claude") {
    // Claude Code keeps a session under projects/<its working directory, escaped>/<session>.jsonl.
    const projects = join(home, "projects");
    if (!existsSync(projects)) return null;
    for (const entry of readdirSync(projects, { withFileTypes: true }))
      if (entry.isDirectory() && existsSync(join(projects, entry.name, session + ".jsonl"))) return join(projects, entry.name, session + ".jsonl");
    return null;
  }
  // Codex: sessions/YYYY/MM/DD/rollout-<time>-<session>.jsonl under the day the session began, which may
  // be long before the role request; day directories are listed newest first, file contents are not read.
  const sorted = (directory: string) => existsSync(directory) ?
    readdirSync(directory, { withFileTypes: true }).filter(entry => entry.isDirectory() && /^\d+$/.test(entry.name)).map(entry => entry.name).sort().reverse() : [];
  const sessions = join(home, "sessions");
  for (const year of sorted(sessions)) for (const month of sorted(join(sessions, year))) for (const day of sorted(join(sessions, year, month))) {
    const directory = join(sessions, year, month, day);
    const file = readdirSync(directory).find(name => name.startsWith("rollout-") && name.endsWith(`-${session}.jsonl`));
    if (file) return join(directory, file);
  }
  return null;
}
