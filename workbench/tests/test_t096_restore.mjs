// Real SQLite/native files; supplied subprocess and PTY boundaries only.
// Failure list: lost open set/order; config drift; argv/version/session refusal;
// one failure aborting siblings; worker resumed or attempt mutated; closed pane
// resurrected; success before process identity; history/queued prompts replayed.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import assert from 'node:assert/strict';
import { OrchestrationStore } from '../src/store.ts';

const panesURL = new URL('../src/panes.ts', import.meta.url);
async function exercise(source) {
  const root = mkdtempSync('/private/tmp/t096-contract-'), store = new OrchestrationStore(root);
  let starts = [], writes = 0;
  try {
    assert.equal(store.hasPaneLayout('task'), false, 'No layout event means never saved');
    const other = { id: 'other-launch', task: 'other-task' };
    store.event('pane_native_session', { native_session: 'metadata-only' }, { id: 'metadata', task: 'task' });
    assert.equal(store.hasPaneLayout('task'), false, 'Native metadata alone is not a saved layout');
    store.event('pane_layout_opened', { position: 0 }, other);
    store.event('pane_layout_closed', {}, other);
    assert.equal(store.hasPaneLayout('other-task'), true, 'Explicit empty layout retains its saved state');
    assert.equal(store.hasPaneLayout('task'), false, 'Another task cannot initialize this task layout');
    const fixtureProcess = { execPath: process.execPath, kill() { throw Object.assign(new Error('fixture process absent'), { code: 'ESRCH' }); } };
    const context = vm.createContext({ console, process: fixtureProcess, Buffer, setTimeout, clearTimeout, URL, TextDecoder });
    const module = new vm.SourceTextModule(stripTypeScriptTypes(source), { context,
      initializeImportMeta(meta) { meta.url = panesURL.href; } });
    await module.link(async specifier => {
      let exports;
      if (specifier === 'node:module') exports = { createRequire: () => Object.assign(name => {
        assert.equal(name, 'node-pty');
        return { spawn(shell, args, options) {
          starts.push({ shell, args: [...args], options });
          return { pid: 41000 + starts.length, onData() {}, onExit() {}, write() { writes++; } };
        } };
      }, { resolve() { throw new Error('helper probe not allowed in contract'); } }) };
      else if (specifier === 'node:child_process') {
        const execFile = (executable, args, options, callback) => {
          if (executable === '/fixture/claude') callback(null, '2.1.302 (Claude Code)\n', '');
          else if (executable === '/fixture/wrong-version') callback(null, '9.9.9 (Claude Code)\n', '');
          else if (executable === '/fixture/codex') callback(null, 'codex-cli 0.162.1\n', '');
          else if (executable === '/bin/ps') callback(null, starts.map((s, i) =>
            `${41001+i} 1 ${41001+i} ${42000+i} /bin/zsh\n${42000+i} ${41001+i} ${42000+i} ${42000+i} ${s.options.env.TEST_EXECUTABLE}`).join('\n'), '');
          else throw new Error('unapproved process boundary ' + executable);
        };
        execFile[Symbol.for('nodejs.util.promisify.custom')] = (executable, args, options) => new Promise((resolve, reject) =>
          execFile(executable, args, options, (error, stdout, stderr) => error ? reject(error) : resolve({ stdout, stderr })));
        exports = { execFile };
      }
      if (!exports && specifier.startsWith('node:')) exports = await import(specifier);
      else if (!exports) exports = await import(new URL(specifier, panesURL));
      return new vm.SyntheticModule(Object.keys(exports), function() { for (const [key, value] of Object.entries(exports)) this.setExport(key, value); }, { context });
    });
    await module.evaluate();
    const records = [], expected = new Map();
    const labels = ['missing-argv', 'version-mismatch', 'ideation', 'missing-session', 'executor', 'worker', 'closed'];
    for (const [position, label] of labels.entries()) {
      const session = randomUUID(), config = join(root, label), worker = label === 'worker';
      const executable = worker ? '/fixture/codex' : label === 'version-mismatch' ? '/fixture/wrong-version' : '/fixture/claude';
      const argv = worker ? [executable, '--sandbox', 'workspace-write', '-m', 'sentinel-worker', '-c', 'service_tier="default"'] :
        [executable, '--session-id', session, '--model', 'sentinel-' + label, '--effort', 'low', '--settings', '{"hooks":{},"sentinel":"a b\\\"c"}'];
      const resume = worker ? [...argv, 'resume', session] : [executable, '--resume', ...argv.slice(2)];
      const record = { id: 'launch-' + label, project: 'project', task: 'task', attempt: worker ? 'attempt-worker' : null,
        role: worker ? 'worker' : 'controller', preset: label === 'executor' ? 'executor' : 'ideation',
        session, thread: 'thread-' + label, spec_rev: 1, cli: worker ? 'Codex' : 'Claude Code',
        cli_version: worker ? 'codex-cli 0.162.1' : '2.1.302 (Claude Code)',
        ...(label === 'missing-argv' ? {} : { argv }), shell: '/bin/zsh',
        env: { CLAUDE_CONFIG_DIR: config, CODEX_HOME: config, HOME: root, TEST_EXECUTABLE: executable }, worktree: '/fixture' };
      records.push(record); expected.set(record.id, resume);
      const directory = join(config, worker ? 'sessions' : 'projects/-fixture'); mkdirSync(directory, { recursive: true });
      if (label !== 'missing-session') writeFileSync(join(directory, (worker ? 'rollout-' : '') + session + '.jsonl'), JSON.stringify(worker ?
        { type: 'session_meta', payload: { source: 'cli', id: session, cwd: '/fixture' } } : { type: 'user', sessionId: session, cwd: '/fixture' }) + '\n');
      mkdirSync(join(root, 'traces', record.id), { recursive: true }); writeFileSync(join(root, 'traces', record.id, 'pty.raw'), 'initial trace\n');
      store.launch(record); store.event('pane_started', { shell_pid: 7 }, record);
      store.event('pane_layout_opened', { position, native_session: session, resume_argv: resume }, record);
      if (label === 'closed') store.event('pane_layout_closed', {}, record);
    }
    store.db.exec('CREATE TABLE tasks (id TEXT PRIMARY KEY, data TEXT NOT NULL)');
    const worker = records.find(r => r.role === 'worker');
    const task = { task_id: 'task', project_id: 'project', spec_rev: 1, repo: '/fixture', current_attempt: {
      attempt_id: worker.attempt, thread_id: worker.thread, session_id: worker.session, fence: worker.fence, workspace: '/fixture',
      state: 'running', runtime_identity: { launch: worker.id, shell_pid: 7, leader_pid: 8, native_session: worker.session } } };
    store.db.prepare('INSERT INTO tasks VALUES (?,?)').run('task', JSON.stringify(task));
    const taskBefore = store.db.prepare('SELECT data FROM tasks WHERE id=?').get('task').data;
    const panes = new module.namespace.Panes(root, store, {}, reason => { throw new Error(reason); });
    await panes.recover('epoch-one');
    const workerStatus = panes.status(worker.thread);
    assert.equal(workerStatus.restoration?.error, 'restore_managed_attempt_requires_reclaim', 'Managed worker must remain unrestored pending explicit reclaim');
    assert.equal(panes.panes.has(worker.thread), false, 'Managed worker must not own a new PTY');
    assert.equal(starts.length, 2, 'Exactly the two valid controllers must resume despite failed siblings');
    for (const label of ['ideation', 'executor']) {
      const record = records.find(r => r.id === 'launch-' + label);
      const event = store.lastEvent(record.id, ['pane_restored', 'pane_restore_failed']);
      assert.equal(event.type, 'pane_restored');
      assert.deepEqual(event.data.argv, expected.get(record.id), 'Every resume argv token must equal the independently specified input');
      const spawned = starts.find(start => start.args[3].includes(record.session));
      const quote = value => "'" + value.replaceAll("'", "'\\''") + "'";
      assert.equal(spawned?.args[3], expected.get(record.id).map(quote).join(' ') + '; exec /bin/zsh -f -i',
        'Actual PTY command must carry every independently supplied argv field');
      assert.deepEqual(store.launchRecord(record.id), record, 'Launch record stays immutable');
      assert.equal(panes.status(record.thread).restoration.status, 'restored');
      assert.equal(panes.get(record.thread).attempt, null, 'Controller must not adopt the task worker attempt');
    }
    for (const [label, code] of [['missing-argv', 'restore_argv_missing'], ['version-mismatch', 'restore_version_mismatch'], ['missing-session', 'restore_session_missing']]) {
      const record = records.find(r => r.id === 'launch-' + label);
      assert.equal(panes.status(record.thread).restoration.error, code);
      assert.equal(store.lastEvent(record.id, ['pane_restored']), null, 'A failed pane must not have a success receipt');
    }
    assert.equal(store.lastEvent('launch-closed', ['pane_restored', 'pane_restore_failed']), null);
    assert.equal(store.db.prepare('SELECT data FROM tasks WHERE id=?').get('task').data, taskBefore, 'Worker attempt must remain byte-for-byte unchanged');
    assert.deepEqual(store.openPanes('task').map(p => p.position), [0, 1, 2, 3, 4, 5]);
    assert.equal(writes, 0, 'Restoration must not write a prompt or release an old queue');
    for (const record of records) store.event('pane_layout_closed', {}, record);
    const reopened = new OrchestrationStore(root);
    try {
      assert.equal(reopened.hasPaneLayout('task'), true, 'Saved state survives reopening SQLite after the final close');
      assert.deepEqual(reopened.openPanes('task'), [], 'Persisted empty layout remains empty');
      assert.equal(reopened.hasPaneLayout('never-opened-task'), false, 'Never-opened task stays distinct after reopening SQLite');
    } finally { reopened.close(); }
    return ['two_controllers_resume', 'three_refusals_isolate_siblings', 'worker_unrestored_no_pty', 'attempt_unchanged',
      'argv_every_field_equal', 'actual_pty_argv_every_field_equal', 'launch_immutable', 'saved_positions', 'explicit_close_excluded', 'zero_input_writes',
      'saved_empty_persists_in_sqlite', 'never_saved_and_native_only_distinct', 'layout_saved_state_scoped_to_task'];
  } finally { store.close(); }
}
const report = { status: 'INCOMPLETE', scope: 'real SQLite/native files; supplied process boundaries; not GUI/CLI end-to-end evidence', checks: [], model_turns: 0 };
try {
  const revision = 'a8fbc72bdf88de661f25ffce8d9ac9dff3f3c4f6';
  try { await exercise(execFileSync('git', ['show', revision + ':workbench/src/panes.ts'], { encoding: 'utf8' })); }
  catch (error) { report.known_bad = { revision, rejected: error instanceof assert.AssertionError && error.message.startsWith('Managed worker must remain unrestored'), error: String(error) }; }
  assert.equal(report.known_bad?.rejected, true, 'Previous candidate must fail the worker non-resume contract');
  const candidate = readFileSync(panesURL, 'utf8');
  const mutant = candidate.replace('const shellArgv = ["-f", "-i", "-c", shellCommand(argv)',
    'const shellArgv = ["-f", "-i", "-c", shellCommand([argv[0]!, "--resume", opened.native_session!])');
  assert.notEqual(mutant, candidate);
  try { await exercise(mutant); }
  catch (error) { report.spawn_argv_mutant = { rejected: error instanceof assert.AssertionError && error.message.startsWith('Actual PTY command must carry every independently supplied argv field'), error: String(error) }; }
  assert.equal(report.spawn_argv_mutant?.rejected, true, 'Event-only argv mutant must fail at the actual PTY boundary');
  report.checks = await exercise(candidate); report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(process.argv[2], JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
