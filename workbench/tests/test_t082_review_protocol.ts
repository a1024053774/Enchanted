// T-082 contract: the gate's requested review output must traverse the strict
// parser with its report intact. Inputs come from the recorded real reviewer.
// Failure modes: unrecognized template fields, dropped report, report with a
// wrong type, missing identity, extra fields, and Markdown extraction.
import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [source, payloadPath, output] = process.argv.slice(2);
if (!source || !payloadPath || !output) throw new Error("Expected source, payload, and output paths.");
const { reviewRequest } = await import(pathToFileURL(resolve(source, "workbench/src/gates/qualityProtocol.ts")).href);
const raw = readFileSync(payloadPath, "utf8");
const payload = JSON.parse(raw);
const checks: string[] = [];
let failure: string | null = null;
try {
  const accepted = reviewRequest(raw);
  assert.deepEqual(accepted, payload, "T082-REAL-PAYLOAD: preserve every requested field and the complete report");
  checks.push("T082-REAL-PAYLOAD");
  assert.deepEqual(accepted.report, payload.report);
  assert.deepEqual(accepted.review_requirements, payload.review_requirements);
  checks.push("T082-REPORT-INTACT");
  const reject = (id: string, value: unknown, field: string) => {
    assert.throws(() => reviewRequest(JSON.stringify(value)), (error: any) => error.field === field, id);
    checks.push(id);
  };
  reject("T082-REPORT-OBJECT", { ...payload, report: "unstructured report" }, "report");
  reject("T082-REPORT-ARRAY", { ...payload, report: [] }, "report");
  reject("T082-REPORT-NULL", { ...payload, report: null }, "report");
  reject("T082-REPORT-SECTION", { ...payload, report: { "审查结论": "没有必需的独立节" } }, "report.section");
  assert.equal(reviewRequest(JSON.stringify({ ...payload, report: { "完成条件与变异检查": null } }))
    .report["完成条件与变异检查"], null, "T082-SECTION-EXISTS-ONLY");
  checks.push("T082-SECTION-EXISTS-ONLY");
  reject("T082-REQUIREMENTS-EXACT", { ...payload, review_requirements: { ...payload.review_requirements, unknown: true } }, "review_requirements");
  const missing = { ...payload }; delete missing.session;
  reject("T082-IDENTITY-REQUIRED", missing, "review_request");
  reject("T082-UNKNOWN-FIELD", { ...payload, unknown: true }, "review_request");
  assert.throws(() => reviewRequest("```json\n" + raw + "\n```"), (error: any) => error.field === "review_json");
  checks.push("T082-STRICT-JSON");
  const { OrchestrationStore } = await import(pathToFileURL(resolve(source, "workbench/src/store.ts")).href);
  const { RequestRelay } = await import(pathToFileURL(resolve(source, "workbench/src/relay.ts")).href);
  const { mkdirSync } = await import("node:fs");
  const state = join(dirname(output), "relay-store");
  mkdirSync(state);
  const store = new OrchestrationStore(state);
  try {
    const relay = new RequestRelay(store);
    const binding = { id: "real-report-replay", role: "reviewer", task: payload.task, attempt: payload.attempt,
      session: payload.session, fence: payload.fence, spec_rev: payload.spec_rev, review_id: payload.review_id };
    let transferred: any;
    const receipt = await relay.receive(binding, { name: payload.request_id + ".json", raw }, true, async (input: any) => {
      transferred = input; return { ok: true };
    });
    assert.equal(receipt.result.ok, true, "T082-RELAY-REAL-REPORT");
    assert.deepEqual(transferred.report, payload.report);
    assert.deepEqual(transferred.review_requirements, payload.review_requirements);
    checks.push("T082-RELAY-REAL-REPORT");
  } finally { store.close(); }
} catch (error) { failure = String(error); }
writeFileSync(output, JSON.stringify({ status: failure ? "INCOMPLETE" : "PASS", source, payload: payloadPath,
  checks, failure, real_codex_turns: 0 }, null, 2) + "\n", { flag: "wx" });
process.stdout.write(JSON.stringify({ checks, failure }) + "\n");
process.exitCode = failure ? 1 : 0;
