// Real dev UI, fresh profile per size/theme, screenshot while the first-use hint is visible.
import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
const fork = "/Users/luckye/Documents/Code/synara";
const { chromium, expect } = createRequire(join(fork, "apps/web/package.json"))("playwright/test");
const [out, root, label] = process.argv.slice(2);
if (existsSync(join(out, label + ".json"))) throw new Error("Evidence label exists");
const seed = JSON.parse(readFileSync(join(root, "seed.json"), "utf8"));
const web = JSON.parse(readFileSync(join(root, "web-ready.json"), "utf8")).origin;
const coachmark = "See running tasks, completed work, and anything that needs your attention.";
const activityKey = "synara:activity-onboarding:v1";
const revision = execFileSync("git", ["-C", fork, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
const diff = execFileSync("git", ["-C", fork, "diff", "HEAD", "--", "apps/web/src/components/Sidebar.tsx"], { encoding: "utf8" });
const observations = [];
for (const colorScheme of ["light", "dark"]) {
  for (const viewport of [{ width: 1600, height: 1050 }, { width: 1280, height: 900 }]) {
    const name = `${colorScheme}-${viewport.width}x${viewport.height}`;
    const profile = join(root, `browser-${label}-${name}`);
    if (existsSync(profile)) throw new Error("Profile already exists: " + profile);
    const record = { name, profile, viewport, colorScheme, diagnostics: [], failures: [] };
    observations.push(record);
    const context = await chromium.launchPersistentContext(profile, {
      executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true,
      viewport, reducedMotion: "reduce", colorScheme,
    });
    const page = await context.newPage();
    page.on("pageerror", error => record.diagnostics.push(String(error)));
    try {
      await page.goto(web + "/a2a");
      const main = page.getByRole("main", { name: "任务窗口", exact: true });
      await main.waitFor({ timeout: 60000 });
      record.freshStorage = await page.evaluate(key => localStorage.getItem(key), activityKey);
      expect(record.freshStorage, "New profile has never seen Activity").toBeNull();
      await page.getByRole("button", { name: "Not now", exact: true }).click({ timeout: 30000 });
      await page.getByRole("button", { name: "Skip tour", exact: true }).click({ timeout: 30000 });
      const hint = page.getByText(coachmark, { exact: true });
      await hint.waitFor({ state: "visible", timeout: 15000 });
      record.hintFirstObservedAt = new Date().toISOString();
      await main.getByRole("button", { name: "T057 问题面板", exact: true }).click({ timeout: 30000 });
      const panel = main.locator(`[data-a2a-pane='${seed.dispatched.attempt.thread_id}']`)
        .getByRole("complementary", { name: "问题上报", exact: true });
      await expect(panel.locator("article")).toHaveCount(3, { timeout: 30000 });
      await expect(panel.getByRole("heading", { name: "问题 1：oracle 漏了空页", exact: true })).toBeVisible();
      const title = panel.getByRole("heading", { name: "问题上报", exact: true });
      record.geometry = await title.evaluate(node => {
        const titleRect = node.getBoundingClientRect();
        const main = node.closest("main");
        const mainRect = main.getBoundingClientRect();
        const rect = r => ({ left: r.left, top: r.top, right: r.right, bottom: r.bottom });
        const area = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) *
          Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
        const popups = [...document.querySelectorAll('[data-slot="tooltip-popup"]')].flatMap(popup => {
          const style = getComputedStyle(popup), r = popup.getBoundingClientRect();
          if (style.visibility === "hidden" || style.display === "none" || Number(style.opacity) === 0) return [];
          return [{ text: popup.textContent, rect: rect(r), titleOverlap: area(r, titleRect), mainOverlap: area(r, mainRect) }];
        });
        const points = [.05, .5, .95].map(ratio => {
          const x = titleRect.left + titleRect.width * ratio, y = titleRect.top + titleRect.height / 2;
          const hit = document.elementFromPoint(x, y);
          return { x, y, visible: hit === node || node.contains(hit), hit: hit?.outerHTML.slice(0, 300) };
        });
        return { title: rect(titleRect), main: rect(mainRect), popups, points };
      });
      record.colors = await hint.evaluate(node => {
        const popup = node.closest('[data-slot="tooltip-popup"]');
        const canvas = document.createElement("canvas");
        canvas.width = canvas.height = 1;
        const ctx = canvas.getContext("2d");
        const rgba = css => {
          ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = css; ctx.fillRect(0, 0, 1, 1);
          return [...ctx.getImageData(0, 0, 1, 1).data];
        };
        const popupStyle = getComputedStyle(popup);
        const backgroundCss = popupStyle.backgroundColor;
        const backgroundImage = popupStyle.backgroundImage;
        const color = element => {
          const css = getComputedStyle(element).color;
          return { css, rgba: rgba(css) };
        };
        return { theme: document.documentElement.dataset.themeVariant, backgroundCss, backgroundImage,
          title: color(popup.querySelector('.font-semibold')), body: color(node) };
      });
      await expect(hint, "Hint is visible immediately before capture").toBeVisible();
      record.captureStartedAt = new Date().toISOString();
      const screenshot = await page.screenshot({ path: join(out, `${label}-${name}.png`) });
      record.captureFinishedAt = new Date().toISOString();
      record.hintVisibleAfterCapture = await hint.isVisible();
      // Decode the actual PNG in the browser; sample the hint's blank lower inset.
      // This includes gradient fills, opacity and the real page behind the popup.
      const popup = record.geometry.popups.find(p => p.text.includes(coachmark));
      record.colors.background = await page.evaluate(async ({ png, rect }) => {
        const img = new Image();
        img.src = "data:image/png;base64," + png;
        await img.decode();
        const canvas = document.createElement("canvas");
        canvas.width = img.width; canvas.height = img.height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);
        return [...ctx.getImageData(Math.floor((rect.left + rect.right) / 2), Math.floor(rect.bottom - 5), 1, 1).data].slice(0, 3);
      }, { png: screenshot.toString("base64"), rect: popup.rect });
      const luminance = rgb => rgb.map(value => value / 255)
        .map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4)
        .reduce((total, value, i) => total + value * [.2126, .7152, .0722][i], 0);
      for (const text of [record.colors.title, record.colors.body]) {
        const background = record.colors.background;
        text.foreground = text.rgba.slice(0, 3).map((value, i) => value * text.rgba[3] / 255 + background[i] * (1 - text.rgba[3] / 255));
        const a = luminance(text.foreground), b = luminance(background);
        text.ratio = (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
      }
      // Acceptance oracle comes from the ticket, independently of production layout values.
      for (const [description, assertion] of [
        ["Hint remains present during screenshot", () => expect(record.hintVisibleAfterCapture).toBe(true)],
        ["Theme matches requested light/dark mode", () => expect(record.colors.theme).toBe(colorScheme)],
        ["No tooltip overlaps the panel heading", () => expect(record.geometry.popups.every(p => p.titleOverlap === 0)).toBe(true)],
        ["Title hit targets are clear", () => expect(record.geometry.points.every(p => p.visible)).toBe(true)],
        ["Hint stays outside the task window", () => expect(record.geometry.popups.every(p => p.mainOverlap === 0)).toBe(true)],
        ["Title is readable (contrast >= 4.5)", () => expect(record.colors.title.ratio).toBeGreaterThanOrEqual(4.5)],
        ["Body is readable (contrast >= 4.5)", () => expect(record.colors.body.ratio).toBeGreaterThanOrEqual(4.5)],
      ]) {
        try { assertion(); } catch (error) { record.failures.push({ description, error: String(error) }); }
      }
    } catch (error) {
      record.failures.push({ description: "UI setup/capture", error: String(error.stack ?? error) });
      await page.screenshot({ path: join(out, `${label}-${name}-failure.png`) });
      writeFileSync(join(out, `${label}-${name}-failure.txt`), await page.locator("body").innerText(), { flag: "wx" });
    } finally {
      await context.close();
    }
  }
}
const failure = observations.some(record => record.failures.length > 0);
writeFileSync(join(out, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), fork: revision,
  sidebarDiff: diff, modelCalls: 0, failure, observations }, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify(observations.map(({ name, failures, colors, hintVisibleAfterCapture }) =>
  ({ name, failures, colors, hintVisibleAfterCapture })), null, 2));
if (failure) process.exitCode = 1;
