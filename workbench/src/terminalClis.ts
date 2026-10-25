// T-184, T-187: the CLIs Enchanted's project-terminal shims wrap (terminal/bin), in one place. New CLIs join here.
// - wired: whether a running one came through its shim. The fact is the process's own launch: the shim always adds its
//   launch arguments or, where a CLI has no harmless argument to add, names itself as A2A_SHIM in the environment. A CLI
//   started by its real path or another alias lacks them: no orientation, no turn states, no role records.
// - turns: where its turn states come from. "hooks": Enchanted's hooks report each turn (claude, codex). "osc7501": the
//   CLI reports its own state to the terminal as OSC 7501 (T-187 facts: agy needs AGY_CLI_OSC7501=on, opencode always).
// - inCommand: whether a command (`a2a request`) may run inside it, from the environment the CLI gives its commands. A
//   CLI started inside another inherits the outer one's variable too; then the nearest one among the command's
//   ancestor processes is the one that runs it (commandCli).
// - managed: how the backend starts it as a worker or reviewer (T-187, ready_rev 2), for the CLIs that report their own
//   turns; the gate rebuilds a reviewer's launch with it to compare. Neither has an OS sandbox: agy approves every tool
//   itself (the user's choice C, 2026-10-25), opencode approves what its configuration does not deny; the gate checks
//   afterwards. opencode takes its model through per-session configuration and has no effort setting.
export type LaunchFacts = { argv: string[]; shim: string | null };
export type ManagedLaunch = { executable: string; workspace: string; model: string; effort: string; extraDirectories: string[] };
export type TerminalCli = { wired: (launch: LaunchFacts) => boolean; turns: "hooks" | "osc7501";
  inCommand: (env: NodeJS.ProcessEnv) => boolean;
  managed?: (launch: ManagedLaunch) => { argv: string[]; env: Record<string, string> } };

export const terminalClis: Record<string, TerminalCli> = {
  claude: { turns: "hooks", inCommand: env => Boolean(env.CLAUDECODE),
    wired: ({ argv }) => argv.some((arg, index) => arg === "--plugin-dir" && (argv[index + 1] ?? "").endsWith("/plugin/enchanted-a2a")) },
  // The hook commands name the a2a shim through the terminal's environment, unexpanded in the argument itself.
  codex: { turns: "hooks", inCommand: env => Boolean(env.CODEX_THREAD_ID), wired: ({ argv }) => argv.some(arg => arg.includes('$A2A_TERMINAL_BIN/a2a')) },
  opencode: { turns: "osc7501", inCommand: env => Boolean(env.OPENCODE_SESSION_ID), wired: ({ shim }) => shim === "opencode",
    managed: ({ executable, workspace, model }) => ({ argv: [executable, "--standalone", "--auto", workspace],
      env: { OPENCODE_CONFIG_CONTENT: JSON.stringify({ model }) } }) },
  agy: { turns: "osc7501", inCommand: env => env.A2A_SHIM === "agy", wired: ({ shim }) => shim === "agy",
    managed: ({ executable, model, effort, extraDirectories }) => ({ argv: [executable, "--dangerously-skip-permissions",
      "--model", model, "--effort", effort, ...extraDirectories.flatMap(path => ["--add-dir", path])], env: { AGY_CLI_OSC7501: "on" } }) },
};

// Which registered CLI a process runs, from its argv. A CLI installed as a script (npm) runs as `node <path>/<cli>`.
const RUNTIMES = new Set(["node", "bun", "deno"]);
export function cliProgram(argv: string[]): string | undefined {
  const program = (index: number) => (argv[index] ?? "").split("/").at(-1)!;
  const name = RUNTIMES.has(program(0)) ? program(1) : program(0);
  return Object.hasOwn(terminalClis, name) ? name : undefined;
}

// ancestors: the argv of the command's ancestor processes, nearest first; read only when two CLIs claim it.
export function commandCli(env: NodeJS.ProcessEnv, ancestors: () => string[][]): string | undefined {
  const claimed = Object.keys(terminalClis).filter(name => terminalClis[name].inCommand(env));
  if (claimed.length < 2) return claimed[0];
  return ancestors().map(cliProgram).find(name => name !== undefined && claimed.includes(name));
}

// One OSC 7501 report: `ESC ] 7501 ; state=<s>[:id=..][:kind=<k>][:app=..][:msg=<base64>] (BEL | ESC \)`. A bare `?` is
// the CLI asking whether the terminal supports it, not a state.
// msg: the decoded text a report carries (agy: the question, the permission asked, the last reply).
export type CliTurn = { state: string; kind: string | null; msg: string | null };
const OSC7501 = /\x1b\]7501;([^\x07\x1b]*)(?:\x07|\x1b\\)/g, START = "\x1b]7501;";
export function readOsc7501(carry: string, data: string): { carry: string; turns: CliTurn[] } {
  const text = carry + data, turns: CliTurn[] = [];
  let end = 0;
  for (const match of text.matchAll(OSC7501)) {
    end = match.index! + match[0].length;
    const fields = new Map(match[1].split(":").filter(field => field.includes("="))
      .map(field => [field.slice(0, field.indexOf("=")), field.slice(field.indexOf("=") + 1)]));
    if (fields.get("state")) turns.push({ state: fields.get("state")!, kind: fields.get("kind") ?? null,
      msg: fields.has("msg") ? Buffer.from(fields.get("msg")!, "base64").toString("utf8") : null });
  }
  // Keep an unfinished report for the next chunk, or an output that stops inside a report's opening `ESC ] 7501 ;`.
  // A report is short, so anything longer is not one.
  const report = text.lastIndexOf(START), escape = text.lastIndexOf("\x1b");
  const from = report >= end ? report : escape >= end && START.startsWith(text.slice(escape)) ? escape : -1;
  return { carry: from >= 0 && text.length - from < 4096 ? text.slice(from) : "", turns };
}

// The sidebar's reading of the last report. A permission prompt, a sign-in or anything not listed is not guessed.
export function osc7501State(turn: CliTurn | null | undefined): "running" | "idle" | "waiting_user_answer" | "unknown" {
  if (!turn) return "unknown";
  if (turn.state === "working") return "running";
  if (["idle", "done", "clear"].includes(turn.state)) return "idle";
  return turn.state === "blocked" && turn.kind === "question" ? "waiting_user_answer" : "unknown";
}
