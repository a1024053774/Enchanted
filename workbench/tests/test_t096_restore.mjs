// Contract evidence with real SQLite and native-session files; supplied process
// boundaries only. No daemon, socket, PTY, ps, Electron, vendor CLI or model.
// Failure list: lost open set/order; replay config drift; missing argv/version/
// session; one refusal aborting siblings; stale attempt; closed pane resurrected;
// restored state published before foreground identity; old native events replayed.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import assert from 'node:assert/strict';
import { OrchestrationStore } from '../src/store.ts';

const report = { status: 'INCOMPLETE', scope: 'contract with real SQLite; supplied process boundaries, not end-to-end evidence', checks: [], model_turns: 0 };
const root = mkdtempSync('/private/tmp/t096-contract-');
const store = new OrchestrationStore(root);
const starts = [];
try {
  const context = vm.createContext({ console, process, Buffer, setTimeout, clearTimeout, URL, TextDecoder });
  const source = readFileSync(new URL('../src/panes.ts', import.meta.url), 'utf8');
  const module = new vm.SourceTextModule(stripTypeScriptTypes(source), { context,
    initializeImportMeta(meta) { meta.url = new URL('../src/panes.ts', import.meta.url).href; } });
  await module.link(async specifier => {
    let exports;
    if (specifier === 'node:module') exports = { createRequire: () => Object.assign(name => {
      assert.equal(name, 'node-pty');
      return { spawn(shell, args, options) { starts.push({ shell, args: [...args], options });
        return { pid: 1000 + starts.length, onData() {}, onExit() {}, write() { throw new Error('recovery must not submit input'); } }; } };
    }, { resolve() { throw new Error('no helper probe in this isolated contract'); } }) };
    else if (specifier === 'node:child_process') exports = { execFile(executable, args, options, callback) {
      if (executable === '/fixture/claude') callback(null, '2.1.302 (Claude Code)\n', '');
      else if (executable === '/fixture/wrong-version') callback(null, '9.9.9 (Claude Code)\n', '');
      else if (executable === '/bin/ps') callback(null, starts.map((s, i) => `${1001+i} 1 ${1001+i} ${2000+i} /bin/zsh\n${2000+i} ${1001+i} ${2000+i} ${2000+i} /fixture/claude`).join('\n'), '');
      else throw new Error('unapproved process boundary ' + executable);
    } };
    if (specifier === 'node:child_process') exports.execFile[Symbol.for('nodejs.util.promisify.custom')] = (executable, args, options) => new Promise((resolve, reject) => exports.execFile(executable, args, options, (error, stdout, stderr) => error ? reject(error) : resolve({ stdout, stderr })));
    if (!exports && specifier.startsWith('node:')) exports = await import(specifier);
    else if (!exports) exports = await import(new URL(specifier, new URL('../src/panes.ts', import.meta.url)));
    return new vm.SyntheticModule(Object.keys(exports), function() { for (const [key, value] of Object.entries(exports)) this.setExport(key, value); }, { context });
  });
  await module.evaluate();
  const config = join(root, 'claude'); mkdirSync(join(config, 'projects', '-fixture'), { recursive: true });
  const session = '00112233-4455-4677-8899-aabbccddeeff';
  writeFileSync(join(config, 'projects', '-fixture', session + '.jsonl'), JSON.stringify({ type: 'user', sessionId: session, cwd: '/fixture' }) + '\n');
  const record = { id: 'launch-a', project: 'project', task: 'task', attempt: null, role: 'controller', preset: 'ideation',
    session, thread: 'thread-a', spec_rev: 1, cli: 'Claude Code', cli_version: '2.1.302 (Claude Code)',
    argv: ['/fixture/claude', '--session-id', session, '--model', 'sentinel-model', '--effort', 'low', '--settings', '{"hooks":{}}'],
    shell: '/bin/zsh', env: { CLAUDE_CONFIG_DIR: config, A2A_SESSION: session, HOME: root }, worktree: '/fixture' };
  store.launch(record);
  store.event('pane_started', { shell_pid: 7 }, record);
  mkdirSync(join(root, 'traces', record.id), { recursive: true });
  writeFileSync(join(root, 'traces', record.id, 'pty.raw'), 'initial trace\n');
  store.event('pane_layout_opened', { position: 0, native_session: session, resume_argv: ['/fixture/claude', '--resume', session, '--model', 'sentinel-model', '--effort', 'low', '--settings', '{"hooks":{}}'] }, record);
  store.db.exec('CREATE TABLE tasks (id TEXT PRIMARY KEY, data TEXT NOT NULL)');
  store.db.prepare('INSERT INTO tasks VALUES (?,?)').run('task', JSON.stringify({ task_id: 'task', project_id: 'project', spec_rev: 1, repo: '/fixture' }));
  const panes = new module.namespace.Panes(root, store, {}, reason => { throw new Error(reason); });
  await panes.recover('contract-daemon');
  assert.equal(starts.length, 1, 'Previously open pane must start its recorded native session after restart');
  assert.equal(store.lastEvent(record.id, ['pane_restored', 'pane_restore_failed'])?.type, 'pane_restored', 'Foreground identity must be confirmed before restoration succeeds');
  assert.equal(panes.status(record.thread).restoration.status, 'restored');
  assert.deepEqual(store.launchRecord(record.id), record, 'Original launch record must remain unchanged');
  assert.equal(store.lastEvent(record.id, ['pane_restored']).data.argv[1], '--resume');
  assert.deepEqual(store.lastEvent(record.id, ['pane_restored']).data.argv.slice(2), record.argv.slice(2), 'All non-selector arguments retain their values and order');
  report.checks.push('previously_open_pane_restarted', 'foreground_identity_confirmed', 'immutable_launch', 'argv_fields_retained');
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.assertion = error instanceof assert.AssertionError; }
finally { store.close(); }
writeFileSync(process.argv[2], JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
