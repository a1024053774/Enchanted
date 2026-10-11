// Derived from Synara, MIT License.
// Copyright (c) 2026 T3 Tools Inc.
// Copyright (c) 2026 Emanuele Di Pietro
// See ../../LICENSE.synara for the full permission notice.

import { Schema } from "effect";
import type { TaskCard } from "../gates/taskCards.ts";
import { ModelSelection } from "./modelSelection.ts";
import { A2AMemberRole } from "./a2aMembership.ts";
import {
  A2ASessionPreset,
  type A2AInboxEntry,
  type A2AInboxDelivery,
} from "./a2aInbox.ts";

export const A2AIssueAction = Schema.Literals([
  "close",
  "needs-user",
  "forward",
  "reopen",
  "snooze",
  "dismiss",
  "delivered",
]);
export type A2AIssueAction = typeof A2AIssueAction.Type;

export const A2AGateRequest = Schema.Struct({
  command: Schema.Literals([
    "card_template", "card_validate", "card_save", "card_show",
    "create",
    "claim",
    "revoke",
    "revise",
    "dispatch",
    "attach",
    "run",
    "submit",
    "verify",
    "integrate",
    "reclaim",
    "status",
    "events",
    "issues",
    "answer_issue",
    "answer_issues",
    "disposition",
  ]),
  task: Schema.String,
  repo: Schema.optional(Schema.String),
  project: Schema.optional(Schema.String),
  title: Schema.optional(Schema.String),
  thread: Schema.optional(Schema.String),
  role: Schema.optional(A2AMemberRole),
  preset: Schema.optional(A2ASessionPreset),
  modelSelection: Schema.optional(ModelSelection),
  branch: Schema.optional(Schema.String),
  card: Schema.optional(Schema.String),
  ticket: Schema.optional(Schema.String),
  card_version: Schema.optional(Schema.Number),
  expected_version: Schema.optional(Schema.Number),
  instructions: Schema.optional(Schema.String),
  owner: Schema.optional(Schema.String),
  reason: Schema.optional(Schema.String),
  attempt: Schema.optional(Schema.String),
  session: Schema.optional(Schema.String),
  fence: Schema.optional(Schema.Number),
  spec_rev: Schema.optional(Schema.Number),
  commit: Schema.optional(Schema.String),
  wait_seconds: Schema.optional(Schema.Number),
  runtimeMode: Schema.optional(Schema.Literals(["approval-required", "full-access"])),
  issue: Schema.optional(Schema.String),
  answer: Schema.optional(Schema.String),
  answers: Schema.optional(
    Schema.Array(Schema.Struct({ issue: Schema.String, answer: Schema.String })),
  ),
  mode: Schema.optional(Schema.Literals(["bundle", "individual"])),
  action: Schema.optional(A2AIssueAction),
  basis: Schema.optional(Schema.String),
  body: Schema.optional(Schema.String),
});
export type A2AGateRequest = typeof A2AGateRequest.Type;

export interface A2AAttempt {
  task_id: string;
  attempt_id: string;
  session_id: string;
  fence: number;
  spec_rev: number;
  thread_id: string;
  runtime_mode: "approval-required" | "full-access";
  turn_id: string | null;
  workspace: string;
  base_commit: string;
  card_snapshot_id: string;
  reclaimed: boolean;
  reclaimed_at?: string;
  owner?: string;
  state?: string;
  revocation_reason?: string;
}

export interface A2ACommandResult {
  argv: string[];
  cwd: string;
  stdout: string | null;
  stderr: string | null;
  exit: number | null;
  returncode: number | null;
  outcome?: string;
}

export interface A2AVerification {
  verification_id: string;
  attempt: A2AAttempt;
  spec_rev: number;
  G: string;
  C: string;
  M: string | null;
  card_snapshot_id: string;
  card_version: number;
  commands: { argv: string[]; cwd: string }[];
  results: A2ACommandResult[];
  workspace: string;
  state: "running" | "passed" | "failed" | "interrupted" | "unknown" | "merge_failed";
  command_intent?: { argv: string[]; cwd: string };
  result?: A2ACommandResult;
  ended?: string;
}

