// Isolated audit contract test. PTY spawn is a spy; no CLI, daemon or auth access.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import { resolve, join } from "node:path";

const [mode, destination, auditFile] = process.argv.slice(2);
if (!["allowed", "tier-mismatch"].includes(mode) || !destination || !auditFile)
  throw new Error("Expected allowed|tier-mismatch, fresh output and audit module.");
const output = resolve(destination);
mkdirSync(output);
const root = resolve(import.meta.dirname, "../..");
const review = join(root, "evidence/2026-10-14-batch14/T-081/capability-review-04");
const policy = JSON.parse(readFileSync(join(review, "launch-policy.first-turn.pending.json"), "utf8"));
Object.assign(policy, { approval_ref: "T-081 controller-decision-04 capability-turn-3", output,
  source: policy.root + "/source", workspace: policy.argv[policy.argv.indexOf("-C") + 1],
  first_turn_template: join(review, "FIRST-TURN.template.md") });
writeFileSync(join(output, "policy.json"), JSON.stringify(policy), { flag: "wx" });
process.env.T081_CAPABILITY_POLICY = join(output, "policy.json");
const { Panes } = await import(pathToFileURL(join(policy.source, "workbench/src/panes.ts")).href);
Panes.prototype.createThread = async function () {};
Panes.prototype.dispatch = async function () { return { test_only: true }; };
const require = createRequire(pathToFileURL(join(policy.source, "workbench/package.json")));
const modulePath = require.resolve("node-pty"), original = require(modulePath);
let spawns = 0;
require.cache[modulePath]!.exports = { ...original, spawn() { spawns++; return { pid: 999999 }; } };
await import(pathToFileURL(resolve(auditFile)).href);
const launch = "00000000-0000-4000-8000-000000000101";
const attempt = "00000000-0000-4000-8000-000000000102";
const session = "00000000-0000-4000-8000-000000000103";
const thread = "00000000-0000-4000-8000-000000000104";
const argv = policy.argv.map((v: string) => v.replaceAll("${LAUNCH_ID}", launch));
if (mode === "tier-mismatch") argv[argv.indexOf('service_tier="default"')] = 'service_tier="priority"';
const record = { id: launch, attempt, session, thread, role: "worker", turn_limit: 1,
  hook_authorization: policy.approval_ref, turn_authorization: policy.approval_ref,
  service_tier_requested: "default", argv, request_dir: "/tmp/test-only-no-requests" };
const runtime = { launchRecord: () => record };
await Panes.prototype.createThread.call(runtime, { task_id: "T-081-CAP-04" }, { fence: 1 });
const quote = (v: string) => "'" + v.replaceAll("'", "'\\''") + "'";
const shellArgv = ["-f", "-i", "-c", argv.map(quote).join(" ") + "; exec /bin/zsh -f -i"];
const env = { ...policy.git_hook_environment, A2A_LAUNCH: launch, A2A_ATTEMPT: attempt,
  A2A_SESSION: session, A2A_STATE: policy.state, A2A_TASK: "T-081-CAP-04", A2A_PROJECT: "t081-capability",
  A2A_ROLE: "worker", A2A_MODEL_REQUESTED: "gpt-6.1-sol", A2A_EFFORT_REQUESTED: "xhigh",
  CODEX_HOME: policy.codex_home };
let error: string | null = null;
try { require(modulePath).spawn("/bin/zsh", shellArgv, { cwd: policy.workspace, env }); }
catch (caught) { error = String(caught); }
let passed = mode === "allowed" ? !error && spawns === 1 : Boolean(error) && spawns === 0;
if (mode === "allowed" && passed) {
  const full = readFileSync(policy.first_turn_template, "utf8")
    .replaceAll("${ATTEMPT_ID}", attempt).replaceAll("${SESSION_ID}", session).replaceAll("${THREAD_ID}", thread);
  await Panes.prototype.dispatch.call(runtime, { record }, full.slice("⟦主控 #1⟧\n".length));
  passed = JSON.parse(readFileSync(join(output, "first-turn-before-queue.json"), "utf8")).ok;
}
const result = { status: passed ? "PASS" : "INCOMPLETE", mode, passed, spawns, error,
  failure_id: passed ? null : "AUDIT-BLOCK-BEFORE-SPAWN", real_codex_turns: 0, mocked_pty: true,
  scope: "只证明实际 argv/文本审计边界；未启动真实 PTY、Codex 或 daemon" };
writeFileSync(join(output, "run.json"), JSON.stringify(result, null, 2) + "\n", { flag: "wx" });
process.stdout.write(JSON.stringify(result) + "\n");
process.exitCode = passed ? 0 : 1;
