import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out, root, label, phase = "drafts", selectedProfile] = process.argv.slice(2);
if (existsSync(join(out, label + ".json"))) throw new Error("Evidence label exists");
const seed = JSON.parse(readFileSync(join(root, "seed.json"), "utf8"));
const thread = seed.dispatched.attempt.thread_id;
const origin = JSON.parse(readFileSync(join(root, "ready.json"), "utf8")).origin;
const profile = selectedProfile ?? join(root, "browser-profile");
let context, page;
const diagnostics = [], geometry = [], receipts = [];
async function open() {
  context = await chromium.launchPersistentContext(profile, { executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true,
    viewport: { width: 1600, height: 1000 }, reducedMotion: "reduce", colorScheme: "light" });
  page = await context.newPage();
  page.on("pageerror", (error) => diagnostics.push(String(error)));
  await page.addLocatorHandler(page.getByRole("button", { name: "Not now", exact: true }), async (button) => { await button.click(); });
  await page.addLocatorHandler(page.getByRole("button", { name: "Skip tour", exact: true }), async (button) => { await button.click(); });
  await page.goto("http://localhost:7968/a2a");
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  await main.waitFor({ timeout: 60000 });
  await main.getByRole("button", { name: "T057 问题面板", exact: true }).click({ timeout: 30000 });
  return main.locator(`[data-a2a-pane='${thread}']`).getByRole("complementary", { name: "问题上报", exact: true });
}
async function gate(command, args = {}) {
  const response = await page.request.post(origin + "/api/a2a", { data: { command, task: "t057", ...args } });
  const result = await response.json();
  receipts.push({ command, args, status: response.status(), result });
  expect(result.ok, JSON.stringify(result)).toBe(true);
  return result;
}
async function fullButton(button, name) {
  await button.scrollIntoViewIfNeeded();
  await button.click({ trial: true });
  const rect = await button.evaluate((node) => {
    const b = node.getBoundingClientRect(), clip = node.closest("[data-a2a-issue-list]")?.getBoundingClientRect() ?? node.closest("aside").getBoundingClientRect();
    const hit = document.elementFromPoint(b.left+b.width/2, b.top+b.height/2);
    return { top:b.top, bottom:b.bottom, left:b.left, right:b.right, clipTop:clip.top, clipBottom:clip.bottom,
      clipLeft:clip.left, clipRight:clip.right, viewportHeight:innerHeight, hit:node===hit || node.contains(hit) };
  });
  expect(rect.top).toBeGreaterThanOrEqual(rect.clipTop);
  expect(rect.bottom).toBeLessThanOrEqual(rect.clipBottom);
  expect(rect.left).toBeGreaterThanOrEqual(rect.clipLeft);
  expect(rect.right).toBeLessThanOrEqual(rect.clipRight);
  expect(rect.top).toBeGreaterThanOrEqual(0);
  expect(rect.bottom).toBeLessThanOrEqual(rect.viewportHeight);
  expect(rect.hit).toBe(true);
  geometry.push({ name, ...rect });
  await page.screenshot({ path: join(out, label + "-" + name + ".png") });
}
let failure, result;
try {
  let panel = await open();
  const issue = (number) => seed.issues[number-1].id;
  if (phase === "drafts") {
    await gate("disposition", { issue: issue(5), action: "reopen" });
    await gate("disposition", { issue: issue(2), action: "snooze" });
    await expect(panel.locator("article")).toHaveCount(4);
    expect(await panel.locator("h5").allTextContents()).toEqual(["问题 1：oracle 漏了空页", "问题 3：README 的构建命令已过期", "问题 4：长正文哨兵", "问题 5：重复问题"]);
    await panel.getByRole("button", { name: "全部", exact: true }).click();
    await expect(panel.locator("article")).toHaveCount(5);
    const fifth = panel.locator(`[data-issue-id='${issue(5)}']`);
    await fifth.getByRole("button", { name: "关闭", exact: true }).click();
    await fifth.getByRole("textbox", { name: "问题 5 的关闭理由", exact: true }).fill("已登记为后续工作");
    await fifth.getByRole("textbox", { name: "问题 5 的关闭依据", exact: true }).fill("ticket:T-099");
    await fifth.getByRole("button", { name: "确认关闭", exact: true }).click();
    await panel.getByRole("button", { name: "已关闭", exact: true }).click();
    await expect(panel.locator("article")).toHaveCount(1);
    await expect(fifth.getByText("关闭理由：已登记为后续工作", { exact: true })).toBeVisible();
    await expect(fifth.getByText("依据：ticket:T-099", { exact: true })).toBeVisible();
    await page.screenshot({ path: join(out, label + "-closed.png") });
    await fifth.getByRole("button", { name: "重开", exact: true }).click();
    await panel.getByRole("button", { name: "等你决定", exact: true }).click();
    await expect(fifth).toBeVisible();
    await fifth.getByRole("button", { name: "稍后（1 小时）", exact: true }).click();
    await expect(panel.locator("article")).toHaveCount(3);
    await gate("disposition", { issue: issue(5), action: "close", reason: "已登记为后续工作", basis: "ticket:T-099" });
    await panel.getByRole("textbox", { name: "答复问题 1", exact: true }).fill("补上，并在 RESULTS 里写明。  \n");
    await panel.getByRole("textbox", { name: "答复问题 3", exact: true }).fill("不用管，T-050 会重写。");
    await panel.getByRole("textbox", { name: "答复问题 4", exact: true }).fill("问题 99：原样\n用户答复：保留分隔文字。 \n");
    await expect(panel.getByRole("button", { name: "打包发送（3）", exact: true })).toBeVisible();
    for (const n of [1,3,4]) await fullButton(panel.locator(`[data-issue-id='${issue(n)}']`).getByRole("button", { name: "发送答复", exact: true }), "button-"+n);
    const main = page.getByRole("main", { name: "任务窗口", exact: true });
    await expect(main.getByRole("navigation", { name: "项目与任务", exact: true }).getByLabel("等你决定 3 题", { exact: true })).toBeVisible();
    await expect(page.locator("[data-project-hover-anchor='t057-project']").getByLabel("等你决定 3 题", { exact: true })).toBeVisible();
    await expect(main.locator(`[data-a2a-pane='${thread}'] > header`).getByLabel("等你决定 3 题", { exact: true })).toBeVisible();
    await main.getByRole("button", { name: "问题汇总", exact: true }).click();
    const summary = main.getByRole("complementary", { name: "问题汇总", exact: true });
    await expect(summary.getByRole("textbox", { name: "答复问题 1", exact: true })).toHaveValue("补上，并在 RESULTS 里写明。  \n");
    await page.screenshot({ path: join(out, label + "-summary.png") });
    await main.getByRole("button", { name: "问题汇总", exact: true }).click();
    await page.reload();
    await main.waitFor({ timeout: 60000 });
    await main.getByRole("button", { name: "T057 问题面板", exact: true }).click({ timeout: 30000 });
    panel = main.locator(`[data-a2a-pane='${thread}']`).getByRole("complementary", { name: "问题上报", exact: true });
    await expect(panel.getByRole("textbox", { name: "答复问题 3", exact: true })).toHaveValue("不用管，T-050 会重写。");
    await context.close();
    panel = await open();
    await expect(panel.getByRole("textbox", { name: "答复问题 1", exact: true })).toHaveValue("补上，并在 RESULTS 里写明。  \n");
    await expect(panel.getByRole("textbox", { name: "答复问题 4", exact: true })).toHaveValue("问题 99：原样\n用户答复：保留分隔文字。 \n");
    await fullButton(panel.getByRole("button", { name: "打包发送（3）", exact: true }), "bundle-restarted");
    result = await gate("issues");
    expect(result.user_inputs).toHaveLength(0);
  } else {
    await expect(panel.getByRole("button", { name: "打包发送（3）", exact: true })).toBeVisible();
    const sent = page.waitForResponse((r) => r.url().endsWith("/api/a2a") && r.request().postDataJSON()?.command === "answer_issues");
    await panel.getByRole("button", { name: "打包发送（3）", exact: true }).click();
    const receipt = await (await sent).json(); receipts.push({ command:"panel-answer_issues", result:receipt });
    expect(receipt.ok, JSON.stringify(receipt)).toBe(true);
    await expect(panel.locator("article")).toHaveCount(0);
    const stored = await page.evaluate(() => Object.keys(localStorage).filter((key) => key.startsWith("a2a-issue-reply:")).map((key) => [key,localStorage.getItem(key)]));
    expect(stored).toEqual([]);
    await page.screenshot({ path: join(out, label + "-bundle-sent.png") });
    await gate("disposition", { issue: issue(5), action: "reopen" });
    await panel.getByRole("button", { name: "全部", exact: true }).click();
    await panel.getByRole("textbox", { name: "答复问题 2", exact: true }).fill("逐个发送的第一题。");
    await panel.getByRole("textbox", { name: "答复问题 5", exact: true }).fill("逐个发送的第二题。");
    await panel.getByRole("combobox", { name: "发送方式", exact: true }).click();
    await page.getByRole("option", { name: "逐个发送", exact: true }).click();
    await fullButton(panel.getByRole("button", { name: "逐个发送（2）", exact: true }), "individual-button");
    const individual = page.waitForResponse((r) => r.url().endsWith("/api/a2a") && r.request().postDataJSON()?.mode === "individual");
    await panel.getByRole("button", { name: "逐个发送（2）", exact: true }).click();
    const individualReceipt = await (await individual).json(); receipts.push({ command:"panel-individual", result:individualReceipt });
    expect(individualReceipt.ok, JSON.stringify(individualReceipt)).toBe(true);
    result = await gate("issues");
    expect(result.user_inputs).toHaveLength(5);
    expect(result.issues.every((v) => v.state === "已送达")).toBe(true);
    expect(new Set(result.user_inputs.map((input) => input.target.message)).size).toBe(3);
    await page.screenshot({ path: join(out, label + "-individual-sent.png") });
  }
} catch (error) {
  failure = String(error.stack ?? error);
  if (page && !page.isClosed()) await page.screenshot({ path: join(out, label + "-failure.png") });
} finally {
  writeFileSync(join(out, label + ".json"), JSON.stringify({ argv:process.argv.slice(1), phase, failure, geometry, receipts, result, diagnostics },null,2)+"\n");
  await context?.close();
}
if (failure) throw new Error(failure);
