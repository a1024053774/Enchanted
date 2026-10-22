import { accessSync, constants, readFileSync, realpathSync, statSync } from "node:fs";
import { isAbsolute, join } from "node:path";

export interface TaskCard {
  id: string;
  source: { ticket: string; ready_rev: number } | null;
  goal: string;
  non_goals: string[];
  paths: { allow: string[]; deny: string[] };
  oracle_paths: string[];
  completion_conditions: { argv: string[] }[];
  red_commands: { argv: string[]; test_paths: string[] }[];
  task_type: string;
  repair_target: string | null;
  complexity: "S" | "M" | "L";
  executor: { cli: "Claude Code" | "Codex"; model: string; effort: string };
  base_commit: string | null;
  writer: { task_id: string; attempt_id: string; session_id: string; fence: number; thread_id: string } | null;
}

export class TaskCardError extends Error {
  readonly field: string;
  constructor(field: string, message: string) {
    super(message);
    this.field = field;
  }
}
function check(value: unknown, field: string, message: string): asserts value {
  if (!value) throw new TaskCardError(field, message);
}
function object(value: any, fields: string[], field: string) {
  // Reasons name the expected fields: a controller only sees the refusal (T-122 gui-02 guessed shapes six times).
  check(value && typeof value === "object" && !Array.isArray(value), field, `Object with fields ${fields.join(", ")} required.`);
  check(Object.keys(value).length === fields.length && fields.every((key) => Object.hasOwn(value, key)),
    field, `Fields must be exactly: ${fields.join(", ")}.`);
}
function nonempty(value: unknown, field: string): asserts value is string {
  check(typeof value === "string" && value.trim() && !value.includes("\0"), field, "Nonempty text required.");
}
function strings(value: unknown, field: string, minimum = 0): asserts value is string[] {
  check(Array.isArray(value) && value.length >= minimum, field, "Array has too few entries.");
  value.forEach((item, i) => nonempty(item, `${field}[${i}]`));
}

export function commandArgv(value: unknown, field: string): string[] {
  check(Array.isArray(value) && value.length > 0 &&
    value.every((arg) => typeof arg === "string" && !arg.includes("\0")), field, 'Command argv required: a nonempty string array such as ["python3", "check.py"].');
  const argv = [...value] as string[];
  nonempty(argv[0], field);
  check(argv.every((arg) => !arg.includes("{worktree}") || arg === "{worktree}"), field,
    "The worktree token must occupy one complete argument.");
  const executable = argv[0];
  const paths = isAbsolute(executable) ? [executable] : executable.includes("/") ? [] :
    (process.env.PATH ?? "").split(":").filter(isAbsolute).map((dir) => join(dir, executable));
  let resolved: string | undefined;
  for (const path of paths) {
    try {
      accessSync(path, constants.X_OK);
      if (statSync(path).isFile()) { resolved = realpathSync(path); break; }
    } catch (error) {
      if (!["ENOENT", "EACCES", "ENOTDIR"].includes((error as NodeJS.ErrnoException).code ?? "")) throw error;
    }
  }
  check(resolved, field, "Executable is unavailable.");
  argv[0] = resolved;
  return argv;
}

export interface ProjectQuality {
  source_commit: string;
  path: ".a2a/quality.json";
  raw: string | null;
  rule_checks: { id: string; argv: string[] }[];
}

export function projectRules(value: unknown): ProjectQuality["rule_checks"] {
  object(value, ["schema", "rule_checks"], "project_quality");
  const config = value as { schema: unknown; rule_checks: unknown[] };
  check(config.schema === 1 && Array.isArray(config.rule_checks), "project_quality", "Schema 1 and rule_checks array required.");
  const ids = new Set<string>();
  return config.rule_checks.map((input: any, index) => {
    const field = `project_quality.rule_checks[${index}]`;
    object(input, ["id", "argv"], field);
    nonempty(input.id, field + ".id");
    check(!ids.has(input.id), field, "Rule IDs must be unique."); ids.add(input.id);
    return { id: input.id, argv: commandArgv(input.argv, field + ".argv") };
  });
}

export function ticketSource(path: string) {
  check(isAbsolute(path), "source.ticket", "Absolute ticket path required.");
  const content = readFileSync(path, "utf8");
  const lines = content.split(/\r?\n/);
  check(lines[0] === "---", "source.ticket", "Ticket frontmatter required.");
  const end = lines.indexOf("---", 1);
  check(end > 0, "source.ticket", "Ticket frontmatter is incomplete.");
  const fields = new Map<string, string>();
  for (const line of lines.slice(1, end)) {
    const separator = line.indexOf(":");
    if (separator < 1) continue;
    const key = line.slice(0, separator);
    check(!fields.has(key), "source.ticket", "Duplicate ticket field.");
    fields.set(key, line.slice(separator + 1).trim());
  }
  const ticketId = fields.get("id"), rev = Number(fields.get("ready_rev"));
  check(ticketId && fields.get("ready") === "yes" && Number.isSafeInteger(rev) && rev > 0,
    "source", "A ready ticket and a positive ready_rev are required.");
  return { ticketId, source: { ticket: realpathSync(path), ready_rev: rev } };
}

export function taskCardTemplate(id: string, ticket?: string): TaskCard {
  const source = ticket ? ticketSource(ticket) : null;
  if (source) check(id.startsWith(source.ticketId + "-") && /^[1-9][0-9]*$/.test(id.slice(source.ticketId.length + 1)),
    "id", "Card ID must contain the ticket ID and a sequence number.");
  return { id, source: source?.source ?? null, goal: "", non_goals: [], paths: { allow: [], deny: [] },
    oracle_paths: [], completion_conditions: [], red_commands: [], task_type: "后端逻辑", repair_target: null,
    complexity: "M", executor: { cli: "Codex", model: "", effort: "" }, base_commit: null, writer: null };
}

