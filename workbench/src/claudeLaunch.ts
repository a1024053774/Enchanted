import { readFileSync, realpathSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { A2ATask } from "./contracts/a2aGates.ts";
import { Refusal } from "./gates/core.ts";

export interface ClaudeLaunchInput {
  schema: 1; root: string; state: string; task: string; preset: "ideation" | "executor";
  launch: string; session: string; thread: string; executable: string; version: string;
  role_file: string; code_revision: string; source_snapshot: string; api_url: string;
  turn_limit?: number;
}
const quote = (s: string) => "'" + s.replaceAll("'", "'\\''") + "'";
const requireValue = (v: unknown, code: string) => { if (!v) throw new Refusal(code); };

// T-078-2 P1: only the approved isolated fake-API profile exists. Normal-login
// launch and multi-turn completion await P2/P3 protocol evidence and approval.
export function claudeLaunch(task: A2ATask, input: ClaudeLaunchInput) {
  requireValue(input.schema === 1 && ["ideation", "executor"].includes(input.preset) && input.task === task.task_id, "invalid_controller_launch");
  const turnLimit=input.turn_limit??1;
  requireValue(Number.isInteger(turnLimit) && turnLimit >= 1 && turnLimit <= 6,"invalid_controller_turn_limit");
  for (const field of ["launch", "session", "thread"] as const) requireValue(/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(input[field]), "invalid_controller_identity");
  const root = realpathSync(input.root), state = realpathSync(input.state), repo = realpathSync(task.repo);
  requireValue(root.startsWith("/private/tmp/t078-2-") && input.root === root && state === join(root, "state") && repo === join(root, "repo"), "isolated_controller_root_required");
  const roleRoot = join(root, "roles", input.preset);
  const rolePaths = {
    home: join(roleRoot, "home"), config: join(roleRoot, "claude"), tmp: join(roleRoot, "tmp"), shell: join(roleRoot, "shell"),
    requests: join(roleRoot, "requests"), hooks: join(roleRoot, "hooks"), userData: join(roleRoot, "user-data"), debug: join(roleRoot, "claude-debug.log"),
  };
  requireValue(realpathSync(roleRoot) === roleRoot &&
    realpathSync(rolePaths.home) === rolePaths.home && realpathSync(rolePaths.config) === rolePaths.config &&
    realpathSync(rolePaths.tmp) === rolePaths.tmp && realpathSync(rolePaths.shell) === rolePaths.shell &&
    realpathSync(rolePaths.requests) === rolePaths.requests && realpathSync(rolePaths.hooks) === rolePaths.hooks &&
    realpathSync(rolePaths.userData) === rolePaths.userData, "isolated_controller_role_root_required");
  requireValue(typeof input.executable === "string" && isAbsolute(input.executable) &&
    typeof input.version === "string" && /^\d+\.\d+\.\d+$/.test(input.version) && isAbsolute(input.role_file) &&
    realpathSync(input.role_file) === join(roleRoot, "role.md") && /^[0-9a-f]{40}$/.test(input.code_revision) &&
    typeof input.source_snapshot === "string" && isAbsolute(input.source_snapshot), "controller_launch_config_required");
  const url = new URL(input.api_url);
  requireValue(url.protocol === "http:" && url.hostname === "127.0.0.1" && url.port && url.pathname === "/" && !url.username && !url.password && !url.search && !url.hash, "local_messages_api_required");
  const cli = fileURLToPath(new URL("./gates/cli.ts", import.meta.url));
  const signal = [process.execPath, cli, "--state", state, "signal", "--launch", input.launch].map(quote).join(" ");
  const settings = { hooks: Object.fromEntries(["UserPromptSubmit", "Stop", "PermissionRequest"].map(name =>
    [name, [{ hooks: [{ type: "command", command: signal, timeout: 3 }] }]])) };
  const roleText = new TextDecoder("utf-8", { fatal: true }).decode(readFileSync(input.role_file));
  const argv = [input.executable, "--session-id", input.session, "--model", "claude-haiku-5-5", "--effort", "low",
    "--permission-mode", "manual", "--settings", JSON.stringify(settings), "--append-system-prompt", roleText,
    "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--tools", "Bash,Read", "--disable-slash-commands", "--debug-file", rolePaths.debug];
  const env = { PATH: "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin", SHELL: "/bin/zsh", TERM: "xterm-256color",
    COLORTERM: "truecolor", LANG: "en_US.UTF-8", LC_CTYPE: "UTF-8", TMPDIR: rolePaths.tmp, ZDOTDIR: rolePaths.shell,
    HOME: rolePaths.home, CLAUDE_CONFIG_DIR: rolePaths.config, A2A_USER_DATA: rolePaths.userData, CLAUDE_CODE_DISABLE_TERMINAL_TITLE: "1",
    ANTHROPIC_BASE_URL: url.origin, ANTHROPIC_AUTH_TOKEN: "a2a-fixture-key-not-a-secret",
    A2A_PROJECT: task.project_id, A2A_TASK: task.task_id, A2A_SESSION: input.session, A2A_ROLE: "controller",
    A2A_PRESET: input.preset, A2A_LAUNCH: input.launch, A2A_STATE: state, A2A_NATIVE_SESSION: input.session,
    A2A_SPEC_REV: String(task.spec_rev),
    A2A_REQUEST_DIR: rolePaths.requests, A2A_HOOK_TRACE_DIR: rolePaths.hooks };
  requireValue(env.HOME === rolePaths.home && env.CLAUDE_CONFIG_DIR === rolePaths.config && env.A2A_USER_DATA === rolePaths.userData,
    "isolated_controller_home_required");
  return { id: input.launch, project: task.project_id, task: task.task_id, attempt: null, session: input.session, fence: null,
    spec_rev: task.spec_rev, thread: input.thread, role: "controller", preset: input.preset, cli: "Claude Code",
    cli_version_expected: `${input.version} (Claude Code)`,
    node_executable: process.execPath, node_version: process.version,
    argv, settings, env, worktree: repo,
    shell: "/bin/zsh", shell_argv: ["-f", "-i", "-c", argv.map(quote).join(" ") + "; exec /bin/zsh -f -i"],
    role_card: input.role_file, role_card_revision: "T-078-2/P1", role_text: roleText,
    code_revision: input.code_revision, source_snapshot: input.source_snapshot, base_commit: task.base_commit, model_requested: "claude-haiku-5-5", effort_requested: "low",
    authentication: "isolated fake API only", turn_limit: turnLimit, hook_authorization: "controller-decision-04/P1", execution_state: "started" };
}
