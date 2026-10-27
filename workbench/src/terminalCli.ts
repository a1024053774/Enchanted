import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { requestAt } from "./transport.ts";
import { cliProgram, commandCli } from "./terminalClis.ts";

// The `a2a` command inside an Enchanted project terminal (T-121). Its identity is
// the terminal itself; controller commands need a role the user approved in the UI.
const usage = `a2a：Enchanted 工作台的编排命令（在 Enchanted 的项目终端里运行）

  a2a whoami                  这个终端的项目与身份
  a2a request executor|ideation 申请成为执行主控或构思主控；等用户在界面批准，最多 10 分钟
  a2a release                 放弃当前身份；已派出的工作继续做完
  a2a call terminal_open --cwd <绝对目录>
                              在本项目开普通终端，返回 launch.id；目录须在项目主目录或额外目录内
  a2a call '<JSON>'           以已批准的身份调用门禁命令，可指向工作台里已打开的任一项目：任务命令
                              （别的项目写完整 id <项目>+<任务>），新任务的 card_* 与 create（带 project，
                              repo 为该项目打开的目录），以及 inbox_ready；没打开的项目返回 project_not_opened，例如
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
                              （runtimeMode 为 workspace-write，带 model 与 effort；要 worker 写项目外目录时
                              按任务加 extra_directories，不经审查与集成，未指定就不给）→ status
                              → submitted 后 verify → verified 后带 score_file 的 integrate；
                              交付改了卡外文件（verification.out_of_card）时，集成前先
                              a2a call '{"command":"out_of_card","task":"<任务>","decision":"accept","reason":"<为什么留下>"}'
                              或 decision 为 reject（清单与理由发回 worker）；验收文件与 Git 元数据仍硬拒。
                              或者一条 run 自动走完（身份结束或额度用完时它自己集成，记未评分；
                              有未判断的卡外改动时不集成，返回 out_of_card_unjudged 并暂停）。
                              修订已注册任务：先 status 保存旧 current_attempt.attempt_id，
                              核对旧 worker 已提交、空闲且没有待发送输入；以下示例从 v1 改为 v2：
                              a2a call '{"command":"card_save","task":"<任务>","card":"<v2 JSON 路径>","expected_version":1}'
                              a2a call '{"command":"revise","task":"<任务>","spec_rev":2,"card_version":2}'
                              a2a call '{"command":"reclaim","task":"<任务>","attempt":"<保存的旧 attempt_id>"}'
                              a2a call '{"command":"dispatch","task":"<任务>","runtimeMode":"workspace-write","model":"<模型>","effort":"<强度>"}'
                              spec_rev 须递增；card_save 只存版本，revise 才采用新卡并撤销旧交付。
                              旧会话回收成功才释放路径；未回收仍会 path_overlap，不用交叠参数绕过。
                              与别的任务路径重叠（path_overlap）时看返回的 conflicts 判断：能并行就在 dispatch
                              里加 overlap_reason 写明理由（空白不算），否则等对方验收或回收；已验收的不占路径。
                              worker_working 时先核对旧回合与输入队列，停止或归档未确认时保留现场并上报。
                              回收后脏工作区仍保留、上报；保留证据不继续占用路径。
                              回答 worker 上报的问题：issues / answer_issue，记为主控的回答。
                              attach（role 为 monitor）挂一个只读观察会话。
  a2a help                    显示这段说明

只有用户本人要求时才申请身份；被拒绝或超时就停下告诉用户。申请命令被中断、被杀或超时，后台都会撤回申请。`;

// T-181 (L08), T-185: a model that never picks the a2a skill still has to know the command exists. Claude Code (its
// plugin) and Codex (the shim's -c hooks.SessionStart) both run this at session start and add additionalContext to
// the session's context, so the text holds for either CLI.
// T-185, T-187: one orientation for every terminal CLI: Claude and Codex get it from their session-start hook, opencode
// reads the file as its instructions (terminal/bin/opencode), agy reads it as the AGENTS.md of a directory the shim adds
// to its workspace (terminal/bin/agy).
const orientation = readFileSync(fileURLToPath(new URL("../terminal/orientation/AGENTS.md", import.meta.url)), "utf8").trimEnd();

// This command's ancestor processes and their argv, nearest first (T-187: a CLI started inside another).
function ancestors(): { pid: number; argv: string[] }[] {
  const rows = new Map(execFileSync("/bin/ps", ["-axo", "pid=,ppid=,args="], { encoding: "utf8" }).split("\n")
    .map(line => line.trim().match(/^(\d+)\s+(\d+)\s+(.*)$/)).filter(match => match !== null)
    .map(match => [Number(match![1]), { parent: Number(match![2]), argv: match![3].split(/\s+/) }]));
  const chain: { pid: number; argv: string[] }[] = [];
  for (let pid = process.ppid; rows.has(pid) && chain.length < 64; pid = rows.get(pid)!.parent) chain.push({ pid, argv: rows.get(pid)!.argv });
  return chain;
}
const ancestorArgv = () => ancestors().map(row => row.argv);

// The terminal socket accepts only this identity (T-126); the daemon's data directory is not in the environment.
const socket = process.env.A2A_TERMINAL_SOCKET, launch = process.env.A2A_TERMINAL, token = process.env.A2A_TERMINAL_TOKEN;
// Where the CLI keeps its records, from the environment it gives its commands.
const nativeHome = (cli: string | undefined) => cli === "claude" ? process.env.CLAUDE_CONFIG_DIR || (process.env.HOME && process.env.HOME + "/.claude") :
  cli === "codex" ? process.env.CODEX_HOME || (process.env.HOME && process.env.HOME + "/.codex") : undefined;
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
      // T-195: which CLI process runs this hook, so the session it names is bound to that process.
      const cli = commandCli(process.env, ancestorArgv);
      const pid = ancestors().find(row => cliProgram(row.argv) === cli)?.pid;
      if (socket && launch && token) await requestAt(socket, { command: "terminal_hook", raw_stdin: Buffer.concat(chunks).toString("utf8"),
        ...(cli && pid ? { cli, cli_pid: pid, native_home: nativeHome(cli) } : {}) }, { kind: "terminal", launch, token });
    } catch { /* The daemon decides what to keep; a hook that cannot reach it leaves the turn alone. */ }
    return 0;
  }
  if (command === "session-context" && !rest.length) {
    if (socket && launch && token) print({ hookSpecificOutput: { hookEventName: "SessionStart", additionalContext: orientation } });
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
    const cli = commandCli(process.env, ancestorArgv);
    // The CLI's own session and home, from the environment it gives its commands (T-124 probe 01): the
    // daemon reads only that session's usage-limit records, to tell the user when this controller runs out.
    const native = cli === "claude" ? { native_session: process.env.CLAUDE_CODE_SESSION_ID, native_home: nativeHome(cli) } :
      cli === "codex" ? { native_session: process.env.CODEX_THREAD_ID, native_home: nativeHome(cli) } : {};
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
