import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync, appendFileSync } from "node:fs";
import { join } from "node:path";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out, root, label] = process.argv.slice(2);
const trace = text => appendFileSync(join(out, label + "-trace.log"), text + "\n");
trace("launch");
if (existsSync(join(out, label + ".json"))) throw new Error("Evidence exists");
const seed = JSON.parse(readFileSync(join(root, "seed.json"), "utf8"));
const origin = JSON.parse(readFileSync(join(root, "ready.json"), "utf8")).origin;
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });
const context = await browser.newContext({ viewport: { width: 1600, height: 1050 } });
await context.addInitScript(() => {
  window.t057Notifications = [];
  window.t057Background = true;
  Object.defineProperty(document, "visibilityState", { configurable: true, get: () => window.t057Background ? "hidden" : "visible" });
  Object.defineProperty(document, "hasFocus", { configurable: true, value: () => !window.t057Background });
});
const page = await context.newPage();
trace("page-created");
const receipts = [], checks = [], errors = [];
let failure, lastCalls;
page.on("pageerror", error => errors.push(String(error)));
const calls = () => page.evaluate(() => window.t057Notifications);
let release;
await page.route("**/api/a2a/issues?*", async route => {
  const response = await route.fetch();
  await release;
  await route.fulfill({ response });
});
async function open(reload = false) {
  let done;
  release = new Promise(resolve => { done = resolve; });
  trace("navigate");
  if (reload) await page.reload({ waitUntil: "domcontentloaded" });
  else await page.goto("http://localhost:7968/a2a", { waitUntil: "domcontentloaded" });
  trace("dom-ready");
  await page.getByRole("main", { name: "任务窗口", exact: true }).waitFor({ timeout: 60000 });
  trace("main-ready");
  await page.evaluate(() => { window.desktopBridge = { setTheme: async () => undefined, notifications: { show: async input => { window.t057Notifications.push(input); return true; } } }; });
  done();
  await page.clock.setFixedTime(new Date("2026-10-10T04:00:00.000Z"));
  trace("queries-released");
}
async function gate(command, args) {
  const response = await page.request.post(origin + "/api/a2a", { data: { command, ...args } });
  const result = await response.json(); receipts.push({ command, args, result }); return result;
}
async function check(name, work) {
  try { await work(); checks.push({ name, pass: true }); }
  catch (error) { checks.push({ name, pass: false, error: String(error.stack ?? error) }); }
}
try {
  await open();
  await check("startup-existing-blocking-one-batch", async () => {
    await expect.poll(calls, { timeout: 8000 }).toHaveLength(1);
    expect((await calls())[0]).toMatchObject({ title: "3 个问题等你决定", silent: true, suppressWhenForeground: true });
  });
  await open(true);
  await page.waitForTimeout(2500);
  await check("restart-does-not-repeat", async () => expect(await calls()).toEqual([]));
  const closed = await gate("disposition", { task: "t057", issue: seed.issues[1].id, action: "close", reason: "已登记", basis: "ticket:T-057" });
  expect(closed.ok).toBe(true);
  await check("close-in-app-only", async () => {
    await expect(page.getByText("问题 2：未答哨兵 · 已关闭", { exact: true })).toBeVisible({ timeout: 8000 });
    expect(await calls()).toEqual([]);
  });
  await page.evaluate(() => { window.t057Background = false; window.dispatchEvent(new Event("focus")); document.dispatchEvent(new Event("visibilitychange")); });
  await gate("disposition", { task: "t057", issue: seed.issues[1].id, action: "needs-user" });
  await page.waitForTimeout(2000);
  await check("foreground-no-system", async () => expect(await calls()).toEqual([]));
  await page.evaluate(() => { window.t057Background = true; window.dispatchEvent(new Event("blur")); document.dispatchEvent(new Event("visibilitychange")); });
  await check("foreground-to-background-unreminded", async () => {
    await expect.poll(calls, { timeout: 8000 }).toHaveLength(1);
    expect((await calls())[0]).toMatchObject({ title: "1 个问题等你决定", silent: true });
  });
  await page.evaluate(() => {
    const key = "synara:app-settings:v1";
    localStorage.setItem(key, JSON.stringify({ ...JSON.parse(localStorage.getItem(key) ?? "{}"), enableSystemTaskCompletionNotifications: false }));
  });
  await open(true); await page.waitForTimeout(2000);
  await gate("disposition", { task: "t057", issue: seed.issues[4].id, action: "needs-user" });
  await page.waitForTimeout(2000);
  await check("setting-off-keeps-in-app", async () => {
    expect(await calls()).toEqual([]);
    await expect(page.getByText("问题 5：重复问题 · 等你决定", { exact: true })).toBeVisible();
  });
  await page.evaluate(() => {
    const key = "synara:app-settings:v1";
    localStorage.setItem(key, JSON.stringify({ ...JSON.parse(localStorage.getItem(key) ?? "{}"), enableSystemTaskCompletionNotifications: true }));
  });
  await open(true); await page.waitForTimeout(2000);
  await check("setting-on-restart-pending", async () => {
    expect(await calls()).toHaveLength(1);
    expect((await calls())[0]).toMatchObject({ title: "1 个问题等你决定" });
  });
  const sent = await gate("inbox_send", { from: "executor", to: "ideation", kind: "needs-decision", title: "需要用户答复", body: "无可解析含义的哨兵 Ω" });
  expect(sent.entry?.kind).toBe("needs-decision");
  await check("controller-needs-decision-system", async () => {
    await expect.poll(calls, { timeout: 8000 }).toHaveLength(2);
    expect((await calls())[1]).toMatchObject({ title: "1 项需要你回复", body: "需要用户答复", silent: true });
  });
  await page.screenshot({ path: join(out, label + ".png") });
} catch (error) { failure = String(error.stack ?? error); try { await page.screenshot({ path: join(out, label + "-failure.png"), timeout: 5000 }); } catch {} }
finally {
  try { lastCalls = await calls(); } catch (error) { errors.push(String(error)); }
  writeFileSync(join(out, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), failure, injected_clock: "2026-10-10T04:00:00.000Z", checks, receipts, calls: lastCalls, errors, limitation: "真实应用/HTTP/查询，前后台和桌面接收端受控；不证明 OS 显示。" }, null, 2) + "\n");
  await browser.close();
}
if (failure || checks.some(check => !check.pass)) throw new Error(failure ?? ("Notification contract failed: " + checks.filter(check => !check.pass).map(check => check.name).join(", ")));
