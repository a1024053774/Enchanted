// T-253 gate side in isolation: no CLI, PTY, socket or model. Pane facts come from a test runtime; each task row is
// written as the gate stores it after a dispatch whose pane did not yet show the Codex session (leader bound, native
// session null, as in evidence/2026-11-07-batch33/T-252/green/e2e-codex-dispatch-6159e7697.json).
// Ways it can fail, listed before writing:
// 1. A pane that is not the attempt's (another launch, another shell process) gets its session bound, and reclaim then
//    trusts a foreign agent. Expected: identity_conflict, attempt unchanged, reclaim still refuses identity_conflict.
// 2. A gate command holding the task lock makes the binding fail and it is lost (operation_busy): T-253 again.
//    Expected: nothing is bound while the lock is held, and the session is bound once it is released.
// 3. The binding holds the task lock while it reads the pane, so a run's observeRun (which takes the lock without
//    waiting) fails meanwhile. Expected: the lock is free during every read.
// 4. A replaced attempt gets the session. Expected: stale_attempt, nothing written.
// 5. A second call writes again or overwrites the bound session. Expected: one runtime_bound, values unchanged.
// 6. The plain case: the attempt gets the pane's native session, with one runtime_bound event.
// Expected values come from the ticket (T-253 acceptance) and the gate's identity rule (launch, thread, shell, leader).
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { DatabaseSync } from "node:sqlite";

