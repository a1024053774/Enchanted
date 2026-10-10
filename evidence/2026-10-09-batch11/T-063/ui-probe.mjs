import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
const fork = "/Users/luckye/Documents/Code/synara";
const { chromium, expect } = createRequire(join(fork, "apps/web/package.json"))("playwright/test");
const [out, root, label, mode = "normal", profileName] = process.argv.slice(2);
if (existsSync(join(out, label + ".json"))) throw new Error("Evidence label exists");
const seed = JSON.parse(readFileSync(join(root, "seed.json"), "utf8"));
const web = JSON.parse(readFileSync(join(root, "web-ready.json"), "utf8")).origin;
const profile = join(root, profileName ?? "browser-" + label);
const options = {
  executablePath: process.env.T063_BROWSER_BINARY ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true,
  viewport: { width: 1600, height: 1050 }, reducedMotion: "reduce", colorScheme: "light",
};
const records = [], failures = [];
const revision = execFileSync("git", ["-C", fork, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
const diff = execFileSync("git", ["-C", fork, "diff", "HEAD"], { encoding: "utf8" });
let context, page;
function urlPath(url) { const u = new URL(url); return u.origin + u.pathname; }
async function start(stage, extra = {}) {
  context = await chromium.launchPersistentContext(profile, { ...options, ...extra });
  page = context.pages()[0];
  const record = { stage, start: new Date().toISOString(), binary:options.executablePath, httpCacheDisabled:mode !== "normal-cached" && mode !== "resume-cached", pending: [], errors: [], console: [], failed: [], websockets: [] };
  // Vite's raw module graph and this fixture's HDD-backed Chrome cache are the
  // diagnostic boundary. Preserve the profile and all product storage.
  const cdp = await context.newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.setCacheDisabled", {cacheDisabled:record.httpCacheDisabled});
  records.push(record);
  const pending = new Map();
  page.on("request", r => pending.set(r, { url: urlPath(r.url()), type: r.resourceType(), at: Date.now() }));
  page.on("requestfinished", r => pending.delete(r));
  page.on("requestfailed", r => { pending.delete(r); record.failed.push({ url: urlPath(r.url()), error: r.failure() }); });
  page.on("pageerror", e => record.errors.push(String(e)));
  page.on("console", m => { if (m.type() === "error" || m.type() === "warning") record.console.push(m.text()); });
  page.on("websocket", ws => { const item = { url: urlPath(ws.url()), opened: Date.now(), received: 0 }; record.websockets.push(item); ws.on("framereceived", () => item.received++); ws.on("close", () => item.closed = Date.now()); });
  const began = Date.now();
  await page.goto(web + "/a2a", { waitUntil: "domcontentloaded", timeout:60000 });
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  for (let i = 0; i < 12; i++) {
    try { await main.waitFor({ timeout: 5000 }); break; } catch (error) {
      record.pending.push({ elapsedMs: Date.now() - began, boot: await page.locator(".app-boot-splash").count(), text: await page.locator("body").innerText(), requests: [...pending.values()].map(r => ({ ...r, ageMs: Date.now() - r.at })) });
      if (i === 1) await page.screenshot({ path: join(out, `${label}-${stage}-10s.png`) });
      if (page.isClosed()) throw error;
    }
  }
  record.mainVisible = await main.isVisible();
  record.mainElapsedMs = Date.now() - began;
  if (!record.mainVisible) failures.push(`${stage}: no main UI within 60 seconds`);
  if (record.mainVisible && stage === "reopened") {
    const pane = main.locator(`[data-a2a-pane='${seed.dispatched.attempt.thread_id}']`);
    await pane.getByRole("heading", {name:"问题 1：oracle 漏了空页",exact:true}).waitFor({timeout:30000});
    await pane.getByTestId("empty-landing-heading").waitFor({timeout:30000});
    for (const title of ["问题 1：oracle 漏了空页", "问题 3：README 的构建命令已过期", "问题 4：长正文哨兵"])
      await expect(pane.getByRole("heading", {name:title,exact:true})).toBeVisible({timeout:30000});
    record.hydratedElapsedMs = Date.now() - began;
    record.articleCount = await pane.locator("article").count();
    record.hydrated = true;
    record.projectText = await pane.getByTestId("empty-landing-heading").innerText();
    if (!record.hydrated || record.hydratedElapsedMs > 60000) failures.push(`${stage}: task hydration did not complete within 60 seconds`);
  }
  await page.screenshot({ path: join(out, `${label}-${stage}.png`) });
  return record.mainVisible;
}
async function geometry(stage) {
  const heading = page.getByTestId("empty-landing-heading");
  await heading.waitFor({ timeout: 15000 });
  await heading.evaluate(node => { const landing=node.closest(".chat-pane-enter"); landing.scrollTop=0; });
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const record = await heading.evaluate(node => {
    const hero = node.parentElement;
    const logo = hero.querySelector('svg[aria-label="Synara logo"]');
    const banner = document.querySelector('[data-testid="project-import-landing-banner"]');
    const editor = document.querySelector('[data-empty-landing-composer-block="true"]');
    const landing = node.closest(".chat-pane-enter");
    const rect = n => { const r = n.getBoundingClientRect(); return { left:r.left, top:r.top, right:r.right, bottom:r.bottom, width:r.width, height:r.height }; };
    const area = (a,b) => Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left)) * Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
    const h = rect(node), l = rect(logo), b = banner ? rect(banner) : null, e = editor ? rect(editor) : null;
    const visible = r => r.width > 0 && r.height > 0;
    return { headingText:node.textContent, heading:h, logo:l, banner:b, editor:e, landing:rect(landing), scrollHeight:landing.scrollHeight, clientHeight:landing.clientHeight,
      overlaps:{ bannerLogo:b && visible(b) ? area(b,l) : 0, bannerHeading:b && visible(b) ? area(b,h) : 0, headingEditor:e ? area(h,e) : 0 },
      logoAboveHeading:l.bottom <= h.top, headingAboveEditor:e ? h.bottom <= e.top : false };
  });
  record.stage = stage;
  record.viewport = page.viewportSize();
  records.push(record);
  await page.screenshot({ path: join(out, `${label}-${stage}.png`) });
  if (Object.values(record.overlaps).some(n => n > 0) || !record.logoAboveHeading || !record.headingAboveEditor) failures.push(`${stage}: empty landing overlaps`);
  // A hidden or clipped hero cannot satisfy the no-overlap oracle alone.
  await heading.evaluate(node => {
    const landing=node.closest(".chat-pane-enter"), h=node.getBoundingClientRect(), r=landing.getBoundingClientRect();
    // Scroll only as far as needed to reveal the heading; preserve its preceding logo.
    landing.scrollTop += Math.ceil(Math.max(0,h.bottom-r.bottom));
  });
  await page.screenshot({path:join(out,`${label}-${stage}-hero.png`)});
  const visibleHero = await heading.evaluate(node => {
    const landing=node.closest(".chat-pane-enter").getBoundingClientRect();
    const h=node.getBoundingClientRect(), l=node.parentElement.querySelector('svg[aria-label="Synara logo"]').getBoundingClientRect();
    return h.top >= landing.top && h.bottom <= landing.bottom && l.top >= landing.top && l.bottom <= landing.bottom;
  });
  record.heroReachable = visibleHero;
  if (!visibleHero) failures.push(`${stage}: hero is clipped after scrolling`);
  const composer = page.locator('[data-empty-landing-composer-block="true"]');
  await composer.scrollIntoViewIfNeeded();
  record.composerReachable = await composer.evaluate(node => { const r=node.getBoundingClientRect(), p=node.closest(".chat-pane-enter").getBoundingClientRect();return r.top>=p.top && r.bottom<=p.bottom; });
  if (!record.composerReachable) failures.push(`${stage}: composer is clipped after scrolling`);
  await page.screenshot({path:join(out,`${label}-${stage}-composer.png`)});
}
async function longCopy() {
  await page.getByTestId("project-import-landing-banner").evaluate(node => {
    const text=node.lastElementChild;
    text.firstElementChild.textContent="导入你在 Claude Code 和 Codex 中的项目、历史对话与开发工作记录，以便继续当前的协作";
    text.lastElementChild.textContent="将已有项目和历史记录带到 Synara 中继续处理。";
  });
  await page.getByTestId("empty-landing-heading").evaluate(node => node.textContent="我们接下来要在这个名称较长的协作项目中完成哪一项工作？");
  await page.setViewportSize({width:1280,height:900});
  await geometry("long-copy-1280x900");
}
try {
  if (mode === "resume" || mode === "resume-cached") {
    if (await start("reopened")) {
      await geometry("1600x1050");
      await page.setViewportSize({width:1280,height:900});
      await geometry("1280x900");
      await page.setViewportSize(options.viewport);
      await geometry("resized-back");
      await longCopy();
    }
  } else {
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
    // Stress presentation with longer translated copy; the product has no locale
    // switch. This is a layout-only probe, not an assertion of runtime translation.
    await longCopy();
    records.push({ stage:"storage-before-close", values:await page.evaluate(() => Object.fromEntries(Object.entries(localStorage).filter(([key]) => key.includes("tour") || key.includes("onboarding") || key.includes("announcement")))) });
  }
  await context.close();
  if (mode === "corrupt") {
    // Corrupt only three presentation markers in our own acceptance profile.
    context = await chromium.launchPersistentContext(profile, options);
    page = context.pages()[0];
    const cdp=await context.newCDPSession(page);
    await cdp.send("Network.enable");
    await cdp.send("Network.setCacheDisabled",{cacheDisabled:true});
    await page.goto(web + "/a2a", { waitUntil:"domcontentloaded" });
    await page.evaluate(() => { for (const key of ["synara:feature-tour:since-0.9.2:v1", "synara:project-import-announcement:v1", "synara:activity-onboarding:v1"]) localStorage.setItem(key, "{invalid-json"); });
    records.push({stage:"corrupt-markers-before-close", values:await page.evaluate(() => Object.fromEntries(Object.entries(localStorage).filter(([key]) => key.includes("tour") || key.includes("onboarding") || key.includes("announcement"))))});
    await context.close();
  }
  if (await start("reopened")) await geometry("reopened-1600x1050");
  await context.close();
  }
} catch (error) {
  failures.push(String(error.stack ?? error));
  if (page && !page.isClosed()) await page.screenshot({ path:join(out,label+"-failure.png") });
} finally {
  if (context) await context.close();
  writeFileSync(join(out,label+".json"), JSON.stringify({ argv:process.argv.slice(1), profile, fork:revision, diff, mode, modelCalls:0, records, failures },null,2)+"\n", {flag:"wx"});
}
console.log(JSON.stringify({label,failures,records:records.map(r => ({ stage:r.stage, mainVisible:r.mainVisible,mainElapsedMs:r.mainElapsedMs, overlaps:r.overlaps }))},null,2));
if (failures.length) process.exitCode = 1;
