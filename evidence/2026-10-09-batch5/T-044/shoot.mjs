// Real dev UI only: no response overrides, membership edits, or model calls.
import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const {chromium, expect} = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const root = dirname(fileURLToPath(import.meta.url));
const [label, fixturePath, ended] = process.argv.slice(2);
if (existsSync(join(root, label + ".json"))) throw new Error("Evidence label exists");
const fixture = JSON.parse(readFileSync(fixturePath, "utf8"));
const browser = await chromium.launch({executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: false});
const context = await browser.newContext({viewport: {width: 1600, height: 1000}, reducedMotion: "reduce", colorScheme: "light"});
const page = await context.newPage();
const diagnostics = [];
page.on('pageerror', error => diagnostics.push({type: 'pageerror', message: String(error)}));
page.on('console', message => { if (message.type() === 'error') diagnostics.push({type: 'console-error', message: message.text()}); });
page.on('requestfailed', request => diagnostics.push({type: 'requestfailed', url: request.url(), error: request.failure()}));
let failure, structure;
try {
  await page.goto("http://localhost:7777/a2a");
  await page.getByRole("button", {name: "Not now", exact: true}).click({timeout: 20000}).catch(() => {});
  await page.getByRole("button", {name: "Skip tour", exact: true}).click({timeout: 3000}).catch(() => {});
  const main = page.getByRole("main", {name: "任务窗口", exact: true});
  await main.getByRole("button", {name: fixture.title, exact: true}).click({timeout: 30000});
  await expect(main.locator("section[aria-label$='agent 会话']")).toHaveCount(2, {timeout: 30000});
  await expect(main.locator("section[aria-label='worker agent 会话']")).toBeVisible();
  await expect(main.locator("section[aria-label='reviewer agent 会话']")).toBeVisible();
  if (ended === "ended") await expect(main.locator("section[data-a2a-ended='true']")).toHaveCount(2);
  await page.waitForTimeout(1500);
  structure = await main.locator("section[aria-label$='agent 会话']").evaluateAll(nodes => nodes.map(n => ({
    role: n.getAttribute("aria-label"), thread: n.getAttribute("data-a2a-pane"), ended: n.getAttribute("data-a2a-ended"),
    opacity: getComputedStyle(n).opacity, header: n.querySelector("header")?.innerText, text: n.innerText,
  })));
  await page.screenshot({path: join(root, label + ".png")});
} catch (error) { failure = String(error.stack ?? error); await page.screenshot({path: join(root, label + "-failure.png")}).catch(() => {}); }
finally {
  writeFileSync(join(root, label + ".json"), JSON.stringify({argv: process.argv.slice(1), fixturePath, ended, failure, structure, diagnostics,
    text: await page.locator("body").innerText().catch(() => "")}, null, 2) + "\n");
  await browser.close();
}
if (failure) throw new Error(failure);