export function validateTaskCard(input: unknown, id: string): TaskCard {
  const card = structuredClone(input) as TaskCard;
  object(card, ["id", "source", "goal", "non_goals", "paths", "oracle_paths", "completion_conditions", "red_commands",
    "task_type", "repair_target", "complexity", "executor", "base_commit", "writer"], "card");
  check(card.id === id, "id", "Card ID does not match the task.");
  if (card.source !== null) {
    // T-122 gui-03: naming only the object fields sent a controller off to invent a ticket.
    check(card.source && typeof card.source === "object" && !Array.isArray(card.source), "source",
      "null when the task has no project-map ticket; otherwise an object with fields ticket, ready_rev.");
    object(card.source, ["ticket", "ready_rev"], "source");
    nonempty(card.source.ticket, "source.ticket");
    const source = ticketSource(card.source.ticket);
    check(card.source.ready_rev === source.source.ready_rev, "source.ready_rev", "Ticket revision does not match.");
    check(id.startsWith(source.ticketId + "-") && /^[1-9][0-9]*$/.test(id.slice(source.ticketId.length + 1)),
      "id", "Card ID must contain the ticket ID and a sequence number.");
    card.source = source.source;
  }
  nonempty(card.goal, "goal");
  strings(card.non_goals, "non_goals", 1);
  object(card.paths, ["allow", "deny"], "paths");
  for (const kind of ["allow", "deny"] as const) {
    strings(card.paths[kind], "paths." + kind, kind === "allow" ? 1 : 0);
    for (const path of card.paths[kind]) {
      const parts = path.replace(/\/$/, "").split("/");
      check(path === "." || (!isAbsolute(path) && !path.includes("\\") && !/[\x00-\x1f*?\[\]:]/.test(path) &&
        parts.every((part) => part && part !== "." && part !== "..")), "paths." + kind, "Invalid repository path.");
    }
  }
  strings(card.oracle_paths, "oracle_paths", 1);
  for (const path of card.oracle_paths) {
    const parts = path.replace(/\/$/, "").split("/");
    check(!isAbsolute(path) && !path.includes("\\") && !/[\x00-\x1f*?\[\]:]/.test(path) &&
      parts.every((part) => part && part !== "." && part !== ".." && part.toLowerCase() !== ".git"),
      "oracle_paths", "Exact repository file paths or directory prefixes are required.");
  }
  for (const key of ["completion_conditions", "red_commands"] as const) {
    check(Array.isArray(card[key]) && (key === "red_commands" || card[key].length > 0), key, key === "red_commands"
      ? 'Array of {"argv": [...], "test_paths": [...]} required.' : 'Nonempty array of {"argv": ["program", "arg", ...]} required.');
    for (const [i, command] of card[key].entries()) {
      const field = `${key}[${i}]`;
      object(command, key === "red_commands" ? ["argv", "test_paths"] : ["argv"], field);
      command.argv = commandArgv(command.argv, field);
      if (key === "red_commands") {
        const paths = (command as TaskCard["red_commands"][number]).test_paths;
        strings(paths, field + ".test_paths", 1);
        check(new Set(paths).size === paths.length, field, "Test paths must be unique.");
        for (const path of paths) {
          const parts = path.split("/");
          check(!isAbsolute(path) && !path.includes("\\") && !/[\x00-\x1f*?\[\]:]/.test(path) &&
            parts.every((part) => part && part !== "." && part !== ".." && part.toLowerCase() !== ".git"),
            field + ".test_paths", "Exact repository file paths are required.");
          check(!card.oracle_paths.some((rule) => rule.endsWith("/") ? path.startsWith(rule) : path === rule),
            field + ".test_paths", "Red test paths must not intersect acceptance files.");
        }
      }
    }
  }
  check(["后端逻辑", "前端界面", "缺陷修复", "测试", "重构", "构建与基础设施", "文档", "调研"].includes(card.task_type),
    "task_type", "Unknown task type.");
  if (card.task_type === "缺陷修复") nonempty(card.repair_target, "repair_target");
  else check(card.repair_target === null || typeof card.repair_target === "string", "repair_target", "Text or null required.");
  check(["S", "M", "L"].includes(card.complexity), "complexity", "Complexity must be S, M or L.");
  object(card.executor, ["cli", "model", "effort"], "executor");
  check(["Claude Code", "Codex"].includes(card.executor.cli), "executor.cli", "CLI must be Claude Code or Codex.");
  nonempty(card.executor.model, "executor.model");
  nonempty(card.executor.effort, "executor.effort");
  check(card.base_commit === null && card.writer === null, "writer", "The gate fills the base commit and writer during claim.");
  return card;
}

export function pathAllowed(card: TaskCard, path: string): boolean {
  const matches = (rule: string) => rule === "." || (rule.endsWith("/") ? path.startsWith(rule) : path === rule);
  return card.paths.allow.some(matches) && !card.paths.deny.some(matches);
}

/** Intersect the declared path sets, including paths that do not exist yet. */
export function pathIntersection(left: TaskCard["paths"], right: TaskCard["paths"]): string[] {
  const contains = (outer: string, inner: string) => outer === "." || outer === inner ||
    (outer.endsWith("/") && inner.startsWith(outer));
  const intersections = new Set<string>();
  for (const a of left.allow) for (const b of right.allow) {
    const intersection = contains(a, b) ? b : contains(b, a) ? a : null;
    if (intersection !== null && ![...left.deny, ...right.deny].some((deny) => contains(deny, intersection)))
      intersections.add(intersection);
  }
  return [...intersections].sort();
}
