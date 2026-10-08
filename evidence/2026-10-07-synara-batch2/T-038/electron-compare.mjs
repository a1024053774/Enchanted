import { createRequire } from "node:module";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const { _electron, expect } = createRequire("/Users/luckye/Documents/Code/synara-t038/apps/web/package.json")("playwright/test");
const root = dirname(fileURLToPath(import.meta.url));
const [variant, label, action] = process.argv.slice(2);
const navigate = action === "navigation";
if (!["baseline", "candidate"].includes(variant) || !label || existsSync(join(root, label + ".json"))) throw new Error("Variant and new evidence label required");
const checkout = "/Users/luckye/Documents/Code/" + (variant === "baseline" ? "synara-t038-baseline" : "synara-t038");
const data = "/Volumes/WD-Elements/dev-cache/synara/instances/t038/electron-comparison/" + label;
const home = navigate ? "/Volumes/WD-Elements/dev-cache/synara/instances/t038/desktop-home" : join(data, "home");
const profile = join(data, "profile");
mkdirSync(home, { recursive: true }); mkdirSync(profile, { recursive: true });
const clean = value => String(value).replace(/([?&]token=)[^&\s"']+/g, "$1<redacted>");
const launch = {
  executablePath: "/Volumes/WD-Elements/dev-cache/synara/instances/t038/tools/electron-43.4.1/Electron.app/Contents/MacOS/Electron",
  args: [join(checkout, "apps/desktop/dist-electron/main.js")], cwd: join(checkout, "apps/desktop"), timeout: 60000,
  env: { ...process.env, SYNARA_HOME: home, SYNARA_DESKTOP_SMOKE_USER_DATA: profile, SYNARA_DESKTOP_FLAVOR: "cua",
    SYNARA_SOURCE_DESKTOP_BUILD_MARKER: "synara-source-desktop-build-v2", SYNARA_DISABLE_AUTO_UPDATE: "1", VITE_DEV_SERVER_URL: "http://localhost:7771/" },
};
let app, page, identity, observation, failure;
const errors = [], processLogs = [], requests = [];
const started = Date.now();
try {
  app = await _electron.launch(launch);
  app.process().stdout?.on("data", chunk => processLogs.push({ channel: "stdout", text: clean(chunk) }));
  app.process().stderr?.on("data", chunk => processLogs.push({ channel: "stderr", text: clean(chunk) }));
  identity = await app.evaluate(({ app }) => ({ userData: app.getPath("userData"), appPath: app.getAppPath(), version: process.versions.electron }));
  if (identity.userData !== profile || !identity.appPath.startsWith(checkout + "/")) throw new Error("Incorrect isolated desktop identity");
  await expect.poll(() => app.windows().some(window => window.url().startsWith("http://localhost:7771/")), { timeout: 60000 }).toBe(true);
  page = app.windows().find(window => window.url().startsWith("http://localhost:7771/"));
  page.on("console", message => { if (message.type() === "error") errors.push(clean(message.text())); });
  page.on("pageerror", error => errors.push(clean(error)));
  page.on("requestfailed", request => requests.push({ url: clean(request.url()), failure: request.failure() }));
  try {
    await expect.poll(() => page.evaluate(() => document.querySelectorAll("#root button").length), { timeout: 45000 }).toBeGreaterThan(0);
  } catch (error) { failure = clean(error); }
  if (navigate && !failure) {
    try {
      await page.getByRole("button", { name: "Not now", exact: true }).click({ timeout: 60000 });
      await page.getByRole("button", { name: "Skip tour", exact: true }).click({ timeout: 15000 });
      await page.getByRole("button", { name: "Switch to activity view", exact: true }).click();
      await page.getByRole("button", { name: "Switch to classic view", exact: true }).click();
      await page.getByRole("link", { name: "任务窗口", exact: true }).click();
      const main = page.getByRole("main", { name: "任务窗口", exact: true });
      await expect(main.getByRole("heading", { name: "分页交付", exact: true })).toBeVisible({ timeout: 15000 });
      await expect(main.getByRole("button", { name: "审查笔记", exact: true })).toBeVisible();
      for (const role of ["worker", "reviewer"]) await expect(main.getByRole("region", { name: role + " agent 会话", exact: true })).toBeVisible();
      await expect(main.getByText("Loading conversation", { exact: true })).toHaveCount(0, { timeout: 15000 });
      await expect(main.locator("[aria-label='受管任务门禁'] [aria-current='step']")).toHaveText("ready");
      await page.mouse.move(1550, 950);
    } catch (error) { failure = clean(error); }
  }
  observation = await page.evaluate(() => ({ url: location.href, buttonCount: document.querySelectorAll("#root button").length,
    bootSplash: Boolean(document.querySelector(".app-boot-splash")), rootHtml: document.querySelector("#root")?.innerHTML,
    bridgePresent: Boolean(window.desktopBridge), text: document.body.innerText }));
  await page.screenshot({ path: join(root, label + ".png"), fullPage: true });
} catch (error) { failure = clean(error); }
finally {
  let cleanup = "not started";
  if (app) {
    try { await Promise.race([app.close(), new Promise((_, reject) => setTimeout(() => reject(new Error("Owned Electron close timeout")), 15000))]); cleanup = "app.close"; }
    catch (error) { if (app.process().exitCode === null) app.process().kill("SIGKILL"); cleanup = clean(error) + "; terminated owned Electron PID " + app.process().pid; }
  }
  writeFileSync(join(root, label + ".json"), JSON.stringify({ argv: process.argv.slice(1), variant, checkout, home, profile,
    launch: { executablePath: launch.executablePath, args: launch.args, cwd: launch.cwd, VITE_DEV_SERVER_URL: launch.env.VITE_DEV_SERVER_URL },
    identity, observation, failure, errors, requests, processLogs, seconds: (Date.now() - started) / 1000, cleanup,
    claim: "read-only Electron comparison; fresh isolated data; no model turn or upstream source changes" }, null, 2) + "\n", "utf8");
}
if (!observation) throw new Error(failure ?? "No renderer observation");

process.exit(0); // The report is saved and the owned Electron process has exited or was terminated.
