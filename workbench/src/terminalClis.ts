// T-184, T-187: the CLIs Enchanted's project-terminal shims wrap (terminal/bin), in one place. New CLIs join here.
// - wired: whether a running one came through its shim. The fact is the process's own launch: the shim always adds its
//   launch arguments or, where a CLI has no harmless argument to add, names itself as A2A_SHIM in the environment. A CLI
//   started by its real path or another alias lacks them: no orientation, no turn states, no role records.
// - turns: where its turn states come from. "hooks": Enchanted's hooks report each turn (claude, codex). "osc7501": the
//   CLI reports its own state to the terminal as OSC 7501 (T-187 facts: agy needs AGY_CLI_OSC7501=on, opencode always).
// - inCommand: whether a command (`a2a request`) may run inside it, from the environment the CLI gives its commands. A
//   CLI started inside another inherits the outer one's variable too; then the nearest one among the command's
//   ancestor processes is the one that runs it (commandCli).
export type LaunchFacts = { argv: string[]; shim: string | null };
export type TerminalCli = { wired: (launch: LaunchFacts) => boolean; turns: "hooks" | "osc7501";
  inCommand: (env: NodeJS.ProcessEnv) => boolean };

export const terminalClis: Record<string, TerminalCli> = {
  claude: { turns: "hooks", inCommand: env => Boolean(env.CLAUDECODE),
    wired: ({ argv }) => argv.some((arg, index) => arg === "--plugin-dir" && (argv[index + 1] ?? "").endsWith("/plugin/enchanted-a2a")) },
  // The hook commands name the a2a shim through the terminal's environment, unexpanded in the argument itself.
  codex: { turns: "hooks", inCommand: env => Boolean(env.CODEX_THREAD_ID), wired: ({ argv }) => argv.some(arg => arg.includes('$A2A_TERMINAL_BIN/a2a')) },
  opencode: { turns: "osc7501", inCommand: env => Boolean(env.OPENCODE_SESSION_ID), wired: ({ shim }) => shim === "opencode" },
  agy: { turns: "osc7501", inCommand: env => env.A2A_SHIM === "agy", wired: ({ shim }) => shim === "agy" },
};

// ancestors: the program names of the command's ancestor processes, nearest first; read only when two CLIs claim it.
export function commandCli(env: NodeJS.ProcessEnv, ancestors: () => string[]): string | undefined {
  const claimed = Object.keys(terminalClis).filter(name => terminalClis[name].inCommand(env));
  if (claimed.length < 2) return claimed[0];
  return ancestors().find(name => claimed.includes(name));
}

// One OSC 7501 report: `ESC ] 7501 ; state=<s>[:id=..][:kind=<k>][:app=..][:msg=<base64>] (BEL | ESC \)`. A bare `?` is
// the CLI asking whether the terminal supports it, not a state.
export type CliTurn = { state: string; kind: string | null };
const OSC7501 = /\x1b\]7501;([^\x07\x1b]*)(?:\x07|\x1b\\)/g, START = "\x1b]7501;";
export function readOsc7501(carry: string, data: string): { carry: string; turns: CliTurn[] } {
  const text = carry + data, turns: CliTurn[] = [];
  let end = 0;
  for (const match of text.matchAll(OSC7501)) {
    end = match.index! + match[0].length;
    const fields = new Map(match[1].split(":").filter(field => field.includes("="))
      .map(field => [field.slice(0, field.indexOf("=")), field.slice(field.indexOf("=") + 1)]));
    if (fields.get("state")) turns.push({ state: fields.get("state")!, kind: fields.get("kind") ?? null });
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
