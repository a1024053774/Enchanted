import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const { _electron, expect } = createRequire("/Users/luckye/Documents/Code/synara-t038/apps/web/package.json")("playwright/test");
const root = dirname(fileURLToPath(import.meta.url)), label = process.argv[2];
const checkout = "/Users/luckye/Documents/Code/synara-t038", candidate = "ad13b72c5faeb5fb601c3d40b7090d746f4f2758";
if (!label || existsSync(join(root, label + ".json"))) throw new Error("New evidence label required");
const revision = () => execFileSync("git", ["rev-parse", "HEAD"], { cwd: checkout, encoding: "utf8" }).trim();
if (revision() !== candidate) throw new Error("Frozen candidate changed");
const dataRoot = "/Volumes/WD-Elements/dev-cache/synara/instances/t038/desktop-home";
const profile = "/Volumes/WD-Elements/dev-cache/synara/instances/t038/electron-final/" + label;
mkdirSync(profile, { recursive: true });
const clean = text => String(text).replace(/([?&]token=)[^&\s"']+/g, "$1<redacted>").replace(/Bearer\s+[\w.-]+/gi, "Bearer <redacted>");
const launch = {
  executablePath: "/Volumes/WD-Elements/dev-cache/synara/instances/t038/tools/electron-43.4.1/Electron.app/Contents/MacOS/Electron",
  args: [join(checkout, "apps/desktop/dist-electron/main.js")], cwd: join(checkout, "apps/desktop"), timeout: 60000,
  env: { ...process.env, SYNARA_HOME: dataRoot, SYNARA_DESKTOP_SMOKE_USER_DATA: profile, SYNARA_DESKTOP_FLAVOR: "cua",
    SYNARA_SOURCE_DESKTOP_BUILD_MARKER: "synara-source-desktop-build-v2", SYNARA_DISABLE_AUTO_UPDATE: "1", VITE_DEV_SERVER_URL: "http://localhost:7771/" },
};
let app, page, identity, failure, stage = "launch", observation, cleanup;
const errors = [], requests = [], screenshots = [];
const started = Date.now();
try {
  app = await _electron.launch(launch);
  identity = await app.evaluate(({ app }) => ({ userData: app.getPath("userData"), appPath: app.getAppPath(), version: process.versions.electron }));
  if (identity.userData !== profile || !identity.appPath.startsWith(checkout + "/")) throw new Error("Incorrect desktop isolation");
  await expect.poll(() => app.windows().some(window => window.url().startsWith("http://localhost:7771/")), { timeout: 60000 }).toBe(true);
  page = app.windows().find(window => window.url().startsWith("http://localhost:7771/"));
  await page.emulateMedia({ reducedMotion: "reduce" });
  const windowHandle = await app.browserWindow(page);
  await windowHandle.evaluate(window => { window.show(); window.focus(); });
  page.on("console", message => { if (message.type() === "error") errors.push(clean(message.text())); });
  page.on("pageerror", error => errors.push(clean(error)));
  page.on("requestfailed", request => requests.push({ url: clean(request.url()), failure: request.failure() }));
  const capture = async suffix => {
    const path = join(root, label + "-" + suffix + ".png"); await page.screenshot({ path, fullPage: true }); screenshots.push(path);
  };
  stage = "root-render";
  await expect.poll(() => page.evaluate(() => document.querySelectorAll("#root button").length), { timeout: 45000 }).toBeGreaterThan(0);
  await capture("root");
  stage = "dismiss-import";
  const importButton = page.getByRole("button", { name: "Not now", exact: true });
  await importButton.click({ timeout: 45000 });
  await expect(importButton).not.toBeVisible({ timeout: 15000 });
  stage = "dismiss-tour";
  const skip = page.getByRole("button", { name: "Skip tour", exact: true });
  await skip.click({ timeout: 30000 });
  await expect(skip).not.toBeVisible({ timeout: 15000 });
  const activity = page.getByRole("button", { name: "Switch to activity view", exact: true });
  if (await activity.isVisible()) { await activity.click(); await page.getByRole("button", { name: "Switch to classic view", exact: true }).click(); }
  stage = "navigate-task-window";
  await page.getByRole("link", { name: "任务窗口", exact: true }).click({ timeout: 30000 });
  const main = page.getByRole("main", { name: "任务窗口", exact: true });
  await expect(main.getByRole("heading", { name: "分页交付", exact: true })).toBeVisible({ timeout: 15000 });
  await expect(main.getByRole("button", { name: "审查笔记", exact: true })).toBeVisible();
  for (const role of ["worker", "reviewer"]) await expect(main.getByRole("region", { name: role + " agent 会话", exact: true })).toBeVisible();
  await expect(main.getByText("Loading conversation", { exact: true })).toHaveCount(0, { timeout: 15000 });
  await expect(main.locator("[aria-label='受管任务门禁'] [aria-current='step']")).toHaveText("ready");
  await page.mouse.move(1150, 700);
  await capture("task-window");
  stage = "passed";
} catch (error) { failure = clean(error.stack ?? error); }
finally {
  if (page && !page.isClosed()) {
    observation = { url: clean(page.url()), text: await page.locator("body").innerText(), rootHtml: clean(await page.locator("#root").innerHTML()) };
    if (failure) { const path = join(root, label + "-failure.png"); try { await page.screenshot({ path, fullPage: true }); screenshots.push(path); } catch (error) { errors.push("capture: " + clean(error)); } }
  }
  if (app) {
    try { await Promise.race([app.close(), new Promise((_, reject) => setTimeout(() => reject(new Error("Owned Electron close timeout")), 15000))]); cleanup = "app.close"; }
    catch (error) { if (app.process().exitCode === null) app.process().kill("SIGKILL"); cleanup = clean(error) + "; terminated owned PID " + app.process().pid; }
  }
  writeFileSync(join(root, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), candidate, revisionAfter: revision(),
    sourceDiffAfter: execFileSync("git", ["diff", "--stat", "HEAD"], { cwd: checkout, encoding: "utf8" }),
    runtime: { node: process.version, executable: process.execPath }, launch: { executablePath: launch.executablePath, args: launch.args, cwd: launch.cwd,
      SYNARA_HOME: dataRoot, SYNARA_DESKTOP_SMOKE_USER_DATA: profile, VITE_DEV_SERVER_URL: launch.env.VITE_DEV_SERVER_URL },
    identity, stage, observation, failure, errors, requests, screenshots, cleanup, seconds: (Date.now() - started) / 1000,
    claim: "real isolated Electron task navigation; no source change, response fixture, model turn, or user profile" }, null, 2) + "\n", "utf8");
}
process.exit(failure ? 1 : 0);
