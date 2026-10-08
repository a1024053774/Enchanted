import { createRequire } from "node:module";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara-t038/apps/web/package.json")("playwright/test");
const execute = promisify(execFile);
const root = dirname(fileURLToPath(import.meta.url));
const label = process.argv[2] ?? "cycle-gui";
const resume = process.argv[3] === "claimed";
const output = join(root, label + ".json");
if (existsSync(output)) throw new Error("Evidence already exists");
const f = JSON.parse(readFileSync(join(root, "fixture.json"), "utf8"));
const checkout = "/Users/luckye/Documents/Code/synara-t038", endpoint = "http://127.0.0.1:5811";
const commands = [], screenshots = [], gateRequests = [];
async function command(argv) {
  const t = Date.now();
  try {
    const r = await execute(argv[0], argv.slice(1), { cwd: checkout, env: { ...process.env, A2A_SYNARA_SLOT: "t038" }, timeout: 120000 });
    commands.push({ argv, seconds: (Date.now() - t) / 1000, ...r, exit: 0 }); return r;
  } catch (error) { commands.push({ argv, stdout: error.stdout, stderr: error.stderr, exit: error.code }); throw error; }
}
const gate = step => command(["python3", join(root, "gate-step.py"), step]);
async function rpc(label, input) {
  const path = join(root, label + "-input.json"); writeFileSync(path, JSON.stringify(input, null, 2) + "\n", "utf8");
  await command(["./a2a/scripts/bun", join(root, "native-rpc.mjs"), label, endpoint, path]);
}
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: false });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, reducedMotion: "reduce" });
page.on("response", async response => {
  if (response.url() === endpoint + "/api/a2a" && response.request().method() === "POST")
    gateRequests.push({ input: response.request().postDataJSON(), body: await response.json() });
});
let failure;
try {
  if (!resume) {
  await gate("create");
  const createdAt = new Date().toISOString();
  await rpc("project", { type: "project.create", commandId: f.task + "-project", projectId: f.project, title: "分页二次夹具", workspaceRoot: f.repo, createdAt });
  for (const role of ["worker", "reviewer"]) await rpc(role, { type: "thread.create", commandId: f.task + "-" + role, threadId: f[role], projectId: f.project,
    title: role + " · 二次分页", modelSelection: { provider: "codex", model: "gpt-6.1-sol", options: { reasoningEffort: "xhigh", fastMode: true } },
    runtimeMode: "approval-required", interactionMode: "default", envMode: "local", branch: null, worktreePath: null, createdAt });
  for (const task of [{ taskId: f.task, projectId: f.project, title: "分页二次交付", revision: 0, members: [{ threadId: f.worker, role: "worker" }, { threadId: f.reviewer, role: "reviewer" }] },
    { taskId: f.unmanaged_task, projectId: f.project, title: "二次审查笔记", revision: 0, members: [] }]) {
    const r = await (await page.request.post(endpoint + "/api/a2a/membership", { data: { command: "save", task } })).json();
    expect(r.ok).toBe(true);
  }
  }
  await page.goto("http://localhost:7771/a2a");
  await page.getByRole("button", { name: "Not now", exact: true }).click({ timeout: 60000 });
  await page.getByRole("button", { name: "Skip tour", exact: true }).click({ timeout: 15000 });
  await page.getByRole("button", { name: "Switch to activity view", exact: true }).click();
  await page.getByRole("button", { name: "Switch to classic view", exact: true }).click();
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  await main.getByRole("button", { name: "分页二次交付", exact: true }).click();
  await expect(main.getByRole("button", { name: "二次审查笔记", exact: true })).toBeVisible();
  for (const role of ["worker", "reviewer"]) await expect(main.getByRole("region", { name: role + " agent 会话", exact: true })).toBeVisible();
  await expect(main.getByText("Loading conversation", { exact: true })).toHaveCount(0, { timeout: 15000 });
  const state = async expected => {
    await expect(main.locator("[aria-label='受管任务门禁'] [aria-current='step']")).toHaveText(expected, { timeout: 15000 });
    const actual = await (await page.request.post(endpoint + "/api/a2a", { data: { command: "status", task: f.task } })).json();
    expect(actual.task.state).toBe(expected); return actual;
  };
  const screenshot = async name => {
    await page.mouse.move(1550, 950);
    await page.screenshot({ path: join(root, label + "-" + name + ".png"), fullPage: true });
    screenshots.push({ name, text: await page.locator("body").innerText() });
  };
  if (!resume) { await state("ready"); await screenshot("ready"); await gate("claim-bad"); }
  await state("claimed"); await screenshot("claimed");
  await gate("candidate-bad"); await gate("submit-bad"); await state("submitted"); await screenshot("submitted");
  await gate("verify-bad");
  await expect(main.getByText("失败原因 · failed", { exact: true })).toBeVisible({ timeout: 15000 });
  await main.getByText("失败原因 · failed", { exact: true }).click(); await screenshot("oracle-failed");
  await gate("revoke-bad"); await gate("claim-good"); await gate("candidate-good"); await gate("submit-good"); await gate("verify-good");
  await state("verified"); await screenshot("verified");
  const observer = { state: "failed", updated_at: "2026-10-08T03:00:00Z", failure: { reason: "协议夹具：记录器失败，非真实故障" } };
  const intercept = async route => {
    if (route.request().method() !== "POST" || !["status", "events"].includes(route.request().postDataJSON().command)) return route.continue();
    const response = await route.fetch(); const body = await response.json(); await route.fulfill({ response, json: { ...body, human_input_observer: observer } });
  };
  await page.route("**/api/a2a", intercept);
  await expect(main.getByText("人工输入记录器：failed", { exact: true })).toBeVisible({ timeout: 15000 });
  await expect(main.getByRole("button", { name: "集成候选", exact: true })).toBeDisabled();
  await screenshot("observer-failed-FIXTURE");
  await page.unroute("**/api/a2a", intercept);
  await expect(main.getByText("人工输入记录器：未安装", { exact: true })).toBeVisible({ timeout: 15000 });
  await gate("integrate-good"); await state("accepted"); await screenshot("accepted");
} catch (error) { failure = String(error.stack ?? error);
  try { await page.screenshot({ path: join(root, label + "-failure.png"), fullPage: true }); } catch (captureError) { screenshots.push({ captureFailure: String(captureError) }); }
}
finally {
  writeFileSync(output, JSON.stringify({ argv: process.argv.slice(1), surface: "isolated dev Chrome; not Electron", modelTurns: 0,
    candidate: "ad13b72c5faeb5fb601c3d40b7090d746f4f2758",
    fixture: f, commands, screenshots, gateRequests, failure }, null, 2) + "\n", "utf8");
  await browser.close();
}
if (failure) throw new Error(failure);
