// T-253 review 01 P2, daemon side: the daemon's own callback for a Codex worker pane that has learned its native session.
// Real serve(), gates, stores and private hc core; the pane is a fixture object handed to that callback, and its read is
// scripted. No CLI, PTY child, hook or model. Usage: t253_shutdown_host.ts <source> <state> <control> <ready> <scenario>.
// Ways it can fail, listed before writing:
// 1. stop_while_binding: the daemon closes its stores while a binding is still reading the pane. The binding then meets a
//    closed database, and its refusal record throws again: an unhandled rejection, a non-zero exit, nothing recorded.
//    Expected: the daemon waits for the binding, records native_session_bind_failed (daemon_stopping) and exits 0.
// 2. record_write_fails: the refusal record itself cannot be written. The throw inside the catch is an unhandled
//    rejection that ends the daemon. Expected: the daemon stays up, reports event_write_failed on stderr, stops cleanly.
import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [source, state, control, ready, scenario] = process.argv.slice(2);
if (!source || !state || !control || !ready || !["stop_while_binding", "record_write_fails"].includes(scenario ?? "")) {
  throw new Error("usage: t253_shutdown_host.ts <source> <state> <control> <ready> stop_while_binding|record_write_fails");
}
const load = (path: string) => import(pathToFileURL(join(source, "workbench/src", path)).href);
const { serve } = await load("daemon.ts");
const { A2AGates } = await load("gates/core.ts");
const { createOperatorCredential } = await load("credentials.ts");
const note = (name: string, value: Record<string, unknown> = {}) =>
  appendFileSync(join(control, "host.jsonl"), JSON.stringify({ at: new Date().toISOString(), name, ...value }) + "\n");
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

mkdirSync(state, { recursive: true, mode: 0o700 });
createOperatorCredential(state);
const version = join(control, "version-only");
writeFileSync(version, '#!/bin/sh\nprintf "codex-cli 0.164.0\\n"\n', { mode: 0o700 });
const role = join(control, "role.txt");
writeFileSync(role, "本地确定性夹具，不运行 CLI 或模型。\n");
mkdirSync(join(control, "home"), { recursive: true });

let gates: any, panes: any, closed = false;
await serve(state, { codex_bin: version, codex_home: join(control, "home"), role_card: role,
  code_revision: "t253-fixture", role_card_revision: "t253-fixture" }, (root: string, owned: any) => {
  panes = owned;
  gates = new A2AGates(root, owned);
  // Observed only: the original close runs unchanged.
  const close = gates.close.bind(gates);
  gates.close = () => { closed = true; note("gates_closed"); close(); };
  return gates;
});

const pane = { record: { id: "t253-launch", task: "T253-fixture", attempt: "attempt-fixture", thread: "t253-thread",
  role: "worker", project: "t253", cli: "Codex" }, native: "codex-fixture-session" };
panes.readThread = async (thread: string) => {
  note("read_entered", { thread });
  if (scenario === "stop_while_binding") {
    writeFileSync(join(control, "bind-entered"), "the binding is reading the pane\n");
    while (!gates.shuttingDown) await sleep(10);
    note("stop_seen");
    // The read ends when the gate closes or after 2 s, whichever comes first.
    const until = Date.now() + 2000;
    while (!closed && Date.now() < until) await sleep(10);
    note("read_returned", { after: closed ? "gates_closed" : "timeout" });
  }
  return { workspace: control, provider: "codex", turn: null, running: true, stopped: false, archived: false, blocked: false,
    runtime_identity: { launch: pane.record.id, thread, shell_pid: 4100, leader_pid: 4101, native_session: pane.native } };
};
if (scenario === "record_write_fails") {
  const event = panes.store.event.bind(panes.store);
  panes.store.event = (type: string, data: unknown, binding?: unknown) => {
    if (type === "native_session_bind_failed") { note("record_refused"); throw new Error("fixture: event write refused"); }
    return event(type, data, binding);
  };
}
panes.nativeSessionLearned(pane);
note("callback_called");
writeFileSync(ready, JSON.stringify({ pid: process.pid, source, state, control, scenario, pane: pane.record }) + "\n", { flag: "wx" });
