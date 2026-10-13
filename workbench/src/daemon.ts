import { createServer } from "node:net";
import { chmodSync, existsSync, mkdirSync, readFileSync, realpathSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import { A2AGates, Refusal } from "./gates/core.ts";
import { OrchestrationStore } from "./store.ts";
import { Panes, spawnHelper, type LaunchConfig } from "./panes.ts";
import { socketPath } from "./transport.ts";
import { RequestRelay } from "./relay.ts";
import { writeReviewRequest } from "./relayFiles.ts";
import { reviewRequest, scoreRecords, QualityProtocolError } from "./gates/qualityProtocol.ts";
import { randomUUID } from "node:crypto";

export async function serve(
  root: string,
  config: LaunchConfig,
  createGates: (root: string, panes: Panes) => A2AGates = (root, panes) => new A2AGates(root, panes),
) {
  mkdirSync(root, { recursive: true, mode: 0o700 });
  root = realpathSync(root);
  const socket = socketPath(root);
  if (existsSync(socket)) throw new Error("socket exists; refusing to replace it");
  const helper = spawnHelper();
  const store = new OrchestrationStore(root);
  const panes = new Panes(root, store, config, (reason) => gates.setUserInputObserverStatus("failed", { reason }));
  const gates = createGates(root, panes);
  const relay = new RequestRelay(store);
  const daemon = randomUUID();
  gates.setUserInputObserverStatus("healthy");
  let stopping = false;
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
    await panes.shutdown();
    store.event("daemon_stopped", { pid: process.pid });
    await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
    gates.close(); store.close();
    // Only this server's successfully bound endpoint and PID record are removed.
    if (existsSync(socket)) unlinkSync(socket);
    unlinkSync(join(root, "daemon.pid"));
  };
  const handle = async (envelope: any) => {
    const input = envelope.input;
    if (!input || typeof input.command !== "string") throw new Refusal("invalid_request");
    const identity = envelope.identity;
    if (identity) {
      panes.authenticate(identity);
      if (input.command !== "signal") throw new Refusal("worker_requests_require_stop");
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
    if (input.command === "daemon_stop") {
      stopping = true;
      gates.beginShutdown();
      return { ok: true, pid: process.pid, stopping: true };
    }
    if (input.command === "orchestration_events") return { ok: true, events: store.read(input.task) };
    if (input.command === "pane_output") return { ok: true, ...panes.output(input.launch, input.offset, input.max_bytes) };
    if (input.command === "workbench_snapshot") {
      const result = await gates.call({ command: "status", task: input.task });
      if (!result.ok || !result.task) return result;
      const record = input.launch ? panes.launchRecord(input.launch) :
        result.task.current_attempt?.thread_id ? store.threadLaunch(result.task.current_attempt.thread_id) : undefined;
      if (record && record.task !== input.task) throw new Refusal("launch_task_mismatch");
      const pane = record ? panes.status(record.thread) : null;
      const launch = record ? { id: record.id, project: record.project, task: record.task, attempt: record.attempt,
        session: record.session, fence: record.fence, spec_rev: record.spec_rev, thread: record.thread,
        role: record.role, cli_version: record.cli_version, model_requested: record.model_requested,
        effort_requested: record.effort_requested, created_at: record.created_at } : null;
      return { ok: true, daemon, task: result.task, launch, pane, user_input_observer: result.user_input_observer };
    }
    if (input.command === "pane_status") return { ok: true, ...panes.status(input.thread) };
    if (input.command === "pane_process_info") return { ok: true, ...await panes.processInfo(input.thread) };
    if (input.command === "pane_release") return { ok: true, ...await panes.release(input.thread, input.reason) };
    if (input.command === "pane_dispatch") return { ok: true, dispatch: await panes.dispatch(panes.get(input.thread), input.body) };
    if (input.command === "signal") {
      if (!identity || identity.launch !== input.launch) throw new Refusal("signal_identity_required");
      let completedReview: { task: string; id: string } | undefined;
      await panes.signal(input.launch, input.raw_stdin, input.received_at, async (pane, stop, matched) => {
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
          const receipt = await relay.receive(pane.record as any, file, matched, async (command) => {
            const caller = await panes.caller({ ...identity, native_session: stop.session_id });
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
            return await gates.call(command, caller);
          });
          if (!receipt.replayed) receipts.push(receipt);
          if (pane.record.role === "reviewer" && !receipt.replayed) {
            if (receipt.result.ok) completedReview = { task: pane.record.task, id: pane.record.review_id };
            else {
              const caller = await panes.caller({ ...identity, native_session: stop.session_id });
              await gates.failReviewProtocol(pane.record.task, pane.record.review_id, { receipt, stop }, caller);
              pane.failed = "review_rejected";
            }
          }
        }
        if (matched && receipts.length && pane.record.role === "worker") await panes.dispatch(pane,
          "本回合的异步请求处理结果如下。请仅确认收到并结束；不调用工具、不改文件、不新增请求。\n" + JSON.stringify(receipts, null, 2), "gate");
      });
      return { ok: true, completedReview };
    }
    if (input.command === "launch_show") {
      if (identity && identity.launch !== input.launch) throw new Refusal("stale_launch");
      return { ok: true, ...panes.launchInfo(input.launch) };
    }
    const caller = identity ? await panes.caller(identity) : undefined;
    return await gates.call(input, caller);
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
      try {
        envelope = JSON.parse(buffer.slice(0, end));
        const viewing = ["workbench_snapshot", "pane_output"].includes(envelope.input?.command);
        if (!viewing) store.event("request_received", { id: envelope.id, input: envelope.input,
          source: envelope.identity ? panes.authenticate(envelope.identity).record.role : "executor" });
        result = await handle(envelope);
        if (!viewing || !result.ok) store.event("request_result", { id: envelope.id, command: envelope.input.command,
          ok: result.ok, error: result.error, details: result.details });
      } catch (error) {
        result = { ok: false, error: error instanceof Refusal ? error.code : "orchestration_failed", details: String(error) };
        try { store.event("request_rejected", { id: envelope?.id, input: envelope?.input, result }); }
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
  panes.recover(daemon);
  gates.recoverReviews();
  store.event("daemon_started", { daemon, pid: process.pid, ppid: process.ppid, argv: process.argv, helper, node: process.version });
  process.send?.({ ok: true, pid: process.pid, root, helper });
}

if (import.meta.main) {
  try { await serve(process.argv[2]!, JSON.parse(process.argv[3] ?? "{}")); }
  catch (error) { console.error(error); process.exit(1); }
}
