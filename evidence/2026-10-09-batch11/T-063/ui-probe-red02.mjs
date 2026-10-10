import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
const fork = "/Users/luckye/Documents/Code/synara";
const { chromium } = createRequire(join(fork, "apps/web/package.json"))("playwright/test");
const [out, root, label, mode = "normal"] = process.argv.slice(2);
if (existsSync(join(out, label + ".json"))) throw new Error("Evidence label exists");
const seed = JSON.parse(readFileSync(join(root, "seed.json"), "utf8"));
const web = JSON.parse(readFileSync(join(root, "web-ready.json"), "utf8")).origin;
const profile = join(root, "browser-" + label);
const options = {
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true,
  viewport: { width: 1600, height: 1050 }, reducedMotion: "reduce", colorScheme: "light",
};
const records = [], failures = [];
const revision = execFileSync("git", ["-C", fork, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
const diff = execFileSync("git", ["-C", fork, "diff", "HEAD"], { encoding: "utf8" });
let context, page;
function urlPath(url) { const u = new URL(url); return u.origin + u.pathname; }
async function start(stage, extra = {}) {
  context = await chromium.launchPersistentContext(profile, { ...options, ...extra });
  page = await context.newPage();
  const record = { stage, start: new Date().toISOString(), pending: [], errors: [], console: [], failed: [], websockets: [] };
  records.push(record);
  const pending = new Map();
  page.on("request", r => pending.set(r, { url: urlPath(r.url()), type: r.resourceType(), at: Date.now() }));
  page.on("requestfinished", r => pending.delete(r));
  page.on("requestfailed", r => { pending.delete(r); record.failed.push({ url: urlPath(r.url()), error: r.failure() }); });
  page.on("pageerror", e => record.errors.push(String(e)));
  page.on("console", m => { if (m.type() === "error" || m.type() === "warning") record.console.push(m.text()); });
  page.on("websocket", ws => { const item = { url: urlPath(ws.url()), opened: Date.now(), received: 0 }; record.websockets.push(item); ws.on("framereceived", () => item.received++); ws.on("close", () => item.closed = Date.now()); });
  const began = Date.now();
  await page.goto(web + "/a2a", { waitUntil: "domcontentloaded" });
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  for (let i = 0; i < 12; i++) {
    try { await main.waitFor({ timeout: 5000 }); break; } catch {
      record.pending.push({ elapsedMs: Date.now() - began, boot: await page.locator(".app-boot-splash").count(), text: await page.locator("body").innerText(), requests: [...pending.values()].map(r => ({ ...r, ageMs: Date.now() - r.at })) });
      if (i === 1) await page.screenshot({ path: join(out, `${label}-${stage}-10s.png`) });
    }
  }
  record.mainVisible = await main.isVisible();
  record.mainElapsedMs = Date.now() - began;
  if (!record.mainVisible) failures.push(`${stage}: no main UI within 60 seconds`);
  await page.screenshot({ path: join(out, `${label}-${stage}.png`) });
  return record.mainVisible;
}
async function geometry(stage) {
  const heading = page.getByTestId("empty-landing-heading");
  await heading.waitFor({ timeout: 15000 });
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const record = await heading.evaluate(node => {
    const hero = node.parentElement;
    const logo = hero.querySelector('svg[aria-label="Synara logo"]');
    const banner = document.querySelector('[data-testid="project-import-landing-banner"]');
    const editor = document.querySelector('[contenteditable="true"][role="textbox"]');
    const rect = n => { const r = n.getBoundingClientRect(); return { left:r.left, top:r.top, right:r.right, bottom:r.bottom, width:r.width, height:r.height }; };
    const area = (a,b) => Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left)) * Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
    const h = rect(node), l = rect(logo), b = banner ? rect(banner) : null, e = editor ? rect(editor) : null;
    const visible = r => r.width > 0 && r.height > 0;
    return { headingText:node.textContent, heading:h, logo:l, banner:b, editor:e,
      overlaps:{ bannerLogo:b && visible(b) ? area(b,l) : 0, bannerHeading:b && visible(b) ? area(b,h) : 0, headingEditor:e ? area(h,e) : 0 },
      logoAboveHeading:l.bottom <= h.top, headingAboveEditor:e ? h.bottom <= e.top : false };
  });
  record.stage = stage;
  record.viewport = page.viewportSize();
  records.push(record);
  await page.screenshot({ path: join(out, `${label}-${stage}.png`) });
  if (Object.values(record.overlaps).some(n => n > 0) || !record.logoAboveHeading || !record.headingAboveEditor) failures.push(`${stage}: empty landing overlaps`);
}
try {
  if (await start("fresh")) {
    await page.getByRole("button", { name: "Not now", exact: true }).click({ timeout: 30000 });
    await page.getByRole("button", { name: "Skip tour", exact: true }).click({ timeout: 30000 });
    const main = page.getByRole("main", { name: "任务窗口", exact: true });
    await main.getByRole("button", { name: "T057 问题面板", exact: true }).click();
    const panel = main.locator(`[data-a2a-pane='${seed.dispatched.attempt.thread_id}']`).getByRole("complementary", { name: "问题上报", exact: true });
    await panel.locator("article").nth(2).waitFor();
    await page.getByText("See running tasks, completed work, and anything that needs your attention.", { exact:true }).waitFor({ state:"hidden", timeout:15000 });
    await geometry("1600x1050");
    await page.setViewportSize({ width:1280, height:900 });
    await geometry("1280x900");
    await page.setViewportSize(options.viewport);
    await geometry("resized-back");
    records.push({ stage:"storage-before-close", values:await page.evaluate(() => Object.fromEntries(Object.entries(localStorage).filter(([key]) => key.includes("tour") || key.includes("onboarding") || key.includes("announcement")))) });
  }
  await context.close();
  if (mode === "corrupt") {
    // Corrupt only three presentation markers in our own acceptance profile.
    context = await chromium.launchPersistentContext(profile, options);
    page = await context.newPage();
    await page.goto(web + "/a2a", { waitUntil:"domcontentloaded" });
    await page.evaluate(() => { for (const key of ["synara:feature-tour:since-0.9.2:v1", "synara:project-import-announcement:v1", "synara:activity-onboarding:v1"]) localStorage.setItem(key, "{invalid-json"); });
    await context.close();
  }
  await start("reopened");
  await context.close();
} catch (error) {
  failures.push(String(error.stack ?? error));
  if (page && !page.isClosed()) await page.screenshot({ path:join(out,label+"-failure.png") });
} finally {
  if (context) await context.close();
  writeFileSync(join(out,label+".json"), JSON.stringify({ argv:process.argv.slice(1), profile, fork:revision, diff, mode, modelCalls:0, records, failures },null,2)+"\n", {flag:"wx"});
}
console.log(JSON.stringify({label,failures,records:records.map(r => ({ stage:r.stage, mainVisible:r.mainVisible,mainElapsedMs:r.mainElapsedMs, overlaps:r.overlaps }))},null,2));
if (failures.length) process.exitCode = 1;
