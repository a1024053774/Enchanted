import { createInterface } from "node:readline";

// T-194: the same controller commands as `a2a call`, as MCP tools with structured arguments, for the CLIs that take a
// per-session MCP server (T-194 facts: all four). Each tool is one daemon request under the terminal's own identity:
// the daemon and the gate decide everything, this file only names the arguments. A CLI without it uses `a2a`.
type Field = { type: "string" | "number" | "boolean"; description: string; enum?: string[] }
  | { type: "array"; items: { type: "string" }; description: string };
type Tool = { command: string; description: string; fields?: Record<string, Field>; required?: string[] };

const task: Field = { type: "string", description: "任务号；别的已打开项目的任务写完整 id <项目>+<任务>" };
const project: Field = { type: "string", description: "工作台里已打开的项目 id" };
const launch = {
  runtimeMode: { type: "string", enum: ["workspace-write"], description: "worker 的运行方式" },
  model: { type: "string", description: "worker 的模型" },
  effort: { type: "string", description: "worker 的思考强度" },
  fast: { type: "boolean", description: "Codex 的 Fast 模式；不传就不开" },
  overlap_reason: { type: "string", description: "与别的任务路径重叠（path_overlap）而你判断可以并行时，写明理由" },
  extra_directories: { type: "array", items: { type: "string" }, description: "本次让 worker 另写的项目外绝对目录；不经审查与集成，未指定就不给" },
} satisfies Record<string, Field>;

// The order and wording follow `a2a help` and the a2a skill; their rules (checking the card against the user's words,
// when to wait or stop) hold for these tools as well.
const tools: Record<string, Tool> = {
  whoami: { command: "terminal_whoami", description: "这个终端的项目与身份。" },
  release: { command: "role_release", description: "放弃当前主控身份；已派出的工作继续做完。" },
  terminal_open: { command: "terminal_open", description: "在本项目开普通终端，返回 launch.id；目录须在项目主目录或额外目录内。",
    fields: { cwd: { type: "string", description: "绝对目录" } }, required: ["cwd"] },
  card_template: { command: "card_template", description: "取任务卡模板。填好后存成项目目录以外的 JSON 文件，再 card_save。",
    fields: { task, repo: { type: "string", description: "该项目在工作台里打开的目录" } }, required: ["task", "repo"] },
  card_save: { command: "card_save", description: "保存任务卡的新版本；只存版本，已注册任务要 revise 才采用。",
    fields: { task, project, card: { type: "string", description: "任务卡 JSON 文件的绝对路径" },
      expected_version: { type: "number", description: "当前卡版本，新任务为 0" } }, required: ["task", "card", "expected_version"] },
  create: { command: "create", description: "用已保存的任务卡在项目里注册任务；回执 work_branch 写明工作分支。",
    fields: { task, project, repo: { type: "string", description: "该项目在工作台里打开的目录" },
      card_version: { type: "number", description: "card_save 返回的版本" },
      branch: { type: "string", description: "用户指定的工作分支 refs/heads/<分支>；用户没说就不传" } },
    required: ["task", "project", "repo", "card_version"] },
  dispatch: { command: "dispatch", description: "派 worker：后台新开窗格启动它。之后用 status 看进度，不往 worker 窗格里打字。",
    fields: { task, ...launch }, required: ["task", "runtimeMode", "model", "effort"] },
  run: { command: "run", description: "一条走完派发、验收、审查；一直等到任务结束才返回。CLI 的工具超时先到时调用被截断，run 仍在后台继续，用 status 查。",
    fields: { task, ...launch, wait_seconds: { type: "number", description: "最长等待秒数" } },
    required: ["task", "runtimeMode", "wait_seconds", "model", "effort"] },
  status: { command: "status", description: "任务的门禁状态与当前 attempt。", fields: { task }, required: ["task"] },
  verify: { command: "verify", description: "state 为 submitted 后验收：跑机械检查，再新开只读审查会话。", fields: { task }, required: ["task"] },
  out_of_card: { command: "out_of_card", description: "判断交付里任务卡外的改动（verification.out_of_card）：accept 留下，reject 发回 worker 改。",
    fields: { task, decision: { type: "string", enum: ["accept", "reject"], description: "留下或打回" },
      reason: { type: "string", description: "为什么" } }, required: ["task", "decision", "reason"] },
  integrate: { command: "integrate", description: "state 为 verified 后集成到工作分支；打分写成 JSON 文件（result、boundary_discipline、boundary_reason、engineering_taste、engineering_reason、notes）。",
    fields: { task, score_file: { type: "string", description: "打分 JSON 文件的绝对路径" } }, required: ["task", "score_file"] },
  revise: { command: "revise", description: "已注册任务采用新卡版本；旧 attempt 与候选失效，旧会话仍须 reclaim。",
    fields: { task, spec_rev: { type: "number", description: "大于当前的规格版本" }, card_version: { type: "number", description: "要采用的卡版本" } },
    required: ["task", "spec_rev", "card_version"] },
  reclaim: { command: "reclaim", description: "回收一个 attempt；门禁核对身份、空闲、停止和归档，成功后才释放路径。",
    fields: { task, attempt: { type: "string", description: "要回收的 attempt_id" } }, required: ["task", "attempt"] },
  close: { command: "close", description: "关闭不再做的任务（待认领、没有进行中 attempt）。",
    fields: { task, reason: { type: "string", description: "为什么不做了" } }, required: ["task", "reason"] },
  task_history: { command: "task_history", description: "一个任务在门禁里的全程。", fields: { task }, required: ["task"] },
  issues: { command: "issues", description: "worker 上报的问题。", fields: { task }, required: ["task"] },
  answer_issue: { command: "answer_issue", description: "回答 worker 上报的问题，记为主控的回答；涉及范围、验收、权限、不可逆操作的先问用户。",
    fields: { task, issue: { type: "string", description: "问题 id" }, answer: { type: "string", description: "回答" } },
    required: ["task", "issue", "answer"] },
  attach: { command: "attach", description: "挂一个只读观察会话（monitor）。",
    fields: { task, role: { type: "string", enum: ["monitor"], description: "monitor" },
      instructions: { type: "string", description: "说明文件的绝对路径" },
      cli: { type: "string", enum: ["Codex", "Claude Code"], description: "不传用默认" },
      model: { type: "string", description: "不传用默认" }, effort: { type: "string", description: "不传用默认" } },
    required: ["task", "role", "instructions"] },
  inbox_ready: { command: "inbox_ready", description: "项目收件箱里就绪的条目。", fields: { project }, required: ["project"] },
};

