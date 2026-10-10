import { writeFileSync } from "node:fs";
import { join } from "node:path";
const { A2AGates } = await import("/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts");
const root = process.env.T064_CRASH_ROOT!;
const gates = new A2AGates(root);
const db = (gates as any).db;
db.function("t064_pause", () => {
  writeFileSync(join(root, "inside-transaction.json"), JSON.stringify({ pid: process.pid, point: "role row written, before user input insert" }));
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 30000);
  return 1;
});
db.exec("CREATE TEMP TRIGGER t064_pause_input BEFORE INSERT ON user_inputs BEGIN SELECT t064_pause(); END");
gates.saveRolePermissionSettings({ command: "save", role: "worker", revision: 0, selection: { capabilities: [], autoApproveTools: [] } });
throw new Error("Parent failed to interrupt the injected transaction");
