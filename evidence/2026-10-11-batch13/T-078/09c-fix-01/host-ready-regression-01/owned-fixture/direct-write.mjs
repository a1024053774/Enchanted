import {writeFileSync} from "node:fs";
export function publishReady(path,value) { writeFileSync(path, JSON.stringify(value)+"\n", {flag:"wx"}); }
