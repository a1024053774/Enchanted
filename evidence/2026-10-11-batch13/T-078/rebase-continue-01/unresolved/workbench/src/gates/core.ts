// Derived from Synara, MIT License.
// Copyright (c) 2026 T3 Tools Inc.
// Copyright (c) 2026 Emanuele Di Pietro
// See ../../LICENSE.synara for the full permission notice.

import { randomUUID } from "node:crypto";
import { chmodSync, existsSync, lstatSync, mkdirSync, readFileSync, realpathSync, statSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, join } from "node:path";
import { fileURLToPath } from "node:url";
import { DatabaseSync } from "node:sqlite";
import {
  A2AGateRequest,
  A2AInboxRequest,
  A2AStopRequest,
  type A2AInboxEntry,
  type A2AInboxDelivery,
  type A2AAttempt,
  type A2ARuntimeIdentity,
  type A2ARun,
  type A2AUserInputObserver,
  type A2AGateResult,
  type A2AVerification,
  type A2ACommandResult,
  type A2AReview,
  type A2ARepair,
  type A2ATask,
  type A2AAttachment,
  type A2ATaskMembership,
  type A2AIssueRecord,
  type A2AIssueView,
  type A2AUserInput,
  type A2ARolePermissionsRequest,
  ProjectId,
  ThreadId,
} from "../contracts/index.ts";
import { execFile as execProcessFile, spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { TaskCardError, taskCardTemplate, validateTaskCard, pathAllowed, pathIntersection, projectRules, type ProjectQuality, type TaskCard } from "./taskCards.ts";
import { Schema } from "effect";
import { executorScore, reviewVerdict, QualityProtocolError } from "./qualityProtocol.ts";
import { A2AMembership } from "./membership.ts";
import { readyTickets } from "./readyTickets.ts";
import {
  ensureRolePermissionTables,
  readRolePermissionSettings,
  saveRolePermission,
} from "./rolePermissions.ts";

export class Refusal extends Error {
  readonly code: string;
  readonly details?: unknown;
  constructor(
    code: string,
    details?: unknown,
  ) {
    super(code);
    this.code = code;
    this.details = details;
  }
}
function requireGate(value: unknown, code: string, details?: unknown): asserts value {
  if (!value) throw new Refusal(code, details);
}
function id(value: string | undefined): string {
  requireGate(value && /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(value), "invalid_id");
  return value;
}
function sha(value: string | undefined): string {
  requireGate(value && /^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(value), "invalid_commit");
  return value;
}
function text(value: string | undefined): string {
  requireGate(value && value.trim() && !/[\x00-\x1f]/.test(value), "invalid_text");
  return value;
}
function inputPath(value: string | undefined, directory = false): string {
  requireGate(value && isAbsolute(value) && !/[\x00-\x1f]/.test(value), "invalid_path");
  const path = realpathSync(value);
  requireGate(directory ? statSync(path).isDirectory() : statSync(path).isFile(), "invalid_path");
  return path;
}

// Host-owned lifecycle boundary. The gate does not implement a CLI/provider runtime.
// T-075-1 exercises it with an isolated service; the pane host is supplied by T-075-3.
export interface GateRuntime {
  ensureProject(project: string, repo: string): Promise<void>;
  createThread(task: A2ATask, attempt: A2AAttempt): Promise<void>;
  startThread(task: A2ATask, attempt: A2AAttempt, prompt: string): Promise<void>;
  readThread(thread: string): Promise<{
    workspace: string;
    provider: string;
    turn: string | null;
    runtime_identity: A2ARuntimeIdentity;
    running: boolean;
    stopped: boolean;
    archived: boolean;
    session_ended?: boolean;
    blocked?: boolean;
    error?: { providerPresent: boolean; activeTurn: string | null };
  }>;
  stopThread(thread: string): Promise<void>;
  archiveThread(thread: string): Promise<void>;
  qualityFeedback?(attempt: A2AAttempt, repair: A2ARepair): Promise<void>;
  createReview?(task: A2ATask, review: A2AReview, prompt: string): Promise<void>;
  sessionFacts?(thread: string): Promise<{ launch: Record<string, any>; model: string; effort: string }>;
  sendGateFeedback?(thread: string, messageId: string, message: string): Promise<void>;
  createAttachedThread?(task: A2ATask, attachment: A2AAttachment, prompt: string): Promise<void>;
  sendUserAnswer?(thread: string, messageId: string, message: string): Promise<void>;
  wakeThread?(thread: string, entry: A2AInboxEntry): Promise<{ state: "queued" | "delivered" | "unknown"; message: string }>;
  readWakeDelivery?(thread: string, message: string): Promise<{ state: "queued" | "delivered" | "unknown"; at: string }>;
  interruptThread?(thread: string): Promise<void>;
}
export interface GateActor {
  assertActive(): Promise<void>;
  address?: string;
}
<<<<<<< HEAD
type ScoreProvenance = Pick<NonNullable<A2AAttempt["delivery"]>, "launch_id" | "cli" | "model" | "effort" | "number">;
=======
// A role/transport credential is not a native thread or turn identity.
export interface SubmitCaller extends GateActor {
  thread: string;
  turn: string;
}
>>>>>>> b3fb998c (T-078-1: 接通窗口输入、worker 收件箱和停止通路，记录主控启动计划)

/** The sole mutation owner. Lifecycle signals alone do not constitute delivery. */
export class A2AGates {
  private readonly db: DatabaseSync;
  private readonly membership: A2AMembership;
  private userInputObserver?: A2AUserInputObserver;
  private readonly deferredUserInputs = new Map<string, A2AUserInput>();
  private shuttingDown = false;
  readonly root: string;
  private readonly runtime?: GateRuntime;
  private readonly now: () => number;
  constructor(
    root: string,
    runtime?: GateRuntime,
    now: () => number = Date.now,
  ) {
    this.root = root;
    this.runtime = runtime;
    this.now = now;
    requireGate(isAbsolute(root), "invalid_path");
    mkdirSync(root, { recursive: true, mode: 0o700 });
    this.db = new DatabaseSync(join(root, "state.sqlite3"));
    this.membership = new A2AMembership(root);
    this.db.exec(`PRAGMA busy_timeout=5000; PRAGMA journal_mode=WAL;
      CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS task_card_versions (task TEXT NOT NULL, version INTEGER NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(task,version));
      CREATE TABLE IF NOT EXISTS task_card_snapshots (id TEXT PRIMARY KEY, task TEXT NOT NULL, version INTEGER NOT NULL, attempt TEXT, data TEXT NOT NULL);
      CREATE TRIGGER IF NOT EXISTS task_card_versions_no_update BEFORE UPDATE ON task_card_versions BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS task_card_versions_no_delete BEFORE DELETE ON task_card_versions BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS task_card_snapshots_no_update BEFORE UPDATE ON task_card_snapshots BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS task_card_snapshots_no_delete BEFORE DELETE ON task_card_snapshots BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS verifications (id TEXT PRIMARY KEY, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, task TEXT NOT NULL, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS attachments (id TEXT PRIMARY KEY, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS user_input_events (event_id TEXT PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS user_input_checkpoint (id INTEGER PRIMARY KEY CHECK(id=1), sequence INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS user_input_ingress (command_id TEXT PRIMARY KEY, data TEXT NOT NULL);
      CREATE TRIGGER IF NOT EXISTS user_input_ingress_no_update BEFORE UPDATE ON user_input_ingress BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS user_input_ingress_no_delete BEFORE DELETE ON user_input_ingress BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TABLE IF NOT EXISTS issue_records (id TEXT PRIMARY KEY, task TEXT NOT NULL, thread TEXT NOT NULL, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS inbox_records (id TEXT PRIMARY KEY, data TEXT NOT NULL);
      CREATE TRIGGER IF NOT EXISTS inbox_records_no_update BEFORE UPDATE ON inbox_records BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS inbox_records_no_delete BEFORE DELETE ON inbox_records BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TABLE IF NOT EXISTS inbox_deliveries (seq INTEGER PRIMARY KEY AUTOINCREMENT, entry TEXT NOT NULL, data TEXT NOT NULL);
      CREATE TRIGGER IF NOT EXISTS inbox_deliveries_no_update BEFORE UPDATE ON inbox_deliveries BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS inbox_deliveries_no_delete BEFORE DELETE ON inbox_deliveries BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TABLE IF NOT EXISTS user_inputs (id TEXT PRIMARY KEY, task TEXT, message TEXT, data TEXT NOT NULL);
      CREATE TRIGGER IF NOT EXISTS issue_records_no_update BEFORE UPDATE ON issue_records BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS issue_records_no_delete BEFORE DELETE ON issue_records BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS user_inputs_no_update BEFORE UPDATE ON user_inputs BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS user_inputs_no_delete BEFORE DELETE ON user_inputs BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL, task TEXT NOT NULL, attempt TEXT, type TEXT NOT NULL, details TEXT NOT NULL);
      CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append only'); END;`);
    ensureRolePermissionTables(this.db);
    // T-055 registered one input per message. A reply bundle has one message
    // and several immutable inputs. Preserve every legacy row byte-for-byte
    // while removing only the obsolete message uniqueness constraint.
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const messageUnique = this.db
        .prepare("PRAGMA index_list(user_inputs)")
        .all()
        .some((index) => {
          const columns = this.db
            .prepare(`PRAGMA index_info('${String(index.name).replaceAll("'", "''")}')`)
            .all();
          return index.unique === 1 && columns.length === 1 && columns[0]!.name === "message";
        });
      const legacyColumns = this.db.prepare("PRAGMA table_info(user_inputs)").all();
      if (
        messageUnique ||
        legacyColumns.some(
          (column) => (column.name === "task" || column.name === "message") && column.notnull === 1,
        )
      )
        this.db.exec(`
        CREATE TABLE user_inputs_bundle (id TEXT PRIMARY KEY, task TEXT, message TEXT, data TEXT NOT NULL);
        INSERT INTO user_inputs_bundle SELECT id,task,message,data FROM user_inputs ORDER BY rowid;
        DROP TABLE user_inputs;
        ALTER TABLE user_inputs_bundle RENAME TO user_inputs;
        CREATE TRIGGER user_inputs_no_update BEFORE UPDATE ON user_inputs BEGIN SELECT RAISE(ABORT,'append only'); END;
        CREATE TRIGGER user_inputs_no_delete BEFORE DELETE ON user_inputs BEGIN SELECT RAISE(ABORT,'append only'); END;`);
      this.db.exec("CREATE INDEX IF NOT EXISTS user_inputs_message ON user_inputs(message)");
      // Copy the old dedup ledger atomically. Historical immutable events remain unchanged.
      if (
        this.db
          .prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name='human_inputs'")
          .get()
      ) {
        this.db.exec(
          "INSERT OR IGNORE INTO user_input_events SELECT event_id FROM human_inputs; DROP TABLE human_inputs",
        );
      }
      this.db.exec("COMMIT");
    } finally {
      if (this.db.isTransaction) this.db.exec("ROLLBACK");
    }
    if (
      !this.db
        .prepare("PRAGMA table_info(events)")
        .all()
        .some((column) => column.name === "attempt")
    )
      this.db.exec("ALTER TABLE events ADD COLUMN attempt TEXT");
    mkdirSync(join(root, "locks"), { recursive: true });
  }
  beginShutdown() { this.shuttingDown = true; }
  close() {
    this.membership.close();
    this.db.close();
  }
  private operationLock(task: string): DatabaseSync {
    const lock = new DatabaseSync(join(this.root, "locks", `${task}.sqlite3`));
    lock.exec("PRAGMA busy_timeout=0");
    try {
      lock.exec("BEGIN IMMEDIATE");
      return lock;
    } catch (error) {
      lock.close();
      if (
        (error as { errcode?: number }).errcode === 5 ||
        (error as Error).message.includes("database is locked")
      )
        throw new Refusal("operation_busy");
      throw error;
    }
  }
  /** The manual correction route shares the gate operation lock and revision CAS. */
  saveMembership(input: A2ATaskMembership): A2ATaskMembership {
    const lock = this.operationLock(id(input.taskId));
    try {
      this.checkUserInputObserver();
      const row = this.db.prepare("SELECT data FROM tasks WHERE id=?").get(input.taskId);
      if (row)
        requireGate(
          (JSON.parse(String(row.data)) as A2ATask).project_id === input.projectId,
          "gate_project_mismatch",
        );
      // Lifecycle comes from durable gate bindings, never from a manual editor.
      const current = this.membership.list().find((task) => task.taskId === input.taskId);
      return this.membership.save({
        ...input,
        members: input.members.map(({ threadId, role }) => {
          const attached = this.db.prepare("SELECT data FROM attachments WHERE id=?").get(threadId);
          const attachment = attached
            ? (JSON.parse(String(attached.data)) as A2AAttachment)
            : undefined;
          const worker = this.db
            .prepare("SELECT data FROM attempts WHERE json_extract(data,'$.thread_id')=?")
            .get(threadId);
          const attempt = worker ? (JSON.parse(String(worker.data)) as A2AAttempt) : undefined;
          let endedAt =
            attachment?.state === "ended"
              ? attachment.ended_at
              : attempt?.reclaimed
                ? attempt.reclaimed_at
                : current?.members.find((member) => member.threadId === threadId)?.endedAt;
          if (attempt?.reclaimed && !endedAt) {
            // Published attempt records before reclaimed_at retain their
            // completion time in the append-only event journal.
            const completed = this.db
              .prepare(
                "SELECT time FROM events WHERE task=? AND attempt=? AND type='reclaimed' ORDER BY seq DESC LIMIT 1",
              )
              .get(attempt.task_id, attempt.attempt_id);
            requireGate(completed, "reclaim_unconfirmed");
            endedAt = String(completed.time);
          }
          return { threadId, role, ...(endedAt ? { endedAt } : {}) };
        }),
      });
    } finally {
      lock.close();
    }
  }
  private taskMembership(task: A2ATask): A2ATaskMembership {
    const current = this.membership.list().find((item) => item.taskId === task.task_id);
    if (current) {
      requireGate(current.projectId === task.project_id, "gate_project_mismatch");
      return current;
    }
    return this.membership.save({
      taskId: task.task_id,
      projectId: ProjectId.makeUnsafe(task.project_id),
      title: task.title ?? task.task_id,
      revision: 0,
      members: [],
    });
  }
  private member(task: A2ATask, thread: string, role: A2AAttachment["role"], endedAt?: string) {
    const membership = this.taskMembership(task);
    const previous = membership.members.find((member) => member.threadId === thread);
    const member = {
      threadId: ThreadId.makeUnsafe(thread),
      role: previous?.role ?? role,
      ...(endedAt ? { endedAt } : previous?.endedAt ? { endedAt: previous.endedAt } : {}),
    };
    if (previous && previous.endedAt === member.endedAt) return;
    this.membership.save({
      ...membership,
      members: previous
        ? membership.members.map((value) => (value.threadId === thread ? member : value))
        : [...membership.members, member],
    });
  }
  private saveAttachment(attachment: A2AAttachment) {
    this.db
      .prepare(
        "INSERT INTO attachments(id,data) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
      )
      .run(attachment.thread_id, JSON.stringify(attachment));
  }
  userInputObserverStatus(): A2AUserInputObserver | undefined {
    const status = this.userInputObserver;
    return status
      ? { ...status, ...(status.failure ? { failure: { ...status.failure } } : {}) }
      : undefined;
  }
  setUserInputObserverStatus(
    state: A2AUserInputObserver["state"],
    failure?: A2AUserInputObserver["failure"],
  ) {
    // A failed recorder cannot reset itself. A new service instance must replay
    // the durable Synara journal before reporting healthy again.
    if (this.userInputObserver?.state === "failed") return;
    this.userInputObserver = {
      state,
      updated_at: new Date().toISOString(),
      ...(failure ? { failure } : {}),
    };
  }
  private checkUserInputObserver() {
    requireGate(
      this.userInputObserver?.state !== "failed",
      "user_input_observer_failed",
      this.userInputObserverStatus(),
    );
  }
  taskForThread(thread: string): A2ATask | null {
    if (!thread) return null;
    const rows = this.db.prepare("SELECT data FROM tasks").all();
    for (const row of rows) {
      const task = JSON.parse(String(row.data)) as A2ATask;
      if (task.current_attempt?.thread_id === thread) return task;
    }
    return null;
  }
  userInputTarget(thread: string, project?: string | null): A2AUserInput["target"] {
    const row = this.db
      .prepare("SELECT data FROM attempts WHERE json_extract(data,'$.thread_id')=?")
      .get(thread);
    const attempt = row ? (JSON.parse(String(row.data)) as A2AAttempt) : undefined;
    const member = this.membership
      .list()
      .find((task) => task.members.some((m) => m.threadId === thread));
    const taskId = attempt?.task_id ?? member?.taskId ?? null;
    const taskRow = taskId
      ? this.db.prepare("SELECT data FROM tasks WHERE id=?").get(taskId)
      : undefined;
    const task = taskRow ? (JSON.parse(String(taskRow.data)) as A2ATask) : undefined;
    return {
      project: task?.project_id ?? member?.projectId ?? project ?? null,
      task: taskId,
      attempt: attempt?.attempt_id ?? null,
      thread,
      turn: null,
      message: null,
      request: null,
    };
  }
  /** Only the WS entry registers these receipts; domain replay never guesses command provenance. */
  registerUserInputCommand(commandId: string, input: A2AUserInput): void {
    this.db
      .prepare("INSERT OR IGNORE INTO user_input_ingress(command_id,data) VALUES (?,?)")
      .run(commandId, JSON.stringify(input));
  }
  userInputCommand(commandId: string): A2AUserInput | undefined {
    const row = this.db
      .prepare("SELECT data FROM user_input_ingress WHERE command_id=?")
      .get(commandId);
    return row ? (JSON.parse(String(row.data)) as A2AUserInput) : undefined;
  }
  userInputCheckpoint(): number | undefined {
    const row = this.db.prepare("SELECT sequence FROM user_input_checkpoint WHERE id=1").get();
    return row ? Number(row.sequence) : undefined;
  }
  advanceUserInputCheckpoint(sequence: number): void {
    this.db
      .prepare(
        "INSERT INTO user_input_checkpoint(id,sequence) VALUES (1,?) ON CONFLICT(id) DO UPDATE SET sequence=max(sequence,excluded.sequence)",
      )
      .run(sequence);
  }
  userInputCommands(): ReadonlyArray<{ commandId: string; input: A2AUserInput }> {
    return this.db
      .prepare("SELECT command_id,data FROM user_input_ingress ORDER BY rowid")
      .all()
      .map((row) => ({
        commandId: String(row.command_id),
        input: JSON.parse(String(row.data)) as A2AUserInput,
      }));
  }
  deferUserInput(commandId: string, input: A2AUserInput): void {
    // The RPC observation is still authoritative while this process retains it.
    this.deferredUserInputs.set(commandId, input);
  }
  flushDeferredUserInputs(): void {
    for (const [commandId, input] of this.deferredUserInputs) {
      this.registerUserInputCommand(commandId, input);
      this.appendUserInput(input, `rpc:${commandId}`);
      this.deferredUserInputs.delete(commandId);
    }
  }
  recordUserInput(input: {
    thread_id: string;
    message_id: string;
    event_id: string;
    source_sequence: number;
    turn_id: string | null;
    created_at: string;
    text: string;
    dispatch_origin: "user";
    project_id?: string | null;
    answer?: { request: string; content: unknown };
    attachments?: unknown;
  }): boolean {
    requireGate(
      input.event_id && input.message_id && input.dispatch_origin === "user",
      "invalid_user_input",
    );
    // Answer registration suppresses its dispatched message, including replay overlap.
    if (this.db.prepare("SELECT 1 FROM user_inputs WHERE message=?").get(input.message_id))
      return false;
    const target = this.userInputTarget(input.thread_id, input.project_id);
    return this.appendUserInput(
      {
        id: randomUUID(),
        schema: 1,
        form: input.answer ? "answer" : "message",
        text: input.text,
        target: {
          ...target,
          turn: input.turn_id,
          message: input.message_id,
          request: input.answer?.request ?? null,
        },
        channel: "thread-message",
        reply_to: input.answer?.request ?? null,
        source_ref: {
          message_id: input.message_id,
          event_id: input.event_id,
          source_sequence: input.source_sequence,
        },
        certainty: "observed",
        created_at: input.created_at,
        ...(input.answer
          ? { content: input.answer.content }
          : input.attachments
            ? { content: { attachments: input.attachments } }
            : {}),
      },
      input.event_id,
    );
  }
  appendUserInput(input: A2AUserInput, source: string): boolean {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const inserted = this.db
        .prepare("INSERT OR IGNORE INTO user_input_events(event_id) VALUES (?)")
        .run(source);
      if (!inserted.changes) return false;
      this.saveUserInput(input);
      if (
        input.target.attempt &&
        input.target.task &&
        input.channel !== "ui-derived" &&
        input.form !== "gap"
      ) {
        const row = this.db
          .prepare("SELECT data FROM attempts WHERE id=?")
          .get(input.target.attempt)!;
        const attempt = JSON.parse(String(row.data)) as A2AAttempt;
        this.event(
          input.target.task,
          "human_intervention",
          {
            input_id: input.id,
            task_id: input.target.task,
            attempt_id: input.target.attempt,
            thread_id: input.target.thread,
            turn_id: input.target.turn,
            message_id: input.target.message,
            request_id: input.target.request ?? null,
            channel: input.channel,
            form: input.form,
            event_id: input.source_ref.event_id ?? input.source_ref.command_id,
            source_sequence: input.source_ref.source_sequence,
            session_id: attempt.session_id,
            fence: attempt.fence,
            spec_rev: attempt.spec_rev,
            dispatch_origin: "user",
            text: input.text,
            ...(input.channel === "commit-trailer" ? { source_ref: input.source_ref, certainty: input.certainty } : {}),
          },
          input.target.attempt,
        );
      }
      this.db.exec("COMMIT");
      return true;
    } finally {
      if (this.db.isTransaction) this.db.exec("ROLLBACK");
    }
  }
  rolePermissionSettings() {
    return readRolePermissionSettings(this.db);
  }
  saveRolePermissionSettings(request: A2ARolePermissionsRequest) {
    return saveRolePermission(this.db, request, (input) => this.saveUserInput(input), this.now());
  }
  private saveUserInput(input: A2AUserInput) {
    this.db.prepare("INSERT INTO user_inputs(id,task,message,data) VALUES (?,?,?,?)").run(
      input.id,
      input.target.task,
      input.target.message,
      JSON.stringify({
        ...input,
        target: { ...this.userInputTarget(input.target.thread), ...input.target },
      }),
    );
  }
  private appendIssue(record: A2AIssueRecord) {
    const ownsTransaction = !this.db.isTransaction;
    if (ownsTransaction) this.db.exec("BEGIN IMMEDIATE");
    try {
      this.db
        .prepare("INSERT INTO issue_records(id,task,thread,data) VALUES (?,?,?,?)")
        .run(record.id, record.task_id, record.thread_id, JSON.stringify(record));
      const sequence = this.event(
        record.task_id,
        `issue_${record.kind === "disposition" ? record.action : record.kind}`,
        record,
        record.attempt_id,
      );
      if (ownsTransaction) this.db.exec("COMMIT");
      return sequence;
    } finally {
      if (ownsTransaction && this.db.isTransaction) this.db.exec("ROLLBACK");
    }
  }
  private readIssues(task: string, thread?: string) {
    const records = this.db
      .prepare("SELECT data FROM issue_records WHERE task=? ORDER BY rowid")
      .all(task)
      .map((row) => JSON.parse(String(row.data)) as A2AIssueRecord)
      .filter((record) => thread === undefined || record.thread_id === thread);
    const issues: A2AIssueView[] = records
      .filter((record) => record.kind === "issue")
      .map((issue) => {
        const chain = records.filter((record) => record.issue_id === issue.id);
        const requested = chain.findLastIndex(
          (record) => record.action === "reopen" || record.action === "needs-user",
        );
        const answer = chain.slice(requested + 1).findLast((record) => record.kind === "answer");
        const disposition = chain.findLast((record) => record.kind === "disposition");
        const last = chain.at(-1)!;
        const elapsed = Math.max(0, this.now() - Date.parse(last.created_at));
        const state: A2AIssueView["state"] =
          last.kind === "answer"
            ? "已答复"
            : last.action === "delivered"
              ? "已送达"
              : last.action === "close" || last.action === "dismiss"
                ? "已关闭"
                : last.action === "forward"
                  ? elapsed < 900_000
                    ? "已转交"
                    : "等你决定"
                  : last.action === "snooze"
                    ? elapsed < 3_600_000
                      ? "稍后"
                      : "等你决定"
                    : last.kind === "disposition" || issue.blocking || elapsed >= 900_000
                      ? "等你决定"
                      : "待判断";
        return {
          issue,
          state,
          ...(answer ? { answer } : {}),
          ...(disposition ? { disposition } : {}),
        };
      });
    const user_inputs = this.db
      .prepare("SELECT data FROM user_inputs WHERE task=? ORDER BY rowid")
      .all(task)
      .map((row) => JSON.parse(String(row.data)) as A2AUserInput)
      .filter((input) => thread === undefined || input.target.thread === thread);
    return { records, issues, user_inputs };
  }
  /** Host credentials own identity; arguments cannot select another thread. */
  async raiseIssue(
    input: { title: string; body: string; blocking: boolean; refs: ReadonlyArray<string> },
    caller: SubmitCaller,
  ) {
    const binding = this.ownedThread(caller.thread);
    requireGate(
      binding && ["worker", "reviewer", "monitor"].includes(binding.role),
      "stale_thread",
    );
    const task = binding.task;
    const lock = this.operationLock(task.task_id);
    try {
      this.checkUserInputObserver();
      const current = this.load(task.task_id);
      const attempt = binding.attempt;
      if (attempt)
        requireGate(current.current_attempt?.attempt_id === attempt.attempt_id, "stale_thread");
      requireGate(input.title.trim().length > 0, "invalid_title");
      await caller.assertActive();
      requireGate(this.runtime, "native_runtime_required");
      const live = await this.runtime.readThread(caller.thread);
      requireGate(
        !live.error &&
          live.workspace === (attempt?.workspace ?? task.repo) &&
          live.provider === (binding.attachment?.modelSelection.provider ?? "codex") &&
          !live.archived &&
          live.running &&
          !live.blocked &&
          live.turn === caller.turn,
        "identity_conflict",
      );
      await caller.assertActive();
      const issueId = randomUUID();
      const number =
        Number(
          this.db
            .prepare(
              "SELECT count(*) AS count FROM issue_records WHERE thread=? AND json_extract(data,'$.kind')='issue'",
            )
            .get(caller.thread)!.count,
        ) + 1;
      const issue: A2AIssueRecord = {
        id: issueId,
        schema: 1,
        kind: "issue",
        from: `${binding.role}:${caller.thread}`,
        to: "triage",
        reply_to: null,
        refs: [
          `task:${task.task_id}`,
          ...(attempt ? [`attempt:${attempt.attempt_id}`] : []),
          `thread:${caller.thread}`,
          `turn:${caller.turn}`,
          ...input.refs,
        ],
        created_at: new Date(this.now()).toISOString(),
        body: input.body,
        task_id: task.task_id,
        attempt_id: attempt?.attempt_id ?? null,
        thread_id: caller.thread,
        turn_id: caller.turn,
        number,
        title: input.title,
        blocking: input.blocking,
        issue_id: issueId,
      };
      this.db.exec("BEGIN IMMEDIATE");
      try {
        this.appendIssue(issue);
        this.db.exec("COMMIT");
      } finally {
        if (this.db.isTransaction) this.db.exec("ROLLBACK");
      }
      return { ok: true, id: issueId, number };
    } finally {
      lock.close();
    }
  }
  private async disposeIssue(
    args: A2AGateRequest,
    caller?: SubmitCaller,
    actor = caller ? (caller.address ?? `controller:${caller.thread}`) : "user",
  ): Promise<A2AGateResult> {
    const view = this.readIssues(args.task).issues.find((entry) => entry.issue.id === args.issue);
    requireGate(view, "unknown_issue");
    requireGate(args.action, "invalid_action");
    if (args.action === "dismiss" || args.action === "snooze" || args.action === "reopen")
      requireGate(actor === "user", "user_required");
    if (args.action === "close") {
      requireGate(!view.issue.blocking || actor === "user", "blocking_requires_user");
      requireGate(args.reason?.trim() && args.basis?.trim(), "close_requires_reason_basis");
    }
    if (args.action === "delivered")
      requireGate(
        view.answer?.input_id &&
          view.answer.message_id &&
          view.answer.bundle_id &&
          this.readIssues(args.task).records.some(
            (record) =>
              record.issue_id === view.issue.id &&
              record.action === "delivered" &&
              record.message_id === view.answer!.message_id,
          ),
        "delivery_unconfirmed",
      );
    const record: A2AIssueRecord = {
      ...view.issue,
      id: randomUUID(),
      kind: "disposition",
      action: args.action,
      from: actor,
      to:
        args.action === "forward"
          ? "ideation"
          : args.action === "needs-user" || args.action === "reopen"
            ? "user"
            : "triage",
      reply_to: view.issue.id,
      body: args.body ?? args.reason ?? (args.action === "dismiss" ? "用户选择不处理" : ""),
      ...(args.reason !== undefined || args.action === "dismiss"
        ? { reason: args.reason ?? "用户选择不处理" }
        : {}),
      ...(args.basis !== undefined || args.action === "dismiss"
        ? { basis: args.basis ?? "用户直接选择不处理" }
        : {}),
      ...(args.action === "delivered"
        ? {
            input_id: view.answer!.input_id!,
            message_id: view.answer!.message_id!,
            bundle_id: view.answer!.bundle_id!,
          }
        : {}),
      created_at: new Date(this.now()).toISOString(),
      refs: [
        ...view.issue.refs,
        `issue:${view.issue.id}`,
        ...(caller ? [`actor-thread:${caller.thread}`] : []),
      ],
    };
    this.appendIssue(record);
    const delivery =
      record.to === "ideation" || record.to === "executor"
        ? await this.deliverInbox(record)
        : undefined;
    return {
      ok: true,
      ...this.readIssues(args.task),
      entry: record,
      ...(delivery ? { delivery } : {}),
    };
  }
  private async answerIssues(args: A2AGateRequest): Promise<A2AGateResult> {
    const replies =
      args.command === "answer_issue" ? [{ issue: args.issue, answer: args.answer }] : args.answers;
    requireGate(
      replies?.length && new Set(replies.map((reply) => reply.issue)).size === replies.length,
      "invalid_answers",
    );
    const { issues } = this.readIssues(args.task);
    const rows = replies.map((reply) => {
      const view = issues.find((view) => view.issue.id === reply.issue);
      requireGate(view, "unknown_issue");
      requireGate(view.state !== "已关闭", "issue_closed");
      requireGate(!view.answer, "issue_answered");
      requireGate(
        typeof reply.answer === "string" && reply.answer.trim().length > 0,
        "invalid_answer",
      );
      return { issue: view.issue, answer: reply.answer.trimEnd() };
    });
    requireGate(this.runtime?.sendUserAnswer, "native_runtime_required");
    const grouped = new Map<string, typeof rows>();
    for (const row of rows) {
      const key = args.mode === "individual" ? row.issue.id : row.issue.thread_id;
      grouped.set(key, [...(grouped.get(key) ?? []), row]);
    }
    const noticeThreads = new Set<string>();
    const groups = [...grouped.values()].map((replies) => {
      const thread = replies[0]!.issue.thread_id;
      const notices = noticeThreads.has(thread)
        ? []
        : this.readIssues(args.task, thread).issues.filter(
            (view) =>
              view.state === "已关闭" &&
              view.disposition &&
              !this.db
                .prepare(
                  "SELECT 1 FROM events WHERE task=? AND type='issue_closure_notified' AND json_extract(details,'$.close_id')=?",
                )
                .get(args.task, view.disposition.id),
          );
      noticeThreads.add(thread);
      const text = replies
        .map(({ issue, answer }) => {
          const chars = Array.from(issue.body);
          const body = chars.length > 600 ? chars.slice(0, 599).join("") + "…" : issue.body;
          return `问题 ${issue.number}：${issue.title}\n${body ? body + "\n" : ""}用户答复：${answer}`;
        })
        .join("\n\n");
      return {
        replies,
        thread,
        messageId: randomUUID(),
        bundleId: randomUUID(),
        notices,
        message:
          text +
          notices
            .map(
              (view) =>
                `\n\n（另：你上报的问题 ${view.issue.number} 已被关闭，理由：${view.disposition!.reason ?? view.disposition!.body}。如不同意，请重新上报并补充证据。）`,
            )
            .join(""),
        answers: [] as A2AIssueRecord[],
      };
    });
    const createdAt = new Date(this.now()).toISOString();
    // Input, answer, message registration and derived intervention are atomic.
    this.db.exec("BEGIN IMMEDIATE");
    try {
      for (const group of groups)
        for (const { issue, answer } of group.replies) {
          const inputId = randomUUID();
          const record: A2AIssueRecord = {
            ...issue,
            id: inputId,
            kind: "answer",
            from: "user",
            to: issue.from,
            reply_to: issue.id,
            created_at: createdAt,
            body: answer,
            input_id: inputId,
            message_id: group.messageId,
            bundle_id: group.bundleId,
            refs: [
              ...issue.refs,
              `issue:${issue.id}`,
              `input:${inputId}`,
              `message:${group.messageId}`,
            ],
          };
          const sequence = this.appendIssue(record);
          this.saveUserInput({
            id: inputId,
            schema: 1,
            form: "answer",
            text: answer,
            target: {
              task: issue.task_id,
              attempt: issue.attempt_id,
              thread: issue.thread_id,
              turn: null,
              message: group.messageId,
            },
            channel: "issue-panel",
            reply_to: issue.id,
            source_ref: {
              message_id: group.messageId,
              event_id: record.id,
              source_sequence: sequence,
            },
            certainty: "observed",
            created_at: createdAt,
            bundle_id: group.bundleId,
            question: { number: issue.number, title: issue.title, body: issue.body },
          });
          if (issue.attempt_id)
            this.event(
              issue.task_id,
              "human_intervention",
              {
                input_id: inputId,
                event_id: inputId,
                task_id: issue.task_id,
                attempt_id: issue.attempt_id,
                thread_id: issue.thread_id,
                message_id: group.messageId,
                dispatch_origin: "user",
                text: group.message,
              },
              issue.attempt_id,
            );
          group.answers.push(record);
        }
      this.db.exec("COMMIT");
    } finally {
      if (this.db.isTransaction) this.db.exec("ROLLBACK");
    }
    for (const group of groups) {
      const current = this.load(args.task).current_attempt;
      const binding = this.ownedThread(group.thread);
      let action: "delivered" | "forward" = "forward";
      if (
        (current &&
          current.thread_id === group.thread &&
          current.attempt_id === group.replies[0]!.issue.attempt_id &&
          !current.reclaimed) ||
        (binding?.attachment && group.replies[0]!.issue.attempt_id === null)
      ) {
        try {
          await this.runtime.sendUserAnswer(group.thread, group.messageId, group.message);
          action = "delivered";
          for (const view of group.notices)
            this.event(
              args.task,
              "issue_closure_notified",
              {
                close_id: view.disposition!.id,
                issue_id: view.issue.id,
                message_id: group.messageId,
              },
              view.issue.attempt_id,
            );
        } catch (error) {
          // Only an explicit terminal receipt permits forwarding. Unknown
          // delivery failures preserve the answer and remain errors.
          if (!(error instanceof Refusal) || error.code !== "session_ended") throw error;
        }
      }
      for (const record of group.answers) {
        const disposition: A2AIssueRecord = {
          ...record,
          id: randomUUID(),
          kind: "disposition",
          from: "system",
          to: action === "forward" ? "executor" : record.to,
          reply_to: record.id,
          body: action === "forward" ? "session-ended" : "",
          ...(action === "forward" ? { reason: "session-ended" } : {}),
          action,
          created_at: new Date(this.now()).toISOString(),
        };
        this.appendIssue(disposition);
        if (action === "forward") await this.deliverInbox(disposition);
      }
    }
    return { ok: true, ...this.readIssues(args.task) };
  }
  private event(task: string, type: string, details: unknown, expectedAttempt?: string | null) {
    this.checkUserInputObserver();
    const row = this.db.prepare("SELECT data FROM tasks WHERE id=?").get(task);
    const current = row ? (JSON.parse(String(row.data)) as A2ATask).current_attempt : null;
    const inserted = this.db
      .prepare("INSERT INTO events(time,task,attempt,type,details) VALUES (?,?,?,?,?)")
      .run(
        new Date().toISOString(),
        task,
        expectedAttempt === undefined ? (current?.attempt_id ?? null) : expectedAttempt,
        type,
        JSON.stringify(details),
      );
    return Number(inserted.lastInsertRowid);
  }
  private load(task: string): A2ATask {
    const row = this.db.prepare("SELECT data FROM tasks WHERE id=?").get(task);
    requireGate(row, "unknown_task");
    return JSON.parse(String(row.data)) as A2ATask;
  }
  private save(
    task: A2ATask,
    type: string,
    details: unknown = task,
    historicalAttempt?: A2AAttempt,
  ) {
    this.checkUserInputObserver();
    const ownsTransaction = !this.db.isTransaction;
    if (ownsTransaction) this.db.exec("BEGIN IMMEDIATE");
    try {
      this.db
        .prepare(
          "INSERT INTO tasks(id,data) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
        )
        .run(task.task_id, JSON.stringify(task));
      if (task.current_attempt)
        this.db
          .prepare(
            "INSERT INTO attempts(id,data) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
          )
          .run(task.current_attempt.attempt_id, JSON.stringify(task.current_attempt));
      if (historicalAttempt)
        this.db
          .prepare(
            "INSERT INTO attempts(id,data) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
          )
          .run(historicalAttempt.attempt_id, JSON.stringify(historicalAttempt));
      if (task.verification)
        this.db
          .prepare(
            "INSERT INTO verifications(id,data) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
          )
          .run(task.verification.verification_id, JSON.stringify(task.verification));
      this.event(task.task_id, type, details, historicalAttempt?.attempt_id);
      if (ownsTransaction) this.db.exec("COMMIT");
    } finally {
      if (ownsTransaction && this.db.isTransaction) this.db.exec("ROLLBACK");
    }
  }
  private cardVersion(task: string, version: number | undefined): TaskCard {
    requireGate(Number.isSafeInteger(version) && version! > 0, "invalid_card_version");
    const row = this.db.prepare("SELECT data FROM task_card_versions WHERE task=? AND version=?").get(task, version!);
    requireGate(row, "unknown_card_version");
    return JSON.parse(String(row.data)) as TaskCard;
  }
  private cardSnapshot(task: string, version: number, card: TaskCard, attempt: string | null = null) {
    const snapshot = randomUUID();
    this.db.prepare("INSERT INTO task_card_snapshots(id,task,version,attempt,data) VALUES (?,?,?,?,?)")
      .run(snapshot, task, version, attempt, JSON.stringify(card));
    return snapshot;
  }
  private boundCard(attempt: A2AAttempt): TaskCard {
    const row = this.db.prepare("SELECT data FROM task_card_snapshots WHERE id=? AND task=? AND attempt=?")
      .get(attempt.card_snapshot_id, attempt.task_id, attempt.attempt_id);
    requireGate(row, "stale_card_snapshot");
    return JSON.parse(String(row.data)) as TaskCard;
  }
  private attemptName(attempt: A2AAttempt) {
    return `${attempt.task_id}-a${attempt.fence}`;
  }
  private projectWorktrees(task: A2ATask) {
    return join(this.root, "worktrees", id(task.project_id));
  }
  /** The caller holds the task operation lock. System issues never impersonate a worker. */
  private lifecycleIssue(task: A2ATask, attempt: A2AAttempt, reason: string, details: unknown) {
    const issueId = randomUUID();
    const number = Number(this.db.prepare(
      "SELECT count(*) AS n FROM issue_records WHERE thread=? AND json_extract(data,'$.kind')='issue'",
    ).get(attempt.thread_id)!.n) + 1;
    const issue: A2AIssueRecord = {
      id: issueId, issue_id: issueId, schema: 1, kind: "issue", from: "system", to: "executor",
      reply_to: null, refs: [`task:${task.task_id}`, `attempt:${attempt.attempt_id}`, `session:${attempt.session_id}`],
      created_at: new Date(this.now()).toISOString(), body: JSON.stringify({ reason, details }, null, 2),
      task_id: task.task_id, attempt_id: attempt.attempt_id, thread_id: attempt.thread_id,
      turn_id: attempt.turn_id ?? "", number, title: `worktree：${reason}`, blocking: true,
    };
    // inboxRecords includes issue_records; one append serves both query surfaces.
    this.appendIssue(issue);
  }
  private async checkClaimPaths(task: A2ATask, reason?: string) {
    if (reason !== undefined) text(reason);
    const common = await this.git(task.task_id, task.repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"]);
    const conflicts: { task: string; attempt: string; snapshot: string; paths: string[] }[] = [];
    const active = this.db.prepare("SELECT data FROM attempts").all()
      .map((row) => JSON.parse(String(row.data)) as A2AAttempt)
      .filter((a) => !a.reclaimed && a.cleanup?.state !== "removed" && (a.state !== "revoked" || Boolean(a.thread_id)));
    for (const a of active) {
      const owner = this.load(a.task_id);
      const otherCommon = await this.git(task.task_id, owner.repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"]);
      if (common !== otherCommon) continue;
      const paths = pathIntersection(task.card.paths, this.boundCard(a).paths);
      if (paths.length) conflicts.push({ task: owner.task_id, attempt: a.attempt_id, snapshot: a.card_snapshot_id, paths });
    }
    this.event(task.task_id, "claim_path_check", {
      common_dir: common, card_snapshot_id: task.card_snapshot_id, conflicts,
      reason: reason ?? null, actor: "executor", passed: !conflicts.length || Boolean(reason),
    }, null);
    requireGate(!conflicts.length || reason, "path_overlap", { conflicts });
  }
  private async retainCommit(task: A2ATask, ref: string, commit: string) {
    const previous = await this.git(task.task_id, task.repo, ["rev-parse", "--verify", "--quiet", ref], [0, 1]);
    requireGate(!previous || previous === commit, "retention_ref_conflict", { ref, expected: commit, actual: previous });
    if (!previous) await this.git(task.task_id, task.repo, ["update-ref", ref, commit, "0".repeat(commit.length)]);
    const actual = await this.git(task.task_id, task.repo, ["rev-parse", "--verify", ref]);
    requireGate(actual === commit, "retention_ref_conflict", { ref, expected: commit, actual });
    await this.commitExists(task.task_id, task.repo, actual);
  }
  private async cleanupAttempt(task: A2ATask, attempt: A2AAttempt) {
    if (attempt.cleanup?.state === "removed") return;
    if (attempt.thread_id && !attempt.reclaimed) {
      this.event(task.task_id, "worktree_cleanup_deferred", { reason: "worker_not_reclaimed", workspace: attempt.workspace }, attempt.attempt_id);
      return;
    }
    const preserve = (reason: string, details: unknown) => {
      attempt.cleanup = { ...attempt.cleanup, state: attempt.cleanup?.state === "pending" ? "pending" : "preserved", reason };
      this.save(task, "worktree_preserved", { reason, details, workspace: attempt.workspace }, attempt);
      this.lifecycleIssue(task, attempt, reason, details);
    };
    const last = this.db.prepare("SELECT data FROM verifications WHERE json_extract(data,'$.attempt.attempt_id')=? ORDER BY rowid DESC LIMIT 1")
      .get(attempt.attempt_id);
    if (last && ["running", "interrupted", "unknown"].includes((JSON.parse(String(last.data)) as A2AVerification).state)) {
      preserve("verification_unresolved", { verification: JSON.parse(String(last.data)) });
      return;
    }
    try {
      const expectedPath = join(this.projectWorktrees(task), this.attemptName(attempt));
      requireGate(attempt.workspace === expectedPath, "cleanup_identity_conflict", { expectedPath, actual: attempt.workspace });
      const branch = `refs/heads/a2a/${this.attemptName(attempt)}`;
      const ref = `refs/a2a/attempts/${task.task_id}/a${attempt.fence}`;
      const deleteBranch = attempt.state === "accepted";
      if (existsSync(attempt.workspace)) {
        requireGate(realpathSync(attempt.workspace) === attempt.workspace, "cleanup_identity_conflict");
        const registered = await this.git(task.task_id, task.repo, ["worktree", "list", "--porcelain", "-z"]);
        requireGate(registered.split("\0\0").some((block) => {
          const fields = block.split("\0");
          return fields.includes(`worktree ${attempt.workspace}`) && fields.includes(`branch ${branch}`);
        }), "cleanup_identity_conflict");
        const head = sha(await this.git(task.task_id, attempt.workspace, ["rev-parse", "HEAD"]));
        requireGate(await this.git(task.task_id, attempt.workspace, ["symbolic-ref", "--quiet", "HEAD"], [0, 1]) === branch,
          "cleanup_identity_conflict");
        requireGate(!deleteBranch || head === task.candidate_commit, "cleanup_unsubmitted_head", { head, candidate: task.candidate_commit });
        const status = await this.git(task.task_id, attempt.workspace, ["status", "--porcelain=v1", "--untracked-files=all"]);
        if (status) { preserve("dirty_worktree", { head, status }); return; }
        // The reference is durable before either destructive operation. Replays
        // may only finish this exact head and path, never adopt a new tip.
        await this.retainCommit(task, ref, head);
        attempt.cleanup = { state: "pending", head, branch, ref, delete_branch: deleteBranch };
        this.save(task, "worktree_cleanup_intent", { cleanup: attempt.cleanup, workspace: attempt.workspace }, attempt);
        await this.git(task.task_id, task.repo, ["worktree", "remove", attempt.workspace]);
      } else {
        requireGate(attempt.cleanup?.state === "pending" && attempt.cleanup.head && attempt.cleanup.ref === ref &&
          attempt.cleanup.branch === branch && attempt.cleanup.delete_branch === deleteBranch, "cleanup_unconfirmed");
        await this.retainCommit(task, ref, attempt.cleanup.head);
        const registered = await this.git(task.task_id, task.repo, ["worktree", "list", "--porcelain", "-z"]);
        requireGate(!registered.split("\0").includes(`worktree ${attempt.workspace}`), "cleanup_unconfirmed");
      }
      if (deleteBranch) {
        const current = await this.git(task.task_id, task.repo, ["rev-parse", "--verify", "--quiet", branch], [0, 1]);
        if (current) {
          requireGate(current === attempt.cleanup!.head, "cleanup_identity_conflict", { branch, current });
          await this.git(task.task_id, task.repo, ["update-ref", "-d", branch, current]);
        }
      }
      attempt.cleanup = { ...attempt.cleanup!, state: "removed" };
      this.save(task, "worktree_removed", { cleanup: attempt.cleanup, workspace: attempt.workspace }, attempt);
    } catch (error) {
      if (!(error instanceof Refusal) || ![
        "git_failed", "command_unknown", "command_timeout", "command_unavailable", "cleanup_identity_conflict",
        "cleanup_unsubmitted_head", "cleanup_unconfirmed", "retention_ref_conflict",
      ].includes(error.code)) throw error;
      preserve(error.code, error.details);
    }
  }
  private async cleanupVerification(task: A2ATask, attempt: A2AAttempt, v: A2AVerification) {
    if (v.cleanup === "removed") return;
    if (v.state === "merge_failed" && v.conflict) {
      // Only the recorded conflict in this private verifier may be aborted.
      // Unknown delivery/session states keep the original directory instead.
      requireGate(attempt.rework?.state === "delivered" || attempt.rework?.state === "replacing", "conflict_unresolved");
      try {
        requireGate(v.workspace === join(this.projectWorktrees(task), `${this.attemptName(attempt)}-verify-${v.ordinal}`),
          "cleanup_identity_conflict");
        requireGate(await this.git(task.task_id, v.workspace, ["rev-parse", "HEAD"]) === v.G, "cleanup_identity_conflict");
        const unmerged = await this.execute(task.task_id, ["git", "-C", v.workspace, "ls-files", "--unmerged", "-z"], v.workspace);
        const diff = await this.execute(task.task_id, ["git", "-C", v.workspace, "diff", "--binary", "--no-ext-diff", "--no-color"], v.workspace);
        requireGate(unmerged.returncode === 0 && unmerged.stdout === v.conflict.unmerged &&
          diff.returncode === 0 && diff.stdout === v.conflict.diff &&
          !(await this.git(task.task_id, v.workspace, ["ls-files", "--others", "--exclude-standard", "-z"])),
          "conflict_scene_changed");
        this.save(task, "verification_cleanup_intent", { verification_id: v.verification_id, conflict: v.conflict, workspace: v.workspace });
        await this.git(task.task_id, v.workspace, ["-c", "core.hooksPath=/dev/null", "merge", "--abort"]);
        requireGate(!(await this.git(task.task_id, v.workspace, ["status", "--porcelain=v1", "--untracked-files=all"])), "dirty_worktree");
        await this.git(task.task_id, task.repo, ["worktree", "remove", v.workspace]);
        v.cleanup = "removed";
        this.save(task, "verification_worktree_removed", { verification_id: v.verification_id, workspace: v.workspace });
      } catch (error) {
        if (!(error instanceof Refusal)) throw error;
        v.cleanup = "preserved";
        this.save(task, "verification_worktree_preserved", { verification_id: v.verification_id, reason: error.code, details: error.details });
        this.lifecycleIssue(task, attempt, "verification_cleanup_failed", { verification_id: v.verification_id, reason: error.code, details: error.details });
      }
      return;
    }
    if (!["passed", "failed"].includes(v.state) || !v.M) return;
    const ref = `refs/a2a/verifications/${task.task_id}/a${attempt.fence}/v${v.ordinal}`;
    await this.retainCommit(task, ref, v.M);
    v.retained_ref = ref;
    this.save(task, "verification_cleanup_intent", { verification_id: v.verification_id, workspace: v.workspace, ref, M: v.M });
    const result = await this.execute(task.task_id, ["git", "-C", task.repo, "worktree", "remove", v.workspace], task.repo);
    v.cleanup = result.returncode === 0 ? "removed" : "preserved";
    this.save(task, "verification_worktree_" + v.cleanup, { verification_id: v.verification_id, workspace: v.workspace, result });
    if (result.returncode !== 0) this.lifecycleIssue(task, attempt, "verification_cleanup_failed", { verification_id: v.verification_id, result });
  }
  private async execute(
    task: string,
    argv: string[],
    cwd: string,
    env?: NodeJS.ProcessEnv,
    input?: string,
  ): Promise<A2ACommandResult> {
    this.checkUserInputObserver();
    const command = argv[0];
    requireGate(command, "invalid_command");
    this.event(task, "command_intent", { argv, cwd, ...(input === undefined ? {} : { stdin: input }) });
    const result = await new Promise<A2ACommandResult>((resolve, reject) => {
      const child = execProcessFile(
        command,
        argv.slice(1),
        { cwd, env, encoding: "utf8", timeout: 60_000, maxBuffer: 4 * 1024 * 1024 },
        (error, stdout, stderr) => {
          const code = error && typeof error.code === "number" ? error.code : error ? null : 0;
          const record: A2ACommandResult = {
            argv,
            cwd,
            stdout,
            stderr,
            exit: code,
            returncode: code,
          };
          try {
            this.event(task, "command_result", record);
          } catch (recordingError) {
            reject(recordingError);
            return;
          }
          if (error && code === null) {
            const refusal = error.killed ? "command_timeout" : "command_unavailable";
            reject(new Refusal(refusal, { ...record, reason: error.message }));
          } else resolve(record);
        },
      );
      if (input !== undefined) child.stdin!.end(input);
    });
    return result;
  }
  private async git(
    task: string,
    repo: string,
    args: string[],
    allowed = [0],
    env?: NodeJS.ProcessEnv,
  ) {
    const result = await this.execute(task, ["git", "-C", repo, ...args], repo, env);
    requireGate(
      result.returncode !== null && allowed.includes(result.returncode),
      "git_failed",
      result,
    );
    requireGate(result.stdout !== null, "command_unknown", result);
    return result.stdout.trim();
  }
  private async commitExists(task: string, repo: string, commit: string) {
    sha(commit);
    requireGate(
      (await this.git(task, repo, ["cat-file", "-t", commit], [0, 128])) === "commit",
      "invalid_commit",
    );
  }
  private async ancestor(task: string, repo: string, old: string, candidate: string) {
    const result = await this.execute(
      task,
      ["git", "-C", repo, "merge-base", "--is-ancestor", old, candidate],
      repo,
    );
    requireGate(result.returncode === 0 || result.returncode === 1, "git_failed", result);
    return result.returncode === 0;
  }
  private checkVerification(
    task: A2ATask,
    attempt: A2AAttempt,
    v: A2AVerification | null,
  ): asserts v is A2AVerification {
    requireGate(
      v &&
        v.attempt.task_id === task.task_id &&
        v.attempt.attempt_id === attempt.attempt_id &&
        v.attempt.session_id === attempt.session_id &&
        v.attempt.fence === attempt.fence &&
        v.attempt.spec_rev === attempt.spec_rev &&
        v.attempt.base_commit === attempt.base_commit &&
        v.spec_rev === task.spec_rev &&
        v.C === task.candidate_commit &&
        v.card_snapshot_id === attempt.card_snapshot_id &&
        v.card_version === task.card_version,
      "stale_verification",
    );
    const row = this.db.prepare("SELECT data FROM verifications WHERE id=?").get(v.verification_id);
    requireGate(row && String(row.data) === JSON.stringify(v), "stale_verification");
  }
  private interruptVerification(task: A2ATask) {
    if (task.state !== "verifying") return;
    const v = task.verification;
    this.checkVerification(task, this.current(task), v);
    requireGate(v.state === "running" && !task.integration_intent, "needs_reconciliation");
    v.state = "interrupted";
    v.ended = new Date().toISOString();
    v.result ??= {
      argv: v.command_intent?.argv ?? [],
      cwd: v.workspace,
      exit: null,
      returncode: null,
      stdout: null,
      stderr: null,
      outcome: "unknown",
    };
    task.state = "submitted";
    this.save(task, "verification_interrupted", v);
  }
  private invalidate(task: A2ATask, reason: string) {
    this.interruptVerification(task);
    const previous = task.current_attempt;
    if (previous && !["abandoned", "upgraded"].includes(previous.state ?? "")) {
      previous.state = "revoked";
      previous.revocation_reason = reason;
    }
    task.current_attempt = null;
    task.state = "ready";
    task.candidate_commit = null;
    task.verification = null;
    task.integration_intent = null;
    this.save(
      task,
      "revoked",
      { reason, attempt: previous?.attempt_id, spec_rev: task.spec_rev, previous_attempt: previous },
      previous ?? undefined,
    );
  }
  /** The caller holds the task lock; all attempt creation uses this path. */
  private async claim(task: A2ATask, args: A2AGateRequest, run?: A2ARun, conflict?: A2AVerification): Promise<A2AGateResult> {
    const taskId = task.task_id;
    if (args.command === "dispatch") {
      requireGate(this.runtime, "runtime_required");
      requireGate(args.runtimeMode, "runtime_mode_required");
    }
    const owner = text(args.command === "claim" ? args.owner : taskId);
    requireGate(task.state === "ready" && !task.current_attempt, "already_claimed");
    // A claim reserves paths across tasks. The task lock alone cannot
    // serialize two different tasks that claim the same repository paths.
    const reservation = this.operationLock("$claims");
    let attempt: A2AAttempt;
    try {
      await this.checkClaimPaths(task, args.overlap_reason);
      const base = sha(await this.integration(task));
      attempt = {
        task_id: taskId,
        attempt_id: randomUUID(),
        session_id: randomUUID(),
        fence: task.fence + 1,
        spec_rev: task.spec_rev,
        thread_id: args.command === "dispatch" ? randomUUID() : "",
        runtime_mode: args.runtimeMode ?? "approval-required",
        turn_id: null,
        runtime_identity: null,
        workspace: "",
        base_commit: base,
        card_snapshot_id: "",
        reclaimed: false,
        owner,
        state: "preparing",
        ...(conflict ? { conflict_source: conflict.verification_id } : {}),
      };
      const boundCard: TaskCard = { ...structuredClone(task.card), base_commit: base,
        writer: { task_id: taskId, attempt_id: attempt.attempt_id, session_id: attempt.session_id,
          fence: attempt.fence, thread_id: attempt.thread_id } };
      attempt.card_snapshot_id = this.cardSnapshot(taskId, task.card_version, boundCard, attempt.attempt_id);
      attempt.workspace = join(this.projectWorktrees(task), this.attemptName(attempt));
      task.current_attempt = attempt;
      task.repair = null;
      task.review = null;
      task.fence = attempt.fence;
      task.state = "preparing";
      this.save(task, args.command === "dispatch" ? "dispatch_intent" : "claim_intent", {
        attempt,
        task,
        ...(args.command === "dispatch"
          ? { model: task.card.executor.model, reasoning_effort: task.card.executor.effort, requested_service_tier: "default" }
          : {}),
      });
      if (run) {
        run.attempt_id = attempt.attempt_id;
        run.thread_id = attempt.thread_id;
        this.saveRun(run, "run_bound");
      }
    } finally { reservation.close(); }
    mkdirSync(this.projectWorktrees(task), { recursive: true });
    try {
      await this.git(taskId, task.repo, [
        "worktree",
        "add",
        "-b",
        `a2a/${this.attemptName(attempt)}`,
        attempt.workspace,
        attempt.base_commit,
      ]);
    } catch (error) {
      task.state = "paused";
      attempt.state = "worktree_failed";
      this.save(task, "worktree_failed", { reason: String(error) });
      throw new Refusal("worktree_failed");
    }
    if (args.command === "dispatch") {
      this.checkUserInputObserver();
      await this.runtime!.createThread(task, attempt);
      this.member(task, attempt.thread_id, "worker");
      this.membership.bindPreset(attempt.thread_id, "worker");
      const live = await this.runtime!.readThread(attempt.thread_id);
      attempt.runtime_identity = { ...this.runtimeIdentity(attempt, live) };
      this.checkThread(attempt, live);
      requireGate(!live.blocked, "run_blocked", live);
    }
    attempt.state = "claimed";
    task.state = "claimed";
    this.save(task, "claimed");
    if (args.command === "claim") return { ok: true, attempt };
    const submit = {
      command: "submit",
      task: taskId,
      attempt: attempt.attempt_id,
      session: attempt.session_id,
      fence: attempt.fence,
      spec_rev: attempt.spec_rev,
      commit: "<FULL_COMMIT_SHA>",
    };
    const entry = [process.execPath, fileURLToPath(new URL("./cli.ts", import.meta.url)), "--state", this.root];
    const submitCommand = [...entry, "submit", "--task", taskId, "--attempt", attempt.attempt_id,
      "--session", attempt.session_id, "--fence", String(attempt.fence), "--spec-rev", String(attempt.spec_rev),
      "--commit", "FULL_COMMIT_SHA"].map((part) => "'" + part.replaceAll("'", "'\\''") + "'").join(" ");
    const prompt = `${JSON.stringify(this.boundCard(attempt), null, 2)}\n\n受管身份：${JSON.stringify(submit)}\nGit 写操作：把执行工具的工作目录设为本 attempt 的 worktree。git add <路径> 和 git commit … 必须各自作为一条独立的工具命令执行；不要与 cd、检查命令或彼此用 &&、分号、管道、换行、变量赋值或重定向拼接。git status、git diff、测试和 git rev-parse 另行执行。两条 Git 前缀 allow 规则只授权对应命令；若独立执行仍被沙箱拒绝，上报问题并结束，不重试或修改权限。\n完成并 Git 提交后，把 FULL_COMMIT_SHA 换成完整提交号，运行以下 CLI 显式交付：\n${submitCommand}\n本会话的 CLI 会将 submit、status、issue 请求写到 A2A_REQUEST_DIR 指向的本 attempt 专用 /tmp 目录；不直接连接 socket。queued=true 只表示已排队，不是门禁通过。最后结束回合，让 Stop hook 读取并转交；没有请求文件就不交付。请求文件不得进入 Git 提交。查状态用同一入口 status --task，问题上报用 issue --task --title --body。不要修改合同、验收程序或沙箱权限。`;
    const dispatchPrompt = conflict ? `${prompt}\n\n${this.conflictPrompt(task, conflict)}\n原 worker 会话已结束。请在本次新 attempt 的 worktree 内整理，使用本次身份提交；旧 C 只作参考，不照搬其旧 attempt 尾注。` : prompt;
    this.event(taskId, "prompt_intent", { thread: attempt.thread_id, prompt: dispatchPrompt });
    this.checkUserInputObserver();
    await this.runtime!.startThread(task, attempt, dispatchPrompt);
    const live = await this.runtime!.readThread(attempt.thread_id);
    this.bindObservedIdentity(attempt, live);
    attempt.turn_id = live.turn;
    this.save(task, "dispatched", { attempt });
    return { ok: true, task, attempt };
  }
  private conflictPrompt(task: A2ATask, v: A2AVerification) {
    return `验收合并发生内容冲突，尚未通过验收或集成。\n${JSON.stringify({
      task: task.task_id, verification: v.verification_id, integration_ref: task.integration_ref,
      G: v.G, C: v.C, files: v.conflict!.files,
      candidate_ref: v.conflict!.candidate_ref, base_ref: v.conflict!.base_ref,
      merge_stdout: v.result!.stdout, merge_stderr: v.result!.stderr,
    }, null, 2)}\n请检查工作分支最新头，以它为基线重新整理，自己解决冲突并保留任务要求的双方行为。不要直接选择 ours/theirs 覆盖另一方。不要更改任务卡、验收程序、门禁状态或权限。原提交和冲突证据已保留；程序没有改写 worker 工作区或工作分支。\n在允许路径内完成整理，重跑卡上全部完成条件，以本 attempt 的身份和尾注提交新的候选，再用派发时给出的 submit 命令显式重交完整提交号。仍使用各自独立的 git add、git commit 命令。新候选会重跑整串门禁并重新审查，旧候选的通过结论不能沿用。若最新头又发生变化而无法按此基线重交，请上报，不修改身份或绕过检查。`;
  }
  private async writeConflict(task: A2ATask, attempt: A2AAttempt, v: A2AVerification) {
    requireGate(v.conflict && v.C === task.candidate_commit, "stale_verification");
    const repair: NonNullable<A2AAttempt["rework"]> = {
      verification_id: v.verification_id, prior_candidate: v.C, base_commit: v.G,
      message_id: randomUUID(), prior_turn: attempt.turn_id, state: "pending",
    };
    attempt.rework = repair;
    attempt.state = "rework";
    task.state = "rework";
    this.save(task, "conflict_rework_intent", { repair, conflict: v.conflict });
    try {
      requireGate(this.runtime && attempt.thread_id, "conflict_worker_unavailable");
      const live = await this.runtime.readThread(attempt.thread_id);
      this.current(this.load(task.task_id), attempt.attempt_id);
      this.checkThread(attempt, live);
      requireGate(!live.error && !live.blocked, "conflict_session_unknown", live);
      if (live.stopped || live.session_ended) {
        requireGate(!live.running, "conflict_session_unknown", live);
        repair.state = "replacing";
        this.save(task, "conflict_replacement_intent", { repair, live });
        if (!live.stopped) await this.runtime.stopThread(attempt.thread_id);
        const stopped = await this.runtime.readThread(attempt.thread_id);
        this.checkThread(attempt, stopped);
        requireGate(stopped.stopped && !stopped.running && !stopped.error, "stop_unconfirmed", stopped);
        if (!stopped.archived) await this.runtime.archiveThread(attempt.thread_id);
        const archived = await this.runtime.readThread(attempt.thread_id);
        this.checkThread(attempt, archived);
        requireGate(archived.stopped && archived.archived && !archived.error, "reclaim_unconfirmed", archived);
        attempt.reclaimed = true;
        attempt.reclaimed_at = new Date().toISOString();
        this.member(task, attempt.thread_id, "worker", attempt.reclaimed_at);
        this.save(task, "reclaimed", { attempt, archived });
        await this.cleanupVerification(task, attempt, v);
        this.invalidate(task, "conflict_session_ended");
        await this.cleanupAttempt(task, attempt);
        // No inherited overlap exception: every new attempt must check the
        // current set of path owners through the same claim implementation.
        const next = await this.claim(task, { command: "dispatch", task: task.task_id, runtimeMode: attempt.runtime_mode }, undefined, v);
        repair.state = "replaced";
        repair.replacement_attempt = next.attempt!.attempt_id;
        this.save(task, "conflict_worker_replaced", { repair, original_attempt: attempt.attempt_id }, attempt);
        return;
      }
      requireGate(!live.archived && this.runtime.sendGateFeedback, "conflict_worker_unavailable", live);
      const message = this.conflictPrompt(task, v);
      this.event(task.task_id, "conflict_feedback_intent", { message_id: repair.message_id, thread: attempt.thread_id, text: message });
      await this.runtime.sendGateFeedback(attempt.thread_id, repair.message_id, message);
      repair.state = "delivered";
      // A repair explicitly opens a new submission turn. Native identity and
      // the attempt/session/fence/card bindings are not replaced by that turn.
      attempt.turn_id = null;
      this.save(task, "conflict_feedback_delivered", { repair });
    } catch (error) {
      // This includes the external send/stop/create boundary: a missing receipt
      // is unknown, never permission to repeat a delivery or spawn.
      repair.state = "unknown";
      repair.failure = { reason: error instanceof Refusal ? error.code : "conflict_external_unknown",
        details: error instanceof Refusal ? error.details ?? null : String(error) };
      this.save(task, "conflict_rework_unknown", { repair }, attempt);
      this.lifecycleIssue(task, attempt, repair.failure.reason, { repair, verification_id: v.verification_id });
      return;
    }
    await this.cleanupVerification(task, attempt, v);
  }
  /** Called only while the original task operation lock is held. */
  private async verifyCandidate(task: A2ATask, attempt: A2AAttempt): Promise<A2AGateResult> {
    const taskId = task.task_id;
    this.interruptVerification(task);
    requireGate(!task.repair, task.repair?.stopped ? "quality_rejection_limit" : "repair_submission_required", task.repair);
    requireGate(task.state === "submitted" && task.candidate_commit, "not_submitted");
    requireGate(!task.integration_intent, "needs_reconciliation");
    requireGate(task.quality, "project_quality_snapshot_required");
    const G = sha(await this.integration(task)),
      C = task.candidate_commit;
    await this.commitExists(taskId, task.repo, G);
    if (attempt.rework?.state === "submitted") {
      const base = this.candidateBase(attempt, C);
      requireGate(await this.ancestor(taskId, task.repo, base, G) &&
        await this.ancestor(taskId, task.repo, base, C), "rework_baseline_changed", { base, G, C });
    }
    const verification_id = randomUUID();
    const ordinal = Number(this.db.prepare(
      "SELECT count(*) AS n FROM verifications WHERE json_extract(data,'$.attempt.attempt_id')=?",
    ).get(attempt.attempt_id)!.n) + 1;
    const workspace = join(this.projectWorktrees(task), `${this.attemptName(attempt)}-verify-${ordinal}`);
    const commands = this.boundCard(attempt).completion_conditions.map((command) => ({
      argv: command.argv.map((arg) => arg === "{worktree}" ? workspace : arg), cwd: workspace,
    }));
    const v: A2AVerification = {
      verification_id,
      ordinal,
      attempt: structuredClone(attempt),
      spec_rev: task.spec_rev,
      G,
      C,
      M: null,
      card_snapshot_id: attempt.card_snapshot_id,
      card_version: task.card_version,
      commands,
      results: [],
      workspace,
      state: "running",
      command_intent: commands[0],
      quality: { snapshot: structuredClone(task.quality), red: [], rules: [] },
    };
    task.verification = v;
    task.state = "verifying";
    this.save(task, "verification_intent", v);
    mkdirSync(this.projectWorktrees(task), { recursive: true });
    mkdirSync(join(this.root, "verification"), { recursive: true });
    if (await this.ancestor(taskId, task.repo, G, C)) {
      v.M = C;
      await this.git(taskId, task.repo, ["worktree", "add", "--detach", workspace, C]);
    } else {
      await this.git(taskId, task.repo, ["worktree", "add", "--detach", workspace, G]);
      const env = {
        ...process.env,
        GIT_AUTHOR_NAME: "A2A",
        GIT_AUTHOR_EMAIL: "a2a@localhost",
        GIT_COMMITTER_NAME: "A2A",
        GIT_COMMITTER_EMAIL: "a2a@localhost",
      };
      const merge = await this.execute(
        taskId,
        [
          "git",
          "-C",
          workspace,
          "-c",
          "core.hooksPath=/dev/null",
          "merge",
          "--no-ff",
          "--no-commit",
          "--no-edit",
          C,
        ],
        workspace,
        env,
      );
      if (merge.returncode !== 0) {
        v.state = "merge_failed";
        v.result = merge;
        v.ended = new Date().toISOString();
        task.state = "submitted";
        this.save(task, "verification_result", v);
        const unmerged = await this.execute(taskId, ["git", "-C", workspace, "ls-files", "--unmerged", "-z"], workspace);
        requireGate(unmerged.returncode === 0 && unmerged.stdout !== null, "git_failed", unmerged);
        if (merge.returncode !== 1 || !unmerged.stdout) throw new Refusal("git_failed", merge);
        const files = [...new Set(unmerged.stdout.split("\0").filter(Boolean).map((row) => {
          const tab = row.indexOf("\t");
          requireGate(tab > 0, "invalid_unmerged_entry", { row });
          return row.slice(tab + 1);
        }))];
        const diff = await this.execute(taskId, ["git", "-C", workspace, "diff", "--binary", "--no-ext-diff", "--no-color"], workspace);
        requireGate(diff.returncode === 0 && diff.stdout !== null, "git_failed", diff);
        const ref = `refs/a2a/verifications/${taskId}/a${attempt.fence}/v${ordinal}`;
        v.conflict = { files, unmerged: unmerged.stdout, diff: diff.stdout,
          candidate_ref: ref + "-candidate", base_ref: ref + "-base" };
        await this.retainCommit(task, v.conflict.candidate_ref, C);
        await this.retainCommit(task, v.conflict.base_ref, G);
        this.save(task, "verification_conflict", v);
        await this.writeConflict(task, attempt, v);
        throw new Refusal("merge_conflict", v);
      }
      const tree = await this.git(taskId, workspace, ["write-tree"]);
      v.M = await this.git(
        taskId,
        workspace,
        ["commit-tree", tree, "-p", G, "-p", C, "-m", `A2A managed integration ${taskId}`],
        [0],
        env,
      );
      await this.git(taskId, workspace, ["reset", "--hard", v.M]);
    }
    this.save(task, "merge_candidate", v);
    try { await this.checkPaths(task, attempt, v); }
    catch (error) {
      if (!(error instanceof Refusal)) throw error;
      v.state = "failed";
      v.ended = new Date().toISOString();
      task.state = "submitted";
      this.save(task, "verification_result", { verification: v, error: error.code, details: error.details });
      await this.cleanupVerification(task, attempt, v);
      await this.rejectDelivery(task, attempt, "path_boundary", { error: error.code, details: error.details });
      throw error;
    }
    try {
      for (const [index, command] of v.commands.entries()) {
        v.command_intent = command;
        // The next command has no result yet. Keep completed results separately.
        delete v.result;
        this.save(task, "completion_intent", { verification_id, card_snapshot_id: v.card_snapshot_id, index: index + 1, command });
        const started = new Date().toISOString();
        const result = await this.execute(taskId, command.argv, workspace);
        v.result = result;
        v.results.push(result);
        this.event(taskId, "completion_check", { verification_id, card_snapshot_id: v.card_snapshot_id,
          index: index + 1, result, started, ended: new Date().toISOString(), passed: result.returncode === 0 });
        if (result.returncode !== 0) break;
      }
      v.state = v.results.length === commands.length && v.results.every((result) => result.returncode === 0) ? "passed" : "failed";
      task.state = v.state === "passed" ? "reviewing" : "submitted";
    } catch (error) {
      if (!(error instanceof Refusal)) throw error;
      v.state = "unknown";
      task.state = "paused";
      v.result = {
        argv: v.command_intent!.argv,
        cwd: workspace,
        returncode: null,
        exit: null,
        stdout: null,
        stderr: null,
        outcome: "unknown",
      };
      v.ended = new Date().toISOString();
      this.save(task, "verification_result", { verification: v, failure: error.details });
      throw new Refusal("verification_unknown", v);
    }
    if (v.state === "passed") {
      v.state = "running"; task.state = "verifying";
      try {
        await this.checkQuality(task, attempt, v);
        this.checkQualityEvidence(task, attempt, v);
        v.state = "passed"; task.state = "reviewing";
      } catch (error) {
        const expected = error instanceof Refusal && ["red_state_failed", "red_test_file_invalid", "red_test_not_changed", "red_test_symlink", "rule_check_failed"].includes(error.code);
        v.state = expected ? "failed" : "unknown";
        task.state = expected ? "submitted" : "paused";
        v.ended = new Date(this.now()).toISOString();
        if (!expected) v.result = { ...v.command_intent!, stdout: null, stderr: null, exit: null, returncode: null, outcome: "unknown" };
        const failure = { error: error instanceof Refusal ? error.code : "quality_command_unknown",
          details: error instanceof Refusal ? error.details : String(error) };
        this.save(task, "verification_result", { task, verification: v, failure });
        if (expected) {
          await this.cleanupVerification(task, attempt, v);
          await this.rejectDelivery(task, attempt, failure.error === "rule_check_failed" ? "rule_checks" : "red_state", failure);
        }
        else this.qualityIssue(task, attempt, "质量检查结果未知，等待核对", failure);
        throw expected ? error : new Refusal("verification_unknown", failure);
      }
      try { await this.checkTrailers(task, attempt, v); }
      catch (error) {
        if (!(error instanceof Refusal)) throw error;
        v.state = "failed";
        v.ended = new Date().toISOString();
        task.state = "submitted";
        this.save(task, "verification_result", { verification: v, error: error.code, details: error.details });
        await this.cleanupVerification(task, attempt, v);
        await this.rejectDelivery(task, attempt, "commit_trailers", { error: error.code, details: error.details });
        throw error;
      }
    }
    v.ended = new Date().toISOString();
    this.save(task, "verification_result", { verification: v, task });
    await this.cleanupVerification(task, attempt, v);
    if (v.state !== "passed") {
      await this.rejectDelivery(task, attempt, "completion", { error: "oracle_failed", result: v.result });
      throw new Refusal("oracle_failed", v);
    }
    await this.requestReview(task, attempt);
    return { ok: true, task, verification: v };
  }
  private async integration(task: A2ATask) {
    return this.git(task.task_id, task.repo, ["rev-parse", "--verify", "--quiet", task.integration_ref], [0, 1]);
  }
  private async revalidateForIntegration(task: A2ATask, attempt: A2AAttempt, v: A2AVerification, actual: string) {
    await this.commitExists(task.task_id, task.repo, sha(actual));
    this.checkVerification(task, attempt, v);
    const previous = attempt.revalidation;
    const same = previous?.candidate_commit === v.C && previous.card_snapshot_id === v.card_snapshot_id &&
      previous.spec_rev === v.spec_rev;
    const misses = (same ? previous.misses : 0) + 1;
    attempt.revalidation = { candidate_commit: v.C, card_snapshot_id: v.card_snapshot_id,
      spec_rev: v.spec_rev, misses, previous_verification_id: v.verification_id };
    const abortedIntent = task.integration_intent;
    task.integration_intent = null;
    // Keep the previous verification row and its Git retention reference. The
    // counter is persisted before another oracle can start, including on replay.
    task.state = misses >= 4 ? "paused" : "submitted";
    this.save(task, "integration_compare_failed", { expected: v.G, actual, candidate: v.C, misses, aborted_intent: abortedIntent,
      verification_id: v.verification_id,
      review_reuse_binding: { candidate_commit: v.C, task_id: task.task_id, attempt_id: attempt.attempt_id,
        session_id: attempt.session_id, fence: attempt.fence, spec_rev: v.spec_rev, card_snapshot_id: v.card_snapshot_id } });
    if (misses >= 4) {
      this.lifecycleIssue(task, attempt, "integration_revalidation_limit", { misses, expected: v.G, actual,
        candidate: v.C, verification_id: v.verification_id });
      throw new Refusal("integration_revalidation_limit", { misses, attempt: attempt.attempt_id });
    }
    // Re-run the public verify request's quality and review chain while the
    // original task operation lock is still held.
    await this.verifyCandidate(task, attempt);
  }
  private async integrationWorktree(task: A2ATask): Promise<string | null> {
    const output = await this.git(task.task_id, task.repo, ["worktree", "list", "--porcelain", "-z"]);
    const matches: string[] = [];
    for (const block of output.split("\0\0")) {
      const fields = block.split("\0");
      if (!fields.includes("branch " + task.integration_ref)) continue;
      const path = fields.find((field) => field.startsWith("worktree "))?.slice(9);
      requireGate(path, "integration_worktree_unknown");
      matches.push(inputPath(path, true));
    }
    requireGate(matches.length <= 1, "integration_worktree_unknown", { matches });
    return matches[0] ?? null;
  }
  private async checkIntegrationHead(task: A2ATask, workspace: string | null) {
    requireGate(await this.integrationWorktree(task) === workspace, "integration_worktree_changed");
    if (workspace) {
      const ref = await this.git(task.task_id, workspace, ["symbolic-ref", "--quiet", "HEAD"], [0, 1]);
      requireGate(ref === task.integration_ref, "integration_worktree_changed", { workspace, ref });
    }
  }
  private async changedPaths(task: A2ATask, from: string, to: string): Promise<string[]> {
    const result = await this.execute(task.task_id,
      ["git", "-C", task.repo, "diff", "--name-only", "--no-renames", "-z", from, to, "--"], task.repo);
    requireGate(result.returncode === 0 && result.stdout !== null, "git_failed", result);
    return result.stdout.split("\0").filter(Boolean);
  }
  private async checkIntegratedContent(task: A2ATask, intent: NonNullable<A2ATask["integration_intent"]>) {
    await this.checkIntegrationHead(task, intent.worktree);
    if (!intent.worktree) return;
    const paths = await this.changedPaths(task, intent.G, intent.M);
    if (!paths.length) return;
    const result = await this.execute(task.task_id,
      ["git", "-C", intent.worktree, "diff", "--quiet", intent.M, "--", ...paths], intent.worktree);
    requireGate(result.returncode === 0, "needs_reconciliation", { intent_id: intent.intent_id, result });
  }
  private async advanceWorkBranch(task: A2ATask, intent: NonNullable<A2ATask["integration_intent"]>) {
    requireGate(await this.ancestor(task.task_id, task.repo, intent.G, intent.M), "integration_not_fast_forward");
    await this.checkIntegrationHead(task, intent.worktree);
    const cwd = intent.worktree ?? task.repo;
    const argv = intent.command_intent!.argv;
    this.event(task.task_id, "command_intent", { argv, cwd, protocol: { ref: intent.integration_ref, G: intent.G, M: intent.M } });
    const child = spawn(argv[0]!, argv.slice(1), { cwd, stdio: ["pipe", "pipe", "pipe"], timeout: 60_000 });
    let stdout = "", stderr = "", ioError: string | undefined;
    child.stdout.on("data", (chunk) => { stdout += String(chunk); });
    child.stderr.on("data", (chunk) => { stderr += String(chunk); });
    child.stdin.on("error", (error) => { ioError = String(error); });
    child.on("error", (error) => { ioError = String(error); });
    const closed = new Promise<A2ACommandResult>((resolve) => child.on("close", (code, signal) => {
      resolve({ argv, cwd, stdout, stderr, exit: code, returncode: code,
        ...(signal || ioError ? { outcome: ioError ?? String(signal) } : {}) });
    }));
    const reader = createInterface({ input: child.stdout });
    const lines = reader[Symbol.asyncIterator]();
    const send = async (input: string, expected: string) => {
      this.event(task.task_id, "git_transaction_input", { intent_id: intent.intent_id, stdin: input });
      child.stdin.write(input);
      const response = await lines.next();
      this.event(task.task_id, "git_transaction_response", { intent_id: intent.intent_id, response: response.value ?? null });
      requireGate(!response.done && response.value === expected, "needs_reconciliation", { expected, response: response.value });
    };
    let phase: "starting" | "preparing" | "prepared" | "committing" = "starting";
    let transactionFailure: unknown;
    try {
      await send("start\n", "start: ok");
      phase = "preparing";
      await send(`update ${intent.integration_ref} ${intent.M} ${intent.G}\nprepare\n`, "prepare: ok");
      phase = "prepared";
      if (intent.worktree) {
        for (const dryRun of [true, false]) {
          const result = await this.execute(task.task_id,
            ["git", "-C", cwd, "read-tree", ...(dryRun ? ["-n"] : []), "-m", "-u", intent.G, intent.M], cwd);
          requireGate(result.returncode === 0, "dirty_integration_worktree", { result, intent_id: intent.intent_id });
        }
        this.event(task.task_id, "integration_worktree_advanced", { intent_id: intent.intent_id, workspace: cwd, G: intent.G, M: intent.M });
      }
      await this.checkIntegrationHead(task, intent.worktree);
      phase = "committing";
      await send("commit\n", "commit: ok");
    } catch (error) {
      transactionFailure = error;
    } finally {
      // Closing stdin aborts an uncommitted Git transaction. Preserve its result.
      child.stdin.end();
      const result = await closed;
      reader.close();
      this.event(task.task_id, "command_result", result);
    }
    const result = await closed;
    if (transactionFailure) {
      // No worktree update can run before prepare succeeds. An exited, aborted
      // prepare plus a changed live ref proves a failed comparison. Missing I/O
      // receipts and every later phase retain the pending recovery intent.
      if (transactionFailure instanceof Refusal && transactionFailure.code === "needs_reconciliation" &&
          phase === "preparing" && result.returncode !== null && result.returncode !== 0 && !ioError) {
        const actual = await this.integration(task);
        if (actual && actual !== intent.G && actual !== intent.M)
          throw new Refusal("integration_compare_failed", { intent_id: intent.intent_id, actual, result });
      }
      throw transactionFailure;
    }
    requireGate(result.returncode === 0 && !ioError, "needs_reconciliation", result);
    return result;
  }
  private candidateBase(attempt: A2AAttempt, candidate: string) {
    if (attempt.rework?.state !== "submitted") return attempt.base_commit;
    requireGate(attempt.rework.candidate_commit === candidate, "stale_rework_candidate");
    return attempt.rework.base_commit;
  }
  private async checkPaths(task: A2ATask, attempt: A2AAttempt, v: A2AVerification) {
    const paths = new Set<string>();
    for (const [from, to] of [[this.candidateBase(attempt, v.C), v.C], [v.G, v.M!]]) {
      for (const path of await this.changedPaths(task, from!, to!)) paths.add(path);
    }
    const card = this.boundCard(attempt);
    const forbidden = [...paths].filter((path) => !pathAllowed(card, path));
    this.event(task.task_id, "path_check", { verification_id: v.verification_id, card_snapshot_id: v.card_snapshot_id,
      G: v.G, C: v.C, M: v.M, paths: [...paths], forbidden, rules: card.paths, passed: forbidden.length === 0 });
    requireGate(forbidden.length === 0, "path_boundary_failed", { forbidden });
  }
  private async projectQuality(taskId: string, repo: string, commit: string): Promise<ProjectQuality> {
    const path = ".a2a/quality.json" as const;
    const tree = await this.git(taskId, repo, ["ls-tree", "-z", commit, "--", path]);
    if (!tree) return { source_commit: commit, path, raw: null, rule_checks: [] };
    requireGate(/^(100644|100755) blob [a-f0-9]+\t\.a2a\/quality\.json\0$/.test(tree), "invalid_project_quality_file");
    const result = await this.execute(taskId, ["git", "-C", repo, "show", `${commit}:${path}`], repo);
    requireGate(result.returncode === 0 && result.stdout !== null, "git_failed", result);
    try { return { source_commit: commit, path, raw: result.stdout, rule_checks: projectRules(JSON.parse(result.stdout)) }; }
    catch (error) {
      if (error instanceof TaskCardError || error instanceof SyntaxError) throw new Refusal("invalid_project_quality", String(error));
      throw error;
    }
  }

  private async qualityCommand(task: A2ATask, v: A2AVerification, check: string, phase: string, argv: string[], workspace: string) {
    const command = { argv: argv.map((arg) => arg === "{worktree}" ? workspace : arg), cwd: workspace };
    v.command_intent = command; delete v.result;
    this.save(task, "quality_command_intent", { task, verification_id: v.verification_id, check, phase, command });
    const result = await this.execute(task.task_id, command.argv, workspace);
    v.result = result;
    return result;
  }

  private async checkQuality(task: A2ATask, attempt: A2AAttempt, v: A2AVerification) {
    const card = this.boundCard(attempt);
    requireGate(v.quality && task.quality, "project_quality_snapshot_required");
    for (const [index, command] of card.red_commands.entries()) {
      const base = join(this.root, "verification", `${v.verification_id}-red-base-${index + 1}`);
      const candidate = join(this.root, "verification", `${v.verification_id}-red-candidate-${index + 1}`);
      await this.git(task.task_id, task.repo, ["worktree", "add", "--detach", base, attempt.base_commit]);
      await this.git(task.task_id, task.repo, ["worktree", "add", "--detach", candidate, v.C]);
      for (const path of command.test_paths) {
        const tree = await this.git(task.task_id, task.repo, ["ls-tree", "-z", v.C, "--", path]);
        requireGate(/^(100644|100755) blob [a-f0-9]+\t/.test(tree) && tree.endsWith("\t" + path + "\0"), "red_test_file_invalid", { path, tree });
        const changed = await this.execute(task.task_id, ["git", "-C", task.repo, "diff", "--name-only", "--no-renames", "-z", attempt.base_commit, v.C, "--", path], task.repo);
        requireGate(changed.returncode === 0, "git_failed", changed);
        requireGate(changed.stdout === path + "\0", "red_test_not_changed", { path });
        // Only Git-tracked regular files in the explicit manifest are copied.
        // Reject a base-side symlink component instead of following it outside B.
        let target = base;
        const parts = path.split("/");
        for (const [partIndex, part] of parts.entries()) {
          target = join(target, part);
          try {
            const stat = lstatSync(target);
            requireGate(!stat.isSymbolicLink(), "red_test_symlink", { path, target });
            requireGate(partIndex < parts.length - 1 ? stat.isDirectory() : stat.isFile() && stat.nlink === 1,
              "red_test_file_invalid", { path, target });
          }
          catch (error) { if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error; }
        }
        mkdirSync(dirname(target), { recursive: true });
        // The isolated C checkout is never executed before this read. Git's
        // file mode above excludes symlinks and submodules on the source side.
        writeFileSync(target, readFileSync(join(candidate, path)), { mode: tree.startsWith("100755") ? 0o755 : 0o644 });
        chmodSync(target, tree.startsWith("100755") ? 0o755 : 0o644);
      }
      const baseResult = await this.qualityCommand(task, v, "red_state", "base-with-tests", command.argv, base);
      const candidateResult = await this.qualityCommand(task, v, "red_state", "candidate", command.argv, candidate);
      const passed = baseResult.returncode !== null && baseResult.returncode > 0 && candidateResult.returncode === 0;
      const record = { index: index + 1, B: attempt.base_commit, C: v.C, test_paths: command.test_paths,
        base_workspace: base, candidate_workspace: candidate, base_result: baseResult, candidate_result: candidateResult, passed };
      v.quality.red.push(record);
      this.save(task, "red_check", { task, verification_id: v.verification_id, ...record });
      requireGate(passed, "red_state_failed", record);
    }
    if (!card.red_commands.length) this.event(task.task_id, "red_not_applicable", { verification_id: v.verification_id });
    for (const rule of task.quality.rule_checks) {
      const result = await this.qualityCommand(task, v, "rule_checks", rule.id, rule.argv, v.workspace);
      const record = { id: rule.id, result, passed: result.returncode === 0 };
      v.quality.rules.push(record);
      this.save(task, "rule_check", { task, verification_id: v.verification_id, source_commit: task.quality.source_commit, ...record });
      requireGate(record.passed, "rule_check_failed", record);
    }
    if (!task.quality.rule_checks.length) this.event(task.task_id, "rules_not_applicable", {
      verification_id: v.verification_id, source_commit: task.quality.source_commit, configured: task.quality.raw !== null });
  }

  private checkQualityEvidence(task: A2ATask, attempt: A2AAttempt, v: A2AVerification) {
    const card = this.boundCard(attempt), quality = v.quality;
    requireGate(task.quality && quality && JSON.stringify(quality.snapshot) === JSON.stringify(task.quality) &&
      quality.red.length === card.red_commands.length && quality.rules.length === task.quality.rule_checks.length &&
      quality.red.every((record, index) => record.index === index + 1 && record.B === attempt.base_commit && record.C === v.C &&
        JSON.stringify(record.test_paths) === JSON.stringify(card.red_commands[index]!.test_paths) &&
        record.base_result.returncode !== null && record.base_result.returncode > 0 && record.candidate_result.returncode === 0 && record.passed) &&
      quality.rules.every((record, index) => record.id === task.quality!.rule_checks[index]!.id && record.result.returncode === 0 && record.passed),
      "quality_reverification_required");
  }
  private async checkTrailers(task: A2ATask, attempt: A2AAttempt, v: A2AVerification) {
    const commits = (await this.git(task.task_id, task.repo, ["rev-list", "--reverse", `${this.candidateBase(attempt, v.C)}..${v.C}`])).split("\n").filter(Boolean);
    const required = ["task", "attempt", "session", "role", "tool", "model", "effort", "native-session", "launch"];
    for (const commit of commits) {
      const message = await this.git(task.task_id, task.repo, ["show", "-s", "--format=%B", commit]);
      const parsed = await this.execute(task.task_id, ["git", "interpret-trailers", "--parse"], task.repo, undefined, message + "\n");
      requireGate(parsed.returncode === 0, "git_failed", parsed);
      const trailers: Record<string, string[]> = {};
      for (const line of (parsed.stdout ?? "").split("\n")) {
        const colon = line.indexOf(":");
        const key = line.slice(0, colon).toLowerCase();
        if (colon < 0 || !key.startsWith("a2a-")) continue;
        (trailers[key.slice(4)] ??= []).push(line.slice(colon + 1).trim());
      }
      let error: string | null = null;
      const missing = Object.keys(trailers).length === 0;
      if (!missing) {
        if (trailers.task?.some((value) => value !== task.task_id)) error = "trailer_task_mismatch";
        else if (Object.keys(trailers).length !== required.length ||
          required.some((key) => trailers[key]?.length !== 1 || !trailers[key]![0])) error = "invalid_trailers";
        else if (trailers.attempt![0] !== attempt.attempt_id || trailers.session![0] !== attempt.session_id || trailers.role![0] !== "worker")
          error = "trailer_identity_mismatch";
      }
      this.event(task.task_id, "trailer_check", { commit, trailers, verification_id: v.verification_id,
        card_snapshot_id: v.card_snapshot_id, passed: !error, missing, error });
      requireGate(!error, error ?? "invalid_trailers", { commit, trailers });
      if (missing) this.appendUserInput({
        id: randomUUID(), schema: 1, form: "action", text: `用户本人提交 ${commit}（推断：缺尾注）`,
        target: { project: task.project_id, task: task.task_id, attempt: attempt.attempt_id,
          thread: attempt.thread_id, turn: null, message: null },
        channel: "commit-trailer", reply_to: null,
        source_ref: { commit, label: "推断：缺尾注", event_id: `commit:${task.task_id}:${attempt.attempt_id}:${commit}` },
        certainty: "inferred", created_at: new Date(this.now()).toISOString(),
        content: { session_id: attempt.session_id, fence: attempt.fence, spec_rev: attempt.spec_rev, card_snapshot_id: v.card_snapshot_id },
      }, `commit:${task.task_id}:${attempt.attempt_id}:${commit}`);
    }
  }
  private current(task: A2ATask, expected?: string) {
    const attempt = task.current_attempt;
    requireGate(attempt && (!expected || attempt.attempt_id === expected), "stale_attempt");
    requireGate(
      attempt.task_id === task.task_id &&
        attempt.fence === task.fence &&
        attempt.spec_rev === task.spec_rev,
      "stale_attempt",
    );
    return attempt;
  }

  private qualityIssue(task: A2ATask, attempt: A2AAttempt, title: string, body: unknown, thread = attempt.thread_id) {
    const issueId = randomUUID();
    const number = Number(this.db.prepare("SELECT count(*) AS n FROM issue_records WHERE thread=? AND json_extract(data,'$.kind')='issue'")
      .get(thread)!.n) + 1;
    this.appendIssue({ id: issueId, schema: 1, kind: "issue", from: "system", to: "executor", reply_to: null,
      refs: [`task:${task.task_id}`, `attempt:${attempt.attempt_id}`], created_at: new Date(this.now()).toISOString(),
      body: JSON.stringify(body), task_id: task.task_id, attempt_id: attempt.attempt_id, thread_id: thread,
      turn_id: null, number, title, blocking: true, issue_id: issueId });
  }

  private async rejectDelivery(task: A2ATask, attempt: A2AAttempt, check: string, failure: unknown) {
    requireGate(task.verification && task.candidate_commit, "verification_required");
    if (task.repair?.verification_id === task.verification.verification_id) return;
    const count = Number(this.db.prepare("SELECT count(*) AS n FROM events WHERE task=? AND attempt=? AND type='delivery_rejected'")
      .get(task.task_id, attempt.attempt_id)!.n) + 1;
    const repair: A2ARepair = { id: randomUUID(), candidate_commit: task.candidate_commit,
      verification_id: task.verification.verification_id, check, count, stopped: count >= 3, failure };
    task.repair = repair;
    task.state = repair.stopped ? "paused" : "submitted";
    this.db.exec("BEGIN IMMEDIATE");
    try {
      this.save(task, "delivery_rejected", { task, repair });
      if (repair.stopped) this.qualityIssue(task, attempt, "同一 attempt 连续三次打回，停止自动回写", repair);
      this.db.exec("COMMIT");
    } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }
    if (!attempt.thread_id) {
      this.qualityIssue(task, attempt, "打回没有可回写的 worker 会话", repair);
      return;
    }
    requireGate(this.runtime?.qualityFeedback, "quality_feedback_runtime_required");
    this.current(this.load(task.task_id), attempt.attempt_id);
    const live = await this.runtime.readThread(attempt.thread_id);
    this.checkThread(attempt, live);
    requireGate(!live.error && !live.blocked && !live.stopped && !live.archived, "feedback_identity_unknown", live);
    await this.runtime.qualityFeedback(attempt, repair);
  }

  private reviewAttempt(review: A2AReview): A2AAttempt {
    return { ...review.attempt, session_id: review.session_id, thread_id: review.thread_id,
      workspace: review.workspace, runtime_identity: review.runtime_identity, turn_id: null };
  }

  private requireReviewed(task: A2ATask, attempt: A2AAttempt) {
    const review = task.review;
    requireGate(review && review.state === "passed" && review.result?.verdict === "可合并" &&
      review.task_id === task.task_id && review.attempt.attempt_id === attempt.attempt_id &&
      review.attempt.session_id === attempt.session_id && review.attempt.fence === attempt.fence &&
      review.spec_rev === task.spec_rev && review.card_snapshot_id === attempt.card_snapshot_id &&
      review.candidate_commit === task.candidate_commit, "review_required");
    const row = this.db.prepare("SELECT details FROM events WHERE task=? AND attempt=? AND type='review_result' AND json_extract(details,'$.review.review_id')=? ORDER BY seq DESC LIMIT 1")
      .get(task.task_id, attempt.attempt_id, review.review_id);
    requireGate(row && JSON.stringify(JSON.parse(String(row.details)).review) === JSON.stringify(review), "stale_review");
    return review;
  }

  private reviewLifecycleFailed(task: A2ATask, review: A2AReview, phase: string, details: unknown) {
    // A historical review must never pause or replace a newer attempt/result.
    const current = task.current_attempt?.attempt_id === review.attempt.attempt_id &&
      task.review?.review_id === review.review_id && !["accepted", "abandoned", "upgraded"].includes(task.state);
    if (current) { task.review!.state = "unknown"; task.state = "paused"; }
    this.db.exec("BEGIN IMMEDIATE");
    try {
      this.save(task, "review_lifecycle_failed", { task, review_id: review.review_id, phase, details, current });
      this.qualityIssue(task, review.attempt, "审查运行状态无法确认，停止自动推进", {
        review_id: review.review_id, phase, details, current }, review.thread_id);
      this.db.exec("COMMIT");
    } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }
  }

  recoverReviews() {
    // Called once at daemon startup. The new host cannot adopt old reviewers.
    for (const row of this.db.prepare("SELECT id FROM tasks").all()) {
      const taskId = String(row.id), lock = this.operationLock(taskId);
      try {
        const task = this.load(taskId), review = task.review;
        if (!review || !["requested", "running", "passed", "needs_fix"].includes(review.state)) continue;
        const ended = this.db.prepare("SELECT 1 FROM events WHERE task=? AND type='review_reclaimed' AND json_extract(details,'$.review_id')=?")
          .get(taskId, review.review_id);
        if (!ended) this.reviewLifecycleFailed(task, review, "daemon_restart", { reason: "reviewer_not_owned_by_this_daemon" });
      } finally { lock.close(); }
    }
  }

  private async requestReview(task: A2ATask, attempt: A2AAttempt) {
    const v = task.verification!;
    if (task.review?.state === "passed" && task.review.candidate_commit === v.C) {
      const review = this.requireReviewed(task, attempt);
      task.state = "verified";
      this.save(task, "review_reused", { task, review, verification_id: v.verification_id, G: v.G, M: v.M });
      return;
    }
    requireGate(this.runtime?.createReview, "review_runtime_required");
    const previous = task.review?.result?.findings ?? [];
    const reviewId = randomUUID();
    const ordinal = Number(this.db.prepare("SELECT count(*) AS n FROM events WHERE task=? AND attempt=? AND type='review_requested'")
      .get(task.task_id, attempt.attempt_id)!.n) + 1;
    const review: A2AReview = { review_id: reviewId, ordinal, task_id: task.task_id, attempt: { ...attempt },
      candidate_commit: v.C, spec_rev: task.spec_rev, card_snapshot_id: attempt.card_snapshot_id,
      verification_id: v.verification_id, thread_id: randomUUID(), session_id: randomUUID(),
      workspace: join(this.projectWorktrees(task), `${this.attemptName(attempt)}-review-${ordinal}`), requested_at: new Date(this.now()).toISOString(),
      launch_id: null, runtime_identity: null, state: "requested" };
    task.review = review; task.state = "reviewing";
    this.save(task, "review_requested", { task, review });
    try {
      await this.git(task.task_id, task.repo, ["worktree", "add", "--detach", review.workspace, v.C]);
      const diff = await this.git(task.task_id, task.repo, ["diff", "--no-ext-diff", "--no-renames", attempt.base_commit, v.C, "--"]);
      const shape = { schema: 1, request_id: "review-" + reviewId, command: "review_submit", task: task.task_id,
        attempt: attempt.attempt_id, session: review.session_id, fence: attempt.fence, spec_rev: task.spec_rev,
        review_id: reviewId, candidate_commit: v.C, verdict: "可合并或需修复", findings: [] };
      const prompt = `只读审查这一次交付，不实现或提交代码。独立判断候选是否满足任务卡；不要把机械通过当作审查结论。\n任务卡：\n${JSON.stringify(this.boundCard(attempt), null, 2)}\n候选改动：\n${diff}\n机械验收：\n${JSON.stringify(v, null, 2)}\n上一轮问题清单：\n${JSON.stringify(previous)}\n最终消息必须是一个完整 JSON 对象，不能加 Markdown 或说明文字。明确发起 review_submit，Stop hook 才会转交；结束回合本身不算交付。以下身份字段不可改；verdict 只选“可合并”或“需修复”。可合并时 findings 为空；需修复时每项为 {"location":{"path":"仓库相对路径","line":1},"failure_scenario":"具体失败场景","suggestion":"修复建议"}，至少一项。不能调用 worker 的 submit、不能集成、不能写请求文件。\n${JSON.stringify(shape, null, 2)}`;
      await this.runtime.createReview(task, review, prompt);
      const live = await this.runtime.readThread(review.thread_id);
      review.runtime_identity = { ...live.runtime_identity };
      review.launch_id = live.runtime_identity.launch;
      this.checkThread(this.reviewAttempt(review), live);
      review.state = "running";
      this.member(task, review.thread_id, "reviewer");
      this.save(task, "review_started", { task, review });
    } catch (error) {
      this.reviewLifecycleFailed(this.load(task.task_id), review, "create", {
        error: error instanceof Refusal ? error.code : String(error),
        details: error instanceof Refusal ? error.details : undefined });
      throw error;
    }
  }

  async failReviewProtocol(taskId: string, reviewId: string, details: unknown, caller: SubmitCaller) {
    const lock = this.operationLock(taskId);
    try {
      const task = this.load(taskId), attempt = this.current(task), review = task.review;
      requireGate(review?.review_id === reviewId && review.thread_id === caller.thread &&
        (review.state === "running" || review.state === "cancelled"), "stale_review");
      await caller.assertActive();
      if (review.state === "cancelled") {
        this.event(taskId, "review_after_termination", { review_id: reviewId, details }, attempt.attempt_id);
        return;
      }
      review.state = "unknown"; task.state = "paused";
      this.db.exec("BEGIN IMMEDIATE");
      try {
        this.save(task, "review_protocol_failed", { task, review, details });
        this.qualityIssue(task, attempt, "审查结论协议无效，已停止", details, review.thread_id);
        this.db.exec("COMMIT");
      } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }
    } finally { lock.close(); }
  }

  async reclaimReview(taskId: string, reviewId: string) {
    const lock = this.operationLock(taskId);
    try {
      const row = this.db.prepare("SELECT details FROM events WHERE task=? AND type='review_result' AND json_extract(details,'$.review.review_id')=? ORDER BY seq DESC LIMIT 1")
        .get(taskId, reviewId);
      requireGate(row && this.runtime, "review_result_required");
      const review = JSON.parse(String(row.details)).review as A2AReview;
      const done = this.db.prepare("SELECT 1 FROM events WHERE task=? AND type='review_reclaimed' AND json_extract(details,'$.review_id')=?")
        .get(taskId, reviewId);
      if (done) return;
      try {
        const live = await this.runtime.readThread(review.thread_id);
        this.checkThread(this.reviewAttempt(review), live);
        requireGate(!live.running && !live.blocked && !live.error, "reviewer_not_idle");
        this.event(taskId, "review_reclaim_intent", { review_id: reviewId, thread: review.thread_id }, review.attempt.attempt_id);
        await this.runtime.stopThread(review.thread_id);
        await this.runtime.archiveThread(review.thread_id);
        const after = await this.runtime.readThread(review.thread_id);
        this.checkThread(this.reviewAttempt(review), after);
        requireGate(after.stopped && after.archived, "review_reclaim_unconfirmed");
        await this.cleanupReviewWorktree(this.load(taskId), review);
        this.member(this.load(taskId), review.thread_id, "reviewer", new Date(this.now()).toISOString());
        this.event(taskId, "review_reclaimed", { review_id: reviewId, thread: review.thread_id }, review.attempt.attempt_id);
      } catch (error) {
        this.reviewLifecycleFailed(this.load(taskId), review, "reclaim", {
          error: error instanceof Refusal ? error.code : String(error),
          details: error instanceof Refusal ? error.details : undefined });
        throw error;
      }
    } finally { lock.close(); }
  }

  private async cleanupReviewWorktree(task: A2ATask, review: A2AReview) {
    requireGate(review.result && ["passed", "needs_fix"].includes(review.state), "review_result_required");
    requireGate(review.task_id === task.task_id && review.attempt.task_id === task.task_id &&
      Number.isSafeInteger(review.ordinal) && review.ordinal > 0 &&
      review.workspace === join(this.projectWorktrees(task), `${this.attemptName(review.attempt)}-review-${review.ordinal}`),
      "review_cleanup_identity_unknown");
    requireGate(!lstatSync(review.workspace).isSymbolicLink() && realpathSync(review.workspace) === review.workspace,
      "review_cleanup_identity_unknown");
    const listed = await this.git(task.task_id, task.repo, ["worktree", "list", "--porcelain", "-z"]);
    requireGate(listed.split("\0").includes("worktree " + review.workspace), "review_cleanup_identity_unknown");
    requireGate(!(await this.git(task.task_id, review.workspace, ["symbolic-ref", "--quiet", "HEAD"], [0, 1])) &&
      await this.git(task.task_id, review.workspace, ["rev-parse", "HEAD"]) === review.candidate_commit,
      "review_cleanup_identity_unknown");
    requireGate(!(await this.git(task.task_id, review.workspace, ["status", "--porcelain=v1", "--untracked-files=all"])),
      "dirty_review_worktree");
    const binding = { review_id: review.review_id, workspace: review.workspace, candidate_commit: review.candidate_commit,
      ordinal: review.ordinal, attempt: review.attempt.attempt_id };
    this.event(task.task_id, "review_worktree_cleanup_intent", binding, review.attempt.attempt_id);
    await this.git(task.task_id, task.repo, ["worktree", "remove", review.workspace]);
    const after = await this.git(task.task_id, task.repo, ["worktree", "list", "--porcelain", "-z"]);
    requireGate(!existsSync(review.workspace) && !after.split("\0").includes("worktree " + review.workspace),
      "review_cleanup_unconfirmed");
    // Keep the review object exactly as stored by review_result. R8 validates
    // that immutable binding; cleanup is recorded in its own append-only events.
    this.event(task.task_id, "review_worktree_removed", binding, review.attempt.attempt_id);
  }

  private scoreData(path: string | undefined, command: "integrate" | "abandon" = "integrate") {
    requireGate(path, "score_required");
    let value: unknown;
    try { value = JSON.parse(readFileSync(inputPath(path), "utf8")); }
    catch (error) { if (error instanceof SyntaxError) throw new Refusal("invalid_score", "Invalid JSON."); throw error; }
    return executorScore(value, command);
  }

  private finalScore(task: A2ATask, attempt: A2AAttempt, intent: { score?: { score_id: string; data: Record<string, unknown> } },
    provenance: ScoreProvenance | undefined = attempt.delivery) {
    requireGate(intent.score && provenance, "score_provenance_required");
    const previous = this.db.prepare("SELECT details FROM events WHERE task=? AND attempt=? AND type='score_recorded'")
      .all(task.task_id, attempt.attempt_id);
    requireGate(previous.length === 0, "attempt_already_scored");
    const claimed = this.db.prepare("SELECT time FROM events WHERE task=? AND attempt=? AND type='claimed' ORDER BY seq LIMIT 1")
      .get(task.task_id, attempt.attempt_id);
    requireGate(claimed, "score_provenance_required");
    const delivery = provenance, now = this.now();
    const rejections: Record<string, number> = { identity_version: 0, path_boundary: 0, completion: 0,
      red_state: 0, rule_checks: 0, independent_review: 0, commit_trailers: 0 };
    const identityErrors = new Set(["stale_attempt", "stale_session", "stale_fence", "stale_spec", "stale_thread", "stale_turn",
      "identity_conflict", "invalid_commit", "not_descendant", "workspace_head_mismatch", "dirty_worktree", "candidate_conflict"]);
    let identityRejections = 0;
    for (const row of this.db.prepare("SELECT details FROM events WHERE task=? AND type='rejected'").all(task.task_id)) {
      const entry = JSON.parse(String(row.details));
      if (entry.input?.command === "submit" && entry.input.attempt === attempt.attempt_id && identityErrors.has(entry.error)) identityRejections++;
    }
    // Relay-only schema/identity refusals never reach the gate. Count each
    // durable request once, excluding gate refusals already counted above.
    for (const row of this.db.prepare("SELECT q.input,r.data FROM relay_requests q JOIN relay_results r ON r.key=q.key WHERE q.launch=? AND q.attempt=?")
      .all(delivery.launch_id, attempt.attempt_id)) {
      const input = JSON.parse(String(row.input)), result = JSON.parse(String(row.data));
      if (input.command === "submit" && ["relay_identity_mismatch", "invalid_relay_request"].includes(result.error)) identityRejections++;
    }
    rejections.identity_version = identityRejections;
    for (const row of this.db.prepare("SELECT details FROM events WHERE task=? AND attempt=? AND type='delivery_rejected'").all(task.task_id, attempt.attempt_id)) {
      const key = JSON.parse(String(row.details)).repair.check;
      requireGate(Object.hasOwn(rejections, key), "score_check_unknown", key); rejections[key]!++;
    }
    const score = { schema: 1, score_id: intent.score.score_id, created_at: new Date(now).toISOString(), source: "executor",
      launch_id: delivery.launch_id, project: task.project_id, task: task.task_id, attempt: attempt.attempt_id,
      cli: delivery.cli, model: delivery.model, effort: delivery.effort, data: intent.score.data,
      ...(intent.score.data.result === "放弃" ? {} : { facts: { task_type: task.card.task_type, complexity: task.card.complexity, delivery_rounds: delivery.number,
        elapsed_seconds: Math.max(0, Math.floor((now - Date.parse(String(claimed.time))) / 1000)),
        human_interventions: Number(this.db.prepare("SELECT count(*) AS n FROM events WHERE task=? AND attempt=? AND type='human_intervention'")
          .get(task.task_id, attempt.attempt_id)!.n), rejections } }) };
    this.event(task.task_id, "score_recorded", score, attempt.attempt_id);
  }

  private saveRun(run: A2ARun, type: string) {
    this.checkUserInputObserver();
    this.db.exec("BEGIN IMMEDIATE");
    try {
      this.db
        .prepare(
          "INSERT INTO runs(id,task,data) VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
        )
        .run(run.run_id, run.task_id, JSON.stringify(run));
      this.event(run.task_id, type, run, run.attempt_id ?? undefined);
      this.db.exec("COMMIT");
    } finally {
      if (this.db.isTransaction) this.db.exec("ROLLBACK");
    }
  }
  private runtimeIdentity(attempt: A2AAttempt, live: Awaited<ReturnType<GateRuntime["readThread"]>>) {
    const identity = live.runtime_identity;
    requireGate(identity && identity.thread === attempt.thread_id && typeof identity.launch === "string" &&
      identity.launch.length > 0 && Number.isInteger(identity.shell_pid) && identity.shell_pid > 0 &&
      (identity.leader_pid === null || Number.isInteger(identity.leader_pid) && identity.leader_pid > 0) &&
      (identity.native_session === null || typeof identity.native_session === "string" && identity.native_session.length > 0),
      "identity_conflict", { attempt, live });
    return identity;
  }
  private checkThread(attempt: A2AAttempt, live: Awaited<ReturnType<GateRuntime["readThread"]>>) {
    const identity = this.runtimeIdentity(attempt, live), bound = attempt.runtime_identity;
    requireGate(
      live.workspace === attempt.workspace &&
        live.provider === "codex" &&
        bound && identity.launch === bound.launch && identity.thread === bound.thread && identity.shell_pid === bound.shell_pid &&
        (bound.leader_pid === null || identity.leader_pid === bound.leader_pid) &&
        (bound.native_session === null || identity.native_session === bound.native_session),
      "identity_conflict",
      { attempt, live },
    );
  }
  private bindObservedIdentity(attempt: A2AAttempt, live: Awaited<ReturnType<GateRuntime["readThread"]>>) {
    this.checkThread(attempt, live);
    const bound = attempt.runtime_identity!, identity = live.runtime_identity;
    const changed = bound.leader_pid === null && identity.leader_pid !== null ||
      bound.native_session === null && identity.native_session !== null;
    if (bound.leader_pid === null) bound.leader_pid = identity.leader_pid;
    if (bound.native_session === null) bound.native_session = identity.native_session;
    return changed;
  }
  private checkErrorReclaim(live: Awaited<ReturnType<GateRuntime["readThread"]>>) {
    requireGate(
      !live.error ||
        (live.error.providerPresent === false &&
          live.error.activeTurn === null &&
          live.running === false &&
          live.blocked === false),
      "run_external_unknown",
      live,
    );
  }
  private async observeRun(run: A2ARun) {
    requireGate(!this.shuttingDown, "daemon_stopping");
    this.checkUserInputObserver();
    const attempt = this.current(this.load(run.task_id), run.attempt_id!);
    let live: Awaited<ReturnType<GateRuntime["readThread"]>>;
    try {
      live = await this.runtime!.readThread(attempt.thread_id);
    } catch (error) {
      this.current(this.load(run.task_id), run.attempt_id!);
      if (error instanceof Refusal) throw error;
      throw new Refusal("run_external_unknown", String(error));
    }
    requireGate(!this.shuttingDown, "daemon_stopping");
    this.current(this.load(run.task_id), run.attempt_id!);
    this.checkThread(attempt, live);
    requireGate(!live.error, "run_external_unknown", live);
    requireGate(!live.blocked, "run_blocked", live);
    requireGate(!live.archived && !live.stopped, "run_external_unknown", live);
    if (attempt.runtime_identity!.leader_pid === null && live.runtime_identity.leader_pid !== null ||
        attempt.runtime_identity!.native_session === null && live.runtime_identity.native_session !== null) {
      // Binding is an ordinary task mutation. Refuse a concurrent gate owner.
      const lock = new DatabaseSync(join(this.root, "locks", `${run.task_id}.sqlite3`));
      try {
        lock.exec("PRAGMA busy_timeout=0; BEGIN IMMEDIATE");
        const task = this.load(run.task_id);
        const current = this.current(task, run.attempt_id!);
        if (this.bindObservedIdentity(current, live)) this.save(task, "runtime_bound", { attempt: current });
      } finally {
        lock.close();
      }
    }
    return live;
  }
  private async waitForIdle(run: A2ARun) {
    const deadline = performance.now() + 60_000;
    for (;;) {
      requireGate(!this.shuttingDown, "daemon_stopping");
      const row = this.db.prepare("SELECT data FROM attempts WHERE id=?").get(run.attempt_id!);
      requireGate(row, "unknown_attempt");
      const attempt = JSON.parse(String(row.data)) as A2AAttempt;
      requireGate(
        attempt.task_id === run.task_id && attempt.thread_id === run.thread_id,
        "identity_conflict",
      );
      if (attempt.reclaimed) return;
      const live = await this.runtime!.readThread(attempt.thread_id);
      requireGate(!this.shuttingDown, "daemon_stopping");
      this.checkThread(attempt, live);
      requireGate(!live.error, "run_external_unknown", live);
      requireGate(!live.blocked, "run_blocked", live);
      if (!live.running) return;
      requireGate(performance.now() < deadline, "run_reclaim_deadline", live);
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }
  private async run(args: A2AGateRequest): Promise<A2AGateResult> {
    requireGate(Number.isSafeInteger(args.wait_seconds) && args.wait_seconds! > 0, "invalid_wait");
    requireGate(args.runtimeMode, "runtime_mode_required");
    requireGate(this.runtime, "runtime_required");
    this.load(args.task);
    const lock = new DatabaseSync(join(this.root, "locks", `${args.task}.run.sqlite3`));
    let run: A2ARun | undefined;
    try {
      lock.exec("PRAGMA busy_timeout=0");
      try {
        lock.exec("BEGIN IMMEDIATE");
      } catch (error) {
        if (
          (error as { errcode?: number }).errcode === 5 ||
          (error as Error).message.includes("database is locked")
        )
          throw new Refusal("run_busy");
        throw error;
      }
      run = {
        run_id: randomUUID(),
        task_id: args.task,
        attempt_id: null,
        thread_id: null,
        started: new Date().toISOString(),
        wait_seconds: args.wait_seconds!,
        phase: "dispatching",
        outcome: "running",
      };
      this.saveRun(run, "run_started");
      const dispatch = await this.request(
        { command: "dispatch", task: args.task, runtimeMode: args.runtimeMode, overlap_reason: args.overlap_reason },
        undefined,
        run,
      );
      requireGate(dispatch.ok, dispatch.error ?? "gate_failure", dispatch.details);
      run.phase = "waiting_submit";
      this.saveRun(run, "run_phase");
      const deadline = performance.now() + args.wait_seconds! * 1000;
      let previous = "";
      for (;;) {
        requireGate(!this.shuttingDown, "daemon_stopping");
        const initial = this.load(args.task);
        this.current(initial, run.attempt_id!);
        if (["accepted", "abandoned", "upgraded"].includes(initial.state)) break;
        requireGate(performance.now() < deadline, "run_deadline");
        const live = await this.observeRun(run);
        const task = this.load(args.task);
        const change = JSON.stringify({
          task_state: task.state,
          turn: live.turn,
          running: live.running,
          blocked: live.blocked ?? false,
        });
        if (change !== previous) {
          this.event(
            args.task,
            "run_observed",
            { run_id: run.run_id, live, task_state: task.state },
            run.attempt_id!,
          );
          previous = change;
        }
        requireGate(performance.now() < deadline, "run_deadline");
        requireGate(!task.repair?.stopped, "quality_rejection_limit", task.repair);
        requireGate(["claimed", "submitted", "reviewing", "verified", "integrating", "accepted", "abandoned", "upgraded"].includes(task.state), "run_state_changed", task.state);
        if (["accepted", "abandoned", "upgraded"].includes(task.state)) break;
        if (task.state === "submitted" && !task.repair) {
          run.phase = "verifying";
          this.saveRun(run, "run_phase");
          const verified = await this.request({ command: "verify", task: args.task, attempt: run.attempt_id! });
          const after = this.load(args.task);
          this.current(after, run.attempt_id!);
          if (!verified.ok) {
            requireGate(!after.repair?.stopped, "quality_rejection_limit", after.repair);
            requireGate(after.repair && (after.repair.failure as { error?: string })?.error === verified.error,
              verified.error ?? "gate_failure", verified.details);
          }
          continue;
        }
        const phase = task.repair ? "waiting_repair" : task.state === "reviewing" ? "reviewing" :
          task.state === "integrating" ? "integrating" : task.state === "verified" ? "waiting_executor" : "waiting_submit";
        if (run.phase !== phase) { run.phase = phase; this.saveRun(run, "run_phase"); }
        await new Promise((resolve) =>
          setTimeout(resolve, Math.min(100, Math.max(0, deadline - performance.now()))),
        );
      }
      run.phase = "reclaiming";
      this.saveRun(run, "run_phase");
      await this.waitForIdle(run);
      requireGate(!this.shuttingDown, "daemon_stopping");
      const cleanup = await this.request({
        command: "reclaim",
        task: args.task,
        attempt: run.attempt_id!,
      });
      requireGate(cleanup.ok, "run_reclaim_failed", cleanup);
      run.reclaimed = true;
      requireGate(!this.shuttingDown, "daemon_stopping");
      const finalState = this.load(args.task).state;
      run.outcome = finalState === "accepted" ? "completed" : finalState;
      run.ended = new Date().toISOString();
      this.saveRun(run, "run_finished");
      return { ok: true, task: this.load(args.task), run };
    } catch (error) {
      if (!run) throw error;
      const code =
        error instanceof Refusal
          ? error.code === "stale_attempt"
            ? "run_superseded"
            : error.code
          : "run_external_unknown";
      const details = error instanceof Refusal ? error.details : String(error);
      if (
        run.attempt_id &&
        (code === "run_superseded" || code === "run_deadline" &&
          !this.load(args.task).repair && !this.load(args.task).review)
      ) {
        try {
          await this.waitForIdle(run);
          requireGate(!this.shuttingDown, "daemon_stopping");
          const cleanup = await this.request({
            command: "reclaim",
            task: args.task,
            attempt: run.attempt_id,
          });
          requireGate(cleanup.ok, cleanup.error ?? "run_reclaim_failed", cleanup.details);
          run.reclaimed = true;
        } catch (cleanup) {
          run.cleanup_failure =
            cleanup instanceof Refusal
              ? { error: cleanup.code, details: cleanup.details }
              : String(cleanup);
        }
      }
      run.error = code;
      run.details = details;
      run.outcome =
        code === "run_deadline"
          ? "deadline"
          : code === "run_superseded"
            ? "superseded"
            : ["oracle_failed", "merge_failed"].includes(code)
              ? "verification_failed"
              : run.phase === "reclaiming"
                ? "integrated_reclaim_failed"
                : "paused";
      run.ended = new Date().toISOString();
      if (this.userInputObserver?.state === "failed") {
        // The write that failed may also prevent a final receipt. Keep the last
        // durable phase and expose the pause; never invent persisted evidence.
        return { ok: false, error: code, details, run };
      }
      this.saveRun(run, "run_finished");
      return { ok: false, error: code, details, task: this.load(args.task), run };
    } finally {
      lock.close();
    }
  }

  private inboxRecords(): A2AInboxEntry[] {
    return [
      ...this.db.prepare("SELECT data FROM inbox_records ORDER BY rowid").all(),
      ...this.db.prepare("SELECT data FROM issue_records ORDER BY rowid").all(),
    ].map((row) => JSON.parse(String(row.data)) as A2AInboxEntry);
  }
  private inboxEntry(entryId: string): A2AInboxEntry {
    const entry = this.inboxRecords().find((record) => record.id === entryId);
    requireGate(entry, "unknown_inbox_entry");
    return entry;
  }
  private inboxConfirmed(entryId: string, role: string): boolean {
    return this.inboxRecords().some(
      (record) => record.kind === "ack" && record.from === role && record.reply_to === entryId,
    );
  }
  private inboxIssueWaiting(issue: A2AInboxEntry, records: ReadonlyArray<A2AInboxEntry>): boolean {
    const native = this.db.prepare("SELECT task FROM issue_records WHERE id=?").get(issue.id);
    if (native)
      return (
        this.readIssues(String(native.task)).issues.find((view) => view.issue.id === issue.id)
          ?.state === "等你决定"
      );
    const last = records
      .filter(
        (entry) =>
          (entry.kind === "disposition" || entry.kind === "answer") &&
          (entry.reply_to === issue.id || entry.refs.includes(`issue:${issue.id}`)),
      )
      .at(-1);
    if (!last)
      return Boolean(issue.blocking) || this.now() - Date.parse(issue.created_at) >= 900_000;
    if (last.kind === "answer" || ["close", "dismiss", "delivered"].includes(last.action ?? ""))
      return false;
    if (last.action === "forward") return this.now() - Date.parse(last.created_at) >= 900_000;
    if (last.action === "snooze") return this.now() - Date.parse(last.created_at) >= 3_600_000;
    return true;
  }
  private appendInbox(entry: A2AInboxEntry): void {
    this.db
      .prepare("INSERT INTO inbox_records(id,data) VALUES (?,?)")
      .run(entry.id, JSON.stringify(entry));
  }
  private inboxDelivery(entry: string): A2AInboxDelivery | undefined {
    const row = this.db
      .prepare("SELECT data FROM inbox_deliveries WHERE entry=? ORDER BY seq DESC LIMIT 1")
      .get(entry);
    return row ? (JSON.parse(String(row.data)) as A2AInboxDelivery) : undefined;
  }
  private appendDelivery(receipt: A2AInboxDelivery): void {
    this.db
      .prepare("INSERT INTO inbox_deliveries(entry,data) VALUES (?,?)")
      .run(receipt.entry_id, JSON.stringify(receipt));
  }
  private async refreshInboxDelivery(entry: string): Promise<A2AInboxDelivery | undefined> {
    const previous = this.inboxDelivery(entry);
    if (previous?.state !== "queued") return previous;
    const lock = this.operationLock(`inbox-${entry}`);
    try {
      const current = this.inboxDelivery(entry)!;
      if (current.state !== "queued") return current;
      requireGate(current.thread && current.message && this.runtime?.readWakeDelivery, "wake_receipt_runtime_required");
      const observed = await this.runtime.readWakeDelivery(current.thread, current.message);
      requireGate(["queued", "delivered", "unknown"].includes(observed.state) && Number.isFinite(Date.parse(observed.at)), "invalid_wake_receipt");
      if (observed.state === "queued") return current;
      const receipt = { ...current, state: observed.state, created_at: observed.at };
      this.appendDelivery(receipt);
      return receipt;
    } finally { lock.close(); }
  }
  private ownedThread(thread: string) {
    const task = this.taskForThread(thread);
    if (task?.current_attempt && !task.current_attempt.reclaimed)
      return { task, role: "worker", attempt: task.current_attempt };
    const row = this.db.prepare("SELECT data FROM attachments WHERE id=?").get(thread);
    const attached = row ? (JSON.parse(String(row.data)) as A2AAttachment) : undefined;
    if (attached?.state === "active")
      return { task: this.load(attached.task_id), role: attached.role, attachment: attached };
    return undefined;
  }
  private async deliverInbox(entry: A2AInboxEntry): Promise<A2AInboxDelivery> {
    const lock = this.operationLock(`inbox-${entry.id}`);
    try {
      const previous = this.inboxDelivery(entry.id);
      // A persisted pending receipt is unknown, not permission to send again.
      if (previous) return previous;
      const created_at = new Date(this.now()).toISOString();
      this.appendDelivery({ state: "pending", entry_id: entry.id, created_at });
      let receipt: A2AInboxDelivery;
      try {
        requireGate(this.runtime?.wakeThread, "wake_runtime_required");
        const targets = this.membership
          .presetThreads(entry.to)
          .filter((thread) => this.ownedThread(thread));
        if (entry.to.includes(":")) {
          const [role, thread] = entry.to.split(":");
          if (thread && this.ownedThread(thread)?.role === role) targets.push(thread);
        }
        requireGate(
          targets.length === 1,
          targets.length ? "ambiguous_role_session" : "role_session_missing",
        );
        const thread = targets[0]!;
        const result = await this.runtime.wakeThread(thread, entry);
        requireGate(["queued", "delivered", "unknown"].includes(result.state), "invalid_wake_receipt");
        receipt = {
          state: result.state,
          entry_id: entry.id,
          created_at: new Date(this.now()).toISOString(),
          thread,
          message: result.message,
        };
      } catch (error) {
        // Delivery is the external boundary. Preserve the entry and a failure
        // receipt, without a retry, replacement target, or success claim.
        receipt = {
          state: error instanceof Refusal ? "undelivered" : "unknown",
          entry_id: entry.id,
          created_at: new Date(this.now()).toISOString(),
          reason: error instanceof Refusal ? error.code : String(error),
        };
      }
      this.appendDelivery(receipt);
      return receipt;
    } finally {
      lock.close();
    }
  }
  private async inboxCall(args: A2AInboxRequest, actor?: GateActor, caller?: SubmitCaller): Promise<A2AGateResult> {
    requireGate(actor?.address, "caller_identity_required");
    const role = actor.address;
    requireGate(
      /^(?:user|ideation|executor|system|triage|(?:worker|reviewer|monitor):[A-Za-z0-9_.-]+)$/.test(
        role,
      ),
      "invalid_address",
    );
    if (!["inbox_list", "inbox_ready"].includes(args.command)) await actor.assertActive();
    if (args.command === "inbox_ready") {
      requireGate(["ideation", "executor"].includes(role), "controller_required");
      requireGate(args.project, "project_required");
      const repos = new Set(this.db.prepare("SELECT data FROM tasks").all()
        .map(row => JSON.parse(String(row.data)) as A2ATask)
        .filter(task => task.project_id === args.project).map(task => task.repo));
      requireGate(repos.size === 1, repos.size ? "ambiguous_project" : "unknown_project");
      const result = readyTickets([...repos][0]!);
      return { ok: result.diagnostics.length === 0, ...result,
        ...(result.diagnostics.length ? { error: "invalid_ready_tickets" } : {}) };
    }
    if (args.command === "inbox_list") {
      const records = this.inboxRecords();
      return {
        ok: true,
        entries: await Promise.all(records
          .filter(
            (entry) =>
              entry.kind !== "ack" &&
              (role === "user"
                ? entry.kind === "issue" && this.inboxIssueWaiting(entry, records)
                : (entry.to === role ||
                    (entry.kind === "issue" &&
                      entry.to === "triage" &&
                      ["ideation", "executor"].includes(role))) &&
                  !this.inboxConfirmed(entry.id, role)),
          )
          .map(async (entry) => {
            const delivery = await this.refreshInboxDelivery(entry.id);
            return { entry, ...(delivery ? { delivery } : {}) };
          })),
      };
    }
    this.checkUserInputObserver();
    if (args.command === "inbox_ack" || args.kind === "ack") {
      const original = this.inboxEntry(args.id ?? args.reply_to ?? "");
      requireGate(original.kind !== "ack", "ack_is_terminal");
      requireGate(original.to === role, "recipient_required");
      if (args.command === "inbox_send")
        requireGate(args.to === original.from, "recipient_required");
      const lock = this.operationLock(`inbox-${original.id}`);
      let ack: A2AInboxEntry;
      try {
        const previous = this.inboxRecords().find(
          (entry) => entry.kind === "ack" && entry.from === role && entry.reply_to === original.id,
        );
        if (previous) {
          const delivery = await this.refreshInboxDelivery(previous.id);
          return {
            ok: delivery?.state === "delivered" || delivery?.state === "queued",
            entry: previous,
            ...(delivery ? { delivery } : {}),
            ...(!["delivered", "queued"].includes(delivery?.state ?? "") ? { error: "wake_undelivered" } : {}),
          };
        }
        ack = {
          id: randomUUID(),
          schema: 1,
          kind: "ack",
          from: role,
          to: original.from,
          reply_to: original.id,
          refs: [],
          created_at: new Date(this.now()).toISOString(),
          body: args.body ?? "确认收到。",
        };
        this.appendInbox(ack);
      } finally {
        lock.close();
      }
      const delivery = await this.deliverInbox(ack);
      return {
        ok: delivery.state === "delivered" || delivery.state === "queued",
        entry: ack,
        delivery,
        ...(!["delivered", "queued"].includes(delivery.state) ? { error: "wake_undelivered" } : {}),
      };
    }
    requireGate(
      !args.id && args.kind && args.to && args.body !== undefined,
      "inbox_arguments_required",
    );
    const handoffDirections: Partial<Record<A2AInboxEntry["kind"], readonly [string, string]>> = {
      assign: ["ideation", "executor"],
      revise: ["ideation", "executor"],
      cancel: ["ideation", "executor"],
      report: ["executor", "ideation"],
      "needs-decision": ["executor", "ideation"],
    };
    const direction = handoffDirections[args.kind];
    if (direction)
      requireGate(role === direction[0] && args.to === direction[1], "invalid_direction");
    if (args.kind === "issue")
      requireGate(
        /^(?:worker|reviewer|monitor):/.test(role) && args.to === "triage",
        "invalid_direction",
      );
    requireGate(
      /^(?:user|ideation|executor|system|triage|(?:worker|reviewer|monitor):[A-Za-z0-9_.-]+)$/.test(
        args.to,
      ),
      "invalid_address",
    );
    requireGate(
      (args.refs ?? []).every((ref) =>
        /^(?:ticket|task|attempt|thread|turn|message|request|input|issue|file|commit|worker):.+$/.test(
          ref,
        ),
      ),
      "invalid_reference",
    );
    const parent = args.reply_to ? this.inboxEntry(args.reply_to) : undefined;
    if (args.kind === "issue")
      requireGate(args.title?.trim() && args.to === "triage", "invalid_issue");
    else requireGate(!args.blocking, "blocking_only_for_issue");
    if (args.kind !== "answer")
      requireGate(
        args.certainty === undefined && args.bundle_id === undefined,
        "answer_fields_only_for_answer",
      );
    if (args.kind !== "disposition")
      requireGate(
        args.action === undefined && args.reason === undefined && args.basis === undefined,
        "disposition_fields_only_for_disposition",
      );
    if (args.kind === "disposition") {
      requireGate(parent?.kind === "issue" && args.action, "disposition_requires_issue");
      requireGate(
        ["executor", "ideation", "user", "system"].includes(role),
        "disposition_sender_required",
      );
      if (args.action === "close" || args.action === "dismiss")
        requireGate(!parent.blocking || role === "user", "blocking_requires_user");
      if (args.action === "dismiss") requireGate(role === "user", "user_required");
      if (args.action === "close")
        requireGate(args.reason?.trim() && args.basis?.trim(), "close_requires_reason_basis");
      const legacy = this.db.prepare("SELECT data FROM issue_records WHERE id=?").get(parent.id);
      if (legacy) {
        const issue = JSON.parse(String(legacy.data)) as A2AIssueRecord;
        if (caller) requireGate(["ideation", "executor"].includes(role), "controller_required");
        const lock = this.operationLock(issue.task_id);
        try {
          const result = await this.disposeIssue(
            {
              command: "disposition",
              task: issue.task_id,
              issue: issue.id,
              action: args.action,
              reason: args.reason,
              basis: args.basis,
              body: args.body,
            },
            caller,
            role,
          );
          return {
            ...result,
            ...(result.delivery && !["delivered", "queued"].includes(result.delivery.state)
              ? { ok: false, error: "wake_undelivered" }
              : {}),
          };
        } finally {
          lock.close();
        }
      }
    }
    if (args.kind === "stop")
      requireGate(
        ["ideation", "user"].includes(role) && args.to === "executor",
        "invalid_stop_sender",
      );
    if (args.kind === "answer")
      requireGate(role === "ideation" && args.to === "executor", "invalid_answer_sender");
    const entry: A2AInboxEntry = {
      id: randomUUID(),
      schema: 1,
      kind: args.kind,
      from: role,
      to: args.to,
      reply_to: parent?.id ?? null,
      refs: args.refs ?? [],
      created_at: new Date(this.now()).toISOString(),
      body: args.body,
      ...(args.title !== undefined ? { title: args.title } : {}),
      ...(args.kind === "issue" ? { blocking: args.blocking ?? false } : {}),
      ...(args.action ? { action: args.action } : {}),
      ...(args.reason !== undefined ? { reason: args.reason } : {}),
      ...(args.basis !== undefined ? { basis: args.basis } : {}),
      ...(args.kind === "answer"
        ? { certainty: "relayed", bundle_id: args.bundle_id ?? randomUUID() }
        : {}),
    };
    this.appendInbox(entry);
    const delivery = await this.deliverInbox(entry);
    return {
      ok: delivery.state === "delivered" || delivery.state === "queued",
      entry,
      delivery,
      ...(!["delivered", "queued"].includes(delivery.state) ? { error: "wake_undelivered" } : {}),
    };
  }
  private async emergencyStop(args: A2AStopRequest, actor?: GateActor): Promise<A2AGateResult> {
    requireGate(actor?.address, "caller_identity_required");
    requireGate(["ideation", "executor", "user"].includes(actor.address), "controller_required");
    await actor.assertActive();
    const stop = this.inboxEntry(args.stop_id);
    requireGate(
      stop.kind === "stop" && stop.to === "executor" && ["user", "ideation"].includes(stop.from),
      "stop_entry_required",
    );
    const target = this.ownedThread(args.thread);
    requireGate(
      target && ["worker", "reviewer", "monitor"].includes(target.role),
      "worker_target_required",
    );
    const taskLock = this.operationLock(target.task.task_id);
    let entryLock: DatabaseSync | undefined;
    try {
      entryLock = this.operationLock(`inbox-${stop.id}`);
      if (actor.address === "ideation") requireGate(this.now() - Date.parse(stop.created_at) > 120_000, "stop_too_early");
      requireGate(!this.inboxConfirmed(stop.id, "executor"), "stop_already_acknowledged");
      requireGate(
        stop.refs.includes(`thread:${args.thread}`) ||
          (target.attempt && stop.refs.includes(`attempt:${target.attempt.attempt_id}`)),
        "stop_target_mismatch",
      );
      requireGate(this.runtime?.interruptThread, "interrupt_runtime_required");
      const live = await this.runtime.readThread(args.thread);
      requireGate(
        !live.archived &&
          !live.error &&
          live.workspace === (target.attempt?.workspace ?? target.task.repo) &&
          live.provider === (target.attachment?.modelSelection.provider ?? "codex"),
        "identity_conflict",
      );
      await actor.assertActive();
      this.checkUserInputObserver();
      this.event(target.task.task_id, "emergency_interrupt_intent", { stop_id: stop.id, thread: args.thread, actor: actor.address },
        target.attempt?.attempt_id ?? null);
      await this.runtime.interruptThread(args.thread);
      this.event(
        target.task.task_id,
        "emergency_interrupt_requested",
        { stop_id: stop.id, thread: args.thread, actor: actor.address },
        target.attempt?.attempt_id ?? null,
      );
      return { ok: true, interruptRequested: true };
    } finally {
      entryLock?.close();
      taskLock.close();
    }
  }
  async call(raw: unknown, caller?: SubmitCaller, actor: GateActor | undefined = caller): Promise<A2AGateResult> {
    const command = (raw as { command?: unknown } | null)?.command;
    if (typeof command === "string" && (command.startsWith("inbox_") || command === "stop")) {
      try {
        return command === "stop"
          ? await this.emergencyStop(Schema.decodeUnknownSync(A2AStopRequest)(raw), actor)
          : await this.inboxCall(Schema.decodeUnknownSync(A2AInboxRequest)(raw), actor, caller);
      } catch (error) {
        return {
          ok: false,
          error: error instanceof Refusal ? error.code : "invalid_request",
          details: String(error),
        };
      }
    }
    const result = await this.request(raw, caller, undefined, actor);
    const observer = this.userInputObserverStatus();
    return { ...result, ...(observer ? { user_input_observer: observer } : {}) };
  }

  private async request(raw: unknown, caller?: SubmitCaller, run?: A2ARun, actor: GateActor | undefined = caller): Promise<A2AGateResult> {
    let taskId: string | undefined;
    let lock: DatabaseSync | undefined;
    try {
      const args = Schema.decodeUnknownSync(A2AGateRequest)(raw);
      taskId = id(args.task);
      if (args.attempt !== undefined) id(args.attempt);
      if (args.session !== undefined) id(args.session);
      if (args.command === "status")
        return { ok: true, task: this.load(taskId), ...this.readIssues(taskId) };
      if (args.command === "issues") {
        this.load(taskId);
        return { ok: true, ...this.readIssues(taskId, args.thread) };
      }
      if (args.command === "events") {
        const rows = this.db
          .prepare(
            "SELECT seq,time,task,attempt,type,details FROM events WHERE task=? ORDER BY seq",
          )
          .all(taskId);
        return {
          ok: true,
          events: rows.map((r) => ({
            seq: Number(r.seq),
            time: String(r.time),
            task: String(r.task),
            attempt: r.attempt === null ? null : String(r.attempt),
            type: String(r.type),
            details: JSON.parse(String(r.details)) as unknown,
          })),
        };
      }
      if (actor && !caller) {
        requireGate(["executor", "user"].includes(actor.address ?? ""), "controller_required");
        await actor.assertActive();
      }
      if (caller) {
        if (caller.address === "executor") await caller.assertActive();
        else if (args.command === "review_submit")
          requireGate(caller.address === "reviewer:" + caller.thread, "reviewer_required");
        else if (args.command !== "disposition")
          requireGate(
            args.command === "submit" && this.taskForThread(caller.thread)?.task_id === taskId,
            "stale_thread",
          );
      }
      this.checkUserInputObserver();
      if (args.command === "run") return await this.run(args);
      // A separate SQLite write transaction is the OS-released task operation lock.
      // Keep the inode, never unlink it. Main-state reads remain available during an oracle.
      lock = this.operationLock(taskId);
      if (args.command === "disposition") {
        if (caller) {
          const member = this.membership
            .list()
            .find((entry) => entry.taskId === taskId)
            ?.members.find((entry) => entry.threadId === caller.thread);
          requireGate(
            (member?.role === "controller" && !member.endedAt) ||
              (["ideation", "executor"].includes(caller.address ?? "") &&
                this.ownedThread(caller.thread)?.role === "controller"),
            "controller_required",
          );
          await caller.assertActive();
          requireGate(this.runtime, "native_runtime_required");
          const live = await this.runtime.readThread(caller.thread);
          requireGate(
            !live.error &&
              !live.archived &&
              !live.blocked &&
              live.running &&
              live.turn === caller.turn,
            "identity_conflict",
          );
          await caller.assertActive();
        }
        return await this.disposeIssue(args, caller, actor?.address);
      }
      if (args.command === "answer_issue" || args.command === "answer_issues")
        return await this.answerIssues(args);
      if (args.command === "card_template") {
        inputPath(args.repo, true);
        return { ok: true, card: taskCardTemplate(taskId, args.ticket) };
      }
      if (args.command === "card_show")
        return { ok: true, card: this.cardVersion(taskId, args.card_version), card_version: args.card_version };
      if (args.command === "card_validate" || args.command === "card_save") {
        let source: unknown;
        try { source = JSON.parse(readFileSync(inputPath(args.card), "utf8")); }
        catch (error) {
          if (error instanceof SyntaxError) throw new Refusal("invalid_task_card", { field: "card", reason: "Invalid JSON." });
          throw error;
        }
        const card = validateTaskCard(source, taskId);
        if (args.command === "card_validate") return { ok: true, card,
          details: { rules: "13 个字段；非目标与允许路径非空；完成条件为 argv；任务类型八选一；CLI 为 Claude Code 或 Codex。" } };
        requireGate(Number.isSafeInteger(args.expected_version) && args.expected_version! >= 0, "invalid_card_version");
        this.db.exec("BEGIN IMMEDIATE");
        try {
          const row = this.db.prepare("SELECT max(version) AS version FROM task_card_versions WHERE task=?").get(taskId)!;
          requireGate(Number(row.version ?? 0) === args.expected_version, "card_version_conflict");
          const version = args.expected_version! + 1;
          this.db.prepare("INSERT INTO task_card_versions(task,version,data,created_at) VALUES (?,?,?,?)")
            .run(taskId, version, JSON.stringify(card), new Date(this.now()).toISOString());
          this.event(taskId, "card_saved", { card, card_version: version }, null);
          this.db.exec("COMMIT");
          return { ok: true, card, card_version: version };
        } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }
      }
      if (args.command === "create") {
        requireGate(!this.db.prepare("SELECT 1 FROM tasks WHERE id=?").get(taskId), "task_exists");
        const repo = inputPath(args.repo, true);
        const card = validateTaskCard(this.cardVersion(taskId, args.card_version), taskId);
        const branch = text(args.branch);
        requireGate(branch.startsWith("refs/heads/"), "invalid_work_branch");
        await this.git(taskId, repo, ["check-ref-format", branch]);
        requireGate(
          (await this.git(taskId, repo, ["rev-parse", "--show-toplevel"])) === repo,
          "invalid_repo",
        );
        const base = sha(await this.git(taskId, repo, ["rev-parse", "--verify", branch]));
        await this.commitExists(taskId, repo, base);
        const quality = await this.projectQuality(taskId, repo, base);
        const other = this.db.prepare("SELECT data FROM tasks WHERE json_extract(data,'$.repo')=?").all(repo);
        requireGate(other.every((row) => JSON.parse(String(row.data)).integration_ref === branch), "project_branch_conflict");
        const task: A2ATask = {
          task_id: taskId,
          title: text(args.title ?? taskId),
          project_id: id(args.project ?? (this.runtime ? undefined : taskId)),
          repo,
          integration_ref: branch,
          card_snapshot_id: "",
          card_version: args.card_version!,
          card,
          base_commit: base,
          state: "creating",
          spec_rev: 1,
          fence: 0,
          current_attempt: null,
          candidate_commit: null,
          verification: null,
          integration_intent: null,
          quality,
        };
        requireGate(task.title!.length <= 240, "invalid_title");
        const membership = this.membership.list().find((item) => item.taskId === taskId);
        requireGate(
          !membership || membership.projectId === task.project_id,
          "gate_project_mismatch",
        );
        this.db.exec("BEGIN IMMEDIATE");
        try {
          task.card_snapshot_id = this.cardSnapshot(taskId, task.card_version, card);
          this.save(task, "create_intent");
          this.db.exec("COMMIT");
        } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }
        this.checkUserInputObserver();
        await this.runtime?.ensureProject(task.project_id, repo);
        this.taskMembership(task);
        task.state = "ready";
        this.save(task, "created");
        return { ok: true, task };
      }
      const task = this.load(taskId);
      requireGate(task.card_snapshot_id && task.integration_ref, "task_card_registration_required");
      if (args.command === "attach") {
        requireGate(this.runtime?.createAttachedThread, "runtime_required");
        requireGate(
          args.role && args.modelSelection && args.runtimeMode,
          "attachment_arguments_required",
        );
        const prompt = readFileSync(inputPath(args.instructions), "utf8");
        requireGate(prompt.trim(), "invalid_text");
        const preset = args.preset ?? (args.role !== "controller" ? args.role : undefined);
        if (preset)
          requireGate(
            args.role === (preset === "ideation" || preset === "executor" ? "controller" : preset),
            "preset_role_mismatch",
          );
        const attachment: A2AAttachment = {
          task_id: taskId,
          thread_id: randomUUID(),
          role: args.role,
          ...(preset ? { preset } : {}),
          modelSelection: args.modelSelection,
          runtime_mode: args.runtimeMode,
          state: "creating",
        };
        this.saveAttachment(attachment);
        if (preset) this.membership.bindPreset(attachment.thread_id, preset);
        await this.runtime.createAttachedThread(task, attachment, prompt);
        this.member(task, attachment.thread_id, attachment.role);
        attachment.state = "active";
        this.saveAttachment(attachment);
        this.event(taskId, "attached", { attachment, prompt }, null);
        return { ok: true, task, attachment };
      }
      if (args.command === "reclaim" && args.thread !== undefined) {
        requireGate(!args.attempt, "ambiguous_reclaim");
        const thread = id(args.thread);
        const row = this.db.prepare("SELECT data FROM attachments WHERE id=?").get(thread);
        requireGate(row, "unknown_attachment");
        const attachment = JSON.parse(String(row.data)) as A2AAttachment;
        requireGate(attachment.task_id === taskId, "stale_thread");
        requireGate(this.runtime, "runtime_required");
        if (attachment.state === "ended") {
          requireGate(attachment.ended_at, "reclaim_unconfirmed");
          this.member(task, thread, attachment.role, attachment.ended_at);
          return { ok: true, task, attachment };
        }
        const live = await this.runtime.readThread(thread);
        requireGate(
          live.workspace === task.repo && live.provider === attachment.modelSelection.provider,
          "identity_conflict",
        );
        this.checkErrorReclaim(live);
        requireGate(!live.blocked, "run_blocked", live);
        requireGate(!live.running, "worker_working");
        this.event(taskId, "attachment_reclaim_intent", { attachment, live }, null);
        let archived = live;
        // A failed bookkeeping write may follow confirmed native stop/archive.
        // Reconcile those observed facts without repeating the external effects.
        if (!(live.stopped && live.archived)) {
          await this.runtime.stopThread(thread);
          const stopped = await this.runtime.readThread(thread);
          requireGate(
            stopped.workspace === task.repo &&
              stopped.provider === attachment.modelSelection.provider &&
              stopped.stopped,
            "stop_unconfirmed",
          );
          await this.runtime.archiveThread(thread);
          archived = await this.runtime.readThread(thread);
        }
        requireGate(
          archived.workspace === task.repo &&
            archived.provider === attachment.modelSelection.provider &&
            archived.stopped &&
            archived.archived,
          "reclaim_unconfirmed",
        );
        attachment.state = "ended";
        attachment.ended_at = new Date().toISOString();
        this.db.exec("BEGIN IMMEDIATE");
        try {
          this.saveAttachment(attachment);
          this.event(taskId, "attachment_reclaimed", { attachment, archived }, null);
          this.db.exec("COMMIT");
        } finally {
          if (this.db.isTransaction) this.db.exec("ROLLBACK");
        }
        this.member(task, thread, attachment.role, attachment.ended_at);
        return { ok: true, task, attachment };
      }
      if (args.command === "revoke" || args.command === "revise") {
        requireGate(task.state !== "accepted", "already_accepted");
        requireGate(!task.integration_intent, "needs_reconciliation");
        const reason = args.command === "revoke" ? text(args.reason) : "spec revised";
        if (args.command === "revise")
          requireGate(
            Number.isSafeInteger(args.spec_rev) && args.spec_rev! > task.spec_rev,
            "stale_spec",
          );
        const revisedCard = args.command === "revise" && args.card_version !== undefined
          ? validateTaskCard(this.cardVersion(taskId, args.card_version), taskId) : null;
        // Retain the interrupted record under its old spec before revising.
        this.interruptVerification(task);
        if (args.command === "revise") {
          if (revisedCard) {
            task.card_snapshot_id = this.cardSnapshot(taskId, args.card_version!, revisedCard);
            task.card_version = args.card_version;
            task.card = revisedCard;
          }
          task.spec_rev = args.spec_rev!;
        }
        const previous = task.current_attempt;
        this.invalidate(task, reason);
        if (previous) await this.cleanupAttempt(task, previous);
        return { ok: true, task };
      }
      if (args.command === "dispatch" || args.command === "claim") return await this.claim(task, args, run);
      let historicalAttempt: A2AAttempt | undefined;
      if (
        args.command === "reclaim" &&
        args.attempt &&
        task.current_attempt?.attempt_id !== args.attempt
      ) {
        const row = this.db.prepare("SELECT data FROM attempts WHERE id=?").get(id(args.attempt));
        requireGate(row, "unknown_attempt");
        const previous = JSON.parse(String(row.data)) as A2AAttempt;
        requireGate(previous.task_id === taskId, "stale_attempt");
        if (previous.reclaimed) {
          await this.cleanupAttempt(task, previous);
          return { ok: true, task };
        }
        historicalAttempt = previous;
      }
      if (args.attempt && !historicalAttempt)
        requireGate(task.current_attempt?.attempt_id === args.attempt, "stale_attempt");
      if (args.command === "verify" && task.state === "rework")
        throw new Refusal("conflict_rework_required", task.current_attempt?.rework);
      if (args.command === "verify")
        requireGate(task.state === "submitted" || task.state === "verifying", "not_submitted");
      if (args.command === "integrate")
        requireGate(
          task.state === "verified" || task.state === "accepted" || task.integration_intent,
          "not_verified",
        );
      const attempt = historicalAttempt ?? this.current(task, args.attempt);
      if (args.command === "abandon") {
        requireGate(args.attempt === attempt.attempt_id, "stale_attempt");
        requireGate(!caller || caller.address === "executor", "executor_required");
        const data = this.scoreData(args.score_file, "abandon");
        requireGate(task.state !== "accepted", "already_accepted");
        requireGate(!task.integration_intent, "needs_reconciliation");
        if (["abandoned", "upgraded"].includes(task.state)) {
          const row = this.db.prepare("SELECT details FROM events WHERE task=? AND attempt=? AND type='score_recorded'")
            .get(taskId, attempt.attempt_id);
          requireGate(row && JSON.stringify(JSON.parse(String(row.details)).data) === JSON.stringify(data), "score_replay_mismatch");
          return { ok: true, task, replayed: true };
        }
        let provenance: ScoreProvenance | undefined = attempt.delivery;
        if (!provenance) {
          requireGate(this.runtime?.sessionFacts && attempt.thread_id && attempt.runtime_identity, "score_provenance_required");
          const facts = await this.runtime.sessionFacts(attempt.thread_id);
          requireGate(facts.launch.id === attempt.runtime_identity.launch && facts.launch.role === "worker", "score_provenance_required");
          provenance = { number: 0, launch_id: facts.launch.id,
            cli: facts.launch.cli_version, model: facts.model, effort: facts.effort };
        }
        if (task.repair && attempt.thread_id) {
          requireGate(this.runtime?.qualityFeedback, "quality_feedback_runtime_required");
          await this.runtime.qualityFeedback(attempt, { ...task.repair, stopped: true });
        }
        const pendingReview = task.review && ["requested", "running", "unknown"].includes(task.review.state) ? task.review : null;
        if (pendingReview) pendingReview.state = "cancelled";
        task.state = data.result === "放弃" ? "abandoned" : "upgraded";
        attempt.state = task.state;
        this.db.exec("BEGIN IMMEDIATE");
        try {
          this.save(task, "attempt_ended", { task, result: data.result });
          this.finalScore(task, attempt, { score: { score_id: "score-" + randomUUID(), data } }, provenance);
          if (pendingReview) this.qualityIssue(task, attempt, "attempt 已终结，未完成的审查会话仍待核对回收", {
            review_id: pendingReview.review_id, thread_id: pendingReview.thread_id, state: "cancelled" });
          this.db.exec("COMMIT");
        } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }
        return { ok: true, task, details: { cleanup: "not_performed", thread: attempt.thread_id, review_thread: pendingReview?.thread_id ?? null } };
      }
      if (args.command === "review_submit") {
        const review = task.review;
        requireGate(caller && this.runtime && review?.state === "running" &&
          args.review_id === review.review_id && caller.thread === review.thread_id, "reviewer_required");
        requireGate(args.attempt === attempt.attempt_id && args.session === review.session_id &&
          args.fence === attempt.fence && args.spec_rev === task.spec_rev &&
          review.attempt.session_id === attempt.session_id && review.attempt.fence === attempt.fence &&
          review.spec_rev === task.spec_rev && review.card_snapshot_id === attempt.card_snapshot_id,
          "stale_review");
        requireGate(args.candidate_commit === task.candidate_commit && args.candidate_commit === review.candidate_commit,
          "review_candidate_mismatch");
        requireGate(task.state === "reviewing" && task.verification?.state === "passed" &&
          task.verification.verification_id === review.verification_id, "review_verification_mismatch");
        this.checkVerification(task, attempt, task.verification);
        this.checkQualityEvidence(task, attempt, task.verification);
        await caller.assertActive();
        const live = await this.runtime.readThread(review.thread_id);
        const bound = this.reviewAttempt(review);
        this.bindObservedIdentity(bound, live);
        requireGate(!live.error && !live.blocked && live.running && live.turn === caller.turn &&
          live.runtime_identity.native_session && live.runtime_identity.leader_pid, "review_identity_unknown");
        const launchRow = this.db.prepare("SELECT data FROM launch_records WHERE id=?").get(review.launch_id!);
        const launch = launchRow ? JSON.parse(String(launchRow.data)) : null;
        requireGate(launch && launch.role === "reviewer" && launch.review_id === review.review_id &&
          launch.review_verification_id === review.verification_id && launch.session === review.session_id &&
          launch.thread === review.thread_id && launch.attempt === attempt.attempt_id && launch.sandbox === "read-only" &&
          launch.review_home_was_empty === true && launch.argv[launch.argv.indexOf("--sandbox") + 1] === "read-only" &&
          !launch.argv.some((arg: string) => ["resume", "fork", "--resume", "--fork"].includes(arg)), "review_not_fresh");
        requireGate(review.thread_id !== attempt.thread_id && review.session_id !== attempt.session_id &&
          review.launch_id !== attempt.runtime_identity?.launch &&
          live.runtime_identity.native_session !== attempt.runtime_identity?.native_session, "review_writer_conflict");
        const reused = this.db.prepare("SELECT 1 FROM orchestration_events WHERE type='native_record' AND launch!=? AND json_extract(data,'$.record.type')='session_meta' AND json_extract(data,'$.record.payload.id')=? LIMIT 1")
          .get(review.launch_id!, live.runtime_identity.native_session);
        requireGate(!reused, "review_native_session_reused");
        const verdict = reviewVerdict(args.verdict, args.findings);
        review.runtime_identity = bound.runtime_identity;
        review.result = { ...verdict, turn_id: caller.turn, received_at: new Date(this.now()).toISOString() };
        review.state = verdict.verdict === "可合并" ? "passed" : "needs_fix";
        task.state = review.state === "passed" ? "verified" : "submitted";
        this.save(task, "review_result", { task, review });
        if (review.state === "needs_fix") await this.rejectDelivery(task, attempt, "independent_review", review.result);
        return { ok: true, task };
      }
      if (args.command === "submit") {
        requireGate(args.attempt === attempt.attempt_id, "stale_attempt");
        requireGate(args.session === attempt.session_id, "stale_session");
        requireGate(args.fence === attempt.fence, "stale_fence");
        requireGate(args.spec_rev === task.spec_rev, "stale_spec");
        if (attempt.thread_id) {
          requireGate(
            this.runtime && caller && caller.thread === attempt.thread_id,
            "stale_thread",
          );
          await caller.assertActive();
          const live = await this.runtime.readThread(attempt.thread_id);
          this.bindObservedIdentity(attempt, live);
          requireGate(
            !live.error &&
              live.workspace === attempt.workspace &&
              live.provider === "codex" &&
              live.running &&
              !live.blocked &&
              attempt.runtime_identity!.leader_pid !== null && attempt.runtime_identity!.native_session !== null &&
              live.turn === caller.turn,
            "identity_conflict",
          );
          requireGate(!attempt.turn_id || attempt.turn_id === caller.turn ||
            task.repair && !task.repair.stopped && task.repair.candidate_commit === task.candidate_commit, "stale_turn");
        } else requireGate(!caller, "stale_thread");
        const repairing = task.state === "rework";
        if (repairing) requireGate(attempt.rework?.state === "delivered", "conflict_delivery_unconfirmed", attempt.rework);
        const reworkSubmission = repairing || Boolean(task.repair && !task.repair.stopped &&
          task.repair.candidate_commit === task.candidate_commit && attempt.rework?.state === "submitted");
        requireGate(["claimed", "submitted", "rework"].includes(task.state), "invalid_state");
        const commit = sha(args.commit);
        requireGate(
          repairing || !task.candidate_commit || task.candidate_commit === commit ||
            task.repair && !task.repair.stopped && task.repair.candidate_commit === task.candidate_commit,
          "candidate_conflict",
        );
        await this.commitExists(taskId, task.repo, commit);
        requireGate(
          await this.ancestor(taskId, task.repo, attempt.base_commit, commit),
          "not_descendant",
        );
        let submissionBase = reworkSubmission ? attempt.rework!.base_commit : this.candidateBase(attempt, commit);
        if (reworkSubmission) requireGate(await this.ancestor(taskId, task.repo, submissionBase, commit),
          "rework_baseline_changed", { base: submissionBase, commit });
        if (repairing) {
          requireGate(commit !== attempt.rework!.prior_candidate, "conflict_candidate_unchanged");
          const head = sha(await this.integration(task));
          requireGate(await this.ancestor(taskId, task.repo, submissionBase, head) &&
            await this.ancestor(taskId, task.repo, head, commit), "rework_baseline_changed", { base: submissionBase, head, commit });
          // Only a head read from the integration ref can extend the repair
          // baseline. A worker cannot nominate a commit to hide its own delta.
          submissionBase = head;
        }
        requireGate(
          (await this.git(taskId, attempt.workspace, ["rev-parse", "HEAD"])) === commit,
          "workspace_head_mismatch",
        );
        requireGate(
          !(await this.git(taskId, attempt.workspace, [
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
          ])),
          "dirty_worktree",
        );
        if (caller) {
          await caller.assertActive();
          attempt.turn_id = caller.turn;
        }
        if (task.candidate_commit === commit && !task.repair) return { ok: true, task, replayed: true };
        requireGate(!task.repair || commit !== task.repair.candidate_commit, "repair_requires_new_candidate");
        if (attempt.thread_id) {
          requireGate(this.runtime?.sessionFacts, "delivery_facts_required");
          const facts = await this.runtime.sessionFacts(attempt.thread_id);
          requireGate(facts.launch.role === "worker" && facts.launch.id === attempt.runtime_identity?.launch &&
            facts.model !== "unknown" && facts.effort !== "unknown", "delivery_facts_unknown");
          attempt.delivery = { commit, turn_id: attempt.turn_id, launch_id: facts.launch.id, cli: facts.launch.cli_version,
            model: facts.model, effort: facts.effort, number: (attempt.delivery?.number ?? 0) + 1,
            submitted_at: new Date(this.now()).toISOString() };
        }
        attempt.state = "submitted";
        const stats = await this.execute(taskId,
          ["git", "-C", task.repo, "diff", "--numstat", "--no-renames", "-z", submissionBase, commit, "--"], task.repo);
        requireGate(stats.returncode === 0 && stats.stdout !== null, "git_failed", stats);
        const rows = stats.stdout.split("\0").filter(Boolean).map((row) => row.split("\t", 3));
        this.event(taskId, "submission_metrics", { commit, files: rows.length,
          added: rows.reduce((sum, row) => sum + (row[0] === "-" ? 0 : Number(row[0])), 0),
          deleted: rows.reduce((sum, row) => sum + (row[1] === "-" ? 0 : Number(row[1])), 0),
          binary_files: rows.filter((row) => row[0] === "-").length });
        if (reworkSubmission) {
          attempt.rework!.state = "submitted";
          attempt.rework!.base_commit = submissionBase;
          attempt.rework!.candidate_commit = commit;
          delete attempt.revalidation;
          task.verification = null;
          this.event(taskId, "conflict_rework_submitted", { previous_verification: attempt.rework!.verification_id,
            previous_candidate: attempt.rework!.prior_candidate, candidate: commit, base: submissionBase,
            review_required: "fresh", attempt: attempt.attempt_id, session: attempt.session_id,
            fence: attempt.fence, spec_rev: task.spec_rev, card_snapshot_id: attempt.card_snapshot_id });
        }
        task.candidate_commit = commit;
        task.state = "submitted";
        task.repair = null;
        task.verification = null;
        this.save(task, "submitted", { attempt, commit, task });
        return { ok: true, task };
      }
      if (args.command === "verify") return await this.verifyCandidate(task, attempt);
      if (args.command === "integrate") {
        const score = this.scoreData(args.score_file);
        if (task.state === "accepted") {
          requireGate(JSON.stringify(score) === JSON.stringify(task.integration_intent?.score?.data), "score_replay_mismatch");
          if (!attempt.thread_id) await this.cleanupAttempt(task, attempt);
          return { ok: true, task, replayed: true };
        }
        for (;;) {
          const recovering = Boolean(task.integration_intent);
          let intent = task.integration_intent;
          const v = task.verification;
          requireGate((task.state === "verified" || intent) && v?.state === "passed", "not_verified");
          this.checkVerification(task, attempt, v);
          this.checkQualityEvidence(task, attempt, v);
          this.requireReviewed(task, attempt);
          requireGate(attempt.delivery, "score_provenance_required");
          if (intent) requireGate(intent.score && JSON.stringify(intent.score.data) === JSON.stringify(score), "score_replay_mismatch");
          requireGate(v.M, "not_verified");
          const actual = await this.integration(task);
          if (intent) {
            requireGate(
              task.state === "integrating" &&
                intent.state === "pending" &&
                intent.verification_id === v.verification_id &&
                intent.G === v.G &&
                intent.M === v.M &&
                intent.C === v.C &&
                intent.spec_rev === v.spec_rev &&
                intent.card_snapshot_id === v.card_snapshot_id &&
                intent.integration_ref === task.integration_ref &&
                intent.attempt.task_id === taskId &&
                intent.attempt.attempt_id === attempt.attempt_id &&
                intent.attempt.session_id === attempt.session_id &&
                intent.attempt.fence === attempt.fence &&
                intent.attempt.spec_rev === task.spec_rev &&
                (actual === intent.G || actual === intent.M),
              "needs_reconciliation",
              { intent, actual },
            );
            if (actual === intent.M) {
              await this.checkIntegratedContent(task, intent);
              intent.state = "completed";
              task.state = "accepted";
              attempt.state = "accepted";
              this.db.exec("BEGIN IMMEDIATE");
              try {
                this.save(task, "integrated_reconciled", intent);
                this.finalScore(task, attempt, intent);
                this.db.exec("COMMIT");
              } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }
              if (!attempt.thread_id) await this.cleanupAttempt(task, attempt);
              return { ok: true, task, reconciled: true };
            }
          } else {
            if (actual !== v.G) {
              await this.revalidateForIntegration(task, attempt, v, actual);
              continue;
            }
            intent = {
              G: v.G,
              C: v.C,
              M: v.M,
              verification_id: v.verification_id,
              attempt: structuredClone(attempt),
              spec_rev: v.spec_rev,
              card_snapshot_id: v.card_snapshot_id,
              integration_ref: task.integration_ref,
              worktree: await this.integrationWorktree(task),
              intent_id: randomUUID(),
              state: "pending",
              score: { score_id: "score-" + randomUUID(), data: score },
              command_intent: {
                argv: [],
                cwd: task.repo,
              },
            };
            intent.command_intent = {
              argv: ["git", "-C", intent.worktree ?? task.repo, "update-ref", "--stdin"],
              cwd: intent.worktree ?? task.repo,
            };
            task.integration_intent = intent;
            task.state = "integrating";
            this.save(task, "integration_intent", intent);
          }
          let result: A2ACommandResult;
          try { result = await this.advanceWorkBranch(task, intent); }
          catch (error) {
            if (error instanceof Refusal && error.code === "integration_compare_failed") {
              if (recovering) throw new Refusal("needs_reconciliation", error.details);
              const comparison = error.details as { actual: string };
              await this.revalidateForIntegration(task, attempt, v, comparison.actual);
              continue;
            }
            if (error instanceof Refusal && error.code === "dirty_integration_worktree")
              this.lifecycleIssue(task, attempt, error.code, { intent, failure: error.details });
            throw error;
          }
          const readback = await this.integration(task);
          intent.result = result;
          const completed = result.returncode === 0 && readback === intent.M;
          if (completed) {
            await this.checkIntegratedContent(task, intent);
            intent.state = "completed";
            task.state = "accepted";
            attempt.state = "accepted";
          }
          this.db.exec("BEGIN IMMEDIATE");
          try {
            this.save(task, completed ? "integrated" : "integration_conflict", { intent, readback });
            if (completed) this.finalScore(task, attempt, intent);
            this.db.exec("COMMIT");
          } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }
          requireGate(completed, "needs_reconciliation", { intent, readback });
          if (!attempt.thread_id) await this.cleanupAttempt(task, attempt);
          return { ok: true, task };
        }
      }
      requireGate(args.command === "reclaim", "invalid_command");
      const ownsTask = task.current_attempt?.attempt_id === attempt.attempt_id;
      if (attempt.reclaimed) {
        if (ownsTask && !["accepted", "abandoned", "upgraded"].includes(task.state)) this.invalidate(task, "controller reclaim");
        await this.cleanupAttempt(task, attempt);
        return { ok: true, task };
      }
      requireGate(
        !ownsTask || !task.integration_intent || task.integration_intent.state === "completed",
        "needs_reconciliation",
      );
      requireGate(this.runtime && attempt.thread_id, "no_bound_thread");
      const live = await this.runtime.readThread(attempt.thread_id);
      requireGate(
        live.workspace === attempt.workspace && live.provider === "codex",
        "identity_conflict",
      );
      this.checkThread(attempt, live);
      requireGate(attempt.runtime_identity!.leader_pid !== null && attempt.runtime_identity!.native_session !== null,
        "identity_conflict", { attempt, live });
      this.checkErrorReclaim(live);
      requireGate(!live.blocked, "run_blocked", live);
      requireGate(!live.running, "worker_working");
      this.event(taskId, "reclaim_intent", { attempt, live }, attempt.attempt_id);
      if (ownsTask && !["accepted", "abandoned", "upgraded"].includes(task.state)) this.invalidate(task, "controller reclaim");
      this.checkUserInputObserver();
      await this.runtime.stopThread(attempt.thread_id);
      const stopped = await this.runtime.readThread(attempt.thread_id);
      this.checkThread(attempt, stopped);
      requireGate(stopped.stopped, "stop_unconfirmed");
      this.checkUserInputObserver();
      await this.runtime.archiveThread(attempt.thread_id);
      const archived = await this.runtime.readThread(attempt.thread_id);
      this.checkThread(attempt, archived);
      requireGate(archived.archived && archived.stopped, "reclaim_unconfirmed");
      attempt.reclaimed = true;
      attempt.reclaimed_at = new Date().toISOString();
      this.member(task, attempt.thread_id, "worker", attempt.reclaimed_at);
      this.save(task, "reclaimed", { attempt, archived }, attempt);
      await this.cleanupAttempt(task, attempt);
      return { ok: true, task };
    } catch (error) {
      const ioCode = (error as NodeJS.ErrnoException).code;
      const code =
        error instanceof QualityProtocolError ? (error.field.startsWith("score") ? "invalid_score" : "invalid_review_result") :
        error instanceof TaskCardError ? "invalid_task_card" : error instanceof Refusal
          ? error.code
          : [
                "ENOENT",
                "EACCES",
                "EEXIST",
                "EISDIR",
                "ENOTDIR",
                "ERR_ENCODING_INVALID_ENCODED_DATA",
              ].includes(ioCode ?? "")
            ? "local_io_failed"
            : "gate_failure";
      const details = error instanceof TaskCardError ? { field: error.field, reason: error.message } :
        error instanceof Refusal ? error.details : String(error);
      // A failed observer must remain queryable even when SQLite cannot append.
      if (taskId && this.userInputObserver?.state !== "failed")
        this.event(taskId, "rejected", { error: code, details, input: raw });
      return { ok: false, error: code, details };
    } finally {
      lock?.close();
    }
  }
}
