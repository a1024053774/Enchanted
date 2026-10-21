import { app, BrowserWindow, ipcMain, dialog, nativeTheme } from 'electron';
import { mkdirSync, mkdtempSync, writeFileSync, rmSync, realpathSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { dirname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs, promisify, isDeepStrictEqual } from 'node:util';
import { execFile } from 'node:child_process';
import { request } from '../src/transport.ts';
import { readOperatorCredential } from '../src/credentials.ts';
import { randomUUID } from 'node:crypto';
import { NotificationCenter, type NotificationPreference } from './notificationCenter.ts';
import type { EmptyInputDeclaration } from '../src/panes.ts';

type Options = { state: string; task?: string; launch?: string | string[]; userData: string };
type PaneBinding = {
  key: string; launch?: string; project?: string | null; identity?: Record<string, unknown>; opening?: Promise<void>;
  sequence: number; inputQueue: Promise<unknown>; pendingRelease: Promise<any> | null;
  closing?: boolean;
  viewOnly?: boolean;
};
type WindowBinding = {
  window: BrowserWindow; options: Options; operator: NonNullable<ReturnType<typeof readOperatorCredential>>;
  panes: Map<string, PaneBinding>; closing: boolean; closed: boolean;
  layout: Layout | null; names: Record<string, string>;
  task: any; switching?: Promise<unknown>; creating?: Promise<unknown>;
  creation?: { repo: string; persisted: boolean | 'unknown' };
};
const execute = promisify(execFile);
const directory = dirname(fileURLToPath(import.meta.url));
const windows = new Map<number, WindowBinding>();
let handlersRegistered = false;
let appUserData: string | undefined;
const notificationCenters = new Map<string, NotificationCenter>();
function notificationCenter(context: WindowBinding) {
  const key = JSON.stringify([context.options.state, context.options.userData]);
  let center = notificationCenters.get(key);
  if (!center) { center = new NotificationCenter(context.options.userData); notificationCenters.set(key, center); }
  return center;
}
function updateDockBadge() {
  // Multiple desktop windows observe the same catalog; count it only once.
  const counts = new Map<string, number>();
  for (const context of windows.values()) counts.set(context.options.state,
    Math.max(counts.get(context.options.state) ?? 0, notificationCenter(context).badgeCount()));
  const count = BrowserWindow.getFocusedWindow() ? 0 : [...counts.values()].reduce((sum, count) => sum + count, 0);
  app.dock.setBadge(count ? String(count) : '');
}

function requireAgentView(task: string, launch: string, result: any) {
  if (!result.ok || result.task?.task_id !== task || result.launch?.task !== task || result.launch?.id !== launch ||
      !['controller', 'worker', 'reviewer', 'monitor'].includes(result.launch.role)) throw new Error('Agent task or launch mismatch');
}

type Layout = string | { direction: 'right' | 'down'; first: Layout; second: Layout };
function replaceLeaf(tree: Layout | null, key: string, replacement: Layout | null): Layout | null {
  if (tree === null || typeof tree === 'string') return tree === key ? replacement : tree;
  const first = replaceLeaf(tree.first, key, replacement), second = replaceLeaf(tree.second, key, replacement);
  return first && second ? { ...tree, first, second } : first ?? second;
}
function mapLayout(tree: Layout | null, convert: (key: string) => string | null): Layout | null {
  if (tree === null) return null;
  if (typeof tree === 'string') return convert(tree);
  const first = mapLayout(tree.first, convert), second = mapLayout(tree.second, convert);
  return first && second ? { ...tree, first, second } : first ?? second;
}
function serializedArrangement(context: WindowBinding, tree = context.layout, names = context.names) {
  return { tree: mapLayout(tree, key => context.panes.get(key)?.viewOnly ? null : context.panes.get(key)?.launch ?? null),
    names: Object.fromEntries(Object.entries(names).flatMap(([key, name]) => {
      const pane = context.panes.get(key), id = pane?.launch; return id && !pane.viewOnly ? [[id, name]] : [];
    })) };
}
async function saveArrangement(context: WindowBinding) {
  const result = await request(context.options.state, { command: 'pane_layout_save', task: context.options.task,
    arrangement: serializedArrangement(context) }, context.operator);
  if (!result.ok) throw new Error(result.error);
}

function requireCurrentPane(task: string, launch: string, result: any) {
  if (!result.ok) throw new Error(result.error);
  const record = result.launch;
  if (result.task?.task_id !== task || record?.task !== task || record?.id !== launch) throw new Error('Pane task or launch mismatch');
  if (result.pane?.lifecycle !== 'running' || result.pane.failed || result.pane.historical ||
      !(record.role === 'controller' && record.attempt === null && ['ideation', 'executor'].includes(record.preset) ||
        record.role === 'worker' && record.attempt !== null && result.task.current_attempt?.attempt_id === record.attempt ||
        record.role === 'reviewer' && record.attempt !== null)) {
    throw new Error('Pane is not a current running session');
  }
}

function requireSavedPane(task: string, launch: string, result: any) {
  if (result.ok && result.task?.task_id === task && result.launch?.task === task && result.launch?.id === launch &&
      ['failed', 'pending'].includes(result.pane?.restoration?.status)) return;
  requireCurrentPane(task, launch, result);
}

function requireShellPane(project: string | null, launch: string, result: any) {
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
  // A failed connection sends nothing and must not consume a daemon sequence.
  // Once connected, an unknown outcome still consumes it; commands are never replayed.
  const command = { ...input, request_id: randomUUID() };
  const receive = (result: any) => {
    if (input.command === 'window_release' && !result.ok &&
        ['empty_input_declaration_required', 'empty_input_declaration_stale', 'pane_not_interrupted'].includes(result.error)) return result;
    if (!result.ok) throw new Error(result.error);
    return result;
  };
  if (input.command === 'window_release') {
    // Panes owns PTY write order; later input can invalidate a pending declaration.
    let response: Promise<any>;
    pane.inputQueue = pane.inputQueue.then(() => { response = request(context.options.state, command, pane.identity, () => ++pane.sequence); });
    const result = pane.inputQueue.then(() => response).then(receive);
    pane.pendingRelease = result;
    const finished = () => { if (pane.pendingRelease === result) pane.pendingRelease = null; };
    void result.then(finished, finished);
    return result;
  }
  const result = pane.inputQueue.then(() => request(context.options.state, command, pane.identity, () => ++pane.sequence)).then(receive);
  pane.inputQueue = result.then(() => undefined, () => undefined);
  return result;
}

function registerHandlers() {
  if (handlersRegistered) return;
  handlersRegistered = true;
  app.on('browser-window-focus', updateDockBadge);
  app.on('browser-window-blur', updateDockBadge);
  ipcMain.handle('a2a:execution-settings', async (event, change?: { role: string; model: string; effort: string; fast: boolean }) => {
    const context = windowTarget(event);
    if (change !== undefined && (!change || typeof change !== 'object' || Array.isArray(change) ||
      Object.keys(change).sort().join(',') !== 'effort,fast,model,role' ||
      !['worker', 'reviewer', 'monitor', 'ideation', 'executor'].includes(change.role) ||
      ![change.model, change.effort].every(value => typeof value === 'string' && value.trim() && !/[\0\r\n]/.test(value)) ||
      typeof change.fast !== 'boolean')) throw new Error('Invalid execution settings');
    const result = await request(context.options.state, change === undefined ? { command: 'execution_settings' } :
      { command: 'execution_settings_save', ...change }, context.operator);
    if (!result.ok) throw new Error(result.error);
    return result.settings;
  });
  ipcMain.handle('a2a:notification-setting', (event, enabled?: boolean, preference: NotificationPreference = 'notifications') => {
    const context = windowTarget(event);
    if (enabled !== undefined && typeof enabled !== 'boolean') throw new Error('Invalid notification setting');
    if (!['notifications', 'dockBadges'].includes(preference)) throw new Error('Invalid notification preference');
    const value = notificationCenter(context).setting(enabled, preference);
    updateDockBadge();
    return value;
  });
  ipcMain.handle('a2a:flow', async event => {
    const context = windowTarget(event);
    const result = await request(context.options.state, { command: 'flow_snapshot' });
    if (!result.ok) throw new Error(result.error);
    return { lanes: result.lanes, unassigned: result.unassigned };
  });
  ipcMain.handle('a2a:sidebar', async event => {
    const context = windowTarget(event);
    let result: Awaited<ReturnType<typeof request>>;
    try {
      result = await request(context.options.state, { command: 'sidebar_snapshot' });
      if (!result.ok) throw new Error(result.error);
    } catch (error) {
      // A failed read removes the basis for this catalog's current reminders.
      // Keep seen question IDs; reconnecting cannot emit the same reminder again.
      for (const sibling of windows.values()) {
        if (sibling.options.state === context.options.state) notificationCenter(sibling).invalidate();
      }
      updateDockBadge();
      throw error;
    }
    const notices = notificationCenter(context).observe(result.agents);
    updateDockBadge();
    return { ...result, notices, notifications: notificationCenter(context).setting(),
      dockBadges: notificationCenter(context).setting(undefined, 'dockBadges') };
  });
  ipcMain.handle('a2a:select-agent', async (event, launch: string) => {
    const context = windowTarget(event);
    if (typeof launch !== 'string' || !launch) throw new Error('Invalid agent launch');
    if (context.closing || context.switching || context.creating || [...context.panes.values()].some(p => p.closing)) throw new Error('Task view is changing');
    const select = async () => {
      const catalog = await request(context.options.state, { command: 'sidebar_snapshot' });
      if (!catalog.ok) throw new Error(catalog.error);
      const agent = catalog.agents.find((row: any) => row.id === launch);
      if (!agent?.task || !catalog.projects.some((p: any) => p.project_id === agent.project && p.tasks.some((t: any) => t.task_id === agent.task))) throw new Error('Unknown agent launch');
      const snapshot = await request(context.options.state, { command: 'workbench_snapshot', task: agent.task, launch });
      requireAgentView(agent.task, launch, snapshot);
      if (context.options.task !== agent.task) await changeTask(context, agent.task);
      let pane = [...context.panes.values()].find(p => p.launch === launch);
      if (!pane) {
        // A sidebar click may inspect an ended or old attempt. This transient
        // view never gets an input credential or changes the saved pane layout.
        pane = { key: randomUUID(), launch, viewOnly: true, sequence: 0, inputQueue: Promise.resolve(), pendingRelease: null };
        context.panes.set(pane.key, pane);
        context.layout = context.layout ? { direction: 'right', first: context.layout, second: pane.key } : pane.key;
      }
      return { ...selection(context), focusKey: pane.key };
    };
    context.switching = select();
    try { return await context.switching; } finally { context.switching = undefined; }
  });
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
  ipcMain.handle('a2a:creation-repository', async (event, ...args: unknown[]) => {
    const context = windowTarget(event);
    if (args.length) throw new Error('Repository path must be chosen by the native dialog');
    if (context.closing || context.switching || context.creating) throw new Error('Task view is changing');
    if (context.creation?.persisted) throw new Error('Registration has already started; close the previous form first');
    const choose = async () => {
      const picked = await dialog.showOpenDialog(context.window, { title: '选择 Git 仓库根目录',
        defaultPath: context.creation?.repo ?? context.task?.repo ?? homedir(), properties: ['openDirectory'] });
      if (picked.canceled) return null;
      const repo = realpathSync(picked.filePaths[0]);
      const top = await execute('git', ['-C', repo, 'rev-parse', '--show-toplevel']);
      if (realpathSync(top.stdout.trim()) !== repo) throw new Error('请选择 Git 仓库根目录');
      const branch = (await execute('git', ['-C', repo, 'symbolic-ref', '--quiet', 'HEAD'])).stdout.trim();
      if (context.closing) throw new Error('Window is closing');
      const task = 'task-' + randomUUID();
      const result = await request(context.options.state, { command: 'card_template', task, repo }, context.operator);
      if (!result.ok) throw new Error(result.error + ': ' + JSON.stringify(result.details ?? null));
      context.creation = { repo, persisted: false };
      return { repo, branch, card: result.card };
    };
    context.creating = choose();
    try { return await context.creating; } finally { context.creating = undefined; }
  });
  ipcMain.handle('a2a:creation-cancel', (event, ...args: unknown[]) => {
    const context = windowTarget(event);
    if (args.length) throw new Error('Invalid cancellation arguments');
    if (context.closing || context.switching || context.creating) throw new Error('Task view is changing');
    if (context.creation?.persisted === 'unknown') throw new Error('Registration outcome unknown; cancellation is forbidden');
    // No gate writes occur before confirmation. After a partial confirmation,
    // closing this form only forgets its UI state; append-only records survive.
    const persisted = context.creation?.persisted ?? false;
    context.creation = undefined;
    return { ok: true, persisted };
  });
  ipcMain.handle('a2a:creation-submit', async (event, input: Record<string, string>) => {
    const context = windowTarget(event), draft = context.creation;
    if (context.closing || context.switching || context.creating) throw new Error('Task view is changing');
    if (!draft) throw new Error('请先通过目录对话框选择仓库');
    if (draft.persisted) throw new Error('Registration has already started; do not replay it');
    const keys = ['task', 'project', 'title', 'branch', 'card'];
    if (!input || typeof input !== 'object' || Object.keys(input).length !== keys.length ||
        !keys.every(key => Object.hasOwn(input, key))) throw new Error('Invalid creation fields');
    const invalidField = keys.find(key => typeof input[key] !== 'string') ??
      (!input.title.trim() || input.title.length > 240 ? 'title' : undefined);
    if (invalidField) return { ok: false, error: 'Invalid creation fields', stage: 'preflight', persisted: false,
      details: { field: invalidField, reason: invalidField === 'title'
        ? '标题须为包含非空白字符的文本，且不超过 240 个字符。' : '表单字段须为文本。' } };
    const submit = async () => {
      const temporary = mkdtempSync(join(tmpdir(), 'a2a-task-card-'));
      const card = join(temporary, 'card.json');
      let stage = 'card_validate';
      let validatedCard: unknown;
      let cardVersion = 1; // This form saves with expected_version=0.
      const failure = async (result: any) => {
        // These gate refusals occur before the business commit. All other
        // errors, including daemon result-event failures, require readback.
        const beforeCommit = stage === 'card_save'
          ? ['invalid_task_card', 'invalid_card_version', 'card_version_conflict']
          : ['project_branch_conflict', 'invalid_work_branch', 'invalid_repo', 'invalid_title'];
        if (stage === 'card_validate' || beforeCommit.includes(result.error)) {
          draft.persisted = stage === 'create';
          return { ...result, stage, persisted: draft.persisted };
        }
        draft.persisted = 'unknown';
        const command = stage === 'card_save' ? 'card_show' : 'status';
        let observed: any;
        try {
          observed = await request(context.options.state, { command, task: input.task,
            ...(command === 'card_show' ? { card_version: cardVersion } : {}) }, context.operator);
        } catch (error) { observed = { ok: false, error: 'readback_failed', details: String(error) }; }
        const task = observed.task;
        const matches = observed.ok && (command === 'card_show'
          ? isDeepStrictEqual(observed.card, validatedCard)
          : task?.task_id === input.task && task.repo === draft.repo && task.project_id === input.project &&
            task.title === input.title && task.integration_ref === input.branch && task.card_version === cardVersion &&
            task.state === 'ready' && isDeepStrictEqual(task.card, validatedCard));
        const details = { failure: result.details ?? null, readback: { command,
          outcome: matches ? command === 'card_show' ? 'card_saved' : 'registered' : 'unknown',
          error: observed.error ?? null, details: observed.details ?? null } };
        if (matches) {
          draft.persisted = true;
          if (command === 'status') {
            context.creation = undefined;
            return { ok: true, task, stage, persisted: true, reconciled: true, details };
          }
        }
        // Absence, a mismatching record, or a failed read cannot establish
        // that an uncertain mutation never committed. Do not enable replay.
        return { ...result, details, stage, persisted: draft.persisted };
      };
      try {
        writeFileSync(card, input.card, { flag: 'wx', mode: 0o600 });
        const validated = await request(context.options.state, { command: stage, task: input.task, card }, context.operator);
        if (!validated.ok) return { ...validated, stage, persisted: false };
        validatedCard = validated.card;
        stage = 'card_save';
        // From this point a lost response can conceal a durable write. Never
        // silently retry or label the result as a cancelled draft.
        draft.persisted = true;
        const saved = await request(context.options.state, { command: stage, task: input.task, card, expected_version: 0 }, context.operator);
        if (!saved.ok) return await failure(saved);
        cardVersion = saved.card_version;
        stage = 'create';
        const created = await request(context.options.state, { command: stage, task: input.task,
          repo: draft.repo, project: input.project, title: input.title, branch: input.branch, card_version: saved.card_version }, context.operator);
        if (!created.ok) return await failure(created);
        context.creation = undefined;
        return { ...created, stage, persisted: true };
      } catch (error) {
        return await failure({ ok: false, error: 'creation_call_failed', details: String(error) });
      } finally { rmSync(temporary, { recursive: true, force: true }); }
    };
    context.creating = submit();
    try { return await context.creating; } finally { context.creating = undefined; }
  });
  ipcMain.handle('a2a:new-terminal', async (event, source: string = 'default') => {
    const context = windowTarget(event);
    if (!['default', 'home', 'project', 'choose'].includes(source)) throw new Error('Invalid terminal directory source');
    return createTerminal(context, source);
  });
  ipcMain.handle('a2a:pane-action', async (event, key: string, action: { type: string; direction?: string; name?: string }) => {
    const { context, pane } = target(event, key);
    if (context.creating || [...context.panes.values()].some(p => p.closing)) throw new Error('Task view is changing');
    if (!action || typeof action !== 'object') throw new Error('Invalid pane action');
    if (action.type === 'split') {
      if (!['right', 'down'].includes(action.direction!)) throw new Error('Invalid split direction');
      return createTerminal(context, 'split', pane, action.direction as 'right' | 'down');
    }
    if (action.type !== 'rename' || typeof action.name !== 'string' || !action.name.trim() || action.name.length > 100) throw new Error('Invalid pane name');
    const previous = context.names[key];
    context.names[key] = action.name.trim();
    context.creating = saveArrangement(context);
    try { await context.creating; }
    catch (error) { if (previous === undefined) delete context.names[key]; else context.names[key] = previous; throw error; }
    finally { context.creating = undefined; }
    return selection(context);
  });
  ipcMain.handle('a2a:select-task', async (event, task: string | null) => {
    const context = windowTarget(event);
    if (task !== null && (typeof task !== 'string' || !task)) throw new Error('Invalid task');
    if (context.closing || context.switching || context.creating || [...context.panes.values()].some(pane => pane.closing)) throw new Error('Task view is changing');
    if (task === (context.options.task ?? null)) return selection(context);
    context.switching = changeTask(context, task);
    try { return await context.switching; }
    finally { context.switching = undefined; }
  });
  ipcMain.handle('a2a:snapshot', async (event, key: string) => {
    const { context, pane } = target(event, key);
    const task = context.options.task!;
    const scope = pane.project !== undefined ? { project: pane.project } : { task };
    const result = await request(context.options.state, { command: 'workbench_snapshot', ...scope,
      ...(pane.launch ? { launch: pane.launch } : {}) });
    if (context.switching || pane.closing || context.panes.get(key) !== pane) throw new Error('Task view changed');
    if (!result.ok) throw new Error(result.error);
    if (pane.project !== undefined) requireShellPane(pane.project, pane.launch!, result);
    else if (pane.viewOnly) requireAgentView(task, pane.launch!, result);
    else if ([...context.panes.values()].filter(value => value.project === undefined && !value.viewOnly).length > 1) requireSavedPane(task, pane.launch!, result);
    if (pane.launch && result.launch?.id !== pane.launch) throw new Error('Pane launch changed');
    if (result.launch && !pane.launch) {
      const opened = await request(context.options.state, { command: 'pane_layout_open', task,
        launch: result.launch.id, position: [...context.panes.keys()].indexOf(pane.key) }, context.operator);
      if (!opened.ok) throw new Error(opened.error);
      pane.launch = result.launch.id;
    }
    if (context.switching || pane.closing || context.panes.get(key) !== pane) throw new Error('Task view changed');
    const writable = !pane.viewOnly && !result.recovering && !pane.closing && result.pane?.lifecycle === 'running' && !result.pane.failed &&
      result.pane?.restoration?.status !== 'pending' &&
      Boolean(result.launch && (pane.project !== undefined && result.launch.role === 'shell' ||
        result.launch.role === 'controller' && result.launch.attempt === null ||
        result.launch.role === 'worker' && result.launch.attempt !== null && result.task.current_attempt?.attempt_id === result.launch.attempt));
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
  ipcMain.handle('a2a:resize', (event, key: string, cols: number, rows: number) => {
    const { context, pane } = target(event, key);
    if (!Number.isInteger(cols) || cols < 2 || cols > 1000 || !Number.isInteger(rows) || rows < 1 || rows > 1000) throw new Error('Invalid terminal size');
    return sendWindowCommand(context, pane, { command: 'window_resize', cols, rows });
  });
  ipcMain.handle('a2a:input', (event, key: string, data: string, encoding: 'utf8' | 'binary' = 'utf8') => {
    const { context, pane } = target(event, key);
    if (!['utf8', 'binary'].includes(encoding) || typeof data !== 'string' ||
        (encoding === 'binary' ? data.length : Buffer.byteLength(data, 'utf8')) > 1024 * 1024 ||
        (encoding === 'binary' && [...data].some(char => char.charCodeAt(0) > 255))) throw new Error('Invalid terminal input');
    return sendWindowCommand(context, pane, { command: 'window_input', data, encoding });
  });
  ipcMain.handle('a2a:answer', (event, key: string, question: string, answers: string[]) => {
    const { context, pane } = target(event, key);
    if (typeof question !== 'string' || !question || question.length > 256 || !Array.isArray(answers) ||
        answers.length < 1 || answers.length > 4 || answers.some(answer => typeof answer !== 'string' || !answer.trim() || answer.length > 4000)) {
      throw new Error('Invalid question answer');
    }
    return sendWindowCommand(context, pane, { command: 'window_answer', question, answers });
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
    if (pane.closing || context.closing || context.creating) throw new Error('Pane is closing');
    pane.closing = true;
    const outcomes = await Promise.allSettled([pane.inputQueue, pane.pendingRelease, pane.opening]);
    for (const outcome of outcomes) if (outcome.status === 'rejected') console.error('Pane input outcome remains unconfirmed:', String(outcome.reason));
    const nextLayout = replaceLeaf(context.layout, key, null), nextNames = { ...context.names };
    delete nextNames[key];
    if (pane.launch && !pane.viewOnly) {
      const closed = await request(context.options.state, { command: 'pane_layout_close',
        ...(pane.project !== undefined ? { project: pane.project } : { task: context.options.task }),
        launch: pane.launch, layout_task: context.options.task, arrangement: serializedArrangement(context, nextLayout, nextNames) }, context.operator);
      if (!closed.ok) { pane.closing = false; throw new Error(closed.error); }
    }
    if (pane.identity) {
      const closed = await request(context.options.state, { command: 'window_close' }, pane.identity);
      if (!closed.ok) throw new Error(closed.error);
    }
    context.panes.delete(key);
    context.layout = nextLayout; context.names = nextNames;
    return { ok: true, ...selection(context) };
  });
  app.on('window-all-closed', () => app.quit());
}

function selection(context: WindowBinding) {
  return { task: context.task, paneKeys: [...context.panes.keys()], layout: context.layout, names: context.names };
}

async function changeTask(context: WindowBinding, task: string | null) {
  const options = { ...context.options, task: task ?? undefined, launch: undefined };
  // Validate before detaching. Original admission rules still apply to saved
  // panes; transient sidebar inspection is separately read-only.
  const prepared = await prepareSelection(options);
  if (context.closing) throw new Error('Window is closing');
  for (const pane of context.panes.values()) pane.closing = true;
  try {
    await detachPanes(context);
    if (context.closing) throw new Error('Window is closing');
    context.options = options; context.task = prepared.task;
    context.layout = prepared.layout; context.names = prepared.names;
    context.panes = new Map(prepared.panes.map(pane => [pane.key, pane]));
    return selection(context);
  } finally { for (const pane of context.panes.values()) pane.closing = false; }
}

function restoreArrangement(panes: PaneBinding[], saved: any) {
  const names: Record<string, string> = {}, included = new Set<string>();
  let layout = mapLayout(saved?.tree ?? null, id => {
    const pane = panes.find(p => p.launch === id);
    if (!pane || included.has(pane.key)) return null;
    included.add(pane.key); return pane.key;
  });
  for (const pane of panes) {
    if (!included.has(pane.key)) layout = layout ? { direction: 'right', first: layout, second: pane.key } : pane.key;
    if (saved?.names?.[pane.launch!]) names[pane.key] = saved.names[pane.launch!];
  }
  return { layout, names };
}
async function createTerminal(context: WindowBinding, source: string, relative?: PaneBinding, direction: 'right' | 'down' = 'right') {
  if (context.closing || context.switching || context.creating || [...context.panes.values()].some(p => p.closing)) throw new Error('Task view is changing');
  const create = async () => {
    let project: string | null = context.task?.project_id ?? null;
    let cwd = source === 'home' || !context.task ? homedir() : context.task.repo;
    if (source === 'project' && !context.task) throw new Error('请先选择项目中的任务');
    if (source === 'choose') {
      const picked = await dialog.showOpenDialog(context.window, { title: '选择终端目录', defaultPath: cwd, properties: ['openDirectory'] });
      if (picked.canceled) return selection(context);
      cwd = picked.filePaths[0];
    }
    if (relative?.project !== undefined) {
      project = relative.project;
      const value = await request(context.options.state, { command: 'workbench_snapshot', project, launch: relative.launch });
      requireShellPane(project, relative.launch!, value); cwd = value.launch.worktree;
    }
    if (context.closing) throw new Error('Window is closing');
    const result = await request(context.options.state, { command: 'shell_start', project, cwd }, context.operator);
    requireShellPane(project, result.launch?.id, { ...result, task: null });
    const pane: PaneBinding = { key: randomUUID(), launch: result.launch.id, project, sequence: 0,
      inputQueue: Promise.resolve(), pendingRelease: null };
    for (const [key, existing] of context.panes) {
      if (!existing.launch && !existing.identity && !existing.opening && !relative) {
        context.panes.delete(key); context.layout = replaceLeaf(context.layout, key, null);
      }
    }
    context.panes.set(pane.key, pane);
    context.layout = relative ? replaceLeaf(context.layout, relative.key, { direction, first: relative.key, second: pane.key }) :
      context.layout ? { direction: 'right', first: context.layout, second: pane.key } : pane.key;
    await saveArrangement(context);
    return selection(context);
  };
  context.creating = create();
  try { return await context.creating; } finally { context.creating = undefined; }
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
    const saved = await request(options.state, { command: 'pane_layout', free: true });
    if (!saved.ok) throw new Error(saved.error);
    const panes: PaneBinding[] = [];
    for (const opened of saved.panes) {
      const value = await request(options.state, { command: 'workbench_snapshot', project: null, launch: opened.launch });
      requireShellPane(null, opened.launch, value);
      panes.push({ key: randomUUID(), launch: opened.launch, project: null, sequence: 0, inputQueue: Promise.resolve(), pendingRelease: null });
    }
    return { task: null, saved: true, panes, ...restoreArrangement(panes, saved.arrangement) };
  }
  const snapshot = await request(options.state, { command: 'workbench_snapshot', task: options.task });
  if (!snapshot.ok) throw new Error(snapshot.error);
  let saved = false;
  let arrangement: any = null;
  let launches: (string | undefined)[];
  if (options.launch === undefined) {
    const layout = await request(options.state, { command: 'pane_layout', task: options.task });
    if (!layout.ok) throw new Error(layout.error);
    launches = layout.panes.map((pane: { launch: string }) => pane.launch);
    saved = layout.saved; arrangement = layout.arrangement;
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
      ranks.set(launch!, ['worker', 'reviewer'].includes(value.launch.role) ? 2 : value.launch.preset === 'ideation' ? 0 : 1);
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
  return { task: snapshot.task, saved, panes, ...restoreArrangement(panes, arrangement) };
}

export async function run(options: Options) {
  if (!isAbsolute(options.state) || !isAbsolute(options.userData)) throw new Error('Absolute data paths are required');
  const { task, saved, panes, layout, names } = await prepareSelection(options);
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
  if (windows.size === 0) {
    const updateDockIcon = () => app.dock.setIcon(join(directory, 'brand',
      nativeTheme.shouldUseDarkColors ? 'logo-on-dark.png' : 'logo-on-light.png'));
    updateDockIcon();
    nativeTheme.on('updated', updateDockIcon);
  }
  const window = new BrowserWindow({ width: 1440, height: 900, minWidth: 900, minHeight: 650,
    title: 'Enchanted', backgroundColor: '#111111',
    webPreferences: { preload: join(directory, 'preload.cjs'), nodeIntegration: false,
      contextIsolation: true, sandbox: true, backgroundThrottling: false,
      additionalArguments: ['--a2a-pane-keys=' + JSON.stringify(panes.map(pane => pane.key))] } });
  const context: WindowBinding = { window, options, operator, task, layout, names, panes: new Map(panes.map(pane => [pane.key, pane])), closing: false, closed: false };
  const senderId = window.webContents.id;
  windows.set(senderId, context);
  registerHandlers();
  // Persist creation before exposing the window. A crash must not depend on a
  // shutdown hook. Reopening an existing failed pane preserves its diagnosis.
  if (!saved) for (const [position, pane] of panes.entries()) {
    if (!pane.launch) continue;
    const opened = await request(options.state, { command: 'pane_layout_open',
      ...(pane.project !== undefined ? { project: pane.project } : { task: options.task }), launch: pane.launch, position }, operator);
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
  window.on('closed', () => { windows.delete(senderId); updateDockBadge(); });
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
