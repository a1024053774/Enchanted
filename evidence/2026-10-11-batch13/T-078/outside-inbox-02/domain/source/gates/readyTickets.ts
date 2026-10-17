import { readdirSync, readFileSync, realpathSync } from "node:fs";
import { join, relative, isAbsolute } from "node:path";

export type ReadyTicket = { id: string; title: string; type: string; ready_by: string; ready_rev: number };
export function readyTickets(repo: string): { ready: ReadyTicket[]; diagnostics: string[] } {
  const root = realpathSync(repo);
  const directory = realpathSync(join(root, ".project-map", "tickets"));
  const inside = (path: string) => {
    const value = relative(root, path);
    if (isAbsolute(value) || value === ".." || value.startsWith("../")) throw new Error("ticket_path_outside_project");
  };
  inside(directory);
  const tickets = new Map<string, Record<string, any>>();
  const diagnostics: string[] = [];
  for (const name of readdirSync(directory).filter(name => name.endsWith(".md")).sort()) {
    try {
      const path = realpathSync(join(directory, name)); inside(path);
      const lines = new TextDecoder("utf-8", { fatal: true }).decode(readFileSync(path)).split(/\r?\n/);
      if (lines[0]?.trim() !== "---") throw new Error("front_matter_required");
      const fields: Record<string, any> = {};
      let closed = false;
      for (const line of lines.slice(1)) {
        if (line.trim() === "---") { closed = true; break; }
        if (!line.trim()) continue;
        const colon = line.indexOf(":");
        const key = line.slice(0, colon).trim(), raw = line.slice(colon + 1).trim();
        if (colon < 1 || !key || Object.hasOwn(fields, key)) throw new Error("invalid_front_matter_field");
        // This is the project's flat scalar/inline-list format, not YAML.
        if (raw.startsWith('"')) fields[key] = JSON.parse(raw);
        else if (raw.startsWith("[")) {
          if (raw.includes('"')) fields[key] = JSON.parse(raw);
          else {
            if (!raw.endsWith("]") || raw.slice(1, -1).includes("[") || raw.slice(1, -1).includes("]")) throw new Error("invalid_inline_list");
            fields[key] = raw.slice(1, -1).split(",").map(value => value.trim()).filter(Boolean);
          }
        } else fields[key] = raw;
      }
      if (!closed || typeof fields.id !== "string" || !fields.id || tickets.has(fields.id)) throw new Error("invalid_ticket_id_or_header");
      tickets.set(fields.id, fields);
    } catch (error) { diagnostics.push(`${name}: ${String(error)}`); }
  }
  const ready: ReadyTicket[] = [];
  for (const [id, item] of tickets) {
    if (item.status !== "open" || !["ready", "ready_by", "ready_rev"].some(key => Object.hasOwn(item, key))) continue;
    if (["ready", "ready_by", "ready_rev"].some(key => !item[key])) { diagnostics.push(`${id}: missing_ready_fields`); continue; }
    if (item.ready === "no") continue;
    if (item.ready !== "yes" || !["ideation", "executor"].includes(item.ready_by) ||
        !/^[0-9]+$/.test(String(item.ready_rev)) || !Number.isSafeInteger(Number(item.ready_rev)) || Number(item.ready_rev) < 1 ||
        !Array.isArray(item.blocked_by) || !item.blocked_by.every((value: unknown) => typeof value === "string")) {
      diagnostics.push(`${id}: invalid_ready_fields`); continue;
    }
    if (!["build", "task", "research"].includes(item.type) || item.claimed_by) continue;
    if (!item.blocked_by.every((dependency: string) => ["closed", "superseded"].includes(tickets.get(dependency)?.status))) continue;
    ready.push({ id, title: item.title ?? "", type: item.type, ready_by: item.ready_by, ready_rev: Number(item.ready_rev) });
  }
  return { ready, diagnostics };
}
