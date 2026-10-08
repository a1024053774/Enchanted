import { createRequire } from "node:module";
import { existsSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const requireFromWeb = createRequire("/Users/luckye/Documents/Code/synara-t038/apps/web/package.json");
const { chromium, expect } = requireFromWeb("playwright/test");
const root = dirname(fileURLToPath(import.meta.url));
const label = process.argv[2];
const output = join(root, label + ".json");
if (existsSync(output)) throw new Error("Evidence label already exists");
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(String(error)));
let failure;
try {
  await page.goto("http://localhost:7771/a2a");
  await page.getByRole("button", { name: "Not now", exact: true }).click({ timeout: 15000 });
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  await expect(main).toBeVisible({ timeout: 30000 });
  await expect(main.getByRole("heading", { name: "分页交付", exact: true })).toBeVisible();
  await expect(main.getByRole("button", { name: "审查笔记", exact: true })).toBeVisible();
  await expect(main.getByRole("region", { name: "worker agent 会话", exact: true })).toBeVisible();
  await expect(main.getByRole("region", { name: "reviewer agent 会话", exact: true })).toBeVisible();
  await expect(main.getByText("ready", { exact: true })).toBeVisible();
  await expect(main.getByText("Loading conversation", { exact: true })).toHaveCount(0, { timeout: 15000 });
} catch (error) {
  failure = String(error);
} finally {
  await page.screenshot({ path: join(root, label + ".png"), fullPage: true });
  writeFileSync(output, JSON.stringify({ argv: process.argv.slice(1), surface: "dev web in isolated headless Chrome; not desktop", url: page.url(),
    browserVersion: browser.version(), errors, failure, text: await page.locator("body").innerText() }, null, 2) + "\n", "utf8");
  await browser.close();
}
if (failure) throw new Error(failure);
