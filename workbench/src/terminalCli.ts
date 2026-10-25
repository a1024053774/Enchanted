import { requestAt } from "./transport.ts";

// The `a2a` command inside an Enchanted project terminal (T-121). Its identity is
// the terminal itself; controller commands need a role the user approved in the UI.
const usage = `a2a：Enchanted 工作台的编排命令（在 Enchanted 的项目终端里运行）

  a2a whoami                  这个终端的项目与身份
  a2a request executor|ideation 申请成为执行主控或构思主控；等用户在界面批准，最多 10 分钟
  a2a release                 放弃当前身份；已派出的工作继续做完
  a2a call terminal_open --cwd <绝对目录>
                              在本项目开普通终端，返回 launch.id；目录须在项目主目录或额外目录内
  a2a call '<JSON>'           以已批准的身份调用本项目的门禁命令：本项目任务上的任务命令，
                              新任务的 card_* 与 create（project 为本项目、repo 为本项目目录），
                              以及本项目的 inbox_ready，例如
                              a2a call '{"command":"inbox_ready","project":"<项目>"}'
                              派发前对照用户原话逐项核对任务卡并列出结果，含先后顺序、等待条件与首版演练要求；漏项先改卡。
                              单独写验收脚本也须自检：每条判据对应用户明确要求，期望从原始数据推导，先独立确定样本预期，再写或运行检查器。
                              优先实际运行全文断言对照：从原始数据构造不带任何开头说明、只含必需内容的最小正确正文并确认通过；复制后数据不变，只在开头否定全文断言，预期转拒绝。
                              没有开头说明不能判为缺项，不要求固定确认语、逐项明细或自行限定的字词；不能把正常标签或自由文字一律判错。拦反例后须原样重跑全部正例，误拒先纠正自加条件。
                              检查器须核对开头对全文的限定；不能以改错数字代替此反例，也不能只核对正文数字关系。仍误收就记录失败、修正复验或明确交独立审查。
                              正例含无额外明细的最小正确内容与另一种允许排版；反例含错数字、缺项、关键词仍在但标题或上下文含义相反的内容。
                              核对全文断言，区分业务动作相反与正文真实性、有效性被否定；有限禁词表须用未参与规则编写的改述复验，不能只测必命中的词。
                              实际运行并保留每项输入、要求依据、预期和实际退出码；不擅加逐项列名或排版条件，不只查存在或字串。
                              发现不符先修检查器，不改预期或给正例补无关内容凑通过；自检完成后才交付脚本或用于任务卡。
                              脚本只核对机械事实，无法机械判定的含义交独立审查。暂时未完成须有推进事实与等待条件；明确拒绝报告原始错误和 task/attempt；
                              结果未知保留原请求，不自动重发写入。没有新事实就停止轮询，报告最后确定事实、具体停点与缺少的事实或决定。
                              派 worker：card_template → card_save → create → dispatch
                              （runtimeMode 为 workspace-write，带 model 与 effort）→ status
                              → submitted 后 verify → verified 后带 score_file 的 integrate；
                              或者一条 run 自动走完（身份结束或额度用完时它自己集成，记未评分）。
                              修订已注册任务：先 status 保存旧 current_attempt.attempt_id，
                              核对旧 worker 已提交、空闲且没有待发送输入；以下示例从 v1 改为 v2：
                              a2a call '{"command":"card_save","task":"<任务>","card":"<v2 JSON 路径>","expected_version":1}'
                              a2a call '{"command":"revise","task":"<任务>","spec_rev":2,"card_version":2}'
                              a2a call '{"command":"reclaim","task":"<任务>","attempt":"<保存的旧 attempt_id>"}'
                              a2a call '{"command":"dispatch","task":"<任务>","runtimeMode":"workspace-write","model":"<模型>","effort":"<强度>"}'
                              spec_rev 须递增；card_save 只存版本，revise 才采用新卡并撤销旧交付。
                              旧会话回收成功才释放路径；未回收仍会 path_overlap，不用交叠参数绕过。
                              worker_working 时先核对旧回合与输入队列，停止或归档未确认时保留现场并上报。
                              回收后脏工作区仍保留、上报；保留证据不继续占用路径。
                              回答 worker 上报的问题：issues / answer_issue，记为主控的回答。
                              attach（role 为 monitor）挂一个只读观察会话。
  a2a help                    显示这段说明

只有用户本人要求时才申请身份；被拒绝或超时就停下告诉用户。申请命令被中断、被杀或超时，后台都会撤回申请。`;

// T-181 (L08): a model that never picks the a2a skill still has to know the command exists. Claude Code adds a
// SessionStart hook's stdout to the session's context; this is what it reads.
const orientation = `你运行在 Enchanted 工作台的项目终端里。\`a2a\` 命令已经在 PATH 上，\`a2a help\` 列出全部命令；不用在文件系统里找它。
- 用户让你担任主控（执行主控或构思主控）时，直接用 Bash 运行 \`a2a request executor\` 或 \`a2a request ideation\`（Bash 超时设 600000 毫秒），由用户在 Enchanted 界面里批准或拒绝。不要先用问答框问用户是否批准，那不能代替这一步。
- 担任主控、派 worker 之前，先读 enchanted-a2a 插件的 a2a skill，按它的步骤做。
用户没有要你做这些时，照常工作。`;

// The terminal socket accepts only this identity (T-126); the daemon's data directory is not in the environment.
const socket = process.env.A2A_TERMINAL_SOCKET, launch = process.env.A2A_TERMINAL, token = process.env.A2A_TERMINAL_TOKEN;
const print = (value: unknown) => process.stdout.write(JSON.stringify(value, null, 2) + "\n");

async function main(argv: string[]) {
  const [command, ...rest] = argv;
  if (!command || command === "help" || command === "--help" || command === "-h") {
    process.stdout.write(usage + "\n");
    return 0;
  }
  // T-133, T-107: the Enchanted plugin's hooks hand each event to the daemon. Whatever happens, it prints nothing
  // (a UserPromptSubmit hook's output becomes the model's context) and exits 0, so it never changes the user's turn.
  if (command === "hook" && !rest.length) {
    try {
      const chunks: Buffer[] = [];
      for await (const chunk of process.stdin) chunks.push(chunk as Buffer);
      if (socket && launch && token) await requestAt(socket, { command: "terminal_hook", raw_stdin: Buffer.concat(chunks).toString("utf8") },
        { kind: "terminal", launch, token });
    } catch { /* The daemon decides what to keep; a hook that cannot reach it leaves the turn alone. */ }
    return 0;
  }
  if (command === "session-context" && !rest.length) {
    if (socket && launch && token) process.stdout.write(orientation + "\n");
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
  if (command === "call" && rest.length === 3 && rest[0] === "terminal_open" && rest[1] === "--cwd") {
    return finish(await send({ command: "terminal_open", cwd: rest[2] }));
  }
  process.stderr.write(usage + "\n");
  return 2;
}

if (import.meta.main) process.exitCode = await main(process.argv.slice(2));
