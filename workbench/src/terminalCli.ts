import { requestAt } from "./transport.ts";

// The `a2a` command inside an Enchanted project terminal (T-121). Its identity is
// the terminal itself; controller commands need a role the user approved in the UI.
const usage = `a2a：Enchanted 工作台的编排命令（在 Enchanted 的项目终端里运行）

  a2a whoami                  这个终端的项目与身份
  a2a request executor|ideation 申请成为执行主控或构思主控；等用户在界面批准，最多 10 分钟
  a2a release                 放弃当前身份；已派出的工作继续做完
  a2a call '<JSON>'           以已批准的身份调用本项目的门禁命令：本项目任务上的任务命令，
                              新任务的 card_* 与 create（project 为本项目、repo 为本项目目录），
                              以及本项目的 inbox_ready，例如
                              a2a call '{"command":"inbox_ready","project":"<项目>"}'
                              派 worker：card_template → card_save → create → dispatch
                              （runtimeMode 为 workspace-write，带 model 与 effort）→ status
                              → submitted 后 verify → verified 后带 score_file 的 integrate；
                              或者一条 run 自动走完（身份结束或额度用完时它自己集成，记未评分）。
                              回答 worker 上报的问题：issues / answer_issue，记为主控的回答。
                              attach（role 为 monitor）挂一个只读观察会话。
  a2a help                    显示这段说明

只有用户本人要求时才申请身份；被拒绝或超时就停下告诉用户。申请命令被中断、被杀或超时，后台都会撤回申请。`;

// The terminal socket accepts only this identity (T-126); the daemon's data directory is not in the environment.
const socket = process.env.A2A_TERMINAL_SOCKET, launch = process.env.A2A_TERMINAL, token = process.env.A2A_TERMINAL_TOKEN;
const print = (value: unknown) => process.stdout.write(JSON.stringify(value, null, 2) + "\n");

async function main(argv: string[]) {
  const [command, ...rest] = argv;
  if (!command || command === "help" || command === "--help" || command === "-h") {
    process.stdout.write(usage + "\n");
    return 0;
  }
  if (!socket || !launch || !token) {
    process.stderr.write("a2a：这个终端不是 Enchanted 打开的项目终端，没有终端身份。\n");
    return 2;
  }
  const identity = { kind: "terminal", launch, token };
  const send = (input: Record<string, unknown>) => requestAt(socket, input, identity);
  const finish = (result: any) => { print(result); return result.ok ? 0 : 1; };
  if (command === "whoami" && !rest.length) return finish(await send({ command: "terminal_whoami" }));
  if (command === "release" && !rest.length) return finish(await send({ command: "role_release" }));
  if (command === "request" && rest.length === 1) {
    const cli = process.env.CLAUDECODE ? "claude" : process.env.CODEX_THREAD_ID ? "codex" : undefined;
    // The CLI's own session and home, from the environment it gives its commands (T-124 probe 01): the
    // daemon reads only that session's usage-limit records, to tell the user when this controller runs out.
    const native = cli === "claude" ? { native_session: process.env.CLAUDE_CODE_SESSION_ID,
      native_home: process.env.CLAUDE_CONFIG_DIR || (process.env.HOME && process.env.HOME + "/.claude") } :
      cli === "codex" ? { native_session: process.env.CODEX_THREAD_ID,
        native_home: process.env.CODEX_HOME || (process.env.HOME && process.env.HOME + "/.codex") } : {};
    process.stderr.write(`申请成为${rest[0] === "executor" ? "执行主控" : rest[0] === "ideation" ? "构思主控" : rest[0]}，等用户在 Enchanted 里批准…\n`);
    // The daemon holds this call until the user decides. If this process stops
    // waiting for any reason, the daemon sees the connection close and withdraws it.
    const answered = await send({ command: "role_request", role: rest[0], cli, ...native, wait_seconds: 600 });
    if (!answered.ok) return finish(answered);
    // The user granted the role; confirming it here is what makes it take effect.
    return finish(await send({ command: "role_request_confirm", role_request: answered.role_request.id }));
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
