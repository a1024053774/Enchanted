// T-242 (review-3 re-review), T-246: every order of a short run of hook and foreground events against ByProcess, checked
// against the invariants written independently of the module:
//   I1 what is shown is the state the process in front last reported itself, or nothing before it has reported;
//   I2 a report from any other process, early or late, never changes I1's answer; a process is its pid and start
//      time, so one given an exited process's pid (T-246 review) starts with nothing;
//   I3 only processes still running (or the one in front) keep a report, so exited ones do not pile up.
// Failures it is written to catch: a late hook of an exited CLI shows on the one in front (I2), or erases what the one in
// front reported so it stays unknown (I2, the re-review's case); a process given a reused pid shows the earlier one's
// report (I2); the front process's own report not shown, or one carried over before it reports (I1); reports of exited
// processes kept (I3).
// Not modelled: a hook of an exited process that arrives after its pid was given to a new one (the hook carries no
// start time to tell them apart).
// Usage: node test_by_process.ts [module path, default ../src/byProcess.ts] [max length, default 6]
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";

const modulePath = resolve(process.argv[2] ?? new URL("../src/byProcess.ts", import.meta.url).pathname);
const maxLength = Number(process.argv[3] ?? 6);
const { ByProcess } = await import(pathToFileURL(modulePath).href);

const ZSH = 100, A = 101, B = 102;
type Event = { kind: "note"; pid: number; state: "running" | "idle" } | { kind: "front"; pid: number | null }
  | { kind: "exit"; pid: number } | { kind: "reuse"; pid: number };
const events: Event[] = [
  ...[A, B].flatMap((pid) => (["running", "idle"] as const).map((state) => ({ kind: "note" as const, pid, state }))),
  ...[A, B, ZSH, null].map((pid) => ({ kind: "front" as const, pid })),
  ...[A, B].flatMap((pid) => [{ kind: "exit" as const, pid }, { kind: "reuse" as const, pid }]),
];
const label = (e: Event) => e.kind === "note" ? `note(${e.pid},${e.state})` : `${e.kind}(${e.pid})`;

let sequences = 0;
// A sequence is replayable when a pid is reused only after its process exited, and an exited process's late hook
// arrives only before its pid is reused.
function valid(sequence: Event[]) {
  const dead = new Set<number>(), reused = new Set<number>();
  for (const e of sequence) {
    if (e.kind === "reuse") { if (!dead.has(e.pid)) return false; dead.delete(e.pid); reused.add(e.pid); }
    else if (e.kind === "exit") { if (dead.has(e.pid)) return false; dead.add(e.pid); }
  }
  return true;
}
function run(sequence: Event[]) {
  const dead = new Set<number>();
  const started = new Map<number, number>([[ZSH, 0], [A, 0], [B, 0]]);
  const turns = new ByProcess((pid: number) => !dead.has(pid));
  // Each process (pid@start): its last report; the process the last front read named.
  const last = new Map<string, string>(), current = (pid: number) => `${pid}@${started.get(pid)}`;
  let front: string | null = null, clock = 0;
  const exitedSinceCall = new Set<number>();
  for (const e of sequence) {
    clock++;
    if (e.kind === "note") { turns.note(e.pid, e.state, clock); last.set(current(e.pid), e.state); exitedSinceCall.clear(); }
    else if (e.kind === "front") {
      turns.foreground(e.pid === null ? null : { pid: e.pid, started: started.get(e.pid)! });
      front = e.pid === null ? null : current(e.pid); exitedSinceCall.clear();
    } else if (e.kind === "exit") { dead.add(e.pid); exitedSinceCall.add(e.pid); }
    else { dead.delete(e.pid); started.set(e.pid, clock); exitedSinceCall.delete(e.pid); }
  }
  const shown = turns.shown();
  const expected = front === null ? null : last.get(front) ?? null;
  const where = sequence.map(label).join(" ");
  // The process the last front read named may have exited or given its pid to later processes since (nothing reads
  // the front in between): nothing, or the last state of it or of one of those later holders of its pid, which may be
  // in front now (the next front read settles it); never a report under another pid.
  const frontPid = front === null ? null : Number(front.split("@")[0]);
  if (frontPid !== null && (dead.has(frontPid) || current(frontPid) !== front)) {
    const since = Number(front!.split("@")[1]);
    const holders = [...last].filter(([key]) => key.startsWith(`${frontPid}@`) && Number(key.split("@")[1]) >= since).map(([, state]) => state);
    assert(shown === null || holders.includes(shown), `I1 ${where}: ${shown}`);
  }
  else assert.equal(shown, expected, `I1/I2 ${where}`);
  // I3: a pid may keep a report while its process runs, while it is in front, or until the next call after it exited
  // (an exit itself calls nothing); a reused pid's earlier report may stay until that pid is seen in front.
  const allowed = [A, B].filter((pid) => sequence.some((e) => e.kind === "note" && e.pid === pid) &&
    (!dead.has(pid) || pid === frontPid || exitedSinceCall.has(pid))).length;
  assert(turns.size <= allowed, `I3 ${where}: ${turns.size} > ${allowed}`);
  sequences++;
}
function search(prefix: Event[]) {
  run(prefix);
  if (prefix.length < maxLength) for (const e of events) { const next = [...prefix, e]; if (valid(next)) search(next); }
}
search([]);
console.log(JSON.stringify({ status: "PASS", module: modulePath, max_length: maxLength, sequences }));
