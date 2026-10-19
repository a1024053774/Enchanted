// Execute actual main IPC with supplied Electron/transport boundaries, no model.
// Failure modes: absent entry, renderer path injection, foreign window/frame,
// cross-window repo reuse, writes before confirmation, swallowed gate refusal,
// cancel retains a draft, parallel submission, and hidden partial registration.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { EventEmitter } from 'node:events';
import { readFileSync, writeFileSync, mkdtempSync, rmSync, existsSync, realpathSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const output = process.argv[2];
if (!output || existsSync(output)) throw new Error('New report path required');
const source = resolve(process.argv[3] ?? 'workbench/app/main.ts');
const report = { status: 'INCOMPLETE', scope: 'main IPC only; transport supplied, no backend/GUI proof', source, checks: [], model_turns: 0 };
const root = realpathSync(mkdtempSync(join(tmpdir(), 't106-ipc-')));
const repo = join(root, 'repo');
const handlers = new Map(), commands = [], saved = [], tasks = [];
let picked = repo, gateFailure = null, blockValidation = null, number = 0;
try {
  execFileSync('git', ['-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo]);
  const template = id => ({ id, source: null, goal: '', non_goals: [], paths: { allow: [], deny: [] },
    oracle_paths: [], completion_conditions: [], red_commands: [], task_type: '后端逻辑', repair_target: null,
    complexity: 'M', executor: { cli: 'Codex', model: '', effort: '' }, base_commit: null, writer: null });
  const request = async (_state, input, identity) => {
    if (input.command === 'pane_layout') return { ok: true, saved: true, panes: [] };
    assert.equal(identity.kind, 'operator', 'Creation commands must use operator identity');
    commands.push(structuredClone(input));
    if (input.command === 'card_template') { assert.equal(input.repo, repo); return { ok: true, card: template(input.task) }; }
    const card = input.card ? JSON.parse(readFileSync(input.card, 'utf8')) : null;
    if (card) assert.equal(card.id, input.task, 'Fixture card and request must identify the same task');
    if (input.command === 'card_validate') {
      if (blockValidation) await blockValidation;
      if (gateFailure === 'validate') return { ok: false, error: 'invalid_task_card', details: { field: 'card', reason: 'Fields do not match the task card schema.' } };
      return { ok: true, card };
    }
    if (input.command === 'card_save') {
      assert.equal(input.expected_version, 0);
      if (gateFailure === 'save') return { ok: false, error: 'card_version_conflict' };
      saved.push(card); return { ok: true, card_version: 1, card };
    }
    if (input.command === 'create') {
      assert.equal(input.repo, repo, 'Repository must be chosen by main, never supplied by renderer');
      assert.equal(input.branch, 'refs/heads/main'); assert.equal(input.card_version, 1);
      if (gateFailure === 'create') return { ok: false, error: 'project_branch_conflict' };
      const task = { task_id: input.task, project_id: input.project, title: input.title, card: saved.at(-1) };
      tasks.push(task); return { ok: true, task };
    }
    throw new Error('Unexpected command: ' + input.command);
  };
  class Window extends EventEmitter {
    constructor() { super(); this.webContents = { id: ++number, mainFrame: {}, on() {}, setWindowOpenHandler() {} }; }
    async loadFile() {}
  }
  const electron = { app: Object.assign(new EventEmitter(), { whenReady: async () => {}, setPath() {} }), BrowserWindow: Window,
    ipcMain: { handle: (name, handler) => { assert.ok(!handlers.has(name)); handlers.set(name, handler); } },
    dialog: { showOpenDialog: async () => ({ canceled: picked === null, filePaths: picked === null ? [] : [picked] }) } };
  const context = vm.createContext({ process, console, Buffer });
  const module = new vm.SourceTextModule(stripTypeScriptTypes(readFileSync(source, 'utf8')), {
    context, initializeImportMeta: meta => { meta.url = pathToFileURL(source).href; } });
  await module.link(async spec => {
    const exports = spec === 'electron' ? electron : spec === '../src/transport.ts' ? { request }
      : spec === '../src/credentials.ts' ? { readOperatorCredential: () => ({ kind: 'operator' }) } : await import(spec);
    return new vm.SyntheticModule(Object.keys(exports), function () {
      for (const [key, value] of Object.entries(exports)) this.setExport(key, value);
    }, { context });
  });
  await module.evaluate();
  const window = await module.namespace.run({ state: root, userData: join(root, 'ui') });
  const event = { sender: window.webContents, senderFrame: window.webContents.mainFrame };
  const names = ['a2a:creation-repository', 'a2a:creation-submit', 'a2a:creation-cancel'];
  assert.ok(names.every(name => handlers.has(name)), 'Creation IPC entry is missing');
  const invoke = (name, ...args) => Promise.resolve().then(() => handlers.get('a2a:creation-' + name)(event, ...args));
  for (const name of names) {
    await assert.rejects(async () => handlers.get(name)({ sender: window.webContents, senderFrame: {} }));
    await assert.rejects(async () => handlers.get(name)({ sender: { id: 999 }, senderFrame: {} }));
  }
  await assert.rejects(() => invoke('repository', '/renderer/injected'));
  let draft = await invoke('repository');
  assert.equal(draft.repo, repo); assert.equal(draft.branch, 'refs/heads/main');
  assert.equal(commands.at(-1).command, 'card_template');
  assert.equal(saved.length, 0); assert.equal(tasks.length, 0);
  await invoke('cancel');
  await assert.rejects(() => invoke('submit', {}));
  picked = null; assert.equal(await invoke('repository'), null); picked = repo;
  draft = await invoke('repository');
  const other = await module.namespace.run({ state: root, userData: join(root, 'ui') });
  await assert.rejects(() => handlers.get(names[1])({ sender: other.webContents, senderFrame: other.webContents.mainFrame }, {}));
  const card = { ...template(draft.card.id), goal: 'sentinel-goal-比较<标签>', non_goals: ['保留旧任务'],
    paths: { allow: ['src/'], deny: [] }, oracle_paths: ['tests/'],
    completion_conditions: [{ argv: ['node', 'tests/check.mjs'] }],
    executor: { cli: 'Codex', model: 'gpt-6.1-sol', effort: 'xhigh' } };
  const input = { task: card.id, project: 'sentinel-project', title: '独立标题<边界>',
    branch: 'refs/heads/main', card: JSON.stringify(card) };
  await assert.rejects(() => invoke('submit', { ...input, repo: '/renderer/injected' }));
  gateFailure = 'validate';
  const denied = await invoke('submit', input);
  assert.equal(denied.ok, false); assert.equal(denied.error, 'invalid_task_card');
  assert.equal(denied.details.field, 'card'); assert.equal(saved.length, 0); assert.equal(tasks.length, 0);
  gateFailure = 'save';
  assert.equal((await invoke('submit', input)).error, 'card_version_conflict');
  assert.equal(tasks.length, 0);
  gateFailure = null;
  let unblock; blockValidation = new Promise(resolve => { unblock = resolve; });
  const pending = invoke('submit', input);
  // Wait until the validation boundary is reached, while its outcome is held.
  for (let i = 0; commands.at(-1)?.command !== 'card_validate' && i < 100; i++) await new Promise(resolve => setTimeout(resolve, 1));
  await assert.rejects(() => invoke('submit', input));
  await assert.rejects(() => invoke('cancel'));
  unblock(); blockValidation = null;
  const created = await pending;
  assert.equal(created.ok, true); assert.equal(created.task.title, input.title);
  assert.equal(created.task.project_id, input.project); assert.deepEqual(saved.at(-1), card);
  assert.deepEqual(commands.slice(-3).map(row => row.command), ['card_validate', 'card_save', 'create']);
  assert.ok(commands.filter(row => row.card).every(row => !existsSync(row.card)), 'Temporary card files must be removed');
  draft = await invoke('repository'); gateFailure = 'create';
  const partial = await invoke('submit', { ...input, task: draft.card.id, card: JSON.stringify({ ...card, id: draft.card.id }) });
  assert.equal(partial.ok, false); assert.equal(partial.persisted, true);
  assert.equal(partial.error, 'project_branch_conflict');
  await assert.rejects(() => invoke('submit', input), /registration/i);
  const closed = await invoke('cancel'); assert.equal(closed.persisted, true);
  report.checks = ['main_owned_repository', 'operator_commands_only', 'foreign_frame_window_and_extra_path_rejected',
    'window_scoped_draft', 'cancel_and_native_picker_cancel_do_not_register', 'validation_refusal_keeps_details_before_save',
    'save_refusal_does_not_create', 'confirmation_serialized', 'exact_card_and_metadata_forwarded',
    'temporary_files_removed', 'partial_registration_visible_and_not_replayed'];
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
finally { rmSync(root, { recursive: true, force: true }); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
