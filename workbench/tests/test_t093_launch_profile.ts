import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";
import { claudeLaunch } from "../src/claudeLaunch.ts";

const output = process.argv[2];
assert(output, "new summary path required");
const root = realpathSync(mkdtempSync("/private/tmp/t078-2-t093-profile-"));
const privateRoot = realpathSync(mkdtempSync("/private/tmp/a2a-claude-login-test-"));
const checks: any[] = [];
try {
  for (const name of ["state", "repo"]) mkdirSync(join(root, name));
  for (const name of ["home", "claude", "tmp", "shell", "requests", "hooks", "user-data"]) {
    mkdirSync(join(root, "roles", "ideation", name), { recursive: true });
  }
  for (const name of ["home", "home/.claude", "tmp", "shell"]) mkdirSync(join(privateRoot, name), { recursive: true });
  writeFileSync(join(root, "roles/ideation/role.md"), "隔离主控角色。\n");
  const task: any = { task_id: "t093-profile", project_id: "t093", repo: join(root, "repo"), spec_rev: 1, base_commit: "a".repeat(40) };
  const common: any = { schema: 1, root, state: join(root, "state"), task: task.task_id, preset: "ideation",
    launch: randomUUID(), session: randomUUID(), thread: randomUUID(), executable: "/usr/bin/true", version: "2.1.302",
    role_file: join(root, "roles/ideation/role.md"), code_revision: "a".repeat(40), source_snapshot: join(root, "source.json"),
    api_url: "http://127.0.0.1:23101", turn_limit: 3 };
  const isolation: any = { homeRoot: privateRoot, home: join(privateRoot, "home"), config: join(privateRoot, "home/.claude"),
    tmp: join(privateRoot, "tmp"), shell: join(privateRoot, "shell"), debug: join(privateRoot, "debug.log"),
    api_url: "http://127.0.0.1:23102", audit_directory: join(root, "audit") };
  const normal = { ...common, authentication: "normal-login", credential_source: "file", upstream_url: "http://127.0.0.1:443" };
  const check = (name: string, run: () => void) => {
    try { run(); checks.push({ name, status: "PASS" }); }
    catch (error) { checks.push({ name, status: "INCOMPLETE", error: String(error) }); }
  };
  check("normal_login_uses_private_auth_without_fake_token", () => {
    const profile = (claudeLaunch as any)(task, normal, isolation);
    assert.equal(profile.authentication, "isolated normal login");
    assert.equal(profile.env.HOME, isolation.home);
    assert.equal(profile.env.CLAUDE_CONFIG_DIR, isolation.config);
    assert.equal(profile.env.ANTHROPIC_BASE_URL, isolation.api_url);
    assert.equal(Object.hasOwn(profile.env, "ANTHROPIC_AUTH_TOKEN"), false);
    assert.equal(Object.hasOwn(profile.env, "ANTHROPIC_API_KEY"), false);
  });
  check("claude_native_factory_defaults_and_overrides", () => {
    const profile = claudeLaunch(task, common);
    assert.equal(profile.argv[profile.argv.indexOf('--model') + 1], 'claude-haiku-5-5');
    assert.equal(profile.argv[profile.argv.indexOf('--effort') + 1], 'low');
    assert.equal(profile.settings.fastMode, false);
    const overridden = claudeLaunch(task, { ...common, execution: { model: 'opus', effort: 'high', fast: true } });
    assert.equal(overridden.argv[overridden.argv.indexOf('--model') + 1], 'opus');
    assert.equal(overridden.argv[overridden.argv.indexOf('--effort') + 1], 'high');
    assert.equal(overridden.settings.fastMode, true);
    assert.ok(overridden.argv.includes('--permission-mode'));
    assert.equal(overridden.argv[overridden.argv.indexOf('--permission-mode') + 1], 'manual');
  });
  check("normal_login_keeps_existing_hook_and_stop_contract", () => {
    const profile = (claudeLaunch as any)(task, normal, isolation);
    assert.deepEqual(Object.keys(profile.settings.hooks), ["UserPromptSubmit", "Stop", "PermissionRequest", "PreToolUse", "PostToolUse", "PostToolUseFailure"]);
    for (const entries of Object.values(profile.settings.hooks) as any[]) {
      assert(entries[0].hooks[0].command.includes(" signal --launch ") || entries[0].hooks[0].command.includes("'signal' '--launch'"));
      assert(entries[0].hooks[0].command.includes(normal.launch));
    }
    assert.equal(profile.turn_limit, 3);
    assert.equal(profile.shell_argv.at(-1).includes("sandbox-exec"), false, "CLI inherits the single outer profile");
    assert.equal(profile.shell_argv.at(-1).includes("; exec /bin/zsh"), false);
  });
  check("normal_login_records_current_version_without_release_lock", () => {
    const profile = (claudeLaunch as any)(task, { ...normal, version: "2.1.304" }, isolation);
    assert.equal(profile.cli_version_expected, "2.1.304 (Claude Code)");
    assert.equal(profile.role_card_revision, "T-093/normal-login/2.1.304");
    for (const version of ["", "unknown", "2.1", "2.1.304\n"]) {
      assert.throws(() => (claudeLaunch as any)(task, { ...normal, version }, isolation));
    }
  });
  check("fixture_entry_still_refuses_real_api_address", () => {
    assert.throws(() => claudeLaunch(task, { ...common, api_url: "https://api.anthropic.com" }),
      (e: any) => e.code === "local_messages_api_required");
  });
  const current = readFileSync(new URL("../src/claudeLaunch.ts", import.meta.url), "utf8");
  const original = execFileSync("git", ["show", "617863704:workbench/src/claudeLaunch.ts"], { encoding: "utf8" });
  const result = { task: "T-093", status: checks.every(c => c.status === "PASS") ? "PASS" : "INCOMPLETE", checks,
    main_revision: "61786370428c3ec5f894ea60acccf2695d54c2dc", source_equals_main: current === original,
    scope: "真实构造入口；不启动 CLI、不读取登录凭据", real_cli_starts: 0, real_credential_reads: 0 };
  writeFileSync(output, JSON.stringify(result, null, 2) + "\n", { flag: "wx" });
  console.log(JSON.stringify({ status: result.status, checks: checks.length, source_equals_main: result.source_equals_main }));
  process.exitCode = result.status === "PASS" ? 0 : 1;
} finally { rmSync(root, { recursive: true }); rmSync(privateRoot, { recursive: true }); }
