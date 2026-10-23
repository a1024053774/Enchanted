import { app, BrowserWindow, ipcMain, dialog, nativeTheme } from 'electron';
import { mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { request } from '../src/transport.ts';
import { readOperatorCredential } from '../src/credentials.ts';
import { randomUUID } from 'node:crypto';
import { NotificationCenter, type NotificationPreference } from './notificationCenter.ts';
import type { EmptyInputDeclaration } from '../src/panes.ts';

type Options = { state: string; task?: string; project?: string; launch?: string | string[]; userData: string; inspect?: boolean };
type PaneBinding = {
  key: string; launch?: string; task?: string; project?: string | null; identity?: Record<string, unknown>; opening?: Promise<void>;
  sequence: number; inputQueue: Promise<unknown>; pendingRelease: Promise<any> | null;
  closing?: boolean;
  viewOnly?: boolean;
};
type WindowBinding = {
  window: BrowserWindow; options: Options; operator: NonNullable<ReturnType<typeof readOperatorCredential>>;
  panes: Map<string, PaneBinding>; parked: Map<string, PaneBinding>; closing: boolean; closed: boolean;
  layout: Layout | null; names: Record<string, string>;
  task: any; project: { project_id: string; repo: string | null } | null;
  switching?: Promise<unknown>; creating?: Promise<unknown>;
};
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
async function serializedArrangement(context: WindowBinding, tree = context.layout, names = context.names) {
  const selected = { tree: mapLayout(tree, key => context.panes.get(key)?.viewOnly ? null : context.panes.get(key)?.launch ?? null),
    names: Object.fromEntries(Object.entries(names).flatMap(([key, name]) => {
      const pane = context.panes.get(key), id = pane?.launch; return id && !pane.viewOnly ? [[id, name]] : [];
    })) };
  if (!context.options.inspect) return selected;
  // A single-agent view edits only its leaf, not the hidden siblings in the
  // task/project arrangement. Reconstruct the saved open set before changing it.
  const saved = await request(context.options.state, { command: 'pane_layout',
    ...(context.options.task ? { task: context.options.task } : { project: context.options.project }) });
  if (!saved.ok) throw new Error(saved.error);
  const opened = saved.panes.filter((pane: { task: string | null }) => context.options.task !== undefined || pane.task === null);
  const full = restoreArrangement(opened.map((pane: { launch: string }) => ({ key: pane.launch, launch: pane.launch })), saved.arrangement);
  const kept = new Set<string>();
  mapLayout(selected.tree, id => { kept.add(id); return id; });
  for (const pane of context.panes.values()) if (pane.launch && !pane.viewOnly && !kept.has(pane.launch)) {
    full.layout = replaceLeaf(full.layout, pane.launch, null); delete full.names[pane.launch];
  }
  return { tree: full.layout, names: { ...full.names, ...selected.names } };
}
async function saveArrangement(context: WindowBinding) {
  const result = await request(context.options.state, { command: 'pane_layout_save', task: context.options.task,
    project: context.options.task ? undefined : context.options.project, arrangement: await serializedArrangement(context) }, context.operator);
  if (!result.ok) throw new Error(result.error);
}

function requireCurrentPane(task: string, launch: string, result: any) {
  if (!result.ok) throw new Error(result.error);
  const record = result.launch;
  if (result.task?.task_id !== task || record?.task !== task || record?.id !== launch) throw new Error('Pane task or launch mismatch');
  if (result.pane?.lifecycle !== 'running' || result.pane.failed || result.pane.historical ||
      !(record.role === 'controller' && record.attempt === null && ['ideation', 'executor'].includes(record.preset) ||
        record.role === 'worker' && record.attempt !== null && result.task.current_attempt?.attempt_id === record.attempt ||
        ['reviewer', 'monitor'].includes(record.role) && record.attempt !== null)) {
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
function target(event: Electron.IpcMainInvokeEvent, key: string, readOnly = false) {
  const context = windowTarget(event);
  if (context.switching && !readOnly || context.closing) throw new Error('Task view is changing');
  const pane = typeof key === 'string' ? context.panes.get(key) ?? (readOnly ? context.parked.get(key) : undefined) : undefined;
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
  ipcMain.handle('a2a:theme', (event, theme: unknown) => {
    windowTarget(event);
    if (!['system', 'light', 'dark'].includes(theme as string)) throw new Error('Invalid theme');
    nativeTheme.themeSource = theme as 'system' | 'light' | 'dark';
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
    const notices = notificationCenter(context).observe(result.agents, result.controller_quota);
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
      const agent = [...catalog.agents, ...catalog.terminals].find((row: any) => row.id === launch);
      if (agent?.terminal) {
        await changeView(context, { project: agent.project, launch });
        const pane = [...context.panes.values()].find(p => p.launch === launch);
        if (!pane) throw new Error('This terminal is not open in this window');
        return { ...selection(context), focusKey: pane.key };
      }
      if (!agent?.task || !catalog.projects.some((p: any) => p.project_id === agent.project && p.tasks.some((t: any) => t.task_id === agent.task))) throw new Error('Unknown agent launch');
      const snapshot = await request(context.options.state, { command: 'workbench_snapshot', task: agent.task, launch });
      requireAgentView(agent.task, launch, snapshot);
      await changeView(context, { task: agent.task, launch });
      const pane = [...context.panes.values()].find(p => p.launch === launch)!;
      return { ...selection(context), focusKey: pane.key };
    };
    context.switching = select();
    try { return await context.switching; } finally { context.switching = undefined; }
  });
  ipcMain.handle('a2a:decide-role-request', async (event, roleRequest: unknown, approved: unknown, parentLaunch: unknown) => {
    const context = windowTarget(event);
    if (typeof roleRequest !== 'string' || !roleRequest || typeof approved !== 'boolean' ||
        !(parentLaunch === null || typeof parentLaunch === 'string' && parentLaunch)) throw new Error('Invalid role request decision');
    const result = await request(context.options.state, { command: 'role_request_decide', role_request: roleRequest, approved, parent_launch: parentLaunch }, context.operator);
    if (!result.ok) throw new Error(result.error);
    return result.role_request;
  });
  // Issue reports of every task in a project (T-132). A failed read fails the whole list, never an empty one.
  ipcMain.handle('a2a:issues', async (event, project: unknown) => {
    const context = windowTarget(event);
    if (typeof project !== 'string' || !project) throw new Error('Invalid project');
    const listed = await request(context.options.state, { command: 'tasks_list', project });
    if (!listed.ok) throw new Error(listed.error);
    return await Promise.all(listed.tasks.map(async (task: any) => {
      const result = await request(context.options.state, { command: 'issues', task: task.task_id }, context.operator);
      if (!result.ok) throw new Error(result.error);
      return { task: task.task_id, name: String(task.task_id).slice(String(task.task_id).indexOf('+') + 1), title: task.title, issues: result.issues };
    }));
  });
  ipcMain.handle('a2a:issue-answer', async (event, task: unknown, issue: unknown, answer: unknown) => {
    const context = windowTarget(event);
    if (![task, issue, answer].every(value => typeof value === 'string' && value.trim())) throw new Error('Invalid answer');
    const result = await request(context.options.state, { command: 'answer_issue', task, issue, answer }, context.operator);
    if (!result.ok) throw new Error(result.error);
  });
  ipcMain.handle('a2a:issue-dispose', async (event, task: unknown, issue: unknown, action: unknown, reason?: unknown, basis?: unknown) => {
    const context = windowTarget(event);
    if (![task, issue].every(value => typeof value === 'string' && value) || !['close', 'snooze'].includes(action as string) ||
      [reason, basis].some(value => value !== undefined && typeof value !== 'string') ||
      (action === 'close' && ![reason, basis].every(value => typeof value === 'string' && value.trim()))) throw new Error('Invalid disposition');
    const result = await request(context.options.state, { command: 'disposition', task, issue, action,
      ...(reason !== undefined ? { reason } : {}), ...(basis !== undefined ? { basis } : {}) }, context.operator);
    if (!result.ok) throw new Error(result.error);
  });
  ipcMain.handle('a2a:records', async (event, project: unknown) => {
    const context = windowTarget(event);
    if (typeof project !== 'string' || !project) throw new Error('Invalid project');
    const result = await request(context.options.state, { command: 'user_input_records', project }, context.operator);
    if (!result.ok) throw new Error(result.error);
    return result.records;
  });
  ipcMain.handle('a2a:metrics', async (event, project: unknown, since: unknown, until: unknown) => {
    const context = windowTarget(event);
    if (typeof project !== 'string' || !project || [since, until].some(value => value !== null && typeof value !== 'string')) throw new Error('Invalid metrics range');
    const result = await request(context.options.state, { command: 'metrics', project, since, until }, context.operator);
    if (!result.ok) throw new Error(result.error);
    return result;
  });
  // The Reflect page's session tree (T-137).
  ipcMain.handle('a2a:reflect', async (event, project: unknown) => {
    const context = windowTarget(event);
    if (typeof project !== 'string' || !project) throw new Error('Invalid project');
    const result = await request(context.options.state, { command: 'reflect_tree', project }, context.operator);
    if (!result.ok) throw new Error(result.error);
    return result.nodes;
  });
  ipcMain.handle('a2a:retrospectives', async (event, project: unknown) => {
    const context = windowTarget(event);
    if (typeof project !== 'string' || !project) throw new Error('Invalid project');
    const result = await request(context.options.state, { command: 'retrospective_list', project }, context.operator);
    if (!result.ok) throw new Error(result.error);
    return { schedule: result.schedule, runs: result.runs, suggestions: result.suggestions };
  });
  ipcMain.handle('a2a:retrospective-start', async (event, project: unknown, selection: any) => {
    const context = windowTarget(event);
    if (typeof project !== 'string' || !project || !selection || typeof selection !== 'object') throw new Error('Invalid retrospective');
    const result = await request(context.options.state, { command: 'retrospective_start', project,
      cli: selection.cli, model: selection.model, effort: selection.effort }, context.operator);
    if (!result.ok) throw new Error(result.error);
    return result.run;
  });
  ipcMain.handle('a2a:retrospective-schedule', async (event, change: any) => {
    const context = windowTarget(event);
    if (!change || typeof change !== 'object') throw new Error('Invalid schedule');
    const result = await request(context.options.state, { ...change, command: 'retrospective_schedule_save' }, context.operator);
    if (!result.ok) throw new Error(result.error);
    return result.schedule;
  });
  ipcMain.handle('a2a:retrospective-decide', async (event, suggestion: unknown, approved: unknown) => {
    const context = windowTarget(event);
    if (typeof suggestion !== 'string' || typeof approved !== 'boolean') throw new Error('Invalid decision');
    const result = await request(context.options.state, { command: 'retrospective_decide', suggestion, approved }, context.operator);
    if (!result.ok) throw new Error(result.error);
  });
  ipcMain.handle('a2a:archive-usage', async event => {
    const context = windowTarget(event);
    const result = await request(context.options.state, { command: 'trajectory_archive' }, context.operator);
    if (!result.ok) throw new Error(result.error);
    return { sessions: result.sessions, bytes: result.bytes };
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
  ipcMain.handle('a2a:open-project', async (event, ...args: unknown[]) => {
    const context = windowTarget(event);
    if (args.length) throw new Error('Project directory must be chosen by the native dialog');
    if (context.closing || context.switching || context.creating || [...context.panes.values()].some(p => p.closing)) throw new Error('Task view is changing');
    const picked = await dialog.showOpenDialog(context.window, { title: '打开项目目录', buttonLabel: '打开',
      defaultPath: context.project?.repo ?? context.task?.repo ?? homedir(), properties: ['openDirectory', 'createDirectory'] });
    if (picked.canceled) return null;
    const opened = await request(context.options.state, { command: 'project_open', repo: picked.filePaths[0] }, context.operator);
    if (!opened.ok) throw new Error(opened.error);
    context.switching = changeView(context, { project: opened.project });
    try { return await context.switching; } finally { context.switching = undefined; }
  });
  ipcMain.handle('a2a:remove-project', async (event, project: string) => {
    const context = windowTarget(event);
    if (typeof project !== 'string' || !project) throw new Error('Invalid project');
    if (context.closing || context.switching || context.creating) throw new Error('Task view is changing');
    const removed = await request(context.options.state, { command: 'project_remove', project }, context.operator);
    if (!removed.ok) throw new Error(removed.error);
    if (context.options.project === project && !context.options.task) {
      context.switching = changeView(context, {});
      try { await context.switching; } finally { context.switching = undefined; }
    }
    return selection(context);
  });
  ipcMain.handle('a2a:select-project', async (event, project: string | null) => {
    const context = windowTarget(event);
    if (project !== null && (typeof project !== 'string' || !project)) throw new Error('Invalid project');
    if (context.closing || context.switching || context.creating || [...context.panes.values()].some(pane => pane.closing)) throw new Error('Task view is changing');
    if (!context.options.task && context.options.launch === undefined && (context.options.project ?? null) === project &&
        (project === null || !context.panes.size)) return selection(context);
    context.switching = changeView(context, project === null ? {} : { project });
    try { return await context.switching; }
    finally { context.switching = undefined; }
  });
  ipcMain.handle('a2a:new-terminal', async (event, ...args: unknown[]) => {
    const context = windowTarget(event);
    if (args.length) throw new Error('Invalid terminal arguments');
    return createTerminal(context);
  });
  ipcMain.handle('a2a:pane-action', async (event, key: string, action: { type: string; direction?: string; name?: string }) => {
    const { context, pane } = target(event, key);
    if (context.creating || [...context.panes.values()].some(p => p.closing)) throw new Error('Task view is changing');
    if (!action || typeof action !== 'object') throw new Error('Invalid pane action');
    if (action.type === 'split') {
      if (!['right', 'down'].includes(action.direction!)) throw new Error('Invalid split direction');
      return createTerminal(context, pane, action.direction as 'right' | 'down');
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
    if (task === (context.options.task ?? null) && context.options.launch === undefined) return selection(context);
    context.switching = changeView(context, task === null ? {} : { task });
    try { return await context.switching; }
    finally { context.switching = undefined; }
  });
  ipcMain.handle('a2a:snapshot', async (event, key: string) => {
    const { context, pane } = target(event, key, true);
    const task = pane.task!;
    const scope = pane.project !== undefined ? { project: pane.project } : { task };
    const result = await request(context.options.state, { command: 'workbench_snapshot', ...scope,
      ...(pane.launch ? { launch: pane.launch } : {}) });
    if (pane.closing || context.panes.get(key) !== pane && context.parked.get(key) !== pane) throw new Error('Task view changed');
    if (!result.ok) throw new Error(result.error);
    if (pane.project !== undefined) requireShellPane(pane.project, pane.launch!, result);
    else if (pane.viewOnly) requireAgentView(task, pane.launch!, result);
    else if ([...context.panes.values()].filter(value => value.task === task && !value.viewOnly).length > 1) requireSavedPane(task, pane.launch!, result);
    if (pane.launch && result.launch?.id !== pane.launch) throw new Error('Pane launch changed');
    if (result.launch && !pane.launch) {
      const opened = await request(context.options.state, { command: 'pane_layout_open', task,
        launch: result.launch.id, position: [...context.panes.keys()].indexOf(pane.key) }, context.operator);
      if (!opened.ok) throw new Error(opened.error);
      pane.launch = result.launch.id;
    }
    if (pane.closing || context.panes.get(key) !== pane && context.parked.get(key) !== pane) throw new Error('Task view changed');
    const writable = context.panes.get(key) === pane && !context.switching && !pane.viewOnly && !result.recovering && !pane.closing && result.pane?.lifecycle === 'running' && !result.pane.failed &&
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
    const selected = context.panes.get(key) === pane && !context.switching;
    return { ...result, pane_key: pane.key, window_id: selected ? pane.identity?.window : undefined,
      input_enabled: Boolean(selected && writable && pane.identity && !context.closing) };
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
    const { context, pane } = target(event, key, true);
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
        launch: pane.launch, layout_task: context.options.task, arrangement: await serializedArrangement(context, nextLayout, nextNames) }, context.operator);
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
  return { task: context.task, project: context.task ? { project_id: context.task.project_id, repo: context.task.repo } : context.project, paneKeys: [...context.panes.keys()], connectedPaneKeys: [...context.panes.keys(), ...context.parked.keys()], layout: context.layout, names: context.names,
    launches: Object.fromEntries([...context.panes.values()].filter(pane => pane.launch).map(pane => [pane.key, pane.launch!])) };
}

async function changeView(context: WindowBinding, view: { task?: string; project?: string; launch?: string }) {
  const options = { ...context.options, task: view.task, project: view.project, launch: view.launch, inspect: view.launch !== undefined };
  // Validate before detaching. Original admission rules still apply to saved
  // panes; transient sidebar inspection is separately read-only.
  const prepared = await prepareSelection(options);
  if (context.closing) throw new Error('Window is closing');
  // Four inactive terminals bound scrollback memory. Eviction releases the
  // credential and renderer; the daemon retains full output for later replay.
  const retainedPaneLimit = 4;
  const connected = [...context.panes.values(), ...context.parked.values()];
  const retained = new Map<string, PaneBinding>();
  for (const pane of prepared.panes) {
    const existing = connected.find(old => old.launch === pane.launch && old.task === pane.task && old.project === pane.project && old.viewOnly === pane.viewOnly);
    if (existing) retained.set(pane.key, existing);
  }
  const parked = new Map(context.parked), retiring: PaneBinding[] = [];
  for (const pane of retained.values()) parked.delete(pane.key);
  for (const pane of context.panes.values()) if (![...retained.values()].includes(pane)) {
    if (pane.launch) parked.set(pane.key, pane); else retiring.push(pane);
  }
  // A launch becoming historical/read-only must not retain its writable binding.
  for (const [key, pane] of parked) if (prepared.panes.some(next => next.launch === pane.launch)) {
    parked.delete(key); retiring.push(pane);
  }
  while (parked.size > retainedPaneLimit) {
    const pane = parked.values().next().value!;
    parked.delete(pane.key); retiring.push(pane);
  }
  for (const pane of retiring) pane.closing = true;
  try {
    await detachPanes(context, retiring);
    if (context.closing) throw new Error('Window is closing');
    context.options = options; context.task = prepared.task; context.project = prepared.project;
    context.layout = mapLayout(prepared.layout, key => retained.get(key)?.key ?? key);
    context.names = Object.fromEntries(Object.entries(prepared.names).map(([key, name]) => [retained.get(key)?.key ?? key, name]));
    context.panes = new Map(prepared.panes.map(pane => { const binding = retained.get(pane.key) ?? pane; return [binding.key, binding]; }));
    context.parked = parked;
    return selection(context);
  } finally { for (const pane of context.panes.values()) pane.closing = false; }
}

function restoreArrangement(panes: Pick<PaneBinding, 'key' | 'launch'>[], saved: any) {
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
// New terminals start in the selected project's directory, or home when no
// project is selected. A split keeps the directory of the pane it splits.
async function createTerminal(context: WindowBinding, relative?: PaneBinding, direction: 'right' | 'down' = 'right') {
  if (context.closing || context.switching || context.creating || [...context.panes.values()].some(p => p.closing)) throw new Error('Task view is changing');
  const create = async () => {
    let project: string | null = context.task?.project_id ?? context.project?.project_id ?? null;
    let cwd = context.task?.repo ?? context.project?.repo ?? homedir();
    if (relative?.project !== undefined) {
      project = relative.project;
      const value = await request(context.options.state, { command: 'workbench_snapshot', project, launch: relative.launch });
      requireShellPane(project, relative.launch!, value); cwd = value.launch.worktree;
    }
    if (context.closing) throw new Error('Window is closing');
    const result = await request(context.options.state, { command: 'shell_start', project, cwd }, context.operator);
    requireShellPane(project, result.launch?.id, { ...result, task: null });
    // A project terminal never becomes a task agent. Starting one from a task
    // opens its project-level terminal view before adding the new pane.
    if (context.task) { await changeView(context, project === null ? {} : { project }); relative = undefined; }
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

async function detachPanes(context: WindowBinding, panes = [...context.panes.values(), ...context.parked.values()]) {
  const outcomes = await Promise.allSettled(panes.flatMap(pane =>
    [pane.inputQueue, pane.pendingRelease, pane.opening]));
  for (const outcome of outcomes) if (outcome.status === 'rejected') console.error('Window input outcome remains unconfirmed:', String(outcome.reason));
  const revocations = await Promise.allSettled(panes.filter(pane => pane.identity).map(async pane => {
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
    if (Array.isArray(options.launch)) throw new Error('A project agent view requires one launch');
    const project = options.project ?? null;
    let catalogEntry: { project_id: string; repo: string | null } | null = null;
    if (project !== null) {
      const catalog = await request(options.state, { command: 'sidebar_snapshot' });
      if (!catalog.ok) throw new Error(catalog.error);
      const row = catalog.projects.find((p: any) => p.project_id === project);
      if (!row) throw new Error('unknown_project');
      catalogEntry = { project_id: row.project_id, repo: row.repo };
    }
    const saved = await request(options.state, { command: 'pane_layout', ...(project === null ? { free: true } : { project }) });
    if (!saved.ok) throw new Error(saved.error);
    const panes: PaneBinding[] = [];
    // A project is a task overview. Unassigned terminals keep their dedicated area.
    const selected = options.launch ? [{ launch: options.launch, task: null }] : project === null ? saved.panes : [];
    for (const opened of selected.filter((pane: { task: string | null }) => pane.task === null)) {
      const value = await request(options.state, { command: 'workbench_snapshot', project, launch: opened.launch });
      requireShellPane(project, opened.launch, value);
      panes.push({ key: randomUUID(), launch: opened.launch, project, sequence: 0, inputQueue: Promise.resolve(), pendingRelease: null });
    }
    return { task: null, project: catalogEntry, saved: true, panes, ...restoreArrangement(panes, saved.arrangement) };
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
  const panes: PaneBinding[] = launches.map(launch => ({ key: randomUUID(), launch, task: options.task, sequence: 0,
    inputQueue: Promise.resolve(), pendingRelease: null }));
  if (options.inspect && typeof options.launch === 'string') {
    const value = await request(options.state, { command: 'workbench_snapshot', task: options.task, launch: options.launch });
    requireAgentView(options.task, options.launch, value);
    if (value.pane?.lifecycle !== 'running' || value.pane.failed || value.pane.historical ||
        value.launch.attempt && value.task.current_attempt?.attempt_id !== value.launch.attempt ||
        !['worker', 'controller'].includes(value.launch.role)) panes[0]!.viewOnly = true;
    // Agent inspection does not replace the task's saved arrangement.
    const layout = await request(options.state, { command: 'pane_layout', task: options.task });
    if (!layout.ok) throw new Error(layout.error);
    if (!panes[0]!.viewOnly && !layout.panes.some((pane: { launch: string }) => pane.launch === options.launch)) {
      const opened = await request(options.state, { command: 'pane_layout_open', task: options.task,
        launch: options.launch, position: layout.panes.length }, readOperatorCredential(options.state)!);
      if (!opened.ok) throw new Error(opened.error);
    }
    arrangement = layout.arrangement; saved = true;
  }
  return { task: snapshot.task, project: null, saved, panes, ...restoreArrangement(panes, arrangement) };
}

export async function run(options: Options) {
  if (!isAbsolute(options.state) || !isAbsolute(options.userData)) throw new Error('Absolute data paths are required');
  const { task, project, saved, panes, layout, names } = await prepareSelection(options);
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
    title: 'Enchanted', backgroundColor: '#00000000', titleBarStyle: 'hiddenInset', trafficLightPosition: { x: 18, y: 20 },
    vibrancy: 'sidebar', visualEffectState: 'active',
    webPreferences: { preload: join(directory, 'preload.cjs'), nodeIntegration: false,
      contextIsolation: true, sandbox: true, backgroundThrottling: false,
      additionalArguments: ['--a2a-pane-keys=' + JSON.stringify(panes.map(pane => pane.key)), '--a2a-home=' + homedir()] } });
  const context: WindowBinding = { window, options, operator, task, project, layout, names, panes: new Map(panes.map(pane => [pane.key, pane])), parked: new Map(), closing: false, closed: false };
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
  // A renderer killed from outside (e.g. SIGTERM to its process group) leaves an
  // empty window; the panes live in the daemon, so a reload reattaches them.
  // One reload per crash; a renderer that dies again within 10s of a reload is left
  // as is (logged) rather than reloaded in a loop.
  let reloadedAt = 0;
  window.webContents.on('render-process-gone', (_event, details) => {
    console.error('Renderer gone:', details.reason, details.exitCode);
    if (Date.now() - reloadedAt < 10000) { console.error('Renderer gone again right after a reload; not reloading'); return; }
    void (async () => {
      // Let a pending project switch, terminal creation or pane close settle so the new renderer reads the final pane set.
      await Promise.allSettled([context.switching, context.creating]);
      // A failed close can leave its flag set; reload after 10s rather than stay blank.
      for (const deadline = Date.now() + 10000; Date.now() < deadline && [...context.panes.values()].some(pane => pane.closing);)
        await new Promise(resolve => setTimeout(resolve, 100));
      if (context.closing || context.closed || window.isDestroyed()) return;
      reloadedAt = Date.now();
      window.webContents.reload();
    })();
  });
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
