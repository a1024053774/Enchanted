const { main } = await import(process.env.A2A_MUTANT_CLI ?? "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/cli.ts");
const { A2AGates } = await import(process.env.A2A_MUTANT_CORE ?? "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts");
import { boundary, runtime } from "./native-runtime.ts";
const argv = process.argv.slice(2);
const value = (key: string) => argv[argv.indexOf("--" + key) + 1];
if (argv.includes("create")) argv.push("--project", value("task"));
// Native managed submit travels through the actual MCP handler, with the fixture
// supplying only provider-side active-turn facts. It never writes gate SQLite.
if (argv.includes("submit") && process.env.A2A_TEST_THREAD_CONTROL) {
  const gates = new A2AGates(value("state"), runtime);
  try {
    const task = (await gates.call({command: "status", task: value("task")})).task;
    const attempt = task?.current_attempt;
    if (attempt?.thread_id) {
      const { a2aSubmitTool } = await import("/Users/luckye/Documents/Code/synara/apps/server/src/a2a/tools.ts");
      const { Effect } = await import("/Users/luckye/Documents/Code/synara/packages/a2a-gates/node_modules/effect/dist/index.js");
      const live = await boundary("submit-begin", {thread: attempt.thread_id});
      const args = {task: value("task"), attempt: value("attempt"), session: value("session"),
        fence: Number(value("fence")), spec_rev: Number(value("spec-rev")), commit: value("commit")};
      const result = await Effect.runPromise(a2aSubmitTool(gates).handler(args, {
        callerThreadId: attempt.thread_id, callerTurnId: live.turn,
        assertCallerTurnActive: () => Effect.void,
      } as any));
      const resultText = (result.content[0] as any).text;
      await boundary("submit-end", {thread: attempt.thread_id});
      await new Promise<void>(resolve => process.stdout.write(resultText + "\n", () => resolve()));
      process.exitCode = JSON.parse(resultText).ok ? 0 : 1;
    } else process.exitCode = await main(argv, runtime);
  } finally { gates.close(); }
} else process.exitCode = await main(argv, process.env.A2A_TEST_THREAD_CONTROL ? runtime : undefined);
