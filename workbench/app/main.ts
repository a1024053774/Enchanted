import { app, BrowserWindow, ipcMain } from 'electron';
import { mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { request } from '../src/transport.ts';
import { readOperatorCredential } from '../src/credentials.ts';
import { randomUUID } from 'node:crypto';
import type { EmptyInputDeclaration } from '../src/panes.ts';

type Options = { state: string; task: string; launch?: string | string[]; userData: string };
type PaneBinding = {
  key: string; launch?: string; identity?: Record<string, unknown>; opening?: Promise<void>;
  sequence: number; inputQueue: Promise<unknown>; pendingRelease: Promise<any> | null;
  closing?: boolean;
};
type WindowBinding = {
  window: BrowserWindow; options: Options; operator: NonNullable<ReturnType<typeof readOperatorCredential>>;
  panes: Map<string, PaneBinding>; closing: boolean; closed: boolean;
};
const directory = dirname(fileURLToPath(import.meta.url));
const windows = new Map<number, WindowBinding>();
let handlersRegistered = false;
let appUserData: string | undefined;

function requireCurrentPane(task: string, launch: string, result: any) {
  if (!result.ok) throw new Error(result.error);
  const record = result.launch;
  if (result.task?.task_id !== task || record?.task !== task || record?.id !== launch) throw new Error('Pane task or launch mismatch');
  if (result.pane?.lifecycle !== 'running' || result.pane.failed || result.pane.historical ||
      !(record.role === 'controller' && record.attempt === null && ['ideation', 'executor'].includes(record.preset) ||
        record.role === 'worker' && record.attempt !== null && result.task.current_attempt?.attempt_id === record.attempt)) {
    throw new Error('Pane is not a current running session');
  }
}

function requireSavedPane(task: string, launch: string, result: any) {
  if (result.ok && result.task?.task_id === task && result.launch?.task === task && result.launch?.id === launch &&
      ['failed', 'pending'].includes(result.pane?.restoration?.status)) return;
  requireCurrentPane(task, launch, result);
}

function target(event: Electron.IpcMainInvokeEvent, key: string) {
  const context = windows.get(event.sender.id);
  if (!context || event.sender !== context.window.webContents || event.senderFrame !== event.sender.mainFrame) {
    throw new Error('Unknown window');
  }
  const pane = typeof key === 'string' ? context.panes.get(key) : undefined;
  if (!pane) throw new Error('Unknown pane key');
  return { context, pane };
}

function sendWindowCommand(context: WindowBinding, pane: PaneBinding, input: Record<string, unknown>) {
  if (!pane.identity || context.closing || pane.closing) throw new Error('Window is not available for input');
  if (input.command === 'window_release' && pane.pendingRelease) throw new Error('Queue release is already pending');
  const command = { ...input, sequence: ++pane.sequence, request_id: randomUUID() };
  const receive = (result: any) => {
    if (input.command === 'window_release' && !result.ok &&
        ['empty_input_declaration_required', 'empty_input_declaration_stale', 'pane_not_interrupted'].includes(result.error)) return result;
    if (!result.ok) throw new Error(result.error);
    return result;
  };
  if (input.command === 'window_release') {
    // Panes owns PTY write order; later input can invalidate a pending declaration.
    let response: Promise<any>;
    pane.inputQueue = pane.inputQueue.then(() => { response = request(context.options.state, command, pane.identity); });
    const result = pane.inputQueue.then(() => response).then(receive);
    pane.pendingRelease = result;
    const finished = () => { if (pane.pendingRelease === result) pane.pendingRelease = null; };
    void result.then(finished, finished);
    return result;
  }
  pane.inputQueue = pane.inputQueue.then(() => request(context.options.state, command, pane.identity)).then(receive);
  return pane.inputQueue;
}

function registerHandlers() {
  if (handlersRegistered) return;
  handlersRegistered = true;
  ipcMain.handle('a2a:snapshot', async (event, key: string) => {
    const { context, pane } = target(event, key);
    const result = await request(context.options.state, { command: 'workbench_snapshot', task: context.options.task,
      ...(pane.launch ? { launch: pane.launch } : {}) });
    if (!result.ok) throw new Error(result.error);
    if (context.panes.size > 1) requireSavedPane(context.options.task, pane.launch!, result);
    if (pane.launch && result.launch?.id !== pane.launch) throw new Error('Pane launch changed');
    if (result.launch && !pane.launch) {
      const opened = await request(context.options.state, { command: 'pane_layout_open', task: context.options.task,
        launch: result.launch.id, position: [...context.panes.keys()].indexOf(pane.key) }, context.operator);
      if (!opened.ok) throw new Error(opened.error);
      pane.launch = result.launch.id;
    }
    const writable = !result.recovering && !pane.closing && result.pane?.lifecycle === 'running' && !result.pane.failed &&
      result.pane?.restoration?.status !== 'pending' &&
      Boolean(result.launch && (result.launch.role === 'controller' && result.launch.attempt === null ||
        result.launch.attempt !== null && result.task.current_attempt?.attempt_id === result.launch.attempt));
    if (writable && result.launch && !pane.identity && !context.closing) {
      // Concurrent snapshot readers share one credential request, including a failed outcome.
      // Closing waits for this request before revoking a credential it may have issued.
      pane.opening ??= request(context.options.state, { command: 'window_open', task: context.options.task, launch: pane.launch }, context.operator)
        .then(opened => {
          if (!opened.ok) throw new Error(opened.error);
          pane.identity = opened.identity;
        });
      await pane.opening;
    }
    return { ...result, pane_key: pane.key, window_id: pane.identity?.window,
      input_enabled: Boolean(writable && pane.identity && !context.closing) };
  });
  ipcMain.handle('a2a:input', (event, key: string, data: string, encoding: 'utf8' | 'binary' = 'utf8') => {
    const { context, pane } = target(event, key);
    if (!['utf8', 'binary'].includes(encoding) || typeof data !== 'string' ||
        (encoding === 'binary' ? data.length : Buffer.byteLength(data, 'utf8')) > 1024 * 1024 ||
        (encoding === 'binary' && [...data].some(char => char.charCodeAt(0) > 255))) throw new Error('Invalid terminal input');
    return sendWindowCommand(context, pane, { command: 'window_input', data, encoding });
  });
  ipcMain.handle('a2a:composition-start', (event, key: string) => {
    const { context, pane } = target(event, key);
    return sendWindowCommand(context, pane, { command: 'window_composition' });
  });
  ipcMain.handle('a2a:release-queue', (event, key: string, declaration: EmptyInputDeclaration) => {
    const { context, pane } = target(event, key);
    return sendWindowCommand(context, pane, { command: 'window_release', declaration });
  });
  ipcMain.handle('a2a:focus-observation', (event, key: string, rawSequence: string) => {
    const { context, pane } = target(event, key);
    if (typeof rawSequence !== 'string' || rawSequence.length > 4096) throw new Error('Invalid focus observation');
    return sendWindowCommand(context, pane, { command: 'window_observation', type: 'focus-mode-intercept', raw_sequence: rawSequence });
  });
  ipcMain.handle('a2a:output', async (event, key: string, offset: number) => {
    const { context, pane } = target(event, key);
    if (!pane.launch || !Number.isSafeInteger(offset) || offset < 0) throw new Error('Invalid output request');
    const result = await request(context.options.state, { command: 'pane_output', launch: pane.launch, offset, max_bytes: 65536 });
    if (!result.ok) throw new Error(result.error);
    return result;
  });
  ipcMain.handle('a2a:close-pane', async (event, key: string) => {
    const { context, pane } = target(event, key);
    if (pane.closing || context.closing) throw new Error('Pane is closing');
    pane.closing = true;
    const outcomes = await Promise.allSettled([pane.inputQueue, pane.pendingRelease, pane.opening]);
    for (const outcome of outcomes) if (outcome.status === 'rejected') console.error('Pane input outcome remains unconfirmed:', String(outcome.reason));
    if (pane.launch) {
      const closed = await request(context.options.state, { command: 'pane_layout_close', task: context.options.task,
        launch: pane.launch }, context.operator);
      if (!closed.ok) { pane.closing = false; throw new Error(closed.error); }
    }
    if (pane.identity) {
      const closed = await request(context.options.state, { command: 'window_close' }, pane.identity);
      if (!closed.ok) throw new Error(closed.error);
    }
    context.panes.delete(key);
    return { ok: true };
  });
  app.on('window-all-closed', () => app.quit());
}

export async function run(options: Options) {
  if (!isAbsolute(options.state) || !isAbsolute(options.userData) || !options.task) throw new Error('Absolute data paths and a task are required');
  let saved = false;
  let launches: (string | undefined)[];
  if (options.launch === undefined) {
    const layout = await request(options.state, { command: 'pane_layout', task: options.task });
    if (!layout.ok) throw new Error(layout.error);
    launches = layout.panes.map((pane: { launch: string }) => pane.launch);
    saved = launches.length > 0;
    if (!saved) launches = [undefined];
  } else launches = typeof options.launch === 'string' ? [options.launch] : [...options.launch];
  if (!launches.length || launches.some(launch => launch !== undefined && (typeof launch !== 'string' || !launch)) ||
      new Set(launches).size !== launches.length) throw new Error('Distinct nonempty pane launches are required');
  const operator = readOperatorCredential(options.state);
  if (!operator) throw new Error('operator_credential_required');
  if (launches.length > 1) {
    // Reject the complete selection before creating a window or input credential.
    const ranks = new Map<string, number>();
    for (const launch of launches) {
      const value = await request(options.state, { command: 'workbench_snapshot', task: options.task, launch });
      (saved ? requireSavedPane : requireCurrentPane)(options.task, launch!, value);
      ranks.set(launch!, value.launch.role === 'worker' ? 2 : value.launch.preset === 'ideation' ? 0 : 1);
    }
    if (!saved) launches.sort((a, b) => ranks.get(a!)! - ranks.get(b!)!);
  }
  if (appUserData && appUserData !== options.userData) throw new Error('Windows in one process must share application user-data');
  if (!appUserData) {
    appUserData = options.userData;
    const sessionData = join(options.userData, 'session');
    for (const path of [options.userData, sessionData, join(options.userData, 'logs'), join(options.userData, 'crashes')]) {
      mkdirSync(path, { recursive: true, mode: 0o700 });
    }
    app.setPath('userData', options.userData);
    app.setPath('sessionData', sessionData);
    app.setPath('logs', join(options.userData, 'logs'));
    app.setPath('crashDumps', join(options.userData, 'crashes'));
  }
  await app.whenReady();
  const panes: PaneBinding[] = launches.map(launch => ({ key: randomUUID(), launch, sequence: 0,
    inputQueue: Promise.resolve(), pendingRelease: null }));
  const window = new BrowserWindow({ width: 1440, height: 900, minWidth: 900, minHeight: 650,
    title: 'a2a 工作台', backgroundColor: '#111111',
    webPreferences: { preload: join(directory, 'preload.cjs'), nodeIntegration: false,
      contextIsolation: true, sandbox: true, backgroundThrottling: false,
      additionalArguments: ['--a2a-pane-keys=' + JSON.stringify(panes.map(pane => pane.key))] } });
  const context: WindowBinding = { window, options, operator, panes: new Map(panes.map(pane => [pane.key, pane])), closing: false, closed: false };
  const senderId = window.webContents.id;
  windows.set(senderId, context);
  registerHandlers();
  // Persist creation before exposing the window. A crash must not depend on a
  // shutdown hook. Reopening an existing failed pane preserves its diagnosis.
  if (!saved) for (const [position, pane] of panes.entries()) {
    if (!pane.launch) continue;
    const opened = await request(options.state, { command: 'pane_layout_open', task: options.task, launch: pane.launch, position }, operator);
    if (!opened.ok) { window.destroy(); throw new Error(opened.error); }
  }
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  window.webContents.on('will-navigate', event => event.preventDefault());
  window.on('close', event => {
    if (context.closed) return;
    event.preventDefault();
    if (context.closing) return;
    context.closing = true;
    void (async () => {
      const outcomes = await Promise.allSettled([...context.panes.values()].flatMap(value =>
        [value.inputQueue, value.pendingRelease, value.opening]));
      for (const outcome of outcomes) if (outcome.status === 'rejected') console.error('Window input outcome remains unconfirmed:', String(outcome.reason));
      for (const value of context.panes.values()) {
        try {
          if (value.identity) {
            const result = await request(options.state, { command: 'window_close' }, value.identity);
            if (!result.ok) throw new Error(result.error);
          }
        } catch (error) { console.error('Window credential revocation was not confirmed:', String(error)); }
      }
      context.closed = true;
      window.destroy();
    })();
  });
  window.on('closed', () => { windows.delete(senderId); });
  await window.loadFile(join(directory, 'renderer/index.html'));
  return window;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { values } = parseArgs({ args: process.argv.slice(2), options: Object.fromEntries(
    ['state', 'task', 'launch', 'user-data'].map(key => [key, { type: 'string' as const, ...(key === 'launch' ? { multiple: true } : {}) }])) });
  const state = values.state ?? join(homedir(), 'Library/Application Support/a2a-orchestrator');
  run({ state, task: values.task!, launch: values.launch, userData: values['user-data'] ?? join(state, 'ui') })
    .catch(error => { console.error(error); app.exit(1); });
}
