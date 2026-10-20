// Pure main/preload contract check. No Electron, daemon, PTY, ps, socket or model.
// The actual TS modules execute in a VM; only their external boundaries are supplied.
// Failure cases: missing/wrong key, cross-window key, iframe sender, duplicated
// global handlers or credentials, shared sequence, retargeted output, close/open race,
// lost panes in one window, foreign-task/stale selection, credentials issued on refusal.
// Layout boundaries: first use selects current worker; explicit final close stays
// empty on repeated reopen; empty preload works; explicit selection can reopen.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { EventEmitter } from 'node:events';
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { parseArgs } from 'node:util';
import assert from 'node:assert/strict';

const out = process.argv[2];
if (!out) throw new Error('New JSON report path required');
const { values } = parseArgs({ args: process.argv.slice(3), options: {
  source: { type: 'string' }, contract: { type: 'string', default: 'questions-flow' },
} });
assert.ok(['legacy', 'picker', 'shell', 'panes', 'creation', 'sidebar', 'questions', 'flow', 'questions-flow'].includes(values.contract), 'Select an explicit known IPC contract');
const sourceURL = values.source ? pathToFileURL(resolve(values.source) + '/') : new URL('../../', import.meta.url);
const mainURL = new URL('workbench/app/main.ts', sourceURL);
const preloadURL = new URL('workbench/app/preload.ts', sourceURL);
const baselineRevision = 'cc18d93dbbcf2ee641dc92befe68e5b0609b4807';
const legacyPreload = execFileSync('git', ['show', baselineRevision + ':workbench/app/preload.ts'], { encoding: 'utf8' });
const paneHandlers = ['a2a:snapshot', 'a2a:input', 'a2a:composition-start', 'a2a:release-queue', 'a2a:focus-observation', 'a2a:output'];
const recoveredPaneHandlers = [...paneHandlers, 'a2a:close-pane'];
const windowHandlers = ['a2a:projects', 'a2a:tasks', 'a2a:selection', 'a2a:select-task'];
const legacyBridge = ['paneKeys', 'snapshot', 'closePane', 'output', 'input', 'beginComposition', 'releaseQueue', 'observeFocus'];
const pickerBridge = [...legacyBridge, 'projects', 'tasks', 'selection', 'selectTask'];
const shellWindowHandlers = [...windowHandlers, 'a2a:new-terminal'];
const shellBridge = [...pickerBridge, 'newTerminal'];
const panesHandlers = ['a2a:pane-action', 'a2a:resize'];
const panesBridge = ['paneAction', 'resize'];
const creationHandlers = ['a2a:creation-repository', 'a2a:creation-submit', 'a2a:creation-cancel'];
const sidebarHandlers = ['a2a:sidebar', 'a2a:select-agent', 'a2a:notification-setting'];
const sidebarBridge = ['sidebar', 'selectAgent', 'notificationSetting'];
const creationBridge = ['creationRepository', 'creationSubmit', 'creationCancel'];
const badRevision = '6974c2aad1233133264b7448e1277cd19fa0b6ba';
const report = { status: 'INCOMPLETE', scope: 'actual main/preload modules with supplied Electron/transport/filesystem boundaries; no GUI or backend proof',
  argv: process.argv, contract: values.contract, source: fileURLToPath(sourceURL), known_bad: badRevision, checks: [], model_turns: 0 };

