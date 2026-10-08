import { createRequire } from "node:module";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara-t038/apps/web/package.json")("playwright/test");
const root = dirname(fileURLToPath(import.meta.url));
const label = process.argv[2];
if (!label || existsSync(join(root, label + ".json"))) throw new Error("New evidence label required");
const fixture = JSON.parse(readFileSync(join(root, "fixture.json"), "utf8"));
const historical = JSON.parse(readFileSync(join(root, "claim-bad.json"), "utf8")).result.attempt;
const current = JSON.parse(readFileSync(join(root, "claim-good.json"), "utf8")).result.attempt;
// T-037's published event contract. These events exist only in intercepted read responses.
const event = (thread, attempt, id, seq, text) => ({
  seq, time: "2026-10-08T03:00:00Z", task: fixture.task, attempt: attempt.attempt_id,
  type: "human_intervention", details: {
    task_id: fixture.task, attempt_id: attempt.attempt_id, session_id: attempt.session_id,
    fence: attempt.fence, spec_rev: attempt.spec_rev, thread_id: thread, turn_id: null,
    message_id: "FIXTURE-message-" + id, event_id: "FIXTURE-event-" + id,
    source_sequence: seq, created_at: "2026-10-08T03:00:00Z", dispatch_origin: "user", text,
  },
});
const workerEvent = event(fixture.worker, historical, "worker", 100001, "人工介入协议夹具：历史 worker 输入；未执行 turn");
const reviewerEvent = event(fixture.reviewer, current, "reviewer", 100002, "人工介入协议夹具：reviewer 输入；未执行 turn");
const foreignEvent = { ...workerEvent, task: "FIXTURE-foreign-task", details: { ...workerEvent.details, task_id: "FIXTURE-foreign-task" } };
const fixtureEvents = [workerEvent, workerEvent, reviewerEvent, foreignEvent];
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
const requests = [];
await page.route("**/api/a2a", async route => {
  if (route.request().method() !== "POST") return route.continue();
  const input = route.request().postDataJSON();
  if (input.command !== "events" || input.task !== fixture.task) return route.continue();
  const response = await route.fetch();
  const actual = await response.json();
  requests.push({ input, actualEventCount: actual.events.length });
  await route.fulfill({ response, json: { ...actual, events: [...actual.events, ...fixtureEvents] } });
});
let failure, before, after;
try {
  const status = async () => (await page.request.post("http://127.0.0.1:5811/api/a2a", { data: { command: "status", task: fixture.task } })).json();
  before = await status();
  await page.goto("http://localhost:7771/a2a");
  await page.getByRole("button", { name: "Not now", exact: true }).click({ timeout: 60000 });
  await page.getByRole("button", { name: "Skip tour", exact: true }).click({ timeout: 15000 });
  await page.getByRole("button", { name: "Switch to activity view", exact: true }).click();
  await page.getByRole("button", { name: "Switch to classic view", exact: true }).click();
  await expect(page.getByText("See running tasks, completed work, and anything that needs your attention.", { exact: true })).toHaveCount(0);
  for (const [role, text] of [["worker", workerEvent.details.text], ["reviewer", reviewerEvent.details.text]]) {
    const pane = page.getByRole("region", { name: role + " agent 会话", exact: true });
    await expect(pane.getByText("人工介入 · 1", { exact: true })).toBeVisible({ timeout: 10000 });
    await pane.getByText("查看人工介入记录", { exact: true }).click();
    await expect(pane.getByText(text, { exact: false })).toBeVisible();
  }
  await expect(page.getByRole("region", { name: "worker agent 会话" }).getByText(historical.attempt_id, { exact: false })).toBeVisible();
  after = await status();
  expect(before.task.state).toBe("accepted");
  expect(after.task).toEqual(before.task);
  await page.mouse.move(1550, 950);
  await page.waitForTimeout(1200);
} catch (error) { failure = String(error); }
finally {
  await page.screenshot({ path: join(root, label + ".png"), fullPage: true });
  writeFileSync(join(root, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), fixture: true,
    claim: "T-037 protocol fixture only; no real human-input producer or model turn", fixtureEvents,
    requests, before, after, failure, text: await page.locator("body").innerText() }, null, 2) + "\n", "utf8");
  await browser.close();
}
if (failure) throw new Error(failure);
