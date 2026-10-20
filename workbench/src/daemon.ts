import { createServer } from "node:net";
import { chmodSync, existsSync, mkdirSync, readFileSync, realpathSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import { A2AGates, Refusal } from "./gates/core.ts";
import { OrchestrationStore } from "./store.ts";
import { Panes, spawnHelper, type LaunchConfig } from "./panes.ts";
import { socketPath } from "./transport.ts";
import { RequestRelay, isPendingInboxResult } from "./relay.ts";
import { writeReviewRequest, writeControllerContext } from "./relayFiles.ts";
import { reviewRequest, scoreRecords, QualityProtocolError } from "./gates/qualityProtocol.ts";
import { randomUUID } from "node:crypto";
import { createOperatorCredential, readOperatorCredential } from "./credentials.ts";
import { sidebarSnapshot } from './sidebar.ts';

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
  const relay = new RequestRelay(store);
  const feedbackText = (receipts: unknown[]) =>
    "本回合的异步请求处理结果如下。请仅确认收到并结束；不调用工具、不改文件、不新增请求。\n" + JSON.stringify(receipts, null, 2);
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
      const dispatch = await panes.dispatch(pane, feedbackText([final]), "gate");
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
  const catalogCommands = new Set(["projects_list", "tasks_list", "sidebar_snapshot"]);
  const readOnly = new Set([...catalogCommands, "daemon_status", "orchestration_events", "pane_output", "workbench_snapshot",
    "pane_layout", "pane_status", "pane_process_info", "launch_show", "status", "events", "issues", "card_show", "card_template", "card_validate"]);
  const authenticate = (identity: any): { source: string; kind: "operator" | "window" | "launch" | "anonymous"; window?: WindowBinding } => {
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
    // Requests and deferred receipt writes retain their stores until their
    // final results are durable. run observes beginShutdown at safe boundaries.
    if (activeRequests > 0) await new Promise<void>((resolve) => { requestsDrained = resolve; });
    await recovery;
    await panes.shutdown();
    store.event("daemon_stopped", { pid: process.pid });
    await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
    gates.close(); store.close();
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
  const handle = async (envelope: any, authority: ReturnType<typeof authenticate>) => {
    const input = envelope.input;
    if (!input || typeof input.command !== "string") throw new Refusal("invalid_request");
    const identity = envelope.identity;
    if (authority.kind === "anonymous" && !readOnly.has(input.command)) throw new Refusal("caller_identity_required");
    if (recovering && !readOnly.has(input.command) && !["daemon_stop", "signal"].includes(input.command)) throw new Refusal("daemon_recovering");
    if (authority.kind === "launch") {
      if (input.command !== "signal") throw new Refusal("worker_requests_require_stop");
    }
    if (authority.kind === "window" && !["window_input", "window_resize", "window_composition", "window_release", "window_observation", "window_close"].includes(input.command)) {
      throw new Refusal("window_command_forbidden");
    }
    if (input.command === "projects_list") return { ok: true, projects: gates.listProjects() };
    if (input.command === "tasks_list") return { ok: true, tasks: gates.listTasks(input.project) };
    if (input.command === 'sidebar_snapshot') return { ok: true, ...await sidebarSnapshot(gates, store, panes) };
    const assertScope = (record: Record<string, any>) => {
      if (record.role === "shell") {
        if ((input.project ?? null) !== record.project) throw new Refusal("launch_project_mismatch");
      } else if (record.task !== input.task) throw new Refusal("launch_task_mismatch");
    };
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
    if (["window_input", "window_resize", "window_composition", "window_release", "window_observation", "window_close"].includes(input.command)) {
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
      const recordInput = async (text: string, content?: Record<string, unknown>) => {
        try {
          gates.appendUserInput({ id: randomUUID(), schema: 1, form: content ? "action" : "message", text,
            target: { project: record.project, task: record.task, attempt: record.attempt, thread: record.thread,
              turn: panes.get(record.thread).turn, message: null, request: null },
            channel: "terminal-window", reply_to: null, certainty: "observed", created_at: receipt.received_at,
            source_ref: { command_id: receipt.request_id, source_sequence: receipt.sequence, window_id: receipt.window_id },
            ...(content ? { content } : {}) }, `window:${receipt.window_id}:${receipt.request_id}`);
        } catch (error) {
          gates.setUserInputObserverStatus("failed", { reason: String(error) });
          throw error;
        }
      };
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
      return { ok: true, prepared: panes.prepareControllerLaunch(status.task, input.preset, input.parent_launch) };
    }
    if (input.command === "controller_start") {
      if (authority.kind !== "operator") throw new Refusal("operator_required");
      const status = await gates.call({ command: "status", task: input.task });
      if (!status.ok || !status.task) return status;
      if (input.manifest?.state !== root) throw new Refusal("controller_state_mismatch");
      const launch = await panes.startController(status.task, input.manifest);
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
      if (record && record.task !== input.task) throw new Refusal("launch_task_mismatch");
      const pane = record ? panes.status(record.thread) : null;
      const launch = record ? { id: record.id, project: record.project, task: record.task, attempt: record.attempt,
        session: record.session, fence: record.fence, spec_rev: record.spec_rev, thread: record.thread,
        role: record.role, preset: record.preset ?? null, cli_version: record.cli_version, model_requested: record.model_requested,
        effort_requested: record.effort_requested, created_at: record.created_at } : null;
      return { ok: true, daemon, recovering, task: result.task, launch, pane, user_input_observer: result.user_input_observer };
    }
    if (input.command === "pane_status") return { ok: true, ...panes.status(input.thread) };
    if (input.command === "pane_process_info") return { ok: true, ...await panes.processInfo(input.thread) };
    if (input.command === "pane_screen_key") {
      if (authority.kind!=="operator") throw new Refusal("operator_required");
      return {ok:true,...await panes.screenKey(input.thread,input,authority.source)};
    }
    if (input.command === "pane_release") return { ok: true, ...await panes.release(input.thread, input.reason) };
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
            const caller = await panes.caller({ ...identity, native_session: stop.session_id });
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
            return await panes.parentLaunch.run(controller ? pane.record.id : null, () => gates.call(command, caller));
          });
          if (!receipt.replayed && !isPendingInboxResult(receipt.result)) receipts.push(receipt);
          if (pane.record.role === "reviewer" && !receipt.replayed) {
            if (receipt.result.ok) completedReview = { task: pane.record.task, id: pane.record.review_id };
            else {
              const caller = await panes.caller({ ...identity, native_session: stop.session_id });
              await gates.failReviewProtocol(pane.record.task, pane.record.review_id, { receipt, stop }, caller);
              pane.failed = "review_rejected";
            }
          }
        }
        if (matched && receipts.length && ["worker", "controller"].includes(pane.record.role)) await panes.dispatch(pane, feedbackText(receipts), "gate");
      });
      const payload = JSON.parse(input.raw_stdin);
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
    const actor = authority.kind === "operator" ? { address: "executor",
      assertActive: async () => { if (stopping) throw new Refusal("daemon_stopping"); } } : undefined;
    const { parent_launch, ...gateInput } = input;
    return await panes.parentLaunch.run(authority.kind === "operator" ? parent_launch ?? null : null,
      () => gates.call(gateInput, undefined, actor));
  };
  const server = createServer((connection) => {
    connection.setEncoding("utf8");
    let buffer = "", handled = false;
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
      let shellInput = false;
      try {
        envelope = JSON.parse(buffer.slice(0, end));
        shellInput = isShellInput(envelope);
        const authority = authenticate(envelope.identity);
        const catalogRead = catalogCommands.has(envelope.input?.command);
        const viewing = catalogRead || ["workbench_snapshot", "pane_output"].includes(envelope.input?.command);
        if (!viewing && !shellInput) store.event("request_received", { id: envelope.id, input: eventInput(envelope.input), source: authority.source });
        result = await handle(envelope, authority);
        if (result.ok && ["controller_start", "pane_release", "window_release", "signal"].includes(envelope.input.command)) {
          await settleInboxFeedback();
        }
        if (!catalogRead && !shellInput && (!viewing || !result.ok)) store.event("request_result", { id: envelope.id, command: envelope.input.command,
          ok: result.ok, error: result.error, details: result.details });
      } catch (error) {
        const processQuery = (error as { process_query?: unknown })?.process_query;
        result = { ok: false, error: error instanceof Refusal ? error.code : "orchestration_failed", details: String(error),
          ...(processQuery ? { diagnostics: { process_query: processQuery } } : {}) };
        try { if (!shellInput && !catalogCommands.has(envelope?.input?.command)) store.event("request_rejected", { id: envelope?.id, input: eventInput(envelope?.input), result }); }
        catch (recordError) {
          gates.setUserInputObserverStatus("failed", { reason: String(recordError) });
          result = { ok: false, error: "event_write_failed", details: String(recordError) };
        }
      } finally { activityFinished(); }
      connection.end(JSON.stringify(result) + "\n");
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
  });
  await new Promise<void>((resolve, reject) => { server.once("error", reject); server.listen(socket, resolve); });
  chmodSync(socket, 0o600);
  writeFileSync(join(root, "daemon.pid"), String(process.pid) + "\n", { flag: "wx", mode: 0o600 });
  recovery = panes.recover(daemon).finally(() => { recovering = false; });
  void recovery.catch(error => gates.setUserInputObserverStatus("failed", { reason: String(error) }));
  gates.recoverReviews();
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
