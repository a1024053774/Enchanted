import { appendFileSync } from "node:fs";

// No argv, environment, prompt or auth data enters the process list. The
// profile label describes inherited launch provenance, not an OS verdict.
export function recordLoginProcess(role: string, pid = process.pid, ppid = process.ppid) {
  const file = process.env.A2A_PROFILE_PROCESS_LOG;
  if (!file) return;
  appendFileSync(file, JSON.stringify({ pid, ppid, role, profile: "C inherited" }) + "\n", { mode: 0o600 });
}
recordLoginProcess("Node process");
