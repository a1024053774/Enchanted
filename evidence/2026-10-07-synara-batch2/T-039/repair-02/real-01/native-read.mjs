import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const here = dirname(fileURLToPath(import.meta.url));
const runtime = JSON.parse(readFileSync(join(here, "runtime.json"), "utf8"));
const [label, threadId] = process.argv.slice(2);
const output = join(here, `${label}.json`);
if (existsSync(output)) throw new Error("Evidence label already exists");
const token = readFileSync(`${runtime.root}/bootstrap-token`, "utf8");
const negotiate = new URL("/ws/negotiate", runtime.endpoint);
negotiate.searchParams.set("token", token);
negotiate.searchParams.set("x-synara-client-build", "1.0.1-beta.2");
negotiate.searchParams.set("x-synara-protocol-epoch", "1");
negotiate.searchParams.set("x-synara-protocol-min-revision", "3");
negotiate.searchParams.set("x-synara-protocol-max-revision", "3");
const response = await fetch(negotiate);
const compatibility = await response.json();
if (!response.ok) throw new Error(JSON.stringify(compatibility));
const url = new URL("/ws", runtime.endpoint);
url.protocol = "ws:";
url.searchParams.set("token", token);
url.searchParams.set("x-synara-client-build", "1.0.1-beta.2");
url.searchParams.set("x-synara-protocol-epoch", String(compatibility.protocolEpoch));
url.searchParams.set("x-synara-protocol-revision", String(compatibility.negotiatedRevision));
url.searchParams.set("x-synara-server-instance", compatibility.serverInstanceId);
const socket = new WebSocket(url);
const request = { _tag: "Request", id: "1", tag: "orchestration.getThreadDetailSnapshot", payload: { threadId }, headers: [] };
const messages = [];
const result = await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error("RPC timed out")), 20000);
  socket.addEventListener("open", () => socket.send(JSON.stringify(request)));
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
const record = JSON.stringify({ time: new Date().toISOString(), argv: process.argv.slice(1), request, compatibility, messages }, null, 2);
if (record.includes(token)) throw new Error("Private token appeared in read result");
writeFileSync(output, record + "\n", "utf8");
console.log(JSON.stringify(result));
if (result.exit._tag !== "Success") process.exitCode = 1;
