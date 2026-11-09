import { linkSync, unlinkSync, writeFileSync } from "node:fs";

// Publish only complete JSON, without replacing an earlier ready record.
// A failed publication retains the pending file for fixture diagnosis.
export function publishReady(path: string, value: Record<string, unknown>) {
  const pending = path + ".pending";
  writeFileSync(pending, JSON.stringify(value) + "\n", { flag: "wx" });
  linkSync(pending, path);
  unlinkSync(pending);
}
