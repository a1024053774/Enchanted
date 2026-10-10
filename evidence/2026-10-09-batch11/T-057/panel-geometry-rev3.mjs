import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out, root, label] = process.argv.slice(2);
if (existsSync(join(out, label + ".json"))) throw new Error("Evidence exists");
const seed = JSON.parse(readFileSync(join(root, "seed.json"), "utf8"));
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1050 }, reducedMotion: "reduce", colorScheme: "light" });
const geometry = []; let failure;
await page.addLocatorHandler(page.getByRole("button", { name: "Not now", exact: true }), button => button.click());
await page.addLocatorHandler(page.getByRole("button", { name: "Skip tour", exact: true }), button => button.click());
try {
  await page.goto("http://localhost:7968/a2a", { waitUntil: "domcontentloaded" });
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  await main.waitFor({ timeout: 60000 });
  await main.getByRole("button", { name: "T057 问题面板", exact: true }).click();
  const panel = main.locator(`[data-a2a-pane='${seed.dispatched.attempt.thread_id}']`).getByRole("complementary", { name: "问题上报", exact: true });
  const articles = panel.locator("article");
  await expect(articles).toHaveCount(6);
  for (const article of await articles.all()) await article.getByRole("textbox").fill("几何测试答复 Ω");
  for (const size of [{ width: 1600, height: 1050 }, { width: 1280, height: 900 }]) {
    await page.setViewportSize(size);
    // Role queries omit descendants skipped by content-visibility while
    // scrolled away. Select every form's submit before scrolling each into view.
    const singles = panel.locator('article form > button[type="submit"]');
    await expect(singles).toHaveCount(6);
    const buttons = [...await singles.all(), panel.getByRole("button", { name: "打包发送（6）", exact: true })];
    for (let index = 0; index < buttons.length; index++) {
      const button = buttons[index];
      await button.scrollIntoViewIfNeeded();
      await button.click({ trial: true });
      const rect = await button.evaluate(node => {
        const b = node.getBoundingClientRect();
        const clip = (node.closest("[data-a2a-issue-list]") ?? node.closest("aside")).getBoundingClientRect();
        const hit = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
        return { top: b.top, bottom: b.bottom, left: b.left, right: b.right, clipTop: clip.top, clipBottom: clip.bottom, viewportHeight: innerHeight, viewportWidth: innerWidth, centerHit: hit === node || node.contains(hit) };
      });
      expect(rect.top).toBeGreaterThanOrEqual(Math.max(0, rect.clipTop) - 1);
      expect(rect.bottom).toBeLessThanOrEqual(Math.min(rect.viewportHeight, rect.clipBottom) + 1);
      expect(rect.left).toBeGreaterThanOrEqual(0);
      expect(rect.right).toBeLessThanOrEqual(rect.viewportWidth);
      expect(rect.centerHit).toBe(true);
      const image = `${label}-${size.width}x${size.height}-${index + 1}.png`;
      await page.screenshot({ path: join(out, image) });
      geometry.push({ size, index, rect, image });
    }
  }
} catch (error) { failure = String(error.stack ?? error); }
finally {
  writeFileSync(join(out, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), failure, geometry, click_trial_only: true }, null, 2) + "\n");
  await browser.close();
}
if (failure) throw new Error(failure);
