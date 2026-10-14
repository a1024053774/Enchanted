import { readFileSync, realpathSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { A2ATask } from "./contracts/a2aGates.ts";
import { Refusal } from "./gates/core.ts";

export interface ClaudeLaunchInput {
  schema: 1; root: string; state: string; task: string; preset: "ideation" | "executor";
  launch: string; session: string; thread: string; executable: string;
  role_file: string; code_revision: string; source_snapshot: string; api_url: string;
}
const quote = (s: string) => "'" + s.replaceAll("'", "'\\''") + "'";
const requireValue = (v: unknown, code: string) => { if (!v) throw new Refusal(code); };

// T-078-2 P1: only the approved isolated fake-API profile exists. Normal-login
// launch and multi-turn completion await P2/P3 protocol evidence and approval.
export function claudeLaunch(task: A2ATask, input: ClaudeLaunchInput) {
  requireValue(input.schema === 1 && ["ideation", "executor"].includes(input.preset) && input.task === task.task_id, "invalid_controller_launch");
  for (const field of ["launch", "session", "thread"] as const) requireValue(/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(input[field]), "invalid_controller_identity");
  const root = realpathSync(input.root), state = realpathSync(input.state), repo = realpathSync(task.repo);
  requireValue(root.startsWith("/private/tmp/t078-2-") && input.root === root && state === join(root, "state") && repo === join(root, "repo"), "isolated_controller_root_required");
  requireValue(input.executable === "/Users/luckye/.local/share/claude/versions/2.1.296" && isAbsolute(input.role_file) &&
    realpathSync(input.role_file) === join(root, "role.md") && /^[0-9a-f]{40}$/.test(input.code_revision) &&
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
    "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--tools", "Bash,Read", "--disable-slash-commands", "--debug-file", join(root,"claude-debug.log")];
  const env = { PATH: "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin", SHELL: "/bin/zsh", TERM: "xterm-256color",
    COLORTERM: "truecolor", LANG: "en_US.UTF-8", LC_CTYPE: "UTF-8", TMPDIR: join(root, "tmp"), ZDOTDIR: join(root, "shell"),
    HOME: realpathSync(join(root, "home")), CLAUDE_CONFIG_DIR: realpathSync(join(root, "claude")), DISABLE_AUTOUPDATER: "1", CLAUDE_CODE_DISABLE_TERMINAL_TITLE: "1",
    ANTHROPIC_BASE_URL: url.origin, ANTHROPIC_AUTH_TOKEN: "a2a-fixture-key-not-a-secret",
    A2A_PROJECT: task.project_id, A2A_TASK: task.task_id, A2A_SESSION: input.session, A2A_ROLE: "controller",
    A2A_PRESET: input.preset, A2A_LAUNCH: input.launch, A2A_STATE: state, A2A_NATIVE_SESSION: input.session,
    A2A_REQUEST_DIR: join(root, "requests"), A2A_HOOK_TRACE_DIR: join(root,"hooks") };
  requireValue(env.HOME === join(root, "home") && env.CLAUDE_CONFIG_DIR === join(root, "claude"), "isolated_controller_home_required");
  return { id: input.launch, project: task.project_id, task: task.task_id, attempt: null, session: input.session, fence: null,
    spec_rev: task.spec_rev, thread: input.thread, role: "controller", preset: input.preset, cli: "Claude Code",
    cli_version_expected: "2.1.296 (Claude Code)", node_executable: process.execPath, node_version: process.version,
    argv, settings, env, worktree: repo,
    shell: "/bin/zsh", shell_argv: ["-f", "-i", "-c", argv.map(quote).join(" ") + "; exec /bin/zsh -f -i"],
    role_card: input.role_file, role_card_revision: "T-078-2/P1", role_text: roleText,
    code_revision: input.code_revision, source_snapshot: input.source_snapshot, base_commit: task.base_commit, model_requested: "claude-haiku-5-5", effort_requested: "low",
    authentication: "isolated fake API only", turn_limit: 1, hook_authorization: "controller-decision-04/P1", execution_state: "started" };
}
