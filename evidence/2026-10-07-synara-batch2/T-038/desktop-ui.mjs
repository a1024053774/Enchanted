import { createRequire } from "node:module";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const { _electron, chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara-t038/apps/web/package.json")("playwright/test");
const execute = promisify(execFile);
const root = dirname(fileURLToPath(import.meta.url));
const checkout = "/Users/luckye/Documents/Code/synara-t038";
const label = process.argv[2];
const browserMode = process.argv[3] === "browser";
const resume = process.argv[3] === "resume" || browserMode;
const alreadyClaimed = process.argv[4] === "claimed";
const alreadyFailed = process.argv[4] === "failed";
const record = join(root, label + ".json");
if (existsSync(record)) throw new Error("Evidence label already exists");
const fixturePath = join(root, browserMode ? "fixture.json" : "fixture-desktop.json");
const fixture = JSON.parse(readFileSync(fixturePath, "utf8"));
const home = "/Volumes/WD-Elements/dev-cache/synara/instances/t038/desktop-home";
const profile = "/Volumes/WD-Elements/dev-cache/synara/instances/t038/electron-profile-main";
mkdirSync(home, { recursive: true }); mkdirSync(profile, { recursive: true });
const launch = {
  executablePath: "/Volumes/WD-Elements/dev-cache/synara/instances/t038/tools/electron-43.4.1/Electron.app/Contents/MacOS/Electron",
  args: [join(checkout, "apps/desktop/dist-electron/main.js")], cwd: join(checkout, "apps/desktop"), timeout: 60000,
  env: { ...process.env, SYNARA_HOME: home, SYNARA_DESKTOP_SMOKE_USER_DATA: profile, SYNARA_DESKTOP_FLAVOR: "cua",
    SYNARA_SOURCE_DESKTOP_BUILD_MARKER: "synara-source-desktop-build-v2", SYNARA_DISABLE_AUTO_UPDATE: "1",
    VITE_DEV_SERVER_URL: "http://localhost:7771/a2a" },
};
const steps = [], errors = [];
let app, page, failure, token = "", endpoint;
let browser;
const clean = (text) => String(text).replace(/([?&]token=)[^&\s"']+/g, "$1<redacted>").replaceAll(token || "\u0000", "<redacted>");
async function command(argv, extraEnv = {}) {
  const started = Date.now();
  try {
    const result = await execute(argv[0], argv.slice(1), { cwd: checkout, env: { ...process.env, ...extraEnv, A2A_SYNARA_SLOT: "t038" }, timeout: 120000, maxBuffer: 8 * 1024 * 1024 });
    steps.push({ argv, seconds: (Date.now() - started) / 1000, stdout: clean(result.stdout), stderr: clean(result.stderr), exit: 0 });
    return result;
  } catch (error) {
    steps.push({ argv, stdout: clean(error.stdout), stderr: clean(error.stderr), exit: error.code }); throw error;
  }
}
async function gate(step, alias = step) { await command(["python3", join(root, "gate-step.py"), step, fixturePath, alias]); }
async function rpc(name, input) {
  const path = join(root, name + "-input.json"); if (existsSync(path)) throw new Error("RPC input already exists");
  writeFileSync(path, JSON.stringify(input, null, 2) + "\n", "utf8");
  await command(["./a2a/scripts/bun", join(root, "native-rpc.mjs"), name, endpoint, path], { A2A_GATE_BEARER: token });
}
async function screenshot(name) {
  if (browserMode) name = name.replace(/^desktop-/, "dev-");
  const path = join(root, name + ".png"); if (existsSync(path)) throw new Error("Screenshot already exists");
  await page.screenshot({ path, fullPage: true });
  steps.push({ screenshot: path, text: clean(await page.locator("body").innerText()) });
}
async function expectState(state) {
  await expect(page.getByRole("main", { name: "任务窗口" }).locator("[aria-label='受管任务门禁']").getByText(state, { exact: true })).toBeVisible({ timeout: 15000 });
  // The named state must be current (the other four badges are only milestones).
  await expect.poll(async () => {
    const url = new URL("/api/a2a", endpoint); url.searchParams.set("token", token);
    const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ command: "status", task: fixture.task }) });
    return (await response.json()).task?.state;
  }, { timeout: 15000 }).toBe(state);
}
try {
  if (browserMode) {
    browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });
    page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
    await page.goto("http://localhost:7771/a2a"); endpoint = "http://127.0.0.1:5811";
    steps.push({ surface: "dev Chrome; separate profile; native desktop remains unverified", modelCalls: false });
  } else {
  app = await _electron.launch(launch);
  await expect.poll(() => app.windows().some((window) => window.url().startsWith("http://localhost:7771/a2a")), { timeout: 60000 }).toBe(true);
  steps.push({ windows: app.windows().map((window) => ({ url: clean(window.url()) })) });
  page = app.windows().find((window) => window.url().startsWith("http://localhost:7771/a2a"));
  page.setDefaultTimeout(45000);
  page.on("console", (message) => { if (message.type() === "error") errors.push(clean(message.text())); });
  page.on("requestfailed", (request) => errors.push(clean({ url: request.url(), failure: request.failure() })));
  page.on("pageerror", (error) => errors.push(clean(error)));
  await expect.poll(() => page.evaluate(() => Boolean(window.desktopBridge?.getWsUrl?.())), { timeout: 60000 }).toBe(true);
  const ws = new URL(await page.evaluate(() => window.desktopBridge.getWsUrl()));
  token = ws.searchParams.get("token") ?? ""; endpoint = "http://" + ws.host;
  const identity = await app.evaluate(({ app }) => ({ userData: app.getPath("userData"), appPath: app.getAppPath(), version: process.versions.electron }));
  if (identity.userData !== profile) throw new Error("Desktop profile is not isolated: " + identity.userData);
  steps.push({ identity, endpoint, home, profile, pid: app.process().pid, modelCalls: false });
  }
  if (!resume) {
  await gate("create", "desktop-create");
  const now = new Date().toISOString();
  await rpc("desktop-project", { type: "project.create", commandId: fixture.task + "-project", projectId: fixture.project, title: "分页桌面夹具", workspaceRoot: fixture.repo, createdAt: now });
  for (const role of ["worker", "reviewer"]) await rpc("desktop-" + role, { type: "thread.create", commandId: fixture.task + "-" + role, threadId: fixture[role], projectId: fixture.project, title: role + " · 分页",
    modelSelection: { provider: "codex", model: "gpt-6.1-sol", options: { reasoningEffort: "xhigh", fastMode: true } }, runtimeMode: "approval-required", interactionMode: "default", envMode: "local", branch: null, worktreePath: null, createdAt: now });
  const membershipUrl = new URL("/api/a2a/membership", endpoint); membershipUrl.searchParams.set("token", token);
  for (const task of [{ taskId: fixture.task, projectId: fixture.project, title: "分页交付", revision: 0, members: [{ threadId: fixture.worker, role: "worker" }, { threadId: fixture.reviewer, role: "reviewer" }] },
    { taskId: fixture.unmanaged_task, projectId: fixture.project, title: "审查笔记", revision: 0, members: [] }]) {
    const response = await fetch(membershipUrl, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ command: "save", task }) });
    const result = await response.json(); steps.push({ membership: task, result }); if (!result.ok) throw new Error(JSON.stringify(result));
  }
  }
  await page.waitForSelector("#root > *", { timeout: 60000 });
  const notNow = page.getByRole("button", { name: "Not now", exact: true });
  if (browserMode) await notNow.click({ timeout: 60000 });
  else if (await notNow.isVisible()) await notNow.click();
  const skip = page.getByRole("button", { name: "Skip tour", exact: true });
  if (browserMode) await skip.click({ timeout: 15000 });
  else if (await skip.isVisible()) await skip.click();
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  await expect(main.getByRole("heading", { name: "分页交付", exact: true })).toBeVisible({ timeout: 45000 });
  await expect(main.getByRole("button", { name: "审查笔记", exact: true })).toBeVisible();
  await expect(main.getByRole("region", { name: "worker agent 会话", exact: true })).toBeVisible();
  await expect(main.getByRole("region", { name: "reviewer agent 会话", exact: true })).toBeVisible();
  await expect(main.getByText("Loading conversation", { exact: true })).toHaveCount(0, { timeout: 15000 });
  if (!alreadyClaimed && !alreadyFailed) {
    await expectState("ready"); await screenshot("desktop-ready");
    await gate("claim-bad"); await expectState("claimed"); await screenshot("desktop-claimed");
    await gate("candidate-bad");
  }
  if (!alreadyFailed) {
    await gate("submit-bad"); await expectState("submitted"); await screenshot("desktop-submitted");
    await gate("verify-bad");
  }
  await expect(main.getByText("失败原因 · failed", { exact: true })).toBeVisible({ timeout: 15000 });
  await main.getByText("失败原因 · failed", { exact: true }).click(); await screenshot("desktop-oracle-failed");
  await gate("revoke-bad"); await gate("claim-good"); await gate("candidate-good"); await gate("submit-good"); await gate("verify-good");
  await expectState("verified"); await screenshot("desktop-verified");
  const fixtureObserver = { state: "failed", updated_at: new Date().toISOString(), failure: { reason: "协议夹具：记录器写入失败，非真实故障", event_id: "observer-fixture", source_sequence: 1, thread_id: fixture.worker, message_id: "observer-message" } };
  const observerHandler = async (route) => {
    const request = route.request(); if (new URL(request.url()).pathname !== "/api/a2a" || request.method() !== "POST") return route.continue();
    if (!["status", "events"].includes(request.postDataJSON().command)) return route.continue();
    const response = await route.fetch(); const body = await response.json(); body.human_input_observer = fixtureObserver;
    await route.fulfill({ response, json: body });
  };
  await page.route("**/api/a2a*", observerHandler);
  await expect(page.getByText("人工输入记录器：failed", { exact: true })).toBeVisible({ timeout: 15000 });
  await expect(main.getByRole("button", { name: "集成候选", exact: true })).toBeDisabled();
  await screenshot("desktop-observer-failed-FIXTURE");
  steps.push({ fixture: true, kind: "observer failure display only", input: fixtureObserver, expected: "real task stays verified; integrate button disabled; not a real listener failure" });
  await page.unroute("**/api/a2a*", observerHandler);
  await expect(page.getByText("人工输入记录器：未安装", { exact: true })).toBeVisible({ timeout: 15000 });
  await gate("integrate-good"); await expectState("accepted"); await screenshot("desktop-accepted");
} catch (error) {
  failure = clean(error.stack ?? error);
  if (page && !page.isClosed()) {
    steps.push({ rendererHtml: clean(await page.content()), rendererUrl: clean(page.url()) });
    await screenshot(label + "-failure");
  }
} finally {
  writeFileSync(record, JSON.stringify({ argv: process.argv.slice(1), launch: { executablePath: launch.executablePath, args: launch.args, cwd: launch.cwd,
    env: { SYNARA_HOME: home, SYNARA_DESKTOP_SMOKE_USER_DATA: profile, SYNARA_DESKTOP_FLAVOR: "cua", VITE_DEV_SERVER_URL: launch.env.VITE_DEV_SERVER_URL } }, steps, errors, failure }, null, 2) + "\n", "utf8");
  if (app) {
    const closing = app.close();
    const settled = await Promise.race([closing.then(() => true), new Promise((resolve) => setTimeout(() => resolve(false), 15000))]);
    if (!settled) app.process().kill("SIGKILL");
  }
  if (browser) await browser.close();
}
if (failure) throw new Error(failure);
