// Production daemon/relay/gates with a real PTY deterministic provider boundary.
// No vendor executable is spawned. The worker target remains the native receiver.
import { createRequire } from "node:module";
import { existsSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { serve } from "../src/daemon.ts";
import { A2AGates } from "../src/gates/core.ts";
import { createOperatorCredential, readOperatorCredential } from "../src/credentials.ts";
import { request } from "../src/transport.ts";
import { publishReady } from "./ready_file.ts";

const [scratchArg, configFile, structureFile] = process.argv.slice(2);
const scratch = realpathSync(scratchArg);
if (!scratch.startsWith("/private/tmp/t078-2-a14-rehearsal-")) throw new Error("owned scratch required");
const state = join(scratch, "state");
const peer = resolve("workbench/tests/t078_09b_rehearsal_peer.py");
const cli = resolve("workbench/src/gates/cli.ts");
const launchConfig = JSON.parse(readFileSync(configFile, "utf8"));
const receiver = join(scratch, "target", "bin", "codex-receiver");
if (realpathSync(launchConfig.codex_bin) !== receiver) throw new Error("owned deterministic receiver required");
const exec = promisify(execFile);
process.env.A2A_OPERATOR_CREDENTIAL = join(scratch, "operator.json");
createOperatorCredential(state);
const pty = createRequire(import.meta.url)("node-pty"), spawn = pty.spawn;
let panes: any;
const actualPeers = new Map<string, { shell: number; role: string; tail: string; start: string | null }>();
pty.spawn = (file: string, args: string[], options: any) => {
  if (options.env.A2A_ROLE !== "controller") {
    if (file !== "/bin/zsh" || options.env.A2A_ROLE !== "worker" || !args.some(arg => arg.includes(receiver))) {
      throw new Error("unapproved rehearsal executable; no vendor spawn");
    }
    return spawn(file, args, options);
  }
  const record = panes.store.launchRecord(options.env.A2A_LAUNCH);
  const commands = ["UserPromptSubmit", "Stop", "PermissionRequest"].map(
    event => record.settings.hooks[event][0].hooks[0].command);
  if (!commands.every(command => command === commands[0])) throw new Error("native hook commands differ");
  const peerArgs = ["-B", peer, "--root", scratch, "--role", record.preset, "--structure", resolve(structureFile),
    "--session-id", record.session, "--debug-file", join(scratch,"roles",record.preset,"claude-debug.log")];
  const quote = (arg: string) => "'" + arg.replaceAll("'", "'\\''") + "'";
  // Keep a real shell parent. The command after Python prevents tail exec.
  const command = ["/usr/bin/python3", ...peerArgs].map(quote).join(" ") + "; peer_status=$?; exit $peer_status";
  const terminal = spawn("/bin/zsh", ["-f","-i","-c",command], { ...options, env: { ...options.env,
    T078_REHEARSAL_HOOK: commands[0], T078_REHEARSAL_NODE: process.execPath, T078_REHEARSAL_CLI: cli } });
  actualPeers.set(record.id, { shell: terminal.pid, role: record.preset, tail: peerArgs.join(" "), start: null });
  writeFileSync(join(scratch, "peer-identities.json"), JSON.stringify([...actualPeers.entries()].map(
    ([launch, value]) => ({ launch, ...value })), null, 2) + "\n");
  return terminal;
};

await serve(state, launchConfig, (root, value) => {
  panes = value;
  const original = value.processInfo.bind(value);
  // This is solely the provider identity seam. Check a real peer PID/argv and
  // two actual lstart reads; caller/Stop/auth/relay and all writes stay real.
  value.processInfo = async (thread: string) => {
    const pane = value.get(thread);
    if (pane.record.role !== "controller") return original(thread);
    const owned = actualPeers.get(pane.record.id);
    if (!owned || owned.shell !== pane.pty.pid) throw new Error("provider peer binding changed");
    const readyFile=join(scratch,"peer",owned.role,"ready.json");
    if (!existsSync(readyFile)) return {shell_pid:owned.shell,leader:null,processes:[],failed:pane.failed};
    const actual=JSON.parse(readFileSync(readyFile,"utf8"));
    if (actual.role!==owned.role || actual.session!==pane.record.session) throw new Error("provider peer session changed");
    const pid=actual.pid;
    const probe = async () => {
      const result = await exec("/bin/ps", ["-ww", "-p", String(pid), "-o", "ppid=,lstart=,command="],
        { env: { ...process.env, LC_ALL: "C", LANG: "C" } });
      const match = /^\s*(\d+)\s+(\w{3}\s+\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\d{4})\s+(.+?)\s*$/.exec(result.stdout);
      if (!match || Number(match[1])!==owned.shell || !match[3].endsWith(" " + owned.tail)) throw new Error("provider peer argv/parent changed");
      return match[2];
    };
    const first = await probe(), second = await probe();
    if (first !== second || (owned.start !== null && owned.start !== first)) throw new Error("provider peer lifetime changed");
    owned.start = first;
    return { shell_pid: owned.shell, leader: pid, native_session: pane.native,
      session_ended: false, processes: [{ pid: owned.shell, command: "/bin/zsh" },{ pid, command: peer }], failed: pane.failed };
  };
  return new A2AGates(root, value);
});
publishReady(join(scratch, "host-ready.json"), { pid: process.pid, state,
  provider_boundary: "real node-pty Python replacement; verified PID/argv/lstart; no Claude" });

let stopping = false;
const stop = async () => {
  if (stopping) return;
  stopping = true;
  try { await request(state, { command: "daemon_stop" }, readOperatorCredential(state)); }
  catch (error) { console.error(error); process.exitCode = 1; }
};
process.once("SIGTERM", () => { void stop(); });
// Unref permits a normally closed daemon to exit without waiting for this timer.
setTimeout(() => { console.error("rehearsal_host_hard_timeout"); void stop(); }, 400_000).unref();
