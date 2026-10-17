// Pure main/preload contract check. No Electron, daemon, PTY, ps, socket or model.
// The actual TS modules execute in a VM; only their external boundaries are supplied.
// Failure cases: missing/wrong key, cross-window key, iframe sender, duplicated
// global handlers or credentials, shared sequence, retargeted output, close/open race.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { EventEmitter } from 'node:events';
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const out = process.argv[2];
if (!out) throw new Error('New JSON report path required');
const mainURL = new URL('../app/main.ts', import.meta.url);
const preloadURL = new URL('../app/preload.ts', import.meta.url);
const badRevision = '6974c2aad1233133264b7448e1277cd19fa0b6ba';
const report = { status: 'INCOMPLETE', scope: 'actual main/preload modules with supplied Electron/transport/filesystem boundaries; no GUI or backend proof',
  argv: process.argv, known_bad: badRevision, checks: [], model_turns: 0 };

async function exercise(source) {
  const handlers = new Map(), registrations = [], requests = [], liveCredentials = new Map();
  let windowNumber = 0, credentialNumber = 0, openingResolve;
  const app = Object.assign(new EventEmitter(), { setPath() {}, whenReady: async () => {}, quit() {} });
  class Window extends EventEmitter {
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
    worker: { id: 'worker', thread: 'thread-worker', role: 'worker', preset: null, attempt: 'attempt-one' },
    controller: { id: 'controller', thread: 'thread-controller', role: 'controller', preset: 'executor', attempt: null },
    historical: { id: 'historical', thread: 'thread-old', role: 'worker', preset: null, attempt: 'attempt-old' },
    opening: { id: 'opening', thread: 'thread-opening', role: 'worker', preset: null, attempt: 'attempt-one' },
  };
  async function request(state, input, identity) {
    const item = { command: input.command, input: structuredClone(input), window: identity?.window ?? null };
    requests.push(item);
    if (input.command === 'workbench_snapshot') return { ok: true, task: { task_id: 'task-one', current_attempt: { attempt_id: 'attempt-one' } },
      launch: { task: 'task-one', ...records[input.launch] }, pane: { lifecycle: 'running', failed: null } };
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
  const electron = { app, BrowserWindow: Window, ipcMain,
    contextBridge: { exposeInMainWorld(_name, value) { bridge = value; } },
    ipcRenderer: { invoke: (name, ...args) => Promise.resolve().then(() => handlers.get(name)(rendererEvent, ...args)) } };
  const context = vm.createContext({ process: fakeProcess, console, Buffer });
  async function load(text, url) {
    const module = new vm.SourceTextModule(stripTypeScriptTypes(text, { mode: 'strip' }), {
      context, identifier: url.href, initializeImportMeta(meta) { meta.url = url.href; },
    });
    await module.link(async specifier => {
      let exports;
      if (specifier === 'electron') exports = electron;
      else if (specifier === 'node:fs') exports = { mkdirSync() {} };
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
  assert.equal(requests.filter(row => row.command === 'window_open').length, 1);
  const b = await run({ ...options, launch: 'controller' });
  const bKey = key(b), second = await invoke(b, 'a2a:snapshot', bKey);
  assert.equal(second.input_enabled, true, 'Nullable controller attempt must remain writable');
  assert.notEqual(aKey, bKey); assert.notEqual(first.window_id, second.window_id);
  assert.equal(registrations.length, 6); assert.equal(new Set(registrations).size, 6);
  const beforeDenied = requests.length;
  for (const channel of registrations) {
    await assert.rejects(() => invoke(a, channel, bKey, 'must-not-arrive'));
    await assert.rejects(() => Promise.resolve().then(() => handlers.get(channel)({ ...event(a), senderFrame: {} }, aKey, 'must-not-arrive')));
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
  await load(readFileSync(preloadURL, 'utf8'), preloadURL);
  assert.equal(bridge.paneKeys[0], aKey); assert.ok(Object.isFrozen(bridge.paneKeys));
  assert.equal((await bridge.snapshot(aKey)).window_id, first.window_id);
  await assert.rejects(() => bridge.snapshot(bKey));
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
  assert.ok(a.destroyed); assert.equal(handlers.size, 6);
  await invoke(b, 'a2a:input', bKey, 'still B');
  assert.equal(requests.at(-1).target, 'controller');
  return ['unregistered_key_rejected', 'six_handlers_once', 'per_window_keys_and_sequences', 'iframe_and_other_window_denied',
    'bound_output', 'nullable_controller_and_historical_worker', 'keyed_preload', 'close_drains_identity_and_keeps_other_window'];
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
  report.checks = await exercise(readFileSync(mainURL, 'utf8'));
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(out, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify(report) + '\n');
process.exitCode = report.status === 'PASS' ? 0 : 1;
