const { main } = await import(process.env.A2A_MUTANT_CLI ?? `${process.env.A2A_WORKBENCH}/src/gates/cli.ts`);
const { A2AGates } = await import(process.env.A2A_MUTANT_CORE ?? `${process.env.A2A_WORKBENCH}/src/gates/core.ts`);
import { boundary, runtime } from "./native-runtime.ts";
const argv = process.argv.slice(2);
const value = (key: string) => argv[argv.indexOf("--" + key) + 1];
if (argv.includes("create")) argv.push("--project", value("task"));
// The fixture supplies only runtime-side active-turn facts to the production
// gate's caller interface. It never writes gate SQLite or invokes a model.
if (argv.includes("submit") && process.env.A2A_TEST_THREAD_CONTROL) {
  const gates = new A2AGates(value("state"), runtime);
  try {
    const task = (await gates.call({command: "status", task: value("task")})).task;
    const attempt = task?.current_attempt;
    if (attempt?.thread_id) {
      const live = await boundary("submit-begin", {thread: attempt.thread_id});
      const args = {task: value("task"), attempt: value("attempt"), session: value("session"),
        fence: Number(value("fence")), spec_rev: Number(value("spec-rev")), commit: value("commit")};
      const result = await gates.call({ ...args, command: "submit" }, {
        thread: attempt.thread_id, turn: live.turn,
        assertActive: async () => {},
      });
      const resultText = JSON.stringify(result);
      await boundary("submit-end", {thread: attempt.thread_id});
      await new Promise<void>(resolve => process.stdout.write(resultText + "\n", () => resolve()));
      process.exitCode = JSON.parse(resultText).ok ? 0 : 1;
    } else process.exitCode = await main(argv, runtime);
  } finally { gates.close(); }
} else process.exitCode = await main(argv, process.env.A2A_TEST_THREAD_CONTROL ? runtime : undefined);
