// OS-boundary fixture only. No authentication, vendor CLI or model protocol.
import { createServer, get } from "node:http";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const options = JSON.parse(readFileSync(process.argv[2], "utf8"));
const role = process.argv[3], directory = join(options.root, role);
const servers = [], sockets = new Set();
let received = 0, forwarded = 0, closing = false;
function save(name, value) {
  writeFileSync(join(directory, name), JSON.stringify(value) + "\n", { flag: "wx", mode: 0o600 });
}
function listen(port, receive) {
  const server = createServer(receive);
  server.on("connection", socket => { sockets.add(socket); socket.on("close", () => sockets.delete(socket)); });
  servers.push(server);
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", () => { server.off("error", reject); resolve(); });
  });
}
try {
  if (role === "U") {
    for (const port of [options.upstream_port, options.other_port]) {
      await listen(port, (request, response) => {
        if (request.url !== "/t093-connection-probe" || request.method !== "GET" || request.headers.authorization) {
          response.writeHead(400).end(); return;
        }
        received++;
        response.writeHead(200, { "content-type": "text/plain" }).end("local-probe-ok");
      });
    }
  } else if (role === "F") {
    await listen(options.forward_port, (request, response) => {
      if (request.url !== "/t093-connection-probe" || request.method !== "GET" || request.headers.authorization) {
        response.writeHead(400).end(); return;
      }
      received++;
      const upstream = get(`http://127.0.0.1:${options.upstream_port}/t093-connection-probe`, result => {
        forwarded++;
        response.writeHead(result.statusCode);
        result.pipe(response);
      });
      upstream.setTimeout(1500, () => upstream.destroy());
      upstream.on("error", () => response.writeHead(502).end());
    });
    // An occupied address cannot stand in for a permission denial. This is a
    // separate, previously unused port. EPERM/EACCES is the required result.
    const denied = createServer();
    const bind = await new Promise(resolve => {
      denied.once("error", error => resolve({ denied: ["EPERM", "EACCES"].includes(error.code), code: error.code }));
      denied.listen(options.bind_probe_port, "127.0.0.1", () => denied.close(() => resolve({ denied: false, code: null })));
    });
    save("bind-probe.json", bind);
  } else throw new Error("invalid_role");
  save("ready.json", { pid: process.pid, ppid: process.ppid, role, profile: role,
    ports: role === "F" ? [options.forward_port] : [options.upstream_port, options.other_port] });
  const timer = setInterval(async () => {
    if (closing || (!existsSync(join(directory, "stop")) && Date.now() < options.deadline_ms)) return;
    closing = true; clearInterval(timer);
    for (const socket of sockets) socket.destroy();
    await Promise.all(servers.map(server => new Promise(resolve => server.close(resolve))));
    save("closed.json", { received, forwarded, deadline_reached: Date.now() >= options.deadline_ms });
    if (role === "U") process.execve("/usr/bin/python3", ["/usr/bin/python3", "-I", "-S", "-B", options.python_probe,
      "--stage", "U-after", "--options", join(options.root, "options.json")], { PATH: "/usr/bin:/bin", LANG: "C" });
  }, 30);
} catch (error) {
  // Never persist arbitrary error text or a terminal stream.
  save("endpoint-failure.json", { kind: "endpoint_setup_failed", code: typeof error.code === "string" ? error.code : null });
  for (const socket of sockets) socket.destroy();
  for (const server of servers) server.close();
  process.exitCode = 2;
}
