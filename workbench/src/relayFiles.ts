import { closeSync, constants, fstatSync, fsyncSync, openSync, readFileSync, readdirSync, realpathSync, renameSync, writeFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import { randomUUID } from "node:crypto";

export interface RelayFile { name: string; raw?: string; error?: string }

// Called only after the daemon matches an authenticated reviewer's Stop.
// The model remains read-only; the hook request handler persists its explicit JSON.
export function writeReviewRequest(directory: string, input: Record<string, any>): RelayFile {
  const root = realpathSync(directory);
  if (root !== directory || !/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(input.request_id)) throw new Error("invalid_review_request_path");
  const name = input.request_id + ".json", raw = JSON.stringify(input) + "\n";
  let fd: number;
  try { fd = openSync(join(root, name), "wx", 0o600); }
  catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
    // A repeated explicit request may reuse its file, never replace it. The
    // existing relay journal decides whether its operation already completed.
    const prior = readWorkerRequests(root).find((file) => file.name === name);
    if (!prior || prior.error || prior.raw !== raw) throw new Error("review_request_file_changed");
    return prior;
  }
  try { writeFileSync(fd, raw); fsyncSync(fd); }
  finally { closeSync(fd); }
  return { name, raw };
}

export type ControllerContext = {
  schema: 2; launch: string; preset: "ideation" | "executor"; project: string; task: string;
  session: string; native_session: string; spec_rev: number; prompt_id: string;
};
export function writeControllerContext(directory: string, context: ControllerContext) {
  if (!isAbsolute(directory) || realpathSync(directory) !== directory) throw new Error("request_directory_changed");
  const temporary = join(directory, "controller-context." + randomUUID() + ".tmp");
  const fd = openSync(temporary, "wx", 0o600);
  try { writeFileSync(fd, JSON.stringify(context) + "\n"); fsyncSync(fd); }
  finally { closeSync(fd); }
  renameSync(temporary, join(directory, "controller-context"));
}

export function queueSessionRequest(input: Record<string, any>, env = process.env) {
  const directory = env.A2A_REQUEST_DIR;
  if (!directory || !isAbsolute(directory) || !["worker", "controller"].includes(env.A2A_ROLE ?? "")) throw new Error("session_request_directory_required");
  const root = realpathSync(directory);
  const request_id = input.request_id ?? randomUUID();
  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(request_id)) throw new Error("invalid_request_id");
  let request: Record<string, any>;
  if (env.A2A_ROLE === "controller") {
    if (root !== directory) throw new Error("request_directory_changed");
    const fd = openSync(join(root, "controller-context"), constants.O_RDONLY | constants.O_NOFOLLOW);
    let context: ControllerContext;
    try {
      if (!fstatSync(fd).isFile()) throw new Error("controller_context_required");
      context = JSON.parse(readFileSync(fd, "utf8"));
    } finally { closeSync(fd); }
    const expected = { launch: env.A2A_LAUNCH, preset: env.A2A_PRESET, project: env.A2A_PROJECT, task: env.A2A_TASK,
      session: env.A2A_SESSION, native_session: env.A2A_NATIVE_SESSION, spec_rev: Number(env.A2A_SPEC_REV) };
    if (context.schema !== 2 || !["ideation", "executor"].includes(context.preset) ||
        Object.entries(expected).some(([key, value]) => !value || context[key as keyof ControllerContext] !== value) ||
        !Number.isSafeInteger(context.spec_rev) || context.spec_rev < 1 ||
        typeof context.prompt_id !== "string" || !/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(context.prompt_id)) {
      throw new Error("controller_context_mismatch");
    }
    request = { ...context, ...input, schema: 2, request_id };
  } else {
    request = { schema: 1, request_id, task: env.A2A_TASK, attempt: env.A2A_ATTEMPT,
      session: env.A2A_SESSION, fence: Number(env.A2A_FENCE), spec_rev: Number(env.A2A_SPEC_REV), ...input };
    if (!request.task || !request.attempt || !request.session || !Number.isSafeInteger(request.fence) || !Number.isSafeInteger(request.spec_rev)) {
      throw new Error("worker_binding_required");
    }
  }
  const file = join(root, request_id + ".json");
  const fd = openSync(file, "wx", 0o600);
  try { writeFileSync(fd, JSON.stringify(request) + "\n"); fsyncSync(fd); }
  finally { closeSync(fd); }
  return { ok: true, queued: true, delivered: false, request_id, path: file };
}

export function readWorkerRequests(directory: string): RelayFile[] {
  if (!isAbsolute(directory)) throw new Error("worker_request_directory_required");
  if (realpathSync(directory) !== directory) throw new Error("request_directory_changed");
  return readdirSync(directory).filter((name) => name.endsWith(".json")).sort().map((name) => {
    const file = join(directory, name);
    try {
      const fd = openSync(file, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
      try {
        if (!fstatSync(fd).isFile()) return { name, error: "request_must_be_regular_file" };
        return { name, raw: readFileSync(fd, "utf8") };
      }
      finally { closeSync(fd); }
    } catch (error) { return { name, error: String(error) }; }
  });
}
