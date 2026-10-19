// Actual main → daemon decoder/auth/handler → gates → SQLite. Only Electron,
// PTY and socket-listening boundaries are supplied, as in review probe-postsave-02.
// The triggers abort result events after a real commit, not the business write.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { EventEmitter } from 'node:events';
import * as fs from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import { DatabaseSync } from 'node:sqlite';
import assert from 'node:assert/strict';

const output = process.argv[2];
if (!output || fs.existsSync(output)) throw new Error('New report path required');
const source = resolve(process.argv[3] ?? '.');
const root = fs.mkdtempSync('/private/tmp/t106-postcommit-');
const tree = join(root, 'runtime');
const report = { status: 'INCOMPLETE', source, root, model_turns: 0, cases: [],
  scope: 'actual main/daemon/gates/SQLite; supplied Electron, PTY, socket listening; no GUI proof' };
const previousCredential = process.env.A2A_OPERATOR_CREDENTIAL;
async function load(file, overrides) {
  const context = vm.createContext({ process, console, Buffer, setTimeout, clearTimeout });
  const module = new vm.SourceTextModule(stripTypeScriptTypes(fs.readFileSync(file, 'utf8')), {
    context, initializeImportMeta: meta => { meta.url = pathToFileURL(file).href; meta.main = false; } });
  await module.link(async spec => {
    const values = overrides[spec] ?? await import(spec.startsWith('.') ? new URL(spec, pathToFileURL(file)).href : spec);
    return new vm.SyntheticModule(Object.keys(values), function () {
      for (const [key, value] of Object.entries(values)) this.setExport(key, value);
    }, { context });
  });
  await module.evaluate(); return module.namespace;
}
try {
  fs.cpSync(join(source, 'workbench/src'), join(tree, 'src'), { recursive: true });
  fs.cpSync(process.env.T106_DEPENDENCIES ?? '/Users/luckye/Documents/Code/a2a/workbench/node_modules', join(tree, 'node_modules'), { recursive: true, verbatimSymlinks: true });
  const gatesModule = await import(pathToFileURL(join(tree, 'src/gates/core.ts')));
  const credentials = await import(pathToFileURL(join(tree, 'src/credentials.ts')));
  const repo = join(root, 'repo');
  execFileSync('git', ['-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo]);
  fs.mkdirSync(join(repo, 'tests')); fs.writeFileSync(join(repo, 'tests/check.mjs'), 'throw new Error("registration must not execute completion");\n');
  execFileSync('git', ['-C', repo, 'add', '.']);
  execFileSync('git', ['-C', repo, '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=T106 fixture', '-c', 'user.email=t106@example.invalid', 'commit', '-m', 'Independent postcommit fixture']);
  for (const name of ['save-result', 'save-event-failure', 'save-readback-failure', 'save-before-write', 'save-conflicting-record', 'create-result', 'create-readback-failure']) {
    const state = join(root, name); fs.mkdirSync(state);
    process.env.A2A_OPERATOR_CREDENTIAL = join(root, name + '-operator.json');
    credentials.createOperatorCredential(state);
    let listener;
    class Panes { constructor() { this.panes = new Map(); } async recover() {} async shutdown() {} }
    const net = { createServer: callback => { listener = callback; return { once() {}, listen(_path, ready) { ready(); }, close(done) { done(); } }; } };
    const daemon = await load(join(tree, 'src/daemon.ts'), { 'node:net': net,
      'node:fs': { ...fs, chmodSync(path, mode) { if (path !== join(state, 'control.sock')) fs.chmodSync(path, mode); } },
      './panes.ts': { Panes, spawnHelper: () => '/fixture/no-pty' } });
    let gates;
    await daemon.serve(state, {}, path => { gates = new gatesModule.A2AGates(path); return gates; });
    await new Promise(resolve => setTimeout(resolve, 0));
    const row = { name, status: 'INCOMPLETE', commands: [] }; report.cases.push(row);
    const request = async (_state, input, identity) => new Promise((resolve, reject) => {
      row.commands.push(input.command);
      const connection = new EventEmitter(); connection.setEncoding = () => {};
      connection.end = wire => { try { resolve(JSON.parse(wire)); } catch (error) { reject(error); } queueMicrotask(() => connection.emit('close')); };
      listener(connection); connection.emit('data', JSON.stringify({ id: name + '-' + row.commands.length, input, identity }) + '\n');
    });
    const db = new DatabaseSync(join(state, 'state.sqlite3'));
    const mutation = name.startsWith('save') ? 'card_save' : 'create';
    const readback = name.startsWith('save') ? 'card_show' : 'status';
    let condition = `NEW.type='request_result' AND json_extract(NEW.data,'$.command')='${mutation}'`;
    if (['save-before-write', 'save-conflicting-record'].includes(name)) condition = "NEW.type='request_received' AND json_extract(NEW.data,'$.input.command')='card_save'";
    if (name === 'save-event-failure') condition += ` OR NEW.type='request_rejected' AND json_extract(NEW.data,'$.input.command')='card_save'`;
    if (name.endsWith('readback-failure')) condition += ` OR NEW.type='request_received' AND json_extract(NEW.data,'$.input.command')='${readback}'`;
    db.exec(`CREATE TRIGGER fail_after_commit BEFORE INSERT ON orchestration_events WHEN ${condition} BEGIN SELECT RAISE(ABORT,'T106 postcommit fault'); END;`);
    let invoke;
    try {
      const handlers = new Map();
      class Window extends EventEmitter {
        constructor() { super(); this.webContents = { id: 1, mainFrame: {}, on() {}, setWindowOpenHandler() {} }; } async loadFile() {}
      }
      const electron = { app: Object.assign(new EventEmitter(), { whenReady: async () => {}, setPath() {} }), BrowserWindow: Window,
        ipcMain: { handle: (key, fn) => handlers.set(key, fn) }, dialog: { showOpenDialog: async () => ({ canceled: false, filePaths: [repo] }) } };
      const main = await load(join(source, 'workbench/app/main.ts'), { electron, '../src/transport.ts': { request }, '../src/credentials.ts': credentials });
      const window = await main.run({ state, userData: join(state, 'ui') });
      const event = { sender: window.webContents, senderFrame: window.webContents.mainFrame };
      invoke = (command, ...args) => Promise.resolve().then(() => handlers.get('a2a:creation-' + command)(event, ...args));
      const draft = await invoke('repository');
      const card = { id: draft.card.id, source: null, goal: '独立提交后故障 · ' + name, non_goals: ['不运行模型'],
        paths: { allow: ['.'], deny: ['.git/'] }, oracle_paths: ['tests/check.mjs'], completion_conditions: [{ argv: [process.execPath, 'tests/check.mjs'] }],
        red_commands: [], task_type: '测试', repair_target: null, complexity: 'S',
        executor: { cli: 'Codex', model: 'gpt-6.1-sol', effort: 'xhigh' }, base_commit: null, writer: null };
      const input = { task: card.id, project: 'postcommit-project', title: '提交后的错误 ' + name, branch: 'refs/heads/main', card: JSON.stringify(card) };
      if (name === 'save-conflicting-record') {
        const seed = join(state, 'independent-existing-card.json');
        fs.writeFileSync(seed, JSON.stringify({ ...card, goal: '属于另一份输入的旧卡片' }));
        // Seed an independent existing version through the real gate. The UI
        // request still traverses daemon/auth and is faulted before its write.
        assert.equal((await gates.call({ command: 'card_save', task: card.id, card: seed, expected_version: 0 })).ok, true);
      }
      row.result = await invoke('submit', input);
      row.counts = Object.fromEntries(['tasks', 'task_card_versions', 'task_card_snapshots', 'attempts', 'launch_records'].map(table =>
        [table, Number(db.prepare('SELECT count(*) AS n FROM ' + table).get().n)]));
      assert.equal(row.counts.task_card_versions, name === 'save-before-write' ? 0 : 1, 'Independent SQLite count must locate the fault before or after the card commit');
      assert.equal(row.counts.tasks, mutation === 'create' ? 1 : 0);
      assert.equal(row.commands.filter(command => command === mutation).length, 1, 'Do not replay a mutation');
      assert.ok(row.commands.includes(readback), 'An uncertain response must be checked through the read-only gate');
      if (name === 'create-result') {
        assert.equal(row.result.ok, true, 'A matching ready task proves registration despite result-event failure');
        assert.equal(row.result.task.task_id, card.id); assert.equal(row.result.task.title, input.title);
      } else {
        assert.equal(row.result.ok, false);
        await assert.rejects(() => invoke('submit', input), /registration/i);
        if (name === 'save-result') {
          assert.equal(row.result.persisted, true, 'Readback must recognize the persisted card');
          assert.equal((await invoke('cancel')).persisted, true);
        } else {
          assert.equal(row.result.persisted, 'unknown', 'Unverifiable state must remain unknown');
          await assert.rejects(() => invoke('cancel'), /unknown/i);
          await assert.rejects(() => invoke('repository'), /registration/i);
        }
      }
      row.status = 'PASS';
    } catch (error) { row.error = String(error); row.stack = error.stack; row.status = 'NO_GO'; }
    finally {
      const stopped = await request(state, { command: 'daemon_stop' }, credentials.readOperatorCredential(state));
      assert.equal(stopped.ok, true);
      for (let i = 0; fs.existsSync(join(state, 'daemon.pid')) && i < 100; i++) await new Promise(resolve => setTimeout(resolve, 5));
      assert.ok(!fs.existsSync(join(state, 'daemon.pid')), 'Fake listening server must complete real daemon shutdown'); db.close();
    }
  }
  report.status = report.cases.every(row => row.status === 'PASS') ? 'PASS' : 'NO_GO';
} catch (error) { report.error = String(error); report.stack = error.stack; }
finally {
  if (previousCredential === undefined) delete process.env.A2A_OPERATOR_CREDENTIAL; else process.env.A2A_OPERATOR_CREDENTIAL = previousCredential;
  fs.rmSync(join(tree, 'node_modules'), { recursive: true, force: true });
  if (report.status === 'PASS') { fs.rmSync(root, { recursive: true, force: true }); report.fixture_removed = true; }
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' }); console.log(JSON.stringify(report));
}
process.exitCode = report.status === 'PASS' ? 0 : 1;
