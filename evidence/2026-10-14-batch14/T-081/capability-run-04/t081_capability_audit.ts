// A test-only preloader: validate the approved launch before the real PTY spawn.
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import { join } from "node:path";

const policyFile = process.env.T081_CAPABILITY_POLICY;
if (!policyFile) throw new Error("T-081 approved policy file is required.");
const policy = JSON.parse(readFileSync(policyFile, "utf8"));
if (policy.approval_ref !== "T-081 controller-decision-04 capability-turn-3" || policy.turn_limit !== 1)
  throw new Error("T-081 approval or turn limit differs.");
const { Panes } = await import(pathToFileURL(join(policy.source, "workbench/src/panes.ts")).href);
const require = createRequire(pathToFileURL(join(policy.source, "workbench/package.json")));
const modulePath = require.resolve("node-pty"), original = require(modulePath);
const quote = (v: string) => "'" + v.replaceAll("'", "'\\''") + "'";
const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
let runtime: any, starts = 0, dispatches = 0;
const create = Panes.prototype.createThread;
Panes.prototype.createThread = async function (task: any, attempt: any) {
  if (runtime || task.task_id !== "T-081-CAP-04" || attempt.fence !== 1)
    throw new Error("Only the approved first T-081 worker may start.");
  runtime = this;
  return create.call(this, task, attempt);
};
require.cache[modulePath]!.exports = { ...original, spawn(shell: string, argv: string[], options: any) {
  const env = options.env, launch = env.A2A_LAUNCH;
  if (!runtime || starts++ !== 0 || !uuid.test(launch) || !uuid.test(env.A2A_ATTEMPT))
    throw new Error("One fresh approved worker only; no restart.");
  const expected = policy.argv.map((v: string) => v.replaceAll("${LAUNCH_ID}", launch));
  const record = runtime.launchRecord(launch);
  const expectedShell = ["-f", "-i", "-c", expected.map(quote).join(" ") + "; exec /bin/zsh -f -i"];
  const gitKeys = Object.keys(env).filter((key) => key.startsWith("GIT_CONFIG_"));
  const ok = shell === "/bin/zsh" && options.cwd === policy.workspace &&
    env.CODEX_HOME === policy.codex_home && env.A2A_STATE === policy.state &&
    env.A2A_TASK === "T-081-CAP-04" && env.A2A_PROJECT === "t081-capability" && env.A2A_ROLE === "worker" &&
    env.A2A_MODEL_REQUESTED === "gpt-6.1-sol" && env.A2A_EFFORT_REQUESTED === "xhigh" &&
    !Object.hasOwn(env, "NODE_OPTIONS") && !Object.hasOwn(env, "T081_CAPABILITY_POLICY") &&
    gitKeys.length === 3 && Object.entries(policy.git_hook_environment).every(([key, value]) => env[key] === value) &&
    record.turn_limit === 1 && record.hook_authorization === policy.approval_ref &&
    record.turn_authorization === policy.approval_ref && record.service_tier_requested === "default" &&
    JSON.stringify(record.argv) === JSON.stringify(expected) && JSON.stringify(argv) === JSON.stringify(expectedShell);
  writeFileSync(join(policy.output, "launch-before-spawn.json"), JSON.stringify({
    ok, daemon_pid: process.pid, launch, attempt: env.A2A_ATTEMPT, session: env.A2A_SESSION,
    thread: env.A2A_SESSION ? record.thread : null, shell, argv: record.argv, shell_argv: argv,
    cwd: options.cwd, codex_home: env.CODEX_HOME, request_dir: record.request_dir,
    git_environment: Object.fromEntries(gitKeys.map((key) => [key, env[key]])),
    approval_ref: policy.approval_ref,
  }, null, 2) + "\n", { flag: "wx", mode: 0o600 });
  if (!ok) throw new Error("Actual worker argv differs from the approved policy; spawn refused.");
  const terminal = original.spawn(shell, argv, options);
  writeFileSync(join(policy.output, "spawned.json"), JSON.stringify({
    daemon_pid: process.pid, shell_pid: terminal.pid, launch,
  }, null, 2) + "\n", { flag: "wx", mode: 0o600 });
  return terminal;
} };
const dispatch = Panes.prototype.dispatch;
Panes.prototype.dispatch = async function (pane: any, text: string, source = "executor", context?: any) {
  if (dispatches++ !== 0 || source !== "executor" || context || pane.record.role !== "worker")
    throw new Error("Only the approved first dispatch is permitted.");
  const expand = (v: string) => v.replaceAll("${ATTEMPT_ID}", pane.record.attempt)
    .replaceAll("${SESSION_ID}", pane.record.session).replaceAll("${THREAD_ID}", pane.record.thread);
  const expected = expand(readFileSync(policy.first_turn_template, "utf8"));
  const actual = "⟦主控 #1⟧\n" + text;
  const ok = actual === expected;
  writeFileSync(join(policy.output, "first-turn-before-queue.json"), JSON.stringify({
    ok, launch: pane.record.id, actual, expected, approval_ref: policy.approval_ref,
  }, null, 2) + "\n", { flag: "wx", mode: 0o600 });
  if (!ok) throw new Error("Actual first turn differs from the approved prompt; dispatch refused.");
  return dispatch.call(this, pane, text, source, context);
};
