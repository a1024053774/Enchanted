import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const fork = "/Users/luckye/Documents/Code/synara";
const root = process.env.T064_ROOT!;
const backend = JSON.parse(readFileSync(join(root, "ready.json"), "utf8")).origin;
process.env.VITE_WS_URL = backend.replace("http:", "ws:");
process.env.PORT = "8088";
const { createServer } = await import(join(fork,"apps/web/node_modules/vite/dist/node/index.js"));
const server = await createServer({ root: join(fork,"apps/web"), configFile: join(fork,"apps/web/vite.config.ts"),
  cacheDir: join(root,"vite"), server: { host:"localhost",port:8088,strictPort:true } });
await server.listen();
writeFileSync(join(root,"web-ready.json"),JSON.stringify({origin:"http://localhost:8088",pid:process.pid}));
process.on("SIGTERM",async()=>{await server.close();process.exit(0);});
