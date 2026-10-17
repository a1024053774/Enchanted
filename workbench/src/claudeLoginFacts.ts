import { readFileSync, readdirSync, lstatSync } from "node:fs";
import { join } from "node:path";

const percent = (text: string) => text.replace(/%[0-9a-f]{2}/gi, value => value.toUpperCase());
export function credentialVariants(secrets: readonly string[]) {
  return [...new Set(secrets.filter(Boolean).flatMap(value => {
    const base = Buffer.from(value).toString("base64"), url = Buffer.from(value).toString("base64url");
    const json = JSON.stringify(value).slice(1, -1);
    return [value, json, json.replace(/[\u007f-\uffff]/g, c => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0")),
      encodeURIComponent(value).replace(/[!'()*]/g, c => "%" + c.charCodeAt(0).toString(16).toUpperCase()), base, base.replace(/=+$/, ""), url];
  }))].sort((a, b) => b.length - a.length);
}
export function credentialHits(text: string, secrets: readonly string[]) {
  const normalized = percent(text);
  return [...new Set(credentialVariants(secrets).map(percent))].reduce((count, value) => count + normalized.split(value).length - 1, 0);
}
function pattern(value: string) {
  const escaped = value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(escaped.replace(/%[0-9a-f]{2}/gi, value => [...value].map(c => /[a-f]/i.test(c) ? `[${c.toLowerCase()}${c.toUpperCase()}]` : c).join("")), "g");
}
export function redactCredentials(text: string, secrets: readonly string[]) {
  for (const value of credentialVariants(secrets)) text = text.replace(pattern(value), "<CREDENTIAL>");
  return text;
}

// Map visible characters back to the original stream, preserving terminal
// protocol outside a redacted credential. Incomplete escapes stay private.
export function terminalText(raw: string) {
  const escape = /\x1b(?:\[[0-?]*[ -/]*[@-~]|\][\s\S]*?(?:\x07|\x1b\\)|[PX^_][\s\S]*?\x1b\\|(?![\[\]PX^_])[ -/]*[0-~])/y;
  let text = "", end = raw.length;
  const positions: number[] = [];
  for (let i = 0; i < raw.length;) {
    if (raw[i] === "\x1b") {
      escape.lastIndex = i;
      const match = escape.exec(raw);
      if (!match) { end = i; break; }
      i += match[0].length; continue;
    }
    const code = raw.charCodeAt(i);
    if ((code >= 32 && code !== 127 && !(code >= 128 && code <= 159)) || code === 10 || code === 9) {
      positions.push(i); text += raw[i];
    }
    i++;
  }
  return { text, positions, end };
}
export function safeTerminal(raw: string, secrets: readonly string[]) {
  const { text, positions, end } = terminalText(raw), normalized = percent(text);
  let cut = text.length;
  const matches: { start: number; end: number }[] = [];
  for (const value of credentialVariants(secrets)) {
    for (const match of text.matchAll(pattern(value))) matches.push({ start: match.index!, end: match.index! + match[0].length });
    const candidate = percent(value);
    for (let n = Math.min(candidate.length - 1, normalized.length); n > text.length - cut; n--) {
      if (normalized.endsWith(candidate.slice(0, n))) { cut = text.length - n; break; }
    }
  }
  // Never publish the prefix of a complete match when another credential can
  // extend the same suffix across the next chunk.
  for (;;) {
    const crossing = matches.find(m => m.start < cut && m.end > cut);
    if (!crossing) break;
    cut = crossing.start;
  }
  const rawEnd = cut < text.length ? positions[cut]! : end;
  const ranges = matches.filter(m => m.end <= cut).sort((a, b) => a.start - b.start || b.end - a.end);
  const merged: { start: number; end: number }[] = [];
  for (const range of ranges) {
    const last = merged.at(-1);
    if (last && range.start <= last.end) last.end = Math.max(last.end, range.end);
    else merged.push({ ...range });
  }
  let safe = "", offset = 0;
  for (const range of merged) {
    const start = positions[range.start]!, finish = positions[range.end - 1]! + 1;
    safe += raw.slice(offset, start) + "<CREDENTIAL>"; offset = finish;
  }
  return safe + raw.slice(offset, rawEnd);
}
export function preflightObserved(raw: string) {
  const text = terminalText(raw).text.replace(/\s+/g, " ");
  return /Unable to connect to Anthropic services|Checking connectivity\.\.\.|(?:Failed|Unable) to connect to (?:https?:\/\/)?(?:api\.anthropic\.com|platform\.claude\.com)(?=[:/\s.]|$)/i.test(text);
}
export function homeReferences(value: unknown, home: string, field = "launch"): { field: string; occurrences: number }[] {
  if (typeof value === "string") return value.includes(home) ? [{ field, occurrences: value.split(home).length - 1 }] : [];
  if (Array.isArray(value)) return value.flatMap((child, index) => homeReferences(child, home, `${field}[${index}]`));
  if (value && typeof value === "object") return Object.entries(value).flatMap(([key, child]) => homeReferences(child, home, field + "." + key));
  return [];
}
export function scanCredentialFiles(directory: string, secrets: readonly string[]) {
  let hits = 0, files = 0;
  const walk = (path: string) => {
    for (const name of readdirSync(path)) {
      const file = join(path, name), info = lstatSync(file);
      if (info.isSymbolicLink()) continue;
      if (info.isDirectory()) walk(file);
      else if (info.isFile()) { files++; hits += credentialHits(readFileSync(file).toString("utf8"), secrets); }
    }
  };
  walk(directory);
  return { hits, files };
}
export function countForwarderRecords(file: string, received: number) {
  const rows = readFileSync(file, "utf8").split("\n").filter(Boolean).map(line => JSON.parse(line));
  const requests = rows.filter(row => row.kind === "request");
  const ids = requests.map(row => row.sequence);
  const sequences = ids.every((id, index) => id === index + 1);
  return { received_requests: received, ledger_requests: requests.length,
    model_requests: requests.filter(row => row.method === "POST" && row.path === "/v1/messages").length,
    counts_match: received === requests.length && sequences,
    outcomes: rows.filter(row => row.kind === "outcome").length };
}
