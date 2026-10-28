import { readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import { QualityProtocolError, reviewRequest } from "./gates/qualityProtocol.ts";
import { serveTools } from "./terminalMcp.ts";

// T-203: a reviewer hands in its verdict, findings and report through a tool; the identity fields and review requirements
// come from the template the gate writes for this review. The tool checks the result with the gate's own validation at
// once, so the reviewer can fix it within the turn, and writes it to its request directory. The daemon reads that file at
// the reviewer's Stop and validates it again (daemon.ts): nothing here is a weaker gate.
export const REVIEW_TEMPLATE_FILE = "review-template.json";
export const REVIEW_RESULT_FILE = "review-result.json";
const FIELDS = ["verdict", "findings", "report"];

// The reviewer session's MCP server, as its launch names it; the gate rebuilds it to check the launch (reviewLaunch).
export function reviewMcpServer(requestDirectory: string) {
  return { command: process.execPath, args: [fileURLToPath(import.meta.url), "mcp", requestDirectory], env: { ELECTRON_RUN_AS_NODE: "1" } };
}
export const claudeReviewMcp = (requestDirectory: string) =>
  JSON.stringify({ mcpServers: { enchanted: { type: "stdio", ...reviewMcpServer(requestDirectory) } } });
// Codex gives an MCP server only the variables named here; its tool needs no approval prompt (as the terminal shim, T-194).
export function codexReviewMcp(requestDirectory: string) {
  const server = reviewMcpServer(requestDirectory), key = "mcp_servers.enchanted";
  return [`${key}.command=${JSON.stringify(server.command)}`, `${key}.args=${JSON.stringify(server.args)}`,
    `${key}.env={ELECTRON_RUN_AS_NODE="1"}`, `${key}.default_tools_approval_mode="approve"`].flatMap(value => ["-c", value]);
}

export function writeReviewTemplate(directory: string, template: Record<string, unknown>) {
  writeFileSync(join(directory, REVIEW_TEMPLATE_FILE), JSON.stringify(template) + "\n", { flag: "wx", mode: 0o600 });
}

export function readReviewResult(directory: string): string | null {
  try { return readFileSync(join(directory, REVIEW_RESULT_FILE), "utf8"); }
  catch (error) { if ((error as NodeJS.ErrnoException).code === "ENOENT") return null; throw error; }
}

// How to fix each field reviewRequest names; a template field is the gate's, never the reviewer's to fix.
const hints: Record<string, string> = {
  review_fields: "只交 verdict、findings、report 三项，别的字段由工具补齐。",
  verdict: "verdict 只能是“可合并”或“需修复”。",
  findings: "可合并时 findings 是空数组；需修复时至少写一项。",
  finding: "findings 的每一项只含 location、failure_scenario、suggestion 三个字段。",
  location: "location 只含 path 与 line 两个字段。",
  "location.path": "location.path 写仓库相对路径：不以 / 开头，不含反斜杠、. 或 ..。",
  "location.line": "location.line 写正整数行号。",
  "finding.text": "failure_scenario 与 suggestion 都写非空文字。",
  report: "report 是非空对象，每节一个键。",
  "report.section": "report 必须有“完成条件与变异检查”这一节。",
};

export function saveReviewResult(directory: string, fields: unknown) {
  let template: Record<string, unknown>;
  try { template = JSON.parse(readFileSync(join(directory, REVIEW_TEMPLATE_FILE), "utf8")); }
  catch (error) { return { ok: false, error: "review_template_unreadable", details: { reason: String(error) },
    explanation: { reason: "门禁为这次审查写的模板读不到。", next: "结束本回合，由主控处理。" } }; }
  const given = fields as Record<string, unknown>;
  try {
    if (!given || typeof given !== "object" || Array.isArray(given) || Object.keys(given).some(key => !FIELDS.includes(key)))
      throw new QualityProtocolError("review_fields");
    const envelope = { ...template, verdict: given.verdict, findings: given.findings, report: given.report };
    reviewRequest(JSON.stringify(envelope));
    const temporary = join(directory, `${REVIEW_RESULT_FILE}.${randomUUID()}.tmp`);
    writeFileSync(temporary, JSON.stringify(envelope) + "\n", { flag: "wx", mode: 0o600 });
    renameSync(temporary, join(directory, REVIEW_RESULT_FILE));
  } catch (error) {
    if (!(error instanceof QualityProtocolError)) throw error;
    const hint = hints[error.field];
    return { ok: false, error: "invalid_review_result", details: { field: error.field },
      explanation: hint ? { reason: `字段 ${error.field} 不符合要求。`, next: hint + "改好后再调用一次。" }
        : { reason: `门禁模板里的 ${error.field} 不符合协议。`, next: "结束本回合，由主控处理。" } };
  }
  return { ok: true, saved: true, next: "已收下。结束本回合后门禁才处理；结束前再交一次会覆盖这一次。" };
}

const finding = { type: "object", additionalProperties: false, required: ["location", "failure_scenario", "suggestion"],
  properties: {
    location: { type: "object", additionalProperties: false, required: ["path", "line"], properties: {
      path: { type: "string", description: "仓库相对路径" }, line: { type: "integer", description: "行号，正整数" } } },
    failure_scenario: { type: "string", description: "具体失败场景" }, suggestion: { type: "string", description: "修复建议" } } };
const tool = { name: "review_submit", description: "交这次审查的结论：verdict、findings、report。身份字段由工具补齐。不合格式会当场说明哪一项要改；结束本回合前以最后一次成功提交为准，回合结束时门禁才处理。",
  inputSchema: { type: "object", additionalProperties: false, required: FIELDS, properties: {
    verdict: { type: "string", enum: ["可合并", "需修复"], description: "结论" },
    findings: { type: "array", items: finding, description: "可合并时为空；需修复时至少一项" },
    report: { type: "object", description: "审查报告，每节一个键、值为文字；必须有“完成条件与变异检查”一节，逐项写改了什么、运行的命令、结果" } } } };

// `reviewResult.ts mcp <request dir>`: the reviewer session's MCP server. `reviewResult.ts submit <request dir> <file>`: the
// same for agy, whose interactive sessions do not give the model MCP tools (T-194 facts); the file holds the three fields.
async function main([command, directory, file]: string[]) {
  if (command === "mcp" && directory && !file) {
    await serveTools([tool], async (name, args) => name === tool.name ? saveReviewResult(directory, args)
      : { ok: false, error: "unknown_tool", details: { tool: name } });
    return 0;
  }
  if (command === "submit" && directory && file) {
    let fields: unknown;
    try { fields = JSON.parse(readFileSync(file, "utf8")); }
    catch (error) {
      process.stdout.write(JSON.stringify({ ok: false, error: "review_file_unreadable", details: { reason: String(error) },
        explanation: { reason: "这个文件读不到或不是 JSON。", next: "写成只含 verdict、findings、report 的 JSON 对象再运行一次。" } }, null, 2) + "\n");
      return 1;
    }
    const result = saveReviewResult(directory, fields);
    process.stdout.write(JSON.stringify(result, null, 2) + "\n");
    return result.ok ? 0 : 1;
  }
  process.stderr.write("usage: reviewResult.ts mcp <request dir> | submit <request dir> <file>\n");
  return 2;
}

if (import.meta.main) process.exitCode = await main(process.argv.slice(2));
