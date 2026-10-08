// Screenshot driver for the isolated t043 instance. Usage: ./a2a/scripts/bun shoot.mjs <label> <light|dark> <observer: missing|healthy|failed> <intervention: yes|no>
// Gate state, membership, threads and messages are real. Two read-response fixtures are labelled FIXTURE:
//  - GET /api/a2a?thread=<id> (what ChatView's own gate row reads) answers with the real task status, standing in for a thread bound by a real run;
//  - the human_intervention event and the observer block are appended to read responses (T-037 published shapes), no real producer.
import { createRequire } from "node:module";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const root = dirname(fileURLToPath(import.meta.url));
const [label, scheme, observerMode, intervention] = process.argv.slice(2);
if (!label || !["light", "dark"].includes(scheme) || !["missing", "healthy", "failed"].includes(observerMode) || !["yes", "no"].includes(intervention)) throw new Error("usage: label light|dark missing|healthy|failed yes|no");
const output = join(root, label + ".json");
if (existsSync(output)) throw new Error("Evidence label already exists");
const f = JSON.parse(readFileSync(join(root, "fixture.json"), "utf8"));
const messages = JSON.parse(readFileSync(join(root, "messages.json"), "utf8"));
const endpoint = "http://127.0.0.1:5816";
const observer = observerMode === "missing" ? undefined
  : observerMode === "healthy" ? { state: "healthy", updated_at: "2026-10-08T09:30:00Z" }
  : { state: "failed", updated_at: "2026-10-08T09:30:00Z", failure: { reason: "协议夹具：监听进程退出（exit 70），非真实故障" } };
const humanEvent = {
  seq: 100001, time: "2026-10-08T09:21:07Z", task: f.task, attempt: f.attempt.attempt_id, type: "human_intervention",
  details: { task_id: f.task, attempt_id: f.attempt.attempt_id, session_id: f.attempt.session_id, fence: f.attempt.fence, spec_rev: f.attempt.spec_rev,
    thread_id: f.threads.worker, turn_id: null, message_id: messages.worker, event_id: "FIXTURE-event-worker", source_sequence: 100001,
    created_at: "2026-10-08T09:21:07Z", dispatch_origin: "user", text: "先按 CONTRACT.md 补齐游标分页，再跑一遍 oracle。" },
};
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: false });
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, reducedMotion: "reduce", colorScheme: scheme });
const page = await context.newPage();
const seen = [];
await page.route("**/api/a2a**", async (route) => {
  const request = route.request(); const url = new URL(request.url());
  if (request.method() === "GET" && url.searchParams.get("thread")?.startsWith(f.task)) {
    const status = await (await page.request.post(endpoint + "/api/a2a", { data: { command: "status", task: f.task } })).json();
    seen.push({ get: url.search }); return route.fulfill({ json: { ...status, ...(observer ? { human_input_observer: observer } : {}) } });
  }
  if (request.method() !== "POST" || url.pathname !== "/api/a2a") return route.continue();
  const input = request.postDataJSON();
  if (!["status", "events"].includes(input.command) || input.task !== f.task) return route.continue();
  const response = await route.fetch(); const body = await response.json();
  if (input.command === "events" && intervention === "yes") body.events = [...body.events, humanEvent];
  if (observer) body.human_input_observer = observer;
  return route.fulfill({ response, json: body });
});
let failure, structure;
try {
  await page.goto("http://localhost:7776/a2a");
  await page.getByRole("button", { name: "Not now", exact: true }).click({ timeout: 60000 }).catch(() => {});
  await page.getByRole("button", { name: "Skip tour", exact: true }).click({ timeout: 8000 }).catch(() => {});
  await page.getByRole("button", { name: "Switch to activity view", exact: true }).click({ timeout: 8000 }).catch(() => {});
  await page.getByRole("button", { name: "Switch to classic view", exact: true }).click({ timeout: 8000 }).catch(() => {});
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  const taskName = process.env.TASK ?? "分页交付";
  await main.getByRole("button", { name: taskName, exact: true }).click({ timeout: 30000 });
  await expect(main.locator("section[aria-label$='agent 会话']")).toHaveCount(Number(process.env.COLUMNS ?? 3), { timeout: 30000 });
  await page.waitForTimeout(4000);
  // Fixture noise only: instance has no provider, so dismiss the provider toast and failed-turn banners before the shot.
  for (const close of await page.getByRole("button", { name: /^(Dismiss|Close)/i }).all()) await close.click({ timeout: 1000 }).catch(() => {});
  if (process.env.OPEN_FAILURE) await main.getByText("失败原因", { exact: false }).first().click();
  if (process.env.EXPAND) await main.getByText("查看人工介入记录", { exact: true }).click(); // baseline only: opens the old record block
  if (process.env.OPEN_EDITOR) await main.getByRole("button", { name: "会话归属", exact: true }).click();
  structure = await page.evaluate(() => ({
    gateSections: document.querySelectorAll("[aria-label='受管任务门禁']").length,
    observerIndicators: document.querySelectorAll("[aria-label='人工输入记录器状态']").length,
    legacyRecordBlocks: [...document.querySelectorAll("summary")].filter((n) => n.textContent?.includes("查看人工介入记录")).length,
    markedRows: [...document.querySelectorAll("[data-message-role='user'][data-message-id]")].filter((n) => getComputedStyle(n, "::before").content.includes("人工介入")).map((n) => n.getAttribute("data-message-id")),
    columnHeaders: [...document.querySelectorAll("section[aria-label$='agent 会话'] > header")].map((n) => n.innerText.replace(/\s+/g, " ")),
    scrollWidth: (() => { const c = document.querySelector("section[aria-label$='agent 会话']")?.parentElement; return c ? { client: c.clientWidth, scroll: c.scrollWidth } : null; })(),
  }));
  await page.mouse.move(1590, 990);
  await page.screenshot({ path: join(root, label + ".png") });
} catch (error) { failure = String(error.stack ?? error); try { await page.screenshot({ path: join(root, label + "-failure.png") }); } catch {} }
finally {
  const text = await page.locator("body").innerText().catch(() => "");
  writeFileSync(output, JSON.stringify({ argv: process.argv.slice(1), scheme, observerMode, intervention, fixtureNote: "see header comment", requests: seen.length, structure, failure, text }, null, 2) + "\n", "utf8");
  await browser.close();
}
if (failure) throw new Error(failure);
