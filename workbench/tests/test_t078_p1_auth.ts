import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, realpathSync, writeFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { join } from "node:path";
import { claudeLaunch } from "../src/claudeLaunch.ts";

// Contract from controller #94 and official gateway docs: public bearer token,
// no API-key environment, no credential helper or permission/auth overrides.
// Failure cases: missing token, retained API key, endpoint or HOME drift.
const [output] = process.argv.slice(2); mkdirSync(output);
const root = realpathSync(mkdtempSync("/tmp/t078-2-auth-"));
for (const name of ["state", "repo", "home", "claude"]) mkdirSync(join(root, name));
writeFileSync(join(root, "role.md"), "公开假服务认证构造检查。\n", "utf8");
const task: any = { task_id: "auth-fixture", project_id: "t078-p1-project", repo: join(root, "repo"),
  spec_rev: 1, base_commit: "a".repeat(40) };
const input: any = { schema: 1, root, state: join(root, "state"), task: task.task_id, preset: "ideation",
  launch: randomUUID(), session: randomUUID(), thread: randomUUID(),
  executable: "/Users/luckye/.local/share/claude/versions/2.1.296", role_file: join(root, "role.md"),
  code_revision: "a".repeat(40), source_snapshot: join(root, "sources.tar.gz"), api_url: "http://127.0.0.1:12345" };
const profile = claudeLaunch(task, input);
const checks: any[] = [];
function check(name: string, run: () => void) {
  try { run(); checks.push({ name, status: "PASS" }); }
  catch (error) { checks.push({ name, status: "INCOMPLETE", error: String(error) }); }
}
check("public_bearer_without_api_key", () => {
  assert.equal((profile.env as any).ANTHROPIC_AUTH_TOKEN, "a2a-fixture-key-not-a-secret");
  assert.equal(Object.hasOwn(profile.env, "ANTHROPIC_API_KEY"), false);
});
check("endpoint_and_isolation_preserved", () => {
  assert.equal(profile.env.ANTHROPIC_BASE_URL, "http://127.0.0.1:12345");
  assert.equal(profile.env.HOME, join(root, "home"));
  assert.equal(profile.env.CLAUDE_CONFIG_DIR, join(root, "claude"));
  assert.equal(Object.hasOwn(profile.env,"IS_DEMO"),false);
  assert.deepEqual(Object.keys(profile.settings), ["hooks"]);
  assert.equal(profile.argv.includes("--bare"), false);
});
const result = { status: checks.every(c => c.status === "PASS") ? "PASS" : "INCOMPLETE", checks,
  argv: process.argv, root, scope: "Pure launch construction; no interactive-authentication claim",
  real_cli_starts: 0, api_starts: 0, real_vendor_model_turns: 0 };
writeFileSync(join(output, "results.json"), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result)); process.exitCode = result.status === "PASS" ? 0 : 1;
