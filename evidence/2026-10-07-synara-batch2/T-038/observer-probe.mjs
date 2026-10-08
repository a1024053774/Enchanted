import { createRequire } from "node:module";
import { existsSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara-t038/apps/web/package.json")("playwright/test");
const root = dirname(fileURLToPath(import.meta.url));
const [label, mode] = process.argv.slice(2);
const output = join(root, label + ".json");
if (existsSync(output)) throw new Error("Evidence label already exists");
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
const observer = mode === "missing" ? undefined : { state: mode, updated_at: "2026-10-08T03:00:00Z",
  ...(mode === "failed" ? { failure: { reason: "协议夹具：SQLite 写锁，非真实故障", event_id: "fixture-event", source_sequence: 99,
    thread_id: "fixture-thread", message_id: "fixture-message" } } : {}) };
const requests = [];
await page.route("**/api/a2a*", async (route) => {
  const request = route.request();
  if (new URL(request.url()).pathname !== "/api/a2a" || request.method() !== "POST") return route.continue();
  const input = request.postDataJSON();
  if (!["status", "events"].includes(input.command)) return route.continue();
  const response = await route.fetch();
  const body = await response.json();
  delete body.human_input_observer;
  if (observer) body.human_input_observer = observer;
  requests.push({ input, actualTaskState: body.task?.state });
  await route.fulfill({ response, json: body });
});
let failure;
try {
  await page.goto("http://localhost:7771/a2a");
  await page.getByRole("button", { name: "Not now", exact: true }).click({ timeout: 60000 });
  await page.getByRole("button", { name: "Skip tour", exact: true }).click({ timeout: 15000 });
  await page.getByRole("button", { name: "Switch to activity view", exact: true }).click();
  await page.getByRole("button", { name: "Switch to classic view", exact: true }).click();
  await expect(page.getByText("See running tasks, completed work, and anything that needs your attention.", { exact: true })).toHaveCount(0);
  const text = mode === "missing" ? "人工输入记录器：未安装" : "人工输入记录器：" + mode;
  await expect(page.getByText(text, { exact: true })).toBeVisible({ timeout: 10000 });
  if (mode === "failed") await expect(page.getByText("协议夹具：SQLite 写锁，非真实故障", { exact: true })).toBeVisible();
  await page.mouse.move(1550, 950);
  await page.waitForTimeout(1200);
} catch (error) { failure = String(error); }
finally {
  await page.screenshot({ path: join(root, label + ".png"), fullPage: true });
  writeFileSync(output, JSON.stringify({ argv: process.argv.slice(1), fixture: true, mode, observer, requests, failure,
    claim: "renderer consumes explicitly marked protocol fixture; not a real observer/listener failure", text: await page.locator("body").innerText() }, null, 2) + "\n", "utf8");
  await browser.close();
}
if (failure) throw new Error(failure);