async function exercise(source, withRecovery = false, withCatalog = false, preloadSource = legacyPreload, withShell = false, withPanes = false, withCreation = false) {
  const withFlow = withCreation && ['flow','questions-flow'].includes(values.contract);
  const withQuestions = withCreation && ['questions', 'questions-flow'].includes(values.contract);
  const keyedHandlers = [...(withRecovery ? recoveredPaneHandlers : paneHandlers), ...(withPanes ? panesHandlers : []), ...(withQuestions ? ['a2a:answer'] : [])];
  const withSidebar = withCreation && ['sidebar','questions','flow','questions-flow'].includes(values.contract);
  const expectedHandlers = [...keyedHandlers, ...(withShell ? shellWindowHandlers : withCatalog ? windowHandlers : []), ...(withCreation ? creationHandlers : []), ...(withSidebar ? sidebarHandlers : []), ...(withFlow ? ['a2a:flow'] : [])];
  const expectedBridge = [...(withShell ? shellBridge : withCatalog ? pickerBridge : legacyBridge), ...(withPanes ? panesBridge : []), ...(withCreation ? creationBridge : []), ...(withSidebar ? sidebarBridge : []), ...(withQuestions ? ['answer'] : []), ...(withFlow ? ['flow'] : [])];
  const fixtureProject = 'catalog-project-sentinel';
  const fixtureSummary = { task_id: 'task-one', project_id: fixtureProject, title: '独立任务标题', state: 'claimed' };
  const fixtureTask = { ...fixtureSummary, repo: '/fixture/project-repo', current_attempt: { attempt_id: 'attempt-one' } };
  const notificationCalls = [], badgeCalls = [], settingsFiles = new Map(), sidebarStates = new Map();
  let questionId = 'question-one', focusedWindow = null, sidebarFailure = null;
  const disconnectedError = new Error('t110-socket-unavailable');
  const layout = new Map(), restorations = new Map();
  const shellLayout = new Map();
  let shellNumber = 0;
  let layoutSaved = false;
  const handlers = new Map(), registrations = [], requests = [], liveCredentials = new Map();
  let windowNumber = 0, credentialNumber = 0, openingResolve;
  const app = Object.assign(new EventEmitter(), { setPath() {}, whenReady: async () => {}, quit() {}, setBadgeCount(value) { badgeCalls.push(value); }, dock: { setBadge(value) { badgeCalls.push(value === '' ? 0 : Number(value)); } } });
  class Window extends EventEmitter {
    static getFocusedWindow() { return focusedWindow; }
    constructor(options) {
      super(); this.options = options; this.id = ++windowNumber; this.destroyed = false;
      this.webContents = Object.assign(new EventEmitter(), { mainFrame: {}, setWindowOpenHandler() {} });
      Object.defineProperty(this.webContents, 'id', { get: () => {
        if (this.destroyed) throw new Error('WebContents destroyed');
        return this.id + 100;
      } });
    }
    async loadFile() {}
    close() { this.emit('close', { preventDefault() {} }); }
    destroy() { this.destroyed = true; this.emit('closed'); }
  }
  const ipcMain = { handle(name, handler) {
    if (handlers.has(name)) throw new Error('Duplicate global IPC handler');
    registrations.push(name); handlers.set(name, handler);
  }, removeHandler(name) { handlers.delete(name); } };
  const records = {
    reviewer: { id: 'reviewer', thread: 'thread-reviewer', role: 'reviewer', preset: null, attempt: 'attempt-one' },
    worker: { id: 'worker', thread: 'thread-worker', role: 'worker', preset: null, attempt: 'attempt-one' },
    controller: { id: 'controller', thread: 'thread-controller', role: 'controller', preset: 'executor', attempt: null },
    ideation: { id: 'ideation', thread: 'thread-ideation', role: 'controller', preset: 'ideation', attempt: null },
    foreign: { id: 'foreign', task: 'task-other', thread: 'thread-foreign', role: 'worker', attempt: 'attempt-one' },
    historical: { id: 'historical', thread: 'thread-old', role: 'worker', preset: null, attempt: 'attempt-old' },
    opening: { id: 'opening', thread: 'thread-opening', role: 'worker', preset: null, attempt: 'attempt-one' },
  };
  async function request(state, input, identity, nextSequence) {
    if (nextSequence) input = { ...input, sequence: nextSequence() };
    const item = { command: input.command, input: structuredClone(input), window: identity?.window ?? null };
    requests.push(item);
    if (input.command === 'flow_snapshot') return { ok: true, lanes: [{task:'T-flow-sentinel', title:'随输入变化', stage:'review'}], unassigned:[{id:'orphan-sentinel'}] };
    if (input.command === 'sidebar_snapshot' && sidebarFailure === 'transport') throw disconnectedError;
    if (input.command === 'sidebar_snapshot' && sidebarFailure === 'refused') return { ok: false, error: 't110-sidebar-unavailable' };
    if (input.command === 'sidebar_snapshot') return { ok: true, projects: [{project_id: fixtureProject, tasks: [fixtureSummary]}],
      agents: Object.values(records).filter(row => row.role !== 'shell').map(row => ({ ...row, project: fixtureProject, task: 'task-one',
        parent: row.id === 'controller' ? 'ideation' : row.id === 'worker' ? 'controller' : null,
        descendants: { count: row.id === 'ideation' ? 2 : row.id === 'controller' ? 1 : 0, state: 'waiting_user_answer',
          state_label: '等待用户回答', counts: [{ state: 'waiting_user_answer', label: '等待用户回答', count: 1 }] },
        state: sidebarStates.get(row.id) ?? 'unknown', question_id: row.id === 'worker' ? questionId : null, role_label: row.role })) };
    if (input.command === 'projects_list') return { ok: true, projects: [{ project_id: fixtureProject }] };
    if (input.command === 'tasks_list') return input.project === '../invalid'
      ? { ok: false, error: 'invalid_id' }
      : { ok: true, tasks: input.project === fixtureProject ? [fixtureSummary] : [] };
    if (input.command === 'shell_start') {
      assert.equal(identity.kind, 'operator');
      assert.ok(input.project === fixtureProject || withPanes && input.project === null, 'Terminal project must come from the selected task or be unassigned');
      assert.equal(input.cwd, input.project === null ? (await import('node:os')).homedir() : '/fixture/project-repo', 'Terminal cwd must come from the selected directory source');
      const id = 'fixture-shell-' + ++shellNumber;
      records[id] = { id, thread: 'thread-' + id, role: 'shell', project: input.project, worktree: input.cwd,
        task: null, attempt: null, session: null, fence: null };
      shellLayout.set(id, { launch: id, task: null, position: shellLayout.size });
      return { ok: true, launch: records[id] };
    }
    if (input.command === 'pane_layout_save') return { ok: true };
    if (input.command === 'pane_layout' && input.free) return { ok: true, saved: true, panes: [...shellLayout.values()].filter(p => records[p.launch].project === null) };
    if (input.command === 'pane_layout') return input.project ? { ok: true, saved: true, panes: [...shellLayout.values()] }
      : { ok: true, saved: layoutSaved, panes: [...layout.values()].sort((a, b) => a.position - b.position) };
    if (['pane_layout_open', 'pane_layout_close'].includes(input.command)) {
      assert.equal(identity.kind, 'operator', 'Layout persistence requires the operator identity');
      layoutSaved = true;
      if (input.project !== undefined) {
        assert.ok(input.project === fixtureProject || withPanes && input.project === null);
        if (input.command === 'pane_layout_open') shellLayout.set(input.launch, { launch: input.launch, task: null, position: input.position });
        else shellLayout.delete(input.launch);
      } else if (input.command === 'pane_layout_open') layout.set(input.launch, { launch: input.launch, position: input.position });
      else layout.delete(input.launch);
      return { ok: true };
    }
    if (input.command === 'workbench_snapshot' && (input.project || withPanes && records[input.launch]?.role === 'shell')) return {
      ok: true, task: null, launch: records[input.launch], pane: { lifecycle: 'running', failed: null } };
    if (input.command === 'workbench_snapshot') return input.task !== fixtureTask.task_id ? { ok: false, error: 'unknown_task' }
      : { ok: true, task: fixtureTask, launch: { task: 'task-one', ...records[input.launch ?? 'worker'] },
          pane: restorations.get(input.launch) ?? { lifecycle: 'running', failed: null } };
    if (input.command === 'window_open') {
      assert.equal(identity.kind, 'operator');
      const credential = { kind: 'window', window: 'fixture-window-' + ++credentialNumber, token: 'non-secret-fixture-token' };
      liveCredentials.set(credential.window, input.launch);
      if (input.launch === 'opening') await new Promise(resolve => { openingResolve = resolve; });
      return { ok: true, identity: credential };
    }
    if (input.command === 'pane_output') return { ok: true, launch: input.launch, data_base64: Buffer.from(input.launch).toString('base64') };
    assert.ok(liveCredentials.has(identity?.window), 'Input/close must use a live pane credential');
    item.target = liveCredentials.get(identity.window);
    if (input.command === 'window_close') liveCredentials.delete(identity.window);
    return { ok: true };
  }
  let bridge, rendererEvent;
  const fakeProcess = { argv: ['node', fileURLToPath(import.meta.url)] };
  const electron = { app, BrowserWindow: Window, ipcMain, dialog: { showOpenDialog: async () => ({ canceled: true, filePaths: [] }) },
    contextBridge: { exposeInMainWorld(_name, value) { bridge = value; } },
    ipcRenderer: { invoke: (name, ...args) => Promise.resolve().then(() => handlers.get(name)(rendererEvent, ...args)) } };
  const context = vm.createContext({ process: fakeProcess, console, Buffer });
  let notificationModule;
  async function linkedNotificationModule(url) {
    if (notificationModule) return notificationModule;
    notificationModule = new vm.SourceTextModule(stripTypeScriptTypes(readFileSync(url, 'utf8'), { mode: 'strip' }), {context});
    await notificationModule.link(async spec => {
      const exports = spec === 'node:fs' ? { existsSync: path => settingsFiles.has(path),
        readFileSync: path => settingsFiles.get(path), writeFileSync: (path,value) => settingsFiles.set(path,value) } : await import(spec);
      return new vm.SyntheticModule(Object.keys(exports), function() { for (const [k,v] of Object.entries(exports)) this.setExport(k,v); }, {context});
    });
    return notificationModule;
  }
  async function load(text, url) {
    const module = new vm.SourceTextModule(stripTypeScriptTypes(text, { mode: 'strip' }), {
      context, identifier: url.href, importModuleDynamically: async spec => {
        assert.equal(spec, 'electron');
        class Notification { static isSupported() { return true; } constructor(value) { this.value = value; } show() { notificationCalls.push(this.value); } }
        const child = new vm.SyntheticModule(['Notification'], function () { this.setExport('Notification', Notification); }, { context });
        await child.link(() => {}); await child.evaluate(); return child;
      }, initializeImportMeta(meta) { meta.url = url.href; },
    });
    await module.link(async specifier => {
      let exports;
      if (specifier === 'electron') exports = electron;
      else if (specifier === 'node:fs') exports = { ...await import('node:fs'), mkdirSync() {},
        existsSync: path => settingsFiles.has(path),
        writeFileSync: (path, value) => settingsFiles.set(path, value),
        readFileSync: path => settingsFiles.get(path) };
      else if (specifier === 'node:child_process') exports = { execFile() { throw new Error('Unexpected process call in pane IPC contract'); } };
      else if (specifier === './notificationCenter.ts') return await linkedNotificationModule(new URL(specifier, mainURL));
      else if (specifier === '../src/transport.ts') exports = { request };
      else if (specifier === '../src/credentials.ts') exports = { readOperatorCredential: () => ({ kind: 'operator', token: 'fixture' }) };
      else if (['node:path', 'node:os', 'node:url', 'node:util', 'node:crypto'].includes(specifier)) exports = await import(specifier);
      else throw new Error('Unapproved unit boundary: ' + specifier);
      const names = Object.keys(exports);
      return new vm.SyntheticModule(names, function() { for (const name of names) this.setExport(name, exports[name]); }, { context });
    });
    await module.evaluate();
    return module.namespace;
  }
  const { run } = await load(source, mainURL);
  const options = { state: '/fixture/state', task: 'task-one', userData: '/fixture/ui' };
  if (withRecovery) {
    const initial = await run(options);
    const initialKeys = JSON.parse(initial.options.webPreferences.additionalArguments[0].slice('--a2a-pane-keys='.length));
    assert.equal(initialKeys.length, 1, 'Never-saved layout must still select the current worker');
    assert.equal((await handlers.get('a2a:snapshot')({ sender: initial.webContents, senderFrame: initial.webContents.mainFrame }, initialKeys[0])).launch.id, 'worker');
    assert.equal(layoutSaved, true, 'Initial default selection must be persisted');
    initial.close();
    for (let n = 0; !initial.destroyed && n < 20; n++) await Promise.resolve();
  }
  const credentialRequestsBeforeA = requests.filter(row => row.command === 'window_open').length;
  const a = await run({ ...options, launch: 'worker' });
  const event = window => ({ sender: window.webContents, senderFrame: window.webContents.mainFrame });
  const invoke = (window, channel, key, ...args) => Promise.resolve().then(() => handlers.get(channel)(event(window), key, ...args));
  // This is the independent sentinel that rejects the old no-key API.
  let rejected = false;
  try { await invoke(a, 'a2a:snapshot', 'not-registered'); } catch { rejected = true; }
  assert.ok(rejected, 'Unregistered pane key was accepted');
  const key = window => JSON.parse(window.options.webPreferences.additionalArguments.find(arg => arg.startsWith('--a2a-pane-keys=')).slice('--a2a-pane-keys='.length))[0];
  const aKey = key(a);
  const [first, simultaneous] = await Promise.all([invoke(a, 'a2a:snapshot', aKey), invoke(a, 'a2a:snapshot', aKey)]);
  assert.equal(first.pane_key, aKey); assert.equal(first.window_id, simultaneous.window_id); assert.equal(first.input_enabled, true);
  assert.equal(requests.filter(row => row.command === 'window_open').length - credentialRequestsBeforeA, 1);
  const b = await run({ ...options, launch: 'controller' });
  const bKey = key(b), second = await invoke(b, 'a2a:snapshot', bKey);
  assert.equal(second.input_enabled, true, 'Nullable controller attempt must remain writable');
  assert.notEqual(aKey, bKey); assert.notEqual(first.window_id, second.window_id);
  assert.deepEqual([...registrations].sort(), [...expectedHandlers].sort(), 'IPC handler names must match the selected contract');
  assert.equal(new Set(registrations).size, registrations.length, 'IPC handler registration must not repeat');
  const trailing = { 'a2a:snapshot': [], 'a2a:input': ['must-not-arrive'], 'a2a:composition-start': [],
    'a2a:release-queue': [{ window_id: first.window_id }], 'a2a:focus-observation': ['\x1b[?1004h'],
    'a2a:output': [0], 'a2a:close-pane': [], 'a2a:pane-action': [{ type: 'rename', name: '测试' }], 'a2a:resize': [80, 24], 'a2a:answer': ['question-sentinel', ['独立答复']] };
  const validArguments = Object.fromEntries(keyedHandlers.map(channel => [channel, [aKey, ...trailing[channel]]]));
  Object.assign(validArguments, { 'a2a:projects': [], 'a2a:tasks': [fixtureProject], 'a2a:selection': [], 'a2a:select-task': ['task-one'], 'a2a:new-terminal': [] });
  Object.assign(validArguments, { 'a2a:creation-repository': [], 'a2a:creation-submit': [{}], 'a2a:creation-cancel': [], 'a2a:flow': [], 'a2a:sidebar': [], 'a2a:select-agent': ['worker'], 'a2a:notification-setting': [false] });
  const beforeDenied = requests.length;
  for (const channel of keyedHandlers) {
    await assert.rejects(() => invoke(a, channel, bKey, ...trailing[channel]));
    assert.equal(requests.length, beforeDenied, 'Cross-window pane key must not reach the transport');
  }
  const unknownSender = { id: 999999, mainFrame: {} };
  for (const channel of expectedHandlers) {
    await assert.rejects(() => Promise.resolve().then(() => handlers.get(channel)({ ...event(a), senderFrame: {} }, ...validArguments[channel])));
    await assert.rejects(() => Promise.resolve().then(() => handlers.get(channel)({ sender: unknownSender, senderFrame: unknownSender.mainFrame }, ...validArguments[channel])));
    assert.equal(requests.length, beforeDenied, 'Denied sender must not reach the transport');
  }
  assert.equal(requests.length, beforeDenied, 'Denied sender/key must not reach the transport');
  await invoke(a, 'a2a:input', aKey, 'A'); await invoke(b, 'a2a:input', bKey, 'B');
  const inputs = requests.filter(row => row.command === 'window_input');
  assert.deepEqual(inputs.map(row => [row.target, row.input.data, row.input.sequence]), [['worker', 'A', 1], ['controller', 'B', 1]]);
  assert.equal((await invoke(a, 'a2a:output', aKey, 0)).launch, 'worker');
  assert.equal((await invoke(b, 'a2a:output', bKey, 0)).launch, 'controller');
  const h = await run({ ...options, launch: 'historical' });
  assert.equal((await invoke(h, 'a2a:snapshot', key(h))).input_enabled, false);
  rendererEvent = event(a);
  fakeProcess.argv = ['node', 'preload', ...a.options.webPreferences.additionalArguments];
  await load(preloadSource, preloadURL);
  assert.deepEqual(Object.keys(bridge).sort(), [...expectedBridge].sort(), 'Preload names must match the selected contract');
  assert.equal(bridge.paneKeys[0], aKey); assert.ok(Object.isFrozen(bridge.paneKeys));
  assert.equal((await bridge.snapshot(aKey)).window_id, first.window_id);
  await assert.rejects(() => bridge.snapshot(bKey));
  if (withQuestions) {
    const before = requests.length;
    await assert.rejects(() => bridge.answer(bKey, 'question-sentinel', ['独立答复']));
    await assert.rejects(() => bridge.answer(aKey, '', ['独立答复']));
    await assert.rejects(() => bridge.answer(aKey, 'question-sentinel', []));
    assert.equal(requests.length, before, 'Denied answers must not reach the transport');
    await bridge.answer(aKey, 'question-sentinel', ['独立答复']);
    const sent = requests.at(-1);
    assert.equal(sent.command, 'window_answer'); assert.equal(sent.target, 'worker');
    assert.deepEqual(sent.input.answers, ['独立答复']); assert.equal(sent.input.question, 'question-sentinel');
  }
  if (withSidebar) {
    if (withFlow) {
      const beforeFlow = requests.length, beforeFlowCredentials = credentialNumber;
      const flow = await bridge.flow();
      assert.deepEqual(JSON.parse(JSON.stringify(flow)), {lanes:[{task:'T-flow-sentinel',title:'随输入变化',stage:'review'}],unassigned:[{id:'orphan-sentinel'}]}, 'Flow must preserve daemon facts');
      assert.deepEqual(requests.slice(beforeFlow).map(row=>row.input), [{command:'flow_snapshot'}], 'Flow must use only the read command');
      assert.equal(credentialNumber, beforeFlowCredentials, 'Flow must not issue pane credentials');
    }
    const hierarchy = (await bridge.sidebar()).agents;
    assert.equal(hierarchy.find(row => row.id === 'worker').parent, 'controller');
    assert.equal(hierarchy.find(row => row.id === 'controller').parent, 'ideation');
    assert.equal(hierarchy.find(row => row.id === 'ideation').descendants.count, 2);
    assert.equal(hierarchy.find(row => row.id === 'controller').descendants.state, 'waiting_user_answer');
    assert.equal(hierarchy.find(row => row.id === 'controller').descendants.counts[0].label, '等待用户回答');
    await assert.rejects(() => bridge.selectAgent('absent'));
    await assert.rejects(() => bridge.selectAgent('../invalid'));
    await assert.rejects(() => bridge.notificationSetting('yes'));
    const before = credentialNumber;
    const originalSelection = await bridge.selection();
    const focused = await bridge.selectAgent('worker');
    assert.equal(focused.focusKey, aKey);
    const readonly = await bridge.selectAgent('reviewer');
    assert.notEqual(readonly.focusKey, aKey);
    assert.equal((await bridge.snapshot(readonly.focusKey)).input_enabled, false);
    await assert.rejects(() => bridge.input(readonly.focusKey, 'no credential'));
    assert.equal(credentialNumber, before, 'Sidebar inspection must not grant input');
    await assert.rejects(() => bridge.selectAgent('foreign'), /mismatch/);
    assert.equal((await bridge.selection()).task.task_id, originalSelection.task.task_id);
    const controllerView = await bridge.selectAgent('ideation');
    assert.equal((await bridge.snapshot(controllerView.focusKey)).input_enabled, false, 'Transient controller view must not issue an input credential');
    assert.equal(credentialNumber, before, 'Transient view cannot acquire credentials');
    await bridge.closePane(controllerView.focusKey);
    const removals = requests.filter(row => row.command === 'pane_layout_close').length;
    await bridge.closePane(readonly.focusKey);
    assert.equal(requests.filter(row => row.command === 'pane_layout_close').length, removals, 'Transient close must not change saved layout');
    assert.equal(await bridge.notificationSetting(), true);
    sidebarStates.set('worker', 'waiting_user_answer');
    const notice = await bridge.sidebar();
    assert.equal(notice.notices?.length, 1, 'Only entering waiting-user emits one notification');
    assert.equal(notice.notices[0].id, 'question-one');
    assert.equal(notice.notices[0].launch, 'worker');
    assert.equal((await bridge.sidebar()).notices.length, 1, 'Repeated reads keep a single notification');
    assert.equal(notificationCalls.length, 0, 'System notification API must never be called');
    assert.equal(badgeCalls.at(-1), 1, 'Background Dock badge counts pending user questions');
    focusedWindow = a; app.emit('browser-window-focus');
    assert.equal(badgeCalls.at(-1), 0, 'Foreground clears Dock badge');
    focusedWindow = null; app.emit('browser-window-blur');
    assert.equal(badgeCalls.at(-1), 1, 'Background restores Dock count');
    assert.equal(await bridge.notificationSetting(false, 'dockBadges'), false);
    assert.equal(badgeCalls.at(-1), 0, 'Dock setting clears badge immediately');
    await bridge.notificationSetting(true, 'dockBadges');
    assert.equal(badgeCalls.at(-1), 1);
    for (const state of ['running','idle','waiting_controller_answer','unknown','ended']) {
      sidebarStates.set('worker', state);
      assert.equal((await bridge.sidebar()).notices.length, 0, 'Other states do not notify');
      assert.equal(badgeCalls.at(-1), 0);
    }
    sidebarStates.set('worker', 'waiting_user_answer');
    assert.equal((await bridge.sidebar()).notices.length, 0, 'The same question never notifies twice');
    questionId = 'question-two';
    assert.equal((await bridge.sidebar()).notices.length, 1, 'A different question while waiting notifies once');
    assert.equal(await bridge.notificationSetting(false), false);
    assert.equal((await bridge.sidebar()).notices.length, 0, 'Disabled notifications stay silent');
    questionId = 'question-disabled';
    await bridge.sidebar();
    await bridge.notificationSetting(true);
    assert.equal((await bridge.sidebar()).notices.length, 0, 'Enabling while already waiting is not a new question');
    questionId = null;
    assert.equal((await bridge.sidebar()).notices.length, 0, 'Missing question identity cannot notify');
    questionId = 'question-three';
    assert.equal((await bridge.sidebar()).notices.length, 1);
    await assert.rejects(() => bridge.notificationSetting(true, 'foreign'));
    await assert.rejects(() => bridge.notificationSetting('yes', 'dockBadges'));
    for (const failure of ['transport', 'refused']) {
      questionId = 'disconnect-question-' + failure;
      assert.equal((await bridge.sidebar()).notices.length, 1);
      assert.equal(badgeCalls.at(-1), 1, 'Disconnect probe starts with a trusted pending question');
      sidebarFailure = failure;
      const beforeFailure = requests.length;
      if (failure === 'transport') await assert.rejects(() => bridge.sidebar(), error => error === disconnectedError,
        'Transport failure must reach the caller unchanged');
      else await assert.rejects(() => bridge.sidebar(), /t110-sidebar-unavailable/);
      assert.equal(requests.length, beforeFailure + 1, 'A failed sidebar read must not retry');
      assert.equal(badgeCalls.at(-1), 0, 'Disconnected unknown state must clear Dock badge');
      app.emit('browser-window-blur');
      assert.equal(badgeCalls.at(-1), 0, 'Focus changes must not restore an untrusted count');
      sidebarFailure = null;
      assert.equal((await bridge.sidebar()).notices.length, 0, 'Reconnect preserves question deduplication');
      assert.equal(badgeCalls.at(-1), 1, 'A fresh verified read may restore the pending count');
      assert.equal((await invoke(b, 'a2a:sidebar')).notices.length, 0, 'Sibling window shares the invalidated notice state');
    }


  }
  await bridge.beginComposition(aKey);
  await bridge.observeFocus(aKey, '\x1b[?1004h');
  await bridge.releaseQueue(aKey, { window_id: first.window_id });
  const bindingCommands = requests.filter(row => ['window_composition', 'window_observation', 'window_release'].includes(row.command));
  assert.ok(bindingCommands.every(row => row.window === first.window_id));
  const opening = await run({ ...options, launch: 'opening' });
  const pending = invoke(opening, 'a2a:snapshot', key(opening));
  for (let n = 0; !openingResolve && n < 20; n++) await Promise.resolve();
  assert.ok(openingResolve);
  opening.close();
  await assert.rejects(() => invoke(opening, 'a2a:input', key(opening), 'late'));
  assert.equal(opening.destroyed, false, 'Closing must wait for the admitted identity request');
  openingResolve(); await pending;
  for (let n = 0; !opening.destroyed && n < 20; n++) await Promise.resolve();
  assert.equal(opening.destroyed, true);
  assert.ok(![...liveCredentials.values()].includes('opening'), 'Late identity must be revoked');
  a.close();
  for (let n = 0; !a.destroyed && n < 20; n++) await Promise.resolve();
  assert.ok(a.destroyed); assert.equal(handlers.size, expectedHandlers.length);
  if (withRecovery) assert.ok(layout.has('worker'), 'Closing the application view must preserve the open pane set');
  await invoke(b, 'a2a:input', bKey, 'still B');
  assert.equal(requests.at(-1).target, 'controller');
  const three = await run({ ...options, launch: ['worker', 'controller', 'ideation'] });
  const threeKeys = JSON.parse(three.options.webPreferences.additionalArguments[0].slice('--a2a-pane-keys='.length));
  assert.equal(threeKeys.length, 3, 'Three selected launches must create three pane keys in one window');
  const threeSnapshots = await Promise.all(threeKeys.map(paneKey => invoke(three, 'a2a:snapshot', paneKey)));
  assert.deepEqual(threeSnapshots.map(value => value.launch.id), ['ideation', 'controller', 'worker']);
  assert.equal(new Set(threeSnapshots.map(value => value.window_id)).size, 3);
  for (const [index, paneKey] of threeKeys.entries()) {
    await invoke(three, 'a2a:input', paneKey, 'pane-' + index);
    assert.equal((await invoke(three, 'a2a:output', paneKey, 0)).launch, threeSnapshots[index].launch.id);
  }
  assert.deepEqual(requests.filter(row => row.command === 'window_input').slice(-3).map(row => row.input.sequence), [1, 1, 1]);
  for (const [index, paneKey] of threeKeys.entries()) {
    await invoke(three, 'a2a:release-queue', paneKey, { window_id: threeSnapshots[index].window_id, launch: threeSnapshots[index].launch.id });
  }
  const declarations = requests.filter(row => row.command === 'window_release').slice(-3);
  assert.deepEqual(declarations.map(row => [row.window, row.input.declaration.window_id, row.input.declaration.launch]),
    threeSnapshots.map(value => [value.window_id, value.window_id, value.launch.id]));
  assert.equal(registrations.length, expectedHandlers.length, 'Adding panes must not register more IPC handlers');
  for (const launch of ['foreign', 'historical']) {
    const beforeWindows = windowNumber, beforeCredentials = credentialNumber;
    await assert.rejects(() => run({ ...options, launch: ['ideation', 'controller', launch] }));
    assert.equal(windowNumber, beforeWindows, 'Invalid third pane must not create a window');
    assert.equal(credentialNumber, beforeCredentials, 'Invalid third pane must not receive a credential');
  }
  await assert.rejects(() => run({ ...options, launch: ['worker', 'worker'] }));
  if (withPanes) {
    const reviewed = await run({ ...options, launch: ['controller', 'reviewer'] });
    const reviewKeys = JSON.parse(reviewed.options.webPreferences.additionalArguments[0].slice('--a2a-pane-keys='.length));
    const results = await Promise.all(reviewKeys.map(k => invoke(reviewed, 'a2a:snapshot', k)));
    const index = results.findIndex(r => r.launch.role === 'reviewer');
    assert.ok(index >= 0, 'Reviewer must coexist with other agent panes');
    assert.equal(results[index].input_enabled, false, 'Reviewer pane must remain read-only');
    await invoke(reviewed, 'a2a:pane-action', reviewKeys[index], { type: 'rename', name: '独立审查' });
    assert.equal((await invoke(reviewed, 'a2a:selection')).names[reviewKeys[index]], '独立审查');
  }
  if (withRecovery) {
    const sibling = threeSnapshots[1].window_id;
    await invoke(three, 'a2a:close-pane', threeKeys[0]);
    assert.equal(layout.has('ideation'), false, 'Explicit pane close must persist removal');
    assert.ok(liveCredentials.has(sibling), 'Closing one pane keeps its sibling credential');
    await assert.rejects(() => invoke(three, 'a2a:snapshot', threeKeys[0]));
    layout.clear(); layout.set('worker', { launch: 'worker', position: 3 }); layout.set('controller', { launch: 'controller', position: 1 });
    restorations.set('worker', { lifecycle: 'unknown', historical: true, failed: 'restore_managed_attempt_requires_reclaim',
      restoration: { status: 'failed', error: 'restore_managed_attempt_requires_reclaim' } });
    const restored = await run(options);
    const keys = JSON.parse(restored.options.webPreferences.additionalArguments[0].slice('--a2a-pane-keys='.length));
    const snapshots = await Promise.all(keys.map(k => invoke(restored, 'a2a:snapshot', k)));
    assert.deepEqual(snapshots.map(value => value.launch.id), ['controller', 'worker'], 'Saved positions survive reload without explicit launch arguments');
    assert.equal(snapshots[0].input_enabled, true); assert.equal(snapshots[1].input_enabled, false);
    assert.equal(snapshots[1].window_id, undefined, 'Unrestored worker gets no input credential');
    for (const k of keys) await invoke(restored, 'a2a:close-pane', k);
    assert.equal(layout.size, 0);
    restorations.delete('worker');
    const sole = await run({ ...options, launch: 'worker' });
    await invoke(sole, 'a2a:snapshot', key(sole));
    await invoke(sole, 'a2a:close-pane', key(sole));
    assert.equal(layout.size, 0, 'All explicit pane closes persisted an empty set');
    sole.close();
    for (let n = 0; !sole.destroyed && n < 20; n++) await Promise.resolve();
    const beforeReopen = requests.length;
    for (let repeat = 0; repeat < 2; repeat++) {
      const reopened = await run(options);
      const emptyKeys = JSON.parse(reopened.options.webPreferences.additionalArguments[0].slice('--a2a-pane-keys='.length));
      // Exercise a real snapshot if the faulty default selector reappears.
      for (const k of emptyKeys) await invoke(reopened, 'a2a:snapshot', k);
      assert.equal(layout.size, 0, 'Explicitly closed final pane must stay absent when app reopens');
      assert.equal(emptyKeys.length, 0, 'Saved empty layout must create no pane keys');
      rendererEvent = event(reopened);
      fakeProcess.argv = ['node', 'preload', ...reopened.options.webPreferences.additionalArguments];
      await load(preloadSource, preloadURL);
      assert.deepEqual(Object.keys(bridge).sort(), [...expectedBridge].sort(), 'Empty preload keeps the complete interface');
      assert.equal(bridge.paneKeys.length, 0, 'Preload must expose the saved empty pane set');
      reopened.close();
      for (let n = 0; !reopened.destroyed && n < 20; n++) await Promise.resolve();
      assert.ok(reopened.destroyed, 'Empty window can close normally');
    }
    if (withShell) {
      assert.deepEqual(requests.slice(beforeReopen).map(row => row.input), [
        { command: 'workbench_snapshot', task: 'task-one' }, { command: 'pane_layout', task: 'task-one' },
        { command: 'pane_layout', project: fixtureProject },
        { command: 'workbench_snapshot', task: 'task-one' }, { command: 'pane_layout', task: 'task-one' },
        { command: 'pane_layout', project: fixtureProject },
      ], 'Empty reopen may only read the task and saved task/project layouts, without selecting a launch or issuing credentials');
    } else if (withCatalog) {
      assert.deepEqual(requests.slice(beforeReopen).map(row => row.input), [
        { command: 'workbench_snapshot', task: 'task-one' }, { command: 'pane_layout', task: 'task-one' },
        { command: 'workbench_snapshot', task: 'task-one' }, { command: 'pane_layout', task: 'task-one' },
      ], 'Empty reopen may only read the task and saved layout, without selecting a launch or issuing credentials');
    } else assert.ok(requests.slice(beforeReopen).every(row => row.command === 'pane_layout'), 'Empty reopen must not select a worker or issue input credentials');
    await assert.rejects(() => run({ ...options, launch: [] }), /Distinct nonempty pane launches/);
    const explicit = await run({ ...options, launch: 'worker' });
    await invoke(explicit, 'a2a:snapshot', key(explicit));
    assert.deepEqual([...layout.keys()], ['worker'], 'Explicit selection may reopen a closed pane');
  }
  if (withCatalog) {
    const catalog = await run({ ...options, launch: 'worker' });
    rendererEvent = event(catalog);
    fakeProcess.argv = ['node', 'preload', ...catalog.options.webPreferences.additionalArguments];
    await load(preloadSource, preloadURL);
    const beforeCatalog = requests.length, beforeCredentials = credentialNumber;
    let projects;
    await assert.doesNotReject(async () => { projects = await bridge.projects(); }, 'Projects must work without a pane key');
    assert.deepEqual(JSON.parse(JSON.stringify(projects)), [{ project_id: fixtureProject }]);
    assert.deepEqual(JSON.parse(JSON.stringify(await bridge.tasks(fixtureProject))), [fixtureSummary]);
    assert.deepEqual(JSON.parse(JSON.stringify(await bridge.tasks('absent-project'))), []);
    await assert.rejects(() => bridge.tasks('../invalid'), /invalid_id/);
    assert.deepEqual(requests.slice(beforeCatalog).map(row => row.input), [
      { command: 'projects_list' }, { command: 'tasks_list', project: fixtureProject },
      { command: 'tasks_list', project: 'absent-project' }, { command: 'tasks_list', project: '../invalid' },
    ], 'Window catalog arguments must reach the correct read commands');
    const beforeSelection = requests.length;
    const selected = await bridge.selection();
    assert.deepEqual(JSON.parse(JSON.stringify(selected.task)), fixtureTask);
    assert.deepEqual([...selected.paneKeys], [key(catalog)]);
    assert.equal(requests.length, beforeSelection, 'Reading selection must stay local to this window');
    const cleared = await bridge.selectTask(null);
    assert.equal(cleared.task, null); assert.equal(cleared.paneKeys.length, 0);
    assert.equal((await bridge.selection()).task, null);
    const restored = await bridge.selectTask('task-one');
    assert.deepEqual(JSON.parse(JSON.stringify(restored.task)), fixtureTask);
    assert.equal(restored.paneKeys.length, 1);
    await assert.rejects(() => bridge.selectTask('absent-task'), /unknown_task/);
    await assert.rejects(() => bridge.selectTask(''), /Invalid task/);
    assert.deepEqual([...(await bridge.selection()).paneKeys], [...restored.paneKeys], 'Rejected task must preserve this window selection');
    assert.equal(credentialNumber, beforeCredentials, 'Window catalog calls must not issue pane input credentials');
    assert.equal(registrations.length, expectedHandlers.length);
    if (withShell) {
      await bridge.selectTask(null);
      const beforeNoTask = requests.length;
      if (withPanes) {
        const free = await bridge.newTerminal();
        const freeKey = free.paneKeys[0];
        assert.equal((await bridge.snapshot(freeKey)).launch.project, null);
        await bridge.closePane(freeKey);
      } else {
        await assert.rejects(() => bridge.newTerminal(), /请先选择任务/);
        assert.equal(requests.length, beforeNoTask, 'No task must not create a terminal');
      }
      const selectedAgain = await bridge.selectTask('task-one');
      const pending = bridge.newTerminal();
      await assert.rejects(() => bridge.newTerminal(), /Task view is changing/);
      const created = await pending;
      assert.equal(created.paneKeys.length, selectedAgain.paneKeys.length + 1, 'New terminal must add one pane');
      const shellKey = created.paneKeys.find(key => !selectedAgain.paneKeys.includes(key));
      const shell = await bridge.snapshot(shellKey);
      assert.equal(shell.launch.role, 'shell'); assert.equal(shell.task, null); assert.equal(shell.input_enabled, true);
      await bridge.input(shellKey, 'shell-sentinel');
      assert.equal(requests.at(-1).target, shell.launch.id);
      assert.equal(requests.at(-1).input.sequence, 1);
      const savedProject = records[shell.launch.id].project;
      records[shell.launch.id].project = 'foreign-project';
      const beforeWrongProject = credentialNumber;
      await assert.rejects(() => bridge.snapshot(shellKey), /Shell project or launch mismatch/);
      assert.equal(credentialNumber, beforeWrongProject, 'Foreign shell cannot issue a credential');
      records[shell.launch.id].project = savedProject;
      await bridge.closePane(shellKey);
      assert.equal(shellLayout.size, 0, 'Explicit shell close must remove its project layout');
      await assert.rejects(() => bridge.input(shellKey, 'closed-shell'));
    }
  }
  return ['unregistered_key_rejected', 'keyed_handlers_once', 'per_window_keys_and_sequences', 'iframe_and_other_window_denied',
    'bound_output', 'nullable_controller_and_historical_worker', 'keyed_preload', 'close_drains_identity_and_keeps_other_window',
    'three_panes_independent_credentials_sequences_output', 'foreign_task_and_old_launch_rejected_before_window', 'duplicate_launch_rejected'];
}

