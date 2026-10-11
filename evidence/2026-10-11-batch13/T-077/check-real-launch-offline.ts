// Validate the exact approval argv with production Panes; execute no process.
// Failures: wrong planned ID/argv, fixed capability token, second launch before
// approval, third attempt accepted, or a leftover planning fixture directory.
import assert from "node:assert/strict";
import childProcess from "node:child_process";
import { promisify } from "node:util";
import { createRequire, syncBuiltinESMExports } from "node:module";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const source = "/Users/luckye/Documents/Code/a2a-wt-t077";
const evidence = join(source, "evidence/2026-10-11-batch13/T-077");
const plan = JSON.parse(readFileSync(join(evidence, "real-plan-01.json"), "utf8"));
assert(!existsSync(plan.fixture), "Never reuse an existing fixture directory");
const observed: any[] = [], checks: string[] = [];
childProcess.execFile = Object.assign(() => { throw new Error("Unconfigured external execution"); }, {
  [promisify.custom]: async (file: string, args: string[]) => {
    assert.equal(file, plan.codex); assert.deepEqual(args, ["--version"]);
    return { stdout: "codex-cli 0.162.1\n", stderr: "" };
  },
}) as any;
syncBuiltinESMExports();
const require = createRequire(pathToFileURL(join(source, "workbench/src/panes.ts")));
require("node-pty").spawn = (file: string, args: string[], options: any) => {
  observed.push({ file, args, cwd: options.cwd, launch: options.env.A2A_LAUNCH });
  return { pid: 91000 + observed.length, onData: () => {}, onExit: () => {},
    write: () => { throw new Error("Offline plan check must not submit input"); },
    kill: () => { throw new Error("Offline plan check must not signal a process"); } };
};
const { installLaunchGuard } = await import("./real-launch-host.ts");
const Panes = await installLaunchGuard(source, plan);
const { OrchestrationStore } = await import(pathToFileURL(join(source, "workbench/src/store.ts")).href);
mkdirSync(plan.fixture, { mode: 0o700 });
let store: any, failure: string | null = null;
try {
  mkdirSync(plan.home, { mode: 0o700 }); mkdirSync(plan.state); mkdirSync(join(plan.fixture, "control"));
  store = new OrchestrationStore(plan.state);
  const panes = new Panes(plan.state, store, { codex_bin: plan.codex, codex_home: plan.home,
    role_card: plan.role_card, role_card_revision: plan.role_card_revision, code_revision: plan.product_revision,
    hook_authorization: "offline command-render check; no hooks executed", turn_limit: 4 }, () => {});
  const task = { task_id: plan.task, project_id: plan.project, card: { executor: { cli: "Codex", model: "gpt-6.1-sol", effort: "xhigh" } } };
  const attempt = (fence: number) => ({ task_id: plan.task, attempt_id: `offline-attempt-${fence}`, session_id: `offline-session-${fence}`,
    thread_id: `offline-thread-${fence}`, fence, spec_rev: 1, workspace: plan.launches[fence - 1]?.workspace,
    runtime_mode: "workspace-write", base_commit: "offline" });
  const approve = (fence: number) => writeFileSync(join(plan.fixture, "control", `approval-a${fence}.json`), JSON.stringify({
    launch: plan.launches[fence - 1].launch, product_revision: plan.product_revision, controller_ref: "offline-only simulated approval",
  }), { flag: "wx" });
  approve(1);
  await panes.createThread(task, attempt(1));
  const first = panes.get("offline-thread-1");
  assert.equal(first.record.id, plan.launches[0].launch);
  assert.deepEqual(first.record.argv, plan.launches[0].argv);
  assert.notEqual(first.token, first.record.id);
  checks.push("first production argv equals approval plan; token remains separate");
  first.stopped = true; first.archived = true;
  await assert.rejects(() => panes.createThread(task, attempt(2)), { code: "ENOENT" });
  assert.equal(observed.length, 1);
  checks.push("unapproved second attempt cannot reach spawn");
  approve(2);
  await panes.createThread(task, attempt(2));
  const second = panes.get("offline-thread-2");
  assert.deepEqual(second.record.argv, plan.launches[1].argv);
  assert.notEqual(second.token, first.token); assert.notEqual(second.token, second.record.id);
  checks.push("second production argv equals approval plan; token remains independently generated");
  await assert.rejects(() => panes.createThread(task, attempt(3)));
  assert.equal(observed.length, 2);
  checks.push("third attempt cannot reach spawn");
} catch (error) { failure = String(error); }
finally {
  store?.close();
  assert(!existsSync(join(plan.home, "auth.json")), "This offline check must not copy authentication");
  rmSync(plan.fixture, { recursive: true });
}
assert(!existsSync(plan.fixture));
writeFileSync(join(evidence, "real-launch-offline-01.json"), JSON.stringify({
  status: failure ? "INCOMPLETE" : "PASS", scope: "Production command rendering with mocked version response and PTY; no real startup evidence",
  checks, failure, observed, real_codex_turns: 0, external_processes_started: 0, isolated_auth_copied: false,
  planning_fixture_removed: true, argv: process.argv,
}, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify({ status: failure ? "INCOMPLETE" : "PASS", checks: checks.length, failure, real_codex_turns: 0 }));
process.exitCode = failure ? 1 : 0;
