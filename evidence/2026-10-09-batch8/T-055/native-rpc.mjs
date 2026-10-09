import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// The fixture uses the published feature-socket protocol, not database writes.
const root = process.env.T055_EVIDENCE || dirname(fileURLToPath(import.meta.url));
const [label, endpoint, inputPath] = process.argv.slice(2);
const output = join(root, `${label}.json`);
if (existsSync(output)) throw new Error("Evidence label already exists");
const command = JSON.parse(readFileSync(inputPath, "utf8"));
const negotiate = new URL("/ws/negotiate", endpoint);
if (process.env.A2A_GATE_BEARER) negotiate.searchParams.set("token", process.env.A2A_GATE_BEARER);
negotiate.searchParams.set("x-synara-client-build", "1.0.1-beta.2");
negotiate.searchParams.set("x-synara-protocol-epoch", "1");
negotiate.searchParams.set("x-synara-protocol-min-revision", "3");
negotiate.searchParams.set("x-synara-protocol-max-revision", "3");
const response = await fetch(negotiate);
const compatibility = await response.json();
if (!response.ok) throw new Error(JSON.stringify(compatibility));
const url = new URL("/ws", endpoint);
url.protocol = "ws:";
if (process.env.A2A_GATE_BEARER) url.searchParams.set("token", process.env.A2A_GATE_BEARER);
url.searchParams.set("x-synara-client-build", "1.0.1-beta.2");
url.searchParams.set("x-synara-protocol-epoch", String(compatibility.protocolEpoch));
url.searchParams.set("x-synara-protocol-revision", String(compatibility.negotiatedRevision));
url.searchParams.set("x-synara-server-instance", compatibility.serverInstanceId);
const socket = new WebSocket(url);
const messages = [];
const result = await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error("RPC timed out")), 20000);
  socket.addEventListener("open", () => socket.send(JSON.stringify({
    _tag: "Request", id: "1", tag: process.env.A2A_RPC_TAG || "orchestration.dispatchCommand", payload: command, headers: [],
  })));
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(String(event.data));
    messages.push(message);
    if (message._tag === "Exit" && message.requestId === "1") {
      clearTimeout(timer);
      resolve(message);
    }
  });
  socket.addEventListener("error", (event) => { clearTimeout(timer); reject(event); });
});
socket.close();
writeFileSync(output, JSON.stringify({ argv: process.argv.slice(1), command, compatibility, messages }, null, 2) + "\n", "utf8");
console.log(JSON.stringify(result));
if (result.exit._tag !== "Success") process.exitCode = 1;
