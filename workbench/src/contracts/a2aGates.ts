// Derived from Synara, MIT License.
// Copyright (c) 2026 T3 Tools Inc.
// Copyright (c) 2026 Emanuele Di Pietro
// See ../../LICENSE.synara for the full permission notice.

import { Schema } from "effect";
import type { TaskCard, ProjectQuality } from "../gates/taskCards.ts";
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
    "review_submit",
    "abandon",
    "close",
    "out_of_card",
    "reclaim",
    "status",
    "events",
    "task_history",
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
  cli: Schema.optional(Schema.Literals(["Codex", "Claude Code"])),
  model: Schema.optional(Schema.String),
  effort: Schema.optional(Schema.String),
  fast: Schema.optional(Schema.Boolean),
  branch: Schema.optional(Schema.String),
  card: Schema.optional(Schema.String),
  ticket: Schema.optional(Schema.String),
  card_version: Schema.optional(Schema.Number),
  expected_version: Schema.optional(Schema.Number),
  instructions: Schema.optional(Schema.String),
  owner: Schema.optional(Schema.String),
  reason: Schema.optional(Schema.String),
  overlap_reason: Schema.optional(Schema.String),
  decision: Schema.optional(Schema.Literals(["accept", "reject"])),
  attempt: Schema.optional(Schema.String),
  session: Schema.optional(Schema.String),
  fence: Schema.optional(Schema.Number),
  spec_rev: Schema.optional(Schema.Number),
  commit: Schema.optional(Schema.String),
  review_id: Schema.optional(Schema.String),
  candidate_commit: Schema.optional(Schema.String),
  verdict: Schema.optional(Schema.String),
  findings: Schema.optional(Schema.Unknown),
  review_requirements: Schema.optional(Schema.Unknown),
  report: Schema.optional(Schema.Unknown),
  score_file: Schema.optional(Schema.String),
  wait_seconds: Schema.optional(Schema.Number),
  runtimeMode: Schema.optional(Schema.Literals(["approval-required", "full-access", "workspace-write"])),
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

export interface A2ARuntimeIdentity {
  launch: string;
  thread: string;
  shell_pid: number;
  leader_pid: number | null;
  native_session: string | null;
}

export interface A2AAttempt {
  task_id: string;
  attempt_id: string;
  session_id: string;
  fence: number;
  spec_rev: number;
  thread_id: string;
  runtime_mode: "approval-required" | "full-access" | "workspace-write";
  turn_id: string | null;
  runtime_identity: A2ARuntimeIdentity | null;
  workspace: string;
  base_commit: string;
  card_snapshot_id: string;
  // T-187: the Git metadata read once the worktree existed (core.ts gitMetadata).
  git_metadata?: { head: string; config: string | null; worktree_config: string | null; hooks: Record<string, string | null> };
  reclaimed: boolean;
  reclaimed_at?: string;
  owner?: string;
  state?: string;
  revocation_reason?: string;
  delivery?: {
    commit: string; turn_id: string | null; launch_id: string; cli: string;
    model: string; effort: string; number: number; submitted_at: string;
  };
  conflict_source?: string;
  rework?: {
    verification_id: string;
    prior_candidate: string;
    base_commit: string;
    message_id: string;
    prior_turn: string | null;
    state: "pending" | "delivered" | "unknown" | "submitted" | "replacing" | "replaced";
    candidate_commit?: string;
    replacement_attempt?: string;
    failure?: { reason: string; details: unknown };
  };
  revalidation?: {
    candidate_commit: string;
    card_snapshot_id: string;
    spec_rev: number;
    misses: number;
    previous_verification_id: string;
  };
  cleanup?: {
    state: "pending" | "removed" | "preserved";
    head?: string;
    branch?: string;
    ref?: string;
    delete_branch?: boolean;
    reason?: string;
  };
}

export interface A2ARepair {
  id: string;
  candidate_commit: string;
  verification_id: string;
  check: string;
  count: number;
  stopped: boolean;
  failure: unknown;
}

