// Test-only PTY and process observations. The daemon, CLI, relay, gates,
// registration queue, Git and SQLite remain the selected product source.
// This host never runs Codex or supplies a review verdict.
import { mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { installControlledPTY } from "./controlled_quality_pty.ts";
import { pathToFileURL } from "node:url";
import { publishReady } from "./ready_file.ts";

const [source, root, control, ready] = process.argv.slice(2);
if (process.argv.length !== 6) throw new Error("Expected source, state, control and ready paths.");
const load = (name: string) => import(pathToFileURL(join(source, "workbench/src", name)).href);
const { serve } = await load("daemon.ts");
const { A2AGates } = await load("gates/core.ts");
const { createOperatorCredential } = await load("credentials.ts");
const config = JSON.parse(readFileSync(join(control, "config.json"), "utf8"));
const bind = installControlledPTY(source, control, config);

mkdirSync(root, { recursive: true, mode: 0o700 });
createOperatorCredential(root);
await serve(root, config, (state: string, runtime: any) => {
  bind(runtime);
  return new A2AGates(state, runtime);
});
publishReady(ready, { pid: process.pid, source, root, control, argv: process.argv,
  evidence_layer: "real-CLI-daemon-relay-gates-Git-SQLite; controlled-PTY-process-native-inputs",
  real_codex_turns: 0, replaces: ["node-pty.spawn", "Panes.processInfo"] });
