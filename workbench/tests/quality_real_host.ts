// Audits two approved launches, then delegates to the original PTY and gates.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createRequire } from "node:module";
import { serve } from "../src/daemon.ts";
import { A2AGates } from "../src/gates/core.ts";

const [policyPath, configPath, ready] = process.argv.slice(2);
if (process.argv.length !== 5) throw new Error("Expected policy, config and ready paths.");
const policy = JSON.parse(readFileSync(policyPath, "utf8"));
const config = JSON.parse(readFileSync(configPath, "utf8"));
const require = createRequire(import.meta.url), modulePath = require.resolve("node-pty"), original = require(modulePath);
let panes: any;
const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
const quote = (v: string) => "'" + v.replaceAll("'", "'\\''") + "'";
require.cache[modulePath]!.exports = { ...original, spawn(shell: string, argv: string[], options: any) {
  const env = options.env, role = env.A2A_ROLE, launch = env.A2A_LAUNCH, attempt = env.A2A_ATTEMPT;
  if (!["worker", "reviewer"].includes(role) || !uuid.test(launch) || !uuid.test(attempt) ||
    (role === "reviewer" && !uuid.test(env.A2A_REVIEW))) throw new Error("Unexpected launch identity.");
  const selected = policy[role];
  const expand = (v: string) => v.replaceAll("${LAUNCH_ID}", launch).replaceAll("${ATTEMPT_ID}", attempt)
    .replaceAll("${REVIEW_ID}", env.A2A_REVIEW ?? "");
  const expected = selected.argv.map(expand), record = panes.launchRecord(launch);
  const shellArgv = ["-f", "-i", "-c", expected.map(quote).join(" ") + "; exec /bin/zsh -f -i"];
  const gitKeys = Object.keys(env).filter((k) => k.startsWith("GIT_CONFIG_"));
  const gitOK = role === "reviewer" ? gitKeys.length === 0 : gitKeys.length === 3 &&
    env.GIT_CONFIG_COUNT === "1" && env.GIT_CONFIG_KEY_0 === "core.hooksPath" && env.GIT_CONFIG_VALUE_0 === policy.git_hooks;
  const ok = shell === "/bin/zsh" && options.cwd === expand(selected.workspace) && env.CODEX_HOME === selected.home &&
    env.A2A_STATE === policy.state && env.A2A_TASK === policy.task && env.A2A_CLI === policy.cli && env.A2A_NODE === policy.node &&
    env.A2A_MODEL_REQUESTED === "gpt-6.1-sol" && env.A2A_EFFORT_REQUESTED === "xhigh" && gitOK &&
    record.role === role && record.sandbox === selected.sandbox && record.turn_limit === selected.record_turn_limit &&
    record.service_tier_requested === "default" && JSON.stringify(record.argv) === JSON.stringify(expected) &&
    JSON.stringify(argv) === JSON.stringify(shellArgv) && (role === "worker" || record.review_home_was_empty === true);
  const output = join(policy.root, "launch-" + role + "-before-spawn.json");
  if (existsSync(output)) throw new Error("One worker and one fresh reviewer only; no restart.");
  writeFileSync(output, JSON.stringify({ ok, role, launch, attempt, review: env.A2A_REVIEW ?? null,
    shell, shell_argv: argv, argv: record.argv, cwd: options.cwd, home: env.CODEX_HOME,
    git_environment: Object.fromEntries(gitKeys.map((key) => [key, env[key]])), request_dir: record.request_dir,
    real_runtime: true }, null, 2) + "\n", { flag: "wx", mode: 0o600 });
  if (!ok) throw new Error("Actual launch differs from the approved delivery policy.");
  return original.spawn(shell, argv, options);
} };
await serve(policy.state, config, (root, runtime) => { panes = runtime; return new A2AGates(root, runtime); });
writeFileSync(ready, JSON.stringify({ pid: process.pid, state: policy.state, argv: process.argv }) + "\n", { flag: "wx" });