const requestRole = { description: "申请成为执行主控（executor）或构思主控（ideation）。只在用户本人要求时申请；调用会等用户在 Enchanted 界面批准或拒绝，最多 10 分钟。被拒绝或超时就停下告诉用户。",
  inputSchema: { type: "object", properties: { role: { type: "string", enum: ["executor", "ideation"], description: "executor 或 ideation" } },
    required: ["role"], additionalProperties: false } };

type Send = (input: Record<string, unknown>, signal: AbortSignal) => Promise<any>;
// role: runs the whole role request (wait, then confirm); meta is the call's MCP _meta, where some CLIs name their session.
type RequestRole = (role: string, meta: Record<string, any> | undefined, signal: AbortSignal) => Promise<any>;

export function serveMcp(send: Send, role: RequestRole): Promise<void> {
  return serveTools([{ name: "request_role", ...requestRole }, ...Object.entries(tools).map(([name, tool]) => ({
    name, description: tool.description, inputSchema: { type: "object", properties: tool.fields ?? {}, required: tool.required ?? [], additionalProperties: false } }))],
  async (name, args, meta, signal) => {
    if (name === "request_role") return role(String(args.role), meta, signal);
    const tool = tools[name];
    if (!tool) return { ok: false, error: "unknown_tool", details: { tool: name } };
    return send({ ...args, command: tool.command }, signal);
  });
}

export type McpTool = { name: string; description: string; inputSchema: Record<string, unknown> };
type Call = (name: string, args: Record<string, unknown>, meta: Record<string, any> | undefined, signal: AbortSignal) => Promise<any>;
// An MCP stdio server for these tools (T-194; T-203 adds the reviewer's). Each call's answer is its JSON text; ok:false is an
// error result. Resolves when the session ends: the client closed the input or stopped reading the output.
export function serveTools(list: McpTool[], call: Call): Promise<void> {
  let ended!: () => void;
  const done = new Promise<void>(resolve => { ended = resolve; });
  // Once the session is over nothing more is written: a call stopped by the close gets no answer (T-194 review 2, F2).
  let open = true;
  const write = (message: unknown) => { if (open) process.stdout.write(JSON.stringify(message) + "\n"); };
  const calls = new Map<unknown, AbortController>();
  const input = createInterface({ input: process.stdin });
  // The client closing the server's input ends the session (MCP stdio shutdown): every call still in flight stops as if
  // cancelled, so a pending role request is withdrawn and never confirmed (T-194 review F1).
  const end = () => { open = false; for (const controller of calls.values()) controller.abort(); ended(); };
  input.on("close", end);
  // The client no longer reading the server's output ends the session the same way; any other output error is a fault.
  process.stdout.on("error", error => {
    if ((error as NodeJS.ErrnoException).code !== "EPIPE") throw error;
    end();
    input.close();
  });
  input.on("line", async line => {
    let message: any;
    try { message = JSON.parse(line); } catch { return; }
    const { id, method, params } = message ?? {};
    if (method === "notifications/cancelled") return calls.get(params?.requestId)?.abort();
    if (id === undefined) return;
    if (method === "initialize")
      return write({ jsonrpc: "2.0", id, result: { protocolVersion: params?.protocolVersion ?? "2025-06-18",
        capabilities: { tools: {} }, serverInfo: { name: "enchanted", version: "1" } } });
    if (method === "ping") return write({ jsonrpc: "2.0", id, result: {} });
    if (method === "tools/list")
      return write({ jsonrpc: "2.0", id, result: { tools: list } });
    if (method !== "tools/call") return write({ jsonrpc: "2.0", id, error: { code: -32601, message: `method not found: ${method}` } });
    const controller = new AbortController();
    calls.set(id, controller);
    try {
      const result = await call(String(params?.name), params?.arguments ?? {}, params?._meta, controller.signal);
      write({ jsonrpc: "2.0", id, result: { content: [{ type: "text", text: JSON.stringify(result, null, 2) }], isError: !result.ok } });
    } catch (error) {
      // The daemon's answer is unknown (it went away, or the CLI cancelled the call): never replayed here.
      write({ jsonrpc: "2.0", id, result: { content: [{ type: "text", text: JSON.stringify({ ok: false, error: "outcome_unknown",
        details: { reason: String((error as Error).message ?? error) } }) }], isError: true } });
    } finally { calls.delete(id); }
  });
  return done;
}
