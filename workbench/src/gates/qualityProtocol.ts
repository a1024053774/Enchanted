import type { A2AReviewFinding } from "../contracts/a2aGates.ts";
import { taskIdPattern } from "../contracts/a2aMembership.ts";

// Validation of explicit wire data only. No inference from prose or tool output.
export class QualityProtocolError extends Error {
  readonly field: string;
  constructor(field: string) { super(field); this.field = field; }
}
function requireValue(value: unknown, field: string): asserts value {
  if (!value) throw new QualityProtocolError(field);
}
function exact(value: any, keys: string[], field: string) {
  requireValue(value && typeof value === "object" && !Array.isArray(value) &&
    Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key)), field);
}
const nonempty = (value: unknown) => typeof value === "string" && value.trim().length > 0 && !value.includes("\0");

export function reviewVerdict(verdict: unknown, findings: unknown): { verdict: "可合并" | "需修复"; findings: A2AReviewFinding[] } {
  requireValue(verdict === "可合并" || verdict === "需修复", "verdict");
  requireValue(Array.isArray(findings) && (verdict === "可合并" ? findings.length === 0 : findings.length > 0), "findings");
  for (const finding of findings) {
    exact(finding, ["location", "failure_scenario", "suggestion"], "finding");
    exact(finding.location, ["path", "line"], "location");
    requireValue(nonempty(finding.location.path) && !finding.location.path.startsWith("/") &&
      !finding.location.path.includes("\\") && finding.location.path.split("/").every((part: string) => part && part !== "." && part !== ".."), "location.path");
    requireValue(Number.isSafeInteger(finding.location.line) && finding.location.line > 0, "location.line");
    requireValue(nonempty(finding.failure_scenario) && nonempty(finding.suggestion), "finding.text");
  }
  return { verdict, findings: structuredClone(findings) };
}

// The report is model-authored evidence. Validate its container, not the
// correctness of the judgement or whether a mutation should have failed.
export function reviewEvidence(requirements: unknown, report: unknown) {
  const value = requirements as any;
  exact(value, ["completion_conditions_sufficiency", "mutation_checks"], "review_requirements");
  exact(value.mutation_checks, ["min", "max", "workspace", "report_section"], "mutation_checks");
  requireValue(value.completion_conditions_sufficiency === true && value.mutation_checks.min === 2 &&
    value.mutation_checks.max === 5 && nonempty(value.mutation_checks.workspace) &&
    value.mutation_checks.report_section === "完成条件与变异检查", "review_requirements");
  requireValue(report && typeof report === "object" && !Array.isArray(report) && Object.keys(report).length > 0, "report");
  requireValue(Object.hasOwn(report, "完成条件与变异检查"), "report.section");
  return { review_requirements: structuredClone(value), report: structuredClone(report) as Record<string, unknown> };
}

export function reviewRequest(raw: unknown): Record<string, any> {
  requireValue(typeof raw === "string", "last_assistant_message");
  let value: any;
  try { value = JSON.parse(raw); }
  catch (error) { if (error instanceof SyntaxError) throw new QualityProtocolError("review_json"); throw error; }
  exact(value, ["schema", "request_id", "command", "task", "attempt", "session", "fence", "spec_rev",
    "review_id", "candidate_commit", "verdict", "findings", "review_requirements", "report"], "review_request");
  requireValue(value.schema === 1 && value.command === "review_submit", "review_command");
  requireValue(typeof value.task === "string" && taskIdPattern.test(value.task), "task");
  for (const key of ["attempt", "session", "review_id", "request_id"]) {
    requireValue(typeof value[key] === "string" && /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(value[key]), key);
  }
  requireValue(value.request_id === "review-" + value.review_id, "request_id");
  requireValue(Number.isSafeInteger(value.fence) && value.fence > 0 && Number.isSafeInteger(value.spec_rev) && value.spec_rev > 0, "review_version");
  requireValue(typeof value.candidate_commit === "string" && /^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(value.candidate_commit), "candidate_commit");
  reviewVerdict(value.verdict, value.findings);
  reviewEvidence(value.review_requirements, value.report);
  return value;
}

