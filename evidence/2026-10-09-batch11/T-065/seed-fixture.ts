// Setup-only controlled native boundary. HTTP/UI/server after startup are real.
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
const root = process.env.T057_ROOT!;
const fork = process.env.T057_FORK!;
const { A2AGates } = await import(join(fork, "packages/a2a-gates/src/core.ts"));
const repo = join(root, "repo");
mkdirSync(repo, { recursive: true });
const git = (...args: string[]) => execFileSync("git", ["-C", repo, ...args], { encoding: "utf8",
  env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" } }).trim();
git("init"); git("config", "user.name", "T057 isolated fixture"); git("config", "user.email", "fixture@example.invalid"); git("config", "commit.gpgsign", "false");
writeFileSync(join(repo, "sentinel.txt"), "T057 external fixture\n");
git("add", "sentinel.txt"); git("commit", "-m", "External fixture");
writeFileSync(join(root, "oracle.py"), "raise SystemExit(0)\n");
writeFileSync(join(root, "instructions.txt"), "Isolated fixture. Do not change files.\n");
let worker: any;
const core = new A2AGates(join(root, "userdata/a2a-gates"), {
  ensureProject: async () => {}, createThread: async (_task: any, attempt: any) => { worker = attempt; },
  startThread: async () => {},
  readThread: async () => ({ workspace: worker.workspace, provider: "codex", turn: "seed-turn", running: true, stopped: false, archived: false }),
  stopThread: async () => {}, archiveThread: async () => {},
});
const created = await core.call({ command: "create", task: "t057", project: "t057-project", title: "T057 问题面板",
  repo, base: git("rev-parse", "HEAD"), oracle: join(root, "oracle.py"), instructions: join(root, "instructions.txt") });
if (!created.ok) throw new Error(JSON.stringify(created));
const dispatched = await core.call({ command: "dispatch", task: "t057", runtimeMode: "approval-required" });
if (!dispatched.ok) throw new Error(JSON.stringify(dispatched));
const rows = process.env.T065_NO_ISSUES === '1' ? [] : [
  ["oracle 漏了空页", "分页夹具没有覆盖最后一页为空的情况。", true],
  ["未答哨兵", "这题未答，不参加发送。", false],
  ["README 的构建命令已过期", "", true],
  ["长正文哨兵", "😀".repeat(601), true],
  ["重复问题", "已经登记为后续工作。", false],
];
const issues = [];
for (const [title, body, blocking] of rows) issues.push(await core.raiseIssue({ title, body, blocking, refs: ["file:sentinel.txt#L1"] },
  { thread: worker.thread_id, turn: "seed-turn", assertActive: async () => {} }));
const state = await core.call({ command: "status", task: "t057" });
core.close();
writeFileSync(join(root, "seed.json"), JSON.stringify({ created, dispatched, issues, state,
  limitation: "Only initial issue creation uses a controlled native boundary; no provider or user auth was invoked." }, null, 2));
console.log(JSON.stringify({ root, task: "t057", thread: worker.thread_id, issues }));
