// Real P-review host. This observer checks the approved argv before delegating
// to the ORIGINAL node-pty spawn. It supplies no runtime identity or verdict.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createRequire } from "node:module";
import { serve } from "../src/daemon.ts";
import { A2AGates } from "../src/gates/core.ts";

const [policyPath, configPath, ready] = process.argv.slice(2);
if (process.argv.length !== 5) throw new Error("Expected policy, launch config and ready paths.");
const policy = JSON.parse(readFileSync(policyPath, "utf8"));
const config = JSON.parse(readFileSync(configPath, "utf8"));
const require = createRequire(import.meta.url), modulePath = require.resolve("node-pty");
const original = require(modulePath);
let panes: any;
const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
const quote = (v: string) => "'" + v.replaceAll("'", "'\\''") + "'";
require.cache[modulePath]!.exports = { ...original, spawn(shell: string, argv: string[], options: any) {
  const launch = options.env.A2A_LAUNCH, review = options.env.A2A_REVIEW;
  if (!uuid.test(launch) || !uuid.test(review)) throw new Error("Expected fresh product UUIDs.");
  const expand = (v: string) => v.replaceAll("${REVIEW_ID}", review).replaceAll("${LAUNCH_ID}", launch);
  const expectedArgv = policy.codex_argv.map(expand);
  const expectedShell = ["-f", "-i", "-c", expectedArgv.map(quote).join(" ") + "; exec /bin/zsh -f -i"];
  const record = panes.launchRecord(launch);
  const expectedEnvironment = { CODEX_HOME: policy.home, A2A_ROLE: "reviewer", A2A_TASK: policy.task,
    A2A_STATE: policy.state, A2A_CLI: policy.cli, A2A_MODEL_REQUESTED: "gpt-6.1-sol", A2A_EFFORT_REQUESTED: "xhigh" };
  const ok = shell === "/bin/zsh" && options.cwd === expand(policy.review_workspace) &&
    JSON.stringify(argv) === JSON.stringify(expectedShell) && JSON.stringify(record.argv) === JSON.stringify(expectedArgv) &&
    Object.entries(expectedEnvironment).every(([key,value]) => options.env[key] === value) &&
    !Object.keys(options.env).some((key) => key.startsWith("GIT_CONFIG_")) && record.role === "reviewer" &&
    record.sandbox === "read-only" && record.review_home_was_empty === true && record.service_tier_requested === "default";
  const output = join(policy.root, "launch-before-spawn.json");
  if (existsSync(output)) throw new Error("P-review permits exactly one native launch; no retry.");
  writeFileSync(output, JSON.stringify({ ok, shell, shell_argv: argv, cwd: options.cwd,
    codex_argv: record.argv, launch, review, request_dir: record.request_dir, expected_environment: expectedEnvironment,
    pid_before_spawn: null, real_runtime: true }, null, 2) + "\n", { flag: "wx", mode: 0o600 });
  if (!ok) throw new Error("Native launch differs from the approved P-review policy.");
  return original.spawn(shell, argv, options);
} };
await serve(policy.state, config, (root, runtime) => {
  panes = runtime;
  return new A2AGates(root, runtime);
});
writeFileSync(ready, JSON.stringify({ pid: process.pid, state: policy.state, argv: process.argv,
  boundary: "original gates, Panes, PTY and process observation; argv audit only" }) + "\n", { flag: "wx" });
