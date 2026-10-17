// Test host for the existing controlled thread service. No provider execution.
<<<<<<< HEAD
import { appendFileSync, existsSync, readFileSync, writeFileSync } from "node:fs";
=======
import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
>>>>>>> b3fb998c (T-078-1: 接通窗口输入、worker 收件箱和停止通路，记录主控启动计划)
import { resolve, join } from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import { serve } from "../src/daemon.ts";
import type { GateActor, SubmitCaller } from "../src/gates/core.ts";
import { createOperatorCredential } from "../src/credentials.ts";
import { boundary, runtime } from "../../acceptance/entry/native-runtime.ts";
import { installControlledPTY } from "./controlled_quality_pty.ts";
import { withReviewerRuntime } from "./legacy_review_runtime.ts";

const [state, control, ready, gate, reviewControl] = process.argv.slice(2);
if (!state || !control || !ready || !gate || !reviewControl || process.argv.length !== 7) {
  throw new Error("Expected state, worker control, ready, gate module and reviewer control paths.");
}
process.env.A2A_TEST_THREAD_CONTROL = resolve(control);
const { A2AGates } = await import(gate);
const config = JSON.parse(readFileSync(join(reviewControl, "config.json"), "utf8"));
const bind = installControlledPTY(fileURLToPath(new URL("../../", import.meta.url)), reviewControl, config);
const audit = join(control, "submit-caller.jsonl");
const launches = join(control, "worker-creations.jsonl");
const owned = new Map<string, any>(existsSync(launches) ? readFileSync(launches, "utf8").trim().split("\n").filter(Boolean)
  .map((line) => { const row = JSON.parse(line); return [row.thread, row]; }) : []);
const controlledRuntime = {
  ...runtime,
  createThread: async (task: any, attempt: any) => {
    await runtime.createThread(task, attempt);
    const creation = { id: randomUUID(), role: "worker", thread: attempt.thread_id, task: task.task_id,
      attempt: attempt.attempt_id, session: attempt.session_id, shell_pid: 10000 + owned.size,
      cli_version: "controlled-runtime fixture", model: task.card.executor.model, effort: task.card.executor.effort,
      evidence_layer: "synthetic external runtime creation; no provider/model execution" };
    appendFileSync(launches, JSON.stringify(creation) + "\n");
    owned.set(attempt.thread_id, creation);
  },
  readThread: async (thread: string) => {
    const live = await runtime.readThread(thread), owner = owned.get(thread);
    if (!owner) throw new Error("Controlled runtime owner was not created by this host");
    // This old external fixture uses its turn token as the owner generation:
    // leader-changed replaces it; helper-joins leaves it unchanged. No actual
    // native session or CLI PID is claimed by this synthetic runtime.
    return { ...live, runtime_identity: { launch: owner.id, thread, shell_pid: owner.shell_pid,
      leader_pid: live.turn ? 20000 : null, native_session: live.turn } };
  },
  sessionFacts: async (thread: string) => {
    const owner = owned.get(thread);
    if (!owner) throw new Error("No controlled runtime creation for this worker.");
    return { launch: owner, model: owner.model, effort: owner.effort };
  },
  qualityFeedback: async (attempt: any, repair: any) => {
    if (!owned.has(attempt.thread_id)) throw new Error("Unknown feedback owner.");
    appendFileSync(join(control, "quality-feedback.jsonl"), JSON.stringify({ attempt: attempt.attempt_id,
      thread: attempt.thread_id, repair, registered: !repair.stopped,
      body: `⟦门禁 #${repair.count}⟧\n${JSON.stringify(repair)}` }) + "\n");
  },
};

class ControlledThreadGates extends A2AGates {
  async call(raw: unknown, caller?: SubmitCaller, actor: GateActor | undefined = caller) {
    const input = raw as Record<string, unknown>;
    if (input?.command !== "submit" || caller) return await super.call(raw, caller, actor);
    if (actor) await actor.assertActive();
    const status = await super.call({ command: "status", task: input.task });
    const attempt = status.task?.current_attempt;
    if (!attempt?.thread_id) return await super.call(raw, caller, actor);
    const live = await boundary("submit-begin", { thread: attempt.thread_id });
    const supplied = { thread: attempt.thread_id, turn: live.turn, assertActive: async () => {} };
    appendFileSync(audit, JSON.stringify({ at: new Date().toISOString(), pid: process.pid,
      request: raw, thread: supplied.thread, turn: supplied.turn, transport_actor: actor?.address ?? null, phase: "begin" }) + "\n");
    try {
      // Pass the socket request unchanged to the real gate. Only the external
      // thread service and its active-turn caller are supplied by this fixture.
      const result = await super.call(raw, supplied, actor);
      appendFileSync(audit, JSON.stringify({ at: new Date().toISOString(), pid: process.pid,
        request: raw, result, phase: "result" }) + "\n");
      return result;
    } finally {
      await boundary("submit-end", { thread: attempt.thread_id });
    }
  }
}

<<<<<<< HEAD
await serve(state, config, (root, panes) => {
  bind(panes);
  return new ControlledThreadGates(root, withReviewerRuntime(controlledRuntime, panes));
});
=======
mkdirSync(state, { recursive: true, mode: 0o700 });
createOperatorCredential(state);
await serve(state, {}, (root, panes) => controlled
  ? new ControlledThreadGates(root, controlledRuntime)
  : new A2AGates(root, panes));
>>>>>>> b3fb998c (T-078-1: 接通窗口输入、worker 收件箱和停止通路，记录主控启动计划)
writeFileSync(ready, JSON.stringify({ pid: process.pid, root: resolve(state),
  gate,
  daemon: fileURLToPath(new URL("../src/daemon.ts", import.meta.url)),
  runtime: fileURLToPath(new URL("../../acceptance/entry/native-runtime.ts", import.meta.url)),
  control: resolve(control), review_control: reviewControl, real_codex_turns: 0, argv: process.argv }) + "\n", { flag: "wx" });
