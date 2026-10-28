import { createServer } from "node:net";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmdirSync, rmSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { basename, isAbsolute, join } from "node:path";
import { A2AGates, Refusal, type TerminalController } from "./gates/core.ts";
import { ControllerQuota, type QuotaState } from "./controllerQuota.ts";
import { A2AGateRequest } from "./contracts/a2aGates.ts";
import { OrchestrationStore } from "./store.ts";
import { Panes, spawnHelper, claudeSubmittedText, codexQuestionReply, type LaunchConfig } from "./panes.ts";
import { socketPath } from "./transport.ts";
import { RequestRelay, isPendingInboxResult } from "./relay.ts";
import { readWorkerRequests, writeReviewRequest, writeControllerContext } from "./relayFiles.ts";

type Asker = { gone?: () => void };
import { reviewRequest, scoreRecords, QualityProtocolError } from "./gates/qualityProtocol.ts";
import { randomUUID } from "node:crypto";
import { createOperatorCredential, readOperatorCredential } from "./credentials.ts";
import { sidebarSnapshot, projectCatalog } from './sidebar.ts';
import { flowSnapshot } from './flow.ts';
import { receiptLines } from './gateReceipts.ts';
import { explainRefusal } from './gates/refusals.ts';
import { checkWorkBranchPrefix, defaultWorkBranch, dropWorkBranch } from './workBranch.ts';
import { metricsSnapshot } from './metrics.ts';
import { userInputRecords } from './userInputRecords.ts';
import { reflectTree } from './reflect.ts';
import { TrajectoryArchive } from './trajectoryArchive.ts';
import { nativeLink } from './nativeLink.ts';
import { Retrospectives, retrospectiveArgv, retrospectivePrompt } from './retrospective.ts';
import { RoleRequests, confirmWindowMs, type RoleRequest } from './roleRequests.ts';
import { executionRole, executionOverrides } from './executionSettings.ts';

// Window payloads can contain shell passwords, even when identity/validation
// fails. Agent input still has its existing dedicated recorder below.
function eventInput(input: any) {
  if (typeof input?.command === "string" && input.command.startsWith("window_")) {
    return { command: input.command, sequence: input.sequence, request_id: input.request_id };
  }
  return input;
}

