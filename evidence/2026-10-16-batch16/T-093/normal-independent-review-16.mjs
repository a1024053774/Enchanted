import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { stripTypeScriptTypes } from 'node:module';
import vm from 'node:vm';
import { OrchestrationStore } from '/Users/luckye/Documents/Code/a2a-wt-t093/workbench/src/store.ts';

const outputRoot = new URL('.', import.meta.url).pathname;
const panesURL = new URL('file:///Users/luckye/Documents/Code/a2a-wt-t093/workbench/src/panes.ts');
const source = fs.readFileSync(panesURL, 'utf8');
const kernel = '/fixture/review-kernel-cli';
const results = [];
async function runCase(name, authentication, sessionExists) {
  const root = fs.mkdtempSync(join(outputRoot, name + '-'));
  const store = new OrchestrationStore(root), calls = [], starts = [];
  const processBoundary = { execPath: process.execPath, env: {}, kill() { throw Object.assign(new Error('supplied absent old process'), { code: 'ESRCH' }); } };
  const context = vm.createContext({ process: processBoundary, Buffer, URL, TextDecoder, setTimeout, clearTimeout });
  const module = new vm.SourceTextModule(stripTypeScriptTypes(source), { context, initializeImportMeta(meta) { meta.url = panesURL.href; } });
  try {
    await module.link(async specifier => {
      let values;
      if (specifier === 'node:module') values = { createRequire: () => name => {
        assert.equal(name, 'node-pty');
        return { spawn(shell, argv, options) {
          starts.push({ shell, argv: [...argv], config: options.env.CLAUDE_CONFIG_DIR });
          calls.push('pty-spawn');
          return { pid: 51307, onData() {}, onExit() {}, write() { throw new Error('input forbidden'); }, kill() {} };
        } };
      } };
      else if (specifier === 'node:fs') values = { ...fs, realpathSync(path) {
        return path === '/fixture/review-cli' ? kernel : fs.realpathSync(path);
      } };
      else if (specifier === 'node:child_process') {
        const execFile = (file, argv, options, callback) => {
          if (file === '/fixture/review-cli') {
            assert.deepEqual([...argv], ['--version']); calls.push('cli-version');
            callback(null, '2.1.302 (Claude Code)\n', '');
          } else {
            assert.equal(file, '/usr/bin/python3');
            assert(argv[3].endsWith('/processSnapshot.py'));
            assert.equal(Number(argv[4]), 51307); calls.push('given-process-snapshot');
            callback(null, JSON.stringify({ schema: 1, root_pid: 51307, method: 'macOS libproc', rows: [
              { pid: 51307, ppid: 1, pgid: 51307, tpgid: 52309, command: '/bin/zsh' },
              { pid: 52309, ppid: 51307, pgid: 52309, tpgid: 52309, command: kernel },
            ] }), '');
          }
        };
        execFile[Symbol.for('nodejs.util.promisify.custom')] = (file, argv, options) => new Promise((resolve, reject) =>
          execFile(file, argv, options, (error, stdout, stderr) => error ? reject(error) : resolve({ stdout, stderr })));
        values = { execFile };
      } else if (specifier.startsWith('node:')) values = await import(specifier);
      else values = await import(new URL(specifier, panesURL));
      return new vm.SyntheticModule(Object.keys(values), function() { for (const [key, value] of Object.entries(values)) this.setExport(key, value); }, { context });
    });
    await module.evaluate();
    const session = randomUUID(), id = randomUUID(), thread = randomUUID(), home = join(root, 'surviving-private-home');
    const config = join(home, '.claude'), cwd = join(root, 'repo');
    fs.mkdirSync(cwd); fs.mkdirSync(join(config, 'projects/review'), { recursive: true });
    if (sessionExists) fs.writeFileSync(join(config, 'projects/review', session + '.jsonl'), JSON.stringify({ type: 'user', sessionId: session, cwd }) + '\n');
    const argv = ['/fixture/review-cli', '--session-id', session, '--model', 'review-sentinel-model', '--effort', 'low', '--permission-mode', 'manual', '--settings', '{"hooks":{}}'];
    const record = { id, project: 'review-project', task: 'review-task', attempt: null, role: 'controller', preset: 'executor',
      session, thread, spec_rev: 1, cli: 'Claude Code', cli_version: '2.1.302 (Claude Code)', argv, shell: '/bin/zsh',
      authentication, executable_path: kernel, env: { HOME: home, CLAUDE_CONFIG_DIR: config, ANTHROPIC_BASE_URL: 'http://127.0.0.1:51821' }, worktree: cwd };
    fs.mkdirSync(join(root, 'traces', id), { recursive: true }); fs.writeFileSync(join(root, 'traces', id, 'pty.raw'), '');
    store.launch(record); store.event('pane_started', { shell_pid: 7 }, record);
    store.event('pane_layout_opened', { position: 0, native_session: session, resume_argv: [argv[0], '--resume', ...argv.slice(2)] }, record);
    store.db.exec('CREATE TABLE tasks (id TEXT PRIMARY KEY, data TEXT NOT NULL)');
    store.db.prepare('INSERT INTO tasks VALUES (?,?)').run(record.task, JSON.stringify({ task_id: record.task, project_id: record.project, spec_rev: 1, repo: cwd }));
    const panes = new module.namespace.Panes(root, store, {}, reason => { throw new Error(reason); });
    await panes.recover('review-ordinary-daemon');
    const event = store.lastEvent(id, ['pane_restored', 'pane_restore_failed']);
    return { name, authentication, sessionExists, outer_session: false, calls, starts: starts.length,
      restoration: event.type, error: event.data.error ?? null, history_unchanged: JSON.stringify(store.launchRecord(id)) === JSON.stringify(record) };
  } finally { store.close(); }
}
results.push(await runCase('normal-surviving-session', 'isolated normal login', true));
results.push(await runCase('normal-missing-session', 'isolated normal login', false));
results.push(await runCase('fake-control', 'isolated fake API only', true));
const control = results.find(row => row.name === 'fake-control');
assert.equal(control.starts, 1, 'ordinary fake-API restore must exercise the PTY boundary');
const normal = results.find(row => row.name === 'normal-surviving-session');
const violated = normal.calls.includes('cli-version') || normal.starts > 0;
const report = { status: violated ? 'FAIL' : 'PASS', candidate: '8771ba58d71a3fc025b09e32c45096b39858572e',
  scope: 'actual recover, real fresh SQLite/native files, ordinary context; all subprocess/PTY boundaries supplied; no OS/CLI/auth/network',
  contract: 'normal-login restore requires protected context before any CLI or PTY boundary', results };
fs.writeFileSync(join(outputRoot, 'normal-independent.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = violated ? 2 : 0;
