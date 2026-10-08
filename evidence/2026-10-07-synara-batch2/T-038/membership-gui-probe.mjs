import { createRequire } from "node:module";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara-t038/apps/web/package.json")("playwright/test");
const root = dirname(fileURLToPath(import.meta.url));
const label = process.argv[2];
if (!label || existsSync(join(root, label + ".json"))) throw new Error("New evidence label required");
const fixture = JSON.parse(readFileSync(join(root, "fixture.json"), "utf8"));
const input = { taskId: fixture.task + "-" + label, title: "GUI 归属复验 · " + label, projectId: fixture.project };
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: false });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, reducedMotion: "reduce" });
let failure, readback, concurrent, afterRefusal;
try {
  await page.goto("http://localhost:7771/a2a");
  await page.getByRole("button", { name: "Not now", exact: true }).click({ timeout: 60000 });
  await page.getByRole("button", { name: "Skip tour", exact: true }).click({ timeout: 15000 });
  await page.getByRole("button", { name: "Switch to activity view", exact: true }).click();
  await page.getByRole("button", { name: "Switch to classic view", exact: true }).click();
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  await main.getByRole("button", { name: "为分页夹具添加任务", exact: true }).click();
  const newTask = page.getByRole("form", { name: "添加任务", exact: true });
  await newTask.getByLabel("任务标题", { exact: true }).fill(input.title);
  await newTask.getByLabel("任务 ID（已有门禁任务时填写）", { exact: true }).fill(input.taskId);
  await newTask.getByRole("button", { name: "添加任务", exact: true }).click();
  await expect(main.getByRole("heading", { name: input.title, exact: true })).toBeVisible();
  await expect(main.getByText("未挂验收合同", { exact: true })).toBeVisible();
  await main.getByRole("button", { name: "会话归属", exact: true }).click();
  const editor = page.getByRole("form", { name: "编辑会话归属", exact: true });
  for (const [title, role] of [["worker · 分页", "worker"], ["reviewer · 分页", "reviewer"]]) {
    await editor.getByRole("combobox", { name: "选择 agent 会话", exact: true }).click();
    await page.getByRole("option", { name: title, exact: true }).click();
    await editor.getByRole("combobox", { name: "会话角色", exact: true }).click();
    await page.getByRole("option", { name: role, exact: true }).click();
    await editor.getByRole("button", { name: "添加会话", exact: true }).click();
  }
  await editor.getByRole("button", { name: "保存归属", exact: true }).click();
  await expect(main.getByRole("region", { name: "worker agent 会话", exact: true })).toBeVisible();
  await expect(main.getByRole("region", { name: "reviewer agent 会话", exact: true })).toBeVisible();
  const list = async () => (await page.request.get("http://127.0.0.1:5811/api/a2a/membership")).json();
  readback = (await list()).tasks.find(task => task.taskId === input.taskId);
  expect(readback).toMatchObject({ ...input, revision: 2, members: [
    { threadId: fixture.worker, role: "worker" }, { threadId: fixture.reviewer, role: "reviewer" },
  ] });
  await main.getByRole("button", { name: "会话归属", exact: true }).click();
  await editor.getByLabel("任务标题", { exact: true }).fill(input.title + " stale local edit");
  concurrent = await (await page.request.post("http://127.0.0.1:5811/api/a2a/membership", {
    data: { command: "save", task: { ...readback, title: input.title + " concurrent save" } },
  })).json();
  expect(concurrent.ok).toBe(true);
  await expect(main.getByRole("heading", { name: concurrent.task.title, exact: true })).toBeVisible();
  await editor.getByRole("button", { name: "保存归属", exact: true }).click();
  await expect(editor.getByRole("alert")).toContainText("stale_revision");
  afterRefusal = (await list()).tasks.find(task => task.taskId === input.taskId);
  expect(afterRefusal).toEqual(concurrent.task);
  await page.mouse.move(1550, 950);
} catch (error) { failure = String(error); }
finally {
  let screenshotFailure;
  try { await page.screenshot({ path: join(root, label + ".png"), fullPage: true }); } catch (error) { screenshotFailure = String(error); }
  writeFileSync(join(root, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), input, readback,
    concurrent, afterRefusal, failure, screenshotFailure, text: page.isClosed() ? undefined : await page.locator("body").innerText() }, null, 2) + "\n", "utf8");
  await browser.close();
}
if (failure) throw new Error(failure);
