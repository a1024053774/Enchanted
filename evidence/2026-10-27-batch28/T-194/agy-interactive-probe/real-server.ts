import { appendFileSync } from "node:fs";
import { serveMcp } from "/private/tmp/t194-dev2/workbench/src/terminalMcp.ts";
const log = (o: unknown) => appendFileSync(process.env.PROBE_LOG!, JSON.stringify(o) + "\n");
process.stdin.on("data", d => log({ in: String(d).slice(0, 300) }));
const out = process.stdout.write.bind(process.stdout);
(process.stdout as any).write = (chunk: any, ...rest: any[]) => { log({ out: String(chunk).slice(0, 300) }); return out(chunk, ...rest); };
serveMcp(async input => ({ ok: true, echo: input }), async role => ({ ok: true, role }));
