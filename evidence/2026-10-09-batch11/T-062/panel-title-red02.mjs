import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out, root, label] = process.argv.slice(2);
if (existsSync(join(out, label + ".json"))) throw new Error("Evidence label exists");
const seed = JSON.parse(readFileSync(join(root, "seed.json"), "utf8"));
const web = JSON.parse(readFileSync(join(root, "web-ready.json"), "utf8")).origin;
const profile = join(root, "browser-" + label);
const coachmark = "See running tasks, completed work, and anything that needs your attention.";
const activityKey = "synara:activity-onboarding:v1";
const forkRevision = execFileSync("git", ["-C", "/Users/luckye/Documents/Code/synara", "rev-parse", "HEAD"], { encoding:"utf8" }).trim();
const context = await chromium.launchPersistentContext(profile, {
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true,
  viewport: { width: 1600, height: 1050 }, reducedMotion: "reduce", colorScheme: "light",
});
const page = await context.newPage();
const observations = [], diagnostics = [];
page.on("pageerror", (error) => diagnostics.push(String(error)));
const main = page.getByRole("main", { name: "任务窗口", exact: true });
const panel = main.locator(`[data-a2a-pane='${seed.dispatched.attempt.thread_id}']`)
  .getByRole("complementary", { name: "问题上报", exact: true });
const title = panel.getByRole("heading", { name: "问题上报", exact: true });
async function openPanel() {
  await main.waitFor({ timeout: 60000 });
  await main.getByRole("button", { name: "T057 问题面板", exact: true }).click({ timeout: 30000 });
  await expect(panel.locator("article")).toHaveCount(3, { timeout: 30000 });
  await expect(panel.getByRole("heading", { name: "问题 1：oracle 漏了空页", exact: true })).toBeVisible();
}
async function observe(stage) {
  const record = await title.evaluate((node) => {
    const b = node.getBoundingClientRect();
    const points = [.05,.5,.95].map((ratio) => {
      const x = b.left + b.width*ratio, y = b.top+b.height/2;
      const hit = document.elementFromPoint(x,y);
      return { x, y, visible: hit === node || node.contains(hit), hit: hit?.outerHTML.slice(0,400) };
    });
    const rect = (r) => ({ left:r.left, top:r.top, right:r.right, bottom:r.bottom });
    const overlaps = [...document.querySelectorAll('[data-slot="tooltip-popup"]')].flatMap((popup) => {
      const r = popup.getBoundingClientRect();
      const style = getComputedStyle(popup);
      if (style.visibility === "hidden" || style.display === "none" || Number(style.opacity) === 0) return [];
      const width = Math.max(0,Math.min(b.right,r.right)-Math.max(b.left,r.left));
      const height = Math.max(0,Math.min(b.bottom,r.bottom)-Math.max(b.top,r.top));
      return width*height > 0 ? [{ text:popup.textContent, rect:rect(r), area:width*height }] : [];
    });
    return { title:node.textContent, rect:rect(b), points, overlaps };
  });
  record.stage = stage;
  record.at = new Date().toISOString();
  record.activitySeen = await page.evaluate((key) => localStorage.getItem(key),activityKey);
  record.coachmarkVisible = await page.getByText(coachmark, { exact:true }).isVisible();
  observations.push(record);
  await page.screenshot({ path:join(out,label+"-"+stage+".png") });
  return record;
}
function assertClear(record) {
  // Ticket oracle: the heading itself must be unobstructed, independent of product constants.
  expect(record.overlaps, "No tooltip may overlap the 问题上报 heading").toEqual([]);
  expect(record.points.every((point) => point.visible), "Heading hit targets are unobstructed").toBe(true);
}
let failure;
try {
  await page.goto(web+"/a2a");
  await main.waitFor({ timeout:60000 });
  await page.getByRole("button", { name:"Not now", exact:true }).click({ timeout:30000 });
  await page.getByRole("button", { name:"Skip tour", exact:true }).click({ timeout:30000 });
  await page.getByText(coachmark, { exact:true }).waitFor({ state:"visible", timeout:15000 });
  await openPanel();
  const initial = await observe("initial");
  // Diagnostic probe before a fixture correction: let the product close its own hint.
  await page.getByText(coachmark, { exact:true }).waitFor({ state:"hidden", timeout:15000 });
  assertClear(await observe("expired"));
  await page.reload();
  await openPanel();
  assertClear(await observe("reload"));
  assertClear(initial);
} catch (error) {
  failure = String(error.stack ?? error);
  await page.screenshot({ path:join(out,label+"-failure.png") });
  writeFileSync(join(out,label+"-failure.txt"),await page.locator("body").innerText(),{flag:"wx"});
} finally {
  writeFileSync(join(out,label+".json"),JSON.stringify({argv:process.argv.slice(1),profile,
    fork:forkRevision,failure,observations,diagnostics},null,2)+"\n",{flag:"wx"});
  await context.close();
}
if (failure) throw new Error(failure);