const [source, summary] = process.argv.slice(2);
if (!source || !summary) throw new Error("usage: t253_native_bind.ts <source root> <summary.json>");
const report: any = { status: "INCOMPLETE", source, fixture: null, checks: [], failed: [], observed: {} };
const check = (name: string, ok: unknown, detail?: unknown) => {
  report.checks.push({ name, ok: Boolean(ok), detail });
  if (!ok) report.failed.push(name);
};
const root = mkdtempSync("/tmp/t253-bind-");
report.fixture = root;
const repo = join(root, "repo");
mkdirSync(repo, { recursive: true });
const pane = { launch: "launch-1", thread: "worker-1", shell_pid: 4100, leader_pid: 4101, native_session: "codex-session-1" };
let identity: any = pane;
let onRead: (() => void) | null = null;
let reads = 0;
const unexpected = async () => { throw new Error("this fixture runs no agent lifecycle"); };
const runtime = {
  ensureProject: unexpected, createThread: unexpected, startThread: unexpected, stopThread: unexpected, archiveThread: unexpected,
  readThread: async (thread: string) => {
    reads++;
    onRead?.();
    await new Promise((resolve) => setTimeout(resolve, 5));
    return { workspace: repo, provider: "codex", turn: "turn-1", running: false, stopped: false, archived: false, blocked: false,
      runtime_identity: { ...identity, thread } };
  },
};
let gates: any;
try {
  const { A2AGates } = await import(pathToFileURL(join(source, "workbench/src/gates/core.ts")).href);
  gates = new A2AGates(root, runtime, () => Date.parse("2026-11-08T12:00:00Z"));
  const db = new DatabaseSync(join(root, "state.sqlite3"));
  const seed = (name: string) => {
    const taskId = "t253-" + name, attemptId = "attempt-" + name;
    const attempt = { task_id: taskId, attempt_id: attemptId, session_id: "session-" + name, fence: 1, spec_rev: 1,
      thread_id: pane.thread, workspace: repo, turn_id: null, reclaimed: false, state: "claimed", card_snapshot_id: "card-" + name,
      runtime_identity: { launch: pane.launch, thread: pane.thread, shell_pid: pane.shell_pid, leader_pid: pane.leader_pid, native_session: null } };
    // A registered task (its card snapshot and integration ref), so reclaim reaches its identity check.
    const task = { task_id: taskId, project_id: "t253", repo, state: "claimed", fence: 1, spec_rev: 1, card_snapshot_id: attempt.card_snapshot_id,
      integration_ref: "refs/heads/main", current_attempt: attempt };
    db.prepare("INSERT INTO tasks(id,data) VALUES (?,?)").run(taskId, JSON.stringify(task));
    db.prepare("INSERT INTO attempts(id,data) VALUES (?,?)").run(attemptId, JSON.stringify(attempt));
    db.prepare("INSERT INTO task_card_snapshots(id,task,version,attempt,data) VALUES (?,?,?,?,?)")
      .run(attempt.card_snapshot_id, taskId, 1, attemptId, JSON.stringify({ executor: { cli: "Codex" } }));
    return { taskId, attemptId };
  };
  const bound = (attemptId: string) => JSON.parse(String(db.prepare("SELECT data FROM attempts WHERE id=?").get(attemptId)!.data)).runtime_identity;
  const boundEvents = (taskId: string) => Number(db.prepare("SELECT count(*) AS n FROM events WHERE task=? AND type='runtime_bound'").get(taskId)!.n);
  const lockFree = (taskId: string) => {
    const lock = new DatabaseSync(join(root, "locks", `${taskId}.sqlite3`));
    try { lock.exec("PRAGMA busy_timeout=0; BEGIN IMMEDIATE"); lock.exec("ROLLBACK"); return true; }
    catch (error) { if (String(error).includes("database is locked")) return false; throw error; }
    finally { lock.close(); }
  };
  const outcome = async (promise: Promise<unknown>) => {
    try { await promise; return "ok"; } catch (error: any) { return error?.code ?? String(error); }
  };

  { // 6, 3, 5: the plain case, the lock during the read, a second call.
    const { taskId, attemptId } = seed("bind");
    identity = pane;
    const free: boolean[] = [];
    onRead = () => free.push(lockFree(taskId));
    const result = await outcome(gates.nativeSessionLearned(taskId, attemptId, pane.thread));
    onRead = null;
    report.observed.bind = { result, bound: bound(attemptId), events: boundEvents(taskId), lock_free_during_reads: free };
    check("binds_pane_session", result === "ok" && bound(attemptId).native_session === pane.native_session &&
      bound(attemptId).leader_pid === pane.leader_pid && boundEvents(taskId) === 1, report.observed.bind);
    check("lock_free_while_reading", free.length > 0 && free.every(Boolean), free);
    const again = await outcome(gates.nativeSessionLearned(taskId, attemptId, pane.thread));
    report.observed.again = { result: again, bound: bound(attemptId), events: boundEvents(taskId) };
    check("second_call_changes_nothing", again === "ok" && bound(attemptId).native_session === pane.native_session &&
      boundEvents(taskId) === 1, report.observed.again);
  }
  for (const [name, changed] of [["other_launch", { launch: "launch-2" }], ["other_shell", { shell_pid: 4999 }]] as const) { // 1
    const { taskId, attemptId } = seed(name);
    identity = { ...pane, ...changed };
    const result = await outcome(gates.nativeSessionLearned(taskId, attemptId, pane.thread));
    const reclaim = await gates.call({ command: "reclaim", task: taskId, attempt: attemptId });
    report.observed[name] = { result, bound: bound(attemptId), events: boundEvents(taskId), reclaim: { ok: reclaim.ok, error: reclaim.error } };
    check(`${name}_refused`, result === "identity_conflict" && bound(attemptId).native_session === null && boundEvents(taskId) === 0 &&
      !reclaim.ok && reclaim.error === "identity_conflict", report.observed[name]);
  }
  { // 4
    const { taskId } = seed("replaced");
    identity = pane;
    const result = await outcome(gates.nativeSessionLearned(taskId, "attempt-earlier", pane.thread));
    report.observed.replaced = { result, bound: bound("attempt-replaced"), events: boundEvents(taskId) };
    check("replaced_attempt_refused", result === "stale_attempt" && bound("attempt-replaced").native_session === null &&
      boundEvents(taskId) === 0, report.observed.replaced);
  }
  { // 2
    const { taskId, attemptId } = seed("busy");
    identity = pane;
    const holder = new DatabaseSync(join(root, "locks", `${taskId}.sqlite3`));
    holder.exec("BEGIN IMMEDIATE");
    const before = reads;
    let settled: string | null = null;
    const pending = outcome(gates.nativeSessionLearned(taskId, attemptId, pane.thread)).then((value) => (settled = value));
    await new Promise((resolve) => setTimeout(resolve, 400));
    const whileHeld = { settled, bound: bound(attemptId), events: boundEvents(taskId), reads: reads - before };
    holder.exec("ROLLBACK");
    holder.close();
    const result = await Promise.race([pending, new Promise((resolve) => setTimeout(() => resolve("timeout"), 5000))]);
    report.observed.busy = { while_held: whileHeld, result, bound: bound(attemptId), events: boundEvents(taskId) };
    check("waits_for_busy_lock", whileHeld.settled === null && whileHeld.bound.native_session === null && whileHeld.events === 0 &&
      result === "ok" && bound(attemptId).native_session === pane.native_session && boundEvents(taskId) === 1, report.observed.busy);
  }
  db.close();
  report.status = report.failed.length ? "FAIL" : "PASS";
} catch (error: any) {
  report.status = "FAIL";
  report.error = `${error?.name ?? "Error"}: ${error?.message ?? String(error)}`;
  report.stack = error?.stack ?? null;
} finally {
  gates?.close();
  // A failed run keeps its fixture for diagnosis; the summary names it.
  if (report.status === "PASS") rmSync(root, { recursive: true, force: true });
}
writeFileSync(summary, JSON.stringify(report, null, 2) + "\n");
console.log(report.status, report.failed.join(",") || "", report.error ?? "");
process.exit(report.status === "PASS" ? 0 : 1);
