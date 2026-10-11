// Read-only diagnostic. No gate construction, migrations, repair or writes to state.
import { DatabaseSync } from "node:sqlite";
import { existsSync, realpathSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { parseArgs } from "node:util";

type View = Map<string, any>;
const copy = (value: any) => structuredClone(value);
const passive = new Set(["card_saved", "command_intent", "command_result", "prompt_intent", "run_observed",
  "submission_metrics", "path_check", "trailer_check", "reclaim_intent", "attachment_reclaim_intent", "rejected",
  "git_transaction_input", "git_transaction_response", "integration_worktree_advanced"]);

function differences(expected: any, observed: any, path = ""): any[] {
  if (expected === observed) return [];
  if (expected !== null && observed !== null && typeof expected === "object" && typeof observed === "object" &&
      Array.isArray(expected) === Array.isArray(observed)) {
    const keys = [...new Set([...Object.keys(expected), ...Object.keys(observed)])].sort();
    return keys.flatMap((key) => {
      const location = path ? path + "." + key : key;
      if (!Object.hasOwn(expected, key) || !Object.hasOwn(observed, key)) return [{ field: location,
        expected: Object.hasOwn(expected, key) ? { present: true, value: expected[key] } : { present: false },
        observed: Object.hasOwn(observed, key) ? { present: true, value: observed[key] } : { present: false } }];
      return differences(expected[key], observed[key], location);
    });
  }
  return [{ field: path, expected, observed }];
}

export function checkConsistency(root: string) {
  root = realpathSync(root);
  const file = join(root, "state.sqlite3"), db = new DatabaseSync(file, { readOnly: true });
  const tasks: View = new Map(), attempts: View = new Map(), verifications: View = new Map(), runs: View = new Map(), attachments: View = new Map();
  const unknown: any[] = [], historyGaps: any[] = [], completed = new Map<string, any[]>();
  let events: any[] = [];
  const reports: any[] = [];
  try {
    db.exec("BEGIN");
    events = db.prepare("SELECT seq,time,task,attempt,type,details FROM events ORDER BY seq").all();
    for (const event of events) {
      const d = JSON.parse(event.details), task = tasks.get(event.task);
      let saved = false;
      const replaceAttempt = (attempt: any) => {
        attempts.set(attempt.attempt_id, copy(attempt));
        if (task?.current_attempt?.attempt_id === attempt.attempt_id) task.current_attempt = copy(attempt);
      };
      try {
        if (["create_intent", "created", "claimed"].includes(event.type)) {
          tasks.set(event.task, copy(d)); saved = true;
        } else if (["claim_intent", "dispatch_intent"].includes(event.type)) {
          if (!task) throw new Error("Missing task creation event");
          task.current_attempt = copy(d.attempt); task.fence = d.attempt.fence; task.state = "preparing"; saved = true;
        } else if (["dispatched", "turn_bound", "runtime_bound"].includes(event.type)) {
          if (!task) throw new Error("Missing task creation event");
          task.current_attempt = copy(d.attempt); saved = true;
        } else if (event.type === "worktree_failed") {
          task.state = "paused"; task.current_attempt.state = "worktree_failed"; saved = true;
        } else if (event.type === "submitted") {
          task.current_attempt = copy(d.attempt); task.candidate_commit = d.commit; task.state = "submitted"; saved = true;
        } else if (["verification_intent", "merge_candidate", "verification_result", "verification_interrupted"].includes(event.type)) {
          const v = copy(d.verification ?? d);
          task.verification = v;
          if (event.type === "verification_intent" || event.type === "merge_candidate") task.state = "verifying";
          else task.state = v.state === "passed" ? "verified" : v.state === "unknown" ? "paused" : "submitted";
          completed.set(v.verification_id, copy(v.results)); saved = true;
        } else if (event.type === "completion_check") {
          const values = completed.get(d.verification_id);
          if (!values) throw new Error("Missing verification for completion event");
          if (d.index !== values.length + 1) throw new Error("Completion event index is out of order");
          values.push(copy(d.result));
        } else if (event.type === "completion_intent") {
          const v = task.verification;
          if (v.verification_id !== d.verification_id) throw new Error("Completion intent binds another verification");
          v.results = copy(completed.get(v.verification_id)); v.command_intent = copy(d.command); delete v.result; saved = true;
        } else if (event.type === "revoked") {
          if (d.attempt) {
            const previous = attempts.get(d.attempt);
            if (!previous) throw new Error("Missing revoked attempt history");
            previous.state = "revoked"; previous.revocation_reason = d.reason;
          }
          task.current_attempt = null; task.state = "ready"; task.spec_rev = d.spec_rev;
          task.candidate_commit = null; task.verification = null; task.integration_intent = null; saved = true;
        } else if (event.type === "integration_intent") {
          task.integration_intent = copy(d); task.state = "integrating"; saved = true;
        } else if (["integrated", "integrated_reconciled", "integration_conflict"].includes(event.type)) {
          if (event.type === "integration_conflict" && !d.intent) {
            task.state = "submitted"; task.verification = null;
          } else {
            const intent = copy(event.type === "integrated_reconciled" ? d : d.intent);
            task.integration_intent = intent;
            task.state = intent.state === "completed" ? "accepted" : "integrating";
            if (intent.state === "completed") task.current_attempt.state = "accepted";
          }
          saved = true;
        } else if (event.type === "reclaimed") {
          replaceAttempt(d.attempt); saved = true;
        } else if (["run_started", "run_bound", "run_phase", "run_finished"].includes(event.type)) {
          runs.set(d.run_id, copy(d));
        } else if (event.type === "attached" || event.type === "attachment_reclaimed") {
          attachments.set(d.attachment.thread_id, copy(d.attachment));
          if (event.type === "attached") historyGaps.push({ table: "attachments", seq: event.seq,
            row: d.attachment.thread_id, reason: "creating 状态没有对应历史事件；active 行与 attached 事件不是同一事务，最终行相等不证明该窗口完整" });
        } else if (!passive.has(event.type)) {
          unknown.push({ seq: event.seq, type: event.type, task: event.task, reason: "没有该事件的状态重建规则" });
        }
        if (saved) {
          const current = tasks.get(event.task);
          if (current?.current_attempt) attempts.set(current.current_attempt.attempt_id, copy(current.current_attempt));
          if (current?.verification) verifications.set(current.verification.verification_id, copy(current.verification));
        }
      } catch (error) {
        // Keep the observed gap; never fill replay state from current table rows.
        unknown.push({ seq: event.seq, type: event.type, task: event.task, reason: String(error) });
      }
    }
    const views = { tasks, attempts, verifications, runs, attachments };
    for (const [name, rebuilt] of Object.entries(views)) {
      const observed: View = new Map(db.prepare(`SELECT id,data FROM "${name}" ORDER BY id`).all()
        .map((row: any) => [String(row.id), JSON.parse(row.data)]));
      const keys = [...new Set([...rebuilt.keys(), ...observed.keys()])].sort(), mismatches: any[] = [];
      for (const key of keys) {
        if (!rebuilt.has(key) || !observed.has(key)) mismatches.push({ row: key,
          reason: rebuilt.has(key) ? "事件重建有行，状态表缺行" : "状态表有行，现有事件不能重建该行" });
        else mismatches.push(...differences(rebuilt.get(key), observed.get(key)).map((diff) => ({ row: key, ...diff })));
      }
      reports.push({ database: file, table: name, status: mismatches.length ? "inconsistent" : "consistent",
        rebuilt_rows: rebuilt.size, observed_rows: observed.size, mismatches,
        reason: rebuilt.size === 0 && observed.size === 0 ? "空表；本夹具未覆盖该变更路径" : undefined,
        history_gaps: historyGaps.filter((gap) => gap.table === name) });
    }
    for (const name of ["user_input_checkpoint", "role_permissions"]) {
      const count = Number(db.prepare(`SELECT count(*) AS n FROM "${name}"`).get()!.n);
      reports.push({ database: file, table: name, status: count ? "unreconstructable" : "consistent", observed_rows: count,
        reason: count ? "不经过门禁 save；当前检查器未取得可逐行重建的事件来源" : "空表；本夹具未覆盖该变更路径" });
    }
    const tableNames = db.prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").all().map((row) => String(row.name));
    db.exec("COMMIT");
    const membershipFile = join(root, "membership.sqlite3");
    if (existsSync(membershipFile)) {
      const membership = new DatabaseSync(membershipFile, { readOnly: true });
      try {
        membership.exec("BEGIN");
        for (const name of ["memberships", "session_presets"]) {
          const rows = membership.prepare(`SELECT * FROM "${name}" ORDER BY 1`).all();
          reports.push({ database: membershipFile, table: name, status: rows.length ? "unreconstructable" : "consistent",
            observed_rows: rows.length, keys: rows.map((row) => row.id ?? row.thread),
            reason: rows.length ? "另库覆盖写不经过 save；events 没有成员 revision / preset 的完整变更历史，不能借当前行补重建答案" : "空表；本夹具未覆盖该变更路径" });
        }
        membership.exec("COMMIT");
      } finally { membership.close(); }
    } else {
      for (const name of ["memberships", "session_presets"]) reports.push({ database: membershipFile, table: name,
        status: "unreconstructable", reason: "membership.sqlite3 不存在，不能宣称另库一致" });
    }
    const covered = new Set(reports.filter((r) => r.database === file).map((r) => r.table));
    for (const report of reports) report.label = ({ consistent: "一致", inconsistent: "不一致",
      unreconstructable: "无法由现有事件重建" } as Record<string, string>)[report.status];
    const allConsistent = reports.every((r) => r.status === "consistent" && !r.history_gaps?.length) && unknown.length === 0;
    return { schema: 1, status: allConsistent ? "PASS" : "INCOMPLETE", state: root,
      generated_at: new Date().toISOString(), event_cutoff_seq: events.at(-1)?.seq ?? 0,
      events_replayed: events.length, tables: reports, unknown_events: unknown,
      other_tables: tableNames.filter((name) => !covered.has(name)).map((table) => ({ table,
        reason: "事件源、追加记录或辅助表；未作为本次旧状态视图比较项，不能据此声称全库校验通过" })),
      limitations: ["检查只读，不补事件或改存储；两库各有读事务，不宣称跨库同事务，应对静止夹具运行。",
        "最终行一致不证明 attachment creating/active 中断窗口有完整历史。"] };
  } finally {
    if (db.isTransaction) db.exec("ROLLBACK");
    db.close();
  }
}

if (import.meta.main) {
  const { values } = parseArgs({ options: { state: { type: "string" }, output: { type: "string" } } });
  if (!values.state || !values.output) throw new Error("--state and --output are required");
  const output = resolve(values.output);
  let report: any;
  try { report = checkConsistency(resolve(values.state)); }
  catch (error) { report = { schema: 1, status: "INCOMPLETE", state: resolve(values.state), error: String(error), tables: [] }; }
  writeFileSync(output, JSON.stringify(report, null, 2) + "\n", { flag: "wx" });
  console.log(JSON.stringify({ status: report.status, output, tables: report.tables.length }));
  process.exitCode = report.status === "PASS" ? 0 : 1;
}
