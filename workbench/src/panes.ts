import { accessSync, appendFileSync, closeSync, constants, existsSync, fstatSync, mkdirSync, mkdtempSync, openSync, readFileSync, readSync, readdirSync, realpathSync } from "node:fs";
import { dirname, isAbsolute, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { randomUUID } from "node:crypto";
import type { A2AAttempt, A2ATask, A2AReview, A2ARepair } from "./contracts/a2aGates.ts";
import { Refusal, type GateRuntime, type SubmitCaller } from "./gates/core.ts";
import { OrchestrationStore, type DispatchSource } from "./store.ts";
import type { A2AInboxEntry } from "./contracts/a2aInbox.ts";
import { claudeLaunch, type ClaudeLaunchInput } from "./claudeLaunch.ts";
import { noticeText, SECURITY_NOTICE_TEXT } from "./claudeNotice.ts";

const exec = promisify(execFile);
const require = createRequire(import.meta.url);
const cli = fileURLToPath(new URL("./gates/cli.ts", import.meta.url));
const quote = (value: string) => "'" + value.replaceAll("'", "'\\''") + "'";
const shellCommand = (argv: string[]) => argv.map(quote).join(" ");
function check(value: unknown, error: string, details?: unknown): asserts value {
  if (!value) throw new Refusal(error, details);
}
export function spawnHelper() {
  const lib = dirname(require.resolve("node-pty"));
  const native = require(join(lib, "utils.js")).loadNativeModule("pty");
  const helper = realpathSync(join(lib, native.dir, "spawn-helper"));
  accessSync(helper, constants.X_OK);
  return helper;
}
export interface LaunchConfig {
  controllers?: Partial<Record<"ideation" | "executor", {
    executable: string; model: string; effort: string; settings: Record<string, unknown>;
    role_card: string; role_card_revision: string;
  }>>;
  codex_bin?: string;
  codex_home?: string;
  role_card?: string;
  role_card_revision?: string;
  code_revision?: string;
  source_snapshot?: string;
  hook_authorization?: string;
  turn_limit?: number;
  turn_authorization?: string;
  reviewers?: { codex_home: string; role_card: string; role_card_revision: string; hook_authorization: string }[];
}
type Pane = {
  record: Record<string, any> & { id: string; task: string; attempt: string | null };
  token: string; task: A2ATask; attempt: A2AAttempt | null; pty: any;
  state: "unknown" | "idle" | "busy"; stopped: boolean; archived: boolean;
  failed: string | null; leader: number | null; native: string | null; turn: string | null;
  nativeEnded: boolean;
  active: { id: string; dispatch: string; at: string; nativeTurn: string | null } | null;
  queue: ReturnType<OrchestrationStore["register"]>[]; writing: boolean;
  stopInProgress: boolean;
  writes: Promise<void>; pendingInputs: number; userDraft: boolean; interrupted: boolean; sending: string | null;
  offsets: Map<string, number>; model: string; effort: string;
  terminalBuffer: string;
  claudePrompt?: boolean;
};

export class Panes implements GateRuntime {
  readonly root: string;
  readonly store: OrchestrationStore;
  readonly config: LaunchConfig;
  readonly panes = new Map<string, Pane>();
  readonly onEventWriteFailed: (reason: string) => void;
  constructor(root: string, store: OrchestrationStore, config: LaunchConfig, onEventWriteFailed: (reason: string) => void) {
    this.root = root; this.store = store; this.config = config;
    this.onEventWriteFailed = onEventWriteFailed;
  }
  ensureProject = async (_project: string, _repo: string) => {};
  startController(task: A2ATask, input: ClaudeLaunchInput) {
    check(new URL(input.api_url).port !== "0", "messages_api_not_bound");
    check(![...this.panes.values()].some(p => !p.stopped && p.record.preset === input.preset), "controller_already_started");
    const record = { ...claudeLaunch(task, input), created_at: new Date().toISOString(), cli_version: "unknown" };
    const token = randomUUID();
    this.store.launch(record);
    const trace = join(this.root, "traces", record.id, "pty.raw");
    mkdirSync(dirname(trace), { recursive: true, mode: 0o700 }); appendFileSync(trace, "", { flag: "wx", mode: 0o600 });
    const terminal = require("node-pty").spawn(record.shell, record.shell_argv, {
      name: "xterm-256color", cols: 160, rows: 45, cwd: record.worktree,
      env: { ...record.env, A2A_CAPABILITY: token }, encoding: "utf8",
    });
    const pane: Pane = { record, token, task, attempt: null, pty: terminal, state: "unknown", stopped: false,
      archived: false, failed: null, leader: null, native: record.session, turn: null, nativeEnded: false, active: null,
      queue: [], writing: false, stopInProgress: false, writes: Promise.resolve(), pendingInputs: 0,
      userDraft: false, interrupted: false, sending: null, offsets: new Map(), model: "unknown", effort: "unknown",
      terminalBuffer: "", claudePrompt: false };
    this.panes.set(record.thread, pane);
    this.store.event("pane_started", { shell_pid: terminal.pid, state: "unknown" }, record);
    terminal.onData((data: string) => {
      try { appendFileSync(trace, data); this.terminalProtocol(pane, data); }
      catch (error) { this.recordFailure(pane, "controller_terminal_failed", error); }
    });
    terminal.onExit((event: unknown) => {
      pane.stopped = true; pane.state = "unknown";
      try { this.store.event("pane_exit", event, record); }
      catch (error) { this.recordFailure(pane, "pane_exit_write_failed", error); }
    });
    return record;
  }
  // T-078-1/#49: prepare argv and its durable record only. Actual Claude launch,
  // auth, hooks and completion matching await decision 20261011T101958Z. This
  // method neither creates a live pane nor issues a launch capability.
  prepareControllerLaunch(task: A2ATask, preset: string) {
    check(preset === "ideation" || preset === "executor", "invalid_controller_preset");
    const c = this.config.controllers?.[preset];
    const nonempty = (value: unknown): value is string => typeof value === "string" && Boolean(value.trim()) && !value.includes("\0");
    check(c && nonempty(c.executable) && isAbsolute(c.executable) && nonempty(c.model) && nonempty(c.effort) &&
      nonempty(c.role_card) && isAbsolute(c.role_card) && nonempty(c.role_card_revision) && nonempty(this.config.code_revision),
      "controller_launch_config_required");
    check(c.settings && typeof c.settings === "object" && !Array.isArray(c.settings) &&
      Object.keys(c.settings).every(key => ["hooks", "permissions"].includes(key)) &&
      Object.values(c.settings).every(value => value && typeof value === "object" && !Array.isArray(value)),
      "invalid_controller_settings");
    const settingsText = JSON.stringify(c.settings);
    const settings = JSON.parse(settingsText);
    const session = randomUUID(), launch = randomUUID(), thread = randomUUID();
    const roleCard = realpathSync(c.role_card);
    const argv = [c.executable, "--session-id", session, "--model", c.model, "--effort", c.effort, "--settings", settingsText];
    const record = { id: launch, project: task.project_id, task: task.task_id, attempt: null,
      session, fence: null, spec_rev: task.spec_rev, thread, role: "controller", preset,
      execution_state: "prepared", validation: "待真实 Claude 复核", created_at: new Date().toISOString(),
      cli: "Claude Code", cli_version: "unknown", argv, settings,
      model_requested: c.model, effort_requested: c.effort,
      code_revision: this.config.code_revision, source_snapshot: this.config.source_snapshot ?? null,
      role_card: roleCard, role_card_revision: c.role_card_revision,
      role_text: new TextDecoder("utf-8", { fatal: true }).decode(readFileSync(roleCard)),
      base_commit: task.base_commit, worktree: realpathSync(task.repo),
      shell: "/bin/zsh", shell_argv: ["-f", "-i", "-c", shellCommand(argv) + "; exec /bin/zsh -f -i"],
      env: { A2A_PROJECT: task.project_id, A2A_TASK: task.task_id, A2A_SESSION: session,
        A2A_ROLE: "controller", A2A_PRESET: preset, A2A_LAUNCH: launch, A2A_STATE: this.root } };
    this.store.db.exec("BEGIN IMMEDIATE");
    try {
      this.store.launch(record);
      this.store.event("controller_launch_prepared", { preset, execution_state: "prepared" }, record);
      this.store.db.exec("COMMIT");
    } finally { if (this.store.db.isTransaction) this.store.db.exec("ROLLBACK"); }
    return record;
  }
  get(thread: string) { const pane = this.panes.get(thread); check(pane, "unknown_pane"); return pane; }
  byLaunch(id: string) {
    const pane = [...this.panes.values()].find((value) => value.record.id === id);
    check(pane, "unknown_launch"); return pane;
  }
  launchRecord(id: string) {
    check(typeof id === "string", "unknown_launch");
    const record = this.store.launchRecord(id);
    check(record, "unknown_launch");
    return record;
  }
  // A restarted host can describe historical launches, never adopt their PTYs.
  recover(daemon: string) {
    for (const record of this.store.launches()) {
      if (record.execution_state === "prepared") continue;
      if (this.store.lastEvent(record.id, ["pane_recovered", "pane_archived"])) continue;
      const exit = this.store.lastEvent(record.id, ["pane_exit"]);
      const start = this.store.lastEvent(record.id, ["pane_started"]);
      this.store.event("pane_recovered", { daemon, state: "unknown", lifecycle: exit ? "interrupted" : "unknown",
        reason: "daemon_restart", shell_pid: start?.data.shell_pid ?? null,
        exit_event: exit?.seq ?? null, session: record.session, fence: record.fence, spec_rev: record.spec_rev }, record as any);
    }
  }
  launchInfo(id: string) {
    const record = this.launchRecord(id);
    const pane = this.panes.get(record.thread);
    if (pane) {
      this.scan(pane);
      return { launch: record, native_session: pane.native, model: pane.model, effort: pane.effort };
    }
    return { launch: record, native_session: null, model: "unknown", effort: "unknown" };
  }
  output(id: string, offset: number, maxBytes = 65536) {
    const record = this.launchRecord(id);
    check(Number.isSafeInteger(offset) && offset >= 0, "invalid_output_offset");
    check(Number.isSafeInteger(maxBytes) && maxBytes > 0 && maxBytes <= 65536, "invalid_output_limit");
    // Use only the persisted launch identity, never a client-supplied filename.
    check(/^[a-zA-Z0-9-]+$/.test(record.id), "invalid_launch_record");
    const file = join(this.root, "traces", record.id, "pty.raw");
    check(existsSync(file), "trace_unavailable");
    const fd = openSync(file, "r");
    try {
      const stat = fstatSync(fd);
      check(stat.isFile(), "trace_unavailable");
      check(offset <= stat.size, "output_offset_past_end");
      const bytes = Buffer.alloc(Math.min(maxBytes, stat.size - offset));
      const read = readSync(fd, bytes, 0, bytes.length, offset);
      check(read === bytes.length, "trace_changed_during_read");
      return { launch: record.id, start_offset: offset, next_offset: offset + read,
        total_bytes: stat.size, data_base64: bytes.toString("base64") };
    } finally { closeSync(fd); }
  }
  async createThread(task: A2ATask, attempt: A2AAttempt) {
    check([...this.panes.values()].filter((pane) => pane.record.role === "worker")
      .every((pane) => pane.stopped && pane.archived), "single_worker_slice");
    check(attempt.runtime_mode === "workspace-write", "worker_requires_workspace_write");
    await this.createPane(task, attempt, this.config);
  }
  async createReview(task: A2ATask, review: A2AReview, prompt: string) {
    const index = this.store.launches().filter((record) => record.role === "reviewer").length;
    const approved = this.config.reviewers?.[index];
    check(approved, "review_launch_config_required");
    const home = realpathSync(approved.codex_home);
    check(home !== realpathSync(this.config.codex_home!) &&
      !this.store.launches().some((record) => record.env.CODEX_HOME === home), "review_home_reused");
    check(!existsSync(join(home, "sessions")) || readdirSync(join(home, "sessions")).length === 0, "review_home_not_empty");
    const attempt = { ...review.attempt, session_id: review.session_id, thread_id: review.thread_id,
      workspace: review.workspace, runtime_identity: null, turn_id: null };
    await this.createPane(task, attempt, { ...this.config, ...approved }, review);
    const pane = this.get(review.thread_id);
    await this.dispatch(pane, `${pane.record.role_text}\n\n${prompt}`);
  }
  private async createPane(task: A2ATask, attempt: A2AAttempt, c: LaunchConfig, review?: A2AReview) {
    const role = review ? "reviewer" : "worker";
    check(c.codex_bin && c.codex_home && c.role_card && c.hook_authorization && c.code_revision && c.role_card_revision, "launch_config_required");
    check(Number.isInteger(c.turn_limit) && c.turn_limit! > 0 && c.turn_limit! <= 10, "invalid_turn_limit");
    const codex = realpathSync(c.codex_bin), home = realpathSync(c.codex_home);
    check(home !== join(process.env.HOME ?? "", ".codex"), "isolated_codex_home_required");
    const environment: Record<string, string> = {};
    for (const key of ["PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "USER", "LOGNAME",
      "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"]) {
      if (process.env[key]) environment[key] = process.env[key]!;
    }
    environment.CODEX_HOME = home;
    const version = (await exec(codex, ["--version"], { env: environment })).stdout.trim();
    check(version === "codex-cli 0.162.1", "codex_version_mismatch", { version });
    const helper = spawnHelper();
    const launch = randomUUID(), token = randomUUID();
    const requestDirectory = realpathSync(mkdtempSync("/tmp/a2a-requests-"));
    const signalCommand = shellCommand([process.execPath, cli, "--state", this.root, "signal", "--launch", launch]);
    const hook = `[{hooks=[{type="command",command=${JSON.stringify(signalCommand)},timeout=10}]}]`;
    const model = task.card.executor.model, effort = task.card.executor.effort;
    check(task.card.executor.cli === "Codex" && ["gpt-6-astra", "gpt-6.1-sol"].includes(model) && effort === "xhigh", "worker_executor_mismatch");
    const argv = [codex, "--no-daemon", "--no-alt-screen", "-C", attempt.workspace,
      "-a", "never", "--sandbox", review ? "read-only" : "workspace-write", "-m", model,
      "-c", `model_reasoning_effort=${JSON.stringify(effort)}`, "-c", 'service_tier="default"',
      "-c", "check_for_update_on_startup=false", "-c", "tui.notifications=false",
      "-c", "sandbox_workspace_write.network_access=false", "-c", "features.network_proxy=false"];
    for (const event of ["UserPromptSubmit", "Stop", "PermissionRequest"]) argv.push("-c", `hooks.${event}=${hook}`);
    argv.push("--dangerously-bypass-hook-trust");
    Object.assign(environment, {
      SHELL: "/bin/zsh", TERM: "xterm-256color", COLORTERM: "truecolor",
      A2A_PROJECT: task.project_id, A2A_TASK: task.task_id, A2A_ATTEMPT: attempt.attempt_id,
      A2A_SESSION: attempt.session_id, A2A_ROLE: role, A2A_LAUNCH: launch,
      A2A_STATE: this.root, A2A_CLI: cli, A2A_NODE: process.execPath, A2A_CAPABILITY: token,
      A2A_REQUEST_DIR: requestDirectory,
      A2A_FENCE: String(attempt.fence), A2A_SPEC_REV: String(attempt.spec_rev),
      A2A_TOOL: version, A2A_MODEL_REQUESTED: model, A2A_EFFORT_REQUESTED: effort,
    });
    if (review) environment.A2A_REVIEW = review.review_id;
    else Object.assign(environment, { GIT_CONFIG_COUNT: "1", GIT_CONFIG_KEY_0: "core.hooksPath",
      GIT_CONFIG_VALUE_0: fileURLToPath(new URL("../hooks/", import.meta.url)) });
    const shellArgv = ["-f", "-i", "-c", shellCommand(argv) + "; exec /bin/zsh -f -i"];
    const { A2A_CAPABILITY: _secret, ...recordedEnvironment } = environment;
    const record = { id: launch, project: task.project_id, task: task.task_id, attempt: attempt.attempt_id,
      session: attempt.session_id, fence: attempt.fence, spec_rev: attempt.spec_rev, thread: attempt.thread_id,
      role, sandbox: review ? "read-only" : "workspace-write",
      ...(review ? { review_id: review.review_id, review_verification_id: review.verification_id, review_home_was_empty: true } : {}),
      created_at: new Date().toISOString(), cli_version: version, argv, request_dir: requestDirectory,
      model_requested: model, effort_requested: effort, service_tier_requested: "default",
      turn_limit: c.turn_limit, turn_authorization: c.turn_authorization ?? null,
      code_revision: c.code_revision, source_snapshot: c.source_snapshot ?? null, role_card: c.role_card, role_card_revision: c.role_card_revision,
      role_text: readFileSync(c.role_card, "utf8"), base_commit: attempt.base_commit, worktree: attempt.workspace,
      shell: "/bin/zsh", shell_argv: shellArgv, env: recordedEnvironment, helper, hook_authorization: c.hook_authorization };
    this.store.launch(record);
    mkdirSync(join(this.root, "traces", launch), { recursive: true, mode: 0o700 });
    appendFileSync(join(this.root, "traces", launch, "pty.raw"), "", { flag: "wx", mode: 0o600 });
    const terminal = require("node-pty").spawn("/bin/zsh", shellArgv, {
      name: "xterm-256color", cols: 160, rows: 45, cwd: attempt.workspace, env: environment, encoding: "utf8",
    });
    const pane: Pane = { record, token, task, attempt, pty: terminal, state: "unknown", stopped: false,
      archived: false, failed: null, leader: null, native: null, turn: null, nativeEnded: false, active: null,
      queue: [], writing: false, stopInProgress: false, writes: Promise.resolve(), pendingInputs: 0, userDraft: false, interrupted: false, sending: null,
      offsets: new Map(), model: "unknown", effort: "unknown", terminalBuffer: "" };
    this.panes.set(attempt.thread_id, pane);
    this.store.event("pane_started", { shell_pid: terminal.pid, state: "unknown" }, record);
    terminal.onData((data: string) => {
      try {
        appendFileSync(join(this.root, "traces", launch, "pty.raw"), data);
      } catch (error) { this.recordFailure(pane, "trace_write_failed", error); return; }
      try { this.terminalProtocol(pane, data); }
      catch (error) { this.recordFailure(pane, "terminal_protocol_failed", error); }
    });
    terminal.onExit((event: unknown) => {
      // The CLI can flush rollout records while exiting without emitting Stop.
      // Read after exit, before publishing the terminal lifecycle transition.
      try {
        this.scan(pane, true);
        this.store.event("native_final_read", { native_session: pane.native,
          offsets: [...pane.offsets].map(([file, offset]) => ({ file: relative(home, file), offset })) }, record);
      } catch (error) {
        this.recordFailure(pane, "native_final_read_failed", error, { native_session: pane.native,
          offsets: [...pane.offsets].map(([file, offset]) => ({ file: relative(home, file), offset })),
          details: error instanceof Refusal ? error.details : null });
      }
      pane.stopped = true; pane.state = "unknown";
      try { this.store.event("pane_exit", event, record); }
      catch (error) { this.recordFailure(pane, "pane_exit_write_failed", error); }
    });
  }
  recordFailure(pane: Pane, type: string, error: unknown, context?: unknown) {
    pane.failed = `${type}: ${String(error)}`; pane.state = "unknown";
    try { this.store.event(type, { error: String(error), state: "unknown", ...(context ? { context } : {}) }, pane.record); }
    catch (recordError) {
      const reason = `event_write_failed: ${String(recordError)}; original ${pane.failed}`;
      pane.failed = reason;
      this.onEventWriteFailed(reason);
      console.error(JSON.stringify({ error: "event_write_failed", launch: pane.record.id, reason }));
    }
  }
  // Terminal capability replies are protocol bytes, never screen-derived state.
  terminalProtocol(pane: Pane, data: string) {
    pane.terminalBuffer += data;
    for (;;) {
      const start = pane.terminalBuffer.indexOf("\x1b");
      if (start < 0) { pane.terminalBuffer = ""; return; }
      pane.terminalBuffer = pane.terminalBuffer.slice(start);
      if (pane.terminalBuffer.length === 1) return;
      if (!["[", "]"].includes(pane.terminalBuffer[1]!)) {
        pane.terminalBuffer = pane.terminalBuffer.slice(2); continue;
      }
      const match = /^(?:\x1b\[([0-?]*[ -/]*[@-~])|\x1b\]([^\x07]*?)(?:\x07|\x1b\\))/.exec(pane.terminalBuffer);
      if (!match) { if (pane.terminalBuffer.length > 4096) pane.terminalBuffer = ""; return; }
      const reply: Record<string, string> = { "6n": "\x1b[1;1R", "c": "\x1b[?1;2c", "0c": "\x1b[?1;2c", ">c": "\x1b[>0;0;0c", ">0c": "\x1b[>0;0;0c", "?u": "\x1b[?0u", "11;?": "\x1b]11;rgb:0000/0000/0000\x1b\\" };
      const response = reply[match[1] ?? match[2]!];
      if (response) {
        const query = match[0];
        void this.serializeWrite(pane, async () => {
          this.store.event("terminal_protocol_write", { query, response }, pane.record);
          pane.pty.write(response);
        }).catch(error => this.recordFailure(pane, "terminal_protocol_failed", error));
      }
      pane.terminalBuffer = pane.terminalBuffer.slice(match[0].length);
    }
  }
  async processInfo(thread: string) {
    const pane = this.get(thread);
    const output = (await exec("/bin/ps", ["-axo", "pid=,ppid=,pgid=,tpgid=,comm="])).stdout;
    const rows = output.trim().split("\n").map((line) => {
      const m = /^\s*(\d+)\s+(\d+)\s+(\d+)\s+(-?\d+)\s+(.+)$/.exec(line);
      check(m, "invalid_process_row", line);
      return { pid: Number(m[1]), ppid: Number(m[2]), pgid: Number(m[3]), tpgid: Number(m[4]), command: m[5]! };
    });
    const descendants = new Set<number>([pane.pty.pid]);
    for (let changed = true; changed;) {
      changed = false;
      for (const row of rows) if (descendants.has(row.ppid) && !descendants.has(row.pid)) { descendants.add(row.pid); changed = true; }
    }
    const owned = rows.filter((row) => descendants.has(row.pid));
    const leaders = owned.filter((row) => row.pid === row.pgid && row.pgid === row.tpgid && row.command === pane.record.argv[0]);
    const leader = leaders.length === 1 ? leaders[0]!.pid : null;
    const shellAlone = owned.length === 1 && owned[0]!.pid === pane.pty.pid;
    if (pane.record.cli !== "Claude Code" && !pane.nativeEnded && !pane.failed && pane.leader !== null && pane.native !== null &&
      leader === null && shellAlone && pane.state === "idle" && !pane.active && !pane.writing && !pane.queue.length) {
      this.store.event("native_session_ended", { shell_pid: pane.pty.pid, leader_pid: pane.leader,
        native_session: pane.native, processes: owned }, pane.record);
      pane.nativeEnded = true;
    }
    if (pane.nativeEnded && !shellAlone) pane.failed = "process_after_session_end";
    else if (!pane.nativeEnded && pane.leader !== null && leader !== pane.leader) pane.failed =
      pane.record.cli === "Claude Code" ? "claude_leader_replaced_or_exited" : "codex_leader_replaced_or_exited";
    if (pane.leader === null && leader !== null) pane.leader = leader;
    this.scan(pane);
    return { shell_pid: pane.pty.pid, leader, native_session: pane.native, session_ended: pane.nativeEnded,
      processes: owned, failed: pane.failed };
  }
  scan(pane: Pane, final = false) {
    if (pane.stopped) return;
    if (pane.record.cli === "Claude Code") return;
    const home = pane.record.env.CODEX_HOME as string;
    const walk = (dir: string): string[] => !existsSync(dir) ? [] : readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
      entry.isDirectory() ? walk(join(dir, entry.name)) : entry.name.endsWith(".jsonl") ? [join(dir, entry.name)] : []);
    const files = final ? [...pane.offsets.keys()].filter((file) => pane.native && file.endsWith(pane.native + ".jsonl")) : walk(join(home, "sessions"));
    if (final) check(pane.native && files.length === 1, "native_bound_log_unavailable", { native_session: pane.native, files });
    for (const file of files) {
      const bytes = readFileSync(file);
      // An isolated home can retain an earlier attempt's rollout. Only logs
      // belonging to this worktree contribute records or native identity.
      if (!final) {
        const end = bytes.indexOf(10);
        if (end < 0) continue;
        const metadata = JSON.parse(bytes.subarray(0, end).toString("utf8"));
        if (metadata.type !== "session_meta" || metadata.payload?.cwd !== pane.attempt.workspace) continue;
      }
      let offset = pane.offsets.get(file) ?? 0;
      check(bytes.length >= offset, "native_log_truncated", { file: relative(home, file), offset, bytes: bytes.length });
      let end: number;
      while ((end = bytes.indexOf(10, offset)) >= 0) {
        const raw = bytes.subarray(offset, end).toString("utf8"), event = JSON.parse(raw);
        this.store.event("native_record", { file: relative(home, file), offset, record: event }, pane.record);
        appendFileSync(join(this.root, "traces", pane.record.id, "native.jsonl"), raw + "\n");
        if (event.type === "session_meta" && event.payload.source === "cli") {
          check(!pane.native || pane.native === event.payload.id, "ambiguous_native_session");
          pane.native = event.payload.id;
        }
        // Only the root CLI file contributes identity or model facts.
        if (pane.native && file.endsWith(pane.native + ".jsonl")) {
          if (event.type === "turn_context" && event.payload.turn_id === pane.turn) {
            pane.model = event.payload.model ?? "unknown";
            pane.effort = event.payload.effort ?? event.payload.reasoning_effort ?? "unknown";
          }
          if (event.type === "event_msg" && event.payload.type === "task_started") {
            pane.turn = event.payload.turn_id;
            pane.model = "unknown"; pane.effort = "unknown";
            if (pane.active) pane.active.nativeTurn = pane.turn;
          }
        }
        offset = end + 1;
        pane.offsets.set(file, offset);
      }
      if (final) check(offset === bytes.length, "native_log_incomplete_line", { file: relative(home, file), offset, bytes: bytes.length });
    }
  }
  startThread = async (_task: A2ATask, attempt: A2AAttempt, prompt: string) => {
    const pane = this.get(attempt.thread_id);
    await this.dispatch(pane, `${pane.record.role_text}\n\n${prompt}`);
  };
  sendGateFeedback = async (thread: string, messageId: string, message: string) => {
    const pane = this.get(thread);
    const live = await this.processInfo(thread);
    check(live.leader && !live.failed && !live.session_ended && pane.native, "conflict_session_unknown", live);
    const item = await this.dispatch(pane, message, "gate");
    this.store.event("gate_feedback_registered", { message_id: messageId, dispatch: item.id }, pane.record);
  };
  async sessionFacts(thread: string) {
    const info = this.launchInfo(this.get(thread).record.id);
    return { launch: info.launch, model: info.model, effort: info.effort };
  }
  async qualityFeedback(attempt: A2AAttempt, repair: A2ARepair) {
    const pane = this.get(attempt.thread_id);
    check(pane.record.role === "worker" && pane.record.attempt === attempt.attempt_id &&
      pane.record.session === attempt.session_id && pane.record.fence === attempt.fence &&
      pane.record.id === attempt.runtime_identity?.launch, "feedback_identity_mismatch");
    if (repair.stopped) {
      const held = pane.queue.filter((item) => item.context?.kind === "quality-repair");
      pane.queue = pane.queue.filter((item) => item.context?.kind !== "quality-repair");
      this.store.event("quality_feedback_stopped", { repair, cancelled: held.map((item) => item.id) }, pane.record);
      return;
    }
    await this.dispatch(pane, "门禁检查未通过。根据失败证据修复，运行完成条件，Git提交后用原CLI显式重交新候选；保持本attempt和原生会话。\n" +
      JSON.stringify({ task: attempt.task_id, attempt: attempt.attempt_id, ...repair }, null, 2), "gate",
      undefined, { kind: "quality-repair", rejection_id: repair.id });
  }
  private serializeWrite(pane: Pane, operation: () => Promise<void>): Promise<void> {
    const result = pane.writes.then(operation);
    // A failed operation stops this stream. Replaying an unknown write is not
    // safe, and a later write must not silently skip that failed operation.
    pane.writes = result;
    return result;
  }
  async beginComposition(launch: string, receipt: Record<string, unknown>, assertCurrent: () => Promise<void>) {
    const pane = this.byLaunch(launch);
    check(!pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
    // Composition has no committed text yet, but already owns the user's draft.
    // An end/cancel does not prove that the CLI input line is empty. Only a user
    // submit or explicit interrupted-queue release clears the draft reservation.
    pane.userDraft = true;
    await this.serializeWrite(pane, async () => {
      await assertCurrent();
      this.store.event("terminal_composition_started", receipt, pane.record);
    });
  }
  async userInput(launch: string, data: string, receipt: Record<string, unknown>,
    record: (text: string, control: boolean) => Promise<void>, assertCurrent: () => Promise<void>,
    encoding: "utf8" | "binary" = "utf8") {
    const pane = this.byLaunch(launch);
    check(data.length > 0 && !pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
    const binary = encoding === "binary";
    const bytes = Buffer.from(data, binary ? "latin1" : "utf8");
    const pasted = !binary && data.startsWith("\x1b[200~") && data.endsWith("\x1b[201~");
    const text = binary ? "终端二进制输入" : pasted ? data.slice(6, -6).replaceAll("\r", "\n") : data;
    const control = binary || (!pasted && (data === "\r" || data === "\n" || data === "\x1b" || data === "\x7f"));
    // Reserve synchronously, before the recorder or identity check can yield.
    // Input records and their bytes keep the same order as admission. Esc also
    // prevents the CR of a paste that is already waiting inside this stream.
    pane.pendingInputs++;
    if (!binary && data === "\x1b") { pane.interrupted = true; pane.state = "busy"; }
    try { await this.serializeWrite(pane, async () => {
      await assertCurrent();
      await record(text, control);
      check(!pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
      if (!binary) pane.userDraft = true;
      this.store.event("terminal_input_write_intent", { ...receipt, encoding,
        ...(binary ? { data_base64: bytes.toString("base64") } : { data }), byte_length: bytes.length }, pane.record);
      if (!binary && !pasted && /[\r\n]/.test(data)) {
        pane.state = "busy"; pane.userDraft = false;
        pane.active = { id: randomUUID(), dispatch: `input:${receipt.request_id}`, at: new Date().toISOString(), nativeTurn: null };
        this.store.event("turn_submit_intent", { ...pane.active, source: "user", request_id: receipt.request_id }, pane.record);
      }
      try {
        pane.pty.write(binary ? bytes : data);
        this.store.event("terminal_input_written", { ...receipt, encoding, byte_length: bytes.length }, pane.record);
      } catch (error) {
        this.recordFailure(pane, "terminal_input_write_unknown", error, receipt);
        throw error;
      }
    });
    } finally { pane.pendingInputs--; }
  }
  async dispatch(pane: Pane, text: string, source: DispatchSource = "executor", inbox?: { id: string; sender: string }, context?: { kind: string; rejection_id: string }) {
    const previous = inbox ? this.store.inboxDispatch(inbox.id) : undefined;
    if (previous) {
      check(previous.launch === pane.record.id && previous.sender === inbox!.sender &&
        previous.text === `⟦主控 #${previous.seq}⟧\n${text}`, "inbox_dispatch_conflict");
      return previous;
    }
    check(!pane.failed && !pane.stopped, "pane_unavailable");
    check(typeof text === "string" && text.trim() && !/[\x00\x1b]/.test(text), "invalid_dispatch_text");
    const item = this.store.register(pane.record.id, text, source, context, inbox);
    pane.queue.push(item);
    this.store.event("dispatch_queued", item, pane.record);
    await this.drain(pane);
    return item;
  }
  wakeThread = async (thread: string, entry: A2AInboxEntry) => {
    const pane = this.get(thread);
    const item = await this.dispatch(pane, `收件箱 ${entry.kind} ${entry.id}\n${entry.body}`, "inbox", { id: entry.id, sender: entry.from });
    return { message: item.id, state: (await this.readWakeDelivery(thread, item.id)).state };
  };
  readWakeDelivery = async (thread: string, message: string): Promise<{ state: "queued" | "delivered" | "unknown"; at: string }> => {
    const item = this.store.dispatchRecord(message);
    check(item, "unknown_dispatch");
    const record = this.store.launchRecord(item.launch);
    check(record?.thread === thread, "wake_identity_mismatch");
    const last = this.store.db.prepare("SELECT time,type FROM orchestration_events WHERE launch=? AND json_extract(data,'$.dispatch')=? AND type IN ('turn_submitted','dispatch_unknown','dispatch_interrupted_before_submit') ORDER BY seq DESC LIMIT 1")
      .get(item.launch, item.id);
    if (last) return { state: last.type === "turn_submitted" ? "delivered" : "unknown", at: String(last.time) };
    const pane = this.panes.get(thread);
    const queued = pane && !pane.failed && !pane.stopped && !pane.archived &&
      (pane.sending === message || pane.queue.some(row => row.id === message));
    return { state: queued ? "queued" : "unknown", at: item.registered_at };
  };
  async drain(pane: Pane) {
    if (pane.state !== "idle" || pane.writing || pane.pendingInputs > 0 || pane.userDraft || pane.interrupted || !pane.queue.length || pane.failed) return;
    const submitted = this.store.db.prepare("SELECT count(*) AS n FROM orchestration_events WHERE launch=? AND type='turn_submit_intent'").get(pane.record.id)!;
    if (Number(submitted.n) >= pane.record.turn_limit) {
      this.store.event("queue_waiting_for_budget", { queued: pane.queue.map((item) => item.id), turn_limit: pane.record.turn_limit }, pane.record);
      return;
    }
    pane.writing = true;
    const item = pane.queue.shift()!;
    pane.sending = item.id;
    const submission = { id: randomUUID(), dispatch: item.id, at: new Date().toISOString(), nativeTurn: null };
    try { await this.serializeWrite(pane, async () => {
      this.store.event("paste_intent", { dispatch: item.id, text: item.text }, pane.record);
      pane.pty.write("\x1b[200~" + item.text + "\x1b[201~");
      this.store.event("paste_written", { dispatch: item.id }, pane.record);
      await new Promise((resolve) => setTimeout(resolve, 300));
      if (pane.interrupted) {
        this.store.event("dispatch_interrupted_before_submit", { dispatch: item.id }, pane.record);
        return;
      }
      pane.state = "busy"; pane.active = submission;
      this.store.event("turn_submit_intent", submission, pane.record);
      pane.pty.write("\r");
      this.store.event("turn_submitted", submission, pane.record);
    });
    } catch (error) {
      pane.state = "unknown"; pane.failed = String(error);
      this.store.event("dispatch_unknown", { dispatch: item.id, error: String(error) }, pane.record);
      throw error;
    } finally { pane.writing = false; pane.sending = null; }
  }
  async releaseByUser(thread: string, reason: string, recordAction: () => Promise<void>, assertCurrent: () => Promise<void>) {
    const pane = this.get(thread);
    check(reason.trim() && !pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
    const info = await this.processInfo(thread);
    check(info.leader && !info.failed, "foreground_agent_required", info);
    await assertCurrent();
    await recordAction();
    await this.serializeWrite(pane, async () => {
      await assertCurrent();
      check(!pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
      this.store.event("user_queue_release", { reason, previous_state: pane.state, previous_submission: pane.active?.id ?? null }, pane.record);
      pane.active = null; pane.userDraft = false; pane.interrupted = false; pane.state = "idle";
    });
    await this.drain(pane);
    return this.status(thread);
  }
  interruptThread = async (thread: string) => {
    const pane = this.get(thread);
    check(!pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
    const info = await this.processInfo(thread);
    check(info.leader && !info.failed, "foreground_agent_required", info);
    pane.interrupted = true; pane.state = "busy";
    await this.serializeWrite(pane, async () => {
      const current = await this.processInfo(thread);
      check(current.leader === info.leader && !current.failed, "identity_conflict", current);
      this.store.event("pane_interrupt_intent", { source: "gate", leader: info.leader }, pane.record);
      try {
        pane.pty.write("\x1b");
        this.store.event("pane_interrupt_written", { source: "gate", leader: info.leader }, pane.record);
      } catch (error) { this.recordFailure(pane, "pane_interrupt_unknown", error); throw error; }
    });
  };
  async release(thread: string, reason: string) {
    const pane = this.get(thread);
    check(pane.state === "unknown" && !pane.active && !pane.failed, "initial_release_only");
    const info = await this.processInfo(thread);
    check(info.leader && !info.failed, pane.record.cli === "Claude Code" ? "foreground_claude_required" : "foreground_codex_required", info);
    this.store.event("executor_action", { action: "initial_release", reason, source: "executor", process_info: info }, pane.record);
    pane.state = "idle";
    await this.drain(pane);
    return this.status(thread);
  }
  async screenKey(thread: string, input: {key:string;purpose:string;screen_id:string;screen_base64:string;authorization_ref:string;selected_label:string}, source: string) {
    const pane=this.get(thread);
    check(source==="executor" && pane.record.cli==="Claude Code" && pane.record.role==="controller" && pane.record.authentication==="isolated fake API only", "screen_operator_required");
    const {key,purpose,screen_id,screen_base64,authorization_ref,selected_label}=input;
    const keys:Record<string,string>={ArrowUp:"\x1b[A",ArrowDown:"\x1b[B",Enter:"\r",Digit1:"1"};
    check((purpose==="onboarding-theme" && ["ArrowUp","ArrowDown","Enter"].includes(key)) || (purpose==="workspace-trust" && key==="Digit1") || (purpose==="onboarding-notice" && key==="Enter"),"invalid_screen_key");
    check(typeof screen_id==="string" && screen_id.length>0 && screen_id.length<=128 && typeof authorization_ref==="string" && authorization_ref.trim() && typeof selected_label==="string" && selected_label.trim(),"invalid_screen_approval");
    const history=()=>this.store.read().filter(e=>e.launch===pane.record.id && e.type==="controller_screen_key_intent");
    const assertUnused=()=>{
      const past=history();
      check(!past.some(e=>e.data.screen_id===screen_id || e.data.screen_base64===screen_base64),"screen_key_already_used");
      if(purpose==="workspace-trust")check(!past.some(e=>e.data.purpose==="workspace-trust"),"workspace_trust_already_used");
      if(purpose==="onboarding-notice"){
        check(!past.some(e=>e.data.purpose==="onboarding-notice"),"onboarding_notice_already_used");
        const previous=past.at(-1)?.data;
        check(previous?.purpose==="onboarding-theme" && previous.key==="Enter" && previous.selected_label==="Dark mode","notice_requires_theme_confirmation");
      }
      if(purpose==="onboarding-theme" && key==="Enter"){
        // selected_label is the approved target after the key, not the prior cursor position.
        const before=past.at(-2)?.data;
        const previous=past.at(-1)?.data;
        check(selected_label==="Dark mode" && before?.purpose==="onboarding-theme" && before.key==="ArrowUp" && before.selected_label==="Auto (match terminal)" && previous?.purpose==="onboarding-theme" && previous.key==="ArrowDown" && previous.selected_label==="Dark mode","theme_selection_not_explicit");
      }
    };
    const assertStartup=()=>check(pane.state==="unknown" && !pane.active && !pane.failed && !pane.stopped && !pane.archived && !pane.writing && !pane.queue.length && !pane.userDraft && !pane.pendingInputs,"screen_requires_startup");
    assertStartup();assertUnused();
    await this.serializeWrite(pane,async()=>{
      assertStartup();assertUnused();
      const info=await this.processInfo(thread);check(info.leader && !info.failed,"foreground_claude_required");assertStartup();
      const observed=this.output(pane.record.id,0);
      check(observed.next_offset===observed.total_bytes && observed.data_base64===screen_base64 && screen_base64.length>0,"screen_changed");
      if(purpose==="onboarding-notice"){
        const before=Buffer.from(history().at(-1)!.data.screen_base64,"base64"),raw=Buffer.from(screen_base64,"base64");
        check(raw.length>before.length && raw.subarray(0,before.length).equals(before),"notice_trace_prefix_changed");
        check(noticeText(raw.subarray(before.length))===SECURITY_NOTICE_TEXT,"notice_text_mismatch");
      }
      this.store.event("controller_screen_key_intent",{source,key,purpose,screen_id,selected_label,directory:pane.record.worktree,authorization_ref,
        screen_base64,received_at:new Date().toISOString()},pane.record);
      try {pane.pty.write(keys[key]!);this.store.event("controller_screen_key_written",{source,key,purpose,screen_id,directory:pane.record.worktree},pane.record);}
      catch(error){this.recordFailure(pane,"screen_key_write_unknown",error);throw error;}
    });
    return {key,purpose,screen_id,written:true,state:pane.state};
  }
  status(thread: string) {
    const pane = this.panes.get(thread);
    if (pane) {
      this.scan(pane);
      return { thread, launch: pane.record.id, state: pane.failed || pane.stopped ? "unknown" : pane.state,
        lifecycle: pane.archived ? "ended" : pane.stopped ? "interrupted" : "running", shell_pid: pane.pty.pid,
        state_source: pane.failed ? "runtime_failure" : "host_events", active: pane.active, native_session: pane.native,
        turn: pane.turn, writing: pane.writing, user_draft: pane.userDraft, interrupted: pane.interrupted,
        queued: pane.queue.map((item) => item.id), failed: pane.failed, stopped: pane.stopped };
    }
    const record = this.store.threadLaunch(thread);
    check(record, "unknown_pane");
    const archived = this.store.lastEvent(record.id, ["pane_archived"]);
    const recovered = this.store.lastEvent(record.id, ["pane_recovered"]);
    return { thread, launch: record.id, state: "unknown", lifecycle: record.execution_state === "prepared" ? "not_started" : archived ? "ended" : recovered?.data.lifecycle ?? "unknown",
      shell_pid: recovered?.data.shell_pid ?? null, state_source: record.execution_state === "prepared" ? "launch_prepared" : archived ? "pane_archived" : recovered ? "pane_recovered" : "launch_record",
      active: null, native_session: null, turn: null, writing: false, queued: [], failed: null,
      stopped: archived ? true : recovered?.data.exit_event ? true : null, historical: true };
  }
  async signal(launch: string, raw: string, received_at: string,
    transfer?: (pane: Pane, stop: any, matched: boolean) => Promise<void>) {
    const pane = this.byLaunch(launch);
    this.store.event("hook_received", { raw_stdin: raw, received_at }, pane.record);
    const value = JSON.parse(raw); this.scan(pane);
    check(value.session_id === pane.native, "hook_native_session_mismatch");
    if (pane.record.cli === "Claude Code") {
      // P1's configured single submission avoids claiming cross-turn Stop
      // correlation before the actual CLI payload has been observed (T-078-2).
      check(pane.record.turn_limit === 1, "claude_turn_correlation_unverified");
      if (value.hook_event_name === "PermissionRequest") {
        this.store.event("permission_wait", value, pane.record); pane.state = "busy"; return;
      }
      if (value.hook_event_name === "UserPromptSubmit") {
        const item = pane.active && this.store.dispatchRecord(pane.active.dispatch);
        check(pane.state === "busy" && item && value.prompt === item.text && !pane.claudePrompt, "claude_submission_unmatched");
        pane.claudePrompt = true; this.store.event("turn_start_signal", value, pane.record); return;
      }
      check(value.hook_event_name === "Stop", "unsupported_hook");
      this.store.event("turn_end_signal", value, pane.record);
      const active = pane.active;
      const matched = Boolean(active && pane.claudePrompt && !pane.failed && !pane.stopInProgress &&
        value.stop_hook_active === false && Date.parse(received_at) >= Date.parse(active.at));
      if (!matched) { this.store.event("stop_not_matched", value, pane.record); return; }
      pane.stopInProgress = true;
      try {
        if (transfer) await transfer(pane, value, true);
        pane.active = null; pane.claudePrompt = false; pane.state = pane.interrupted ? "busy" : "idle";
        this.store.event(pane.state === "idle" ? "pane_idle" : "pane_completion_held", { submission: active!.id, stop: value }, pane.record);
      } catch (error) {
        this.recordFailure(pane, "stop_transfer_failed", error); throw error;
      } finally { pane.stopInProgress = false; }
      return;
    }
    if (value.hook_event_name === "PermissionRequest") {
      pane.failed = "unexpected_permission_request"; pane.state = "unknown";
      this.store.event("permission_wait", value, pane.record);
      return;
    }
    if (value.hook_event_name === "UserPromptSubmit") { this.store.event("turn_start_signal", value, pane.record); return; }
    check(value.hook_event_name === "Stop", "unsupported_hook");
    this.store.event("turn_end_signal", value, pane.record);
    const active = pane.active;
    const matched = Boolean(!pane.failed && !pane.stopInProgress && active?.nativeTurn && value.turn_id === active.nativeTurn && Date.parse(received_at) >= Date.parse(active.at));
    // The Stop handler transfers explicit files while the submitted turn still
    // owns its gate caller identity. A Stop alone never performs a gate command.
    if (matched) pane.stopInProgress = true;
    try {
      if (transfer) await transfer(pane, value, matched);
      if (!matched) { this.store.event("stop_not_matched", value, pane.record); return; }
      pane.active = null; pane.state = pane.failed ? "unknown" : pane.interrupted ? "busy" : "idle";
      this.store.event(pane.state === "idle" ? "pane_idle" : "pane_completion_held", { submission: active!.id, state: pane.state, stop: value }, pane.record);
    } catch (error) {
      if (matched) this.recordFailure(pane, "stop_transfer_failed", error);
      throw error;
    } finally { if (matched) pane.stopInProgress = false; }
  }
  authenticate(identity: any) {
    const pane = this.byLaunch(identity.launch);
    check(identity.token === pane.token, "invalid_launch_identity");
    return pane;
  }
  async caller(identity: any): Promise<SubmitCaller> {
    const pane = this.authenticate(identity);
    check(pane.attempt, "worker_attempt_required");
    const attempt = pane.attempt;
    this.scan(pane);
    check(pane.turn && pane.native === identity.native_session, "native_identity_required");
    const turn = pane.turn;
    return { thread: attempt.thread_id, turn, address: `${pane.record.role}:${attempt.thread_id}`,
      assertActive: async () => {
        const info = await this.processInfo(attempt.thread_id);
        check(info.leader && !info.failed && pane.state === "busy" && pane.active?.nativeTurn === turn, "worker_not_active");
      } };
  }
  readThread = async (thread: string) => {
    const pane = this.get(thread);
    check(pane.attempt, "worker_attempt_required");
    if (!pane.stopped) await this.processInfo(thread);
    return { workspace: pane.attempt.workspace, provider: "codex", turn: pane.turn,
      runtime_identity: { launch: pane.record.id, thread, shell_pid: pane.pty.pid,
        leader_pid: pane.leader, native_session: pane.native },
      running: (pane.state !== "idle" || pane.writing) && !pane.stopped && !pane.nativeEnded,
      stopped: pane.stopped, archived: pane.archived, session_ended: pane.nativeEnded,
      blocked: Boolean(pane.failed), ...(pane.failed ? { error: { providerPresent: !pane.stopped, activeTurn: pane.turn } } : {}) };
  };
  stopThread = async (thread: string) => {
    const pane = this.get(thread);
    check(pane.state === "idle", "worker_not_idle");
    await this.terminate(pane, "gate_reclaim");
  };
  archiveThread = async (thread: string) => {
    const pane = this.get(thread); check(pane.stopped, "worker_not_stopped");
    this.store.event("pane_archived", {}, pane.record); pane.archived = true;
  };
  async terminate(pane: Pane, reason: string) {
    if (pane.stopped) return;
    this.store.event("pane_stop_intent", { reason, shell_pid: pane.pty.pid }, pane.record);
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(() => reject(new Refusal("pane_stop_unconfirmed")), 5000);
      pane.pty.onExit(() => { clearTimeout(timer); resolve(); });
      pane.pty.kill("SIGHUP");
    });
  }
  async shutdown() { for (const pane of this.panes.values()) await this.terminate(pane, "daemon_shutdown_interruption"); }
}
