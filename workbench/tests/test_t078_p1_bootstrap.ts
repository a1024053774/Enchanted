import assert from "node:assert/strict";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { claudeLaunch } from "../src/claudeLaunch.ts";

// Independent contract: controller #91 permits only theme=dark and IS_DEMO=1.
// Failure cases: missing demo variable; absent or extra settings; approval drift;
// preseeded internal key/trust/onboarding state. This test starts no vendor CLI.
const [materials, output] = process.argv.slice(2);
mkdirSync(output);
const approval = JSON.parse(readFileSync(join(materials, "approval.json"), "utf8"));
const input = approval.input;
const task: any = { task_id: input.task, project_id: "t078-p1-project", repo: join(input.root, "repo"),
  spec_rev: 1, base_commit: input.code_revision };
const profile = claudeLaunch(task, input);
const checks: any[] = [];
function check(name: string, run: () => void) {
  try { run(); checks.push({ name, status: "PASS" }); }
  catch (error) { checks.push({ name, status: "INCOMPLETE", error: String(error) }); }
}
check("isolated_demo_environment", () => {
  assert.equal(profile.env.IS_DEMO, "1");
  assert.equal(approval.launch.env.IS_DEMO, "1");
  assert.equal(profile.env.HOME, join(input.root, "home"));
  assert.equal(profile.env.CLAUDE_CONFIG_DIR, join(input.root, "claude"));
});
check("isolated_theme_is_only_setting", () => {
  const settings = readFileSync(join(input.root, "claude/settings.json"));
  assert.deepEqual(JSON.parse(settings.toString("utf8")), { theme: "dark" });
  assert.deepEqual(settings, readFileSync(join(materials, "isolated-settings.json")));
});
check("no_internal_state_preseed", () => {
  assert.equal(existsSync(join(input.root, "claude/.claude.json")), false);
  assert.equal(existsSync(join(input.root, "home/.claude.json")), false);
  assert.deepEqual(Object.keys(profile.settings), ["hooks"]);
  assert.equal(profile.argv.includes("--bare"), false);
});
const result = { status: checks.every(c => c.status === "PASS") ? "PASS" : "INCOMPLETE", checks,
  argv: process.argv, scope: "Static profile and prepared files only; onboarding remains unverified",
  real_cli_starts: 0, api_starts: 0, real_vendor_model_turns: 0 };
writeFileSync(join(output, "results.json"), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result));
process.exitCode = result.status === "PASS" ? 0 : 1;
