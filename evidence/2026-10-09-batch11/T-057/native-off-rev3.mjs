import { createRequire } from "node:module";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const [out, fork, label] = process.argv.slice(2);
const prior = JSON.parse(readFileSync(join(out, "native-notify-rev3-07.json"), "utf8"));
const inputs = JSON.parse(readFileSync(join(out, "native-notify-rev3-07-inputs.json"), "utf8"));
const { home, marker } = prior;
if (!home.startsWith("/tmp/a2a-t057-notify-rev3-") || existsSync(join(out, label + ".json"))) throw new Error("Fixture identity mismatch");
const { _electron: electron, expect } = createRequire(join(fork, "apps/web/package.json"))("playwright/test");
const { createSourceDesktopEnvironment } = await import(join(fork, "apps/desktop/scripts/source-desktop-launch.mjs"));
const env = createSourceDesktopEnvironment({ environment: { ...process.env,
  HOME: join(home, "os-home"), CODEX_HOME: join(home, "codex-empty"), CLAUDE_CONFIG_DIR: join(home, "claude-empty"),
  SYNARA_HOME: home, SYNARA_DESKTOP_SMOKE_USER_DATA: join(home, "electron-profile"), A2A_WORKBENCH: "1", SYNARA_DISABLE_AUTO_UPDATE: "1" } });
delete env.VITE_DEV_SERVER_URL; delete env.ELECTRON_RUN_AS_NODE;
let app, page, endpoint, failure, state, receipt, telemetry;
const save = (suffix, value) => { const text = JSON.stringify(value, null, 2); writeFileSync(join(out, suffix + ".json"), (endpoint?.token ? text.split(endpoint.token).join("[REDACTED]") : text) + "\n", { flag: "wx" }); };
try {
  app = await electron.launch({ executablePath: prior.executable, args: [join(fork, "apps/desktop/dist-electron/main.js")], cwd: join(fork, "apps/desktop"), env, timeout: 60000 });
  await app.firstWindow();
  page = app.windows().find(page => page.url().startsWith("synara-cua://app/"));
  const cdp = await app.context().newCDPSession(page);
  await cdp.send("Emulation.setFocusEmulationEnabled", { enabled: false });
  await (await app.browserWindow(page)).evaluate(window => { window.show(); window.focus(); });
  await app.evaluate(({ app }) => app.focus({ steal: true }));
  await expect.poll(() => existsSync(join(home, "a2a-gates/endpoint.json")), { timeout: 60000 }).toBe(true);
  endpoint = JSON.parse(readFileSync(join(home, "a2a-gates/endpoint.json"), "utf8"));
  await app.evaluate(({ Notification, ipcMain }) => {
    globalThis.t057Off = { ipc: [], native: [] };
    const handler = ipcMain._invokeHandlers.get("desktop:notifications-show");
    ipcMain._invokeHandlers.set("desktop:notifications-show", async (event, input) => { globalThis.t057Off.ipc.push(input); return handler(event, input); });
    const show = Notification.prototype.show;
    Notification.prototype.show = function () { globalThis.t057Off.native.push({ title: this.title, body: this.body, silent: this.silent }); return show.call(this); };
  });
  save(label + "-ready", { pid: app.process().pid, backendPid: endpoint.backendPid, home, marker, executable: prior.executable, entry: join(fork, "apps/desktop/dist-electron/main.js") });
  console.log("NATIVE_OFF_READY " + home);
  while (!existsSync(join(home, "setting-ui-done-rev3-08"))) await new Promise(resolve => setTimeout(resolve, 250));
  state = await page.evaluate(() => JSON.parse(localStorage.getItem("synara:app-settings:v1")).enableSystemTaskCompletionNotifications);
  expect(state).toBe(false);
  await page.screenshot({ path: join(out, label + "-settings-off.png") });
  await app.evaluate(({ app }) => app.hide());
  await expect.poll(() => page.evaluate(() => document.hasFocus()), { timeout: 10000 }).toBe(false);
  const url = new URL("/api/a2a", endpoint.origin); url.searchParams.set("token", endpoint.token);
  const request = { command: "disposition", task: "t057-native", issue: inputs.issues[0].id, action: "needs-user" };
  receipt = await (await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer " + endpoint.token }, body: JSON.stringify(request) })).json();
  expect(receipt.ok).toBe(true);
  await page.waitForTimeout(3000);
  telemetry = await app.evaluate((_electron, marker) => ({ ipc: globalThis.t057Off.ipc.filter(item => item.body?.includes(marker)), native: globalThis.t057Off.native.filter(item => item.body?.includes(marker)) }), marker);
  expect(telemetry.ipc).toEqual([]); expect(telemetry.native).toEqual([]);
} catch (error) { failure = String(error.stack ?? error); }
finally {
  save(label, { argv: process.argv.slice(1), home, marker, failure, setting_readback: state, receipt, telemetry, status: failure ? "INCOMPLETE" : "PASS", real_ui_setting: true, real_focus: true });
  if (app) { const child = app.process(); child.kill("SIGUSR2"); await expect.poll(() => child.exitCode !== null, { timeout: 45000 }).toBe(true); }
}
if (failure) throw new Error(failure);
