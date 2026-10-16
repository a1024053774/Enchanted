// Domain-only contract: no CLI, PTY, socket, model, hook, or Claude fixture.
// Isolated because controller CLI execution is awaiting the user's decision.
// Failures: queue admission reported as delivery; duplicate ack sends twice;
// ready ignores project/metadata; executor cannot honor a stop immediately;
// early/acknowledged stops or argument-selected actors bypass role checks.
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { A2AGates, type GateRuntime, type SubmitCaller } from "../src/gates/core.ts";
import { A2AMembership } from "../src/gates/membership.ts";

const output = resolve(process.argv[2]!);
mkdirSync(output);
const root = mkdtempSync("/tmp/t78-domain-");
const repo = join(root, "repo");
mkdirSync(join(repo, ".project-map", "tickets"), { recursive: true });
let now = Date.parse("2026-10-11T12:00:00Z");
const wakes: any[] = [], interrupts: string[] = [];
const deliveries = new Map<string, "queued" | "delivered" | "unknown">();
const unexpected = async () => { throw new Error("This domain fixture does not run an agent lifecycle"); };
const runtime = {
  ensureProject: unexpected, createThread: unexpected, startThread: unexpected,
  stopThread: unexpected, archiveThread: unexpected,
  readThread: async () => ({ workspace: repo, provider: "codex", turn: "domain-turn", running: true, stopped: false, archived: false }),
  interruptThread: async (thread: string) => { interrupts.push(thread); },
  wakeThread: async (thread: string, entry: any) => {
    const message = "dispatch-" + entry.id;
    wakes.push({ thread, entry: entry.id, message }); deliveries.set(message, "queued");
    return { state: "queued", message };
  },
  readWakeDelivery: async (_thread: string, message: string) => ({ state: deliveries.get(message), at: new Date(now).toISOString() }),
} as unknown as GateRuntime;
const gates = new A2AGates(root, runtime, () => now);
const db = new DatabaseSync(join(root, "state.sqlite3"));
const task = { task_id: "domain-task", project_id: "domain-project", repo, state: "claimed", spec_rev: 1,
  current_attempt: { task_id: "domain-task", attempt_id: "domain-attempt", session_id: "domain-session", fence: 1,
    thread_id: "domain-worker", workspace: repo, turn_id: "domain-turn", reclaimed: false } };
db.prepare("INSERT INTO tasks(id,data) VALUES (?,?)").run(task.task_id, JSON.stringify(task));
db.prepare("INSERT INTO attempts(id,data) VALUES (?,?)").run(task.current_attempt.attempt_id, JSON.stringify(task.current_attempt));
const membership = new A2AMembership(root);
for (const preset of ["ideation", "executor"] as const) {
  const thread = "domain-" + preset;
  // These are logical addressing fixtures, not Claude launches or transcripts.
  const attachment = { thread_id: thread, task_id: task.task_id, role: "controller", preset,
    state: "active", modelSelection: { provider: "codex", model: "domain-only" } };
  db.prepare("INSERT INTO attachments(id,data) VALUES (?,?)").run(thread, JSON.stringify(attachment));
  membership.bindPreset(thread, preset);
}
const caller = (address: string): SubmitCaller => ({ address, thread: "domain-" + address, turn: "domain-turn", assertActive: async () => {} });
const operator = caller("executor"), ideation = caller("ideation");
function ticket(id: string, extra = "", status = "open") {
  writeFileSync(join(repo, ".project-map", "tickets", id + ".md"),
    `---\nid: ${id}\ntitle: ${id}\ntype: build\nstatus: ${status}\nclaimed_by:\nblocked_by: []\nready: yes\nready_by: ideation\nready_rev: 1\n${extra}---\n正文不参与就绪判断。\n`);
}
ticket("R-ready"); ticket("R-closed", "", "closed");
writeFileSync(join(repo, ".project-map", "tickets", "R-blocked.md"),
  "---\nid: R-blocked\ntitle: 依赖未完\ntype: build\nstatus: open\nclaimed_by:\nblocked_by: [R-missing]\nready: yes\nready_by: ideation\nready_rev: 1\n---\n");

