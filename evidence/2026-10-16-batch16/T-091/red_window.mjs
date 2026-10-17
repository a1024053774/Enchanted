// T-091 red observer. Starts one real Electron window with production run().
// CLI/hooks/keys: Electron only here; no agent starts, hooks, or input events.
// The parent supplies three real daemon launches. No renderer or IPC is mocked.
import { app, BrowserWindow } from 'electron';
import { appendFileSync, readFileSync, accessSync } from 'node:fs';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';

const [planFile, logFile] = process.argv.slice(2);
const log = value => appendFileSync(logFile, JSON.stringify({ at: new Date().toISOString(),
  pid: process.pid, app_ready: app.isReady(), ...value }) + '\n');
let protocolFailed = false;
function fatal(error) {
  if (error?.code === 'EPIPE' || error?.code === 'ERR_STREAM_DESTROYED') {
    protocolFailed = true;
    log({ stage: 'protocol_failed', error: String(error), code: error.code,
      policy: 'No further replies; retain the application for owner-verified normal quit' });
    return;
  }
  try { log({ stage: 'fatal', error: String(error), stack: error?.stack }); }
  catch (recordError) { process.stderr.write(String(recordError) + '\n'); }
  process.stderr.write((error?.stack ?? String(error)) + '\n');
  app.exit(2);
}
const reply = value => new Promise((resolve, reject) => {
  log({ stage: 'reply_requested', id: value.id ?? null, ready: value.ready ?? false });
  if (protocolFailed) {
    reject(Object.assign(new Error('observer_protocol_detached'), { code: 'ERR_STREAM_DESTROYED' }));
    return;
  }
  process.stdout.write(JSON.stringify(value) + '\n', error => {
    if (error) reject(error);
    else { log({ stage: 'reply_written', id: value.id ?? null }); resolve(); }
  });
});
process.on('uncaughtException', fatal);
process.on('unhandledRejection', fatal);
process.stdout.on('error', fatal);
log({ stage: 'module_loaded', argv: process.argv, electron: process.versions.electron });
for (const event of ['ready', 'before-quit', 'will-quit', 'quit']) app.on(event, () => log({ stage: event }));
app.on('browser-window-created', (_event, created) => {
  log({ stage: 'window_created', browser_window: created.id });
  created.webContents.on('did-finish-load', () => log({ stage: 'load_completed', browser_window: created.id }));
  created.webContents.on('did-fail-load', (_event, code, description) => log({ stage: 'load_failed', code, description }));
});
let window = null;
let queue = Promise.resolve();
createInterface({ input: process.stdin }).on('line', line => {
  queue = queue.then(async () => {
    const input = JSON.parse(line);
    log({ stage: 'stdin_received', command: input.command, id: input.id });
    if (!window) throw new Error('observer_window_not_ready');
    let value;
    if (input.command === 'inspect') {
      const regions = await window.webContents.executeJavaScript(`
        [...document.querySelectorAll('section.pane')].map(section => {
          const bounds = section.getBoundingClientRect();
          const style = getComputedStyle(section);
          const terminal = section.querySelector('.xterm');
          const terminalBounds = terminal?.getBoundingClientRect();
          return { launch: section.dataset.launchId ?? null, thread: section.dataset.threadId ?? null,
            task: section.dataset.taskId ?? null, text: section.innerText,
            visible: style.display !== 'none' && style.visibility !== 'hidden' &&
              bounds.width > 0 && bounds.height > 0 && bounds.bottom > 0 && bounds.right > 0 &&
              bounds.top < innerHeight && bounds.left < innerWidth,
            bounds: { x: bounds.x, y: bounds.y, width: bounds.width, height: bounds.height },
            terminal: Boolean(terminal), terminal_bounds: terminalBounds ? {
              width: terminalBounds.width, height: terminalBounds.height } : null,
            offset: Number(section.querySelector('[data-output-offset]')?.dataset.outputOffset ?? 0) };
        })`);
      value = { browser_window: window.id, windows: BrowserWindow.getAllWindows().map(w => w.id), regions };
    } else throw new Error('unsupported_observer_command');
    log({ request: input, value });
    await reply({ id: input.id, ok: true, value });
  }).catch(error => { log({ error: String(error) }); void reply({ ok: false, error: String(error) }).catch(fatal); });
});

async function main() {
  const plan = JSON.parse(readFileSync(planFile, 'utf8'));
  const build = JSON.parse(readFileSync(join(plan.build, 'build.json'), 'utf8'));
  for (const key of ['main', 'preload', 'renderer']) accessSync(build[key]);
  log({ stage: 'main_import_started', main: build.main });
  const { run } = await import(pathToFileURL(build.main).href);
  log({ stage: 'main_import_completed' });
  log({ stage: 'product_run_started', requested_launches: plan.launches });
  // Release entry-module evaluation before run() waits for Electron's ready event.
  // The baseline ignores launches and resolves its one current worker.
  void run({ state: plan.state, task: plan.task, userData: plan.userData, launches: plan.launches }).then(async created => {
    window = created;
    log({ stage: 'product_run_completed', browser_window: window.id });
    await reply({ ready: true, pid: process.pid, browser_window: window.id,
      electron: process.versions.electron, node: process.versions.node });
  }).catch(fatal);
}
// No top-level await: startup must not hold Electron's ready event behind run().
void main().catch(fatal);
