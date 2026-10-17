// T-091 red observer. Starts one real Electron window with production run().
// CLI/hooks/keys: Electron only here; no agent starts, hooks, or input events.
// The parent supplies three real daemon launches. No renderer or IPC is mocked.
import { app, BrowserWindow } from 'electron';
import { appendFileSync, readFileSync } from 'node:fs';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';

const [planFile, logFile] = process.argv.slice(2);
const plan = JSON.parse(readFileSync(planFile, 'utf8'));
const log = value => appendFileSync(logFile, JSON.stringify({ at: new Date().toISOString(), ...value }) + '\n');
const reply = value => process.stdout.write(JSON.stringify(value) + '\n');
process.on('uncaughtException', error => { log({ fatal: String(error) }); app.exit(2); });
process.on('unhandledRejection', error => { log({ fatal: String(error) }); app.exit(2); });
const build = JSON.parse(readFileSync(join(plan.build, 'build.json'), 'utf8'));
const { run } = await import(pathToFileURL(build.main).href);
// The unchanged baseline ignores launches and resolves its one current worker.
// The acceptance assertion observes actual terminal regions, not option parsing.
const window = await run({ state: plan.state, task: plan.task, userData: plan.userData, launches: plan.launches });
log({ started: true, pid: process.pid, browser_window: window.id, requested_launches: plan.launches });
reply({ ready: true, pid: process.pid, browser_window: window.id,
  electron: process.versions.electron, node: process.versions.node });
let queue = Promise.resolve();
createInterface({ input: process.stdin }).on('line', line => {
  queue = queue.then(async () => {
    const input = JSON.parse(line);
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
    } else if (input.command === 'close') {
      window.close();
      value = { close_requested: true };
    } else throw new Error('unsupported_observer_command');
    log({ request: input, value });
    reply({ id: input.id, ok: true, value });
  }).catch(error => { log({ error: String(error) }); reply({ ok: false, error: String(error) }); });
});
