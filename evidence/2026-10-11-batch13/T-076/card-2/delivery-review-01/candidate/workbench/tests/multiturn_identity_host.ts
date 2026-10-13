// Test-only external runtime facts. No real provider or process identity claim.
import { appendFileSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { randomUUID } from "node:crypto";
import { installControlledPTY } from "./controlled_quality_pty.ts";
import { withReviewerRuntime } from "./legacy_review_runtime.ts";

const [source, root, control, ready] = process.argv.slice(2);
if (!source || !root || !control || !ready) throw new Error("source, root, control and ready are required");
const { serve } = await import(pathToFileURL(join(source, "workbench/src/daemon.ts")).href);
const { A2AGates } = await import(pathToFileURL(join(source, "workbench/src/gates/core.ts")).href);
const reviewControl = join(control, "quality-control");
const config = JSON.parse(readFileSync(join(reviewControl, "config.json"), "utf8"));
const bind = installControlledPTY(source, reviewControl, config);
const file = join(control, "runtime.json"), audit = join(control, "runtime.jsonl");
const read = () => JSON.parse(readFileSync(file, "utf8"));
function save(value: any) { writeFileSync(file, JSON.stringify(value) + "\n"); }
function observe(method: string, input: any, result: any) {
  appendFileSync(audit, JSON.stringify({ method, input, result, pid: process.pid }) + "\n");
}
const runtime = {
  ensureProject: async () => {},
  createThread: async (task: any, attempt: any) => {
    const state = read();
    const live = { thread_id: attempt.thread_id, workspace: attempt.workspace, provider: "codex", turn: null,
      running: false, stopped: false, archived: false, blocked: false,
      facts: { role: "worker", cli_version: "controlled-runtime fixture", model: task.card.executor.model, effort: task.card.executor.effort },
      runtime_identity: { launch: randomUUID(), thread: attempt.thread_id, shell_pid: 11001,
        leader_pid: 11002, native_session: "fixture-native-" + attempt.thread_id } };
    state.threads[attempt.thread_id] = live; save(state); observe("create", attempt, live);
  },
  sessionFacts: async (thread: string) => {
    const live = read().threads[thread];
    return { launch: { ...live.facts, id: live.runtime_identity.launch }, model: live.facts.model, effort: live.facts.effort };
  },
  startThread: async (_task: any, attempt: any) => {
    const state = read(), live = state.threads[attempt.thread_id];
    live.turn = "delivery-A"; live.running = true; save(state); observe("start", attempt.thread_id, live);
  },
  readThread: async (thread: string) => {
    const live = read().threads[thread];
    if (!live) throw new Error("Unknown controlled thread");
    observe("read", thread, live); return live;
  },
  stopThread: async (thread: string) => {
    const state = read(), live = state.threads[thread];
    if (live.running) throw new Error("Fixture cannot stop a running worker");
    live.stopped = true; state.closes.push(thread); save(state); observe("stop", thread, live);
  },
  archiveThread: async (thread: string) => {
    const state = read(), live = state.threads[thread];
    if (!live.stopped) throw new Error("Fixture cannot archive before stop");
    live.archived = true; save(state); observe("archive", thread, live);
  },
};
class ControlledGates extends A2AGates {
  async call(input: any, supplied?: any) {
    if (input.command !== "submit" || supplied) return super.call(input, supplied);
    const value = await super.call({ command: "status", task: input.task });
    const attempt = value.task?.current_attempt;
    if (!attempt?.thread_id) return super.call(input, supplied);
    const live = await runtime.readThread(attempt.thread_id);
    const caller = { thread: attempt.thread_id, turn: live.turn,
      assertActive: async () => {
        const current = await runtime.readThread(attempt.thread_id);
        if (!current.running || current.turn !== caller.turn) throw new Error("Controlled caller inactive");
      } };
    return super.call(input, caller);
  }
}
await serve(root, config, (state: string, panes: any) => {
  bind(panes);
  return new ControlledGates(state, withReviewerRuntime(runtime, panes));
});
writeFileSync(ready, JSON.stringify({ pid: process.pid, source, root, control,
  runtime: "external controlled fixture", real_codex_turns: 0 }) + "\n", { flag: "wx" });
