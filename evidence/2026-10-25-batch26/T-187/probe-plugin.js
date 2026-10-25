import { appendFileSync } from "node:fs";
const log = process.env.T187_EVENT_LOG;
const write = (kind, value) => appendFileSync(log, JSON.stringify({ t: Date.now(), kind, value }) + "\n");
export const T187Probe = async () => ({
  event: async ({ event }) => write("event", { type: event.type, status: event.properties?.status, keys: Object.keys(event.properties ?? {}) }),
  "tool.execute.before": async (input) => write("tool.before", { tool: input.tool }),
  "permission.ask": async (input) => write("permission.ask", { type: input.type, title: input.title }),
});