export async function serve(
  root: string,
  config: LaunchConfig,
  createGates: (root: string, panes: Panes) => A2AGates = (root, panes) => new A2AGates(root, panes),
) {
  mkdirSync(root, { recursive: true, mode: 0o700 });
  root = realpathSync(root);
  const socket = socketPath(root);
  if (existsSync(socket)) throw new Error("socket exists; refusing to replace it");
  const operator = readOperatorCredential(root);
  if (!operator) throw new Error("operator_credential_required");
  const helper = spawnHelper();
  const store = new OrchestrationStore(root);
  const panes = new Panes(root, store, config, (reason) => gates.setUserInputObserverStatus("failed", { reason }));
  const gates = createGates(root, panes);
  gates.openedProjectRepo = project => store.openedProjects().find(opened => opened.project_id === project)?.repo;
  const relay = new RequestRelay(store);
  const roleRequests = new RoleRequests(store, launch => panes.terminalAlive(launch));
  // A terminal controller's usage limit, read from its own session log (T-124).
  const quota = new ControllerQuota(store);
  const quotaTimer = setInterval(() => {
    try { quota.tick(roleRequests.all().filter(roleRequest => roleRequest.state === "approved")); }
    catch (error) { console.error(JSON.stringify({ error: "controller_quota_failed", reason: String(error) })); }
  }, 5000);
  quotaTimer.unref();
  // Trajectory archive (T-135): after every Claude turn of the session, and every 30 s for everything else. A failed
  // increment is recorded and retried by the next sweep; it never fails the hook or the daemon.
  const archive = new TrajectoryArchive(store.db, root, (type, data, launch) => store.event(type, data, { id: launch, task: null }));
  const archiveSweep = (launch?: string) => {
    try { archive.sweep(launch); }
    catch (error) { store.event("trajectory_archive_failed", { error: String(error) }, launch ? { id: launch, task: null } : undefined); }
  };
  const archiveTimer = setInterval(() => archiveSweep(), 30_000);
  archiveTimer.unref();
  // Retrospectives (T-136): started by the user or the weekly schedule, run in an ordinary project terminal the daemon
  // opens; the schedule is checked and finished runs imported every minute (and on retrospective_tick, whose `now`
  // a test may set).
  const retrospectives = new Retrospectives(store.db, root);
  const startRetrospective = async (project: string, selection: { cli: string; model: string; effort: string },
    trigger: "manual" | "schedule", scheduledFor: string | null, now: Date, range?: { since?: string | null; until?: string | null }) => {
    const opened = store.openedProjects().find(entry => entry.project_id === project);
    if (!opened) throw new Refusal("unknown_project");
    if (!["Claude Code", "Codex"].includes(selection.cli) || typeof selection.model !== "string" || !selection.model.trim() ||
      typeof selection.effort !== "string" || !selection.effort.trim()) throw new Refusal("invalid_retrospective_selection");
    const run = retrospectives.prepare(project, opened.repo, selection, trigger, scheduledFor, now, range);
    const session = randomUUID();
    const argv = retrospectiveArgv(run, config, retrospectivePrompt(run, root), session);
    // The run is recorded before its terminal opens, so its slot is taken; a start that fails says so on the run
    // (T-136 review 01) instead of leaving it "in progress". It is not retried by itself: the user can start one.
    try {
      const shell = panes.startShell(project, opened.repo);
      store.event("retrospective_started", { run: run.id, cli: run.cli, model: run.model, effort: run.effort, argv,
        native_session: run.cli === "Claude Code" ? session : null,
        native_home: run.cli === "Claude Code" ? process.env.CLAUDE_CONFIG_DIR ?? join(process.env.HOME ?? "", ".claude")
          : process.env.CODEX_HOME ?? join(process.env.HOME ?? "", ".codex"),
        package: run.package, out: run.out }, shell);
      retrospectives.record(run.id, "started", { launch: shell.id, native_session: run.cli === "Claude Code" ? session : null });
      await panes.runInShell(shell.id, argv);
      return { ...run, launch: shell.id };
    } catch (error) {
      retrospectives.record(run.id, "start_failed", { error: String(error) });
      throw error;
    }
  };
  const retrospectiveTick = async (now: Date) => {
    const started = [];
    for (const project of store.openedProjects()) {
      const slot = retrospectives.due(project.project_id, now);
      if (!slot) continue;
      const schedule = retrospectives.schedule();
      // A project whose run fails to start has it recorded on the run; the others and the import still go ahead.
      try { started.push(await startRetrospective(project.project_id, schedule, "schedule", slot, now)); }
      catch (error) { store.event("retrospective_tick_failed", { project: project.project_id, error: String(error) }); }
    }
    return { started, imported: retrospectives.importFinished() };
  };
  const retrospectiveTimer = setInterval(() => {
    retrospectiveTick(new Date()).catch(error => store.event("retrospective_tick_failed", { error: String(error) }));
  }, 60_000);
  retrospectiveTimer.unref();
  const controllerOf = (initiator: { launch: string; role_request: string; role: string }): TerminalController => ({ ...initiator,
    state: () => roleRequests.approved(initiator.launch)?.id !== initiator.role_request ? "ended" : quota.exhausted(initiator.role_request) ? "quota_exhausted" : "active" });
  const terminalController = (launch: string, roleRequest: RoleRequest) => controllerOf({ launch, role_request: roleRequest.id, role: roleRequest.role });
  const feedbackText = (receipts: any[], role: string) => role === "worker"
    // T-179: a worker's pane gets a short summary; the full receipt is in relay_results and on the records page.
    ? "门禁回执（完整内容在记录页的“门禁回执”里）。请仅确认收到并结束；不调用工具、不改文件、不新增请求。\n" +
      receipts.map(receipt => receiptLines(relayCommand(receipt.key), receipt.result).join("\n")).join("\n")
    : "本回合的异步请求处理结果如下。请仅确认收到并结束；不调用工具、不改文件、不新增请求。\n" + JSON.stringify(receipts, null, 2);
  // T-205: a refused reply keeps its code and gains one line of why and what to do next, for a2a, MCP and the window alike.
  const explained = (result: any) => {
    const why = result?.ok === false ? explainRefusal(result.error) : null;
    return why ? { ...result, explanation: why } : result;
  };
  const relayCommand = (key: string): string | null => {
    const row = store.db.prepare("SELECT json_extract(input,'$.command') AS command FROM relay_requests WHERE key=?").get(key) as any;
    return row?.command ?? null;
  };
  const settleInboxFeedback = async () => {
    for (const receipt of relay.deferredInboxFeedback()) {
      const delivery = await gates.inboxDeliveryStatus(receipt.result.entry.id);
      if (delivery?.state !== "delivered") continue;
      const pane = [...panes.panes.values()].find(value => value.record.id === receipt.launch);
      if (!pane || pane.stopped || pane.archived || pane.failed) continue;
      const live = await panes.processInfo(pane.record.thread);
      const current = await gates.call({ command: "status", task: pane.record.task });
      if (!current.ok || current.task?.spec_rev !== pane.record.spec_rev || current.task?.project_id !== pane.record.project ||
          pane.stopped || pane.archived || pane.failed || !live.leader || live.failed ||
          live.native_session !== pane.native || live.shell_pid !== pane.pty.pid) continue;
      if (pane.record.role === "controller" && pane.native !== pane.record.session) continue;
      if (pane.record.role === "worker") {
        const attempt = current.task.current_attempt;
        if (!attempt || attempt.reclaimed || attempt.attempt_id !== pane.record.attempt ||
            attempt.session_id !== pane.record.session || attempt.fence !== pane.record.fence) continue;
      }
      if (!relay.claimDeliveredFeedback(receipt.key, delivery)) continue;
      const { launch: _launch, ...original } = receipt;
      const final = { ...original, replayed: false, result: { ...receipt.result, delivery } };
      const dispatch = await panes.dispatch(pane, feedbackText([final], pane.record.role), "gate");
      store.event("relay_feedback_registered", { key: receipt.key, request_id: receipt.request_id,
        entry_id: delivery.entry_id, delivery, dispatch: dispatch.id }, pane.record);
    }
  };
  const daemon = randomUUID();
  type WindowBinding = { id: string; token: string; role: string; task: string | null; launch: string; sequence: number; requests: Set<string> };
  const windows = new Map<string, WindowBinding>();
  const shellInputCommands = new Set(["window_input", "window_composition", "window_observation", "window_release"]);
  const isShellInput = (envelope: any) => {
    if (!shellInputCommands.has(envelope.input?.command) || envelope.identity?.kind !== "window" ||
        typeof envelope.identity.window !== "string") return false;
    const window = windows.get(envelope.identity.window);
    if (window) return window.role === "shell";
    // A closed/restarted shell window must not leak rejected key timings either.
    // Resolve only daemon-issued window IDs, never a client-supplied role.
    const previous = store.db.prepare(`SELECT json_extract(l.data,'$.role') AS role FROM orchestration_events e
      JOIN launch_records l ON l.id=e.launch WHERE e.type='window_opened'
      AND json_extract(e.data,'$.window_id')=? LIMIT 1`).get(envelope.identity.window);
    return previous?.role === "shell";
  };
  const catalogCommands = new Set(["projects_list", "tasks_list", "sidebar_snapshot", "flow_snapshot"]);
  const readOnly = new Set([...catalogCommands, "daemon_status", "orchestration_events", "pane_output", "workbench_snapshot",
    "pane_layout", "pane_status", "pane_process_info", "launch_show", "status", "events", "task_history", "issues", "card_show", "card_template", "card_validate", "execution_settings", "work_branch_prefix", "metrics", "user_input_records", "relay_receipts", "trajectory_archive", "native_link", "retrospective_list", "reflect_tree"]);
  const authenticate = (identity: any): { source: string; kind: "operator" | "window" | "launch" | "terminal" | "anonymous";
      window?: WindowBinding; terminal?: { id: string; project: string | null; task: string | null } } => {
    if (!identity) return { source: "anonymous", kind: "anonymous" };
    if (identity.kind === "operator") {
      if (identity.token !== operator.token || identity.epoch !== operator.epoch || identity.state !== root) throw new Refusal("invalid_operator_identity");
      return { source: "executor", kind: "operator" };
    }
    if (identity.kind === "window") {
      const window = windows.get(identity.window);
      if (!window || identity.token !== window.token) throw new Refusal("invalid_window_identity");
      return { source: "user", kind: "window", window };
    }
    if (identity.kind === "terminal") {
      const terminal = panes.authenticateTerminal(identity).record;
      return { source: "terminal:" + terminal.id, kind: "terminal", terminal };
    }
    const pane = panes.authenticate(identity);
    return { source: pane.record.role === "controller" ? pane.record.preset :
      pane.record.role === "worker" ? `worker:${pane.record.thread}` : pane.record.role, kind: "launch" };
  };
  gates.setUserInputObserverStatus("healthy");
  let stopping = false;
  let recovering = true;
  let recovery: Promise<void>;
  let activeRequests = 0;
  let requestsDrained: (() => void) | undefined;
  const activityFinished = () => {
    activeRequests--;
    if (activeRequests === 0) { requestsDrained?.(); requestsDrained = undefined; }
  };
  const shutdown = async () => {
    stopping = true;
    clearInterval(quotaTimer);
    clearInterval(archiveTimer);
    clearInterval(retrospectiveTimer);
    // Requests and deferred receipt writes retain their stores until their
    // final results are durable. run observes beginShutdown at safe boundaries.
    if (activeRequests > 0) await new Promise<void>((resolve) => { requestsDrained = resolve; });
    await recovery;
    await gates.resumedRunsSettled();
    archiveSweep();
    await panes.shutdown();
    store.event("daemon_stopped", { pid: process.pid });
    await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
    await new Promise<void>((resolve, reject) => terminalServer.close((error) => error ? reject(error) : resolve()));
    gates.close(); store.close();
    if (existsSync(terminalSocket)) unlinkSync(terminalSocket);
    rmdirSync(terminalDirectory);
    // Only this server's successfully bound endpoint and PID record are removed.
    if (existsSync(socket)) unlinkSync(socket);
    unlinkSync(join(root, "daemon.pid"));
  };
  const validateArrangement = async (input: any, task = input.task, project = input.project) => {
    const arrangement = input.arrangement, ids = new Set<string>();
    const opened = new Set(store.openPanes().map(p => p.launch));
    const taskStatus = task ? await gates.call({ command: "status", task: task }) : null;
    if (task && !taskStatus?.ok) throw new Refusal("unknown_task");
    const visit = (node: any, depth = 0) => {
      if (depth > 64) throw new Refusal("invalid_pane_arrangement");
      if (typeof node === "string") {
        const record = panes.launchRecord(node);
        if (ids.has(node) || !opened.has(node) ||
            (task ? record.task !== task && !(record.role === "shell" && record.project === taskStatus?.task?.project_id) :
              project ? record.role !== "shell" || record.project !== project : record.role !== "shell" || record.project !== null)) {
          throw new Refusal("invalid_pane_arrangement");
        }
        ids.add(node); return;
      }
      if (!node || !["right", "down"].includes(node.direction)) throw new Refusal("invalid_pane_arrangement");
      visit(node.first, depth + 1); visit(node.second, depth + 1);
    };
    if (!arrangement || typeof arrangement !== "object") throw new Refusal("invalid_pane_arrangement");
    if (arrangement.tree !== null) visit(arrangement.tree);
    if (!arrangement.names || typeof arrangement.names !== "object" || Array.isArray(arrangement.names) ||
        Object.entries(arrangement.names).some(([id, name]) => !ids.has(id) || typeof name !== "string" || !name.trim() || name.length > 100)) {
      throw new Refusal("invalid_pane_name");
    }
    return { scope: task ? `task:${task}` : project ? `project:${project}` : "free", arrangement };
  };
  // T-121: a CLI the user started in a project terminal. Its own identity commands
  // always work; everything else is a gate command under the role the user approved,
  // limited by command name to those whose project can be checked here: task commands
  // on a task of this project, the commands that prepare a new task, and inbox_ready
  // for this project. Inbox entries and stop carry no project yet and ignore a task
  // field, so a terminal role cannot reach them (it would see, acknowledge or stop
  // another project's work).
  // The gate records a terminal controller's answers as the controller's, and run and attach
  // carry its identity so the work they started outlives the role (T-124).
  const taskCommands = new Set<string>(A2AGateRequest.fields.command.literals);
  const terminalCommand = async (input: Record<string, any>, terminal: { id: string; project: string | null; task: string | null },
    asker: Asker) => {
    if (input.command === "terminal_whoami") {
      const held = roleRequests.approved(terminal.id);
      return { ok: true, terminal: terminal.id, project: terminal.project, role: held?.role ?? null,
        role_requests: roleRequests.all().filter(roleRequest => roleRequest.launch === terminal.id) };
    }
    if (input.command === "role_request") {
      // A request lives only while its asker waits on this connection, so it can
      // never be approved after the agent stopped listening.
      if (!Number.isSafeInteger(input.wait_seconds) || input.wait_seconds < 1 || input.wait_seconds > 600) throw new Refusal("invalid_wait_seconds");
      const requested = roleRequests.request(terminal, input.role, input.cli, { session: input.native_session, home: input.native_home });
      const state = () => roleRequests.all().find(row => row.id === requested.id)!;
      // The connection closing (any signal, including SIGKILL) settles the request at
      // once: a pending one is withdrawn, and a grant the asker never received ends.
      asker.gone = () => {
        const current = state();
        if (current.state === "pending") roleRequests.withdraw(terminal.id, requested.id, "asker_gone");
        else if (current.state === "granted") roleRequests.end(terminal.id, "asker_gone");
      };
      try {
        const deadline = Date.now() + input.wait_seconds * 1000;
        for (;;) {
          const current = state();
          // The asker confirms with role_request_confirm; until then the grant has no authority.
          if (current.state === "granted") return { ok: true, role_request: current, confirm_within_ms: confirmWindowMs };
          if (current.state !== "pending") return { ok: false, error: current.ended_reason ?? "request_" + current.state, role_request: current };
          const reason = stopping ? "daemon_stopping" : Date.now() >= deadline ? "request_wait_timeout" : null;
          if (reason) return { ok: false, error: reason, role_request: roleRequests.withdraw(terminal.id, requested.id, reason) };
          await new Promise(resolve => setTimeout(resolve, 200));
        }
      } finally { asker.gone = undefined; }
    }
    if (input.command === "role_request_confirm") {
      const confirmed = roleRequests.confirm(terminal.id, input.role_request);
      if (!confirmed) throw new Refusal("request_not_granted");
      return { ok: true, role_request: confirmed };
    }
    if (input.command === "role_release") {
      const ended = roleRequests.end(terminal.id, "released");
      if (!ended) throw new Refusal("no_role");
      return { ok: true, role_request: ended };
    }
    // T-133, T-107: an event from the Enchanted plugin's hooks in this terminal's CLI. Kept only while the terminal
    // holds an approved role and the event comes from the session that asked for it; anything else is dropped
    // unrecorded, so an ordinary terminal's prompts never reach the records.
    if (input.command === "terminal_hook") {
      const held = roleRequests.approved(terminal.id);
      let payload: any;
      try { payload = JSON.parse(String(input.raw_stdin)); } catch { return { ok: true, kept: false }; }
      // T-195: the session this terminal's CLI process names in its hooks, with or without a role, for the copied link.
      if ((input.cli === "claude" || input.cli === "codex") && Number.isSafeInteger(input.cli_pid) && typeof payload?.session_id === "string" && payload.session_id)
        panes.noteShellHook(terminal.id, { cli: input.cli, pid: input.cli_pid, session: payload.session_id,
          home: typeof input.native_home === "string" ? input.native_home : null });
      if (!held || !held.native_session || payload?.session_id !== held.native_session) return { ok: true, kept: false };
      // Claude Code asks with AskUserQuestion and reports the answer when the tool returns. Codex asks with
      // request_user_input_async, which returns at once ({"accepted":true}); the user's reply comes back later as a
      // submitted prompt (T-133 probe-04, -05). So the codex shim passes no PostToolUse hook, and that reply ends the wait.
      const codex = held.cli === "codex", name = payload.hook_event_name;
      const tool = payload.tool_name === (codex ? "request_user_input_async" : "AskUserQuestion");
      const state = name === "UserPromptSubmit" ? "running" : name === "PreToolUse" && tool ? "waiting_user_answer"
        : ["PostToolUse", "PostToolUseFailure"].includes(name) && tool ? "running"
        : name === "Stop" || name === "Notification" && payload.notification_type === "idle_prompt" ? "idle" : null;
      if (!state) return { ok: true, kept: false };
      if (name === "UserPromptSubmit") {
        // Codex gives a submission no id of its own: a reply shares its turn_id with the prompt that asked.
        const submission = codex ? payload.turn_id : payload.prompt_id;
        if (typeof payload.prompt !== "string" || typeof submission !== "string" || !submission) return { ok: true, kept: false };
        const reply = codex ? codexQuestionReply(payload.prompt) : null;
        // The whole prompt the user submitted to their controller (T-133 option A); a2a injects nothing into project terminals.
        // A Codex hook call is one submission, so its record gets an id of its own.
        try {
          gates.appendUserInput({ id: randomUUID(), schema: 1, form: reply ? "answer" : "message", text: reply ? reply.text : claudeSubmittedText(payload.prompt) as string,
            target: { project: held.project, task: null, attempt: null, thread: store.launchRecord(terminal.id)!.thread, turn: null, message: null, request: reply?.call ?? null },
            channel: "controller-terminal", reply_to: reply?.call ?? null, certainty: "observed", created_at: new Date().toISOString(),
            source_ref: { event_id: reply?.call ?? submission, label: held.id } },
            `terminal:${terminal.id}:${reply ? reply.call : codex ? randomUUID() : submission}`);
        } catch (error) {
          gates.setUserInputObserverStatus("failed", { reason: String(error) });
          throw error;
        }
      }
      // The user's answer to the controller's own question, as the CLI reports it after the tool returns.
      if (name === "PostToolUse" && tool && typeof payload.tool_use_id === "string" && payload.tool_use_id) {
        const answers = payload.tool_response?.answers;
        const text = answers && typeof answers === "object" && !Array.isArray(answers)
          ? Object.entries(answers).map(([question, answer]) => `${question}：${String(answer)}`).join("\n") : JSON.stringify(payload.tool_response ?? null);
        try {
          gates.appendUserInput({ id: randomUUID(), schema: 1, form: "answer", text,
            target: { project: held.project, task: null, attempt: null, thread: store.launchRecord(terminal.id)!.thread, turn: null, message: null, request: payload.tool_use_id },
            channel: "controller-terminal", reply_to: payload.tool_use_id, certainty: "observed", created_at: new Date().toISOString(),
            source_ref: { event_id: payload.tool_use_id, label: held.id } }, `terminal:${terminal.id}:${payload.tool_use_id}`);
        } catch (error) {
          gates.setUserInputObserverStatus("failed", { reason: String(error) });
          throw error;
        }
      }
      store.event("terminal_turn", { role_request: held.id, session: held.native_session, hook_event_name: name, state,
        prompt_id: typeof payload.prompt_id === "string" ? payload.prompt_id : null, turn_id: typeof payload.turn_id === "string" ? payload.turn_id : null,
        tool_use_id: typeof payload.tool_use_id === "string" ? payload.tool_use_id : null }, terminal);
      return { ok: true, kept: true };
    }
    const roleRequest: RoleRequest | undefined = roleRequests.approved(terminal.id);
    if (!roleRequest) throw new Refusal("approved_role_required");
    // T-193: the role belongs to the terminal, not to the directory it started in. A command names its project (or a
    // task's full id does); without one it is the project the role was granted in. Only an opened project is reachable.
    const target = typeof input.project === "string" ? input.project
      : typeof input.task === "string" && input.task.includes("+") ? input.task.slice(0, input.task.indexOf("+")) : roleRequest.project;
    const opened = store.openedProjects();
    const project = opened.find(row => row.project_id === target);
    // Returned, not thrown: the request loop keeps only a thrown refusal's code, and the controller needs the why.
    if (!project) return { ok: false, error: "project_not_opened", details: { project: target, opened: opened.map(row => row.project_id),
      next: "这个项目没有在工作台里打开：请用户先在工作台打开它的目录，再建卡或派发" } };
    if (input.command === "terminal_open") {
      if (typeof input.cwd !== "string" || !isAbsolute(input.cwd) || !existsSync(input.cwd) || !statSync(input.cwd).isDirectory())
        throw new Refusal("invalid_shell_cwd");
      const cwd = realpathSync(input.cwd);
      const withinProject = [project.repo, ...project.extra_directories].some(root => cwd === root || cwd.startsWith(root.endsWith('/') ? root : root + '/'));
      if (!withinProject) throw new Refusal("terminal_cwd_outside_project");
      return { ok: true, launch: panes.startShell(project.project_id, cwd) };
    }
    if (input.command === "inbox_ready") {
      if (input.project !== target) throw new Refusal("project_required");
    } else if (taskCommands.has(input.command)) {
      if (typeof input.task !== "string") throw new Refusal("task_required");
      // T-123: the gate resolves the task in the target project (GateActor.project): a bare name never reaches
      // another project's task of the same name, and a full id beside a different project is refused (task_project_mismatch).
      if (input.command === "create" && input.project !== target) throw new Refusal("project_required");
    } else throw new Refusal("role_command_not_scoped");
    const { parent_launch: _parent, ...gateInput } = input;
    // Workers this call starts belong to the terminal that holds the role.
    const result = await createGate(gateInput, command => panes.parentLaunch.run(terminal.id, () => gates.call(command, undefined, { address: roleRequest.role, project: target,
      assertActive: async () => {
        if (stopping) throw new Refusal("daemon_stopping");
        if (roleRequests.approved(terminal.id)?.id !== roleRequest.id) throw new Refusal("role_request_ended");
      }, controller: terminalController(terminal.id, roleRequest) })));
    return result;
  };
  // An opened directory owns its project id: a task may join that project
  // only in the same repository, or the project's terminals and tasks diverge.
  const assertOpenedRepo = (command: Record<string, any>) => {
    if (command.command !== 'create') return;
    const opened = store.openedProjects().find(project => project.project_id === command.project);
    if (opened && !(typeof command.repo === 'string' && existsSync(command.repo) && realpathSync(command.repo) === opened.repo))
      throw new Refusal('project_repo_mismatch');
  };
  // T-180: a create without a branch gets the default work branch; the result says which and whether it was new.
  const createGate = async (command: Record<string, any>, call: (input: Record<string, any>) => Promise<any>) => {
    assertOpenedRepo(command);
    if (command.command !== 'create' || command.branch !== undefined) return await call(command);
    if (typeof command.repo !== 'string' || !existsSync(command.repo) || typeof command.project !== 'string' || !command.project)
      throw new Refusal('invalid_work_branch');
    const repo = realpathSync(command.repo);
    const { branch, work_branch, made } = await defaultWorkBranch(repo, command.project, store.workBranchPrefix(),
      gates.repoWorkBranch(command.repo));
    let result: any;
    try { result = await call({ ...command, branch }); }
    catch (error) {
      if (made) await dropWorkBranch(repo, made, error instanceof Refusal ? error.code : String(error));
      throw error;
    }
    if (!result?.ok && made) await dropWorkBranch(repo, made, result?.error);
    return result?.ok ? { ...result, work_branch } : result;
  };
  const handle = async (envelope: any, authority: ReturnType<typeof authenticate>, asker: Asker) => {
    const input = envelope.input;
    if (!input || typeof input.command !== "string") throw new Refusal("invalid_request");
    const identity = envelope.identity;
    if (authority.kind === "anonymous" && !readOnly.has(input.command)) throw new Refusal("caller_identity_required");
    if (recovering && !readOnly.has(input.command) && !["daemon_stop", "signal"].includes(input.command)) throw new Refusal("daemon_recovering");
    if (authority.kind === "launch") {
      if (input.command !== "signal") throw new Refusal("worker_requests_require_stop");
    }
    if (authority.kind === "terminal") return await terminalCommand(input, authority.terminal!, asker);
    if (authority.kind === "window" && !["window_input", "window_answer", "window_resize", "window_composition", "window_release", "window_observation", "window_close"].includes(input.command)) {
      throw new Refusal("window_command_forbidden");
    }
    if (input.command === "projects_list") return { ok: true, projects: gates.listProjects() };
    if (input.command === 'execution_settings') return { ok: true, settings: store.executionSettings() };
    // The records and metrics pages (T-133, T-134) read the gate's and the orchestration's records directly.
    if (input.command === 'user_input_records') {
      if (typeof input.project !== 'string' || !input.project) throw new Refusal('invalid_project');
      return { ok: true, records: userInputRecords(store.db, input.project) };
    }
    // T-179: the gate's receipts to a project's sessions, newest first, each with its summary and the full result.
    if (input.command === 'relay_receipts') {
      if (typeof input.project !== 'string' || !input.project) throw new Refusal('invalid_project');
      const rows = store.db.prepare(`SELECT q.key, q.task, q.attempt, q.launch, json_extract(q.input,'$.command') AS command,
        r.data, r.created_at FROM relay_requests q JOIN relay_results r ON r.key=q.key ORDER BY r.created_at DESC`).all() as any[];
      return { ok: true, receipts: rows.filter(row => String(row.task).startsWith(input.project + '+')).map(row => {
        const result = JSON.parse(String(row.data));
        return { key: row.key, task: row.task, attempt: row.attempt, launch: row.launch, role: store.launchRecord(row.launch)?.role ?? null,
          command: row.command, created_at: row.created_at, ok: Boolean(result.ok), summary: receiptLines(row.command, result), result };
      }) };
    }
    if (input.command === 'trajectory_archive') return { ok: true, ...archive.usage() };
    // T-195: a session's CLI, its own session id and record file, for the sidebar's "复制深度链接".
    if (input.command === 'native_link') {
      if (typeof input.launch !== 'string') throw new Refusal('invalid_launch');
      const shell = store.launchRecord(input.launch)?.role === 'shell' && panes.hasLaunch(input.launch) ? await panes.shellNative(input.launch) : null;
      return { ok: true, link: nativeLink(store.db, root, archive, input.launch, homedir(), shell) };
    }
    // T-137: the Reflect page's tree of every controller this project had and the sessions under it.
    if (input.command === 'reflect_tree') {
      if (typeof input.project !== 'string' || !input.project) throw new Refusal('invalid_project');
      const sidebar = await sidebarSnapshot(gates, store, panes, roleRequests);
      return { ok: true, nodes: reflectTree(store.db, roleRequests.all(), input.project,
        new Map(sidebar.agents.map(agent => [agent.id, agent.state]))) };
    }
    if (input.command === 'retrospective_list') {
      if (typeof input.project !== 'string' || !input.project) throw new Refusal('invalid_project');
      return { ok: true, schedule: retrospectives.schedule(),
        runs: retrospectives.runs(input.project).map(run => ({ ...run, events: retrospectives.events(run.id) })),
        suggestions: retrospectives.suggestions(input.project) };
    }
    if (['retrospective_start', 'retrospective_schedule_save', 'retrospective_tick', 'retrospective_decide'].includes(input.command)) {
      if (authority.kind !== 'operator') throw new Refusal('operator_required');
      if (input.command === 'retrospective_start') return { ok: true, run: await startRetrospective(input.project,
        { cli: input.cli, model: input.model, effort: input.effort }, 'manual', null, new Date(),
        input.since !== undefined || input.until !== undefined ? { since: input.since ?? null, until: input.until ?? null } : undefined) };
      if (input.command === 'retrospective_schedule_save') {
        const change = Object.fromEntries(['enabled', 'weekday', 'hour', 'minute', 'cli', 'model', 'effort'].filter(key => input[key] !== undefined).map(key => [key, input[key]]));
        try { return { ok: true, schedule: retrospectives.saveSchedule(change) }; }
        catch (error) { throw new Refusal(String((error as Error).message)); }
      }
      if (input.command === 'retrospective_tick') {
        const now = input.now === undefined ? new Date() : new Date(input.now);
        if (Number.isNaN(now.getTime())) throw new Refusal('invalid_now');
        return { ok: true, ...await retrospectiveTick(now) };
      }
      if (typeof input.suggestion !== 'string' || typeof input.approved !== 'boolean') throw new Refusal('invalid_suggestion_decision');
      try { return { ok: true, suggestion: retrospectives.decide(input.suggestion, input.approved) }; }
      catch (error) { throw new Refusal(String((error as Error).message)); }
    }
    if (input.command === 'metrics') {
      if ([input.project, input.since, input.until].some(value => value != null && typeof value !== 'string')) throw new Refusal('invalid_metrics_range');
      return { ok: true, ...metricsSnapshot(store.db, { project: input.project, since: input.since, until: input.until }) };
    }
    if (input.command === 'work_branch_prefix') return { ok: true, prefix: store.workBranchPrefix() };
    if (input.command === 'work_branch_prefix_save') {
      if (authority.kind !== 'operator') throw new Refusal('operator_required');
      store.event('work_branch_prefix_saved', { prefix: await checkWorkBranchPrefix(input.prefix) });
      return { ok: true, prefix: store.workBranchPrefix() };
    }
    if (input.command === 'execution_settings_save') {
      if (authority.kind !== 'operator') throw new Refusal('operator_required');
      const selection = Object.fromEntries(['model', 'effort', 'fast'].filter(key => input[key] !== undefined).map(key => [key, input[key]]));
      return { ok: true, settings: store.saveExecutionSettings(executionRole(input.role), executionOverrides(selection)) };
    }
    if (input.command === "tasks_list") return { ok: true, tasks: gates.listTasks(input.project) };
    if (input.command === 'flow_snapshot') return { ok: true, ...await flowSnapshot(gates, store, panes, roleRequests) };
    if (input.command === 'sidebar_snapshot') {
      const snapshot = await sidebarSnapshot(gates, store, panes, roleRequests, quota.current());
      // Issue reports waiting for the user's decision, per project (T-132). A task whose issues cannot be read
      // makes its project's count unknown (null) rather than failing the whole sidebar (review 01).
      const projects = await Promise.all(snapshot.projects.map(async (project: any) => {
        let waiting: number | null = 0;
        for (const task of project.tasks) {
          const result = await gates.call({ command: 'issues', task: task.task_id });
          if (!result.ok) { waiting = null; break; }
          waiting += (result.issues ?? []).filter((view: any) => view.state === '等你决定').length;
        }
        return { ...project, issues_waiting: waiting };
      }));
      return { ok: true, ...snapshot, projects };
    }
    // T-177: the user cleans ended sessions out of the sidebar. Only the list changes; a session still running cannot be hidden.
    if (input.command === 'sidebar_hide') {
      if (authority.kind !== 'operator') throw new Refusal('operator_required');
      if (!Array.isArray(input.launches) || !input.launches.length || input.launches.some((launch: unknown) => typeof launch !== 'string' || !launch)) throw new Refusal('invalid_launches');
      const snapshot = await sidebarSnapshot(gates, store, panes, roleRequests, quota.current());
      const rows = input.launches.map((launch: string) => [...snapshot.agents, ...snapshot.terminals].find((row: any) => row.id === launch));
      if (!rows.every(row => row?.state === 'ended')) throw new Refusal('session_not_ended');
      store.event('sidebar_hidden', { launches: input.launches });
      return { ok: true };
    }
    const assertScope = (record: Record<string, any>) => {
      if (record.role === "shell") {
        if ((input.project ?? null) !== record.project) throw new Refusal("launch_project_mismatch");
      } else if (record.task !== input.task) throw new Refusal("launch_task_mismatch");
    };
    if (input.command === 'project_open') {
      if (authority.kind !== 'operator') throw new Refusal('operator_required');
      if (typeof input.repo !== 'string' || !isAbsolute(input.repo) || !statSync(input.repo).isDirectory()) throw new Refusal('invalid_project_directory');
      const repo = realpathSync(input.repo), catalog = await projectCatalog(gates, store);
      // Everything after the await runs synchronously, so a concurrent open
      // sees this registration; reread the opened list instead of the snapshot.
      const opened = store.openedProjects();
      const existing = opened.find(project => project.repo === repo) ?? catalog.find(project => project.repo === repo);
      if (existing) return { ok: true, project: existing.project_id, repo, created: false };
      const restored = [...store.removedProjects()].find(([, removedRepo]) => removedRepo === repo)?.[0];
      if (restored) {
        store.event('project_opened', { project_id: restored, repo });
        return { ok: true, project: restored, repo, created: false };
      }
      const taken = new Set([...catalog.map(row => row.project_id), ...opened.map(row => row.project_id),
        ...gates.listProjects().map((row: any) => String(row.project_id))]);
      // The directory name becomes the project id; gate ids allow [A-Za-z0-9_.-].
      const base = basename(repo).replace(/[^A-Za-z0-9_.-]+/g, '-').replace(/^[^A-Za-z0-9]+/, '').slice(0, 120) || 'project';
      let project = base;
      for (let n = 2; taken.has(project); n++) project = `${base}-${n}`;
      store.event('project_opened', { project_id: project, repo });
      return { ok: true, project, repo, created: true };
    }
    if (input.command === 'project_settings_save') {
      if (authority.kind !== 'operator') throw new Refusal('operator_required');
      const project = store.openedProjects().find(project => project.project_id === input.project);
      if (!project) throw new Refusal('unknown_project');
      if (!Array.isArray(input.extra_directories) || input.extra_directories.some((path: unknown) =>
        typeof path !== 'string' || !isAbsolute(path) || !statSync(path).isDirectory())) throw new Refusal('invalid_extra_directory');
      const directories = [...new Set<string>(input.extra_directories.map((path: string) => realpathSync(path)))];
      if (directories.includes(project.repo)) throw new Refusal('extra_directory_is_project');
      store.event('project_settings_saved', { project_id: project.project_id, extra_directories: directories });
      return { ok: true, ...project, extra_directories: directories };
    }
    if (input.command === 'project_remove') {
      if (authority.kind !== 'operator') throw new Refusal('operator_required');
      // Refusals that carry details are returned, not thrown: the request loop keeps only a thrown refusal's code.
      // T-190: removing only hides the project; tasks and records stay and come back when the directory is opened again.
      const project = (await projectCatalog(gates, store)).find(row => row.project_id === input.project);
      if (!project) throw new Refusal('unknown_project');
      const running = store.openPanes(undefined, input.project).filter(pane => {
        const record = store.launchRecord(pane.launch);
        return record && panes.status(record.thread).lifecycle === 'running';
      });
      if (running.length) return { ok: false, error: 'project_has_running_terminals', details: { count: running.length } };
      const active = [];
      for (const task of project.tasks) {
        const attempt = (await gates.call({ command: 'status', task: task.task_id })).task?.current_attempt;
        if (attempt && !attempt.reclaimed) active.push({ task: task.task_id, attempt: attempt.attempt_id, state: attempt.state });
      }
      if (active.length && input.attempts !== 'keep' && input.attempts !== 'reclaim')
        return { ok: false, error: 'project_has_active_attempts', details: { attempts: active } };
      if (input.attempts === 'reclaim') for (const row of active) {
        const result = await gates.call({ command: 'reclaim', task: row.task, attempt: row.attempt });
        if (!result.ok) return { ok: false, error: 'project_reclaim_failed', details: { ...row, error: result.error, details: result.details } };
      }
      store.event('project_removed', { project_id: input.project, repo: project.repo,
        kept_attempts: input.attempts === 'keep' ? active : [] });
      return { ok: true };
    }
    if (input.command === "role_request_decide") {
      if (authority.kind !== "operator") throw new Refusal("operator_required");
      // T-107: an executor may be put under an ideation controller of its project, a terminal one holding the role
      // or a running managed one.
      const isIdeation = (launch: string, project: string) => {
        const held = roleRequests.approved(launch);
        if (held) return held.role === "ideation" && held.project === project;
        const record = store.launchRecord(launch);
        return record?.role === "controller" && record.preset === "ideation" && record.project === project &&
          panes.status(record.thread).lifecycle === "running";
      };
      return { ok: true, role_request: roleRequests.decide(input.role_request, input.approved, input.parent_launch ?? null, isIdeation) };
    }
    if (input.command === "shell_start") {
      if (authority.kind !== "operator") throw new Refusal("operator_required");
      return { ok: true, launch: panes.startShell(input.project ?? null, input.cwd) };
    }
    if (input.command === "shell_close") {
      if (authority.kind !== "operator") throw new Refusal("operator_required");
      await panes.closeShell(input.launch);
      return { ok: true };
    }
    const layoutScope = input.task ? `task:${input.task}` : input.project ? `project:${input.project}` : "free";
    if (input.command === "pane_layout") return { ok: true, recovering,
      saved: store.hasPaneLayout(input.task, input.project),
      panes: store.openPanes(input.task, input.project).filter(p => !input.free || panes.launchRecord(p.launch).project === null),
      arrangement: store.paneArrangement(layoutScope) };
    if (input.command === "pane_layout_save") {
      if (authority.kind !== "operator") throw new Refusal("operator_required");
      const saved = await validateArrangement(input);
      store.event("pane_arrangement_saved", saved);
      return { ok: true };
    }
    if (["pane_layout_open", "pane_layout_close"].includes(input.command)) {
      if (authority.kind !== "operator") throw new Refusal("operator_required");
      const record = panes.launchRecord(input.launch);
      assertScope(record);
      const saved = input.command === "pane_layout_close" && input.arrangement !== undefined
        ? await validateArrangement(input, input.layout_task, input.layout_task ? undefined : input.project) : null;
      if (input.command === "pane_layout_open") panes.rememberOpen(input.launch, input.position);
      else if (record.role === "shell") await panes.closeShell(input.launch);
      else panes.forgetOpen(input.launch);
      if (saved) store.event("pane_arrangement_saved", saved);
      return { ok: true };
    }
    if (input.command === "window_open") {
      if (authority.kind !== "operator") throw new Refusal("operator_required");
      const record = panes.launchRecord(input.launch);
      assertScope(record);
      const window = { id: randomUUID(), token: randomUUID(), role: record.role, task: record.task, launch: record.id, sequence: 0, requests: new Set<string>() };
      windows.set(window.id, window);
      store.event("window_opened", { window_id: window.id, actor: "user" }, record as any);
      return { ok: true, identity: { kind: "window", window: window.id, token: window.token } };
    }
    if (["window_input", "window_answer", "window_resize", "window_composition", "window_release", "window_observation", "window_close"].includes(input.command)) {
      const window = authority.window;
      if (!window) throw new Refusal("window_identity_required");
      const record = panes.launchRecord(window.launch);
      if (input.command === "window_close") {
        windows.delete(window.id);
        store.event("window_closed", { window_id: window.id }, record as any);
        return { ok: true };
      }
      if (!Number.isSafeInteger(input.sequence) || input.sequence !== window.sequence + 1 ||
          typeof input.request_id !== "string" || !input.request_id || input.request_id.length > 128) throw new Refusal("invalid_window_sequence");
      if (window.requests.has(input.request_id)) throw new Refusal("window_request_reused");
      const receipt = { window_id: window.id, sequence: input.sequence, request_id: input.request_id, received_at: new Date().toISOString() };
      // Consume both identifiers before any await. Failed/unknown operations
      // cannot be replayed, and later completions cannot move the sequence back.
      window.requests.add(input.request_id);
      window.sequence = input.sequence;
      if (record.role !== "shell") store.event("window_request_admitted", { ...receipt, command: input.command }, record as any);
      const encoding = input.encoding ?? "utf8";
      if (input.command === "window_input" && (!["utf8", "binary"].includes(encoding) || typeof input.data !== "string" ||
          (encoding === "binary" ? input.data.length : Buffer.byteLength(input.data, "utf8")) > 1024 * 1024 ||
          (encoding === "binary" && [...input.data].some(char => char.charCodeAt(0) > 255)))) throw new Refusal("invalid_terminal_input");
      if (input.command === "window_resize") {
        if (!Number.isInteger(input.cols) || input.cols < 2 || input.cols > 1000 || !Number.isInteger(input.rows) || input.rows < 1 || input.rows > 1000) throw new Refusal("invalid_terminal_size");
        const pane = panes.byLaunch(record.id);
        if (pane.stopped || pane.archived || pane.failed || pane.closing) throw new Refusal("pane_unavailable");
        pane.pty.resize(input.cols, input.rows);
        return { ok: true };
      }
      if (record.role === "shell") {
        if (input.command === "window_composition") return { ok: true, observed: true, written: false };
        if (input.command === "window_observation") {
          if (input.type !== "focus-mode-intercept" || typeof input.raw_sequence !== "string" || input.raw_sequence.length > 4096) {
            throw new Refusal("invalid_window_observation");
          }
          return { ok: true, observed: true, written: false };
        }
        if (input.command !== "window_input") throw new Refusal("shell_input_only");
        await panes.shellInput(record.id, input.data, encoding, async () => {
          if (windows.get(window.id) !== window) throw new Refusal("invalid_window_identity");
        });
        return { ok: true, written: input.data.length > 0, request_id: receipt.request_id };
      }
      if (input.command === "window_observation") {
        if (input.type !== "focus-mode-intercept" || typeof input.raw_sequence !== "string" || input.raw_sequence.length > 4096) {
          throw new Refusal("invalid_window_observation");
        }
        store.event("terminal_focus_intercepted", { ...receipt, raw_sequence: input.raw_sequence }, record as any);
        return { ok: true };
      }
      const assertCurrent = async () => {
        if (windows.get(window.id) !== window) throw new Refusal("invalid_window_identity");
        const status = await gates.call({ command: "status", task: record.task });
        const attempt = status.task?.current_attempt;
        if(record.role==="controller" && record.attempt===null){
          const pane=panes.get(record.thread),info=await panes.processInfo(record.thread);
          if(status.task?.task_id!==record.task || status.task?.spec_rev!==record.spec_rev || pane.record.id!==record.id ||
              pane.native!==record.session || pane.failed || pane.stopped || pane.archived || !info.leader || info.failed)throw new Refusal("stale_controller");
        }else if (!attempt || attempt.attempt_id !== record.attempt || attempt.session_id !== record.session ||
            attempt.fence !== record.fence || status.task?.spec_rev !== record.spec_rev || attempt.reclaimed) throw new Refusal("stale_attempt");
        if (windows.get(window.id) !== window) throw new Refusal("invalid_window_identity");
        if (gates.userInputObserverStatus()?.state === "failed") throw new Refusal("user_input_observer_failed");
      };
      const recordInput = async (text: string, content?: Record<string, unknown>, question?: string) => {
        try {
          gates.appendUserInput({ id: randomUUID(), schema: 1, form: question ? "answer" : content ? "action" : "message", text,
            target: { project: record.project, task: record.task, attempt: record.attempt, thread: record.thread,
              turn: panes.get(record.thread).turn, message: null, request: question ?? null },
            channel: "terminal-window", reply_to: question ?? null, certainty: "observed", created_at: receipt.received_at,
            source_ref: { command_id: receipt.request_id, source_sequence: receipt.sequence, window_id: receipt.window_id },
            ...(content ? { content } : {}) }, `window:${receipt.window_id}:${receipt.request_id}`);
        } catch (error) {
          gates.setUserInputObserverStatus("failed", { reason: String(error) });
          throw error;
        }
      };
      if (input.command === 'window_answer') {
        if (typeof input.question !== 'string' || !input.question || !Array.isArray(input.answers)) throw new Refusal('invalid_question_answer');
        const answer = await panes.answerQuestion(window.launch, input.question, input.answers,
          (text, question) => recordInput(text, undefined, question), assertCurrent);
        return { ok: true, written: true, confirmed: answer.confirmed, request_id: receipt.request_id };
      }
      if (input.command === "window_composition") {
        await panes.beginComposition(window.launch, receipt, assertCurrent);
        return { ok: true, observed: true, written: false };
      }
      if (input.command === "window_release") {
        const declaration = input.declaration;
        if (!declaration || declaration.window_id !== window.id) throw new Refusal("empty_input_declaration_required");
        const assertInterrupted = async () => {
          await assertCurrent();
          if (!panes.get(record.thread).interrupted) throw new Refusal("pane_not_interrupted");
        };
        await panes.releaseByUser(record.thread, declaration, async () => {
          const pane = panes.get(record.thread);
          await recordInput("用户声明输入框已空", { action: "queue-release", declaration, previous_submission: pane.active?.id ?? null,
            queued: pane.queue.map(item => item.id) });
        }, assertInterrupted);
        return { ok: true, released: true, request_id: receipt.request_id };
      }
      if (input.data.length === 0) {
        store.event("terminal_input_empty", { ...receipt, byte_length: 0 }, record as any);
        return { ok: true, observed: true, written: false };
      }
      await panes.userInput(window.launch, input.data, receipt,
        (text, control) => recordInput(text, encoding === "binary" ? { action: "terminal-binary",
          data_base64: Buffer.from(input.data, "latin1").toString("base64") } : control ? { action: "terminal-key", data: input.data } : undefined),
        assertCurrent, encoding);
      return { ok: true, written: true, request_id: receipt.request_id };
    }
    if (input.command === "daemon_status") return { ok: true, pid: process.pid, node: process.version, root, helper };
    if (input.command === "scores_validate") {
      try {
        if (typeof input.file !== "string" || !isAbsolute(input.file) || !statSync(input.file).isFile()) throw new Refusal("invalid_path");
        const rows = scoreRecords(new TextDecoder("utf-8", { fatal: true }).decode(readFileSync(input.file)));
        return { ok: true, schema: 1, records: rows.length, imported: false };
      } catch (error) {
        if (error instanceof QualityProtocolError) return { ok: false, error: "invalid_scores", details: { field: error.field } };
        if ((error as NodeJS.ErrnoException).code === "ERR_ENCODING_INVALID_ENCODED_DATA") return { ok: false, error: "invalid_scores", details: { field: "encoding" } };
        if (["ENOENT", "EACCES", "EISDIR", "ENOTDIR", "ELOOP"].includes((error as NodeJS.ErrnoException).code ?? "")) return { ok: false, error: "local_io_failed", details: String(error) };
        throw error;
      }
    }
    if (input.command === "controller_prepare") {
      if (authority.kind !== "operator") throw new Refusal("operator_required");
      const status = await gates.call({ command: "status", task: input.task });
      if (!status.ok || !status.task) return status;
      const selection = Object.fromEntries(['model', 'effort', 'fast'].filter(key => input[key] !== undefined).map(key => [key, input[key]]));
      return { ok: true, prepared: panes.prepareControllerLaunch(status.task, input.preset, input.parent_launch, executionOverrides(selection)) };
    }
    if (input.command === "controller_start") {
      if (authority.kind !== "operator") throw new Refusal("operator_required");
      const status = await gates.call({ command: "status", task: input.task });
      if (!status.ok || !status.task) return status;
      if (input.manifest?.state !== root) throw new Refusal("controller_state_mismatch");
      const overrides = Object.fromEntries(['model', 'effort', 'fast'].filter(key => input[key] !== undefined).map(key => [key, input[key]]));
      const launch = await panes.startController(status.task, { ...input.manifest,
        execution: executionOverrides({ ...input.manifest.execution, ...overrides }) });
      gates.registerController(launch.thread);
      await gates.resumeControllerInbox(launch.thread);
      return { ok: true, launch };
    }
    if (input.command === "daemon_stop") {
      stopping = true;
      gates.beginShutdown();
      return { ok: true, pid: process.pid, stopping: true };
    }
    if (input.command === "orchestration_events") return { ok: true, events: store.read(input.task) };
    if (input.command === "pane_output") return { ok: true, ...panes.output(input.launch, input.offset, input.max_bytes) };
    if (input.command === "workbench_snapshot") {
      if (input.launch) {
        const shell = panes.launchRecord(input.launch);
        if (shell.role === "shell") {
          assertScope(shell);
          return { ok: true, daemon, recovering, task: null, launch: shell, pane: panes.status(shell.thread), user_input_observer: null };
        }
      }
      const result = await gates.call({ command: "status", task: input.task });
      if (!result.ok || !result.task) return result;
      const record = input.launch ? panes.launchRecord(input.launch) :
        result.task.current_attempt?.thread_id ? store.threadLaunch(result.task.current_attempt.thread_id) : undefined;
      if (record && record.task !== result.task.task_id) throw new Refusal("launch_task_mismatch");
      const pane = record ? panes.status(record.thread) : null;
      const launch = record ? { id: record.id, project: record.project, task: record.task, attempt: record.attempt,
        session: record.session, fence: record.fence, spec_rev: record.spec_rev, thread: record.thread,
        role: record.role, preset: record.preset ?? null,
        // A restored pane runs the CLI installed now; history keeps the launch-time version.
        cli_version: panes.panes.get(record.thread)?.record.cli_version ?? record.cli_version, model_requested: record.model_requested,
        effort_requested: record.effort_requested, created_at: record.created_at } : null;
      return { ok: true, daemon, recovering, task: result.task, launch, pane,
        questions: record ? panes.questions(record.id) : [], user_input_observer: result.user_input_observer };
    }
    if (input.command === "pane_status") return { ok: true, ...panes.status(input.thread) };
    if (input.command === "pane_process_info") return { ok: true, ...await panes.processInfo(input.thread) };
    if (input.command === "pane_screen_key") {
      if (authority.kind!=="operator") throw new Refusal("operator_required");
      return {ok:true,...await panes.screenKey(input.thread,input,authority.source)};
    }
    if (input.command === "pane_dispatch") return { ok: true, dispatch: await panes.parentLaunch.run(
      authority.kind === "operator" ? input.parent_launch ?? null : null, () => panes.dispatch(panes.get(input.thread), input.body)) };
    if (input.command === "signal") {
      if (!identity || identity.launch !== input.launch) throw new Refusal("signal_identity_required");
      let completedReview: { task: string; id: string } | undefined;
      const decision = await panes.signal(input.launch, input.raw_stdin, input.received_at, async (pane, stop, matched) => {
        let files = input.relay_files;
        if (pane.record.role === "reviewer") {
          if (!matched) return;
          let request: Record<string, any>;
          try { request = reviewRequest(stop.last_assistant_message); }
          catch (error) {
            if (!(error instanceof QualityProtocolError)) throw error;
            // The same caller identity as the normal path: a Claude reviewer is checked by its prompt id (T-129).
            const caller = await panes.caller({ ...identity, native_session: stop.session_id, prompt_id: stop.prompt_id });
            await gates.failReviewProtocol(pane.record.task, pane.record.review_id,
              { error: error.field, raw: stop.last_assistant_message, stop }, caller);
            pane.failed = "invalid_review_result";
            return;
          }
          files = [writeReviewRequest(pane.record.request_dir, request)];
        }
        if (!Array.isArray(files)) throw new Refusal("relay_files_required");
        const receipts = [];
        for (const file of files) {
          const controller = pane.record.role === "controller";
          const binding = controller ? { id: pane.record.id, task: pane.record.task, session: pane.record.session,
            spec_rev: pane.record.spec_rev, role: "controller" as const, preset: pane.record.preset,
            project: pane.record.project, native_session: stop.session_id, prompt_id: stop.prompt_id } : pane.record;
          const receipt = await relay.receive(binding as any, file, matched, async (command) => {
            const caller = await panes.caller({ ...identity, native_session: stop.session_id, prompt_id: stop.prompt_id });
            if (command.command.startsWith("inbox_") || controller) {
              const assertNative = caller.assertActive;
              // Native liveness alone does not preserve a revoked attempt's
              // authority. Recheck the credential's bound attempt after each
              // native check, including checks performed inside the inbox gate.
              caller.assertActive = async () => {
                await assertNative();
                const current = await gates.call({ command: "status", task: pane.record.task });
                if (controller) {
                  if (!current.ok || current.task?.task_id !== pane.record.task || current.task?.project_id !== pane.record.project ||
                      current.task?.spec_rev !== pane.record.spec_rev) throw new Refusal("stale_controller_launch");
                  return;
                }
                const active = current.task?.current_attempt;
                const bound = pane.record;
                if (!active || active.attempt_id !== bound.attempt || active.session_id !== bound.session ||
                    active.fence !== bound.fence || current.task?.spec_rev !== bound.spec_rev || active.reclaimed) {
                  throw new Refusal("stale_attempt");
                }
              };
            }
            await caller.assertActive();
            if (command.command === "issue") return await gates.raiseIssue({ title: command.title, body: command.body,
              blocking: command.blocking ?? false, refs: command.refs ?? [] }, caller);
            if (command.command === "status") {
              const result = await gates.call({ command: "status", task: command.task });
              const attempt = result.task?.current_attempt;
              if (!attempt || attempt.attempt_id !== command.attempt || attempt.session_id !== command.session ||
                  attempt.fence !== command.fence || result.task?.spec_rev !== command.spec_rev) throw new Refusal("stale_attempt");
              return result;
            }
            return await createGate(command, input => panes.parentLaunch.run(controller ? pane.record.id : null, () => gates.call(input, caller)));
          });
          if (!receipt.replayed && !isPendingInboxResult(receipt.result)) receipts.push(receipt);
          if (pane.record.role === "reviewer" && !receipt.replayed) {
            if (receipt.result.ok) completedReview = { task: pane.record.task, id: pane.record.review_id };
            else {
              const caller = await panes.caller({ ...identity, native_session: stop.session_id, prompt_id: stop.prompt_id });
              await gates.failReviewProtocol(pane.record.task, pane.record.review_id, { receipt, stop }, caller);
              pane.failed = "review_rejected";
            }
          }
        }
        if (matched && receipts.length && ["worker", "controller"].includes(pane.record.role)) await panes.dispatch(pane, feedbackText(receipts, pane.record.role), "gate");
      });
      const payload = JSON.parse(input.raw_stdin);
      if (payload.hook_event_name === "Stop") archiveSweep(input.launch);
      if (payload.hook_event_name === "UserPromptSubmit" && !decision) {
        const pane = panes.authenticate(identity);
        if (pane.record.role === "controller" && pane.claudePromptId === payload.prompt_id) {
          const current = await gates.call({ command: "status", task: pane.record.task });
          if (!current.ok || current.task?.spec_rev !== pane.record.spec_rev || current.task?.project_id !== pane.record.project)
            throw new Refusal("stale_controller_launch");
          writeControllerContext(pane.record.env.A2A_REQUEST_DIR, { schema: 2, launch: pane.record.id,
            preset: pane.record.preset, project: pane.record.project, task: pane.record.task, session: pane.record.session,
            spec_rev: pane.record.spec_rev, native_session: payload.session_id, prompt_id: payload.prompt_id });
        }
      }
      return { ok: true, completedReview, ...(decision ? { hook_output: decision } : {}) };
    }
    if (input.command === "launch_show") {
      if (authority.kind === "launch" && identity.launch !== input.launch) throw new Refusal("stale_launch");
      return { ok: true, ...panes.launchInfo(input.launch) };
    }
    // Since T-126 only the desktop app holds the operator credential, so an issue disposition it sends is the
    // user's own (T-132): the gate lets only the user close a blocking issue.
    const actor = authority.kind === "operator" ? { address: input.command === "disposition" ? "user" : "executor",
      assertActive: async () => { if (stopping) throw new Refusal("daemon_stopping"); } } : undefined;
    const { parent_launch, ...gateInput } = input;
    return await createGate(gateInput, command => panes.parentLaunch.run(authority.kind === "operator" ? parent_launch ?? null : null,
      () => gates.call(command, undefined, actor)));
  };
  // Two sockets share one handler. The terminal socket (T-126) is the only one a project terminal is told about; it
  // takes terminal identities only, so nothing a terminal can read lets it act as the operator or a window.
  const serveConnection = (terminalOnly: boolean) => (connection: import("node:net").Socket) => {
    connection.setEncoding("utf8");
    let buffer = "", handled = false;
    // A role request waits on its connection; the asker going away settles it.
    const asker: Asker = {};
    connection.once("close", () => {
      // Same handling as a request whose event write fails: record it, keep serving.
      try { asker.gone?.(); }
      catch (error) {
        gates.setUserInputObserverStatus("failed", { reason: String(error) });
        console.error(JSON.stringify({ error: "role_request_settle_failed", reason: String(error) }));
      }
    });
    connection.on("error", (error) => {
      store.event("client_connection_error", { error: String(error) });
    });
    connection.on("data", async (chunk) => {
      if (handled) return;
      buffer += chunk;
      if (buffer.length > 4 * 1024 * 1024) { handled = true; connection.end(JSON.stringify({ ok: false, error: "request_too_large" }) + "\n"); return; }
      const end = buffer.indexOf("\n");
      if (end < 0) return;
      handled = true;
      if (stopping) { connection.end(JSON.stringify({ ok: false, error: "daemon_stopping" }) + "\n"); return; }
      activeRequests++;
      let envelope: any;
      let result: any;
      let unlogged = false;
      try {
        envelope = JSON.parse(buffer.slice(0, end));
        // A hook event carries the prompt itself; the terminal_hook command decides whether to keep it.
        unlogged = isShellInput(envelope) || envelope?.input?.command === "terminal_hook" && envelope?.identity?.kind === "terminal";
        // Checked before authenticating, so this socket never tells whether another kind of identity is valid.
        if (terminalOnly && envelope?.identity?.kind !== "terminal") throw new Refusal("terminal_socket_terminal_only");
        const authority = authenticate(envelope.identity);
        const catalogRead = catalogCommands.has(envelope.input?.command);
        const viewing = catalogRead || ["workbench_snapshot", "pane_output"].includes(envelope.input?.command);
        if (!viewing && !unlogged) store.event("request_received", { id: envelope.id, input: eventInput(envelope.input), source: authority.source });
        result = await handle(envelope, authority, asker);
        if (result.ok && ["controller_start", "window_release", "signal"].includes(envelope.input.command)) {
          await settleInboxFeedback();
        }
        if (!catalogRead && !unlogged && (!viewing || !result.ok)) store.event("request_result", { id: envelope.id, command: envelope.input.command,
          ok: result.ok, error: result.error, details: result.details });
      } catch (error) {
        const processQuery = (error as { process_query?: unknown })?.process_query;
        result = { ok: false, error: error instanceof Refusal ? error.code : "orchestration_failed", details: String(error),
          ...(processQuery ? { diagnostics: { process_query: processQuery } } : {}) };
        try { if (!unlogged && !catalogCommands.has(envelope?.input?.command)) store.event("request_rejected", { id: envelope?.id, input: eventInput(envelope?.input), result,
          ...(terminalOnly ? { socket: "terminal" } : {}) }); }
        catch (recordError) {
          gates.setUserInputObserverStatus("failed", { reason: String(recordError) });
          result = { ok: false, error: "event_write_failed", details: String(recordError) };
        }
      } finally { activityFinished(); }
      connection.end(JSON.stringify(explained(result)) + "\n");
      if (result.ok && envelope?.input.command === "signal") {
        connection.once("close", () => {
          if (stopping) return;
          const pane = panes.byLaunch(envelope.input.launch);
          activeRequests++;
          (async () => {
            await panes.drain(pane);
            await settleInboxFeedback();
            if (result.completedReview) await gates.reclaimReview(result.completedReview.task, result.completedReview.id);
          })().catch((error) => {
            pane.failed = String(error); pane.state = "unknown";
            store.event("queue_stopped", { error: String(error) }, pane.record);
          }).finally(activityFinished);
        });
      }
      if (result.ok && envelope?.input.command === "daemon_stop") {
        // Let the response socket close before closing the listening server.
        connection.once("close", () => shutdown().catch((error) => { console.error(error); process.exitCode = 1; }));
      }
    });
  };
  // T-187: an agy or opencode turn ends when the CLI reports it to its terminal (OSC 7501), not in a Stop hook. The
  // backend ends it as a Stop hook would: the same signal command under the pane's own launch identity, with the
  // worker's request files read the way the hook command reads them, then the same drain and review reclaim.
  panes.reportedTurnEnd = async (pane, stop) => {
    activeRequests++;
    try {
      const envelope = { id: randomUUID(), identity: { launch: pane.record.id, token: pane.token },
        input: { command: "signal", launch: pane.record.id, raw_stdin: JSON.stringify(stop), received_at: new Date().toISOString(),
          ...(pane.record.role === "reviewer" ? {} : { relay_files: readWorkerRequests(pane.record.request_dir) }) } };
      const authority = authenticate(envelope.identity);
      store.event("request_received", { id: envelope.id, input: eventInput(envelope.input), source: authority.source });
      const result = await handle(envelope, authority, {});
      store.event("request_result", { id: envelope.id, command: "signal", ok: result.ok, error: result.error, details: result.details });
      await settleInboxFeedback();
      if (stopping) return;
      await panes.drain(pane);
      await settleInboxFeedback();
      if (result.completedReview) await gates.reclaimReview(result.completedReview.task, result.completedReview.id);
    } finally { activityFinished(); }
  };
  const server = createServer(serveConnection(false));
  const terminalServer = createServer(serveConnection(true));
  // A private directory with a random name: its path says nothing about the daemon's data directory.
  const terminalDirectory = mkdtempSync(join(tmpdir(), "enchanted-"));
  const terminalSocket = join(terminalDirectory, "terminal.sock");
  try {
    if (Buffer.byteLength(terminalSocket) > 103) throw new Error("terminal socket path exceeds 103 bytes");
    await new Promise<void>((resolve, reject) => { terminalServer.once("error", reject); terminalServer.listen(terminalSocket, resolve); });
    chmodSync(terminalSocket, 0o600);
    panes.terminalSocket = terminalSocket;
    await new Promise<void>((resolve, reject) => { server.once("error", reject); server.listen(socket, resolve); });
    chmodSync(socket, 0o600);
    writeFileSync(join(root, "daemon.pid"), String(process.pid) + "\n", { flag: "wx", mode: 0o600 });
  } catch (error) {
    // Nothing in the data directory names this directory, so no later start could remove it.
    rmSync(terminalDirectory, { recursive: true, force: true });
    throw error;
  }
  gates.recoverReviews();
  recovery = panes.recover(daemon).finally(() => { recovering = false; });
  void recovery.catch(error => gates.setUserInputObserverStatus("failed", { reason: String(error) }));
  // Runs resume once the previous daemon's panes are restored or confirmed gone (T-124).
  void recovery.then(() => gates.resumeRuns(controllerOf), () => undefined);
  store.event("daemon_started", { daemon, pid: process.pid, ppid: process.ppid, argv: process.argv, helper, node: process.version });
  process.send?.({ ok: true, pid: process.pid, root, helper });
}

if (import.meta.main) {
  try {
    if (process.env.A2A_CLAUDE_LOGIN_SESSION) {
      const session = JSON.parse(readFileSync(process.env.A2A_CLAUDE_LOGIN_SESSION, "utf8"));
      if (session.c_root_pid !== process.pid || session.manifest.state !== process.argv[2]) throw new Error("prepared_login_daemon_mismatch");
      process.env.A2A_OPERATOR_CREDENTIAL = join(session.manifest.root, "operator.json");
      createOperatorCredential(session.manifest.state);
    }
    await serve(process.argv[2]!, JSON.parse(process.argv[3] ?? "{}"));
  }
  catch (error) { console.error(error); process.exit(1); }
}
