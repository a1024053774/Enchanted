import { accessSync, appendFileSync, closeSync, constants, existsSync, fstatSync, mkdirSync, mkdtempSync, openSync, readFileSync, readSync, readdirSync, realpathSync, statSync } from "node:fs";
import { basename, dirname, isAbsolute, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { randomBytes, randomUUID } from "node:crypto";
import { performance } from "node:perf_hooks";
import { AsyncLocalStorage } from "node:async_hooks";
import { validateHookEnvelope, questionFromHook, questionPermission, questionAnswerConfirmed, projectQuestions, nativeAnswerKeys, currentTurnBinding, noncurrentHook, currentTurnTrust } from './questions.ts';
import type { A2AAttachment, A2AAttempt, A2ATask, A2AReview, A2ARepair } from "./contracts/a2aGates.ts";
import { Refusal, treeWritable, type GateRuntime, type SubmitCaller } from "./gates/core.ts";
import { OrchestrationStore, type DispatchSource } from "./store.ts";
import type { A2AInboxEntry } from "./contracts/a2aInbox.ts";
import { claudeLaunch, type ClaudeLaunchInput } from "./claudeLaunch.ts";
import { ClaudeLogin } from "./claudeLogin.ts";
import { noticeText, SECURITY_NOTICE_TEXT } from "./claudeNotice.ts";
import { resumeArgv, nativeSessionFile, codexSessionOrigin, codexSessionFileName } from "./paneRecovery.ts";
import type { ExecutionOverrides } from './executionSettings.ts';
import { cliProgram, terminalClis, readOsc7501, type CliTurn } from './terminalClis.ts';
import { cliProvider } from './gates/taskCards.ts';

const exec = promisify(execFile);
const require = createRequire(import.meta.url);
const cli = fileURLToPath(new URL("./gates/cli.ts", import.meta.url));
const processQuery = fileURLToPath(new URL("./processSnapshot.py", import.meta.url));
const processArgs = fileURLToPath(new URL("./processArgs.py", import.meta.url));
// T-120: ordinary terminals start zsh through Enchanted's ZDOTDIR bootstrap, which
// loads the user's own startup files and then puts the a2a command and CLI shims first.
const terminalResources = fileURLToPath(new URL("../terminal/", import.meta.url));
const terminalCli = fileURLToPath(new URL("./terminalCli.ts", import.meta.url));
const quote = (value: string) => "'" + value.replaceAll("'", "'\\''") + "'";
const shellCommand = (argv: string[]) => argv.map(quote).join(" ");
function check(value: unknown, error: string, details?: unknown): asserts value {
  if (!value) throw new Refusal(error, details);
}
const MANAGED_SHELL_TAIL = "; a2a_cli_status=$?; if (( a2a_cli_status != 0 )); then exit $a2a_cli_status; fi; exec /bin/zsh -f -i";
// The attempt-shaped binding a monitor pane carries (createAttachedThread); its workspace is its own directory.
function monitorAttempt(record: Record<string, any>, task: A2ATask) {
  return { task_id: task.task_id, attempt_id: null, session_id: record.thread, fence: 0, spec_rev: task.spec_rev,
    thread_id: record.thread, runtime_mode: "workspace-write", turn_id: null, workspace: realpathSync(record.worktree), base_commit: null,
    runtime_identity: null } as unknown as A2AAttempt;
}
function requireNotNormalLogin(record: Record<string, any>) {
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
}
// A monitor this daemon started (createPane): read-only, started by a terminal controller, its shell in the managed form.
function requireMonitorRestore(record: Record<string, any>) {
  requireNotNormalLogin(record);
  const shell = record.shell_argv;
  check(record.role === "monitor" && ["Claude Code", "Codex"].includes(record.cli) &&
    record.sandbox === (record.extra_directories?.length ? "workspace-write" : "read-only") &&
    typeof record.parent_launch === "string" && record.shell === "/bin/zsh" && Array.isArray(shell) && shell.length === 4 &&
    shell[0] === "-f" && shell[1] === "-i" && shell[2] === "-c" && typeof shell[3] === "string", "restore_record_unrecognized");
}
function requireFakeControllerRestore(record: Record<string, any>) {
  requireNotNormalLogin(record);
  const env = record.env && typeof record.env === "object" && !Array.isArray(record.env) ? record.env : {};
  const shell = record.shell_argv;
  const command = Array.isArray(shell) ? shell[3] : undefined;
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
  // T-187: the user's own agy and opencode, found as their terminal finds them.
  agy_bin?: string; opencode_bin?: string;
  // The reviewer role card. A reviewer runs on the worker's CLI (D24) in the same home.
  reviewer_role_card?: string; reviewer_role_card_revision?: string;
  // The role card of a read-only monitor a controller attaches to a task (T-124).
  monitor_role_card?: string; monitor_role_card_revision?: string;
  role_card?: string;
  role_card_revision?: string;
  code_revision?: string;
  source_snapshot?: string;
  hook_authorization?: string;
  turn_limit?: number;
  turn_authorization?: string;
}
export type EmptyInputDeclaration = {
  statement: "用户声明输入框已空"; launch: string; window_id: string;
  interruption: number; input_generation: number;
};
// Claude Code worker and reviewer launch (T-122, evidence/2026-10-21-batch19/T-122/probe-01..05):
// never asks for approval, file tools write only where `writable` allows, shell commands run in
// Claude's sandbox, and no settings file is loaded (`--setting-sources ""`: with `local`, a linked
// worktree also loads the main checkout's .claude/settings.local.json, probe-04). User-scope MCP
// is supplied separately with --mcp-config (T-141); its services run outside the Bash sandbox.
// A worker writes its worktree and the request directory. In a linked worktree Claude's sandbox
// itself makes the repository's whole .git writable (probe-04); `gitDenied` takes back the whole
// Git common dir, and only a standalone `git add` or `git commit`
// runs outside the sandbox, as Codex's two prefix rules allow (user ruling 2026-10-21). Claude
// keeps any compound command, `git -c`, env prefix or redirect inside the sandbox, and neither
// `cd` nor `export` carries over to the next command (probe-05). A reviewer writes only its
// one-off candidate copy (its working directory). Both can still write Claude's $TMPDIR: denying
// it breaks every shell command (probe-04).
async function claudeArgv(executable: string, signal: string, session: string,
  selection: { model: string; effort: string; fast: boolean }, writable: string[], shellWritable: string[], gitDenied: string[] = [], extraDirectories: string[] = [], mcpConfig: string | null = null) {
  const hook = [{ hooks: [{ type: "command", command: signal, timeout: 10 }] }];
  // MCP server wildcards are invalid in permissions.allow. The native hook matcher supports
  // this prefix and approves MCP only; Bash and native file tools retain their own checks.
  const mcpPermission = { matcher: "^mcp__", hooks: [{ type: "command", timeout: 10,
    command: "printf '%s\\n' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"allow\"}}'" }] };
  const settings = {
    permissions: { allow: ["Bash", "Read", "Glob", "Grep", ...writable.map(path => `Edit(/${path}/**)`)] },
    sandbox: { enabled: true, autoAllowBashIfSandboxed: true, allowUnsandboxedCommands: false,
      ...(gitDenied.length ? { excludedCommands: ["git add *", "git commit *"] } : {}),
      network: { allowedDomains: ["*"], allowAllUnixSockets: true, allowLocalBinding: true },
      filesystem: { allowWrite: shellWritable, ...(gitDenied.length ? { denyWrite: gitDenied } : {}) } },
    hooks: Object.fromEntries(["SessionStart", "SessionEnd", "UserPromptSubmit", "Stop", "PermissionRequest", "PreToolUse", "PostToolUse"].map(event =>
      [event, event === "PreToolUse" ? [...hook, mcpPermission] : hook])),
    fastMode: selection.fast,
  };
  // dontAsk denies AskUserQuestion anyway; without the tool the model asks through `issue` (T-124 ruling 1a).
  return [executable, "--session-id", session, "--model", selection.model, "--effort", selection.effort, "--permission-mode", "dontAsk",
    "--setting-sources", "", "--disallowedTools", "AskUserQuestion", "--settings", JSON.stringify(settings),
    ...(mcpConfig ? ["--mcp-config", mcpConfig] : []),
    ...extraDirectories.flatMap(path => ["--add-dir", path])];
}
const STARTUP_DEADLINE_MS = 120_000;
// A submitted prompt starts its native turn within a second when the CLI takes it (T-164: 0.1 s).
const TURN_START_DEADLINE_MS = 20_000;
// A CLI started in a project terminal draws its screen within a couple of seconds; one that has written nothing for
// this long may be waiting on a macOS privacy prompt hidden behind other windows (T-174, L01).
const SILENT_FOREGROUND_MS = 6_000;
const WIRING_CHECK_DELAY_MS = 1_500, WIRING_RECHECK_MS = 5_000;
// The text a Claude prompt submitted. A long paste reaches UserPromptSubmit wrapped in Claude's
// own pasted_content markers (seen with the user's login, T-122 GUI round 01); anything else
// is compared as it is.
export function claudeSubmittedText(prompt: unknown) {
  const wrapped = typeof prompt === "string" ? /^\n\n<pasted_content id="([0-9A-Za-z]+)">\n([\s\S]*)\n<\/pasted_content id="\1">\n$/.exec(prompt) : null;
  return wrapped ? wrapped[2] : prompt;
}
// Codex hands the user's answers to request_user_input_async back as a submitted prompt (T-133 probe-05): a JSON list of
// { question, answer, questionItemId: '["request_user_input_async","<call id>",<index>]' } inside this wrapper.
// Anything else, an unreadable wrapper included, is not a reply: it is kept as the prompt it is, word for word.
export function codexQuestionReply(prompt: string): { call: string; text: string } | null {
  const wrapped = /^<send_user_message_question_reply>\n([\s\S]*)\n<\/send_user_message_question_reply>$/.exec(prompt);
  if (!wrapped) return null;
  try {
    const replies = JSON.parse(wrapped[1]);
    if (!Array.isArray(replies) || !replies.length) return null;
    const [tool, call] = JSON.parse(replies[0].questionItemId);
    if (tool !== "request_user_input_async" || typeof call !== "string" || !call) return null;
    return { call, text: replies.map(reply => `${reply.question}：${reply.answer}`).join("\n") };
  } catch { return null; }
}
// The Git paths a Claude worker's sandboxed shell must not write (see claudeArgv).
async function workerGitDenied(worktree: string) {
  // Claude's sandbox already refuses writes to the worktree's own .git file (T-122 e2e red and
  // mutant runs 07), so only the common dir is listed.
  const common = (await exec("git", ["-C", worktree, "rev-parse", "--path-format=absolute", "--git-common-dir"])).stdout.trim();
  return [realpathSync(common)];
}
export type WorkerDeliveryStatus = {
  task: string; attempt: string; session: string; fence: number; spec_rev: number; commit: string; request_id: string;
  received_at: string; result_at: string | null; state: 'processing' | 'submitted' | 'rejected' | 'unknown'; reason: string | null;
  request_turn: string | null; current_turn: string | null; native_turn_changed: boolean; recovery_request_id: string;
};
// T-187: a managed agy or opencode session has no native session id the backend can check (agy reports none); the
// backend names it after its launch.
const reportedSession = (launch: string) => `osc7501:${launch}`;
// An agy or opencode reviewer writes its result to this file: opencode's reports carry no last reply.
export const REVIEW_RESULT_FILE = "review-result.json";
function reviewResult(pane: { record: Record<string, any> }) {
  const file = join(pane.record.request_dir, REVIEW_RESULT_FILE);
  return existsSync(file) ? readFileSync(file, "utf8") : "";
}
type Pane = {
  record: Record<string, any> & { id: string; task: string | null; attempt: string | null };
  token: string; task: A2ATask | null; attempt: A2AAttempt | null; pty: any;
  state: "unknown" | "idle" | "busy"; stopped: boolean; archived: boolean;
  // restored: resumed by this daemon after a restart (T-096, T-124).
  restored?: boolean;
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
  // Project terminal (T-174): when it last wrote output, whether input since then still needs a silence check, and the
  // foreground program that has written nothing since it started.
  outputAt?: number; silenceCheck?: boolean; silenceBusy?: boolean; silentForeground?: { command: string; since: string } | null;
  // T-184: a wrapped CLI in the foreground without the shim's launch arguments, and when its argv is next read.
  unwiredCli?: { command: string; pid: number; since: string } | null; wiringCheckAt?: number; wiringBusy?: boolean;
  // T-187: the last OSC 7501 state report of the terminal's CLI (agy, opencode), until that CLI exits.
  cliTurn?: CliTurn | null; oscCarry?: string;
  // T-187: a managed agy or opencode session; its turns come from its OSC 7501 reports (reportedTurns).
  reports?: boolean; reportedEnding?: boolean; trustWritten?: number;
  claudePromptId?: string | null;
  claudePromptIds?: Set<string>;
  claudeQueuedPrompts?: { prompt: string; received_at: string;
    stops?: Map<string, { value: any; received_at: string;
      transfer?: (pane: Pane, stop: any, matched: boolean) => Promise<void> }> }[];
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
  // The terminal-only socket the daemon opened (T-126); project terminals reach the daemon only through it.
  terminalSocket: string | null = null;
  constructor(root: string, store: OrchestrationStore, config: LaunchConfig, onEventWriteFailed: (reason: string) => void) {
    this.root = root; this.store = store; this.config = config;
    this.onEventWriteFailed = onEventWriteFailed;
  }
  ensureProject = async (_project: string, _repo: string) => {};
  startShell(project: string | null, cwd: string) {
    check(project === null || typeof project === "string" && /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(project), "invalid_project");
    check(typeof cwd === "string" && isAbsolute(cwd) && statSync(cwd).isDirectory(), "invalid_shell_cwd");
    check(this.terminalSocket, "terminal_socket_unavailable");
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
      A2A_TERMINAL_CLI: terminalCli, A2A_NODE: process.execPath, A2A_TERMINAL_SOCKET: this.terminalSocket, A2A_TERMINAL: launch, A2A_TERMINAL_TOKEN: token });
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
      pane.outputAt = Date.now(); pane.silentForeground = null;
      const reports = readOsc7501(pane.oscCarry ?? "", data);
      pane.oscCarry = reports.carry;
      // While a CLI reports its state, look at the foreground every few seconds: it can exit without a line typed after.
      if (reports.turns.length) { pane.cliTurn = reports.turns.at(-1); pane.wiringCheckAt ??= Date.now() + WIRING_RECHECK_MS; }
      try { appendFileSync(trace, data); }
      catch (error) { this.recordFailure(pane, "trace_write_failed", error); }
    });
    const silence = setInterval(() => { void this.watchSilence(pane); void this.watchWiring(pane); }, 1000);
    terminal.onExit((event: unknown) => {
      clearInterval(silence);
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
      pane.silenceCheck = true;
      // T-184: a submitted line may start a CLI; its argv is read once it has had time to exec.
      if (data.includes("\r")) pane.wiringCheckAt = Date.now() + WIRING_CHECK_DELAY_MS;
    });
  }
  // T-184: the foreground program of a project terminal, when it is a CLI a shim wraps, must carry the shim's launch
  // arguments; without them it runs without Enchanted's plugin and hooks, and the terminal says so instead of showing a
  // turn state it cannot know. Read after a submitted line, and again while a warning stands so it clears when that
  // CLI exits.
  private async watchWiring(pane: Pane) {
    const due = pane.wiringCheckAt;
    if (due === undefined || Date.now() < due || pane.wiringBusy || pane.stopped) return;
    pane.wiringBusy = true; pane.wiringCheckAt = undefined;
    try {
      const info = await this.processInfo(pane.record.thread);
      const leader = (info.processes as { pid: number; pgid: number; tpgid: number }[])
        .find(row => row.pid !== pane.pty.pid && row.pid === row.pgid && row.pgid === row.tpgid);
      if (!leader) { pane.unwiredCli = null; pane.cliTurn = null; return; }
      const { stdout } = await exec("/usr/bin/python3", ["-I", "-S", "-B", processArgs, String(leader.pid)], { timeout: 5000 });
      const launch = JSON.parse(stdout) as { argv: string[]; shim: string | null };
      const command = cliProgram(launch.argv);
      const cli = command === undefined ? undefined : terminalClis[command];
      // Reports belong to the CLI in front; another program in front (`opencode; sleep 60`) leaves none standing.
      if (cli?.turns !== "osc7501") pane.cliTurn = null;
      const unwired = Boolean(cli) && !cli!.wired(launch);
      pane.unwiredCli = !unwired ? null : pane.unwiredCli?.pid === leader.pid ? pane.unwiredCli
        : { command: command!, pid: leader.pid, since: new Date().toISOString() };
      if (unwired || pane.cliTurn) pane.wiringCheckAt = Date.now() + WIRING_RECHECK_MS;
    } catch (error) {
      // The process may have exited between the two reads; with no observation the terminal shows no warning.
      pane.unwiredCli = null;
      this.store.event("cli_wiring_check_failed", { error: String(error) }, pane.record);
    } finally { pane.wiringBusy = false; }
  }
  // T-174: only the mechanical fact is used: the terminal's foreground program started after the last output and has
  // written nothing for SILENT_FOREGROUND_MS. A new foreground program starts only from typed input, so the process
  // tree is read once per quiet stretch after input, not on every tick.
  private async watchSilence(pane: Pane) {
    const outputAt = pane.outputAt ?? 0;
    if (!pane.silenceCheck || pane.silenceBusy || pane.stopped || Date.now() - outputAt < SILENT_FOREGROUND_MS) return;
    pane.silenceBusy = true;
    try {
      const info = await this.processInfo(pane.record.thread);
      if (pane.outputAt !== outputAt || pane.stopped) return;
      const leader = (info.processes as { pid: number; pgid: number; tpgid: number; command: string; started?: number }[])
        .find(row => row.pid !== pane.pty.pid && row.pid === row.pgid && row.pgid === row.tpgid);
      if (!leader || typeof leader.started !== "number" || leader.started * 1000 <= outputAt) { pane.silenceCheck = false; return; }
      if (Date.now() - leader.started * 1000 < SILENT_FOREGROUND_MS) return;
      pane.silenceCheck = false;
      pane.silentForeground = { command: basename(leader.command), since: new Date(leader.started * 1000).toISOString() };
    } catch (error) {
      // No hint without an observation; the failure is kept and the next input checks again.
      pane.silenceCheck = false;
      this.store.event("silent_foreground_check_failed", { error: String(error) }, pane.record);
    } finally { pane.silenceBusy = false; }
  }
  // A command the daemon starts in a project terminal it opened itself (a retrospective, T-136); the user sees it
  // there like their own and can keep using the terminal afterwards.
  async runInShell(launch: string, argv: string[]) {
    await this.shellInput(launch, shellCommand(argv) + "\r", "utf8", async () => {});
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
      await this.restore(daemon, record, opened.native_session, opened.resume_argv, opened.position);
    }
    // A monitor (T-124) keeps watching after a restart whether or not a window shows it: its session resumes
    // with the recorded argv like an open pane's. A worker or reviewer whose process went with the previous
    // daemon is registered as stopped once both its recorded shell and CLI processes are confirmed gone, so the
    // gate can reclaim its attempt (T-096 ruling B: reclaim, then a new attempt). This holds after every later
    // restart too, until the pane is archived: a record recovered by an earlier daemon is never live in this one
    // (T-128: the second restart left the worker unknown to the gate, `unknown_pane`).
    for (const record of this.store.launches()) {
      if (!["monitor", "worker", "reviewer"].includes(record.role) || this.panes.has(record.thread)) continue;
      if (!this.store.lastEvent(record.id, ["pane_started"]) || this.store.lastEvent(record.id, ["pane_archived"])) continue;
      if (!this.store.lastEvent(record.id, ["pane_recovered"])) continue;
      if (record.role === "monitor") {
        const bound = this.store.lastEvent(record.id, ["pane_native_session"]);
        const native = record.cli === "Claude Code" ? record.native_session : bound?.data.native_session ?? null;
        this.store.event("pane_restore_pending", { daemon, position: null }, record as any);
        await this.restore(daemon, record, native, record.cli === "Claude Code" ? resumeArgv(record, native) : bound?.data.resume_argv ?? null, null);
      } else await this.registerGone(record);
    }
  }
  private async registerGone(record: any) {
    try {
      const shell = this.store.lastEvent(record.id, ["pane_started"])!.data.shell_pid;
      const leader = this.store.lastEvent(record.id, ["pane_leader_observed"])?.data.leader_pid ?? null;
      // A CLI still exiting after the SIGHUP the previous daemon sent gets up to 10 s, as a closing shell does.
      const deadline = Date.now() + 10_000;
      for (const pid of [shell, leader].filter(pid => pid !== null)) {
        check(Number.isSafeInteger(pid) && pid > 1, "recorded_process_invalid");
        for (;;) {
          const result = await exec("/usr/bin/python3", ["-I", "-S", "-B", processQuery, String(pid)], { timeout: 5000 });
          if (JSON.parse(result.stdout).rows.length === 0) break;
          check(Date.now() < deadline, "previous_process_alive");
          await new Promise(resolve => setTimeout(resolve, 200));
        }
      }
      const native = record.cli === "Claude Code" ? record.native_session : this.store.lastEvent(record.id, ["pane_native_session"])?.data.native_session ?? null;
      const pane = { record, token: "", task: null, attempt: { workspace: record.worktree }, pty: { pid: shell }, state: "unknown",
        stopped: true, archived: false, failed: null, leader, native, turn: null, nativeEnded: false, active: null, queue: [],
        writing: false, stopInProgress: false, writes: Promise.resolve(), pendingInputs: 0, userDraft: false, interrupted: false,
        inputGeneration: 0, interruption: null, sending: null, offsets: new Map(), model: "unknown", effort: "unknown",
        terminalBuffer: "", claudePromptId: null, claudePromptIds: new Set() } as unknown as Pane;
      this.panes.set(record.thread, pane);
      this.store.event("pane_gone_confirmed", { shell_pid: shell, leader_pid: leader, native_session: native }, record);
    } catch (error) {
      this.store.event("pane_gone_unconfirmed", { error: error instanceof Refusal ? error.code : String(error) }, record);
    }
  }
  private async restore(daemon: string, record: any, native: string | null, expected: string[] | null, position: number | null) {
    try {
      // T-096 decision B: worker/reviewer attempts retain their gate-owned
      // runtime binding. Restoration must neither spawn nor mutate an attempt.
      check(record.attempt === null, "restore_managed_attempt_requires_reclaim");
      if (record.role === "monitor") requireMonitorRestore(record); else requireFakeControllerRestore(record);
      const argv = resumeArgv(record, native);
      // A controller pane's shell runs a shell after its CLI; a monitor's, like a worker's, first exits on the CLI's failure.
      const tail = record.role === "monitor" ? MANAGED_SHELL_TAIL : "; exec /bin/zsh -f -i";
      check(record.shell_argv[3] === shellCommand(record.argv) + tail, "restore_record_unrecognized");
      const previous = this.store.lastEvent(record.id, ["pane_started", "pane_restored"]);
      if (Number.isSafeInteger(previous?.data.shell_pid) && previous!.data.shell_pid > 1) {
        try {
          process.kill(previous!.data.shell_pid, 0);
          throw new Refusal("restore_previous_process_alive");
        } catch (error) {
          if ((error as NodeJS.ErrnoException).code !== "ESRCH") throw error;
        }
      }
      check(expected && argv.length === expected.length &&
        argv.every((arg, index) => arg === expected![index]), "restore_argv_changed");
      const taskRow = this.store.db.prepare("SELECT data FROM tasks WHERE id=?").get(record.task);
      const task = taskRow && JSON.parse(String(taskRow.data));
      check(task && task.project_id === record.project && task.spec_rev === record.spec_rev, "restore_task_stale");
      check(typeof record.cli_version === "string" && record.cli_version !== "unknown", "restore_version_missing");
      // Native CLIs update themselves; the restored runtime records its own probe.
      const probe = await exec(argv[0]!, ["--version"], { env: record.env, timeout: 10000, maxBuffer: 65536 });
      const nativeFile = nativeSessionFile(record, native!);
      check(record.shell === "/bin/zsh" && record.env && isAbsolute(record.worktree), "restore_launch_invalid");
      const executablePath = realpathSync(argv[0]!);
      check(record.executable_path === undefined || record.executable_path === executablePath, "restore_executable_changed");
      // Legacy launch history is immutable. Bind this restored runtime only,
      // after the session checks and before creating a PTY; it carries the CLI version now installed.
      const runtimeRecord = { ...record, executable_path: executablePath, cli_version: probe.stdout.trim() };
      const token = randomUUID();
      const trace = join(this.root, "traces", record.id, "pty.raw");
      check(existsSync(trace), "trace_unavailable");
      const shellArgv = ["-f", "-i", "-c", shellCommand(argv) + tail];
      const terminal = require("node-pty").spawn(record.shell, shellArgv, {
        name: "xterm-256color", cols: 160, rows: 45, cwd: record.worktree,
        env: { ...record.env, A2A_CAPABILITY: token }, encoding: "utf8",
      });
      const pane: Pane = { record: runtimeRecord as Pane["record"], token, task, attempt: record.role === "monitor" ? monitorAttempt(record, task) : null, pty: terminal,
        state: "unknown", stopped: false, archived: false, failed: null, leader: null,
        native: native, nativeFile, turn: null, nativeEnded: false, active: null,
        queue: [], writing: false, stopInProgress: false, writes: Promise.resolve(), pendingInputs: 0,
        userDraft: false, interrupted: false, inputGeneration: 0, interruption: null, sending: null,
        offsets: new Map([[nativeFile, readFileSync(nativeFile).length]]), model: "unknown", effort: "unknown",
        terminalBuffer: "", claudePromptId: null, claudePromptIds: new Set(), restored: true };
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
      // A resumed Codex CLI waits at its prompt: the restore sends no input (Claude reports the same through SessionStart).
      if (record.role === "monitor" && record.cli !== "Claude Code") pane.state = "idle";
      this.store.event("pane_restored", { daemon, position, argv,
        shell_argv: shellArgv, shell_pid: terminal.pid, leader: info.leader,
        native_session: native, version_probe: { argv: [argv[0], "--version"], stdout: probe.stdout, stderr: probe.stderr } }, pane.record);
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
        cleanup, native_session: native }, record as any);
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
    check(attempt.runtime_mode === "workspace-write", "worker_requires_workspace_write");
    await this.createPane(task, attempt, this.config, undefined, overrides);
  }
  async createReview(task: A2ATask, review: A2AReview, prompt: string) {
    const attempt = { ...review.attempt, session_id: review.session_id, thread_id: review.thread_id,
      workspace: review.candidate_workspace, runtime_identity: null, turn_id: null };
    check(this.config.reviewer_role_card && this.config.reviewer_role_card_revision, "review_launch_config_required");
    const reviewConfig = { ...this.config, role_card: this.config.reviewer_role_card,
      role_card_revision: this.config.reviewer_role_card_revision };
    if (task.card.executor.cli !== "Codex") {
      // D24: the reviewer defaults to the worker's CLI and model; it runs with the worker launch's selection.
      const worker = this.launchRecord(review.attempt.runtime_identity!.launch);
      await this.createPane(task, attempt, reviewConfig, review,
        { model: worker.model_requested, effort: worker.effort_requested, fast: worker.service_tier_requested === "fast" });
    } else await this.createPane(task, attempt, reviewConfig, review);
    const pane = this.get(review.thread_id);
    // T-187: an agy or opencode reviewer has no OS sandbox. Its review checkout is read-only by file permissions (the
    // candidate copy it works in stays writable for its mutation checks), and its result goes to a file.
    if (pane.reports) {
      treeWritable(review.workspace, false);
      this.store.event("review_checkout_read_only", { workspace: review.workspace }, pane.record);
      prompt += `\n\n本会话的最后一条回复不会被读取：把上面要求的 JSON 原样写入文件 ${join(pane.record.request_dir, REVIEW_RESULT_FILE)}，然后结束本回合。`;
    }
    await this.dispatch(pane, `${pane.record.role_text}\n\n${prompt}`);
  }
  // A read-only monitor a controller attaches to a task (T-124): it belongs to no attempt, opens the
  // task's repository read-only, runs on the CLI the controller chose with the monitor role settings,
  // and lives on after the controller's role ends.
  createAttachedThread = async (task: A2ATask, attachment: A2AAttachment, prompt: string) => {
    check(attachment.role === "monitor", "attach_role_unsupported");
    check(this.config.monitor_role_card && this.config.monitor_role_card_revision, "monitor_launch_config_required");
    check(typeof attachment.workspace === "string" && isAbsolute(attachment.workspace), "monitor_workspace_required");
    mkdirSync(attachment.workspace, { recursive: true, mode: 0o700 });
    const attempt = { task_id: task.task_id, attempt_id: null, session_id: attachment.thread_id, fence: 0, spec_rev: task.spec_rev,
      thread_id: attachment.thread_id, runtime_mode: "workspace-write", turn_id: null, workspace: realpathSync(attachment.workspace), base_commit: null,
      runtime_identity: null } as unknown as A2AAttempt;
    await this.createPane(task, attempt, { ...this.config, role_card: this.config.monitor_role_card,
      role_card_revision: this.config.monitor_role_card_revision }, undefined,
      { ...(attachment.model !== undefined ? { model: attachment.model } : {}), ...(attachment.effort !== undefined ? { effort: attachment.effort } : {}),
        ...(attachment.fast !== undefined ? { fast: attachment.fast } : {}) }, attachment);
    const pane = this.get(attachment.thread_id);
    await this.dispatch(pane, `${pane.record.role_text}\n\n项目目录（只读）：${realpathSync(task.repo)}\n\n${prompt}`);
  };
  private async createPane(task: A2ATask, attempt: A2AAttempt, c: LaunchConfig, review?: A2AReview, overrides: ExecutionOverrides = {},
    monitor?: A2AAttachment) {
    const role = review ? "reviewer" : monitor ? "monitor" : "worker";
    // The task card names the worker's CLI; its reviewer runs on the same CLI (D24). A monitor runs on its own.
    const workerCli: string = monitor ? monitor.cli : task.card.executor.cli;
    const claude = workerCli === "Claude Code";
    // T-187: agy and opencode report their own turns to the terminal (OSC 7501); a monitor stays on Claude Code or Codex.
    const managed = !monitor && Object.hasOwn(terminalClis, workerCli) ? terminalClis[workerCli].managed : undefined;
    const bin = claude ? c.claude_bin : managed ? (workerCli === "agy" ? c.agy_bin : c.opencode_bin) : c.codex_home && c.codex_bin;
    check(bin && c.role_card && c.hook_authorization && c.code_revision && c.role_card_revision, "launch_config_required");
    check(Number.isInteger(c.turn_limit) && c.turn_limit! > 0 && c.turn_limit! <= (claude ? 6 : 10), "invalid_turn_limit");
    const executable = realpathSync(bin!);
    // A Codex worker and its reviewer run in the user's own Codex home (user ruling 2026-10-21, T-127).
    const home = claude || managed ? null : realpathSync(c.codex_home!);
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
    const { model, effort, fast } = this.store.executionSelection(role, (claude || managed) && !review && !monitor
      ? { ...(task.card.executor.model.trim() ? { model: task.card.executor.model } : {}),
          ...(task.card.executor.effort.trim() ? { effort: task.card.executor.effort } : {}), ...overrides } : overrides);
    const launchWorkspace = review ? review.candidate_workspace : attempt.workspace;
    // A worker can put .codex config, hooks or exec policy in its candidate. Keep that
    // untrusted for the independent reviewer; worker/monitor inherit user trust (T-127, T-141).
    const trustRoot = claude || managed ? null : review ? realpathSync(launchWorkspace) : null;
    const nativeSession = claude ? randomUUID() : null;
    const extraDirectories = (this.store.openedProjects().find(project => project.project_id === task.project_id)?.extra_directories ?? [])
      .map(path => realpathSync(path));
    // agy and opencode run without an OS sandbox; a reviewer's checkout is made read-only below instead.
    const sandboxMode = managed ? "none" : monitor && !extraDirectories.length ? "read-only" : "workspace-write";
    const reported = managed?.({ executable, workspace: launchWorkspace, model, effort, extraDirectories });
    // T-141: inherit the user's trust, tools and proxy configuration. Only the write
    // roots, open network, per-session instrumentation and execution selection are supplied.
    const writeRoots = [...(review || monitor ? [] : [requestDirectory]), ...extraDirectories];
    // --setting-sources also excludes user MCP. Pass only its native MCP source, without
    // enabling user settings that can merge wider native file-tool permission grants.
    const userConfig = claude && environment.HOME ? join(environment.HOME, ".claude.json") : null;
    const mcpConfig = userConfig && existsSync(userConfig) &&
      Object.keys(JSON.parse(readFileSync(userConfig, "utf8")).mcpServers ?? {}).length ? userConfig : null;
    const argv = reported ? reported.argv : claude ? await claudeArgv(executable, signalCommand, nativeSession!, { model, effort, fast },
      [...(monitor ? [] : review ? [realpathSync(launchWorkspace)] : [realpathSync(launchWorkspace), requestDirectory]), ...extraDirectories],
      [...(review || monitor ? [] : [requestDirectory]), ...extraDirectories], review || monitor ? [] : await workerGitDenied(launchWorkspace), extraDirectories, mcpConfig) : [executable, "--no-daemon", "--no-alt-screen", "-C", launchWorkspace,
      "-a", "never", "--sandbox", sandboxMode, "-m", model,
      ...(review ? ["-c", `projects={${JSON.stringify(trustRoot)}={trust_level="untrusted"}}`] : []),
      "-c", `model_reasoning_effort=${JSON.stringify(effort)}`, "-c", `service_tier=${JSON.stringify(fast ? 'fast' : 'default')}`,
      "-c", "check_for_update_on_startup=false",
      // Near the quota Codex asks at a turn's end whether to switch models; the next pasted
      // prompt's Enter answered it and switched the model instead of starting a turn (T-167).
      "-c", "notice.hide_rate_limit_model_nudge=true",
      "-c", "sandbox_workspace_write.network_access=true",
      "-c", `sandbox_workspace_write.writable_roots=${JSON.stringify(writeRoots)}`,
      ...extraDirectories.flatMap(path => ["--add-dir", path]),
      "-c", "sandbox_workspace_write.exclude_slash_tmp=true",
      "-c", "sandbox_workspace_write.exclude_tmpdir_env_var=true"];
    if (!claude && !managed) {
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
      // The commit hook reads no turn record for these CLIs (hooks/hook.py): model and effort trailers are unknown.
      ...(managed ? { A2A_TURNS: "osc7501", A2A_NATIVE_SESSION: reportedSession(launch), ...reported!.env } : {}),
    });
    if (review) environment.A2A_REVIEW = review.review_id;
    if (!claude && !managed) {
      // Exclude the shared temporary roots, but retain shell here-documents and tempfile.
      // Workers use their request directory; reviewers/monitors use their one-time copy.
      const temporary = join(review || monitor ? realpathSync(launchWorkspace) : requestDirectory, ".a2a-tmp");
      mkdirSync(temporary, { mode: 0o700 });
      Object.assign(environment, { TMPDIR: temporary + "/", TMPPREFIX: join(temporary, "zsh") });
    }
    if (!review && !monitor) Object.assign(environment, { GIT_CONFIG_COUNT: "1", GIT_CONFIG_KEY_0: "core.hooksPath",
      GIT_CONFIG_VALUE_0: fileURLToPath(new URL("../hooks/", import.meta.url)) });
    const shellArgv = ["-f", "-i", "-c", shellCommand(argv) + MANAGED_SHELL_TAIL];
    const { A2A_CAPABILITY: _secret, ...recordedEnvironment } = environment;
    const record = { id: launch, project: task.project_id, task: task.task_id, attempt: attempt.attempt_id,
      session: attempt.session_id, fence: attempt.fence, spec_rev: attempt.spec_rev, thread: attempt.thread_id,
      role, sandbox: sandboxMode, extra_directories: extraDirectories, parent_launch: this.parentLaunch.getStore() ?? null,
      cli: workerCli, ...(claude ? { native_session: nativeSession } : managed ? { native_session: reportedSession(launch) } : {}),
      ...(review ? { review_id: review.review_id, review_verification_id: review.verification_id,
        review_workspace: review.workspace, candidate_workspace: review.candidate_workspace } : {}),
      created_at: new Date().toISOString(), cli_version: version, argv, executable_path: executable, request_dir: requestDirectory,
      model_requested: model, effort_requested: effort, service_tier_requested: fast ? 'fast' : 'default',
      turn_limit: c.turn_limit, turn_authorization: c.turn_authorization ?? null,
      code_revision: c.code_revision, source_snapshot: c.source_snapshot ?? null, role_card: c.role_card, role_card_revision: c.role_card_revision,
      role_text: readFileSync(c.role_card, "utf8") + `\n\n本会话可写的项目额外目录：${JSON.stringify(extraDirectories)}。其中的改动不进门禁的审查与集成。`, base_commit: attempt.base_commit, worktree: launchWorkspace,
      shell: "/bin/zsh", shell_argv: shellArgv, env: recordedEnvironment, helper, hook_authorization: c.hook_authorization };
    this.store.launch(record);
    mkdirSync(join(this.root, "traces", launch), { recursive: true, mode: 0o700 });
    appendFileSync(join(this.root, "traces", launch, "pty.raw"), "", { flag: "wx", mode: 0o600 });
    const terminal = require("node-pty").spawn("/bin/zsh", shellArgv, {
      name: "xterm-256color", cols: 160, rows: 45, cwd: attempt.workspace, env: environment, encoding: "utf8",
    });
    const pane: Pane = { record, token, task, attempt, pty: terminal, state: "unknown", stopped: false,
      archived: false, failed: null, leader: null, native: managed ? reportedSession(launch) : nativeSession, turn: null, reports: Boolean(managed), nativeEnded: false, active: null,
      queue: [], writing: false, stopInProgress: false, writes: Promise.resolve(), pendingInputs: 0, userDraft: false, interrupted: false, inputGeneration: 0, interruption: null, sending: null,
      offsets: new Map(), model: "unknown", effort: "unknown", terminalBuffer: "",
      startupScreen: "", trustAnswered: false,
      ...(claude ? { claudePromptId: null, claudePromptIds: new Set<string>() } : {}) };
    this.panes.set(attempt.thread_id, pane);
    this.store.event("pane_started", { shell_pid: terminal.pid, state: "unknown" }, record);
    // A Claude session that never reports its start (an unrecognised screen, a CLI that changed)
    // is a failure to show, not a pane that waits forever with its task queued.
    setTimeout(() => {
      if (!pane.started && !pane.stopped && !pane.failed)
        this.recordFailure(pane, "worker_startup_unrecognised", new Error(claude ? "session_start_missing" : "native_ready_signal_missing"), { screen: pane.startupScreen });
    }, STARTUP_DEADLINE_MS).unref();
    terminal.onData((data: string) => {
      try {
        appendFileSync(join(this.root, "traces", launch, "pty.raw"), data);
      } catch (error) { this.recordFailure(pane, "trace_write_failed", error); return; }
      try { this.scan(pane); }
      catch (error) { this.recordFailure(pane, "native_read_failed", error); return; }
      if (pane.reports) this.reportedTurns(pane, data);
      else if (pane.state === "unknown") (claude ? this.confirmWorkerTrust(pane, data) : this.openCodexRestricted(pane, data));
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
  // Inherit the user's trust (T-141). If Codex offers "Open restricted", that choice saves
  // nothing and may be answered once. "Trust and continue" would save a new trust decision,
  // so it gets no key. Initial task release waits for the native ready packet below.
  openCodexRestricted(pane: Pane, data: string) {
    if (pane.started || pane.active || pane.state !== "unknown" || pane.failed) return;
    pane.startupOutputAt = Date.now();
    pane.startupScreen = (pane.startupScreen! + data.replace(/\x1b\[[0-?]*[ -\/]*[@-~]|\x1b\][^\x07]*?(?:\x07|\x1b\\)/g, "").replace(/\s+/g, "")).slice(-4096);
    if (pane.startupScreen.includes("Trustandcontinue")) {
      this.recordFailure(pane, "codex_folder_trust_requested", new Error("trust_choice_not_answered"), { screen: pane.startupScreen });
      return;
    }
    if (pane.trustAnswered || !pane.startupScreen.includes("›1.Openrestricted")) return;
    pane.trustAnswered = true;
    const screen = pane.startupScreen;
    const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
    // Act once the screen has been quiet for a moment, as for Claude's trust screen.
    const quiet = async () => { for (const until = Date.now() + 5000; Date.now() - pane.startupOutputAt! < 800 && Date.now() < until;) await sleep(100); };
    void (async () => {
      this.store.event("codex_restricted_open_intent", { worktree: pane.record.worktree, screen }, pane.record);
      await quiet();
      await this.serializeWrite(pane, async () => { pane.pty.write("\r"); });
      this.store.event("codex_restricted_opened", { worktree: pane.record.worktree }, pane.record);
    })().catch(error => this.recordFailure(pane, "codex_restricted_open_failed", error, { screen: pane.startupScreen }));
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
      // T-141 native startup probes: a trusted folder sends this packet without a trust
      // dialog; a restricted folder sends it only after "Open restricted". It admits the
      // first task only. Later turns still require the matching Stop hook, never OSC idle.
      if (match[2] === "7501;state=idle:app=codex" && pane.record.cli === "Codex" &&
          !pane.started && !pane.active && pane.state === "unknown" && !pane.failed && !pane.stopped) {
        pane.started = true;
        void (async () => {
          const info = await this.processInfo(pane.record.thread);
          check(info.leader && !info.failed, "foreground_codex_required", info);
          if (pane.active || pane.failed || pane.stopped) return;
          this.store.event("codex_startup_ready", { source: "native_terminal_protocol", packet: match[2] }, pane.record);
          pane.state = "idle";
          await this.drain(pane);
        })().catch(error => this.recordFailure(pane, "codex_startup_failed", error));
      }
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
      if (pane.leader === null && leader !== null) {
        pane.leader = leader;
        // Kept so a restarted daemon can confirm this CLI process is gone (T-124).
        this.store.event("pane_leader_observed", { shell_pid: pane.pty.pid, leader_pid: leader }, pane.record);
      }
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
    if (pane.stopped || pane.reports) return;
    if (pane.record.role === "shell") return;
    if (pane.record.cli === "Claude Code") {
      if (!pane.claudeQueuedPrompts?.length) return;
      // A Stop's caller checks also scan. They must not advance past the turn
      // whose completion is still transferring its explicit requests.
      if (pane.stopInProgress) return;
      // Input typed during a working turn (T-166) queues before that turn's Stop.
      // It becomes its own turn only after the turn it was typed into completes.
      if (pane.active) return;
      // Busy-input UPS carries the still-running prompt id. Only the native
      // queued human transcript establishes the eventual new prompt id, before
      // any caller check or hook matching may use that turn.
      const lines = readFileSync(pane.nativeFile!, 'utf8').split('\n');
      lines.pop(); // A final partial line is not yet native evidence.
      const entries = lines.filter(Boolean).map(line => JSON.parse(line));
      while (pane.claudeQueuedPrompts.length) {
        const queued = pane.claudeQueuedPrompts[0]!;
        const entry = entries.find(value => value.type === 'user' && value.isSidechain === false &&
          value.sessionId === pane.native && value.cwd === pane.record.worktree &&
          value.promptSource === 'queued' && value.turnOrigin === 'human' && value.origin?.kind === 'human' &&
          typeof value.promptId === 'string' && value.promptId.length > 0 && value.promptId.length <= 128 &&
          !pane.claudePromptIds!.has(value.promptId) && typeof value.uuid === 'string' && value.uuid.length > 0 &&
          Number.isFinite(Date.parse(value.timestamp)) && Date.parse(value.timestamp) >= Date.parse(queued.received_at) &&
          value.message?.role === 'user' && value.message.content === queued.prompt);
        if (!entry) break;
        pane.claudeQueuedPrompts.shift();
        pane.active = { id: randomUUID(), dispatch: `input:${entry.promptId}`, at: entry.timestamp, nativeTurn: null };
        pane.claudePromptIds!.add(entry.promptId); pane.claudePromptId = entry.promptId;
        pane.state = 'busy'; pane.permission = null;
        this.store.event('turn_submit_intent', { ...pane.active, source: 'user', origin: 'native-transcript' }, pane.record);
        this.store.event('turn_submitted', { ...pane.active, source: 'user', origin: 'native-transcript' }, pane.record);
        this.store.event('turn_start_signal', { session_id: pane.native, prompt_id: entry.promptId, origin: 'native-transcript',
          transcript_path: pane.nativeFile, transcript_uuid: entry.uuid, received_at: queued.received_at }, pane.record);
        for (const [prompt, stop] of queued.stops ?? []) {
          if (prompt !== entry.promptId) this.store.event('stop_not_matched', stop.value, pane.record);
        }
        const early = queued.stops?.get(entry.promptId);
        if (early) {
          this.store.event('claude_stop_matched_transcript', { prompt_id: entry.promptId, received_at: early.received_at,
            transcript_uuid: entry.uuid }, pane.record);
          // The native record supplies identity, not the early Stop. Complete
          // through the same checks and transfer as a Stop arriving after it.
          void this.claudeStop(pane, early.value, early.received_at, early.transfer)
            .then(() => this.drain(pane))
            .catch(error => this.recordFailure(pane, 'deferred_stop_failed', error));
          break;
        }
      }
      return;
    }
    const home = pane.record.env.CODEX_HOME as string;
    const walk = (dir: string): string[] => !existsSync(dir) ? [] : readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
      entry.isDirectory() ? walk(join(dir, entry.name)) : entry.name.endsWith(".jsonl") ? [join(dir, entry.name)] : []);
    // The home is the user's own ~/.codex (T-127), whose sessions directory holds every earlier
    // session under sessions/YYYY/MM/DD (local date). A session this launch started lives in a day
    // directory from the launch's day on and was written since the launch; the rest is never read.
    const since = Date.parse(pane.record.created_at);
    const days: string[] = [];
    for (const day = new Date(since); day.getTime() <= Date.now() + 86_400_000; day.setDate(day.getDate() + 1))
      days.push(join(home, "sessions", String(day.getFullYear()), String(day.getMonth() + 1).padStart(2, "0"), String(day.getDate()).padStart(2, "0")));
    const files = final ? [...pane.offsets.keys()].filter((file) => codexSessionFileName(file, pane.native)) :
      pane.nativeFile ? [pane.nativeFile] : [...new Set([...pane.offsets.keys(), ...days.flatMap(walk).filter((file) => statSync(file).mtimeMs >= since)])];
    if (final) check(pane.native && files.length === 1, "native_bound_log_unavailable", { native_session: pane.native, files });
    for (const file of files) {
      const bytes = readFileSync(file);
      // The home holds other sessions' rollouts. Only logs belonging to this
      // worktree contribute records or native identity.
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
  // An answer to an issue the worker raised: the user's from the UI, or a terminal controller's (T-124).
  // A pane that has ended cannot take it; the gate forwards the answer to the executor instead.
  sendAnswer = async (thread: string, messageId: string, message: string, origin: "user" | "controller") => {
    const pane = this.get(thread);
    if (pane.stopped || pane.archived || pane.nativeEnded) throw new Refusal("session_ended");
    const item = await this.dispatch(pane, message, origin === "user" ? "user" : "executor");
    this.store.event("answer_registered", { message_id: messageId, dispatch: item.id, origin }, pane.record);
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
    // xterm emits complete mouse/focus/device reports through the same onData
    // channel as keys. Recognize only whole report packets, never arbitrary CSI
    // keys or bracketed-paste contents. CSI 1;modifier R is also modified F3;
    // keep it as a key (device queries are already owned by terminalProtocol).
    const protocolReport = binary ? /^(?:\x1b\[M[\s\S]{3})+(?![\s\S])/.test(data)
      : /^(?:(?:\x1b\[|\x9b)(?:<[0-9]+;[0-9]+;[0-9]+[Mm]|[0-9]+;[0-9]+;[0-9]+M|[IO]|0n|(?!1;(?:[2-9]|1[0-6])R)\??[0-9]+;[0-9]+R|[?>][0-9;]+c|\??[0-9]+;[0-4]\$y|(?:4|6|8);[0-9]+;[0-9]+t)|\x1b\](?:4;[0-9]+|10|11|12);rgb:[0-9a-fA-F/]+(?:\x07|\x1b\\)|\x1bP[01]\$r[ -~]*\x1b\\)+(?![\s\S])/.test(data);
    const pasted = !binary && data.startsWith("\x1b[200~") && data.endsWith("\x1b[201~");
    const text = binary ? "终端二进制输入" : pasted ? data.slice(6, -6).replaceAll("\r", "\n") : data;
    const control = binary || (!pasted && /[\x00-\x1f\x7f]/.test(data));
    // Reserve synchronously, before the recorder or identity check can yield.
    // Input records and their bytes keep the same order as admission. Esc also
    // prevents the CR of a paste that is already waiting inside this stream.
    pane.pendingInputs++;
    if (!protocolReport) pane.inputGeneration++;
    if (!binary && data === "\x1b") { pane.interrupted = true; pane.state = "busy"; }
    try { await this.serializeWrite(pane, async () => {
      await assertCurrent();
      if (!protocolReport) await record(text, control);
      check(!pane.failed && !pane.stopped && !pane.archived, "pane_unavailable");
      if (!binary && !protocolReport) pane.userDraft = true;
      this.store.event("terminal_input_write_intent", { ...receipt, encoding,
        ...(binary ? { data_base64: bytes.toString("base64") } : { data }), byte_length: bytes.length }, pane.record);
      const permissionControl = Boolean(!binary && data === "\r" && pane.record.cli === "Claude Code" &&
        pane.permission && pane.active && pane.permission.prompt_id === pane.claudePromptId && pane.permission.submission === pane.active.id);
      if (!binary && !pasted && /[\r\n]/.test(data) && !permissionControl) {
        pane.state = "busy"; pane.userDraft = false;
        pane.permission = null;
        // Claude owns steering/queueing while it works. Enter is input evidence,
        // not a native turn transition; a fresh UPS or verified queued transcript
        // owns the next turn. In particular, do not invalidate an in-flight Stop.
        if (pane.record.cli !== "Claude Code") {
          pane.active = { id: randomUUID(), dispatch: `input:${receipt.request_id}`, at: new Date().toISOString(), nativeTurn: null };
          this.store.event("turn_submit_intent", { ...pane.active, source: "user", request_id: receipt.request_id }, pane.record);
        }
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
      // The Enter reached the terminal, which does not prove a turn started: a CLI dialog can take it
      // (T-167: Codex's rate-limit model prompt). Only the native start signal starts the turn; without
      // it the pane says so. Nothing is resent and no key is pressed for the user.
      setTimeout(() => {
        if (pane.active !== submission || pane.stopped || pane.failed) return;
        if (this.store.lastEvent(pane.record.id, ["turn_submitted", "turn_start_signal"])?.type !== "turn_submitted") return;
        this.store.event("turn_start_missing", { submission: submission.id, dispatch: item.id, deadline_ms: TURN_START_DEADLINE_MS }, pane.record);
      }, TURN_START_DEADLINE_MS).unref();
      // A submitted Codex turn writes its rollout at once. One that never names this pane's folder ran
      // elsewhere or did not start (a hidden resume of a live session: "open in another app"); without
      // this the pane and its review wait forever with no record (T-127 counterexamples).
      if (pane.record.cli !== "Claude Code" && ["worker", "reviewer"].includes(pane.record.role) && !pane.native) setTimeout(() => {
        try { this.scan(pane); } catch (error) { this.recordFailure(pane, "native_read_failed", error); return; }
        if (!pane.native && !pane.stopped && !pane.failed)
          this.recordFailure(pane, "native_session_unbound", new Error("no rollout in the launch folder after the first turn"),
            { workspace: pane.attempt.workspace, submission: submission.id });
      }, STARTUP_DEADLINE_MS).unref();
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
  private deliveryStatus(record: Pane['record']): WorkerDeliveryStatus | null {
    const row = this.store.db.prepare(`SELECT q.seq AS received_seq,q.data AS received,q.time AS received_at,
        r.seq AS result_seq,r.data AS outcome,r.time AS result_at
      FROM orchestration_events q LEFT JOIN orchestration_events r ON r.launch=q.launch
        AND r.type IN ('relay_processed','relay_rejected') AND json_extract(r.data,'$.key')=json_extract(q.data,'$.key')
      WHERE q.launch=? AND q.type='relay_received' AND json_extract(q.data,'$.input.command')='submit'
      ORDER BY q.seq DESC,r.seq DESC LIMIT 1`).get(record.id);
    // An unmatched old Stop is refused before execution, so it has no relay intent.
    // Project its explicit refusal too, without treating it as an executed request.
    const refused = this.store.db.prepare(`SELECT seq,time,data FROM orchestration_events
      WHERE launch=? AND type='relay_rejected' AND json_extract(data,'$.result.error')='relay_requires_current_stop'
        AND json_extract(CASE WHEN json_valid(json_extract(data,'$.file.raw')) THEN json_extract(data,'$.file.raw') ELSE '{}' END,'$.command')='submit'
      ORDER BY seq DESC LIMIT 1`).get(record.id);
    const late = refused && (!row || Number(refused.seq) > Number(row.received_seq)) ? refused : null;
    if (!row && !late) return null;
    const data = late ? JSON.parse(String(late.data)) : null;
    const input = late ? JSON.parse(data.file.raw) : JSON.parse(String(row!.received)).input;
    if (input.task !== record.task || input.attempt !== record.attempt || input.session !== record.session ||
        input.fence !== record.fence || input.spec_rev !== record.spec_rev ||
        typeof input.commit !== 'string' || !/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(input.commit) ||
        typeof input.request_id !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(input.request_id)) return null;
    const result = late ? data.result : row!.outcome ? JSON.parse(String(row!.outcome)).result : null;
    const sequence = Number(late?.seq ?? row!.received_seq);
    const stop = this.store.db.prepare(`SELECT data FROM orchestration_events WHERE launch=?
      AND type=? AND seq<? ORDER BY seq DESC LIMIT 1`).get(record.id, late ? 'stop_not_matched' : 'turn_end_signal', sequence);
    const stopped = stop ? JSON.parse(String(stop.data)) : null;
    const started = this.store.db.prepare(`SELECT data FROM orchestration_events WHERE launch=?
      AND type='turn_start_signal' AND seq<=? ORDER BY seq DESC LIMIT 1`)
      .get(record.id, Number(late?.seq ?? row!.result_seq ?? sequence));
    const current = started ? JSON.parse(String(started.data)) : null;
    const requestTurn = stopped?.prompt_id ?? stopped?.turn_id ?? null;
    const currentTurn = current?.prompt_id ?? current?.turn_id ?? null;
    return { task: input.task, attempt: input.attempt, session: input.session, fence: input.fence, spec_rev: input.spec_rev,
      request_id: input.request_id, commit: input.commit, received_at: String(late?.time ?? row!.received_at),
      result_at: late ? String(late.time) : row!.result_at === null ? null : String(row!.result_at),
      state: !result ? this.panes.get(record.thread)?.stopInProgress ? 'processing' : 'unknown'
        : result.ok ? 'submitted' : result.error === 'relay_outcome_unknown' ? 'unknown' : 'rejected',
      reason: result?.error ?? null, request_turn: requestTurn, current_turn: currentTurn,
      native_turn_changed: Boolean(requestTurn && currentTurn && requestTurn !== currentTurn),
      recovery_request_id: `recover-${sequence}` };
  }
  // The current submission's Enter reached the terminal but no native turn started by the deadline (T-167).
  private startMissing(pane: Pane) {
    const last = pane.active && this.store.lastEvent(pane.record.id, ["turn_submitted", "turn_start_signal", "turn_start_missing"]);
    return Boolean(last && last.type === "turn_start_missing" && last.data.submission === pane.active!.id);
  }
  status(thread: string) {
    const record = this.store.threadLaunch(thread);
    const restore = record && this.store.lastEvent(record.id, ["pane_restore_pending", "pane_restored", "pane_restore_failed"]);
    const restoration = !restore ? null : { status: restore.type === "pane_restored" ? "restored" :
      restore.type === "pane_restore_failed" ? "failed" : "pending", error: restore.data.error ?? null, details: restore.data.details ?? null };
    const pane = this.panes.get(thread);
    if (pane) {
      return { thread, launch: pane.record.id, state: pane.failed || pane.stopped ? "unknown" : pane.state,
        lifecycle: pane.archived || pane.nativeEnded || pane.record.role === "shell" && pane.stopped ? "ended" : pane.stopped ? "interrupted" : "running", shell_pid: pane.pty.pid,
        size: { cols: pane.pty.cols, rows: pane.pty.rows },
        state_source: pane.failed ? "runtime_failure" : "host_events", active: pane.active, native_session: pane.native,
        start_missing: this.startMissing(pane), silent_foreground: pane.silentForeground ?? null,
        unwired_cli: pane.unwiredCli ? { command: pane.unwiredCli.command, since: pane.unwiredCli.since } : null,
        cli_turn: pane.cliTurn ?? null,
        turn: pane.turn, writing: pane.writing, user_draft: pane.userDraft, interrupted: pane.interrupted,
        input_generation: pane.inputGeneration, interruption: pane.interruption,
        queued: pane.queue.map((item) => item.id), failed: pane.failed, stopped: pane.stopped, restoration,
        delivery: pane.record.role === 'worker' ? this.deliveryStatus(pane.record) : null };
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
      stopped: archived ? true : recovered?.data.exit_event ? true : null, historical: true,
      delivery: record.role === 'worker' ? this.deliveryStatus(record) : null };
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
      if (pane.reports) return await this.reportedStop(pane, value, received_at, transfer);
      if (pane.record.cli === 'Claude Code') { this.scan(pane); binding = currentTurnBinding(pane); }
      // A new authenticated Claude UPS is the native CLI's turn transition.
      // Do not infer it from Enter, and do not let a reused old prompt replace it.
      const newClaudePrompt = pane.record.cli === 'Claude Code' && value.hook_event_name === 'UserPromptSubmit' &&
        typeof value.prompt_id === 'string' && !pane.claudePromptIds?.has(value.prompt_id);
      excluded = noncurrentHook(newClaudePrompt ? { ...pane, claudePromptId: null } : pane, value, received_at);
      // Keep unmatched Stop semantics. All other noncurrent hooks are refused
      // before common-field validation and cannot poison the current launch.
      if (excluded) {
        check(value.session_id === pane.native || !value.session_id, 'hook_native_session_mismatch');
        if (value.hook_event_name === 'Stop') {
          this.store.event('stop_not_matched', value, pane.record);
          // Record a definite refusal for delayed requests from a known old root.
          // matched=false prevents the relay from executing any new operation.
          if (pane.record.cli === 'Claude Code' && pane.record.role === 'worker' &&
              pane.claudePromptId && value.prompt_id !== pane.claudePromptId && pane.claudePromptIds?.has(value.prompt_id) &&
              value.session_id === pane.native && !value.agent_id) {
            validateHookEnvelope({ ...pane, claudePromptId: value.prompt_id }, value);
            check(Number.isFinite(Date.parse(received_at)) && value.stop_hook_active === false, 'stale_stop_unverified');
            if (transfer) await transfer(pane, value, false);
          }
          return;
        }
        throw new Refusal('hook_origin_or_turn_mismatch');
      }
      check(Number.isFinite(Date.parse(received_at)), 'hook_received_at_required');
      // SessionEnd is session-scoped: the CLI can exit at its prompt, after the last turn has been cleared.
      if (pane.record.cli === "Claude Code" && value.hook_event_name === "SessionEnd") {
        check(typeof value.session_id === "string" && value.session_id.length > 0 && value.session_id === pane.native &&
          !value.agent_id && value.cwd === pane.record.worktree &&
          typeof value.transcript_path === "string" && basename(value.transcript_path) === `${pane.native}.jsonl` &&
          typeof value.reason === "string" && value.reason.length > 0, "session_end_mismatch");
        this.store.event("native_session_ended", { native_session: pane.native, shell_pid: pane.pty.pid,
          leader_pid: pane.leader, hook_event_name: value.hook_event_name, reason: value.reason }, pane.record);
        pane.nativeEnded = true;
        return;
      }
      // A Claude worker's session start is its ready signal: release the first task to it.
      if (pane.record.cli === "Claude Code" && pane.record.role !== "controller" && value.hook_event_name === "SessionStart") {
        // A monitor resumed after a restart (T-124) starts its session again with source "resume".
        check(value.session_id === pane.native && value.cwd === pane.record.worktree && value.source === (pane.restored ? "resume" : "startup"), "session_start_mismatch");
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
        // A worker, reviewer or monitor asks through `issue` (T-124 ruling 1a): nobody answers its native question,
        // so it is recorded and not shown as waiting. Codex's request_user_input_async returns at once anyway.
        if (pane.record.role !== "controller") {
          if (value.hook_event_name === 'PreToolUse') this.store.event('native_question_ignored', { ...binding, question: question.id, tool: value.tool_name }, pane.record);
          return;
        }
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
          const item = !pane.claudePromptId && pane.active && this.store.dispatchRecord(pane.active.dispatch);
          check(typeof value.prompt_id==="string" && value.prompt_id.length>0 && value.prompt_id.length<=128,"claude_prompt_id_required");
          // Input typed while the current turn is still working or in its Stop
          // batch: the CLI queues it under the running prompt id (T-157, T-166).
          if (pane.active && value.prompt_id === pane.claudePromptId && typeof value.prompt === 'string') {
            const history = this.store.read().filter(event => event.launch === launch);
            const previous = history.findLast(event => ['turn_start_signal', 'claude_prompt_queued'].includes(event.type));
            const enter = history.findLast(event => event.type === 'terminal_input_write_intent' && event.seq > (previous?.seq ?? 0) &&
              event.data.encoding === 'utf8' && typeof event.data.data === 'string' &&
              !event.data.data.startsWith('\x1b[200~') && /[\r\n]/.test(event.data.data) &&
              history.some(written => written.type === 'terminal_input_written' && written.data.request_id === event.data.request_id));
            check(enter, 'claude_prompt_id_reused');
            pane.nativeFile ??= nativeSessionFile(pane.record, pane.native!);
            check(realpathSync(value.transcript_path) === realpathSync(pane.nativeFile), 'question_origin_unverified');
            (pane.claudeQueuedPrompts ??= []).push({ prompt: claudeSubmittedText(value.prompt), received_at });
            this.store.event('claude_prompt_queued', { ...value, input_seq: enter.seq, received_at }, pane.record);
            return;
          }
          check(pane.claudePromptIds && !pane.claudePromptIds.has(value.prompt_id),"claude_prompt_id_reused");
          if (item && claudeSubmittedText(value.prompt) !== item.text) {
            const reason = "登记注入与实际提交正文不一致；已阻断，请处理草稿后再决定。";
            this.store.event("injected_prompt_blocked", { prompt: value.prompt, prompt_id: value.prompt_id,
              dispatch: item.id, submission: pane.active!.id, expected_prompt: item.text, reason }, pane.record);
            this.store.event('native_question_unverified', { ...fact(), reason: 'injected_prompt_blocked', hook_event_name: value.hook_event_name }, pane.record);
            pane.state = "busy";
            return { decision: "block" as const, reason };
          }
          // Source comes from the current structured submission, never text markers.
          // Hand-typed submissions and retired injections cannot trigger this guard.
          if (!item) {
            this.store.event("user_prompt_unregistered", value, pane.record);
            pane.active = { id: randomUUID(), dispatch: `input:${value.prompt_id}`, at: received_at, nativeTurn: null };
            pane.claudePromptId = null; pane.state = 'busy';
            this.store.event('turn_submit_intent', { ...pane.active, source: 'user', origin: 'native-hook' }, pane.record);
            this.store.event('turn_submitted', { ...pane.active, source: 'user', origin: 'native-hook' }, pane.record);
          }
          check(pane.state === "busy" && !pane.claudePromptId, "claude_submission_unmatched");
          pane.permission = null;
          pane.claudePromptIds.add(value.prompt_id);pane.claudePromptId=value.prompt_id;this.store.event("turn_start_signal", value, pane.record); return;
        }
        check(value.hook_event_name === "Stop", "unsupported_hook");
        this.store.event("turn_end_signal", value, pane.record);
        return await this.claudeStop(pane, value, received_at, transfer);
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
        const protocolFailure = pane.record.role === "reviewer" && pane.failed === "invalid_review_result";
        if (protocolFailure && (pane.active !== active || pane.active?.nativeTurn !== value.turn_id || pane.turn !== value.turn_id || pane.native !== value.session_id)) {
          pane.state = "unknown";
          this.store.event("stop_not_matched", { ...value, stage: "after_transfer" }, pane.record); return;
        }
        // A rejected protocol result still ended this matched review turn. Keep the
        // failure/blocking marker; only the gate may stop/archive it and start afresh.
        pane.active = null; pane.state = pane.failed && !protocolFailure ? "unknown" : pane.interrupted ? "busy" : "idle";
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
  // T-187: the end of an agy or opencode turn, sent by the daemon itself under the pane's launch identity when the CLI
  // reports it (reportedTurns). The same transfer and completion as a Codex Stop, without a hook envelope to check.
  private async reportedStop(pane: Pane, value: any, received_at: string,
    transfer?: (pane: Pane, stop: any, matched: boolean) => Promise<void>) {
    check(value.hook_event_name === "Stop" && value.source === "osc7501" && value.session_id === pane.native, "unsupported_hook");
    check(Number.isFinite(Date.parse(received_at)), "hook_received_at_required");
    this.store.event("turn_end_signal", value, pane.record);
    const active = pane.active;
    const matched = Boolean(!pane.failed && !pane.stopInProgress && active?.nativeTurn && value.turn_id === active.nativeTurn &&
      Date.parse(received_at) >= Date.parse(active.at));
    if (active) check(currentTurnTrust(pane, this.store.read().filter(e => e.launch === pane.record.id)) === "verified", "current_turn_untrusted");
    if (matched) pane.stopInProgress = true;
    try {
      if (transfer) await transfer(pane, value, matched);
      if (!matched) { this.store.event("stop_not_matched", value, pane.record); return; }
      const protocolFailure = pane.record.role === "reviewer" && pane.failed === "invalid_review_result";
      pane.active = null; pane.state = pane.failed && !protocolFailure ? "unknown" : pane.interrupted ? "busy" : "idle";
      this.store.event(pane.state === "idle" ? "pane_idle" : "pane_completion_held", { submission: active!.id, state: pane.state, stop: value }, pane.record);
    } catch (error) {
      if (matched) this.recordFailure(pane, "stop_transfer_failed", error);
      throw error;
    } finally { if (matched) pane.stopInProgress = false; }
  }
  // Set by the daemon: ends a reported turn through the same signal command a Stop hook uses.
  reportedTurnEnd?: (pane: Pane, stop: Record<string, unknown>) => Promise<void>;
  // T-187: the turns of a managed agy or opencode session, from its OSC 7501 reports. The first idle report is its ready
  // signal; a working report after a submitted task starts that turn (its id is the backend's); the next idle, done or
  // clear ends it. agy asks to trust each new folder before it starts (agyTrust). A question is recorded and not shown
  // as waiting (T-124 ruling 1a); a permission or sign-in wait is recorded and shown as it is, with no key pressed.
  reportedTurns(pane: Pane, data: string) {
    const read = readOsc7501(pane.oscCarry ?? "", data);
    pane.oscCarry = read.carry;
    if (!pane.started) pane.startupOutputAt = Date.now();
    if (!pane.started) pane.startupScreen = (pane.startupScreen! + data.replace(/\x1b\[[0-?]*[ -\/]*[@-~]|\x1b\][^\x07]*?(?:\x07|\x1b\\)/g, "").replace(/\s+/g, "")).slice(-4096);
    for (const turn of read.turns) {
      pane.cliTurn = turn;
      this.store.event("native_turn_report", turn, pane.record);
      if (turn.state === "working") {
        const active = pane.active;
        if (pane.started && active && !active.nativeTurn) {
          active.nativeTurn = pane.turn = `osc7501:${active.id}`;
          this.store.event("turn_start_signal", { session_id: pane.native, submission: active.id, turn_id: active.nativeTurn, source: "osc7501" }, pane.record);
        }
      } else if (["idle", "done", "clear"].includes(turn.state)) {
        // After a trust answer the session starts once the write is checked (agyTrust), whichever comes first.
        if (!pane.started) { if (!pane.trustAnswered || pane.trustWritten !== undefined) this.reportedStart(pane); }
        else if (pane.active?.nativeTurn && !pane.stopInProgress && !pane.reportedEnding) {
          pane.reportedEnding = true;
          const stop = { hook_event_name: "Stop", source: "osc7501", session_id: pane.native, turn_id: pane.active.nativeTurn,
            report: turn.state, ...(pane.record.role === "reviewer" ? { last_assistant_message: reviewResult(pane) } : {}) };
          void this.reportedTurnEnd!(pane, stop).catch(error => this.recordFailure(pane, "stop_transfer_failed", error))
            .finally(() => { pane.reportedEnding = false; });
        }
      } else if (turn.state === "blocked") {
        if (!pane.started && turn.kind === "permission" && pane.record.cli === "agy" && turn.msg === "Trust this folder?") this.agyTrust(pane);
        else this.store.event(turn.kind === "question" ? "native_question_ignored" : "native_wait_reported",
          { ...turn, submission: pane.active?.id ?? null }, pane.record);
      }
    }
  }
  private reportedStart(pane: Pane) {
    if (pane.started || pane.failed || pane.stopped) return;
    pane.started = true;
    this.store.event("native_session_started", { native_session: pane.native, source: "osc7501", trust_written: pane.trustWritten ?? 0 }, pane.record);
    pane.state = "idle";
    void this.drain(pane).catch(error => this.recordFailure(pane, "dispatch_failed", error));
  }
  // T-187, ready_rev 2: agy asks once for every new folder, and a yes adds the folder to trustedWorkspaces in the user's
  // ~/.gemini/antigravity-cli/settings.json. The user allowed exactly that write, through agy's own dialog: the dialog
  // must name this session's folder with the yes choice drawn as selected, and afterwards the file may differ only by
  // that one folder added to trustedWorkspaces. Anything else stops the session with the screen recorded; no key is
  // pressed. The count of folders written is recorded with the session's start.
  agyTrust(pane: Pane) {
    if (pane.trustAnswered || pane.failed) return;
    pane.trustAnswered = true;
    const settings = join(pane.record.env.HOME, ".gemini/antigravity-cli/settings.json");
    const folder = pane.record.worktree as string;
    const read = () => JSON.parse(readFileSync(settings, "utf8")) as Record<string, unknown>;
    const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
    void (async () => {
      // Act once the dialog has been drawn completely and the output has been quiet for a moment.
      for (const until = Date.now() + 5000; Date.now() - pane.startupOutputAt! < 800 && Date.now() < until;) await sleep(100);
      const screen = pane.startupScreen!;
      const dialog = screen.lastIndexOf("Accessingworkspace:" + folder.replace(/\s+/g, "") + "Doyoutrustthecontentsofthisproject?");
      const yes = screen.lastIndexOf(">Yes,Itrustthisfolder"), no = screen.lastIndexOf(">No,exit");
      if (dialog < 0 || yes < dialog || yes < no) throw new Refusal("agy_trust_dialog_unrecognised");
      const before = read();
      const listed = (value: unknown) => Array.isArray(value) ? value.map(String) : [];
      if (listed(before.trustedWorkspaces).includes(folder)) throw new Refusal("agy_trust_already_listed");
      this.store.event("agy_trust_confirm_intent", { folder, settings, screen }, pane.record);
      await this.serializeWrite(pane, async () => { pane.pty.write("\r"); });
      let after = before;
      for (const until = Date.now() + 10_000; Date.now() < until; await sleep(200)) {
        after = read();
        if (listed(after.trustedWorkspaces).includes(folder)) break;
      }
      const { trustedWorkspaces: was, ...rest } = before, { trustedWorkspaces: now, ...restAfter } = after;
      const added = listed(now).filter(entry => !listed(was).includes(entry));
      if (JSON.stringify(rest) !== JSON.stringify(restAfter) || listed(was).some(entry => !listed(now).includes(entry)) ||
        JSON.stringify(added) !== JSON.stringify([folder])) throw new Refusal("agy_trust_write_unexpected", { added, settings });
      pane.trustWritten = added.length;
      this.store.event("agy_trust_written", { folder, settings, entries_written: added.length }, pane.record);
      if (pane.cliTurn && ["idle", "done", "clear"].includes(pane.cliTurn.state)) this.reportedStart(pane);
    })().catch(error => this.recordFailure(pane, "agy_trust_failed", error, { screen: pane.startupScreen }));
  }
  async claudeStop(pane: Pane, value: any, received_at: string,
    transfer?: (pane: Pane, stop: any, matched: boolean) => Promise<void>) {
    validateHookEnvelope(pane, value);
    check(Number.isFinite(Date.parse(received_at)), 'hook_received_at_required');
    const active = pane.active;
    const current = Boolean(active && pane.claudePromptId && value.prompt_id === pane.claudePromptId &&
      !pane.failed && !pane.stopped && !pane.nativeEnded && !pane.stopInProgress && !value.agent_id &&
      Date.parse(received_at) >= Date.parse(active.at));
    if (current && typeof value.stop_hook_active !== 'boolean') throw new Refusal('stop_hook_active_required');
    const matched = current && value.stop_hook_active === false;
    if (!matched) {
      const queued = pane.claudeQueuedPrompts?.[0];
      // Keep only an authenticated, fresh root Stop while this exact queued
      // input awaits native identity. Consuming that input discards other ids.
      if (queued && !active && !pane.claudePromptId && !pane.failed && !pane.stopped && !pane.nativeEnded &&
          !pane.interrupted && !pane.stopInProgress && !value.agent_id && value.stop_hook_active === false &&
          !pane.claudePromptIds?.has(value.prompt_id) && Date.parse(received_at) >= Date.parse(queued.received_at)) {
        check(realpathSync(value.transcript_path) === realpathSync(pane.nativeFile!), 'question_origin_unverified');
        queued.stops ??= new Map();
        if (!queued.stops.has(value.prompt_id)) queued.stops.set(value.prompt_id, { value, received_at, transfer });
        this.store.event('claude_stop_waiting_transcript', value, pane.record);
        return;
      }
      this.store.event('stop_not_matched', value, pane.record); return;
    }
    check(currentTurnTrust(pane, this.store.read().filter(e => e.launch === pane.record.id)) === 'verified', 'current_turn_untrusted');
    if (pane.record.role !== 'controller') this.claudeTurnFacts(pane, value);
    pane.stopInProgress = true;
    try {
      if (transfer) await transfer(pane, value, true);
      check(currentTurnTrust(pane, this.store.read().filter(e => e.launch === pane.record.id)) === 'verified', 'current_turn_untrusted');
      if (pane.active !== active || pane.claudePromptId !== value.prompt_id) {
        this.store.event('stop_not_matched', { ...value, stage: 'after_transfer' }, pane.record); return;
      }
      this.dropAbsorbedPrompts(pane);
      pane.active = null; pane.claudePromptId = null; pane.permission = null;
      pane.state = pane.interrupted || pane.claudeQueuedPrompts?.length ? 'busy' : 'idle';
      this.store.event(pane.claudeQueuedPrompts?.length ? 'pane_waiting_native_queue' : pane.state === 'idle' ? 'pane_idle' : 'pane_completion_held',
        { submission: active!.id, stop: value }, pane.record);
    } catch (error) {
      this.recordFailure(pane, 'stop_transfer_failed', error); throw error;
    } finally { pane.stopInProgress = false; }
  }
  // Input typed while a tool call is still to come is absorbed into the running
  // turn: the CLI records queue-operation remove with reason absorbed_mid_turn and
  // hands the text to the model with the next tool result. It never becomes a
  // turn of its own, so the pane must not wait for one (T-169).
  private dropAbsorbedPrompts(pane: Pane) {
    if (!pane.claudeQueuedPrompts?.length) return;
    const lines = readFileSync(pane.nativeFile!, 'utf8').split('\n');
    lines.pop(); // A final partial line is not yet native evidence.
    const removals = lines.filter(Boolean).map(line => JSON.parse(line)).filter(value =>
      value.type === 'queue-operation' && value.operation === 'remove' && value.reason === 'absorbed_mid_turn' &&
      value.sessionId === pane.native && typeof value.commandUuid === 'string' && value.commandUuid.length > 0 &&
      Number.isFinite(Date.parse(value.timestamp)));
    const used = new Set(this.store.read().filter(event => event.launch === pane.record.id && event.type === 'claude_prompt_absorbed')
      .map(event => event.data.command_uuid));
    pane.claudeQueuedPrompts = pane.claudeQueuedPrompts.filter(queued => {
      const removal = removals.find(value => !used.has(value.commandUuid) && value.content === queued.prompt &&
        Date.parse(value.timestamp) >= Date.parse(queued.received_at));
      if (!removal) return true;
      used.add(removal.commandUuid);
      this.store.event('claude_prompt_absorbed', { prompt: queued.prompt, received_at: queued.received_at,
        command_uuid: removal.commandUuid, delivery_id: removal.deliveryId ?? null, absorbed_at: removal.timestamp }, pane.record);
      return false;
    });
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
    return { workspace: pane.attempt.workspace, provider: cliProvider(pane.record.cli),
      turn: pane.record.cli === "Claude Code" ? pane.claudePromptId ?? null : pane.turn,
      runtime_identity: { launch: pane.record.id, thread, shell_pid: pane.pty.pid,
        leader_pid: pane.leader, native_session: pane.native },
      running: (pane.state !== "idle" || pane.writing) && !pane.stopped && !pane.nativeEnded,
      stopped: pane.stopped, archived: pane.archived, session_ended: pane.nativeEnded,
      blocked: Boolean(pane.failed), ...(pane.failed ? { error: { providerPresent: !pane.stopped, activeTurn: pane.turn } } : {}) };
  };
  stopThread = async (thread: string) => {
    const pane = this.get(thread);
    // A confirmed CLI exit can leave activity busy (/exit has no Stop hook), with only its shell to reclaim.
    check(pane.stopped || pane.nativeEnded || pane.state === "idle", "worker_not_idle");
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
