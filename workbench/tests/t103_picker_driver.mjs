// Observe the real Electron renderer and IPC. This driver does not replace data,
// handlers, terminal output, or the backend.
import { app } from 'electron';
import { readFileSync, writeFileSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createInterface } from 'node:readline';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ args: process.argv.slice(2), options: Object.fromEntries(
  ['build', 'state', 'task', 'user-data', 'output'].map(key => [key, { type: 'string' }])) });
const record = value => appendFileSync(join(values.output, 'driver.ndjson'), JSON.stringify({
  time: new Date().toISOString(), pid: process.pid, app_ready: app.isReady(), ...value }) + '\n');
const reply = value => new Promise((resolve, reject) => process.stdout.write(JSON.stringify(value) + '\n', error => error ? reject(error) : resolve()));
const build = JSON.parse(readFileSync(join(values.build, 'build.json'), 'utf8'));
app.on('ready', () => record({ stage: 'app-ready' }));
app.on('browser-window-created', (_event, window) => {
  record({ stage: 'window-created', window: window.id });
  window.webContents.on('did-finish-load', () => record({ stage: 'window-loaded', window: window.id }));
});
async function main() {
  record({ stage: 'start', electron: process.versions.electron, executable: process.execPath, node: process.versions.node, task: values.task ?? null });
  const { run } = await import(pathToFileURL(build.main).href);
  record({ stage: 'product-imported' });
  // Electron waits for entry-module evaluation before emitting ready. The
  // product waits for ready to create its window, so this wait must be detached.
  // See the existing bisect_electron_ready.py counterexample and startup test.
  void run({ state: values.state, task: values.task, userData: values['user-data'] }).then(async window => {
  record({ stage: 'product-run-completed', window: window.id });
  const inspect = () => window.webContents.executeJavaScript(`({
    text: document.body.innerText,
    heading: document.querySelector('h1')?.textContent,
    projects: [...document.querySelectorAll('[data-project-id]')].map(node => node.dataset.projectId),
    tasks: [...document.querySelectorAll('[data-task-option]')].map(node => ({
      id: node.dataset.taskOption, text: node.textContent, current: node.getAttribute('aria-current'), disabled: node.disabled })),
    panes: [...document.querySelectorAll('section.pane')].map(node => ({
      key: node.dataset.paneKey, task: node.dataset.taskId, launch: node.dataset.launchId,
      input: node.dataset.inputEnabled, offset: Number(node.querySelector('[data-output-offset]')?.dataset.outputOffset ?? 0),
      terminal: [...node.querySelectorAll('.xterm-accessibility-tree [role="listitem"]')].map(row => row.textContent).join('\\n') })),
    alerts: [...document.querySelectorAll('[role="alert"]')].map(node => node.textContent),
    node: typeof window.require, bridge: Object.keys(window.a2a),
    busy: document.querySelector('nav[aria-busy]')?.getAttribute('aria-busy')
  })`);
  await reply({ ready: true, pid: process.pid, electron_executable: process.execPath, electron_version: process.versions.electron });
  let pending = Promise.resolve();
  createInterface({ input: process.stdin }).on('line', line => {
    pending = pending.then(async () => {
      const request = JSON.parse(line);
      record({ request });
      try {
        let value;
        if (request.command === 'inspect') value = await inspect();
        else if (request.command === 'select') {
          value = await window.webContents.executeJavaScript(`(() => {
            const button = [...document.querySelectorAll('[data-task-option]')].find(node => node.dataset.taskOption === ${JSON.stringify(request.task)});
            if (!button || button.disabled) throw new Error('Task is unavailable');
            button.click(); return { clicked: true };
          })()`);
        } else if (request.command === 'refresh') {
          value = await window.webContents.executeJavaScript(`(() => {
            const button = [...document.querySelectorAll('button')].find(node => node.textContent === '刷新列表');
            if (!button || button.disabled) throw new Error('Refresh is unavailable');
            button.click(); return { clicked: true };
          })()`);
        } else if (request.command === 'bridge') {
          if (!['snapshot', 'input', 'selectTask'].includes(request.operation)) throw new Error('Unsupported probe');
          value = await window.webContents.executeJavaScript(`(async () => {
            try { return { resolved: true, value: await window.a2a[${JSON.stringify(request.operation)}](...${JSON.stringify(request.args)}) }; }
            catch (error) { return { rejected: true, error: String(error) }; }
          })()`);
        } else if (request.command === 'keyboard-select') {
          window.focus();
          const focus = await window.webContents.executeJavaScript(`(() => {
            const button = [...document.querySelectorAll('[data-task-option]')].find(node => node.dataset.taskOption === ${JSON.stringify(request.task)});
            if (!button || button.disabled) throw new Error('Task is unavailable');
            button.focus();
            return { task: document.activeElement?.dataset.taskOption, documentFocused: document.hasFocus() };
          })()`);
          focus.windowFocused = window.isFocused();
          focus.contentsFocused = window.webContents.isFocused();
          record({ stage: 'keyboard-target', target: request.task, focus });
          if (focus.task !== request.task || !focus.documentFocused || !focus.windowFocused || !focus.contentsFocused) {
            throw new Error('Task button does not have keyboard focus');
          }
          window.webContents.sendInputEvent({ type: 'keyDown', keyCode: 'Enter' });
          // Native HTML button activation needs the carriage-return char /
          // keypress as well as keyDown and keyUp. Do not replace it with click.
          window.webContents.sendInputEvent({ type: 'char', keyCode: '\r' });
          window.webContents.sendInputEvent({ type: 'keyUp', keyCode: 'Enter' });
          value = { attempted: true, target: request.task, focus };
        } else if (request.command === 'capture') {
          if (!/^[a-z0-9-]+$/.test(request.name)) throw new Error('Invalid screenshot name');
          if (request.width) window.setSize(request.width, request.height);
          await window.webContents.executeJavaScript('new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))');
          writeFileSync(join(values.output, request.name + '.png'), (await window.webContents.capturePage()).toPNG(), { flag: 'wx' });
          value = await inspect();
        } else if (request.command === 'close') {
          await reply({ id: request.id, ok: true }); window.close(); return;
        } else throw new Error('Unknown command');
        record({ response: { id: request.id, value } });
        await reply({ id: request.id, ok: true, value });
      } catch (error) { await reply({ id: request.id, ok: false, error: String(error) }); }
    }).catch(error => { record({ fatal: String(error) }); app.exit(1); });
  });
  }).catch(failed);
  record({ stage: 'driver-registered' });
}
async function failed(error) {
  record({ stage: 'startup-failed', error: String(error) });
  await reply({ startup_error: String(error), electron_executable: process.execPath, electron_version: process.versions.electron });
  app.exit(1);
}
await main().catch(failed);
