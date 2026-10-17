// Run only through run_t093_login_chain.py, outside the caller's sandbox.
// Real daemon, PTY, process identity, native hook CLI and Stop relay. The sole
// provider is a compiled deterministic fixture. No vendor process is spawned.
import assert from "node:assert/strict";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { randomUUID } from "node:crypto";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { createServer } from "node:http";
import { serve } from "../src/daemon.ts";
import { A2AGates } from "../src/gates/core.ts";
import { createOperatorCredential, readOperatorCredential } from "../src/credentials.ts";
import { request } from "../src/transport.ts";
import { credentialHits, countForwarderRecords } from "../src/claudeLoginFacts.ts";

const output = resolve(process.argv[2]); assert(!existsSync(output), "preserve earlier evidence");
const root = realpathSync(mkdtempSync("/private/tmp/t093-chain-")), state = join(root, "state");
const originalHome = process.env.HOME;
const sourceHome = join(root, "source-home"), token = "synthetic-login-only-" + randomUUID();
const exec = promisify(execFile), checks: string[] = [];
let panes: any, gates: any, failure: string | null = null, daemonStarted = false, launch: any, facts: any;
let upstreamReceived = 0;
const upstream = createServer((req, res) => {
  assert.equal(req.method, "POST"); assert.equal(req.url, "/v1/messages");
  assert.equal(req.headers.authorization, "Bearer " + token);
  const ledger = join(state, "login-audits", launch.id, "requests.jsonl");
  const requests = readFileSync(ledger, "utf8").split("\n").filter(Boolean).map(JSON.parse).filter(row => row.kind === "request");
  assert.equal(requests.length, upstreamReceived + 1, "ledger must exist before receipt");
  let body = ""; req.on("data", bytes => body += bytes); req.on("end", () => {
    assert(Array.isArray(JSON.parse(body).messages)); upstreamReceived++;
    res.writeHead(upstreamReceived === 1 ? 400 : 200, { "content-type": "application/json" }).end("{}");
  });
});
async function wait(test: () => boolean, name: string, timeout = 20_000) {
  const until = Date.now() + timeout;
  while (!test()) { if (Date.now() > until) throw new Error(name); await new Promise(resolve => setTimeout(resolve, 30)); }
}
try {
  for (const name of ["state", "repo", "source-home/.claude"]) mkdirSync(join(root, name), { recursive: true, mode: 0o700 });
  for (const name of ["home", "claude", "tmp", "shell", "requests", "hooks", "user-data"]) mkdirSync(join(root, "roles/ideation", name), { recursive: true, mode: 0o700 });
  writeFileSync(join(root, "roles/ideation/role.md"), "确定性正常登录链路测试。\n");
  writeFileSync(join(sourceHome, ".claude/.credentials.json"), JSON.stringify({ claudeAiOauth: { accessToken: token, refreshToken: "synthetic-refresh-" + randomUUID(), expiresAt: Date.now() + 600_000 } }), { mode: 0o600 });
  writeFileSync(join(sourceHome, "private-sentinel"), "protected fixture home\n", { mode: 0o600 });
  const executable = join(root, "fake-claude");
  await exec("/usr/bin/clang", ["-O0", "-Wall", "-Werror", resolve("workbench/tests/t093_fake_claude.c"), "-o", executable], { timeout: 30_000 });
  copyFileSync(resolve("workbench/tests/t093_fake_login_peer.py"), join(root, "fake-login-peer.py"));
  await new Promise<void>(resolve => upstream.listen(0, "127.0.0.1", resolve));
  const upstreamPort = (upstream.address() as any).port;
  writeFileSync(join(root, "upstream-port"), String(upstreamPort));
  process.env.HOME = sourceHome;
  process.env.A2A_OPERATOR_CREDENTIAL = join(root, "operator.json");
  createOperatorCredential(state); const operator = readOperatorCredential(state)!;
  await serve(state, {}, (directory, value) => { panes = value; gates = new A2AGates(directory, value); return gates; });
  daemonStarted = true;
  const task: any = { task_id: "t093-chain", project_id: "t093-fixture", repo: join(root, "repo"), spec_rev: 1,
    base_commit: "a".repeat(40), state: "registered", current_attempt: null };
  panes.store.db.prepare("INSERT INTO tasks VALUES (?,?)").run(task.task_id, JSON.stringify(task));
  panes.store.db.prepare("INSERT INTO inbox_records VALUES (?,?)").run("t093-independent-sentinel", JSON.stringify({ schema: 1,
    id: "t093-independent-sentinel", kind: "report", from: "ideation", to: "executor", body: "独立 Stop 转交哨兵", reply_to: null, refs: [], created_at: new Date().toISOString() }));
  const manifest = { schema: 1, root, state, task: task.task_id, preset: "ideation", launch: randomUUID(), session: randomUUID(), thread: randomUUID(),
    executable, version: "2.1.302", role_file: join(root, "roles/ideation/role.md"), code_revision: "a".repeat(40), source_snapshot: root,
    authentication: "normal-login", credential_source: "file", upstream_url: `http://127.0.0.1:${upstreamPort}`, turn_limit: 3 };
  const started = await request(state, { command: "controller_start", task: task.task_id, manifest }, operator);
  assert.equal(started.ok, true, "controller_start failed: " + started.error); launch = started.launch;
  const trace = join(state, "traces", launch.id, "pty.raw");
  await wait(() => readFileSync(trace, "utf8").includes("fixture-ready"), "fixture startup deadline");
  assert(readFileSync(trace, "utf8").includes("fixture-sandbox-child-protection-PASS"));
  checks.push("controller_start; sandboxed child cannot read/write source HOME or connect to another port");
  const released = await request(state, { command: "pane_release", thread: launch.thread, reason: "deterministic fixture ready" }, operator);
  assert.equal(released.ok, true);
  const dispatched = await request(state, { command: "pane_dispatch", thread: launch.thread, body: "请通过原生 inbox list 读取 executor 收件箱并在 Stop 转交。" }, operator);
  assert.equal(dispatched.ok, true);
  await wait(() => readFileSync(trace, "utf8").includes("fixture-turn-2-complete"), "two hook/Stop cycles deadline");
  assert.equal(upstreamReceived, 2);
  const results = panes.store.db.prepare("SELECT data FROM relay_results").all().map((row: any) => JSON.parse(row.data));
  assert.equal(results.length, 1); assert.equal(results[0].ok, true);
  assert.deepEqual(results[0].entries.map((entry: any) => entry.entry.id), ["t093-independent-sentinel"]);
  assert.equal(panes.status(launch.thread).state, "idle");
  checks.push("actual UserPromptSubmit and Stop transfer queued native inbox request exactly once; feedback completes");
  assert.equal(credentialHits(JSON.stringify(panes.store.read()), [token]), 0);
  const stopped = await request(state, { command: "daemon_stop" }, operator); assert.equal(stopped.ok, true);
  await wait(() => !existsSync(join(state, "daemon.pid")), "daemon shutdown deadline"); daemonStarted = false;
  const audit = join(state, "login-audits", launch.id);
  facts = JSON.parse(readFileSync(join(audit, "facts.json"), "utf8"));
  assert.equal(facts.counts.counts_match, true); assert.equal(facts.counts.model_requests, 2);
  assert.equal(facts.forwarder.forwarded, upstreamReceived); assert.equal(facts.credential_scan.hits, 0);
  assert.equal(facts.isolated_home_removed, true); assert.equal(existsSync(launch.env.HOME), false);
  assert.deepEqual(facts.inventory.changed, []); assert.equal(facts.onboarding.preflight_observed, false);
  const checked = await exec(process.execPath, [resolve("workbench/src/claudeLoginCheck.ts"), audit]);
  assert.equal(JSON.parse(checked.stdout).counts.model_requests, upstreamReceived);
  checks.push("fact command recounts all attempts; private HOME removed; inventory unchanged; credential scan zero");
  const ledger = join(audit, "requests.jsonl");
  const rows = readFileSync(ledger, "utf8").split("\n");
  writeFileSync(ledger, rows.filter(line => !line.includes('"kind":"request","sequence":2')).join("\n"));
  assert.equal(countForwarderRecords(ledger, upstreamReceived).counts_match, false);
  checks.push("end-to-end missing raw request row is detected");
} catch (error) { failure = error instanceof Error ? error.message : "chain_failed"; }
finally {
  if (daemonStarted) {
    try { await request(state, { command: "daemon_stop" }, readOperatorCredential(state)); await wait(() => !existsSync(join(state, "daemon.pid")), "cleanup deadline"); }
    catch { failure = "daemon_cleanup_unconfirmed"; }
  }
  upstream.closeAllConnections(); await new Promise<void>(resolve => upstream.close(() => resolve()));
  if (launch?.env?.HOME) assert.equal(existsSync(launch.env.HOME), false, "private HOME cleanup must finish");
  if (originalHome === undefined) delete process.env.HOME; else process.env.HOME = originalHome;
  const result = { status: failure ? "INCOMPLETE" : "PASS", task: "T-093", checks, failure,
    upstream_requests: upstreamReceived, real_upstream_requests: 0, real_cli_starts: 0,
    auth_source: "synthetic fixture HOME only", facts, fixture_removed: false };
  // Private source, generated executable, sqlite and raw PTY stay out of evidence.
  // Preserve the failure class and completed checks in the new summary file.
  rmSync(root, { recursive: true }); result.fixture_removed = !existsSync(root);
  writeFileSync(output, JSON.stringify(result, null, 2) + "\n", { flag: "wx", mode: 0o600 });
  console.log(JSON.stringify({ status: result.status, checks: checks.length, failure, upstream_requests: upstreamReceived }));
  process.exitCode = failure ? 2 : 0;
}
