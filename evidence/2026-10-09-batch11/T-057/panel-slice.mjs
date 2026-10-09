import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out, root, label] = process.argv.slice(2);
if (existsSync(join(out, label + ".json"))) throw new Error("Evidence label exists");
const seed = JSON.parse(readFileSync(join(root, "seed.json"), "utf8"));
const thread = seed.dispatched.attempt.thread_id;
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 }, reducedMotion: "reduce", colorScheme: "light" });
const diagnostics = [];
page.on("pageerror", (error) => diagnostics.push(String(error)));
let failure, records;
try {
  await page.addLocatorHandler(page.getByRole("button", { name: "Not now", exact: true }), async (button) => { await button.click(); });
  await page.addLocatorHandler(page.getByRole("button", { name: "Skip tour", exact: true }), async (button) => { await button.click(); });
  await page.goto("http://localhost:7968/a2a");
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  await main.waitFor({ timeout: 60000 });
  await main.getByRole("button", { name: "T057 问题面板", exact: true }).click({ timeout: 30000 });
  const panel = main.locator(`[data-a2a-pane='${thread}']`).getByRole("complementary", { name: "问题上报", exact: true });
  await expect(panel.locator("article")).toHaveCount(5, { timeout: 30000 });
  await page.screenshot({ path: join(out, label + "-before.png") });
  const article = panel.locator("article").filter({ has: page.getByRole("heading", { name: "问题 5：重复问题", exact: true }) });
  await article.getByRole("button", { name: "关闭", exact: true }).click();
  await article.getByRole("textbox", { name: "问题 5 的关闭理由", exact: true }).fill("已登记为后续工作");
  await article.getByRole("textbox", { name: "问题 5 的关闭依据", exact: true }).fill("ticket:T-099");
  await article.getByRole("button", { name: "确认关闭", exact: true }).click();
  await expect(article.getByText("已关闭", { exact: true })).toBeVisible();
  await expect(article.getByText("关闭理由：已登记为后续工作", { exact: true })).toBeVisible();
  await expect(article.getByText("依据：ticket:T-099", { exact: true })).toBeVisible();
  await page.screenshot({ path: join(out, label + "-closed.png") });
  await article.getByRole("button", { name: "重开", exact: true }).click();
  await expect(article.getByText("等你决定", { exact: true })).toBeVisible();
  await page.screenshot({ path: join(out, label + "-reopened.png") });
  const response = await page.request.get("http://127.0.0.1:7967/api/a2a/issues?task=t057");
  records = await response.json();
  expect(records.ok).toBe(true);
  expect(records.records.filter((r) => r.kind === "disposition").map((r) => r.action)).toEqual(["close", "reopen"]);
  expect(records.records.filter((r) => r.kind === "issue")).toEqual(seed.state.records);
} catch (error) {
  failure = String(error.stack ?? error);
  await page.screenshot({ path: join(out, label + "-failure.png") });
} finally {
  writeFileSync(join(out, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), failure, records, diagnostics,
    text: await page.locator("body").innerText() }, null, 2) + "\n");
  await browser.close();
}
if (failure) throw new Error(failure);
