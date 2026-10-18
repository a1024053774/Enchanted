import { existsSync, readFileSync, readdirSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import { Refusal } from "./gates/core.ts";

function requireValue(value: unknown, code: string): asserts value {
  if (!value) throw new Refusal(code);
}

// All configuration tokens retain their original value and order. Only the
// vendor's session selector differs from a first launch; no prompt is supplied.
export function resumeArgv(record: Record<string, any>, native: string | null): string[] {
  requireValue(Array.isArray(record.argv) && record.argv.length > 1 &&
    record.argv.every((arg: unknown) => typeof arg === "string" && !arg.includes("\0")) &&
    isAbsolute(record.argv[0]), "restore_argv_missing");
  requireValue(typeof native === "string" && /^[a-zA-Z0-9-]+$/.test(native), "restore_session_missing");
  const argv = [...record.argv];
  if (record.cli === "Claude Code") {
    const selector = argv.indexOf("--session-id");
    requireValue(selector > 0 && argv[selector + 1] === native &&
      argv.lastIndexOf("--session-id") === selector && !argv.includes("--resume"), "restore_session_selector_invalid");
    argv[selector] = "--resume";
  } else {
    requireValue(record.role === "worker" || record.role === "reviewer", "restore_cli_unsupported");
    requireValue(!argv.includes("resume"), "restore_session_selector_invalid");
    argv.push("resume", native);
  }
  return argv;
}

export function nativeSessionFile(record: Record<string, any>, native: string) {
  const claude = record.cli === "Claude Code";
  const home = claude ? record.env?.CLAUDE_CONFIG_DIR : record.env?.CODEX_HOME;
  requireValue(typeof home === "string" && isAbsolute(home), "restore_home_missing");
  const walk = (directory: string): string[] => !existsSync(directory) ? [] :
    readdirSync(directory, { withFileTypes: true }).flatMap(entry => entry.isDirectory() ? walk(join(directory, entry.name)) :
      entry.isFile() && (claude ? entry.name === native + ".jsonl" : entry.name.endsWith(native + ".jsonl")) ? [join(directory, entry.name)] : []);
  const files = walk(join(home, claude ? "projects" : "sessions")).filter(file => {
    const lines = readFileSync(file, "utf8").split("\n").filter(Boolean);
    return lines.some(line => {
      const value = JSON.parse(line);
      return claude ? value.sessionId === native && value.cwd === record.worktree :
        value.type === "session_meta" && value.payload?.source === "cli" &&
        value.payload.id === native && value.payload.cwd === record.worktree;
    });
  });
  requireValue(files.length === 1, "restore_session_missing");
  return files[0]!;
}
