import { createRequire } from "node:module";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara-t038/apps/web/package.json")("playwright/test");
const root = dirname(fileURLToPath(import.meta.url)), label = process.argv[2];
if (!label || existsSync(join(root, label + ".json"))) throw new Error("New evidence label required");
const f = JSON.parse(readFileSync(join(root, "fixture.json"), "utf8"));
const guiId = f.task + "-membership-gui-headed", guiTitle = "GUI 归属复验 · membership-gui-headed concurrent save";
const expectedMembers = [{ threadId: f.worker, role: "worker" }, { threadId: f.reviewer, role: "reviewer" }];
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: false });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, reducedMotion: "reduce" });
let failure, memberships, screenshotFailure;
try {
  await page.goto("http://localhost:7771/a2a");
  await page.getByRole("button", { name: "Not now", exact: true }).click({ timeout: 60000 });
  await page.getByRole("button", { name: "Skip tour", exact: true }).click({ timeout: 15000 });
  await page.getByRole("button", { name: "Switch to activity view", exact: true }).click();
  await page.getByRole("button", { name: "Switch to classic view", exact: true }).click();
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  await expect(main.getByRole("button", { name: "审查笔记", exact: true })).toBeVisible();
  await main.getByRole("button", { name: "分页交付", exact: true }).click();
  await expect(main.locator("[aria-label='受管任务门禁'] [aria-current='step']")).toHaveText("accepted", { timeout: 15000 });
  for (const role of ["worker", "reviewer"]) await expect(main.getByRole("region", { name: role + " agent 会话", exact: true })).toBeVisible();
  await expect(main.getByText("Loading conversation", { exact: true })).toHaveCount(0, { timeout: 15000 });
  await page.mouse.move(1550, 950);
  await page.screenshot({ path: join(root, label + "-managed.png"), fullPage: true });
  await main.getByRole("button", { name: guiTitle, exact: true }).click();
  await expect(main.getByRole("heading", { name: guiTitle, exact: true })).toBeVisible();
  for (const role of ["worker", "reviewer"]) await expect(main.getByRole("region", { name: role + " agent 会话", exact: true })).toBeVisible();
  memberships = await (await page.request.get("http://127.0.0.1:5811/api/a2a/membership?project=" + f.project)).json();
  expect(memberships.tasks.find(task => task.taskId === f.task).members).toEqual(expectedMembers);
  expect(memberships.tasks.find(task => task.taskId === guiId)).toMatchObject({ title: guiTitle, revision: 3, members: expectedMembers });
  await page.mouse.move(1550, 950);
  await page.screenshot({ path: join(root, label + "-edited.png"), fullPage: true });
} catch (error) { failure = String(error); }
finally {
  try { await page.screenshot({ path: join(root, label + ".png"), fullPage: true }); } catch (error) { screenshotFailure = String(error); }
  writeFileSync(join(root, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), memberships, expectedMembers,
    expectedTitle: guiTitle, failure, screenshotFailure, source: "real restarted service; fresh private dev Chrome; no response interception" }, null, 2) + "\n", "utf8");
  await browser.close();
}
if (failure) throw new Error(failure);
