// Test-only interposition at real attach boundaries. No provider is launched.
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [source, state, control, ready, mode] = process.argv.slice(2);
if (!source || !state || !control || !ready || !["creating", "active"].includes(mode)) {
  throw new Error("source, state, control, ready and creating/active are required");
}
const { serve } = await import(pathToFileURL(join(source, "workbench/src/daemon.ts")).href);
const { A2AGates } = await import(pathToFileURL(join(source, "workbench/src/gates/core.ts")).href);
const release = join(control, "release"), boundary = join(control, "boundary.json");
const unused = async () => { throw new Error("Worker lifecycle is outside this attachment probe"); };
const runtime = {
  ensureProject: async () => {}, createThread: unused, startThread: unused,
  readThread: unused, stopThread: unused, archiveThread: unused,
  createAttachedThread: async (task: any, attachment: any) => {
    if (mode !== "creating") return;
    writeFileSync(boundary, JSON.stringify({ phase: "creating", task: task.task_id,
      thread: attachment.thread_id, pid: process.pid, source_core: join(source, "workbench/src/gates/core.ts") }) + "\n", { flag: "wx" });
    const deadline = Date.now() + 45_000;
    while (!existsSync(release)) {
      if (Date.now() >= deadline) throw new Error("Controlled creating boundary expired");
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
  },
};
class WindowGates extends A2AGates {
  event(task: string, type: string, details: any, expectedAttempt?: string | null) {
    if (mode === "active" && type === "attached") {
      // TypeScript private is a runtime method, not a #private field. Only this
      // disposable host interposes; the product event method is unchanged.
      writeFileSync(boundary, JSON.stringify({ phase: "active-before-attached", task,
        thread: details.attachment.thread_id, pid: process.pid, state_db_in_transaction: this.db.isTransaction,
        source_core: join(source, "workbench/src/gates/core.ts") }) + "\n", { flag: "wx" });
      const deadline = Date.now() + 45_000, sleep = new Int32Array(new SharedArrayBuffer(4));
      while (!existsSync(release)) {
        if (Date.now() >= deadline) throw new Error("Controlled active boundary expired");
        Atomics.wait(sleep, 0, 0, 10);
      }
    }
    return super.event(task, type, details, expectedAttempt);
  }
}
await serve(state, {}, (root: string) => new WindowGates(root, runtime));
writeFileSync(ready, JSON.stringify({ pid: process.pid, state, source, mode,
  evidence_layer: "real daemon/gate/SQLite with controlled attach runtime", real_codex_turns: 0 }) + "\n", { flag: "wx" });
