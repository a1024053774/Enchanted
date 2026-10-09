import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const fork = process.env.T057_FORK!;
const root = process.env.T057_ROOT!;
const origin = JSON.parse(readFileSync(join(root, "ready.json"), "utf8")).origin;
process.env.VITE_WS_URL = origin.replace("http:", "ws:");
process.env.PORT = "7978";
const { createServer } = await import(join(fork, "apps/web/node_modules/vite/dist/node/index.js"));
const server = await createServer({ root: join(fork, "apps/web"), configFile: join(fork, "apps/web/vite.config.ts"),
  server: { host: "localhost", port: 7978, strictPort: true } });
await server.listen();
writeFileSync(join(root, "web-ready.json"), JSON.stringify({ origin: "http://localhost:7978", pid: process.pid }));
process.on("SIGTERM", async () => { await server.close(); process.exit(0); });
