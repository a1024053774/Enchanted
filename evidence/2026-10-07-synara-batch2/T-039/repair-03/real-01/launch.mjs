import { readFileSync } from "node:fs";
const runtime = JSON.parse(readFileSync(new URL("./runtime.json", import.meta.url), "utf8"));
process.env.SYNARA_HOME = runtime.synara_home;
process.env.CODEX_HOME = runtime.codex_home;
process.env.SYNARA_AUTH_TOKEN = readFileSync(`${runtime.root}/bootstrap-token`, "utf8");
process.env.SYNARA_LOG_PROVIDER_EVENTS = "true";
process.env.SYNARA_LOG_WS_EVENTS = "false";
await import("/Users/luckye/Documents/Code/synara/apps/server/src/index.ts");
