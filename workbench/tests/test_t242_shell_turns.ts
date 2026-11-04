// T-242 (review-3 re-review): every order of a short run of hook and foreground events against ShellTurns, checked
// against the invariants written independently of the module:
//   I1 what is shown is the state the process in front last reported itself, or nothing before it has reported;
//   I2 a hook from any other process, early or late, never changes I1's answer;
//   I3 only processes still running (or the one in front) keep a state, so exited ones do not pile up.
// Failures it is written to catch: a late hook of an exited CLI shows on the one in front (I2), or erases what the one in
// front reported so it stays unknown (I2, the re-review's case); the front process's own report not shown, or one
// carried over before it reports (I1); states of exited processes kept (I3).
// Not modelled: a new process given an exited one's pid before a foreground read sees another process (no start time
// is known to tell them apart).
// Usage: node test_t242_shell_turns.ts [module path, default ../src/shellTurns.ts] [max length, default 6]
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";

const modulePath = resolve(process.argv[2] ?? new URL("../src/shellTurns.ts", import.meta.url).pathname);
const maxLength = Number(process.argv[3] ?? 6);
const { ShellTurns } = await import(pathToFileURL(modulePath).href);

const ZSH = 100, A = 101, B = 102;
type Event = { kind: "note"; pid: number; state: "running" | "idle" } | { kind: "front"; pid: number | null } | { kind: "exit"; pid: number };
const events: Event[] = [
  ...[A, B].flatMap((pid) => (["running", "idle"] as const).map((state) => ({ kind: "note" as const, pid, state }))),
  ...[A, B, ZSH, null].map((pid) => ({ kind: "front" as const, pid })),
  ...[A, B].map((pid) => ({ kind: "exit" as const, pid })),
];
const label = (e: Event) => e.kind === "note" ? `note(${e.pid},${e.state})` : `${e.kind}(${e.pid})`;

let sequences = 0;
function run(sequence: Event[]) {
  const dead = new Set<number>();
  const turns = new ShellTurns((pid: number) => !dead.has(pid));
  const last = new Map<number, string>();
  let front: number | null = null;
  const exitedSinceCall = new Set<number>();
  for (const e of sequence) {
    if (e.kind === "note") { turns.note({ cli: "claude", pid: e.pid, state: e.state }); last.set(e.pid, e.state); exitedSinceCall.clear(); }
    else if (e.kind === "front") { turns.foreground(e.pid); front = e.pid; exitedSinceCall.clear(); }
    else { dead.add(e.pid); exitedSinceCall.add(e.pid); }
  }
  const shown = turns.shown()?.state ?? null;
  const expected = front === null ? null : last.get(front) ?? null;
  const where = sequence.map(label).join(" ");
  // A front read can name a process that exited since (the read is not atomic with the exit): nothing or its last state.
  if (front !== null && dead.has(front)) assert(shown === null || shown === expected, `I1 ${where}: ${shown}`);
  else assert.equal(shown, expected, `I1/I2 ${where}`);
  // I3: a noted pid may keep a state while it runs, while it is in front, or until the next call after it exited
  // (an exit itself calls nothing).
  const allowed = [A, B].filter((pid) => last.has(pid) && (!dead.has(pid) || pid === front || exitedSinceCall.has(pid))).length;
  assert(turns.size <= allowed, `I3 ${where}: ${turns.size} > ${allowed}`);
  sequences++;
}
function search(prefix: Event[]) {
  run(prefix);
  if (prefix.length < maxLength) for (const e of events) search([...prefix, e]);
}
search([]);
console.log(JSON.stringify({ status: "PASS", module: modulePath, max_length: maxLength, sequences }));