export interface A2ATask {
  task_id: string;
  title?: string;
  project_id: string;
  repo: string;
  integration_ref: string;
  card_snapshot_id: string;
  card_version: number;
  card: TaskCard;
  base_commit: string;
  state: string;
  spec_rev: number;
  fence: number;
  current_attempt: A2AAttempt | null;
  candidate_commit: string | null;
  verification: A2AVerification | null;
  integration_intent: {
    G: string;
    M: string;
    verification_id: string;
    attempt: A2AAttempt;
    spec_rev?: number;
    C?: string;
    card_snapshot_id: string;
    integration_ref: string;
    worktree: string | null;
    intent_id?: string;
    command_intent?: { argv: string[]; cwd: string };
    result?: A2ACommandResult;
    state: "pending" | "completed";
  } | null;
}

/** A normal native session with a display role, never a delivery attempt. */
export interface A2AAttachment {
  task_id: string;
  thread_id: string;
  role: typeof A2AMemberRole.Type;
  modelSelection: typeof ModelSelection.Type;
  runtime_mode: "approval-required" | "full-access";
  state: "creating" | "active" | "ended";
  ended_at?: string;
  preset?: A2ASessionPreset;
}

export interface A2ARun {
  run_id: string;
  task_id: string;
  attempt_id: string | null;
  thread_id: string | null;
  started: string;
  ended?: string;
  wait_seconds: number;
  phase: string;
  outcome: string;
  reclaimed?: boolean;
  error?: string;
  details?: unknown;
  cleanup_failure?: unknown;
}

export interface A2AUserInputObserver {
  state: "starting" | "healthy" | "failed" | "stopped";
  updated_at: string;
  failure?: {
    event_id?: string;
    source_sequence?: number;
    thread_id?: string;
    message_id?: string;
    reason: string;
  };
}

export interface A2AGateResult {
  ok: boolean;
  card?: TaskCard;
  card_version?: number;
  task?: A2ATask;
  run?: A2ARun;
  user_input_observer?: A2AUserInputObserver;
  attempt?: A2AAttempt;
  attachment?: A2AAttachment;
  verification?: A2AVerification;
  replayed?: boolean;
  reconciled?: boolean;
  error?: string;
  details?: unknown;
  events?: ReadonlyArray<{ seq: number; time: string; type: string; details: unknown }>;
  records?: ReadonlyArray<A2AIssueRecord>;
  issues?: ReadonlyArray<A2AIssueView>;
  user_inputs?: ReadonlyArray<A2AUserInput>;
  entry?: A2AInboxEntry;
  delivery?: A2AInboxDelivery;
  entries?: ReadonlyArray<{ entry: A2AInboxEntry; delivery?: A2AInboxDelivery }>;
  interruptRequested?: boolean;
}

export interface A2AIssueRecord {
  id: string;
  schema: 1;
  kind: "issue" | "answer" | "disposition";
  from: string;
  to: string;
  reply_to: string | null;
  refs: ReadonlyArray<string>;
  created_at: string;
  body: string;
  task_id: string;
  attempt_id: string | null;
  thread_id: string;
  turn_id: string;
  number: number;
  title: string;
  blocking: boolean;
  issue_id: string;
  input_id?: string;
  message_id?: string;
  bundle_id?: string;
  action?: A2AIssueAction;
  reason?: string;
  basis?: string;
}

export interface A2AIssueView {
  issue: A2AIssueRecord;
  state: "待判断" | "等你决定" | "已答复" | "已送达" | "已转交" | "已关闭" | "稍后";
  answer?: A2AIssueRecord;
  disposition?: A2AIssueRecord;
}

export interface A2AUserInput {
  id: string;
  schema: 1;
  form: "message" | "answer" | "approval" | "denial" | "choice" | "action" | "gap";
  text: string;
  target: {
    project?: string | null;
    task: string | null;
    attempt: string | null;
    thread: string;
    turn: string | null;
    message: string | null;
    request?: string | null;
    eventSequence?: number;
  };
  channel: "thread-message" | "issue-panel" | "ws-rpc" | "ui-derived" | "settings-page" | "commit-trailer";
  reply_to: string | null;
  source_ref: {
    message_id?: string;
    event_id?: string;
    source_sequence?: number;
    command_id?: string;
    rpc?: string;
    commit?: string;
    label?: string;
  };
  certainty: "observed" | "inferred";
  created_at: string;
  bundle_id?: string;
  question?: { number: number; title: string; body: string };
  content?: unknown;
}
