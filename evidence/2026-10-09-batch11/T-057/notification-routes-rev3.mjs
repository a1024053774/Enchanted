import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out, root, label] = process.argv.slice(2);
const seed = JSON.parse(readFileSync(join(root, "seed.json"), "utf8"));
const origin = JSON.parse(readFileSync(join(root, "ready.json"), "utf8")).origin;
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });
const page = await browser.newPage();
await page.addInitScript(() => {
  window.t057Timers = [];
  const set = window.setTimeout.bind(window), clear = window.clearTimeout.bind(window);
  const watched = new Set();
  window.setTimeout = (fn, ms, ...args) => {
    let id;
    id = set((...values) => { if (ms === 200) window.t057Timers.push({ action: "fire", id }); fn(...values); }, ms, ...args);
    if (ms === 200) { watched.add(id); window.t057Timers.push({ action: "schedule", id }); }
    return id;
  };
  window.clearTimeout = id => { if (watched.has(id)) window.t057Timers.push({ action: "cancel", id }); clear(id); };
  window.t057Background = false;
  Object.defineProperty(document, "visibilityState", { configurable: true, get: () => window.t057Background ? "hidden" : "visible" });
  Object.defineProperty(document, "hasFocus", { configurable: true, value: () => !window.t057Background });
});
const receipts = [], checks = []; let failure;
async function gate(command, args) {
  const response = await page.request.post(origin + "/api/a2a", { data: { command, ...args } });
  const result = await response.json(); receipts.push({ command, args, result }); return result;
}
const calls = () => page.evaluate(() => window.t057Calls);
try {
  await page.goto("http://localhost:7968/a2a", { waitUntil: "domcontentloaded" });
  await page.getByRole("main", { name: "任务窗口", exact: true }).waitFor({ timeout: 60000 });
  await page.evaluate(() => { window.t057Calls = []; window.desktopBridge = { setTheme: async () => undefined, notifications: { show: async input => { window.t057Calls.push(input); return true; } } }; });
  await page.evaluate(() => { window.t057Background = true; document.dispatchEvent(new Event("visibilitychange")); window.dispatchEvent(new Event("blur")); });
  await expect.poll(calls, { timeout: 6000 }).toHaveLength(1);
  await page.evaluate(() => { window.t057Calls = []; });
  const report = await gate("inbox_send", { from: "executor", to: "ideation", kind: "report", title: "blocking 等你决定 主控停下等用户答复", body: "需要用户做决定" });
  expect(report.entry.kind).toBe("report");
  await page.waitForTimeout(1600);
  expect(await calls()).toEqual([]);
  checks.push("报告正文和标题含等待词语，仍不走系统通知");
  const decision = await gate("inbox_send", { from: "executor", to: "ideation", kind: "needs-decision", title: "Ω-17", body: "常规进度" });
  expect(decision.entry.kind).toBe("needs-decision");
  await expect.poll(calls, { timeout: 6000 }).toHaveLength(1);
  expect((await calls())[0]).toMatchObject({ title: "1 项需要你回复", body: "Ω-17", silent: true, suppressWhenForeground: true });
  checks.push("needs-decision 按 kind 路由，标题与正文无等待含义");
  await page.evaluate(() => { window.t057Calls = []; });
  for (const index of [0, 2]) {
    const result = await gate("disposition", { task: "t057", issue: seed.issues[index].id, action: "needs-user" });
    expect(result.ok).toBe(true);
  }
  await expect.poll(calls, { timeout: 6000 }).toHaveLength(1);
  expect((await calls())[0]).toMatchObject({ title: "2 个问题等你决定", silent: true });
  expect((await calls())[0].body).toBe("问题 1：oracle 漏了空页\n问题 3：README 的构建命令已过期");
  checks.push("同一批两个新等你决定合并一次");
  await page.evaluate(() => { window.t057Calls = []; });
  const issues = await gate("issues", { task: "t057" });
  const delivered = issues.issues.find(v => v.issue.title === "七动作 MCP 独立问题 Ω");
  expect(delivered.state).toBe("已送达");
  const result = await gate("disposition", { task: "t057", issue: delivered.issue.id, action: "delivered" });
  expect(result.ok).toBe(true);
  await expect(page.getByText("问题 6：七动作 MCP 独立问题 Ω · 已送达", { exact: true })).toBeVisible({ timeout: 6000 });
  expect(await calls()).toEqual([]);
  checks.push("送达变化只发软件内通知");
  await page.screenshot({ path: join(out, label + ".png") });
} catch (error) { failure = String(error.stack ?? error); }
finally {
  const observed = await page.evaluate(() => ({ calls: window.t057Calls, timers: window.t057Timers, visibility: document.visibilityState, focus: document.hasFocus(), texts: Array.from(document.body.innerText).slice(-1500).join("") }));
  writeFileSync(join(out, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), failure, checks, receipts, observed, limitation: "真实应用与 HTTP；前后台及 bridge 接收端受控。" }, null, 2) + "\n");
  await browser.close();
}
if (failure) throw new Error(failure);
