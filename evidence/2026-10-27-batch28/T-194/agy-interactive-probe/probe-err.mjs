import { appendFileSync } from "node:fs";
import { createInterface } from "node:readline";
const log = process.env.PROBE_LOG;
const note = (o) => appendFileSync(log, JSON.stringify({ at: new Date().toISOString(), ...o }) + "\n");
const send = (m) => process.stdout.write(JSON.stringify(m) + "\n");
const strict = process.argv[2] === "strict";
createInterface({ input: process.stdin }).on("line", (line) => {
  let m; try { m = JSON.parse(line); } catch { return; }
  note({ method: m.method, id: m.id });
  if (m.id === undefined) return;
  if (m.method === "initialize") send({ jsonrpc: "2.0", id: m.id, result: { protocolVersion: m.params?.protocolVersion ?? "2025-06-18", capabilities: { tools: {} }, serverInfo: { name: "probe", version: "1" } } });
  else if (m.method === "tools/list") send({ jsonrpc: "2.0", id: m.id, result: { tools: [{ name: "probe_echo", description: "Returns the word you give it, uppercased.", inputSchema: { type: "object", properties: { word: { type: "string" } }, required: ["word"] } }] } });
  else if (m.method === "tools/call") send({ jsonrpc: "2.0", id: m.id, result: { content: [{ type: "text", text: String(m.params?.arguments?.word ?? "").toUpperCase() + "-PROBED" }] } });
  else if (m.method === "ping") send({ jsonrpc: "2.0", id: m.id, result: {} });
  else if (strict) send({ jsonrpc: "2.0", id: m.id, error: { code: -32601, message: "method not found: " + m.method } });
  else send({ jsonrpc: "2.0", id: m.id, result: {} });
});
