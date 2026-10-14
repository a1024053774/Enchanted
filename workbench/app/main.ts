import { app, BrowserWindow, ipcMain } from 'electron';
import { mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { request } from '../src/transport.ts';
import { readOperatorCredential } from '../src/credentials.ts';
import { randomUUID } from 'node:crypto';

type Options = { state: string; task: string; launch?: string; userData: string };
const directory = dirname(fileURLToPath(import.meta.url));

export async function run(options: Options) {
  if (!isAbsolute(options.state) || !isAbsolute(options.userData) || !options.task) throw new Error('Absolute data paths and a task are required');
  const operator = readOperatorCredential(options.state);
  if (!operator) throw new Error('operator_credential_required');
  mkdirSync(options.userData, { recursive: true, mode: 0o700 });
  const sessionData = join(options.userData, 'session');
  for (const path of [sessionData, join(options.userData, 'logs'), join(options.userData, 'crashes')]) {
    mkdirSync(path, { recursive: true, mode: 0o700 });
  }
  app.setPath('userData', options.userData);
  app.setPath('sessionData', sessionData);
  app.setPath('logs', join(options.userData, 'logs'));
  app.setPath('crashDumps', join(options.userData, 'crashes'));
  await app.whenReady();
  const window = new BrowserWindow({ width: 1440, height: 900, minWidth: 900, minHeight: 650,
    title: 'a2a 工作台', backgroundColor: '#111111',
    webPreferences: { preload: join(directory, 'preload.cjs'), nodeIntegration: false,
      contextIsolation: true, sandbox: true, backgroundThrottling: false } });
  let launch = options.launch;
  let identity: Record<string, unknown> | undefined;
  let sequence = 0;
  let inputQueue = Promise.resolve();
  let closing = false, closed = false;
  const checkSender = (event: Electron.IpcMainInvokeEvent) => {
    if (event.sender !== window.webContents || event.senderFrame !== window.webContents.mainFrame) throw new Error('Unknown window');
  };
  ipcMain.handle('a2a:snapshot', async (event) => {
    checkSender(event);
    const result = await request(options.state, { command: 'workbench_snapshot', task: options.task, ...(launch ? { launch } : {}) });
    if (!result.ok) throw new Error(result.error);
    if (result.launch) launch = result.launch.id;
    const writable = result.pane?.lifecycle === 'running' && !result.pane.failed &&
      Boolean(result.launch && (result.launch.role === 'controller' && result.launch.attempt === null ||
        result.launch.attempt !== null && result.task.current_attempt?.attempt_id === result.launch.attempt));
    if (result.launch && !identity) {
      const opened = await request(options.state, { command: 'window_open', task: options.task, launch }, operator);
      if (!opened.ok) throw new Error(opened.error);
      identity = opened.identity;
    }
    return { ...result, input_enabled: Boolean(writable && identity && !closing) };
  });
  const sendWindowCommand = (input: Record<string, unknown>) => {
    if (!identity || closing) throw new Error('Window is not available for input');
    const command = { ...input, sequence: ++sequence, request_id: randomUUID() };
    inputQueue = inputQueue.then(async () => {
      const result = await request(options.state, command, identity);
      if (!result.ok) throw new Error(result.error);
    });
    return inputQueue;
  };
  ipcMain.handle('a2a:input', (event, data: string, encoding: 'utf8' | 'binary' = 'utf8') => {
    checkSender(event);
    if (!['utf8', 'binary'].includes(encoding) || typeof data !== 'string' ||
        (encoding === 'binary' ? data.length : Buffer.byteLength(data, 'utf8')) > 1024 * 1024 ||
        (encoding === 'binary' && [...data].some(char => char.charCodeAt(0) > 255))) throw new Error('Invalid terminal input');
    return sendWindowCommand({ command: 'window_input', data, encoding });
  });
  ipcMain.handle('a2a:composition-start', event => {
    checkSender(event);
    return sendWindowCommand({ command: 'window_composition' });
  });
  ipcMain.handle('a2a:release-queue', event => {
    checkSender(event);
    return sendWindowCommand({ command: 'window_release' });
  });
  ipcMain.handle('a2a:focus-observation', (event, rawSequence: string) => {
    checkSender(event);
    if (typeof rawSequence !== 'string' || rawSequence.length > 4096) throw new Error('Invalid focus observation');
    return sendWindowCommand({ command: 'window_observation', type: 'focus-mode-intercept', raw_sequence: rawSequence });
  });
  ipcMain.handle('a2a:output', async (event, offset: number) => {
    checkSender(event);
    if (!launch || !Number.isSafeInteger(offset) || offset < 0) throw new Error('Invalid output request');
    const result = await request(options.state, { command: 'pane_output', launch, offset, max_bytes: 65536 });
    if (!result.ok) throw new Error(result.error);
    return result;
  });
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  window.webContents.on('will-navigate', (event) => event.preventDefault());
  window.on('close', event => {
    if (closed) return;
    event.preventDefault();
    if (closing) return;
    closing = true;
    void (async () => {
      try { await inputQueue; }
      catch (error) { console.error('Window input outcome remains unconfirmed:', String(error)); }
      try {
        if (identity) {
          const result = await request(options.state, { command: 'window_close' }, identity);
          if (!result.ok) throw new Error(result.error);
        }
      } catch (error) { console.error('Window credential revocation was not confirmed:', String(error)); }
      finally { closed = true; window.destroy(); }
    })();
  });
  window.on('closed', () => {
    for (const channel of ['a2a:snapshot', 'a2a:output', 'a2a:input', 'a2a:composition-start', 'a2a:release-queue', 'a2a:focus-observation']) ipcMain.removeHandler(channel);
  });
  app.on('window-all-closed', () => app.quit());
  await window.loadFile(join(directory, 'renderer/index.html'));
  return window;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { values } = parseArgs({ args: process.argv.slice(2), options: Object.fromEntries(
    ['state', 'task', 'launch', 'user-data'].map((key) => [key, { type: 'string' as const }])) });
  const state = values.state ?? join(homedir(), 'Library/Application Support/a2a-orchestrator');
  run({ state, task: values.task!, launch: values.launch, userData: values['user-data'] ?? join(state, 'ui') })
    .catch((error) => { console.error(error); app.exit(1); });
}
