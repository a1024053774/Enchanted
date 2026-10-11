import { closeSync, constants, fstatSync, fsyncSync, openSync, readFileSync, readdirSync, realpathSync, writeFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import { randomUUID } from "node:crypto";

export interface RelayFile { name: string; raw?: string; error?: string }

export function queueWorkerRequest(input: Record<string, any>, env = process.env) {
  const directory = env.A2A_REQUEST_DIR;
  if (!directory || !isAbsolute(directory) || env.A2A_ROLE !== "worker") throw new Error("worker_request_directory_required");
  const root = realpathSync(directory);
  const request_id = input.request_id ?? randomUUID();
  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(request_id)) throw new Error("invalid_request_id");
  const request = { schema: 1, request_id, task: env.A2A_TASK, attempt: env.A2A_ATTEMPT,
    session: env.A2A_SESSION, fence: Number(env.A2A_FENCE), spec_rev: Number(env.A2A_SPEC_REV), ...input };
  if (!request.task || !request.attempt || !request.session || !Number.isSafeInteger(request.fence) || !Number.isSafeInteger(request.spec_rev)) {
    throw new Error("worker_binding_required");
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
