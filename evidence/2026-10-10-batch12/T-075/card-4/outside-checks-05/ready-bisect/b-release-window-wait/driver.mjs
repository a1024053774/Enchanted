// Test process only. Observe product lifecycle and actual IPC without changing it.
import { app, ipcMain } from 'electron';
import { appendFileSync, readFileSync, writeFileSync } from 'node:fs';
import { createInterface } from 'node:readline';
import { isAbsolute, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';

const diagnostics = process.env.A2A_ELECTRON_DIAGNOSTICS;
function stage(name, detail = {}) {
  if (!diagnostics || !isAbsolute(diagnostics)) throw new Error('Absolute A2A_ELECTRON_DIAGNOSTICS is required');
  appendFileSync(diagnostics, JSON.stringify({ time: new Date().toISOString(), pid: process.pid,
    stage: name, app_ready: app.isReady(), ...detail }) + '\n');
}
function fatal(error) {
  const detail = { error: String(error), stack: error?.stack };
  try { stage('fatal', detail); }
  catch (recordError) { process.stderr.write('Diagnostic write failed: ' + String(recordError) + '\n'); }
  process.stderr.write((error?.stack ?? String(error)) + '\n');
  app.exit(1);
}
process.on('uncaughtException', fatal);
process.on('unhandledRejection', fatal);
try { stage('module_loaded', { argv: process.argv, electron: process.versions.electron }); }
catch (error) { fatal(error); }
app.on('ready', () => stage('app_ready_event'));
app.on('will-quit', () => stage('will_quit'));
app.on('quit', (_event, exitCode) => stage('quit', { exit_code: exitCode }));
app.on('browser-window-created', (_event, window) => {
  stage('window_created', { window: window.id });
  window.webContents.on('did-start-loading', () => stage('load_file_started', { window: window.id }));
  window.webContents.on('did-finish-load', () => stage('load_file_completed', { window: window.id, url: window.webContents.getURL() }));
  window.webContents.on('did-fail-load', (_event, code, description, url) => stage('load_file_failed', { code, description, url }));
  window.webContents.on('render-process-gone', (_event, details) => stage('renderer_gone', details));
  window.webContents.on('console-message', (_event, ...details) => stage('renderer_console', { details }));
});
async function reply(value) {
  if (value.ready) stage('ready_send');
  await new Promise((resolve, reject) => process.stdout.write(JSON.stringify(value) + '\n', (error) => error ? reject(error) : resolve()));
  if (value.ready) stage('ready_written');
}

async function main() {
  stage('parse_args_started');
  const { values } = parseArgs({ args: process.argv.slice(2), options: Object.fromEntries(
    ['build', 'state', 'task', 'launch', 'user-data', 'output'].map((key) => [key, { type: 'string' }])) });
  const output = values.output;
  if (!output || join(output, 'stages.jsonl') !== diagnostics) throw new Error('Output must match the harness diagnostic directory');
  stage('parse_args_completed');
  const build = JSON.parse(readFileSync(join(values.build, 'build.json'), 'utf8'));
  stage('manifest_loaded', { main: build.main, preload: build.preload, renderer: build.renderer });
  const originalHandle = ipcMain.handle.bind(ipcMain);
  let firstSnapshot = true;
  ipcMain.handle = (channel, handler) => originalHandle(channel, async (...args) => {
    if (channel === 'a2a:snapshot' && firstSnapshot) stage('first_snapshot_requested');
    const value = await handler(...args);
    if (channel === 'a2a:output') appendFileSync(join(output, 'received.ndjson'), JSON.stringify(value) + '\n');
    if (channel === 'a2a:snapshot') {
      appendFileSync(join(output, 'snapshots.ndjson'), JSON.stringify(value) + '\n');
      if (firstSnapshot) {
        stage('first_snapshot', { task: value.task?.task_id, gate: value.task?.state, launch: value.launch?.id ?? null });
        firstSnapshot = false;
      }
    }
    return value;
  });
  stage('main_import_started');
  const { run } = await import(pathToFileURL(build.main).href);
  stage('main_import_completed');
  stage('product_run_started');
  void run({ state: values.state, task: values.task, launch: values.launch, userData: values['user-data'] }).then(async (window) => {
    stage('product_run_completed', { window: window.id });
    const inspect = () => window.webContents.executeJavaScript(`({
      text: document.body.innerText,
      offset: Number(document.querySelector('[data-output-offset]')?.dataset.outputOffset ?? 0),
      state: document.querySelector('[data-state]')?.dataset.state,
      lifecycle: document.querySelector('[data-lifecycle]')?.dataset.lifecycle,
      gate: document.querySelector('[data-gate-state]')?.dataset.gateState,
      terminal: [...document.querySelectorAll('.xterm-accessibility-tree [role="listitem"]')].map(x => x.textContent).join('\\n'),
      bridge: Object.keys(window.a2a),
      node: typeof window.require
    })`);
    await reply({ ready: true, pid: process.pid });
    let pending = Promise.resolve();
    createInterface({ input: process.stdin }).on('line', (line) => {
      pending = pending.then(async () => {
        const request = JSON.parse(line);
        stage('request_received', { command: request.command, id: request.id });
        let value;
        if (request.command === 'inspect') value = await inspect();
        else if (request.command === 'capture') {
          if (!/^[a-zA-Z0-9_-]+$/.test(request.name)) throw new Error('Invalid capture name');
          await window.webContents.executeJavaScript('new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))');
          const picture = await window.webContents.capturePage();
          writeFileSync(join(output, request.name + '.png'), picture.toPNG(), { flag: 'wx' });
          value = await inspect();
          writeFileSync(join(output, request.name + '.json'), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
        } else if (request.command === 'readonly-input') {
          window.focus();
          await window.webContents.executeJavaScript("document.querySelector('.xterm-helper-textarea').focus()");
          window.webContents.sendInputEvent({ type: 'char', keyCode: 'Z' });
          window.webContents.sendInputEvent({ type: 'keyDown', keyCode: 'Enter' });
          window.webContents.sendInputEvent({ type: 'keyUp', keyCode: 'Enter' });
          // Use a local synthetic ClipboardEvent; never replace the user's clipboard.
          await window.webContents.executeJavaScript(`(() => { const data = new DataTransfer(); data.setData('text/plain', 'READ_ONLY_SENTINEL');
            document.querySelector('.xterm-helper-textarea').dispatchEvent(new ClipboardEvent('paste', { clipboardData: data, bubbles: true })); })()`);
          value = { sent: true };
        } else if (request.command === 'reconnect') {
          await window.webContents.executeJavaScript("[...document.querySelectorAll('button')].find(x => x.textContent === '重新连接').click()");
          value = { clicked: true };
        } else if (request.command === 'close') {
          await reply({ id: request.id, ok: true }); window.close(); return;
        } else throw new Error('Unknown driver command');
        await reply({ id: request.id, ok: true, value });
      }).catch(fatal);
    });
  }).catch(fatal);
}
await main().catch(fatal);