export function executorScore(value: unknown, command: "integrate" | "abandon" = "integrate"): Record<string, unknown> {
  if (command === "abandon" && (value as any)?.result === "放弃") {
    exact(value, ["result", "reason"], "score");
    requireValue(nonempty((value as any).reason), "score.reason");
    return { result: "放弃", reason: (value as any).reason };
  }
  exact(value, ["result", "boundary_discipline", "boundary_reason", "engineering_taste", "engineering_reason", "notes"], "score");
  const data = value as Record<string, unknown>;
  requireValue(data.result === (command === "integrate" ? "通过" : "升级"), "score.result");
  for (const key of ["boundary_discipline", "engineering_taste"]) {
    requireValue(Number.isInteger(data[key]) && Number(data[key]) >= 0 && Number(data[key]) <= 3, "score." + key);
  }
  requireValue(nonempty(data.boundary_reason) && nonempty(data.engineering_reason) && typeof data.notes === "string", "score.text");
  // Stable field order makes exact replay comparisons independent of JSON key order.
  return { result: data.result, boundary_discipline: data.boundary_discipline, boundary_reason: data.boundary_reason,
    engineering_taste: data.engineering_taste, engineering_reason: data.engineering_reason, notes: data.notes };
}

export function scoreRecords(raw: string): Record<string, any>[] {
  requireValue(raw.length === 0 || raw.endsWith("\n"), "scores.incomplete_tail");
  const rows: Record<string, any>[] = [], indexed = new Map<string, Record<string, any>>(), attempts = new Set<string>();
  const v1Checks = ["identity_version", "path_boundary", "completion", "red_state", "rule_checks", "independent_review", "commit_trailers"];
  const v2Checks = [...v1Checks, "oracle"];
  for (const [index, line] of (raw ? raw.slice(0, -1).split("\n") : []).entries()) {
    const field = `scores.line_${index + 1}`;
    let row: any;
    try { row = JSON.parse(line); }
    catch (error) { if (error instanceof SyntaxError) throw new QualityProtocolError(field + ".json"); throw error; }
    requireValue(row && typeof row === "object" && !Array.isArray(row), field);
    for (const key of ["score_id", "created_at", "launch_id", "project", "task", "attempt", "cli", "model", "effort"]) {
      requireValue(nonempty(row[key]), field + "." + key);
    }
    requireValue((row.schema === 1 || row.schema === 2) && ["executor", "user"].includes(row.source) && !indexed.has(row.score_id), field + ".identity");
    const checks = row.schema === 1 ? v1Checks : v2Checks;
    if (row.source === "user") exact(row.data, ["boundary_discipline", "boundary_reason", "engineering_taste", "engineering_reason", "notes"], field + ".user_data");
    try {
      // A run integrated after its terminal controller was gone records no score, and why (T-124).
      // Only the gate writes this form; executorScore still refuses it in a score file.
      if (row.source === "executor" && row.data?.result === "未评分") {
        exact(row.data, ["result", "reason"], "score");
        requireValue(["主控身份已结束", "主控额度用完"].includes(row.data.reason), "score.reason");
      } else executorScore(row.source === "user" ? { result: "通过", ...row.data } : row.data,
        row.source === "user" || row.data?.result === "通过" ? "integrate" : "abandon");
    } catch (error) {
      if (error instanceof QualityProtocolError) throw new QualityProtocolError(field + "." + error.field);
      throw error;
    }
    if (row.source === "executor") {
      const identity = JSON.stringify([row.project, row.task, row.attempt]);
      requireValue(!attempts.has(identity), field + ".duplicate_attempt"); attempts.add(identity);
      if (row.data.result === "放弃") requireValue(!Object.hasOwn(row, "facts"), field + ".abandon_facts");
      else {
        exact(row.facts, ["task_type", "complexity", "delivery_rounds", "elapsed_seconds", "human_interventions", "rejections"], field + ".facts");
        requireValue(["后端逻辑", "前端界面", "缺陷修复", "测试", "重构", "构建与基础设施", "文档", "调研"].includes(row.facts.task_type) &&
          ["S", "M", "L"].includes(row.facts.complexity), field + ".classification");
        for (const key of ["delivery_rounds", "elapsed_seconds", "human_interventions"]) {
          requireValue(Number.isSafeInteger(row.facts[key]) && row.facts[key] >= 0, field + ".facts." + key);
        }
        exact(row.facts.rejections, checks, field + ".rejections");
        requireValue(checks.every((key) => Number.isSafeInteger(row.facts.rejections[key]) && row.facts.rejections[key] >= 0), field + ".rejections");
      }
    } else {
      const original = indexed.get(row.score_of);
      requireValue(original?.source === "executor" && ["launch_id", "project", "task", "attempt", "cli", "model", "effort"]
        .every((key) => original[key] === row[key]), field + ".score_of");
    }
    indexed.set(row.score_id, row); rows.push(row);
  }
  return rows;
}
