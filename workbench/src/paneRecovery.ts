import { existsSync, readFileSync, readdirSync } from "node:fs";
import { basename, isAbsolute, join } from "node:path";
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
    // A Codex monitor (T-124) binds its session the same way; the argv is recorded when the session is bound.
    requireValue(["worker", "reviewer", "monitor"].includes(record.role), "restore_cli_unsupported");
    requireValue(!argv.includes("resume"), "restore_session_selector_invalid");
    argv.push("resume", native);
  }
  return argv;
}

export function codexSessionFileName(file: unknown, native: unknown): boolean {
  return typeof file === "string" && typeof native === "string" && Boolean(native) &&
    basename(file).endsWith(native + ".jsonl");
}

// Codex rollout names can prefix the session ID. A filename mismatch or
// incomplete metadata does not establish that a record belongs to a helper.
export function codexSessionOrigin(file: unknown, metadata: any, native: unknown, worktree: unknown): "root" | "auxiliary" | "unknown" {
  const payload = metadata?.payload;
  if (typeof file !== "string" || metadata?.type !== "session_meta" ||
      typeof native !== "string" || !native || typeof worktree !== "string" ||
      payload?.cwd !== worktree || typeof payload.id !== "string" || !payload.id ||
      !codexSessionFileName(file, payload.id)) return "unknown";
  if (payload.id === native && payload.source === "cli") return "root";
  if (payload.id !== native && payload.source?.subagent?.parent_thread_id === native) return "auxiliary";
  return "unknown";
}

export function nativeSessionFile(record: Record<string, any>, native: string) {
  const claude = record.cli === "Claude Code";
  // A managed Claude session (worker, reviewer, monitor) runs without CLAUDE_CONFIG_DIR: Claude then uses $HOME/.claude.
  const home = claude ? record.env?.CLAUDE_CONFIG_DIR ?? (typeof record.env?.HOME === "string" ? join(record.env.HOME, ".claude") : undefined) :
    record.env?.CODEX_HOME;
  requireValue(typeof home === "string" && isAbsolute(home), "restore_home_missing");
  const walk = (directory: string): string[] => !existsSync(directory) ? [] :
    readdirSync(directory, { withFileTypes: true }).flatMap(entry => entry.isDirectory() ? walk(join(directory, entry.name)) :
      entry.isFile() && (claude ? entry.name === native + ".jsonl" : codexSessionFileName(entry.name, native)) ? [join(directory, entry.name)] : []);
  const files = walk(join(home, claude ? "projects" : "sessions")).filter(file => {
    const lines = readFileSync(file, "utf8").split("\n").filter(Boolean);
    return lines.some(line => {
      const value = JSON.parse(line);
      return claude ? value.sessionId === native && value.cwd === record.worktree :
        codexSessionOrigin(file, value, native, record.worktree) === "root";
    });
  });
  requireValue(files.length === 1, "restore_session_missing");
  return files[0]!;
}
