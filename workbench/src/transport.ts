import { createConnection } from "node:net";
import { spawn } from "node:child_process";
import { closeSync, existsSync, mkdirSync, openSync, realpathSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";

export function statePath(root: string) {
  if (!isAbsolute(root)) throw new Error("state must be an absolute path");
  return root;
}
export function socketPath(root: string) {
  const socket = join(statePath(root), "control.sock");
  if (Buffer.byteLength(socket) > 103) throw new Error("Unix socket path exceeds 103 bytes");
  return socket;
}
export function request(root: string, input: Record<string, unknown>, identity?: Record<string, unknown>): Promise<any> {
  return new Promise((resolve, reject) => {
    const socket = createConnection(socketPath(root));
    let buffer = "";
    let finished = false;
    socket.setEncoding("utf8");
    // A deadline is a failed/unknown call, never permission to replay a mutation.
    const wait = input.command === "run" ? input.wait_seconds : undefined;
    const deadline = typeof wait === "number" && Number.isSafeInteger(wait) && wait > 0
      ? Math.min(2_147_483_647, Math.max(120_000, wait * 1000 + 120_000)) : 120_000;
    socket.setTimeout(deadline, () => socket.destroy(new Error("daemon request deadline; outcome unknown")));
    socket.on("error", reject);
    socket.on("connect", () => socket.write(JSON.stringify({ id: randomUUID(), input, identity }) + "\n"));
    socket.on("data", (chunk) => {
      buffer += chunk;
      const end = buffer.indexOf("\n");
      if (end < 0) return;
      try { finished = true; resolve(JSON.parse(buffer.slice(0, end))); }
      catch (error) { reject(error); }
      socket.end();
    });
    socket.on("close", () => { if (!finished) reject(new Error("daemon disconnected; outcome unknown")); });
  });
}
export async function startDaemon(root: string, options: Record<string, unknown>) {
  statePath(root);
  mkdirSync(root, { recursive: true, mode: 0o700 });
  root = realpathSync(root);
  if (existsSync(socketPath(root))) throw new Error("socket exists; query its owner, do not replace it");
  const stdout = openSync(join(root, "daemon.stdout.log"), "a", 0o600);
  const stderr = openSync(join(root, "daemon.stderr.log"), "a", 0o600);
  const env = { ...process.env };
  for (const key of Object.keys(env)) if (key.startsWith("A2A_") || key.startsWith("GIT_CONFIG_")) delete env[key];
  const child = spawn(process.execPath, [fileURLToPath(new URL("./daemon.ts", import.meta.url)), root, JSON.stringify(options)], {
    detached: true, stdio: ["ignore", stdout, stderr, "ipc"], env,
  });
  closeSync(stdout); closeSync(stderr);
  return await new Promise<any>((resolve, reject) => {
    const deadline = setTimeout(() => {
      child.disconnect(); child.unref();
      reject(new Error(`daemon start deadline; inspect PID ${child.pid} and logs; no automatic retry`));
    }, 10_000);
    child.once("error", (error) => { clearTimeout(deadline); reject(error); });
    child.once("exit", (code, signal) => { clearTimeout(deadline); reject(new Error(`daemon exited (${code}, ${signal}); inspect daemon.stderr.log`)); });
    child.once("message", (message) => {
      clearTimeout(deadline); child.disconnect(); child.unref(); resolve(message);
    });
  });
}
