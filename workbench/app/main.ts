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

type Options = { state: string; task?: string; launch?: string | string[]; userData: string };
type PaneBinding = {
  key: string; launch?: string; project?: string; identity?: Record<string, unknown>; opening?: Promise<void>;
  sequence: number; inputQueue: Promise<unknown>; pendingRelease: Promise<any> | null;
  closing?: boolean;
};
type WindowBinding = {
  window: BrowserWindow; options: Options; operator: NonNullable<ReturnType<typeof readOperatorCredential>>;
  panes: Map<string, PaneBinding>; closing: boolean; closed: boolean;
  task: any; switching?: Promise<unknown>; creating?: Promise<unknown>;
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

function requireShellPane(project: string, launch: string, result: any) {
  if (!result.ok) throw new Error(result.error);
  const record = result.launch;
  if (typeof launch !== 'string' || !launch || result.task !== null || record?.id !== launch || record.role !== 'shell' || record.project !== project ||
      record.task !== null || record.attempt !== null || record.session !== null || record.fence !== null) {
    throw new Error('Shell project or launch mismatch');
  }
}

function windowTarget(event: Electron.IpcMainInvokeEvent) {
  const context = windows.get(event.sender.id);
  if (!context || event.sender !== context.window.webContents || event.senderFrame !== event.sender.mainFrame) {
    throw new Error('Unknown window');
  }
  return context;
}
function target(event: Electron.IpcMainInvokeEvent, key: string) {
  const context = windowTarget(event);
  if (context.switching || context.closing) throw new Error('Task view is changing');
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
  ipcMain.handle('a2a:projects', async event => {
    const context = windowTarget(event);
    const result = await request(context.options.state, { command: 'projects_list' });
    if (!result.ok) throw new Error(result.error);
    return result.projects;
  });
  ipcMain.handle('a2a:tasks', async (event, project: string) => {
    const context = windowTarget(event);
    const result = await request(context.options.state, { command: 'tasks_list', project });
    if (!result.ok) throw new Error(result.error);
    return result.tasks;
  });
  ipcMain.handle('a2a:selection', event => selection(windowTarget(event)));
  ipcMain.handle('a2a:new-terminal', async event => {
    const context = windowTarget(event);
    if (context.closing || context.switching || context.creating || [...context.panes.values()].some(pane => pane.closing)) {
      throw new Error('Task view is changing');
    }
    if (!context.options.task || !context.task) throw new Error('请先选择任务');
    const create = async () => {
      const current = await request(context.options.state, { command: 'workbench_snapshot', task: context.options.task });
      if (!current.ok) throw new Error(current.error);
      if (context.closing || current.task?.task_id !== context.options.task || current.task.project_id !== context.task.project_id ||
          typeof current.task.repo !== 'string' || !isAbsolute(current.task.repo)) throw new Error('项目目录无法核对');
      const result = await request(context.options.state, { command: 'shell_start',
        project: current.task.project_id, cwd: current.task.repo }, context.operator);
      requireShellPane(current.task.project_id, result.launch?.id, { ...result, task: null });
      const pane: PaneBinding = { key: randomUUID(), launch: result.launch.id, project: result.launch.project,
        sequence: 0, inputQueue: Promise.resolve(), pendingRelease: null };
      for (const [key, existing] of context.panes) {
        if (!existing.launch && !existing.identity && !existing.opening && !current.launch) context.panes.delete(key);
      }
      context.panes.set(pane.key, pane);
      context.task = current.task;
      return selection(context);
    };
    context.creating = create();
    try { return await context.creating; }
    finally { context.creating = undefined; }
  });
  ipcMain.handle('a2a:select-task', async (event, task: string | null) => {
    const context = windowTarget(event);
    if (task !== null && (typeof task !== 'string' || !task)) throw new Error('Invalid task');
    if (context.closing || context.switching || context.creating || [...context.panes.values()].some(pane => pane.closing)) throw new Error('Task view is changing');
    if (task === (context.options.task ?? null)) return selection(context);
    const change = async () => {
      const options = { ...context.options, task: task ?? undefined, launch: undefined };
      // Validate the destination before detaching the current view. Switching
      // never closes a saved pane or stops a background session.
      const prepared = await prepareSelection(options);
      if (context.closing) throw new Error('Window is closing');
      for (const pane of context.panes.values()) pane.closing = true;
      try {
        await detachPanes(context);
        if (context.closing) throw new Error('Window is closing');
        context.options = options;
        context.task = prepared.task;
        context.panes = new Map(prepared.panes.map(pane => [pane.key, pane]));
        return selection(context);
      } finally { for (const pane of context.panes.values()) pane.closing = false; }
    };
    context.switching = change();
    try { return await context.switching; }
    finally { context.switching = undefined; }
  });
  ipcMain.handle('a2a:snapshot', async (event, key: string) => {
    const { context, pane } = target(event, key);
    const task = context.options.task!;
    const scope = pane.project ? { project: pane.project } : { task };
    const result = await request(context.options.state, { command: 'workbench_snapshot', ...scope,
      ...(pane.launch ? { launch: pane.launch } : {}) });
    if (context.switching || pane.closing || context.panes.get(key) !== pane) throw new Error('Task view changed');
    if (!result.ok) throw new Error(result.error);
    if (pane.project) requireShellPane(pane.project, pane.launch!, result);
    else if ([...context.panes.values()].filter(value => !value.project).length > 1) requireSavedPane(task, pane.launch!, result);
    if (pane.launch && result.launch?.id !== pane.launch) throw new Error('Pane launch changed');
    if (result.launch && !pane.launch) {
      const opened = await request(context.options.state, { command: 'pane_layout_open', task,
        launch: result.launch.id, position: [...context.panes.keys()].indexOf(pane.key) }, context.operator);
      if (!opened.ok) throw new Error(opened.error);
      pane.launch = result.launch.id;
    }
    if (context.switching || pane.closing || context.panes.get(key) !== pane) throw new Error('Task view changed');
    const writable = !result.recovering && !pane.closing && result.pane?.lifecycle === 'running' && !result.pane.failed &&
      result.pane?.restoration?.status !== 'pending' &&
      Boolean(result.launch && (pane.project && result.launch.role === 'shell' ||
        result.launch.role === 'controller' && result.launch.attempt === null ||
        result.launch.attempt !== null && result.task.current_attempt?.attempt_id === result.launch.attempt));
    if (writable && result.launch && !pane.identity && !context.closing) {
      // Concurrent snapshot readers share one credential request, including a failed outcome.
      // Closing waits for this request before revoking a credential it may have issued.
      pane.opening ??= request(context.options.state, { command: 'window_open', ...scope, launch: pane.launch }, context.operator)
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
      const closed = await request(context.options.state, { command: 'pane_layout_close',
        ...(pane.project ? { project: pane.project } : { task: context.options.task }),
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

function selection(context: WindowBinding) {
  return { task: context.task, paneKeys: [...context.panes.keys()] };
}

async function detachPanes(context: WindowBinding) {
  const outcomes = await Promise.allSettled([...context.panes.values()].flatMap(pane =>
    [pane.inputQueue, pane.pendingRelease, pane.opening]));
  for (const outcome of outcomes) if (outcome.status === 'rejected') console.error('Window input outcome remains unconfirmed:', String(outcome.reason));
  const revocations = await Promise.allSettled([...context.panes.values()].filter(pane => pane.identity).map(async pane => {
    const result = await request(context.options.state, { command: 'window_close' }, pane.identity);
    if (!result.ok) throw new Error(result.error);
    pane.identity = undefined;
    pane.opening = undefined;
  }));
  const failed = revocations.filter(result => result.status === 'rejected');
  if (failed.length) throw new AggregateError(failed.map(result => result.reason), 'Window credential revocation was not confirmed');
}

async function prepareSelection(options: Options) {
  if (!options.task) {
    if (options.launch !== undefined) throw new Error('--launch requires --task');
    return { task: null, saved: true, panes: [] as PaneBinding[] };
  }
  const snapshot = await request(options.state, { command: 'workbench_snapshot', task: options.task });
  if (!snapshot.ok) throw new Error(snapshot.error);
  let saved = false;
  let launches: (string | undefined)[];
  if (options.launch === undefined) {
    const layout = await request(options.state, { command: 'pane_layout', task: options.task });
    if (!layout.ok) throw new Error(layout.error);
    launches = layout.panes.map((pane: { launch: string }) => pane.launch);
    saved = layout.saved;
    if (!saved) launches = [undefined];
  } else launches = typeof options.launch === 'string' ? [options.launch] : [...options.launch];
  if ((!launches.length && !saved) || launches.some(launch => launch !== undefined && (typeof launch !== 'string' || !launch)) ||
      new Set(launches).size !== launches.length) throw new Error('Distinct nonempty pane launches are required');
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
  let panes: PaneBinding[] = launches.map(launch => ({ key: randomUUID(), launch, sequence: 0,
    inputQueue: Promise.resolve(), pendingRelease: null }));
  const shells = await request(options.state, { command: 'pane_layout', project: snapshot.task.project_id });
  if (!shells.ok) throw new Error(shells.error);
  for (const opened of shells.panes.filter((pane: { task: string | null }) => pane.task === null)) {
    const value = await request(options.state, { command: 'workbench_snapshot', project: snapshot.task.project_id, launch: opened.launch });
    requireShellPane(snapshot.task.project_id, opened.launch, value);
    panes.push({ key: randomUUID(), launch: opened.launch, project: snapshot.task.project_id,
      sequence: 0, inputQueue: Promise.resolve(), pendingRelease: null });
  }
  if (panes.some(pane => pane.project) && !snapshot.launch) panes = panes.filter(pane => pane.launch !== undefined);
  return { task: snapshot.task, saved, panes };
}

export async function run(options: Options) {
  if (!isAbsolute(options.state) || !isAbsolute(options.userData)) throw new Error('Absolute data paths are required');
  const { task, saved, panes } = await prepareSelection(options);
  const operator = readOperatorCredential(options.state);
  if (!operator) throw new Error('operator_credential_required');
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
  const window = new BrowserWindow({ width: 1440, height: 900, minWidth: 900, minHeight: 650,
    title: 'a2a 工作台', backgroundColor: '#111111',
    webPreferences: { preload: join(directory, 'preload.cjs'), nodeIntegration: false,
      contextIsolation: true, sandbox: true, backgroundThrottling: false,
      additionalArguments: ['--a2a-pane-keys=' + JSON.stringify(panes.map(pane => pane.key))] } });
  const context: WindowBinding = { window, options, operator, task, panes: new Map(panes.map(pane => [pane.key, pane])), closing: false, closed: false };
  const senderId = window.webContents.id;
  windows.set(senderId, context);
  registerHandlers();
  // Persist creation before exposing the window. A crash must not depend on a
  // shutdown hook. Reopening an existing failed pane preserves its diagnosis.
  if (!saved) for (const [position, pane] of panes.entries()) {
    if (!pane.launch) continue;
    const opened = await request(options.state, { command: 'pane_layout_open',
      ...(pane.project ? { project: pane.project } : { task: options.task }), launch: pane.launch, position }, operator);
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
      if (context.switching) await Promise.allSettled([context.switching]);
      if (context.creating) await Promise.allSettled([context.creating]);
      try { await detachPanes(context); }
      catch (error) { console.error('Window credential revocation was not confirmed:', String(error)); }
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
