import { readFileSync } from "node:fs";
const runtime = JSON.parse(readFileSync(new URL("./runtime.json", import.meta.url), "utf8"));
process.env.SYNARA_HOME = runtime.synara_home;
process.env.CODEX_HOME = runtime.codex_home;
await import("/Users/luckye/Documents/Code/synara/apps/server/src/index.ts");
