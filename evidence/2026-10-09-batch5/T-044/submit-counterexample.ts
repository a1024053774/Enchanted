// Exercise the real a2a_submit handler with a reviewer's caller identity and valid worker credentials.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { A2AGates } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts";
import { a2aSubmitTool } from "/Users/luckye/Documents/Code/synara/apps/server/src/a2a/tools.ts";
import { Effect } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/node_modules/effect/dist/index.js";
const fixture = JSON.parse(readFileSync(process.argv[2]!, "utf8"));
const gates = new A2AGates("/Volumes/WD-Elements/dev-cache/synara/instances/t044/home/dev/a2a-gates");
try {
  const before = (await gates.call({ command: "status", task: fixture.task })).task!;
  const a = before.current_attempt!;
  const result = await Effect.runPromise(a2aSubmitTool(gates).handler({ task: fixture.task,
    attempt: a.attempt_id, session: a.session_id, fence: a.fence, spec_rev: a.spec_rev, commit: fixture.base }, {
      callerThreadId: fixture.attached.attachment.thread_id, callerTurnId: "reviewer-sentinel-turn",
      assertCallerTurnActive: () => Effect.void,
    } as any));
  const output = JSON.parse((result.content[0] as any).text);
  assert.equal(result.isError, true);
  assert.equal(output.error, "stale_thread");
  assert.deepEqual((await gates.call({command: "status", task: fixture.task})).task, before);
  const caller = { thread: fixture.attached.attachment.thread_id, turn: "reviewer-sentinel-turn", assertActive: async () => {} };
  const rejected = [];
  for (const command of ["create", "dispatch", "attach", "claim", "revoke", "revise", "run", "verify", "integrate", "reclaim"]) {
    const response = await gates.call({command, task: fixture.task}, caller);
    assert.equal(response.error, "stale_thread", command);
    assert.deepEqual((await gates.call({command: "status", task: fixture.task})).task, before);
    rejected.push({command, response});
  }
  console.log(JSON.stringify({ status: "PASS", input: {task: fixture.task, worker: a, reviewer: caller.thread}, submit: output, rejected, before,
    after: (await gates.call({command: "status", task: fixture.task})).task }));
} finally { gates.close(); }
