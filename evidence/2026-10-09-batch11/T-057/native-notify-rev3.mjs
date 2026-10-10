import { createRequire } from "node:module";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
const [out, fork, label] = process.argv.slice(2);
if (existsSync(join(out, label + ".json"))) throw new Error("Evidence exists");
const require = createRequire(join(fork, "apps/web/package.json"));
const { _electron: electron, expect } = require("playwright/test");
const { resolveElectronPath } = await import(join(fork, "apps/desktop/scripts/electron-launcher.mjs"));
const { createSourceDesktopEnvironment } = await import(join(fork, "apps/desktop/scripts/source-desktop-launch.mjs"));
const { DEFAULT_SERVER_SETTINGS } = await import(join(fork, "packages/contracts/src/settings.ts"));
const { A2AGates } = await import(join(fork, "packages/a2a-gates/src/core.ts"));
const { synaraDesktopIdentity } = await import(join(fork, "packages/shared/src/desktopIdentity.ts"));
const entryUrl = synaraDesktopIdentity("cua").entryUrl;
const entry = new URL(entryUrl);
const pagePrefix = `${entry.protocol}//${entry.host}/`;
const home = mkdtempSync("/tmp/a2a-t057-notify-rev3-");
for (const name of ["userdata", "os-home", "codex-empty", "claude-empty", "electron-profile", "repo"]) mkdirSync(join(home, name));
const settings = structuredClone(DEFAULT_SERVER_SETTINGS);
settings.enableProviderUpdateChecks = false;
settings.onboardingCompletedAt = "2026-10-10T04:00:00.000Z";
for (const provider of Object.values(settings.providers)) provider.enabled = false;
writeFileSync(join(home, "userdata/settings.json"), JSON.stringify({ revision: 0, migrationVersion: 0, settings }));
const env = createSourceDesktopEnvironment({ environment: {
  ...process.env, HOME: join(home, "os-home"), CODEX_HOME: join(home, "codex-empty"), CLAUDE_CONFIG_DIR: join(home, "claude-empty"),
  SYNARA_HOME: home, SYNARA_DESKTOP_SMOKE_USER_DATA: join(home, "electron-profile"), A2A_WORKBENCH: "1", SYNARA_DISABLE_AUTO_UPDATE: "1",
} });
delete env.VITE_DEV_SERVER_URL;
delete env.ELECTRON_RUN_AS_NODE;
const executable = resolveElectronPath();
const marker = "T057-native-" + randomUUID();
const receipts = [], checks = [];
let app, page, failure, telemetry, history, endpoint, core, paused = false;
const save = (name, value) => {
  const text = JSON.stringify(value, null, 2);
  writeFileSync(join(out, name + ".json"), (endpoint?.token ? text.split(endpoint.token).join("[REDACTED]") : text) + "\n", { flag: "wx" });
};
async function gate(command, args) {
  const url = new URL("/api/a2a", endpoint.origin);
  url.searchParams.set("token", endpoint.token);
  const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer " + endpoint.token }, body: JSON.stringify({ command, ...args }) });
  const result = await response.json(); receipts.push({ command, args, result }); return result;
}
async function readTelemetry() {
  return app.evaluate((_electron, marker) => ({
    ipc: globalThis.t057Telemetry.ipc.filter(item => item.body?.includes(marker)),
    native: globalThis.t057Telemetry.native.filter(item => item.body?.includes(marker)),
    events: globalThis.t057Telemetry.events.filter(item => item.body?.includes(marker)),
  }), marker);
}
async function readHistory() {
  return app.evaluate(async ({ Notification }, marker) => (await Notification.getHistory())
    .filter(item => item.body.includes(marker)).map(item => ({ id: item.id, groupId: item.groupId, title: item.title, body: item.body })), marker);
}
async function background() {
  await app.evaluate(({ app }) => app.hide());
  await expect.poll(() => page.evaluate(() => document.hasFocus()), { timeout: 10000 }).toBe(false);
  const window = await app.browserWindow(page);
  return { native: await window.evaluate(value => ({ visible: value.isVisible(), focused: value.isFocused(), minimized: value.isMinimized() })), document: await page.evaluate(() => ({ visibility: document.visibilityState, focus: document.hasFocus() })) };
}
async function launch() {
  app = await electron.launch({ executablePath: executable, args: [join(fork, "apps/desktop/dist-electron/main.js")], cwd: join(fork, "apps/desktop"), env, timeout: 60000 });
  app.process().stdout?.pipe(await import("node:fs").then(fs => fs.createWriteStream(join(home, "private-main-" + app.process().pid + ".log"))));
  app.process().stderr?.pipe(await import("node:fs").then(fs => fs.createWriteStream(join(home, "private-error-" + app.process().pid + ".log"))));
  await app.firstWindow({ timeout: 60000 });
  await expect.poll(() => app.windows().some(window => window.url().startsWith(pagePrefix)), { timeout: 60000 }).toBe(true);
  page = app.windows().find(window => window.url().startsWith(pagePrefix));
  // Playwright enables synthetic focus by default. Restore real native focus
  // before observing the built application's foreground routing.
  const cdp = await app.context().newCDPSession(page);
  await cdp.send("Emulation.setFocusEmulationEnabled", { enabled: false });
  await page.addLocatorHandler(page.getByRole("button", { name: "Not now", exact: true }), button => button.click(), { noWaitAfter: true });
  await page.addLocatorHandler(page.getByRole("button", { name: "Skip tour", exact: true }), button => button.click(), { noWaitAfter: true });
  await (await app.browserWindow(page)).evaluate(window => { window.setBounds({ width: 1600, height: 1050 }); window.show(); window.focus(); });
  await app.evaluate(({ app }) => app.focus({ steal: true }));
  await expect.poll(() => existsSync(join(home, "a2a-gates/endpoint.json")), { timeout: 60000 }).toBe(true);
  endpoint = JSON.parse(readFileSync(join(home, "a2a-gates/endpoint.json"), "utf8"));
  await expect.poll(async () => {
    try { return (await (await fetch(endpoint.origin + "/health")).json()).startupReady === true; }
    catch { return false; }
  }, { timeout: 60000 }).toBe(true);
  await app.evaluate(({ Notification, ipcMain }) => {
    globalThis.t057Telemetry = { ipc: [], native: [], events: [] };
    const handler = ipcMain._invokeHandlers.get("desktop:notifications-show");
    if (!handler) throw new Error("Notification IPC not registered");
    ipcMain._invokeHandlers.set("desktop:notifications-show", async (event, input) => { globalThis.t057Telemetry.ipc.push(input); return handler(event, input); });
    const show = Notification.prototype.show;
    Notification.prototype.show = function () {
      globalThis.t057Telemetry.native.push({ title: this.title, body: this.body, silent: this.silent });
      this.once("show", () => globalThis.t057Telemetry.events.push({ type: "show", title: this.title, body: this.body, silent: this.silent }));
      this.once("failed", (_event, error) => globalThis.t057Telemetry.events.push({ type: "failed", body: this.body, error: String(error) }));
      return show.call(this);
    };
  });
  await expect.poll(() => page.evaluate(() => document.hasFocus()), { timeout: 10000 }).toBe(true);
  save(label + "-process-" + app.process().pid, { pid: app.process().pid, backendPid: endpoint.backendPid, home, executable, entry: join(fork, "apps/desktop/dist-electron/main.js"), marker });
}
async function stop() {
  if (!app) return;
  const child = app.process();
  child.kill("SIGUSR2");
  await expect.poll(() => child.exitCode !== null, { timeout: 45000 }).toBe(true);
  app = undefined;
}
try {
  await launch();
  const repo = realpathSync(join(home, "repo"));
  const git = (...args) => execFileSync("git", ["-C", repo, ...args], { encoding: "utf8", env: { ...env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" } }).trim();
  git("init"); git("config", "user.name", "T057 native fixture"); git("config", "user.email", "fixture@example.invalid");
  writeFileSync(join(repo, "sentinel.txt"), "Native notification fixture Ω\n");
  git("add", "sentinel.txt"); git("-c", "core.hooksPath=/dev/null", "commit", "-m", "Isolated native input");
  writeFileSync(join(home, "instructions.txt"), "通知验证；provider 禁用，不使用模型。\n");
  writeFileSync(join(home, "oracle.py"), "raise SystemExit(0)\n");
  const created = await gate("create", { task: "t057-native", project: "t057-native", repo, base: git("rev-parse", "HEAD"), oracle: join(home, "oracle.py"), instructions: join(home, "instructions.txt") });
  expect(created.ok, JSON.stringify(created)).toBe(true);
  const attached = await gate("attach", { task: "t057-native", role: "reviewer", preset: "reviewer", modelSelection: { provider: "codex", model: "gpt-6.1-sol" }, runtimeMode: "approval-required", instructions: join(home, "instructions.txt") });
  expect(attached.ok, JSON.stringify(attached)).toBe(true);
  const thread = attached.attachment.thread_id;
  // Only creation of external notification inputs uses controlled native state.
  // The built renderer, server queries, real IPC and macOS Notification stay real.
  core = new A2AGates(join(home, "userdata/a2a-gates"), {
    readThread: async () => ({ workspace: repo, provider: "codex", turn: "native-input", running: true, stopped: false, archived: false }),
  });
  const issues = [];
  for (const [name, blocking] of [["blocking A", true], ["blocking B", true], ["regular", false]]) {
    issues.push(await core.raiseIssue({ title: marker + " " + name, body: "", blocking, refs: [] }, { thread, turn: "native-input", assertActive: async () => {} }));
  }
  core.close(); core = undefined;
  save(label + "-inputs", { marker, issues, created, attached, creation_native_state_controlled: true, new_model_calls: 0 });
  await expect(page.getByLabel("等你决定 2 题", { exact: true }).first()).toBeVisible({ timeout: 10000 });
  expect((await readTelemetry()).ipc).toEqual([]);
  checks.push("真实桌面已读回两题徽标，前台没有系统通知；软件内路由另由浏览器入口证明");
  const closed = await gate("disposition", { task: "t057-native", issue: issues[2].id, action: "close", reason: "已核对夹具的普通软件内通知", basis: "ticket:T-057" });
  expect(closed.ok).toBe(true);
  const backgroundState = await background();
  await expect.poll(async () => (await readTelemetry()).native.length, { timeout: 10000 }).toBe(1);
  telemetry = await readTelemetry();
  save(label + "-os-attempt", { marker, home, executable, telemetry, background: backgroundState });
  paused = true;
  writeFileSync(join(home, "permission-check-required.json"), JSON.stringify({ home, marker, pid: app.process().pid }));
  console.log("OS_PROBE_READY " + home);
  // The operator checks the real surface now. No system authorization is clicked.
  while (!existsSync(join(home, "continue-native-test"))) await new Promise(resolve => setTimeout(resolve, 250));
  paused = false;
  await page.waitForTimeout(1500);
  telemetry = await readTelemetry(); history = await readHistory();
  expect(telemetry.ipc).toHaveLength(1);
  expect(telemetry.ipc[0]).toMatchObject({ title: "2 个问题等你决定", silent: true, suppressWhenForeground: true });
  expect(telemetry.native).toHaveLength(1);
  expect(telemetry.native[0].silent).toBe(true);
  expect(history).toHaveLength(1);
  expect(history[0].id).toBeTruthy();
  expect(history[0].body).toBe(`问题 1：${marker} blocking A\n问题 2：${marker} blocking B`);
  save(label + "-notification-center", { marker, history, telemetry, limitation: "Notification.getHistory 是实际 macOS 通知中心的本应用回执，输出仅保留本探针 marker；未测量物理音频。" });
  checks.push("真实 macOS 通知中心有同批两题的一条回执，实际原生 Notification.silent=true");
  await stop(); await launch();
  await background();
  await page.waitForTimeout(3000);
  expect((await readTelemetry()).ipc).toEqual([]);
  checks.push("实际 Electron 进程重启后已提醒项没有重复调用");
  await (await app.browserWindow(page)).evaluate(window => { window.restore(); window.show(); window.focus(); });
  await app.evaluate(({ app }) => app.focus({ steal: true }));
  const settingsUrl = new URL("/settings?section=notifications", page.url()).toString();
  await page.goto(settingsUrl, { waitUntil: "domcontentloaded" });
  const toggle = page.getByRole("switch", { name: "Desktop activity notifications", exact: true });
  await expect(toggle).toBeChecked(); await toggle.click(); await expect(toggle).not.toBeChecked();
  await page.screenshot({ path: join(out, label + "-settings-off.png") });
  await background();
  const changed = await gate("disposition", { task: "t057-native", issue: issues[0].id, action: "needs-user" });
  expect(changed.ok).toBe(true);
  await page.waitForTimeout(3000);
  expect((await readTelemetry()).ipc).toEqual([]);
  checks.push("真实设置开关关闭后新待决定没有 IPC 或原生通知调用");
} catch (error) {
  failure = String(error.stack ?? error);
  if (page) {
    try {
      save(label + "-ui-diagnostic", { text: await page.evaluate(() => document.body.innerText), foreground: await page.evaluate(() => ({ visibility: document.visibilityState, focus: document.hasFocus() })) });
      await page.screenshot({ path: join(out, label + "-failure.png") });
    } catch {}
  }
}
finally {
  core?.close();
  if (app) { try { telemetry = await readTelemetry(); } catch {} }
  save(label, { argv: process.argv.slice(1), home, executable, marker, failure, paused, checks, telemetry, history, receipts,
    boundary: "候选独立 checkout 标准构建，隔离 Electron 原生 preload/IPC/Notification；无真实模型，通知输入创建的 native 活跃状态受控。" });
  if (!paused) await stop();
}
if (failure) throw new Error(failure);
