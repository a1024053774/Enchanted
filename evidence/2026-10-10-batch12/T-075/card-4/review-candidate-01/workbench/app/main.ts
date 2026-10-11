import { app, BrowserWindow, ipcMain } from 'electron';
import { mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { request } from '../src/transport.ts';

type Options = { state: string; task: string; launch?: string; userData: string };
const directory = dirname(fileURLToPath(import.meta.url));

export async function run(options: Options) {
  if (!isAbsolute(options.state) || !isAbsolute(options.userData) || !options.task) throw new Error('Absolute data paths and a task are required');
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
  const checkSender = (event: Electron.IpcMainInvokeEvent) => {
    if (event.sender !== window.webContents || event.senderFrame !== window.webContents.mainFrame) throw new Error('Unknown window');
  };
  ipcMain.handle('a2a:snapshot', async (event) => {
    checkSender(event);
    const result = await request(options.state, { command: 'workbench_snapshot', task: options.task, ...(launch ? { launch } : {}) });
    if (!result.ok) throw new Error(result.error);
    if (result.launch) launch = result.launch.id;
    return result;
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
  window.on('closed', () => { ipcMain.removeHandler('a2a:snapshot'); ipcMain.removeHandler('a2a:output'); });
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
