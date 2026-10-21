import { accessSync, appendFileSync, closeSync, constants, existsSync, fstatSync, mkdirSync, mkdtempSync, openSync, readFileSync, readSync, readdirSync, realpathSync, statSync } from "node:fs";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { randomBytes, randomUUID } from "node:crypto";
import { performance } from "node:perf_hooks";
import { AsyncLocalStorage } from "node:async_hooks";
import { validateHookEnvelope, questionFromHook, questionPermission, questionAnswerConfirmed, projectQuestions, nativeAnswerKeys, currentTurnBinding, noncurrentHook, currentTurnTrust } from './questions.ts';
import type { A2AAttempt, A2ATask, A2AReview, A2ARepair } from "./contracts/a2aGates.ts";
import { Refusal, type GateRuntime, type SubmitCaller } from "./gates/core.ts";
import { OrchestrationStore, type DispatchSource } from "./store.ts";
import type { A2AInboxEntry } from "./contracts/a2aInbox.ts";
import { claudeLaunch, type ClaudeLaunchInput } from "./claudeLaunch.ts";
import { ClaudeLogin } from "./claudeLogin.ts";
import { noticeText, SECURITY_NOTICE_TEXT } from "./claudeNotice.ts";
import { resumeArgv, nativeSessionFile, codexSessionOrigin, codexSessionFileName } from "./paneRecovery.ts";
import type { ExecutionOverrides } from './executionSettings.ts';

const exec = promisify(execFile);
const require = createRequire(import.meta.url);
const cli = fileURLToPath(new URL("./gates/cli.ts", import.meta.url));
const processQuery = fileURLToPath(new URL("./processSnapshot.py", import.meta.url));
// T-120: ordinary terminals start zsh through Enchanted's ZDOTDIR bootstrap, which
// loads the user's own startup files and then puts the a2a command and CLI shims first.
const terminalResources = fileURLToPath(new URL("../terminal/", import.meta.url));
const terminalCli = fileURLToPath(new URL("./terminalCli.ts", import.meta.url));
const quote = (value: string) => "'" + value.replaceAll("'", "'\\''") + "'";
const shellCommand = (argv: string[]) => argv.map(quote).join(" ");
function check(value: unknown, error: string, details?: unknown): asserts value {
  if (!value) throw new Refusal(error, details);
}
function requireFakeControllerRestore(record: Record<string, any>) {
  const env = record.env && typeof record.env === "object" && !Array.isArray(record.env) ? record.env : {};
  const shell = record.shell_argv;
  const command = Array.isArray(shell) ? shell[3] : undefined;
  // T-093: a missing authentication field must not downgrade a protected
  // launch. Any surviving normal-login marker requires a fresh protected start.
  const normal = record.authentication === "isolated normal login" ||
    typeof record.role_card_revision === "string" && record.role_card_revision.startsWith("T-093/normal-login/") ||
    record.login_audit_directory !== undefined || record.login_preflight_file !== undefined ||
    record.hook_authorization === "T-093/controller-start" || env.A2A_PROFILE_PROCESS_LOG !== undefined ||
    [env.HOME, env.CLAUDE_CONFIG_DIR].some(value => typeof value === "string" && value.startsWith("/private/tmp/a2a-claude-login-")) ||
    typeof env.NODE_OPTIONS === "string" && env.NODE_OPTIONS.includes("claudeLoginProcessTrace") ||
    typeof command === "string" && /^exec(?:\s|$)/.test(command);
  check(!normal, "normal_login_restore_requires_protected_start");
  // T-096's existing P1 contract is positive evidence, including for legacy
  // records without authentication. Unknown profiles never execute a CLI here.
  const base = typeof env.ANTHROPIC_BASE_URL === "string" && /^http:\/\/127\.0\.0\.1:([1-9][0-9]{0,4})$/.exec(env.ANTHROPIC_BASE_URL);
  const temporary = (value: unknown) => typeof value === "string" && value.startsWith("/private/tmp/") &&
    !value.includes("\0") && resolve(value) === value;
  check(record.role === "controller" && record.cli === "Claude Code" && ["ideation", "executor"].includes(record.preset) &&
    (record.authentication === undefined || record.authentication === "isolated fake API only") &&
    record.role_card_revision === "T-078-2/P1" && record.shell === "/bin/zsh" &&
    Array.isArray(shell) && shell.length === 4 && shell[0] === "-f" && shell[1] === "-i" && shell[2] === "-c" &&
    typeof command === "string" &&
    env.ANTHROPIC_AUTH_TOKEN === "a2a-fixture-key-not-a-secret" && base && Number(base[1]) <= 65535 &&
    new URL(env.ANTHROPIC_BASE_URL).origin === env.ANTHROPIC_BASE_URL &&
    temporary(env.HOME) && temporary(env.CLAUDE_CONFIG_DIR) && env.NODE_OPTIONS === undefined &&
    env.ANTHROPIC_API_KEY === undefined && env.CLAUDE_CODE_OAUTH_TOKEN === undefined,
    "restore_record_unrecognized");
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
    executable: string; settings: Record<string, unknown>;
    role_card: string; role_card_revision: string;
  }>>;
  codex_bin?: string;
  codex_home?: string;
  claude_bin?: string;
  // The reviewer role card for Claude Code reviewers, which need no pre-made home.
  reviewer_role_card?: string; reviewer_role_card_revision?: string;
  role_card?: string;
  role_card_revision?: string;
  code_revision?: string;
  source_snapshot?: string;
  hook_authorization?: string;
  turn_limit?: number;
  turn_authorization?: string;
  reviewers?: { codex_home: string; role_card: string; role_card_revision: string; hook_authorization: string }[];
}
export type EmptyInputDeclaration = {
  statement: "用户声明输入框已空"; launch: string; window_id: string;
  interruption: number; input_generation: number;
};
// Claude Code worker and reviewer launch (T-122, evidence/2026-10-21-batch19/T-122/probe-01..04):
// never asks for approval, file tools write only where `writable` allows, shell commands run in
// Claude's sandbox, and no settings file is loaded (`--setting-sources ""`: with `local`, a linked
// worktree also loads the main checkout's .claude/settings.local.json, probe-04), nor MCP servers.
// A worker writes its worktree and the request directory. In a linked worktree Claude's sandbox
// itself makes the repository's whole .git writable (probe-04), so `shellDenied` takes back every
// existing ref except the attempt's branch, packed-refs, HEAD and the other worktrees; a new ref
// name stays creatable and does not reach integration. A reviewer writes only its one-off
// candidate copy (its working directory). Both can still write Claude's $TMPDIR: denying it
// breaks every shell command (probe-04).
async function claudeArgv(executable: string, signal: string, session: string,
  selection: { model: string; effort: string; fast: boolean }, writable: string[], shellWritable: string[], shellDenied: string[] = []) {
  const hook = [{ hooks: [{ type: "command", command: signal, timeout: 10 }] }];
  const settings = {
    permissions: { allow: ["Bash", "Read", "Glob", "Grep", ...writable.map(path => `Edit(/${path}/**)`)] },
    sandbox: { enabled: true, autoAllowBashIfSandboxed: true, allowUnsandboxedCommands: false,
      filesystem: { allowWrite: shellWritable, ...(shellDenied.length ? { denyWrite: shellDenied } : {}) } },
    hooks: Object.fromEntries(["SessionStart", "UserPromptSubmit", "Stop", "PermissionRequest", "PreToolUse", "PostToolUse"].map(event => [event, hook])),
    fastMode: selection.fast,
  };
  return [executable, "--session-id", session, "--model", selection.model, "--effort", selection.effort, "--permission-mode", "dontAsk",
    "--setting-sources", "", "--strict-mcp-config", "--settings", JSON.stringify(settings)];
}
const CLAUDE_STARTUP_DEADLINE_MS = 120_000;
// The repository Git paths a Claude worker's shell must not write (see claudeArgv).
async function workerGitDenied(worktree: string) {
  const git = async (...args: string[]) => (await exec("git", ["-C", worktree, ...args])).stdout.trim();
  const common = realpathSync(await git("rev-parse", "--path-format=absolute", "--git-common-dir"));
  const own = realpathSync(await git("rev-parse", "--path-format=absolute", "--git-dir"));
  const branch = await git("symbolic-ref", "HEAD");
  const refs = (await git("for-each-ref", "--format=%(refname)")).split("\n").filter(ref => ref && ref !== branch);
  const worktrees = existsSync(join(common, "worktrees")) ? readdirSync(join(common, "worktrees")).map(name => join(common, "worktrees", name)) : [];
  return [...refs.flatMap(ref => [join(common, ref), join(common, "logs", ref)]),
    ...["packed-refs", "HEAD", "logs/HEAD", "refs/a2a", "refs/tags", "refs/remotes"].map(path => join(common, path)),
    ...worktrees.filter(path => path !== own)];
}
type Pane = {
  record: Record<string, any> & { id: string; task: string | null; attempt: string | null };
  token: string; task: A2ATask | null; attempt: A2AAttempt | null; pty: any;
  state: "unknown" | "idle" | "busy"; stopped: boolean; archived: boolean;
  failed: string | null; leader: number | null; native: string | null; turn: string | null;
  nativeEnded: boolean;
  active: { id: string; dispatch: string; at: string; nativeTurn: string | null } | null;
  queue: ReturnType<OrchestrationStore["register"]>[]; writing: boolean;
  stopInProgress: boolean;
  writes: Promise<void>; pendingInputs: number; userDraft: boolean; interrupted: boolean; sending: string | null;
  inputGeneration: number; interruption: number | null;
  offsets: Map<string, number>; model: string; effort: string;
  terminalBuffer: string;
  nativeFile?: string;
  // Claude worker start-up: the folder-trust screen as read so far, and whether it was answered.
  startupScreen?: string; trustAnswered?: boolean; startupOutputAt?: number; started?: boolean;
  claudePromptId?: string | null;
  claudePromptIds?: Set<string>;
  permission?: { prompt_id: string; submission: string } | null;
  login?: ClaudeLogin;
  loginCleanup?: Promise<void>;
  closing?: boolean;
  shellChildren?: number[];
};


