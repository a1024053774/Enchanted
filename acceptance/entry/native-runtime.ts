// Evidence-only replacement for the native thread service. No model execution.
import { execFile } from "node:child_process";
import { fileURLToPath } from "node:url";
import type { GateRuntime } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts";
const service = fileURLToPath(new URL("./thread-boundary.py", import.meta.url));
export async function boundary(method: string, payload: unknown): Promise<any> {
  return new Promise((resolve, reject) => {
    execFile("python3", ["-B", service, method, JSON.stringify(payload)], {maxBuffer: 4 * 1024 * 1024},
      (error, stdout, stderr) => error ? reject(new Error(stderr || stdout || String(error))) : resolve(JSON.parse(stdout)));
  });
}
export const runtime: GateRuntime = {
  ensureProject: async (project, repo) => { await boundary("ensure", {project, repo}); },
  createThread: async (task, attempt) => { await boundary("create", {task, attempt}); },
  startThread: async (_task, attempt, prompt) => { await boundary("start", {thread: attempt.thread_id, prompt}); },
  readThread: async (thread) => boundary("read", {thread}),
  stopThread: async (thread) => { await boundary("stop", {thread}); },
  archiveThread: async (thread) => { await boundary("archive", {thread}); },
};
