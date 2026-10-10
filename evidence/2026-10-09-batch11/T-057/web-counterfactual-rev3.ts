import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
const badSource = execFileSync("git", ["-C", process.env.T057_FORK!, "show", "e94a0efc395c26bedb6cbf65f8fdf7f5c2125a58:apps/web/src/a2a/IssueNotifications.tsx"], {encoding:"utf8"});
const fork = process.env.T057_FORK!;
const root = process.env.T057_ROOT!;
const origin = JSON.parse(readFileSync(join(root, "ready.json"), "utf8")).origin;
process.env.VITE_WS_URL = origin.replace("http:", "ws:");
process.env.PORT = "7968";
const { createServer } = await import(join(fork, "apps/web/node_modules/vite/dist/node/index.js"));
const server = await createServer({ root: join(fork, "apps/web"), configFile: join(fork, "apps/web/vite.config.ts"),
  plugins: [{name: "t057-parent-component", enforce:"pre", transform(code, id) { if (id.endsWith("/src/a2a/IssueNotifications.tsx")) return {code:badSource, map:null}; }}],
  server: { host: "localhost", port: 7968, strictPort: true } });
await server.listen();
writeFileSync(join(root, "web-ready.json"), JSON.stringify({ origin: "http://localhost:7968", pid: process.pid }));
process.on("SIGTERM", async () => { await server.close(); process.exit(0); });
