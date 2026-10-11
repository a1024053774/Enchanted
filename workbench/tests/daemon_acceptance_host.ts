// Test host for the existing controlled thread service. No provider execution.
import { appendFileSync, writeFileSync } from "node:fs";
import { resolve, join } from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import { serve } from "../src/daemon.ts";
import type { SubmitCaller } from "../src/gates/core.ts";
import { boundary, runtime } from "../../acceptance/entry/native-runtime.ts";

const [state, control, ready, gate] = process.argv.slice(2);
if (!state || !control || !ready || !gate || process.argv.length !== 6) {
  throw new Error("usage: daemon_acceptance_host.ts ABS_STATE ABS_THREAD_CONTROL_OR_DASH ABS_READY_FILE ABS_GATE_MODULE");
}
const controlled = control !== "-";
if (controlled) process.env.A2A_TEST_THREAD_CONTROL = resolve(control);
else delete process.env.A2A_TEST_THREAD_CONTROL;
const { A2AGates } = await import(gate);
const audit = join(control, "submit-caller.jsonl");
const owned = new Map<string, { launch: string; shell_pid: number }>();
const controlledRuntime = {
  ...runtime,
  createThread: async (task: any, attempt: any) => {
    await runtime.createThread(task, attempt);
    owned.set(attempt.thread_id, { launch: randomUUID(), shell_pid: 10000 + owned.size });
  },
  readThread: async (thread: string) => {
    const live = await runtime.readThread(thread), owner = owned.get(thread);
    if (!owner) throw new Error("Controlled runtime owner was not created by this host");
    // This old external fixture uses its turn token as the owner generation:
    // leader-changed replaces it; helper-joins leaves it unchanged. No actual
    // native session or CLI PID is claimed by this synthetic runtime.
    return { ...live, runtime_identity: { launch: owner.launch, thread, shell_pid: owner.shell_pid,
      leader_pid: live.turn ? 20000 : null, native_session: live.turn } };
  },
};

class ControlledThreadGates extends A2AGates {
  async call(raw: unknown, caller?: SubmitCaller) {
    const input = raw as Record<string, unknown>;
    if (input?.command !== "submit" || caller) return await super.call(raw, caller);
    const status = await super.call({ command: "status", task: input.task });
    const attempt = status.task?.current_attempt;
    if (!attempt?.thread_id) return await super.call(raw, caller);
    const live = await boundary("submit-begin", { thread: attempt.thread_id });
    const supplied = { thread: attempt.thread_id, turn: live.turn, assertActive: async () => {} };
    appendFileSync(audit, JSON.stringify({ at: new Date().toISOString(), pid: process.pid,
      request: raw, thread: supplied.thread, turn: supplied.turn, phase: "begin" }) + "\n");
    try {
      // Pass the socket request unchanged to the real gate. Only the external
      // thread service and its active-turn caller are supplied by this fixture.
      const result = await super.call(raw, supplied);
      appendFileSync(audit, JSON.stringify({ at: new Date().toISOString(), pid: process.pid,
        request: raw, result, phase: "result" }) + "\n");
      return result;
    } finally {
      await boundary("submit-end", { thread: attempt.thread_id });
    }
  }
}

await serve(state, {}, (root, panes) => controlled
  ? new ControlledThreadGates(root, controlledRuntime)
  : new A2AGates(root, panes));
writeFileSync(ready, JSON.stringify({ pid: process.pid, root: resolve(state),
  gate,
  daemon: fileURLToPath(new URL("../src/daemon.ts", import.meta.url)),
  runtime: controlled ? fileURLToPath(new URL("../../acceptance/entry/native-runtime.ts", import.meta.url)) : "Panes",
  control: controlled ? resolve(control) : null, argv: process.argv }) + "\n", { flag: "wx" });
