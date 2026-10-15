// T-077 external-session fixture. The selected daemon and gates remain unchanged.
import { appendFileSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { pathToFileURL } from "node:url";
import { installControlledPTY } from "./controlled_quality_pty.ts";
import { withReviewerRuntime } from "./legacy_review_runtime.ts";

const [state, control, ready, gate, reviewControl] = process.argv.slice(2);
if (!state || !control || control === "-" || !ready || !gate || !reviewControl || process.argv.length !== 7)
  throw new Error("Expected state, controlled-session directory, ready file, gate module and reviewer control directory");
const product = resolve(dirname(gate), "../../..");
process.env.A2A_TEST_THREAD_CONTROL = resolve(control);
const { serve } = await import(pathToFileURL(join(product, "workbench/src/daemon.ts")).href);
const { A2AGates } = await import(pathToFileURL(gate).href);
const { boundary, runtime: original } = await import(pathToFileURL(join(product, "acceptance/entry/native-runtime.ts")).href);
const config = JSON.parse(readFileSync(join(reviewControl, "config.json"), "utf8"));
const bind = installControlledPTY(product, reviewControl, config);
const turns = new Map<string, number>();
const workers = new Map<string, any>();
const modeFile = join(control, "conflict-mode.json");
const mode = () => existsSync(modeFile) ? JSON.parse(readFileSync(modeFile, "utf8")) : {};
const log = (name: string, value: unknown) => appendFileSync(join(control, name + ".jsonl"), JSON.stringify(value) + "\n");
const runtime = {
  ...original,
  createThread: async (task: any, attempt: any) => {
    await original.createThread(task, attempt);
    const creation = { id: attempt.thread_id, role: "worker", cli_version: "controlled-conflict-runtime",
      model: task.card.executor.model, effort: task.card.executor.effort,
      thread: attempt.thread_id, task: task.task_id, attempt: attempt.attempt_id, session: attempt.session_id };
    workers.set(attempt.thread_id, creation);
    log("worker-creations", creation);
  },
  sessionFacts: async (thread: string) => {
    const launch = workers.get(thread);
    if (!launch) throw new Error("No controlled conflict worker creation");
    return { launch, model: launch.model, effort: launch.effort };
  },
  qualityFeedback: async (attempt: any, repair: any) => {
    log("quality-feedback", { attempt: attempt.attempt_id, thread: attempt.thread_id, repair, registered: !repair.stopped });
    if (!repair.stopped) turns.set(attempt.thread_id, (turns.get(attempt.thread_id) ?? 0) + 1);
  },
  startThread: async (task: unknown, attempt: any, prompt: string) => {
    await original.startThread(task, attempt, prompt);
    turns.set(attempt.thread_id, 1);
  },
  readThread: async (thread: string) => {
    const live = await original.readThread(thread);
    const turn = turns.has(thread) ? `fixture-turn:${thread}:${turns.get(thread)}` : live.turn;
    const selected = mode();
    const overrides = selected.thread === thread ? selected.observation ?? {} : {};
    // Stable native identity follows T-076-1; turn changes do not replace it.
    return { ...live, turn,
      runtime_identity: { launch: thread, thread, shell_pid: 101, leader_pid: 102, native_session: thread },
      ...overrides };
  },
  sendGateFeedback: async (thread: string, messageId: string, message: string) => {
    log("gate-feedback", { thread, message_id: messageId, text: message });
    if (mode().delivery_unknown) throw new Error("fixture: feedback receipt unavailable after send");
    await boundary("start", { thread, prompt: message });
    turns.set(thread, (turns.get(thread) ?? 0) + 1);
  },
};

class ControlledConflictGates extends A2AGates {
  async call(raw: any, caller?: any) {
    if (raw?.command !== "submit" || caller) return super.call(raw, caller);
    const status = await super.call({ command: "status", task: raw.task });
    const attempt = status.task?.current_attempt;
    if (!attempt?.thread_id) return super.call(raw, caller);
    await boundary("submit-begin", { thread: attempt.thread_id });
    const live = await runtime.readThread(attempt.thread_id);
    const supplied = { thread: attempt.thread_id, turn: live.turn, assertActive: async () => {} };
    log("submit-caller", { phase: "begin", request: raw, thread: supplied.thread, turn: supplied.turn });
    try {
      const result = await super.call(raw, supplied);
      log("submit-caller", { phase: "result", request: raw, result });
      return result;
    } finally {
      await boundary("submit-end", { thread: attempt.thread_id });
    }
  }
}

await serve(state, config, (root: string, panes: any) => {
  bind(panes);
  return new ControlledConflictGates(root, withReviewerRuntime(runtime, panes));
});
writeFileSync(ready, JSON.stringify({ pid: process.pid, root: resolve(state), gate,
  daemon: join(product, "workbench/src/daemon.ts"),
  runtime: "controlled-conflict-session", control: resolve(control), argv: process.argv }) + "\n", { flag: "wx" });
