import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const fork = process.env.T057_FORK!;
const root = process.env.T057_ROOT!;
const origin = JSON.parse(readFileSync(join(root, "ready.json"), "utf8")).origin;
process.env.VITE_WS_URL = origin.replace("http:", "ws:");
process.env.PORT = "8078";
const { createServer } = await import(join(fork, "apps/web/node_modules/vite/dist/node/index.js"));
const evidence = new URL('.', import.meta.url).pathname;
const baseline = process.env.T065_BASELINE === '1';
const server = await createServer({ root: join(fork, "apps/web"), configFile: join(fork, "apps/web/vite.config.ts"),
  plugins: baseline ? [{ name: 't065-known-bad-source', enforce: 'pre', load(id: string) {
    const path = id.split('?')[0];
    if (path === join(fork, 'apps/web/src/components/ChatView.tsx')) return readFileSync(join(evidence, 'baseline-ChatView.tsx'), 'utf8');
    if (path === join(fork, 'apps/web/src/a2a/IssueNotifications.tsx')) return readFileSync(join(evidence, 'baseline-IssueNotifications.tsx'), 'utf8');
    if (path === join(fork, 'apps/web/src/a2a/IssuePanel.tsx')) return readFileSync(join(evidence, 'baseline-IssuePanel.tsx'), 'utf8');
    if (path === join(fork, 'apps/web/src/a2a/TaskWindow.tsx')) return readFileSync(join(evidence, 'baseline-TaskWindow.tsx'), 'utf8');
  } }] : [],
  server: { host: "localhost", port: 8078, strictPort: true } });
await server.listen();
writeFileSync(join(root, "web-ready.json"), JSON.stringify({ origin: "http://localhost:8078", pid: process.pid }));
process.on("SIGTERM", async () => { await server.close(); process.exit(0); });
