import { readFileSync } from "node:fs";
const runtime = JSON.parse(readFileSync(new URL("./runtime.json", import.meta.url), "utf8"));
// The cache wrapper owns build paths. Runtime homes are explicit fixture inputs.
process.env.SYNARA_HOME = runtime.synara_home;
process.env.CODEX_HOME = runtime.codex_home;
process.env.SYNARA_DESKTOP_SMOKE_USER_DATA = `${runtime.root}/electron-profile`;
process.env.VITE_DEV_SERVER_URL = "http://localhost:5733/";
process.chdir("/Users/luckye/Documents/Code/synara/apps/desktop");
await import("/Users/luckye/Documents/Code/synara/apps/desktop/scripts/start-electron.mjs");
