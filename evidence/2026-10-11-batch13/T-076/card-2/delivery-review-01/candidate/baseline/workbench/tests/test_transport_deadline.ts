// Isolated transport timer contract; no socket, process, daemon or model starts.
// Failure modes: explicit run wait exceeds the client timer, ordinary/invalid
// calls lose their bounded deadline, or the timer overflows into a short wait.
import assert from "node:assert/strict";
import { createRequire, syncBuiltinESMExports } from "node:module";
import { EventEmitter } from "node:events";
import { mkdirSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { resolve, join } from "node:path";

const [modulePath, outputPath] = process.argv.slice(2);
if (!modulePath || !outputPath) throw new Error("transport module and new output directory are required");
const output = resolve(outputPath); mkdirSync(output, { recursive: true });
const require = createRequire(import.meta.url), net = require("node:net");
let scheduled = 0;
net.createConnection = () => {
  const socket: any = new EventEmitter();
  socket.setEncoding = () => socket;
  socket.setTimeout = (milliseconds: number) => { scheduled = milliseconds; return socket; };
  socket.write = () => queueMicrotask(() => socket.emit("data", '{"ok":true,"fixture":"timer-only"}\n'));
  socket.end = () => queueMicrotask(() => socket.emit("close"));
  queueMicrotask(() => socket.emit("connect"));
  return socket;
};
syncBuiltinESMExports();
const { request } = await import(pathToFileURL(resolve(modulePath)).href);
const cases = [
  { name: "explicit-900-second-run", input: { command: "run", wait_seconds: 900 }, minimum: 900_000, exact: null },
  { name: "ordinary-call", input: { command: "status" }, minimum: 120_000, exact: 120_000 },
  { name: "invalid-run-wait", input: { command: "run", wait_seconds: -1 }, minimum: 120_000, exact: 120_000 },
];
const results = [];
for (const row of cases) {
  let failure = null;
  await request("/tmp/t076-timer-only", row.input);
  try {
    assert.ok(scheduled >= row.minimum, "A run client must cover the explicit wait instead of aborting at 120 seconds");
    if (row.exact !== null) assert.equal(scheduled, row.exact);
    assert.ok(Number.isFinite(scheduled) && scheduled <= 2_147_483_647, "The Node timer must remain bounded without integer overflow");
  } catch (error) { failure = String(error); }
  results.push({ case: row.name, input: row.input, scheduled_ms: scheduled, expected_minimum_ms: row.minimum, failure });
}
const record = { status: results.some((row) => row.failure) ? "INCOMPLETE" : "PASS",
  module: resolve(modulePath), real_codex_turns: 0, network: "simulated connection/timer; no real socket", results };
writeFileSync(join(output, "run.json"), JSON.stringify(record, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify(record));
process.exitCode = record.status === "PASS" ? 0 : 1;
