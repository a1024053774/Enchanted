import { request } from "./transport.ts";

// The `a2a` command inside an Enchanted project terminal (T-121). Its identity is
// the terminal itself; controller commands need a role the user approved in the UI.
const usage = `a2a：Enchanted 工作台的编排命令（在 Enchanted 的项目终端里运行）

  a2a whoami                  这个终端的项目与身份
  a2a request executor|ideation 申请成为执行主控或构思主控；等用户在界面批准，最多 10 分钟
  a2a release                 放弃当前身份
  a2a call '<JSON>'           以已批准的身份调用门禁命令，例如
                              a2a call '{"command":"inbox_list"}'
  a2a help                    显示这段说明

只有用户本人要求时才申请身份；被拒绝或超时就停下告诉用户。`;

const state = process.env.A2A_STATE, launch = process.env.A2A_TERMINAL, token = process.env.A2A_TERMINAL_TOKEN;
const print = (value: unknown) => process.stdout.write(JSON.stringify(value, null, 2) + "\n");

async function main(argv: string[]) {
  const [command, ...rest] = argv;
  if (!command || command === "help" || command === "--help" || command === "-h") {
    process.stdout.write(usage + "\n");
    return 0;
  }
  if (!state || !launch || !token) {
    process.stderr.write("a2a：这个终端不是 Enchanted 打开的项目终端，没有终端身份。\n");
    return 2;
  }
  const identity = { kind: "terminal", launch, token };
  const send = (input: Record<string, unknown>) => request(state, input, identity);
  const finish = (result: any) => { print(result); return result.ok ? 0 : 1; };
  if (command === "whoami" && !rest.length) return finish(await send({ command: "terminal_whoami" }));
  if (command === "release" && !rest.length) return finish(await send({ command: "role_release" }));
  if (command === "request" && rest.length === 1) {
    const cli = process.env.CLAUDECODE ? "claude" : process.env.CODEX_THREAD_ID ? "codex" : undefined;
    const requested = await send({ command: "role_request", role: rest[0], cli });
    if (!requested.ok) return finish(requested);
    process.stderr.write(`已提交申请（${rest[0] === "executor" ? "执行主控" : "构思主控"}），等用户在 Enchanted 里批准…\n`);
    const deadline = Date.now() + 10 * 60_000;
    while (Date.now() < deadline) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      const current = await send({ command: "terminal_whoami" });
      if (!current.ok) return finish(current);
      const roleRequest = current.role_requests.find((row: any) => row.id === requested.role_request.id);
      if (roleRequest?.state === "approved") return finish({ ok: true, role_request: roleRequest });
      if (roleRequest && roleRequest.state !== "pending") return finish({ ok: false, error: "request_" + roleRequest.state, role_request: roleRequest });
    }
    return finish({ ok: false, error: "request_wait_timeout", role_request: requested.role_request });
  }
  if (command === "call" && rest.length === 1) {
    let input: unknown;
    try { input = JSON.parse(rest[0]); } catch { input = undefined; }
    if (!input || typeof input !== "object" || Array.isArray(input) || typeof (input as any).command !== "string") {
      process.stderr.write("a2a call 需要一个带 command 字段的 JSON 对象。\n");
      return 2;
    }
    return finish(await send(input as Record<string, unknown>));
  }
  process.stderr.write(usage + "\n");
  return 2;
}

if (import.meta.main) process.exitCode = await main(process.argv.slice(2));