try {
  const bad = execFileSync('git', ['show', `${badRevision}:workbench/app/main.ts`], { encoding: 'utf8' });
  let failedForContract = false;
  try { await exercise(bad); }
  catch (error) {
    failedForContract = error instanceof assert.AssertionError && error.message === 'Unregistered pane key was accepted';
    report.known_bad_result = { rejected: failedForContract, error: String(error) };
  }
  assert.ok(failedForContract, 'Known-bad must fail the pane-key admission assertion');
  const tracer = execFileSync('git', ['show', '7e1c68ad432f281e05c2ac58c1fc3fe2fe079d86:workbench/app/main.ts'], { encoding: 'utf8' });
  let missingPanes = false;
  try { await exercise(tracer); }
  catch (error) {
    missingPanes = error instanceof assert.AssertionError && error.message.startsWith('Three selected launches must create three pane keys in one window');
    report.single_pane_counterexample = { revision: '7e1c68ad432f281e05c2ac58c1fc3fe2fe079d86', rejected: missingPanes, error: String(error) };
  }
  assert.ok(missingPanes, 'Single-pane tracer must fail the simultaneous pane-count assertion');
  if (['sidebar','questions','flow','questions-flow'].includes(values.contract)) {
    const revision = '0967cd465ce20c01b0a6ee29b2931ecbf4032caf';
    try { await exercise(execFileSync('git', ['show', revision + ':workbench/app/main.ts'], { encoding: 'utf8' }), true, true,
      execFileSync('git', ['show', revision + ':workbench/app/preload.ts'], { encoding: 'utf8' }), true, true, true); }
    catch (error) { report.sidebar_known_bad = { revision, rejected: error instanceof assert.AssertionError && error.message.startsWith('IPC handler names must match'), error: String(error) }; }
    assert.equal(report.sidebar_known_bad?.rejected, true, 'Baseline must fail the new sidebar contract');
  }
  const candidate = readFileSync(mainURL, 'utf8');
  const candidatePreload = readFileSync(preloadURL, 'utf8');
  const withCreation = ['creation', 'sidebar','questions','flow','questions-flow'].includes(values.contract);
  const withPanes = ['panes', 'creation', 'sidebar','questions','flow','questions-flow'].includes(values.contract);
  const withShell = ['shell', 'panes', 'creation', 'sidebar','questions','flow','questions-flow'].includes(values.contract);
  const withCatalog = values.contract !== 'legacy';
  report.checks = await exercise(candidate, true, withCatalog, candidatePreload, withShell, withPanes, withCreation);
  const mutant = candidate.replace("command: 'pane_layout_close'", "command: 'pane_layout_open'");
  assert.notEqual(mutant, candidate);
  try { await exercise(mutant, true, withCatalog, candidatePreload, withShell, withPanes, withCreation); }
  catch (error) { report.close_mutant = { rejected: error instanceof assert.AssertionError && error.message.startsWith('Explicit pane close must persist removal'), error: String(error) }; }
  assert.equal(report.close_mutant?.rejected, true, 'Close-without-removal mutant must fail the saved-layout assertion');
  const emptyBadRevision = '11b32303bebf276d20026a6e718719d15f5d4068';
  try { await exercise(execFileSync('git', ['show', emptyBadRevision + ':workbench/app/main.ts'], { encoding: 'utf8' }), true); }
  catch (error) { report.empty_layout_known_bad = { revision: emptyBadRevision, rejected: error instanceof assert.AssertionError && error.message.startsWith('Explicitly closed final pane must stay absent when app reopens'), error: String(error) }; }
  assert.equal(report.empty_layout_known_bad?.rejected, true, 'Previous frozen candidate must fail the explicit empty-layout contract');
  if (withCatalog) {
    const windowMutant = candidate.replace("ipcMain.handle('a2a:projects', async event => {\n    const context = windowTarget(event);",
      "ipcMain.handle('a2a:projects', async (event, key: string) => {\n    const { context } = target(event, key);");
    assert.notEqual(windowMutant, candidate, 'Window-level pane-key mutation must change the selected implementation');
    try { await exercise(windowMutant, true, true, candidatePreload, withShell, withPanes, withCreation); }
    catch (error) { report.window_key_mutant = { rejected: error instanceof assert.AssertionError && error.message.includes('Projects must work without a pane key'), error: String(error) }; }
    assert.equal(report.window_key_mutant?.rejected, true, 'A window list handler requiring a pane key must fail its no-key contract');
  }
  if (['sidebar','questions','flow','questions-flow'].includes(values.contract)) {
    for (const [name, mutantSource, expected] of [
      ['notification', candidate.replace('notificationCenter(context).observe(result.agents)', '[]'), 'Only entering waiting-user emits one notification'],
      ['history_credentials', candidate.replace('launch, viewOnly: true', 'launch, viewOnly: false'), 'Transient controller view must not issue an input credential'],
    ]) {
      assert.notEqual(mutantSource, candidate);
      let rejected = false;
      try { await exercise(mutantSource, true, true, candidatePreload, true, true, true); }
      catch (error) { rejected = error instanceof assert.AssertionError && error.message.startsWith(expected); report[name + '_mutant'] = { rejected, error: String(error) }; }
      assert.equal(rejected, true, name + ' mutant must fail its focused assertion');
    }
  }
  report.checks.push('app_close_preserves_layout', 'explicit_close_removes_one', 'saved_order_and_failed_sibling_render', 'failed_worker_no_input_credential',
    'never_saved_default_selection', 'final_close_stays_empty_on_repeated_reopen', 'empty_preload_and_no_credentials', 'explicit_selection_reopens');
  if (withCatalog) report.checks.push(['sidebar','questions','flow','questions-flow'].includes(values.contract) ? values.contract === 'questions-flow' ? 'explicit_22_handler_and_23_bridge_names' : ['flow','questions'].includes(values.contract) ? 'explicit_21_handler_and_22_bridge_names' : 'explicit_20_handler_and_21_bridge_names' : withCreation ? 'explicit_17_handler_and_18_bridge_names' : withPanes ? 'explicit_14_handler_and_15_bridge_names' : withShell ? 'explicit_12_handler_and_13_bridge_names' : 'explicit_11_handler_and_12_bridge_names', 'iframe_and_unknown_window_rejected_for_all_handlers',
    'projects_without_pane_key', 'tasks_project_argument_and_backend_refusals', 'window_selection_without_transport',
    'select_task_null_and_id_preserve_rejected_destination');
  if (withShell) report.checks.push(withPanes ? 'new_terminal_without_task_and_serializes_creation' : 'new_terminal_requires_task_and_serializes_creation', 'shell_project_cwd_and_identity', 'shell_keyed_input_and_close');
  if (['sidebar','questions','flow','questions-flow'].includes(values.contract)) report.checks.push('sidebar_unknown_launch_and_foreign_task_denied', 'sidebar_focus_and_transient_history_readonly',
    'hierarchy_parent_and_descendant_summary_roundtrip', 'notification_edges_and_disable');
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(out, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify(report) + '\n');
process.exitCode = report.status === 'PASS' ? 0 : 1;
