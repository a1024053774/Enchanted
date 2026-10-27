// T-197: the task page shows an overlap let through with its reason, from the gate's real events of the green run.
// Usage: node history_check.ts <state.sqlite3 of a green T-131 run>
import { DatabaseSync } from "node:sqlite";
import { taskHistory } from "../../../workbench/src/gates/taskHistory.ts";
const db = new DatabaseSync(process.argv[2]!, { readOnly: true });
const events = db.prepare("SELECT seq, time, attempt, type, details FROM events WHERE task=? ORDER BY seq").all("demo+T-5")
  .map((row: any) => ({ seq: Number(row.seq), time: String(row.time), attempt: row.attempt === null ? null : String(row.attempt), type: String(row.type), details: JSON.parse(String(row.details)) }));
const steps = taskHistory(events).steps.filter(step => step.label === "路径重叠");
const reason = "T-5 与 T-4 都写 a.txt，由集成时的合并处理";
// Expected from the scenario: one plain refusal (no reason) and one let through with the reason; the blank reason never reached the check.
const ok = steps.length === 2 && steps[0]!.passed === false && !steps[0]!.detail!.includes("放行理由") &&
  steps[1]!.passed === true && steps[1]!.detail!.includes("demo+T-4") && steps[1]!.detail!.endsWith(`放行理由：${reason}`);
console.log(JSON.stringify({ status: ok ? "PASS" : "FAIL", steps }, null, 2));
process.exit(ok ? 0 : 1);