export interface A2AReview {
  review_id: string;
  ordinal: number;
  task_id: string;
  attempt: A2AAttempt;
  candidate_commit: string;
  spec_rev: number;
  card_snapshot_id: string;
  verification_id: string;
  thread_id: string;
  session_id: string;
  /** The detached Git worktree owned by the gate and kept immutable during review. */
  workspace: string;
  /** A disposable, non-Git copy where the reviewer may construct mutations. */
  candidate_workspace: string;
  /** Shared-repository refs captured before the reviewer starts. */
  shared_refs: string;
  requested_at: string;
  launch_id: string | null;
  runtime_identity: A2ARuntimeIdentity | null;
  state: "requested" | "running" | "passed" | "needs_fix" | "unknown" | "cancelled";
  result?: { verdict: "可合并" | "需修复"; findings: A2AReviewFinding[];
    review_requirements: Record<string, unknown>; report: Record<string, unknown>; turn_id: string; received_at: string };
}

export interface A2AReviewFinding {
  location: { path: string; line: number };
  failure_scenario: string;
  suggestion: string;
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
  quality?: {
    snapshot: ProjectQuality;
    red: { index: number; B: string; C: string; test_paths: string[]; base_workspace: string; candidate_workspace: string;
      base_result: A2ACommandResult; candidate_result: A2ACommandResult; passed: boolean }[];
    rules: { id: string; result: A2ACommandResult; passed: boolean }[];
  };
  ordinal?: number;
  // T-198: changed files the card does not allow; the controller judges them before integration.
  out_of_card?: string[];
  retained_ref?: string;
  cleanup?: "removed" | "preserved";
  conflict?: {
    files: string[];
    unmerged: string;
    diff: string;
    candidate_ref: string;
    base_ref: string;
  };
}

export interface A2ATask {
  // T-123: `<project>+<name>`; `name` is what the user and the task card call it.
  task_id: string;
  name: string;
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
  repair?: A2ARepair | null;
  // T-198: the controller let a candidate's out-of-card files through, with why.
  out_of_card_judgement?: { candidate_commit: string; verification_id: string; out_of_card: string[]; reason: string; at: string } | null;
  review?: A2AReview | null;
  quality?: ProjectQuality;
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
    score?: { score_id: string; data: Record<string, unknown> };
  } | null;
}

/** A normal native session with a display role, never a delivery attempt. */
export interface A2AAttachment {
  task_id: string;
  thread_id: string;
  role: typeof A2AMemberRole.Type;
  // Workbench attachments are read-only monitors (T-124); the model selection comes from
  // the monitor role settings, overridden by what the controller asked for.
  cli: "Codex" | "Claude Code";
  // Its own empty working directory: a monitor in the repository root would share that folder with
  // a Codex controller the user runs there, and their session logs could not be told apart.
  workspace?: string;
  model?: string;
  effort?: string;
  fast?: boolean;
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
  // The terminal controller that started this run (T-124), and when its role was found
  // ended or out of quota; the run then integrates without the controller's score.
  initiator?: { launch: string; role_request: string; role: string };
  initiator_unavailable?: { state: "ended" | "quota_exhausted"; at: string };
  // What the run dispatched with, so a run resumed after a daemon restart can dispatch again (T-124).
  dispatch?: { runtimeMode: string; overlap_reason?: string; model?: string; effort?: string; fast?: boolean };
  // Each daemon restart the run was resumed across.
  resumed?: { at: string; phase: string; task_state: string; redispatched_from: string | null }[];
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
  ready?: ReadonlyArray<{ id: string; title: string; type: string; ready_by: string; ready_rev: number }>;
  diagnostics?: ReadonlyArray<string>;
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
  state: "待判断" | "等你决定" | "已答复" | "已送达" | "已转交" | "已关闭" | "稍后" | "可能已随修订失效";
  answer?: A2AIssueRecord;
  /** The open issue's attempt was revoked by a revise; only the user confirms closing it (T-171). */
  superseded_by_revision?: { attempt: string; reason: string };
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
  channel: "thread-message" | "issue-panel" | "ws-rpc" | "ui-derived" | "settings-page" | "commit-trailer" | "terminal-window" | "controller-terminal";
  reply_to: string | null;
  source_ref: {
    window_id?: string;
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
