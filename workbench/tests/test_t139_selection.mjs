// Failure modes: task includes a project shell; agent selection includes its siblings;
// selecting the same launch again issues a second input credential; ended agent gets stdin.
// A single-agent rename/close must preserve the saved sibling layout and names.
// Runs the actual main.ts with supplied Electron/transport boundaries. This is not GUI evidence.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { EventEmitter } from 'node:events';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';

const [out, revision] = process.argv.slice(2);
assert(out && !existsSync(out), 'New summary path required');
const report = { status: 'INCOMPLETE', argv: process.argv, checks: [], scope: 'Actual main.ts; supplied Electron and daemon boundaries; no performance or GUI claim' };
try {
  const handlers = new Map(), opened = [], closed = [];
  const taskPanes = new Set(['worker-A', 'reviewer-A']);
  let arrangement = { tree: { direction: 'down', first: 'worker-A', second: 'reviewer-A' },
    names: { 'worker-A': 'A worker', 'reviewer-A': 'A review' } };
  const agents = [
    { id: 'worker-A', project: 'demo', task: 'demo+T-A', role: 'worker', attempt: 'a1' },
    { id: 'reviewer-A', project: 'demo', task: 'demo+T-A', role: 'reviewer', attempt: 'a1' },
    { id: 'ended-A', project: 'demo', task: 'demo+T-A', role: 'worker', attempt: 'old' },
    { id: 'worker-B', project: 'demo', task: 'demo+T-B', role: 'worker', attempt: 'b1' },
    { id: 'project-shell', project: 'demo', task: null, role: 'shell', terminal: true, attempt: null, session: null, fence: null },
  ];
  const tasks = ['A', 'B'].map(x => ({ task_id: 'demo+T-' + x, project_id: 'demo', repo: '/fixture/demo', current_attempt: { attempt_id: x === 'A' ? 'a1' : 'b1' } }));
  const request = async (_state, input, identity) => {
    if (input.command === 'sidebar_snapshot') return { ok: true, projects: [{ project_id: 'demo', repo: '/fixture/demo', tasks }], agents };
    if (input.command === 'pane_layout') return { ok: true, saved: true, panes: input.project
      ? [{ launch: 'project-shell', task: null }] : input.free ? [] : [...taskPanes].map(launch => ({ launch })), arrangement };
    if (input.command === 'workbench_snapshot') {
      const launch = agents.find(a => a.id === (input.launch ?? 'worker-A'));
      return { ok: true, task: input.project ? null : tasks.find(t => t.task_id === input.task), launch,
        pane: { lifecycle: launch.id === 'ended-A' ? 'ended' : 'running', failed: null } };
    }
    if (input.command === 'window_open') { opened.push(input.launch); return { ok: true, identity: { kind: 'window', window: 'window-' + opened.length } }; }
    if (input.command === 'window_close') { closed.push(identity.window); return { ok: true }; }
    if (input.command === 'pane_layout_open') { assert.equal(identity.kind, 'operator'); taskPanes.add(input.launch); return { ok: true }; }
    if (input.command === 'pane_layout_save') { arrangement = input.arrangement; return { ok: true }; }
    if (input.command === 'pane_layout_close') { taskPanes.delete(input.launch); if (input.arrangement) arrangement = input.arrangement; return { ok: true }; }
    throw new Error('Unexpected boundary ' + input.command);
  };
  const app = Object.assign(new EventEmitter(), { whenReady: async () => {}, setPath() {}, quit() {}, dock: { setIcon() {}, setBadge() {} } });
  class Window extends EventEmitter {
    static getFocusedWindow() { return null; }
    constructor(options) { super(); this.options = options; this.webContents = Object.assign(new EventEmitter(), { id: 1, mainFrame: {}, setWindowOpenHandler() {} }); }
    async loadFile() {}
  }
  const electron = { app, BrowserWindow: Window, ipcMain: { handle: (name, value) => handlers.set(name, value) }, dialog: {}, nativeTheme: new EventEmitter() };
  const context = vm.createContext({ console, process: { argv: [] }, setTimeout, clearTimeout, AggregateError });
  const url = pathToFileURL(resolve('workbench/app/main.ts'));
  const source = revision ? execFileSync('git', ['show', revision + ':workbench/app/main.ts'], { encoding: 'utf8' }) : readFileSync(url, 'utf8');
  const module = new vm.SourceTextModule(stripTypeScriptTypes(source), { context, initializeImportMeta(meta) { meta.url = url.href; } });
  await module.link(async name => {
    let values;
    if (name === 'electron') values = electron;
    else if (name === '../src/transport.ts') values = { request };
    else if (name === '../src/credentials.ts') values = { readOperatorCredential: () => ({ kind: 'operator' }) };
    else if (name === './notificationCenter.ts') values = { NotificationCenter: class {} };
    else if (name === 'node:fs') values = { mkdirSync() {} };
    else values = await import(name);
    return new vm.SyntheticModule(Object.keys(values), function () { for (const [key, value] of Object.entries(values)) this.setExport(key, value); }, { context });
  });
  await module.evaluate();
  const window = await module.namespace.run({ state: '/fixture/state', task: 'demo+T-A', userData: '/fixture/ui' });
  const event = { sender: window.webContents, senderFrame: window.webContents.mainFrame };
  const invoke = (name, ...args) => handlers.get('a2a:' + name)(event, ...args);
  const check = (name, condition, detail) => { assert(condition, name + ': ' + JSON.stringify(detail)); report.checks.push(name); };
  let selection = await invoke('selection');
  check('task_only_its_agents', JSON.stringify(Object.values(selection.launches).sort()) === JSON.stringify(['reviewer-A', 'worker-A']), selection.launches);
  selection = await invoke('select-agent', 'worker-A');
  check('agent_only_itself', Object.values(selection.launches).join() === 'worker-A', selection.launches);
  const snapshot = await invoke('snapshot', selection.focusKey);
  check('current_worker_writable', snapshot.input_enabled);
  const again = await invoke('select-agent', 'worker-A');
  await invoke('snapshot', again.focusKey);
  check('same_credential_on_reselection', selection.focusKey === again.focusKey && opened.length === 1, opened);
  selection = await invoke('select-agent', 'project-shell');
  check('project_terminal_only_itself', Object.values(selection.launches).join() === 'project-shell', selection.launches);
  selection = await invoke('select-agent', 'ended-A');
  const ended = await invoke('snapshot', selection.focusKey);
  check('ended_read_only_no_credential', !ended.input_enabled && !ended.window_id && !opened.includes('ended-A'), ended);
  let denied = false;
  try { await invoke('input', selection.focusKey, 'must not reach ended'); } catch { denied = true; }
  check('ended_input_rejected', denied);
  selection = await invoke('select-project', 'demo');
  check('project_overview_without_terminal', selection.paneKeys.length === 0, selection);
  selection = await invoke('select-agent', 'worker-A');
  await invoke('pane-action', selection.focusKey, { type: 'rename', name: 'renamed worker' });
  check('agent_rename_keeps_sibling_layout', JSON.stringify(arrangement.tree) === JSON.stringify({ direction: 'down', first: 'worker-A', second: 'reviewer-A' }) &&
    arrangement.names['reviewer-A'] === 'A review' && arrangement.names['worker-A'] === 'renamed worker', arrangement);
  await invoke('close-pane', selection.focusKey);
  selection = await invoke('select-task', 'demo+T-A');
  check('agent_close_keeps_sibling_layout', Object.values(selection.launches).join() === 'reviewer-A' &&
    Object.values(selection.names).join() === 'A review', selection);
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.status = 'NO_GO'; }
writeFileSync(out, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
