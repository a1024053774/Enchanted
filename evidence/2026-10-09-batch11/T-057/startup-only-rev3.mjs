import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const [out, root, label] = process.argv.slice(2);
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara-t057-notify/apps/web/package.json")("playwright/test");
const origin = JSON.parse(readFileSync(join(root, "ready.json"), "utf8")).origin;
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });
const page = await browser.newPage();
await page.addInitScript(() => {
  window.t057Startup = [];
  Object.defineProperty(document, "visibilityState", { configurable: true, get: () => "hidden" });
  Object.defineProperty(document, "hasFocus", { configurable: true, value: () => false });
});
let release;
const held = new Promise(resolve => { release = resolve; });
await page.route("**/api/a2a/issues?*", async route => { const response = await route.fetch(); await held; await route.fulfill({ response }); });
let failure, observations;
try {
  await page.goto("http://localhost:7968/a2a", { waitUntil: "domcontentloaded" });
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  await main.waitFor({ timeout: 60000 });
  await page.evaluate(() => { window.desktopBridge = { setTheme: async () => undefined, notifications: { show: async input => { window.t057Startup.push(input); return true; } } }; });
  release();
  await expect.poll(() => page.evaluate(() => window.t057Startup), { timeout: 8000 }).toHaveLength(1);
  expect((await page.evaluate(() => window.t057Startup))[0]).toMatchObject({ title: "3 个问题等你决定", silent: true });
} catch (error) { failure = String(error.stack ?? error); }
finally {
  observations = await page.evaluate(() => ({ calls: window.t057Startup, text: document.body.innerText, main_visible: document.querySelector('main[aria-label="任务窗口"]')?.getBoundingClientRect().height > 0 }));
  const rows = await (await page.request.post(origin + "/api/a2a", { data: { command: "issues", task: "t057" } })).json();
  await page.screenshot({ path: join(out, label + ".png") });
  writeFileSync(join(out, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), failure, observations, rows, input: "Five seeded issues; exactly numbers 1,3,4 blocking; first observation in background. Expected one combined three-item reminder." }, null, 2) + "\n", { flag: "wx" });
  await browser.close();
}
if (failure) throw new Error(failure);
