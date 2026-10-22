// Shared controlled PTY/process boundary. No gate verdict or provider execution.
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createRequire } from "node:module";

export function installControlledPTY(source: string, control: string, config: any) {
  const require = createRequire(join(source, "workbench/src/panes.ts"));
  const ptyModule = require.resolve("node-pty");
  const original = require(ptyModule);
  const terminals: any[] = [];
  let panes: any;
  const audit = (name: string, data: unknown) => appendFileSync(join(control, name), JSON.stringify(data) + "\n");

  require.cache[ptyModule]!.exports = {
    ...original,
    spawn(shell: string, argv: string[], options: any) {
      // Worker and reviewer share the one Codex home (T-127).
      const homes = [config.codex_home];
      if (shell !== "/bin/zsh" || !homes.includes(options.env.CODEX_HOME)) {
        audit("runtime.jsonl", { method: "controlled-spawn-refused", shell,
          home: options.env.CODEX_HOME, configured_homes: homes, launch: options.env.A2A_LAUNCH });
        throw new Error("Controlled terminal received an unexpected shell or home.");
      }
      const env = options.env;
      const facts = JSON.parse(readFileSync(join(control, "process-facts.json"), "utf8"));
      if (env.A2A_ROLE === "reviewer" && facts.fail_review_spawn) {
        audit("runtime.jsonl", { method: "controlled-review-spawn-failure", launch: env.A2A_LAUNCH });
        throw new Error("controlled-review-spawn-failure");
      }
      const native = env.A2A_ROLE === "reviewer" && facts.next_reviewer_native
        ? facts.next_reviewer_native : "fixture-native-" + env.A2A_LAUNCH;
      // Codex keeps rollouts under sessions/YYYY/MM/DD (local date); the daemon reads only those from the launch day on.
      const now = new Date();
      const day = join(env.CODEX_HOME, "sessions", String(now.getFullYear()), String(now.getMonth() + 1).padStart(2, "0"), String(now.getDate()).padStart(2, "0"));
      const log = join(day, "rollout-" + native + ".jsonl");
      mkdirSync(day, { recursive: true });
      writeFileSync(log, JSON.stringify({ type: "session_meta", payload: { source: "cli", id: native, cwd: options.cwd } }) + "\n", { flag: "wx" });
      const terminal = { pid: 31000 + terminals.length * 10, callbacks: [] as Function[], turns: 0,
        exited: false, launch: env.A2A_LAUNCH, native, log, env, restrictedOpened: false };
      terminals.push(terminal);
      // All credentials here are newly generated test capabilities. There is no
      // copied auth file, user home, native model session or provider credential.
      writeFileSync(join(control, env.A2A_LAUNCH + ".json"), JSON.stringify({
        evidence_layer: "controlled-PTY-and-process-observations", pid: terminal.pid,
        launch: terminal.launch, native, log, env, shell, argv,
      }) + "\n", { flag: "wx", mode: 0o600 });
      audit("runtime.jsonl", { method: "spawn", launch: terminal.launch, native, real_codex_turns: 0 });
      return {
        pid: terminal.pid,
        // Codex 0.163 opens an untrusted folder with this question (T-127 probe-01); the daemon answers it.
        onData(callback: Function) {
          setTimeout(() => callback("Do you trust the contents of this directory?\r\n\x1b[1m› 1. Open restricted\x1b[0m\r\n  2. Quit\r\n"), 20);
        },
        onExit(callback: Function) { terminal.callbacks.push(callback); },
        write(data: string) {
          if (terminal.exited) throw new Error("Write after controlled terminal exit.");
          const registered = panes.store.db.prepare("SELECT seq,id,launch,data FROM dispatch_records ORDER BY seq").all();
          const intents = panes.store.db.prepare("SELECT seq,launch,data FROM orchestration_events WHERE type='turn_submit_intent' ORDER BY seq").all();
          audit("writes.jsonl", { launch: terminal.launch, data, registered, intents });
          if (data === "\r" && !terminal.restrictedOpened) {
            terminal.restrictedOpened = true;
            audit("runtime.jsonl", { method: "restricted-opened", launch: terminal.launch });
            return;
          }
          if (data === "\r") {
            const turn = `fixture-turn-${++terminal.turns}`;
            appendFileSync(log, JSON.stringify({ type: "event_msg", payload: { type: "task_started", turn_id: turn } }) + "\n");
            const current = JSON.parse(readFileSync(join(control, "process-facts.json"), "utf8"));
            if (!(env.A2A_ROLE === "worker" && current.omit_worker_context)) {
              appendFileSync(log, JSON.stringify({ type: "turn_context", payload: { turn_id: turn, model: "gpt-6.1-sol", effort: "xhigh" } }) + "\n");
            }
          }
        },
        kill(signal: string) {
          if (terminal.exited) throw new Error("Duplicate controlled terminal kill.");
          const facts = JSON.parse(readFileSync(join(control, "process-facts.json"), "utf8"));
          if (env.A2A_ROLE === "reviewer" && facts.drop_reviewer_exit) {
            audit("runtime.jsonl", { method: "controlled-review-exit-not-confirmed", launch: terminal.launch, signal });
            return;
          }
          terminal.exited = true;
          audit("runtime.jsonl", { method: "kill", launch: terminal.launch, signal });
          for (const callback of terminal.callbacks) callback({ exitCode: 0, signal: 1 });
        },
      };
    },
  };

  return (runtime: any) => {
    panes = runtime;
    // Only the external process observation is supplied. No gate method, caller
    // assertion, native scan, queue, store or acceptance result is replaced.
    panes.processInfo = async (thread: string) => {
      const pane = panes.get(thread);
      const terminal = terminals.find((item) => item.launch === pane.record.id);
      if (!terminal) throw new Error("No controlled terminal for this launch.");
      const override = JSON.parse(readFileSync(join(control, "process-facts.json"), "utf8"))[pane.record.id] ?? {};
      pane.leader = override.leader ?? terminal.pid + 1;
      panes.scan(pane);
      return { shell_pid: terminal.pid, leader: pane.leader, native_session: pane.native,
        processes: [], failed: pane.failed, evidence_layer: "controlled-process-observation" };
    };
  };
}