const checks: any[] = [];
async function check(name: string, expectation: string, run: () => Promise<unknown>, verify: (value: any) => void) {
  const observed = await run();
  try { verify(observed); checks.push({ name, expectation, status: "PASS", observed }); }
  catch (error) { checks.push({ name, expectation, status: "INCOMPLETE", kind: "contract", observed, error: String(error) }); }
}
const sendReport = () => gates.call({ command: "inbox_send", kind: "report", to: "ideation", from: "user", body: "固定报告原文" }, operator);
const results: Record<string, unknown> = { status: "INCOMPLETE", scope: "domain-only; not credential or live CLI acceptance", root,
  argv: process.argv, node: process.version, real_model_turns: 0, claude_fixture: false, checks };
let setupError = false;
try {
  await check("queue_is_not_delivery", "收件箱已接纳；delivery.state=queued，from 取 caller executor", sendReport, value => {
    assert.equal(value.ok, true); assert.equal(value.entry.from, "executor"); assert.equal(value.delivery.state, "queued");
  });
  const report = checks[0].observed.entry;
  deliveries.set("dispatch-" + report.id, "delivered");
  await check("queued_delivery_can_be_read_back", "读回运行时已写入的投递结果", () => gates.call({ command: "inbox_list", role: "user" }, ideation), value => {
    assert.equal(value.ok, true); assert.equal(value.entries[0].entry.id, report.id); assert.equal(value.entries[0].delivery.state, "delivered");
  });
  const beforeAck = wakes.length;
  const ack1 = await gates.call({ command: "inbox_ack", id: report.id, role: "user" }, ideation);
  await check("ack_is_append_only_and_not_resent", "同一 ack 重复调用只有一条 ack 与一次 wake；排队仍是 queued",
    () => gates.call({ command: "inbox_ack", id: report.id, role: "executor" }, ideation), value => {
      assert.equal(value.ok, true); assert.equal(value.entry.id, (ack1 as any).entry.id);
      assert.equal(value.delivery.state, "queued"); assert.equal(wakes.length, beforeAck + 1);
      assert.equal(db.prepare("SELECT count(*) AS n FROM inbox_records WHERE json_extract(data,'$.kind')='ack'").get()!.n, 1);
    });
  await check("worker_cannot_assign", "worker 凭据所代表的角色不能被 from=ideation 覆盖",
    () => gates.call({ command: "inbox_send", kind: "assign", from: "ideation", to: "executor", body: "不得新增" }, caller("worker:domain-worker")), value => {
      assert.equal(value.ok, false); assert.equal(value.error, "invalid_direction");
    });
  await check("ready_bound_project", "只返回 R-ready；关闭、缺依赖的 ticket 不算就绪",
    () => gates.call({ command: "inbox_ready", project: "domain-project" }, operator), value => {
      assert.equal(value.ok, true); assert.deepEqual(value.ready.map((row: any) => row.id), ["R-ready"]);
    });
  await check("ready_rejects_unbound_project", "未知项目被拒，不根据客户端路径读取",
    () => gates.call({ command: "inbox_ready", project: "foreign-project", repo }, operator), value => {
      assert.equal(value.ok, false); assert.equal(value.error, "unknown_project");
    });
  const stop = await gates.call({ command: "inbox_send", kind: "stop", to: "executor", body: "URGENT 停止 domain-worker",
    refs: ["thread:domain-worker", "input:domain-user-stop"] }, ideation) as any;
  const beforeStop = db.prepare("SELECT data FROM tasks WHERE id=?").get(task.task_id)!.data;
  await check("executor_honors_stop_immediately", "执行主控可以立即中断，不关会话、不改门禁状态，actor=executor",
    () => gates.call({ command: "stop", thread: "domain-worker", stop_id: stop.entry.id, actor: "user" }, operator), value => {
      assert.equal(value.ok, true); assert.deepEqual(interrupts, ["domain-worker"]);
      assert.equal(db.prepare("SELECT data FROM tasks WHERE id=?").get(task.task_id)!.data, beforeStop);
      const event = db.prepare("SELECT details FROM events WHERE type='emergency_interrupt_requested' ORDER BY seq DESC LIMIT 1").get()!;
      assert.equal(JSON.parse(String(event.details)).actor, "executor");
    });
  await check("ideation_cannot_interrupt_early", "构思主控必须等超过两分钟",
    () => gates.call({ command: "stop", thread: "domain-worker", stop_id: stop.entry.id }, ideation), value => {
      assert.equal(value.ok, false); assert.equal(value.error, "stop_too_early");
    });
  now += 120001;
  await check("late_stop_actor_comes_from_caller", "超时中断记录实际 ideation，不采用 actor=user 参数",
    () => gates.call({ command: "stop", thread: "domain-worker", stop_id: stop.entry.id, actor: "user" }, ideation), value => {
      assert.equal(value.ok, true);
      const event = db.prepare("SELECT details FROM events WHERE type='emergency_interrupt_requested' ORDER BY seq DESC LIMIT 1").get()!;
      assert.equal(JSON.parse(String(event.details)).actor, "ideation");
    });
  await gates.call({ command: "inbox_ack", id: stop.entry.id }, operator);
  await check("ack_blocks_break_glass", "已有执行主控 ack 后不得超时中断",
    () => gates.call({ command: "stop", thread: "domain-worker", stop_id: stop.entry.id }, ideation), value => {
      assert.equal(value.ok, false); assert.equal(value.error, "stop_already_acknowledged");
    });
  await check("inbox_tables_are_append_only", "UPDATE/DELETE 都被触发器拒绝", async () => {
    const refused = [];
    for (const table of ["inbox_records", "inbox_deliveries"]) for (const operation of ["UPDATE", "DELETE"]) {
      try { db.exec(operation === "UPDATE" ? `UPDATE ${table} SET data='{}'` : `DELETE FROM ${table}`); refused.push(false); }
      catch (error) { refused.push(String(error).includes("append only")); }
    }
    return refused;
  }, value => assert.deepEqual(value, [true,true,true,true]));
} catch (error) { setupError = true; results.setup_error = String(error); }
finally {
  results.wakes = wakes; results.interrupts = interrupts;
  const tables: Record<string, unknown> = {};
  for (const table of ["tasks","attempts","attachments","inbox_records","inbox_deliveries","events"]) tables[table] = db.prepare(`SELECT * FROM ${table} ORDER BY rowid`).all();
  writeFileSync(join(output,"readback.json"),JSON.stringify(tables,null,2)+"\n");
  results.status = !setupError && checks.every(row => row.status === "PASS") ? "PASS" : "INCOMPLETE";
  writeFileSync(join(output,"results.json"),JSON.stringify(results,null,2)+"\n");
  for (const directory of ["gates","contracts"]) {
    mkdirSync(join(output,"source",directory),{recursive:true});
    for (const name of readdirSync(new URL(`../src/${directory}/`,import.meta.url))) if (name.endsWith(".ts")) {
      writeFileSync(join(output,"source",directory,name),readFileSync(new URL(`../src/${directory}/${name}`,import.meta.url)));
    }
  }
  writeFileSync(join(output,"source","test_t078_inbox_domain.ts"),readFileSync(new URL(import.meta.url)));
  membership.close(); db.close(); gates.close();
}
console.log(JSON.stringify({status:results.status,setup_error:results.setup_error,checks:checks.map(({name,status})=>({name,status}))}));
process.exitCode = setupError ? 2 : results.status === "PASS" ? 0 : 1;
