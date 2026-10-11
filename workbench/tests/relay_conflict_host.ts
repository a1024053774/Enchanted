// Real daemon, Panes, relay and gates. Only the external PTY/process boundary
// is scripted. The version stub never launches Codex or reads credentials.
import { appendFileSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
const [source, state, control, ready] = process.argv.slice(2);
if (!source || !state || !control || !ready) throw new Error("source, state, control and ready required");
const { serve } = await import(pathToFileURL(join(source, "workbench/src/daemon.ts")).href);
const { A2AGates } = await import(pathToFileURL(join(source, "workbench/src/gates/core.ts")).href);
const require = createRequire(pathToFileURL(join(source, "workbench/src/panes.ts")));
const home = join(control, "home"); mkdirSync(join(home, "sessions"), { recursive: true });
const version = join(control, "version-only");
writeFileSync(version, '#!/bin/sh\nprintf "codex-cli 0.162.1\\n"\n', { mode: 0o700, flag: "wx" });
const role = join(control, "role.txt"); writeFileSync(role, "确定性夹具；没有模型或真实 worker。", { flag: "wx" });
const terminals = new Map<string, any>();
require.cache[require.resolve("node-pty")] = { exports: { spawn: (_shell: string, _argv: string[], options: any) => {
  const launch = options.env.A2A_LAUNCH, native = "fixture-native-" + launch;
  const file = join(home, "sessions", "rollout-" + native + ".jsonl");
  const pid = 21001 + terminals.size * 10, exits: ((value: any) => void)[] = [];
  const runtime = { native, file, cwd: options.cwd, turn: 0, shell: pid, leader: pid + 1, exited: false };
  const save = () => writeFileSync(join(control, launch + ".runtime.json"), JSON.stringify(runtime) + "\n");
  writeFileSync(join(control, launch + ".env.json"), JSON.stringify(options.env) + "\n", { flag: "wx" });
  const exit = () => {
    if (runtime.exited) return;
    runtime.exited = true; save();
    for (const callback of [...exits]) callback({ exitCode: 0, signal: 0 });
  };
  terminals.set(launch, { runtime, exit }); save();
  return { pid, onData: () => {}, onExit: (callback: any) => exits.push(callback), kill: exit,
    write: (data: string) => {
      appendFileSync(join(control, "pty.jsonl"), JSON.stringify({ launch, data }) + "\n");
      if (data !== "\r") return;
      if (!runtime.turn) writeFileSync(file, JSON.stringify({ type: "session_meta",
        payload: { id: native, source: "cli", cwd: options.cwd, cli_version: "0.162.1" } }) + "\n", { flag: "wx" });
      runtime.turn++;
      appendFileSync(file, JSON.stringify({ type: "event_msg", payload: { type: "task_started", turn_id: "turn-" + runtime.turn } }) + "\n");
      save();
    } };
} } } as any;
await serve(state, { codex_bin: version, codex_home: home, role_card: role,
  code_revision: "controlled-relay-conflict", role_card_revision: "controlled-relay-conflict",
  hook_authorization: "synthetic hook calls only", turn_limit: 4 }, (root: string, panes: any) => {
  panes.processInfo = async (thread: string) => {
    const pane = panes.get(thread), terminal = terminals.get(pane.record.id);
    panes.scan(pane);
    if (existsSync(join(control, pane.record.id + ".exit"))) terminal.exit();
    const runtime = terminal.runtime;
    if (pane.leader === null) pane.leader = runtime.leader;
    return { shell_pid: runtime.shell, leader: runtime.exited ? null : runtime.leader,
      native_session: pane.native, processes: runtime.exited ? [] : [{ pid: runtime.shell }, { pid: runtime.leader }], failed: pane.failed };
  };
  return new A2AGates(root, panes);
});
writeFileSync(ready, JSON.stringify({ source, state, control, pid: process.pid,
  pty: "controlled", process_observer: "controlled", real_codex_turns: 0 }) + "\n", { flag: "wx" });