// Runtime variables a running Claude Code or Codex session sets for its own child
// processes (observed in their shells, 2026-10-21). Inherited by a user's terminal,
// they make a CLI started there act as a child session (Claude stops saving it).
// User configuration such as CLAUDE_CODE_OAUTH_TOKEN or CLAUDE_CODE_USE_BEDROCK is kept.
const agentSessionMarkers = new Set(["CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_CHILD_SESSION",
  "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_SESSION_ATTENDED", "CLAUDE_CODE_EXECPATH", "CLAUDE_CODE_PLUGIN_DIRS",
  "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_CODE_SSE_PORT", "CLAUDE_PID", "CLAUDE_EFFORT",
  "CODEX_THREAD_ID", "CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED"]);
export class Panes implements GateRuntime {
  // Bound by the authenticated controller request, isolated across awaits.
  // This is ancestry metadata only; gate authority still uses SubmitCaller.
  readonly parentLaunch = new AsyncLocalStorage<string | null>();
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
  startShell(project: string | null, cwd: string) {
    check(project === null || typeof project === "string" && /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(project), "invalid_project");
    check(typeof cwd === "string" && isAbsolute(cwd) && statSync(cwd).isDirectory(), "invalid_shell_cwd");
    const worktree = realpathSync(cwd), launch = randomUUID(), thread = randomUUID();
    const environment = { ...process.env };
    for (const key of Object.keys(environment)) {
      if (key.startsWith("A2A_") || key.startsWith("GIT_CONFIG_") || agentSessionMarkers.has(key)) delete environment[key];
    }
    // The packaged daemon itself runs Electron as Node; the user's shell must not.
    delete environment.ELECTRON_RUN_AS_NODE;
    if (project !== null) environment.A2A_PROJECT = project;
    const token = randomBytes(32).toString("hex");
    if (environment.ZDOTDIR !== undefined) Object.assign(environment, { A2A_USER_ZDOTDIR: environment.ZDOTDIR, A2A_USER_ZDOTDIR_SET: "1" });
    Object.assign(environment, { ZDOTDIR: join(terminalResources, "zdotdir"), A2A_TERMINAL_ZDOTDIR: join(terminalResources, "zdotdir"),
      A2A_TERMINAL_BIN: join(terminalResources, "bin"), A2A_TERMINAL_PLUGIN: join(terminalResources, "plugin/enchanted-a2a"),
      A2A_TERMINAL_CLI: terminalCli, A2A_NODE: process.execPath, A2A_STATE: this.root, A2A_TERMINAL: launch, A2A_TERMINAL_TOKEN: token });
    const record = { id: launch, project, task: null, attempt: null, session: null, fence: null,
      spec_rev: null, thread, role: "shell", created_at: new Date().toISOString(),
      shell: "/bin/zsh", shell_argv: ["-l", "-i"], worktree, env: project === null ? {} : { A2A_PROJECT: project } };
    this.store.launch(record);
    const trace = join(this.root, "traces", launch, "pty.raw");
    mkdirSync(dirname(trace), { recursive: true, mode: 0o700 });
    appendFileSync(trace, "", { flag: "wx", mode: 0o600 });
    const terminal = require("node-pty").spawn(record.shell, record.shell_argv, {
      name: "xterm-256color", cols: 160, rows: 45, cwd: worktree, env: environment, encoding: "utf8",
    });
    const pane: Pane = { record, token, task: null, attempt: null, pty: terminal, state: "unknown",
      stopped: false, archived: false, failed: null, leader: null, native: null, turn: null,
      nativeEnded: false, active: null, queue: [], writing: false, stopInProgress: false,
      writes: Promise.resolve(), pendingInputs: 0, userDraft: false, interrupted: false, sending: null,
      inputGeneration: 0, interruption: null, offsets: new Map(), model: "unknown", effort: "unknown", terminalBuffer: "" };
    this.panes.set(thread, pane);
    terminal.onData((data: string) => {
      try { appendFileSync(trace, data); }
      catch (error) { this.recordFailure(pane, "trace_write_failed", error); }
    });
    terminal.onExit((event: unknown) => {
      pane.stopped = true;
      try { this.store.event("shell_closed", { role: "shell", reason: "process_exit", event, shell_pid: terminal.pid }, record); }
      catch (error) { this.recordFailure(pane, "shell_close_write_failed", error); }
    });
    this.store.event("shell_created", { role: "shell", cwd: worktree, shell_pid: terminal.pid }, record);
    this.rememberOpen(launch, this.store.openPanes(undefined, project ?? undefined).length);
    return record;
  }
  async shellInput(launch: string, data: string, encoding: "utf8" | "binary", assertCurrent: () => Promise<void>) {
    const pane = this.byLaunch(launch);
    check(pane.record.role === "shell", "shell_required");
    await this.serializeWrite(pane, async () => {
      await assertCurrent();
      check(!pane.failed && !pane.stopped && !pane.archived && !pane.closing, "pane_unavailable");
      try { pane.pty.write(encoding === "binary" ? Buffer.from(data, "latin1") : data); }
      catch (error) { this.recordFailure(pane, "shell_input_write_unknown", error); throw error; }
    });
  }
  async closeShell(launch: string) {
    const record = this.launchRecord(launch);
    check(record.role === "shell", "shell_required");
    const pane = this.panes.get(record.thread);
    if (pane) await this.terminate(pane, "shell_close");
    else check(this.store.lastEvent(launch, ["shell_closed"]), "shell_exit_unconfirmed");
    this.forgetOpen(launch);
  }
  async startController(task: A2ATask, input: ClaudeLaunchInput) {
    let login: ClaudeLogin | undefined;
    try {
    if (input.authentication === "normal-login") login = await ClaudeLogin.prepare(input, task.repo);
    else check(new URL(input.api_url!).port !== "0", "messages_api_not_bound");
    const selection = this.store.executionSelection(input.preset, input.execution ?? {});
    const record = { ...claudeLaunch(task, { ...input, execution: selection }, login?.isolation), parent_launch: input.parent_launch ?? null,
      created_at: new Date().toISOString(), executable_path: "",
      cli_version: "unknown", version_probe: null as { argv: string[]; stdout: string; stderr: string } | null };
      const expectedVersion = record.cli_version_expected;
      let probe;
      try {
        probe = login?.versionProbe ?? await exec(input.executable, ["--version"], { env: record.env, timeout: 10000, maxBuffer: 65536 });
      } catch (error) {
        const failure = error as NodeJS.ErrnoException;
        throw new Refusal(failure.code === "ENOENT" ? "controller_executable_missing" : "controller_version_probe_failed",
          { executable: input.executable, expected: expectedVersion, cause: failure.code, message: failure.message });
      }
      const version = probe.stdout.trim();
      // Keep the actual argv (which may use a valid alias), but bind the live
      // identity to the canonical executable now, before starting the PTY.
      record.executable_path = realpathSync(input.executable);
      record.cli_version = version;
      record.version_probe = { argv: login?.versionProbe.argv ?? [input.executable, "--version"], stdout: probe.stdout, stderr: probe.stderr };
      if (login) await login.preflight(record);
      // Version and preflight await other work. Keep the ownership check next
      // to synchronous registration so concurrent starts cannot claim one preset.
      check(![...this.panes.values()].some(p => !p.stopped && p.record.preset === input.preset), "controller_already_started");
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
        userDraft: false, interrupted: false, inputGeneration: 0, interruption: null, sending: null, offsets: new Map(), model: "unknown", effort: "unknown",
        terminalBuffer: "", claudePromptId: null, claudePromptIds: new Set(), login };
      login?.recordChild(terminal.pid, "PTY helper -> zsh -> CLI");
      this.panes.set(record.thread, pane);
      this.store.event("pane_started", { shell_pid: terminal.pid, state: "unknown" }, record);
      terminal.onData((data: string) => {
        try { if (login) login.observe(data, trace); else appendFileSync(trace, data); this.terminalProtocol(pane, data); }
        catch (error) { this.recordFailure(pane, "controller_terminal_failed", error); }
      });
      terminal.onExit((event: unknown) => {
        pane.stopped = true; pane.state = "unknown";
        if (!pane.claudePromptId && !pane.closing && (event as { exitCode?: number }).exitCode !== 0)
          this.recordFailure(pane, 'launch_failed', new Error('native_cli_exit'), { event });
        try { this.store.event("pane_exit", event, record); }
        catch (error) { this.recordFailure(pane, "pane_exit_write_failed", error); }
        if (login) {
          // The normal profile execs the CLI in this PTY's process group.
          // Remove any remaining hook/tool children before deleting its HOME.
          pane.loginCleanup = (async () => {
            try { process.kill(-terminal.pid, "SIGKILL"); }
            catch (error) { if ((error as NodeJS.ErrnoException).code !== "ESRCH") throw new Refusal("login_group_cleanup_failed"); }
            const until = Date.now() + 5000;
            for (;;) {
              try { process.kill(-terminal.pid, 0); }
              catch (error) { if ((error as NodeJS.ErrnoException).code === "ESRCH") break; throw new Refusal("login_group_cleanup_failed"); }
              if (Date.now() >= until) throw new Refusal("login_group_exit_unconfirmed");
              await new Promise(resolve => setTimeout(resolve, 25));
            }
            await login.finish(record);
          })().catch(() => {
            this.recordFailure(pane, "login_fact_collection_failed", new Refusal("login_fact_collection_failed"));
          });
        }
      });
      return record;
    } catch (error) { await login?.discard(); throw error; }
  }
  // T-078-1/#49: prepare argv and its durable record only. Actual Claude launch,
  // auth, hooks and completion matching await decision 20261011T101958Z. This
  // method neither creates a live pane nor issues a launch capability.
  prepareControllerLaunch(task: A2ATask, preset: string, parentLaunch?: string, overrides: ExecutionOverrides = {}) {
    check(preset === "ideation" || preset === "executor", "invalid_controller_preset");
    const c = this.config.controllers?.[preset];
    const nonempty = (value: unknown): value is string => typeof value === "string" && Boolean(value.trim()) && !value.includes("\0");
    check(c && nonempty(c.executable) && isAbsolute(c.executable) &&
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
    const selection = this.store.executionSelection(preset, overrides);
    settings.fastMode = selection.fast;
    const argv = [c.executable, "--session-id", session, "--model", selection.model, "--effort", selection.effort, "--settings", JSON.stringify(settings)];
    const record = { id: launch, project: task.project_id, task: task.task_id, attempt: null,
      session, fence: null, spec_rev: task.spec_rev, thread, role: "controller", preset, parent_launch: parentLaunch ?? null,
      execution_state: "prepared", validation: "待真实 Claude 复核", created_at: new Date().toISOString(),
      cli: "Claude Code", cli_version: "unknown", argv, settings,
      model_requested: selection.model, effort_requested: selection.effort, service_tier_requested: selection.fast ? 'fast' : 'default',
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
  rememberOpen(id: string, position: number) {
    check(Number.isSafeInteger(position) && position >= 0, "invalid_pane_position");
    const record = this.launchRecord(id), pane = this.panes.get(record.thread);
    const previous = this.store.openPanes().find(p => p.launch === id);
    check(pane && !pane.stopped && !pane.archived || previous, "pane_unavailable");
    if (pane) this.scan(pane);
    const native = pane?.native ?? previous?.native_session ?? null;
    // A pane can open before native metadata has arrived. Keep that unknown
    // explicit; scan() records its later binding without inventing a session.
    this.store.event("pane_layout_opened", { position, native_session: native,
      resume_argv: native ? resumeArgv(record, native) : null }, record as any);
  }
  forgetOpen(id: string) {
    const record = this.launchRecord(id);
    this.store.event("pane_layout_closed", {}, record as any);
  }
  async recover(daemon: string) {
    for (const record of this.store.launches()) {
      if (record.role === "shell") {
        // A user's terminal is never resumed or turned into an agent session.
        if (!this.store.lastEvent(record.id, ["shell_closed"])) {
          const start = this.store.lastEvent(record.id, ["shell_created"]);
          const pid = start?.data.shell_pid;
          try {
            if (Number.isSafeInteger(pid) && pid > 1) {
              const result = await exec("/usr/bin/python3", ["-I", "-S", "-B", processQuery, String(pid)], { timeout: 5000 });
              check(JSON.parse(result.stdout).rows.length === 0, "shell_exit_unconfirmed");
            }
            this.store.event("shell_closed", { role: "shell", reason: "daemon_restart", shell_pid: pid ?? null }, record as any);
          } catch (error) {
            this.store.event("shell_exit_unconfirmed", { role: "shell", shell_pid: pid ?? null, error: String(error) }, record as any);
          }
        }
        continue;
      }
      if (record.execution_state === "prepared") continue;
      if (this.store.lastEvent(record.id, ["pane_recovered", "pane_archived"])) continue;
      const exit = this.store.lastEvent(record.id, ["pane_exit"]);
      const start = this.store.lastEvent(record.id, ["pane_started"]);
      this.store.event("pane_recovered", { daemon, state: "unknown", lifecycle: exit ? "interrupted" : "unknown",
        reason: "daemon_restart", shell_pid: start?.data.shell_pid ?? null,
        exit_event: exit?.seq ?? null, session: record.session, fence: record.fence, spec_rev: record.spec_rev }, record as any);
    }
    for (const opened of this.store.openPanes()) {
      const record = this.launchRecord(opened.launch);
      if (record.role === "shell") continue;
      this.store.event("pane_restore_pending", { daemon, position: opened.position }, record as any);
      try {
        // T-096 decision B: worker/reviewer attempts retain their gate-owned
        // runtime binding. Restoration must neither spawn nor mutate an attempt.
        check(record.attempt === null, "restore_managed_attempt_requires_reclaim");
        requireFakeControllerRestore(record);
        const argv = resumeArgv(record, opened.native_session);
        check(record.shell_argv[3] === shellCommand(record.argv) + "; exec /bin/zsh -f -i", "restore_record_unrecognized");
        const previous = this.store.lastEvent(record.id, ["pane_started", "pane_restored"]);
        if (Number.isSafeInteger(previous?.data.shell_pid) && previous!.data.shell_pid > 1) {
          try {
            process.kill(previous!.data.shell_pid, 0);
            throw new Refusal("restore_previous_process_alive");
          } catch (error) {
            if ((error as NodeJS.ErrnoException).code !== "ESRCH") throw error;
          }
        }
        check(opened.resume_argv && argv.length === opened.resume_argv.length &&
          argv.every((arg, index) => arg === opened.resume_argv![index]), "restore_argv_changed");
        const taskRow = this.store.db.prepare("SELECT data FROM tasks WHERE id=?").get(record.task);
        const task = taskRow && JSON.parse(String(taskRow.data));
        check(task && task.project_id === record.project && task.spec_rev === record.spec_rev, "restore_task_stale");
        check(typeof record.cli_version === "string" && record.cli_version !== "unknown", "restore_version_missing");
        // Native CLIs update themselves; the restored runtime records its own probe.
        const probe = await exec(argv[0]!, ["--version"], { env: record.env, timeout: 10000, maxBuffer: 65536 });
        const nativeFile = nativeSessionFile(record, opened.native_session!);
        check(record.shell === "/bin/zsh" && record.env && isAbsolute(record.worktree), "restore_launch_invalid");
        const executablePath = realpathSync(argv[0]!);
        check(record.executable_path === undefined || record.executable_path === executablePath, "restore_executable_changed");
        // Legacy launch history is immutable. Bind this restored runtime only,
        // after the session checks and before creating a PTY; it carries the CLI version now installed.
        const runtimeRecord = { ...record, executable_path: executablePath, cli_version: probe.stdout.trim() };
        const token = randomUUID();
        const trace = join(this.root, "traces", record.id, "pty.raw");
        check(existsSync(trace), "trace_unavailable");
        const shellArgv = ["-f", "-i", "-c", shellCommand(argv) + "; exec /bin/zsh -f -i"];
        const terminal = require("node-pty").spawn(record.shell, shellArgv, {
          name: "xterm-256color", cols: 160, rows: 45, cwd: record.worktree,
          env: { ...record.env, A2A_CAPABILITY: token }, encoding: "utf8",
        });
        const pane: Pane = { record: runtimeRecord as Pane["record"], token, task, attempt: null, pty: terminal,
          state: "unknown", stopped: false, archived: false, failed: null, leader: null,
          native: opened.native_session, nativeFile, turn: null, nativeEnded: false, active: null,
          queue: [], writing: false, stopInProgress: false, writes: Promise.resolve(), pendingInputs: 0,
          userDraft: false, interrupted: false, inputGeneration: 0, interruption: null, sending: null,
          offsets: new Map([[nativeFile, readFileSync(nativeFile).length]]), model: "unknown", effort: "unknown",
          terminalBuffer: "", claudePromptId: null, claudePromptIds: new Set() };
        this.panes.set(record.thread, pane);
        terminal.onData((data: string) => {
          try { appendFileSync(trace, data); this.terminalProtocol(pane, data); }
          catch (error) { this.recordFailure(pane, "restore_terminal_failed", error); }
        });
        terminal.onExit((event: unknown) => {
          pane.stopped = true; pane.state = "unknown";
          try { this.store.event("pane_exit", event, pane.record); }
          catch (error) { this.recordFailure(pane, "pane_exit_write_failed", error); }
        });
        // Creating a shell is not proof the recorded CLI resumed. Require the
        // existing foreground executable/native-identity check before success.
        const deadline = Date.now() + 10000;
        let info: Awaited<ReturnType<Panes["processInfo"]>>;
        do {
          info = await this.processInfo(record.thread);
          check(!info.failed && !pane.stopped, "restore_process_failed");
          if (info.leader) break;
          await new Promise(resolve => setTimeout(resolve, 50));
        } while (Date.now() < deadline);
        check(info.leader, "restore_process_missing");
        this.store.event("pane_restored", { daemon, position: opened.position, argv,
          shell_argv: shellArgv, shell_pid: terminal.pid, leader: info.leader,
          native_session: opened.native_session, version_probe: { argv: [argv[0], "--version"], stdout: probe.stdout, stderr: probe.stderr } }, pane.record);
      } catch (error) {
        const pane = this.panes.get(record.thread);
        let cleanup: string | null = null;
        if (pane) {
          pane.failed = "restore_failed";
          try { await this.terminate(pane, "restore_failed"); }
          catch (stopError) { cleanup = String(stopError); pane.failed = "restore_cleanup_unconfirmed"; }
        }
        this.store.event("pane_restore_failed", { daemon, error: error instanceof Refusal ? error.code : "restore_failed",
          details: error instanceof Refusal && error.code === "normal_login_restore_requires_protected_start" ?
            "正常登录会话不自动续接，请经正常登录入口重新启动。" : String(error),
          cleanup, native_session: opened.native_session }, record as any);
      }
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
  async createThread(task: A2ATask, attempt: A2AAttempt, overrides: ExecutionOverrides = {}) {
    check([...this.panes.values()].filter((pane) => pane.record.role === "worker")
      .every((pane) => pane.stopped && pane.archived), "single_worker_slice");
    check(attempt.runtime_mode === "workspace-write", "worker_requires_workspace_write");
    await this.createPane(task, attempt, this.config, undefined, overrides);
  }
  async createReview(task: A2ATask, review: A2AReview, prompt: string) {
    const attempt = { ...review.attempt, session_id: review.session_id, thread_id: review.thread_id,
      workspace: review.candidate_workspace, runtime_identity: null, turn_id: null };
    if (task.card.executor.cli === "Claude Code") {
      // D24: the reviewer defaults to the worker's CLI and model; it runs with the worker launch's selection.
      const worker = this.launchRecord(review.attempt.runtime_identity!.launch);
      check(this.config.reviewer_role_card && this.config.reviewer_role_card_revision, "review_launch_config_required");
      await this.createPane(task, attempt, { ...this.config, role_card: this.config.reviewer_role_card,
        role_card_revision: this.config.reviewer_role_card_revision }, review,
        { model: worker.model_requested, effort: worker.effort_requested, fast: worker.service_tier_requested === "fast" });
    } else await this.createCodexReview(task, review, attempt);
    const pane = this.get(review.thread_id);
    await this.dispatch(pane, `${pane.record.role_text}\n\n${prompt}`);
  }
  private async createCodexReview(task: A2ATask, review: A2AReview, attempt: A2AAttempt) {
    const index = this.store.launches().filter((record) => record.role === "reviewer").length;
    const approved = this.config.reviewers?.[index];
    check(approved, "review_launch_config_required");
    const home = realpathSync(approved.codex_home);
    check(home !== realpathSync(this.config.codex_home!) &&
      !this.store.launches().some((record) => record.env.CODEX_HOME === home), "review_home_reused");
    check(!existsSync(join(home, "sessions")) || readdirSync(join(home, "sessions")).length === 0, "review_home_not_empty");
    await this.createPane(task, attempt, { ...this.config, ...approved }, review);
  }
  private async createPane(task: A2ATask, attempt: A2AAttempt, c: LaunchConfig, review?: A2AReview, overrides: ExecutionOverrides = {}) {
    const role = review ? "reviewer" : "worker";
    // The task card names the worker's CLI; its reviewer runs on the same CLI (D24).
    const claude = task.card.executor.cli === "Claude Code";
    check((claude ? c.claude_bin : c.codex_bin && c.codex_home) && c.role_card && c.hook_authorization && c.code_revision && c.role_card_revision, "launch_config_required");
    check(Number.isInteger(c.turn_limit) && c.turn_limit! > 0 && c.turn_limit! <= (claude ? 6 : 10), "invalid_turn_limit");
    const executable = realpathSync(claude ? c.claude_bin! : c.codex_bin!);
    const home = claude ? null : realpathSync(c.codex_home!);
    if (!claude) check(home !== join(process.env.HOME ?? "", ".codex"), "isolated_codex_home_required");
    const environment: Record<string, string> = {};
    for (const key of ["PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "USER", "LOGNAME",
      "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL",
      // A Claude worker reaches the API the way the daemon's user does (login, or a gateway URL and token).
      ...(claude ? ["ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN"] : [])]) {
      if (process.env[key]) environment[key] = process.env[key]!;
    }
    if (home) environment.CODEX_HOME = home;
    // Record the installed version; native CLIs are expected to update (user decision 2026-10-21).
    const version = (await exec(executable, ["--version"], { env: environment })).stdout.trim();
    const helper = spawnHelper();
    const launch = randomUUID(), token = randomUUID();
    const requestDirectory = realpathSync(mkdtempSync("/tmp/a2a-requests-"));
    // In the packaged app process.execPath is Electron; it acts as Node only with this variable.
    const signalCommand = "ELECTRON_RUN_AS_NODE=1 " + shellCommand([process.execPath, cli, "--state", this.root, "signal", "--launch", launch]);
    const hook = `[{hooks=[{type="command",command=${JSON.stringify(signalCommand)},timeout=10}]}]`;
    // Role settings hold one selection per role; a Claude Code card's own model and effort are its
    // defaults, since the factory worker selection is a Codex model (review finding 3).
    const { model, effort, fast } = this.store.executionSelection(role, claude && !review
      ? { ...(task.card.executor.model.trim() ? { model: task.card.executor.model } : {}),
          ...(task.card.executor.effort.trim() ? { effort: task.card.executor.effort } : {}), ...overrides } : overrides);
    const launchWorkspace = review ? review.candidate_workspace : attempt.workspace;
    const nativeSession = claude ? randomUUID() : null;
    const sandboxMode = "workspace-write";
    const networkAccess = "false";
    const networkProxy = "false";
    const excludeSlashTmp = review ? "true" : "false";
    const excludeTmpdir = review ? "true" : "false";
    const argv = claude ? await claudeArgv(executable, signalCommand, nativeSession!, { model, effort, fast },
      review ? [realpathSync(launchWorkspace)] : [realpathSync(launchWorkspace), requestDirectory],
      review ? [] : [requestDirectory], review ? [] : await workerGitDenied(launchWorkspace)) : [executable, "--no-daemon", "--no-alt-screen", "-C", launchWorkspace,
      "-a", "never", "--sandbox", sandboxMode, "-m", model,
      "-c", `model_reasoning_effort=${JSON.stringify(effort)}`, "-c", `service_tier=${JSON.stringify(fast ? 'fast' : 'default')}`,
      "-c", "check_for_update_on_startup=false", "-c", "tui.notifications=false",
      "-c", `sandbox_workspace_write.network_access=${networkAccess}`, "-c", `features.network_proxy=${networkProxy}`,
      ...(review ? ["-c", `sandbox_workspace_write.exclude_slash_tmp=${excludeSlashTmp}`,
        "-c", `sandbox_workspace_write.exclude_tmpdir_env_var=${excludeTmpdir}`] : [])];
    if (!claude) {
      for (const event of ["UserPromptSubmit", "Stop", "PermissionRequest", "PreToolUse", "PostToolUse"]) argv.push("-c", `hooks.${event}=${hook}`);
      argv.push("--dangerously-bypass-hook-trust");
    }
    Object.assign(environment, {
      SHELL: "/bin/zsh", TERM: "xterm-256color", COLORTERM: "truecolor",
      A2A_PROJECT: task.project_id, A2A_TASK: task.task_id, A2A_ATTEMPT: attempt.attempt_id,
      A2A_SESSION: attempt.session_id, A2A_ROLE: role, A2A_LAUNCH: launch,
      A2A_STATE: this.root, A2A_CLI: cli, A2A_NODE: process.execPath, A2A_CAPABILITY: token,
      A2A_REQUEST_DIR: requestDirectory,
      A2A_FENCE: String(attempt.fence), A2A_SPEC_REV: String(attempt.spec_rev),
      A2A_TOOL: version, A2A_MODEL_REQUESTED: model, A2A_EFFORT_REQUESTED: effort,
      ...(claude ? { A2A_NATIVE_SESSION: nativeSession! } : {}),
    });
    if (review) environment.A2A_REVIEW = review.review_id;
    else Object.assign(environment, { GIT_CONFIG_COUNT: "1", GIT_CONFIG_KEY_0: "core.hooksPath",
      GIT_CONFIG_VALUE_0: fileURLToPath(new URL("../hooks/", import.meta.url)) });
    const shellArgv = ["-f", "-i", "-c", shellCommand(argv) + "; a2a_cli_status=$?; if (( a2a_cli_status != 0 )); then exit $a2a_cli_status; fi; exec /bin/zsh -f -i"];
    const { A2A_CAPABILITY: _secret, ...recordedEnvironment } = environment;
    const record = { id: launch, project: task.project_id, task: task.task_id, attempt: attempt.attempt_id,
      session: attempt.session_id, fence: attempt.fence, spec_rev: attempt.spec_rev, thread: attempt.thread_id,
      role, sandbox: "workspace-write", parent_launch: this.parentLaunch.getStore() ?? null,
      cli: claude ? "Claude Code" : "Codex", ...(claude ? { native_session: nativeSession } : {}),
      ...(review ? { review_id: review.review_id, review_verification_id: review.verification_id,
        review_workspace: review.workspace, candidate_workspace: review.candidate_workspace,
        ...(claude ? {} : { review_home_was_empty: true }) } : {}),
      created_at: new Date().toISOString(), cli_version: version, argv, executable_path: executable, request_dir: requestDirectory,
      model_requested: model, effort_requested: effort, service_tier_requested: fast ? 'fast' : 'default',
      turn_limit: c.turn_limit, turn_authorization: c.turn_authorization ?? null,
      code_revision: c.code_revision, source_snapshot: c.source_snapshot ?? null, role_card: c.role_card, role_card_revision: c.role_card_revision,
      role_text: readFileSync(c.role_card, "utf8"), base_commit: attempt.base_commit, worktree: launchWorkspace,
      shell: "/bin/zsh", shell_argv: shellArgv, env: recordedEnvironment, helper, hook_authorization: c.hook_authorization };
    this.store.launch(record);
    mkdirSync(join(this.root, "traces", launch), { recursive: true, mode: 0o700 });
    appendFileSync(join(this.root, "traces", launch, "pty.raw"), "", { flag: "wx", mode: 0o600 });
    const terminal = require("node-pty").spawn("/bin/zsh", shellArgv, {
      name: "xterm-256color", cols: 160, rows: 45, cwd: attempt.workspace, env: environment, encoding: "utf8",
    });
    const pane: Pane = { record, token, task, attempt, pty: terminal, state: "unknown", stopped: false,
      archived: false, failed: null, leader: null, native: nativeSession, turn: null, nativeEnded: false, active: null,
      queue: [], writing: false, stopInProgress: false, writes: Promise.resolve(), pendingInputs: 0, userDraft: false, interrupted: false, inputGeneration: 0, interruption: null, sending: null,
      offsets: new Map(), model: "unknown", effort: "unknown", terminalBuffer: "",
      ...(claude ? { claudePromptId: null, claudePromptIds: new Set<string>(), startupScreen: "", trustAnswered: false } : {}) };
    this.panes.set(attempt.thread_id, pane);
    this.store.event("pane_started", { shell_pid: terminal.pid, state: "unknown" }, record);
    // A Claude session that never reports its start (an unrecognised screen, a CLI that changed)
    // is a failure to show, not a pane that waits forever with its task queued.
    if (claude) setTimeout(() => {
      if (!pane.started && !pane.stopped && !pane.failed)
        this.recordFailure(pane, "worker_startup_unrecognised", new Error("session_start_missing"), { screen: pane.startupScreen });
    }, CLAUDE_STARTUP_DEADLINE_MS).unref();
    terminal.onData((data: string) => {
      try {
        appendFileSync(join(this.root, "traces", launch, "pty.raw"), data);
      } catch (error) { this.recordFailure(pane, "trace_write_failed", error); return; }
      try { this.scan(pane); }
      catch (error) { this.recordFailure(pane, "native_read_failed", error); return; }
      if (claude && pane.state === "unknown") this.confirmWorkerTrust(pane, data);
      try { this.terminalProtocol(pane, data); }
      catch (error) { this.recordFailure(pane, "terminal_protocol_failed", error); }
    });
    terminal.onExit((event: unknown) => {
      // The CLI can flush rollout records while exiting without emitting Stop.
      const startupFailed = !pane.native && !pane.closing && (event as { exitCode?: number }).exitCode !== 0;
      // Read after exit, before publishing the terminal lifecycle transition.
      try {
        this.scan(pane, true);
        if (home) this.store.event("native_final_read", { native_session: pane.native,
          offsets: [...pane.offsets].map(([file, offset]) => ({ file: relative(home, file), offset })) }, record);
      } catch (error) {
        this.recordFailure(pane, "native_final_read_failed", error, { native_session: pane.native,
          offsets: [...pane.offsets].map(([file, offset]) => ({ file: relative(home!, file), offset })),
          details: error instanceof Refusal ? error.details : null });
      }
      if (startupFailed) this.recordFailure(pane, 'launch_failed', new Error('native_cli_exit'), { event });
      pane.stopped = true; pane.state = "unknown";
      try { this.store.event("pane_exit", event, record); }
      catch (error) { this.recordFailure(pane, "pane_exit_write_failed", error); }
    });
  }
  // A Claude worker starts in a worktree a2a created, outside any folder the user trusted,
  // so Claude asks whether to trust it. User decision 2026-10-21: answer it for the
  // worker, only before it has received any task, and record that. An unrecognised
  // screen is left alone; the worker then never reports ready and no task is sent.
  confirmWorkerTrust(pane: Pane, data: string) {
    // Only during start-up: never once the session has started, even if it later returns to unknown.
    if (pane.started || pane.active || pane.state !== "unknown") return;
    // Keep reading while the answer is in progress: it checks the redrawn selection.
    pane.startupOutputAt = Date.now();
    pane.startupScreen = (pane.startupScreen! + data.replace(/\x1b\[[0-?]*[ -\/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\)/g, "").replace(/\s+/g, "")).slice(-4096);
    if (pane.trustAnswered || !pane.startupScreen.includes("Yes,Itrustthisfolder")) return;
    pane.trustAnswered = true;
    const screen = pane.startupScreen;
    // Writes go through the pane's write queue, but the wait does not hold it: Claude's
    // terminal capability queries must still be answered meanwhile, or it redraws the dialog.
    const press = (key: string) => this.serializeWrite(pane, async () => { pane.pty.write(key); });
    const selected = () => {
      const yes = pane.startupScreen!.lastIndexOf("❯Yes,Itrustthisfolder"), no = pane.startupScreen!.lastIndexOf("❯No,exit");
      return yes > no;
    };
    void (async () => {
      this.store.event("worker_trust_confirm_intent", { worktree: pane.record.worktree, screen }, pane.record);
      const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
      // Claude draws the dialog before it finishes starting and then redraws it with the
      // default choice; act once its output has been quiet for a moment.
      for (const until = Date.now() + 5000; Date.now() - pane.startupOutputAt! < 800 && Date.now() < until;) await sleep(100);
      pane.startupScreen = "";
      // The default choice is "No, exit". Enter goes only while the trust choice is the last one drawn.
      for (let tries = 1; !selected(); tries++) {
        if (tries > 3) throw new Refusal("trust_choice_not_selected");
        await press("\x1b[B");
        await sleep(600);
      }
      await press("\r");
      this.store.event("worker_trust_confirmed", { worktree: pane.record.worktree }, pane.record);
    })().catch(error => this.recordFailure(pane, "worker_trust_failed", error, { screen: pane.startupScreen }));
  }
  // A Claude turn's observed facts: the effort its Stop hook reports, and the model of the
  // turn's last reply in its transcript (the API's answer, not the requested model).
  claudeTurnFacts(pane: Pane, stop: any) {
    pane.effort = typeof stop.effort?.level === "string" && stop.effort.level ? stop.effort.level : "unknown";
    pane.model = "unknown";
    const lines = readFileSync(stop.transcript_path, "utf8").split("\n");
    for (let index = lines.length - 1; index >= 0; index--) {
      if (!lines[index]!.trim()) continue;
      // The last line can still be half written; a line that does not parse is not a fact.
      let entry: any;
      try { entry = JSON.parse(lines[index]!); } catch { continue; }
      if (entry.type === "user" && entry.promptId !== undefined && entry.promptId !== stop.prompt_id) break;
      // "<synthetic>" marks a reply Claude Code wrote itself (an API error or an interruption).
      if (entry.type === "assistant" && typeof entry.message?.model === "string" && entry.message.model !== "<synthetic>") {
        pane.model = entry.message.model; break;
      }
    }
    this.store.event("native_turn_facts", { prompt_id: stop.prompt_id, model: pane.model, effort: pane.effort }, pane.record);
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
    const started = performance.now();
    let operation: ReturnType<typeof exec> | undefined;
    let completed = false, stdout = "", stderr = "";
    try {
      operation = exec("/usr/bin/python3", ["-I", "-S", "-B", processQuery, String(pane.pty.pid)], { timeout: 5000, maxBuffer: 4 * 1024 * 1024, encoding: "utf8" });
      pane.login?.recordChild((operation as any).child.pid, "libproc process observer");
      const captured = await operation;
      completed = true; stdout = captured.stdout; stderr = captured.stderr;
      const observed = JSON.parse(stdout);
      check(observed.schema === 1 && observed.root_pid === pane.pty.pid && observed.method === "macOS libproc" && Array.isArray(observed.rows), "invalid_process_snapshot");
      const rows = observed.rows as {pid:number;ppid:number;pgid:number;tpgid:number;command:string}[];
      const positive = (value: unknown) => Number.isSafeInteger(value) && (value as number) > 0;
      check(rows.length <= 4096 && rows.every(row=>row && positive(row.pid) && Number.isSafeInteger(row.ppid) && row.ppid>=0 && positive(row.pgid) && Number.isSafeInteger(row.tpgid) && row.tpgid>=-1 && typeof row.command === "string" && isAbsolute(row.command) && !row.command.includes("\0")) && new Set(rows.map(row=>row.pid)).size === rows.length, "invalid_process_row");
      const descendants = new Set<number>([pane.pty.pid]);
      for (let changed = true; changed;) {
        changed = false;
        for (const row of rows) if (descendants.has(row.ppid) && !descendants.has(row.pid)) { descendants.add(row.pid); changed = true; }
      }
      const owned = rows.filter((row) => descendants.has(row.pid));
      check(owned.length === rows.length && (!rows.length || rows.some(row=>row.pid===pane.pty.pid)), "invalid_process_tree");
      if (pane.record.role === "shell") return { shell_pid: pane.pty.pid, leader: null,
        native_session: null, session_ended: pane.stopped, observer: { method: observed.method, root_pid: observed.root_pid },
        processes: owned, failed: pane.failed };
      const leaders = owned.filter((row) => row.pid === row.pgid && row.pgid === row.tpgid && row.command === pane.record.executable_path);
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
        observer: { method: observed.method, root_pid: observed.root_pid },
        processes: owned, failed: pane.failed };
    } catch (error) {
      const failure = error as Error & { code?: string | number; signal?: string; killed?: boolean; stdout?: string; stderr?: string };
      const child = (operation as any)?.child;
      Object.assign(failure, { process_query: {
        root_pid: pane.pty.pid, helper_pid: child?.pid ?? null,
        stdout: completed ? stdout : failure.stdout ?? stdout,
        stderr: completed ? stderr : failure.stderr ?? stderr,
        exit_code: child?.exitCode ?? (completed ? 0 : typeof failure.code === "number" ? failure.code : null),
        signal: child?.signalCode ?? failure.signal ?? null, killed: child?.killed ?? failure.killed ?? false,
        error_code: !completed && typeof failure.code === "string" ? failure.code : null,
        elapsed_ms: performance.now() - started,
      } });
      throw failure;
    }
  }

  scan(pane: Pane, final = false) {
    if (pane.stopped) return;
    if (pane.record.role === "shell") return;
    if (pane.record.cli === "Claude Code") return;
    const home = pane.record.env.CODEX_HOME as string;
    const walk = (dir: string): string[] => !existsSync(dir) ? [] : readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
      entry.isDirectory() ? walk(join(dir, entry.name)) : entry.name.endsWith(".jsonl") ? [join(dir, entry.name)] : []);
    const files = final ? [...pane.offsets.keys()].filter((file) => codexSessionFileName(file, pane.native)) :
      pane.nativeFile ? [pane.nativeFile] : walk(join(home, "sessions"));
    if (final) check(pane.native && files.length === 1, "native_bound_log_unavailable", { native_session: pane.native, files });
    for (const file of files) {
      const bytes = readFileSync(file);
      // An isolated home can retain an earlier attempt's rollout. Only logs
      // belonging to this worktree contribute records or native identity.
      const metadataEnd = bytes.indexOf(10);
      if (metadataEnd < 0 && !final) continue;
      const metadata = JSON.parse(bytes.subarray(0, metadataEnd < 0 ? bytes.length : metadataEnd).toString("utf8"));
      if (!final && (metadata.type !== "session_meta" || metadata.payload?.cwd !== pane.attempt.workspace)) continue;
      const rootFile = codexSessionOrigin(file, metadata, metadata.payload?.id, pane.attempt.workspace) === "root";
      let offset = pane.offsets.get(file) ?? 0;
      check(bytes.length >= offset, "native_log_truncated", { file: relative(home, file), offset, bytes: bytes.length });
      let end: number;
      while ((end = bytes.indexOf(10, offset)) >= 0) {
        const raw = bytes.subarray(offset, end).toString("utf8"), event = JSON.parse(raw);
        this.store.event("native_record", { file: relative(home, file), offset, record: event }, pane.record);
        appendFileSync(join(this.root, "traces", pane.record.id, "native.jsonl"), raw + "\n");
        if (event.type === "session_meta" && event.payload.source === "cli" && rootFile) {
          check(!pane.native || pane.native === event.payload.id, "ambiguous_native_session");
          if (!pane.native) this.store.event("pane_native_session", { native_session: event.payload.id,
            resume_argv: resumeArgv(pane.record, event.payload.id) }, pane.record);
          pane.native = event.payload.id;
        }
        // Only the root CLI file contributes identity or model facts.
        if (rootFile && pane.native === metadata.payload.id) {
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
    const result = pane.writes.then(async () => {
      check(!pane.failed && !pane.stopped && !pane.archived && !pane.closing, "pane_unavailable");
      await operation();
    });
    // Return the original rejection to its caller, but release the queue slot.
    // Unknown physical writes persist pane.failed; the next operation checks
    // that state instead of inheriting an unrelated request's rejected Promise.
    pane.writes = result.then(() => undefined, () => undefined);
    return result;
  }
  async beginComposition(launch: string, receipt: Record<string, unknown>, assertCurrent: () => Promise<void>) {
    const pane = this.byLaunch(launch);
    check(!pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
    // Composition has no committed text yet, but already owns the user's draft.
    // An end/cancel does not prove that the CLI input line is empty. Only a user
    // submit or explicit interrupted-queue release clears the draft reservation.
    pane.userDraft = true;
    pane.inputGeneration++;
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
    const control = binary || (!pasted && /[\x00-\x1f\x7f]/.test(data));
    // Reserve synchronously, before the recorder or identity check can yield.
    // Input records and their bytes keep the same order as admission. Esc also
    // prevents the CR of a paste that is already waiting inside this stream.
    pane.pendingInputs++;
    pane.inputGeneration++;
    if (!binary && data === "\x1b") { pane.interrupted = true; pane.state = "busy"; }
    try { await this.serializeWrite(pane, async () => {
      await assertCurrent();
      await record(text, control);
      check(!pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
      if (!binary) pane.userDraft = true;
      this.store.event("terminal_input_write_intent", { ...receipt, encoding,
        ...(binary ? { data_base64: bytes.toString("base64") } : { data }), byte_length: bytes.length }, pane.record);
      const permissionControl = Boolean(!binary && data === "\r" && pane.record.cli === "Claude Code" &&
        pane.permission && pane.active && pane.permission.prompt_id === pane.claudePromptId && pane.permission.submission === pane.active.id);
      if (!binary && !pasted && /[\r\n]/.test(data) && !permissionControl) {
        pane.state = "busy"; pane.userDraft = false;
        pane.permission = null;
        if (pane.record.cli === "Claude Code") pane.claudePromptId = null;
        pane.active = { id: randomUUID(), dispatch: `input:${receipt.request_id}`, at: new Date().toISOString(), nativeTurn: null };
        this.store.event("turn_submit_intent", { ...pane.active, source: "user", request_id: receipt.request_id }, pane.record);
      }
      if (permissionControl) { pane.userDraft = false; pane.permission = null; }
      try {
        pane.pty.write(binary ? bytes : data);
        const written = this.store.event("terminal_input_written", { ...receipt, encoding, byte_length: bytes.length }, pane.record);
        if (permissionControl) this.store.event("permission_control_written", { ...receipt, ...currentTurnBinding(pane), prompt_id: pane.claudePromptId }, pane.record);
        if(!binary && data==="\x1b") { pane.interruption = written; this.retireClaudeSubmission(pane,"user-esc"); }
      } catch (error) {
        this.recordFailure(pane, "terminal_input_write_unknown", error, receipt);
        throw error;
      }
    });
    } finally { pane.pendingInputs--; }
  }
  async dispatch(pane: Pane, text: string, source: DispatchSource = "executor", inbox?: { id: string; sender: string }, context?: { kind: string; rejection_id: string }) {
    check(pane.record.role !== "shell", "agent_pane_required");
    const previous = inbox ? this.store.inboxDispatch(inbox.id) : undefined;
    if (previous) {
      check(previous.launch === pane.record.id && previous.sender === inbox!.sender &&
        previous.text === `⟦主控 #${previous.seq}⟧\n${text}`, "inbox_dispatch_conflict");
      return previous;
    }
    check(!pane.failed && !pane.stopped, "pane_unavailable");
    check(typeof text === "string" && text.trim() && !/[\x00\x1b]/.test(text), "invalid_dispatch_text");
    const item = this.store.register(pane.record.id, text, source, context, inbox, this.parentLaunch.getStore());
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
  async releaseByUser(thread: string, declaration: EmptyInputDeclaration, recordAction: () => Promise<void>, assertCurrent: () => Promise<void>) {
    const pane = this.get(thread);
    check(!pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
    check(declaration?.statement === "用户声明输入框已空" && declaration.launch === pane.record.id &&
      Number.isSafeInteger(declaration.interruption) && Number.isSafeInteger(declaration.input_generation), "empty_input_declaration_required");
    const matches = () => pane.interrupted && pane.interruption === declaration.interruption && pane.inputGeneration === declaration.input_generation;
    check(matches(), "empty_input_declaration_stale");
    const info = await this.processInfo(thread);
    check(info.leader && !info.failed, "foreground_agent_required", info);
    await assertCurrent();
    let refused = false;
    await this.serializeWrite(pane, async () => {
      await assertCurrent();
      check(!pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
      // A stale declaration is an ordinary refusal, not an unknown PTY write.
      // Resolve this write slot so later admitted user bytes keep their order.
      if (!matches()) { refused = true; this.store.event("empty_input_declaration_rejected", { declaration }, pane.record); return; }
      await recordAction();
      await assertCurrent();
      if (!matches()) { refused = true; this.store.event("empty_input_declaration_rejected", { declaration }, pane.record); return; }
      this.store.event("user_queue_release", { declaration, previous_state: pane.state, previous_submission: pane.active?.id ?? null }, pane.record);
      pane.active = null; pane.claudePromptId = null; pane.userDraft = false; pane.interrupted = false; pane.interruption = null; pane.state = "idle";
    });
    check(!refused, "empty_input_declaration_stale");
    await this.drain(pane);
    return this.status(thread);
  }
  interruptThread = async (thread: string) => {
    const pane = this.get(thread);
    check(!pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
    const info = await this.processInfo(thread);
    check(info.leader && !info.failed, "foreground_agent_required", info);
    pane.interrupted = true; pane.state = "busy";
    pane.inputGeneration++;
    await this.serializeWrite(pane, async () => {
      const current = await this.processInfo(thread);
      check(current.leader === info.leader && !current.failed, "identity_conflict", current);
      this.store.event("pane_interrupt_intent", { source: "gate", leader: info.leader }, pane.record);
      try {
        pane.pty.write("\x1b");
        pane.interruption = this.store.event("pane_interrupt_written", { source: "gate", leader: info.leader }, pane.record);
        this.retireClaudeSubmission(pane,"gate-interrupt");
      } catch (error) { this.recordFailure(pane, "pane_interrupt_unknown", error); throw error; }
    });
  };
  retireClaudeSubmission(pane: Pane, reason: string) {
    if(pane.record.cli!=="Claude Code" || !pane.active)return;
    this.store.event("claude_submission_retired",{reason,submission:pane.active.id,dispatch:pane.active.dispatch,prompt_id:pane.claudePromptId},pane.record);
    pane.active=null;pane.claudePromptId=null;
  }
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
    const keys:Record<string,string>={ArrowUp:"\x1b[A",ArrowDown:"\x1b[B",Enter:"\r"};
    check((purpose==="onboarding-theme" && ["ArrowUp","ArrowDown","Enter"].includes(key)) || (purpose==="workspace-trust" && ["ArrowDown","Enter"].includes(key)) || (purpose==="onboarding-notice" && key==="Enter"),"invalid_screen_key");
    check(typeof screen_id==="string" && screen_id.length>0 && screen_id.length<=128 && typeof authorization_ref==="string" && authorization_ref.trim() && typeof selected_label==="string" && selected_label.trim(),"invalid_screen_approval");
    const history=()=>this.store.read().filter(e=>e.launch===pane.record.id && e.type==="controller_screen_key_intent");
    const assertUnused=()=>{
      const past=history();
      check(!past.some(e=>e.data.screen_id===screen_id || e.data.screen_base64===screen_base64),"screen_key_already_used");
      if(purpose==="workspace-trust"){
        check(!past.some(e=>e.data.purpose==="workspace-trust" && e.data.key==="Enter"),"workspace_trust_already_used");
        check(selected_label==="Yes, I trust this folder","trust_selection_not_explicit");
        if(key==="Enter"){
          const previous=past.at(-1)?.data;
          check(previous?.purpose==="workspace-trust" && previous.key==="ArrowDown" && previous.selected_label==="Yes, I trust this folder","trust_selection_not_explicit");
        }
      }
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
    const assertStartup=()=>check(pane.state==="unknown" && !pane.active && !pane.failed && !pane.stopped && !pane.archived && !pane.writing && !pane.userDraft && !pane.pendingInputs,"screen_requires_startup");
    assertStartup();assertUnused();
    await this.serializeWrite(pane,async()=>{
      assertStartup();assertUnused();
      const info=await this.processInfo(thread);check(info.leader && !info.failed,"foreground_claude_required");assertStartup();
      const observed=this.output(pane.record.id,0);
      check(observed.next_offset===observed.total_bytes && observed.data_base64===screen_base64 && screen_base64.length>0,"screen_changed");
      if(purpose==="workspace-trust" && key==="Enter"){
        const before=Buffer.from(history().at(-1)!.data.screen_base64,"base64"),raw=Buffer.from(screen_base64,"base64");
        check(raw.length>before.length && raw.subarray(0,before.length).equals(before),"trust_screen_not_continued");
      }
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
    const record = this.store.threadLaunch(thread);
    const restore = record && this.store.lastEvent(record.id, ["pane_restore_pending", "pane_restored", "pane_restore_failed"]);
    const restoration = !restore ? null : { status: restore.type === "pane_restored" ? "restored" :
      restore.type === "pane_restore_failed" ? "failed" : "pending", error: restore.data.error ?? null, details: restore.data.details ?? null };
    const pane = this.panes.get(thread);
    if (pane) {
      return { thread, launch: pane.record.id, state: pane.failed || pane.stopped ? "unknown" : pane.state,
        lifecycle: pane.archived || pane.record.role === "shell" && pane.stopped ? "ended" : pane.stopped ? "interrupted" : "running", shell_pid: pane.pty.pid,
        state_source: pane.failed ? "runtime_failure" : "host_events", active: pane.active, native_session: pane.native,
        turn: pane.turn, writing: pane.writing, user_draft: pane.userDraft, interrupted: pane.interrupted,
        input_generation: pane.inputGeneration, interruption: pane.interruption,
        queued: pane.queue.map((item) => item.id), failed: pane.failed, stopped: pane.stopped, restoration };
    }
    check(record, "unknown_pane");
    if (record.role === "shell") {
      const closed = this.store.lastEvent(record.id, ["shell_closed"]);
      return { thread, launch: record.id, state: "unknown", lifecycle: closed ? "ended" : "unknown",
        shell_pid: null, state_source: "shell_history", active: null, native_session: null, turn: null,
        writing: false, queued: [], failed: closed ? null : "shell_exit_unconfirmed", stopped: Boolean(closed),
        historical: true, restoration: null };
    }
    const archived = this.store.lastEvent(record.id, ["pane_archived"]);
    const recovered = this.store.lastEvent(record.id, ["pane_recovered"]);
    return { thread, launch: record.id, state: "unknown", lifecycle: record.execution_state === "prepared" ? "not_started" : archived ? "ended" : recovered?.data.lifecycle ?? "unknown",
      shell_pid: recovered?.data.shell_pid ?? null, state_source: record.execution_state === "prepared" ? "launch_prepared" : archived ? "pane_archived" : recovered ? "pane_recovered" : "launch_record",
      active: null, native_session: null, turn: null, writing: false, queued: [], failed: restoration?.error ?? null, restoration,
      stopped: archived ? true : recovered?.data.exit_event ? true : null, historical: true };
  }
  async signal(launch: string, raw: string, received_at: string,
    transfer?: (pane: Pane, stop: any, matched: boolean) => Promise<void>) {
    const pane = this.byLaunch(launch);
    this.store.event("hook_received", { raw_stdin: raw, received_at }, pane.record);
    let value: any;
    let binding = currentTurnBinding(pane);
    const fact = () => {
      const pending = binding && this.questions(launch).filter(q => q.session_id === binding.session_id &&
        q.submission === binding.submission && ['waiting', 'sending'].includes(q.status));
      const question = pending?.find(q => q.tool_use_id === value?.tool_use_id) ?? (pending?.length === 1 ? pending[0] : null);
      return { ...binding, question: question?.id ?? null };
    };
    let excluded = false;
    try {
      value = JSON.parse(raw);
      check(value && typeof value === 'object' && !Array.isArray(value), 'hook_object_required');
      excluded = noncurrentHook(pane, value, received_at);
      // Keep unmatched Stop semantics. All other noncurrent hooks are refused
      // before common-field validation and cannot poison the current launch.
      if (excluded) {
        check(value.session_id === pane.native || !value.session_id, 'hook_native_session_mismatch');
        if (value.hook_event_name === 'Stop') { this.store.event('stop_not_matched', value, pane.record); return; }
        throw new Refusal('hook_origin_or_turn_mismatch');
      }
      check(Number.isFinite(Date.parse(received_at)), 'hook_received_at_required');
      // A Claude worker's session start is its ready signal: release the first task to it.
      if (pane.record.cli === "Claude Code" && pane.record.role !== "controller" && value.hook_event_name === "SessionStart") {
        check(value.session_id === pane.native && value.cwd === pane.record.worktree && value.source === "startup", "session_start_mismatch");
        check(pane.state === "unknown" && !pane.active && !pane.failed, "initial_release_only");
        pane.started = true;
        this.store.event("native_session_started", { native_session: value.session_id, trust_confirmed: Boolean(pane.trustAnswered) }, pane.record);
        // The daemon drains the pane after every accepted signal, so the queued task goes next.
        pane.state = "idle";
        return;
      }
      this.scan(pane);
      binding = currentTurnBinding(pane);
      validateHookEnvelope(pane, value);
      if (['PreToolUse', 'PostToolUse', 'PostToolUseFailure'].includes(value.hook_event_name)) {
        check(binding?.turn, 'question_turn_mismatch');
        const question = questionFromHook(pane, value, { ...binding, turn: binding.turn });
        if (!question) return;
        const previous = this.questions(launch).find(q => q.id === question.id);
        if (value.hook_event_name === 'PreToolUse') {
          check(!previous, 'question_hook_reused');
          this.store.event('native_question_opened', question, pane.record);
        } else {
          check(previous && previous.submission === question.submission && previous.turn === question.turn &&
            ['waiting', 'sending'].includes(previous.status), 'question_not_pending');
          const response = typeof value.tool_response === 'string' ? JSON.parse(value.tool_response) : value.tool_response;
          const answered = value.hook_event_name === 'PostToolUse' && previous.blocking && previous.questions.every(q =>
            previous.cli === 'claude' ? typeof response?.answers?.[q.question] === 'string' :
              Array.isArray(response?.answers?.[q.id!]?.answers) && response.answers[q.id!].answers.length > 0);
          check(answered || value.hook_event_name === 'PostToolUseFailure', 'question_response_unverified');
          const status = answered ? 'answered' : 'cancelled';
          this.store.event('native_question_resolved', { ...binding, question: question.id, status, response: value.tool_response ?? null }, pane.record);
        }
        return;
      }
      if (pane.record.cli === "Claude Code") {
        // 08e recorded prompt_id on UPS and Stop; it identifies the actual CLI prompt.
        check(Number.isInteger(pane.record.turn_limit) && pane.record.turn_limit >= 1 && pane.record.turn_limit <= 6, "claude_turn_correlation_unverified");
        if (value.hook_event_name === "PermissionRequest") {
          check(pane.active && pane.claudePromptId && value.prompt_id === pane.claudePromptId, "permission_prompt_mismatch");
          const question = questionPermission(pane, value, this.questions(launch));
          // Native Enter still belongs to this root interaction. The same
          // question's permission event does not create a permission wait.
          pane.permission = { prompt_id: value.prompt_id, submission: pane.active.id };
          if (question) {
            this.store.event('native_question_permission', { ...binding, question: question.id }, pane.record);
            return;
          }
          this.store.event("permission_wait", { ...value, ...fact() }, pane.record); pane.state = "busy"; return;
        }
        if (value.hook_event_name === "UserPromptSubmit") {
          const item = pane.active && this.store.dispatchRecord(pane.active.dispatch);
          check(typeof value.prompt_id==="string" && value.prompt_id.length>0 && value.prompt_id.length<=128,"claude_prompt_id_required");
          check(pane.claudePromptIds && !pane.claudePromptIds.has(value.prompt_id),"claude_prompt_id_reused");
          if (item && value.prompt !== item.text) {
            const reason = "登记注入与实际提交正文不一致；已阻断，请处理草稿后再决定。";
            this.store.event("injected_prompt_blocked", { prompt: value.prompt, prompt_id: value.prompt_id,
              dispatch: item.id, submission: pane.active!.id, expected_prompt: item.text, reason }, pane.record);
            this.store.event('native_question_unverified', { ...fact(), reason: 'injected_prompt_blocked', hook_event_name: value.hook_event_name }, pane.record);
            pane.state = "busy";
            return { decision: "block" as const, reason };
          }
          // Source comes from the current structured submission, never text markers.
          // Hand-typed submissions and retired injections cannot trigger this guard.
          if (!item) { this.store.event("user_prompt_unregistered", value, pane.record); if (!pane.active) return; }
          check(pane.state === "busy" && !pane.claudePromptId, "claude_submission_unmatched");
          pane.permission = null;
          pane.claudePromptIds.add(value.prompt_id);pane.claudePromptId=value.prompt_id;this.store.event("turn_start_signal", value, pane.record); return;
        }
        check(value.hook_event_name === "Stop", "unsupported_hook");
        this.store.event("turn_end_signal", value, pane.record);
        const active = pane.active;
        const current = Boolean(active && pane.claudePromptId && value.prompt_id===pane.claudePromptId && !pane.failed && !pane.stopInProgress &&
          !value.agent_id && Date.parse(received_at) >= Date.parse(active.at));
        if (current && typeof value.stop_hook_active !== 'boolean') {
          const error = new Refusal('stop_hook_active_required');
          throw error;
        }
        const matched = current && value.stop_hook_active === false;
        if (!matched) { this.store.event("stop_not_matched", value, pane.record); return; }
        check(currentTurnTrust(pane, this.store.read().filter(e => e.launch === launch)) === 'verified', 'current_turn_untrusted');
        if (pane.record.role !== "controller") this.claudeTurnFacts(pane, value);
        pane.stopInProgress = true;
        try {
          if (transfer) await transfer(pane, value, true);
          check(currentTurnTrust(pane, this.store.read().filter(e => e.launch === launch)) === 'verified', 'current_turn_untrusted');
          if(pane.active!==active || pane.claudePromptId!==value.prompt_id){this.store.event("stop_not_matched",{...value,stage:"after_transfer"},pane.record);return;}
          pane.active = null; pane.claudePromptId = null; pane.permission = null; pane.state = pane.interrupted ? "busy" : "idle";
          this.store.event(pane.state === "idle" ? "pane_idle" : "pane_completion_held", { submission: active!.id, stop: value }, pane.record);
        } catch (error) {
          this.recordFailure(pane, "stop_transfer_failed", error); throw error;
        } finally { pane.stopInProgress = false; }
        return;
      }
      if (value.hook_event_name === "PermissionRequest") {
        pane.failed = "unexpected_permission_request"; pane.state = "unknown";
        this.store.event("permission_wait", { ...value, ...fact() }, pane.record);
        return;
      }
      if (value.hook_event_name === "UserPromptSubmit") { this.store.event("turn_start_signal", value, pane.record); return; }
      check(value.hook_event_name === "Stop", "unsupported_hook");
      this.store.event("turn_end_signal", value, pane.record);
      const active = pane.active;
      const matched = Boolean(!pane.failed && !pane.stopInProgress && active?.nativeTurn && value.turn_id === active.nativeTurn && Date.parse(received_at) >= Date.parse(active.at));
      // The Stop handler transfers explicit files while the submitted turn still
      // owns its gate caller identity. A Stop alone never performs a gate command.
      if (active) check(currentTurnTrust(pane, this.store.read().filter(e => e.launch === launch)) === 'verified', 'current_turn_untrusted');
      if (matched) pane.stopInProgress = true;
      try {
        if (transfer) await transfer(pane, value, matched);
        if (!matched) { this.store.event("stop_not_matched", value, pane.record); return; }
        check(currentTurnTrust(pane, this.store.read().filter(e => e.launch === launch)) === 'verified', 'current_turn_untrusted');
        pane.active = null; pane.state = pane.failed ? "unknown" : pane.interrupted ? "busy" : "idle";
        this.store.event(pane.state === "idle" ? "pane_idle" : "pane_completion_held", { submission: active!.id, state: pane.state, stop: value }, pane.record);
      } catch (error) {
        if (matched) this.recordFailure(pane, "stop_transfer_failed", error);
        throw error;
      } finally { if (matched) pane.stopInProgress = false; }
    } catch (error) {
      if (!excluded && binding) this.store.event('native_question_unverified', {
        reason: String(error), hook_event_name: value?.hook_event_name, tool_use_id: value?.tool_use_id, ...fact(),
      }, pane.record);
      throw error;
    }
  }
  authenticate(identity: any) {
    const pane = this.byLaunch(identity.launch);
    check(pane.record.role !== "shell", "agent_pane_required");
    check(identity.token === pane.token, "invalid_launch_identity");
    return pane;
  }
  // A terminal identity is the terminal itself, alive in this daemon process.
  authenticateTerminal(identity: any) {
    const pane = typeof identity.launch === "string" ? this.panes.get(this.store.launchRecord(identity.launch)?.thread) : undefined;
    check(pane && pane.record.role === "shell" && pane.record.id === identity.launch && typeof identity.token === "string" &&
      identity.token.length === pane.token.length && identity.token === pane.token, "invalid_terminal_identity");
    return pane!;
  }
  terminalAlive(launch: string) {
    const pane = this.panes.get(this.store.launchRecord(launch)?.thread);
    return Boolean(pane && pane.record.role === "shell" && !pane.stopped && !pane.closing && !pane.archived);
  }
  questions(launch: string) {
    return projectQuestions(this.store.read().filter(event => event.launch === launch));
  }
  async answerQuestion(launch: string, id: string, answers: string[],
    record: (text: string, question: string) => Promise<void>, assertCurrent: () => Promise<void>) {
    const pane = this.byLaunch(launch);
    const trusted = () => currentTurnTrust(pane, this.store.read().filter(e => e.launch === launch)) === 'verified';
    check(trusted(), 'current_turn_untrusted');
    const question = this.questions(launch).find(q => q.id === id);
    check(question && question.status === 'waiting', 'question_not_pending');
    const keys = nativeAnswerKeys(question, answers);
    let confirmed = false;
    await this.serializeWrite(pane, async () => {
      await assertCurrent();
      const current = this.questions(launch).find(q => q.id === id);
      check(trusted() && current?.status === 'waiting' && !pane.failed && !pane.stopped && !pane.archived && !pane.interrupted &&
        pane.active?.id === question.submission && pane.native === question.session_id &&
        (question.cli === 'claude' ? pane.claudePromptId === question.turn : pane.turn === question.turn) &&
        pane.inputGeneration === question.input_generation && !pane.userDraft,
        'question_input_changed');
      await record(question.questions.map((q, i) => `问题 ${i + 1}：${q.question}\n用户答复：${answers[i]}`).join('\n'), id);
      check(trusted(), 'current_turn_untrusted');
      const intent = this.store.event('native_question_answer_intent', { question: id, answers }, pane.record);
      let keysWritten = 0;
      const checkpoint = async () => {
        await assertCurrent();
        const events = this.store.read().filter(event => event.launch === launch);
        const current = projectQuestions(events).find(q => q.id === id);
        check(currentTurnTrust({ native: question.session_id, active: { id: question.submission } }, events) === 'verified' &&
          !pane.failed && !pane.stopped && !pane.archived && !pane.interrupted && pane.native === question.session_id &&
          pane.inputGeneration === question.input_generation && !pane.userDraft, 'question_input_changed');
        const sameTurn = pane.active?.id === question.submission &&
          (question.cli === 'claude' ? pane.claudePromptId === question.turn : pane.turn === question.turn);
        if (current?.status === 'answered' && questionAnswerConfirmed(question, answers, events, intent)) {
          const completed = !pane.active && events.some(event => event.type === 'pane_idle' &&
            event.data.submission === question.submission && event.data.stop?.session_id === question.session_id &&
            (question.cli === 'claude' ? event.data.stop.prompt_id === question.turn : event.data.stop.turn_id === question.turn));
          check(sameTurn || completed, 'question_input_changed');
          confirmed = true;
          return true;
        }
        check(current?.status === 'sending' && sameTurn, 'question_input_changed');
        return false;
      };
      for (const key of keys) {
        if (await checkpoint()) break;
        try {
          pane.pty.write(key);
          keysWritten++;
          this.store.event('native_question_answer_key_written', { question: id, key }, pane.record);
        } catch (error) { this.recordFailure(pane, 'question_answer_write_unknown', error, { question: id }); throw error; }
        // Interactive selection/review transitions consume distinct key events.
        await new Promise(resolve => setTimeout(resolve, 75));
      }
      if (!confirmed) await checkpoint();
      this.store.event('native_question_answer_written', { question: id, confirmed, keys_written: keysWritten }, pane.record);
    });
    return { confirmed };
  }

  controllerLaunch = (thread: string) => {
    const pane = this.panes.get(thread);
    if (!pane || pane.record.role !== "controller" || pane.record.cli !== "Claude Code" || pane.stopped || pane.archived || pane.failed) return;
    return { id: pane.record.id, thread, task: pane.record.task, project: pane.record.project,
      preset: pane.record.preset as "ideation" | "executor", session: pane.record.session, spec_rev: pane.record.spec_rev };
  };
  async caller(identity: any): Promise<SubmitCaller> {
    const pane = this.authenticate(identity);
    if (pane.record.role === "controller") {
      const stored = this.store.launchRecord(pane.record.id);
      check(stored && stored.role === "controller" && stored.cli === "Claude Code" && ["ideation", "executor"].includes(stored.preset), "controller_launch_required");
      const fields = ["id", "thread", "task", "project", "preset", "session", "spec_rev"];
      const prompt = identity.prompt_id, submission = pane.active?.id;
      const assertBinding = () => {
        const taskRow = this.store.db.prepare("SELECT data FROM tasks WHERE id=?").get(stored.task);
        const currentTask = taskRow && JSON.parse(String(taskRow.data));
        check(currentTask?.task_id === stored.task && currentTask?.project_id === stored.project &&
          currentTask?.spec_rev === stored.spec_rev, "stale_controller_launch");
        check(fields.every(field => pane.record[field] === stored[field]), "controller_launch_identity_changed");
        check(pane.record.cli === "Claude Code" && pane.record.role === "controller" &&
          pane.native === stored.session && identity.native_session === stored.session &&
          prompt && pane.claudePromptId === prompt && pane.active?.id === submission && submission &&
          pane.stopInProgress && pane.state === "busy" && !pane.failed && !pane.stopped && !pane.archived && !pane.interrupted,
          "controller_not_active");
      };
      assertBinding();
      const first = await this.processInfo(stored.thread); assertBinding();
      check(first.leader && !first.failed && first.native_session === stored.session && first.shell_pid === pane.pty.pid, "native_identity_required");
      return { thread: stored.thread, turn: prompt, address: stored.preset, project: stored.project,
        assertActive: async () => {
          assertBinding();
          const live = await this.processInfo(stored.thread); assertBinding();
          check(live.leader === first.leader && !live.failed && live.native_session === stored.session && live.shell_pid === pane.pty.pid,
            "controller_native_identity_changed");
        } };
    }
    check(pane.attempt, "worker_attempt_required");
    const attempt = pane.attempt;
    if (pane.record.cli === "Claude Code") {
      // Claude's turn is the prompt the daemon submitted; its session id is fixed at launch.
      const turn = identity.prompt_id;
      check(turn && pane.claudePromptId === turn && pane.native === identity.native_session, "native_identity_required");
      return { thread: attempt.thread_id, turn, address: `${pane.record.role}:${attempt.thread_id}`,
        assertActive: async () => {
          const info = await this.processInfo(attempt.thread_id);
          check(info.leader && !info.failed && pane.state === "busy" && pane.claudePromptId === turn, "worker_not_active");
        } };
    }
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
    return { workspace: pane.attempt.workspace, provider: pane.record.cli === "Claude Code" ? "claude" : "codex",
      turn: pane.record.cli === "Claude Code" ? pane.claudePromptId ?? null : pane.turn,
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
    this.forgetOpen(pane.record.id);
    this.store.event("pane_archived", {}, pane.record); pane.archived = true;
  };
  async terminate(pane: Pane, reason: string) {
    if (pane.record.role === "shell") {
      pane.closing = true;
      await Promise.allSettled([pane.writes]);
      if (!pane.stopped) pane.shellChildren = (await this.processInfo(pane.record.thread)).processes.map(row => row.pid);
    }
    if (pane.stopped) {
      await pane.loginCleanup;
      if (pane.record.role === "shell") await this.confirmShellExit(pane);
      return;
    }
    this.store.event("pane_stop_intent", { reason, shell_pid: pane.pty.pid }, pane.record);
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(() => reject(new Refusal("pane_stop_unconfirmed")), 5000);
      pane.pty.onExit(() => { clearTimeout(timer); resolve(); });
      pane.pty.kill("SIGHUP");
    });
    await pane.loginCleanup;
    if (pane.record.role === "shell") await this.confirmShellExit(pane);
  }
  async confirmShellExit(pane: Pane) {
    const pids = pane.shellChildren ?? [pane.pty.pid];
    const deadline = Date.now() + 5000;
    let alive: number[];
    do {
      const observations = await Promise.all(pids.map(async pid => {
        const result = await exec("/usr/bin/python3", ["-I", "-S", "-B", processQuery, String(pid)], { timeout: 5000 });
        const snapshot = JSON.parse(result.stdout);
        check(snapshot.root_pid === pid && Array.isArray(snapshot.rows), "invalid_process_snapshot");
        return snapshot.rows.length ? pid : null;
      }));
      alive = observations.filter((pid): pid is number => pid !== null);
      if (!alive.length) {
        this.store.event("shell_exit_confirmed", { role: "shell", pids }, pane.record);
        return;
      }
      await new Promise(resolve => setTimeout(resolve, 50));
    } while (Date.now() < deadline);
    pane.failed = "shell_children_alive";
    this.store.event("shell_exit_unconfirmed", { role: "shell", pids: alive }, pane.record);
    throw new Refusal("shell_children_alive", { pids: alive });
  }
  async shutdown() { for (const pane of this.panes.values()) await this.terminate(pane, "daemon_shutdown_interruption"); }
}
