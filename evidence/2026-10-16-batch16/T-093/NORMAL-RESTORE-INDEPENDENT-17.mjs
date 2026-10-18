import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import { join, dirname } from 'node:path';
import { randomUUID } from 'node:crypto';
import { stripTypeScriptTypes } from 'node:module';
import vm from 'node:vm';
import { OrchestrationStore } from '/Users/luckye/Documents/Code/a2a-wt-t093/workbench/src/store.ts';
import { Refusal } from '/Users/luckye/Documents/Code/a2a-wt-t093/workbench/src/gates/core.ts';

const repo = '/Users/luckye/Documents/Code/a2a-wt-t093';
const output = dirname(new URL(import.meta.url).pathname);
const panesURL = new URL('file://' + repo + '/workbench/src/panes.ts');
const helperURL = new URL('./paneRecovery.ts', panesURL);
const candidate = '91cd22d523af28ab9a13631d6919635be430ba34';
const badRevision = '8771ba58d71a3fc025b09e32c45096b39858572e';
const candidateSource = fs.readFileSync(panesURL, 'utf8');
const helperSource = fs.readFileSync(helperURL, 'utf8');
const badSource = fs.readFileSync(join(output, 'known-bad-panes.ts'), 'utf8');
const toPlain = value => JSON.parse(JSON.stringify(value));
const savedVersion = '2.1.302 (Claude Code)';
const businessError = 'normal_login_restore_requires_protected_start';
const descriptions = [
  { name: 'normal-surviving', auth: 'isolated normal login', native: true },
  { name: 'normal-no-native', auth: 'isolated normal login', native: false, absentBinding: true },
  { name: 'fake-valid', auth: 'isolated fake API only', native: true },
  { name: 'legacy-valid', native: true, legacy: true },
  { name: 'worker', native: true, worker: true },
  { name: 'fake-bad-version', auth: 'isolated fake API only', native: true, badVersion: true },
  { name: 'fake-no-native-file', auth: 'isolated fake API only', native: false },
  { name: 'fake-replaced-executable', auth: 'isolated fake API only', native: true, replaced: true },
  { name: 'fake-wrong-process', auth: 'isolated fake API only', native: true, wrongProcess: true },
];

async function exercise(source, label) {
  const nonce = randomUUID();
  const root = fs.mkdtempSync(join(output, label + '-'));
  const cwd = join(root, 'repository-' + nonce);
  fs.mkdirSync(cwd);
  const store = new OrchestrationStore(root);
  const rows = [], operations = [], starts = [], auth = [];
  let clock = 0;
  const add = (name, kind, details = {}) => operations.push({ name, kind, ...details });
  const canonical = row => '/supplied/kernel-' + row.name + '-' + nonce;
  const byPath = path => rows.find(row => path === row.executable || String(path).startsWith(row.privateRoot + '/'));
  const readOperation = (kind, path) => {
    const name = byPath(path)?.name ?? null;
    add(name, kind, { path: String(path) });
    if (/credentials|auth\.json|Keychain/i.test(String(path))) {
      auth.push({ kind, path: String(path) });
      throw new Error('Auth read is forbidden in this review');
    }
    assert(String(path).startsWith(root + '/'), 'Supplied filesystem access must stay in the new fixture');
  };
  const suppliedFs = { ...fs };
  for (const kind of ['existsSync', 'readFileSync', 'readdirSync', 'openSync', 'accessSync']) {
    suppliedFs[kind] = (path, ...rest) => { readOperation(kind, path); return fs[kind](path, ...rest); };
  }
  suppliedFs.realpathSync = path => {
    const row = rows.find(row => row.executable === path);
    if (row) { add(row.name, 'canonical'); return canonical(row); }
    readOperation('realpathSync', path);
    return fs.realpathSync(path);
  };
  const suppliedProcess = {
    execPath: process.execPath, env: {},
    kill(pid, signal) {
      const row = rows.find(row => row.oldPid === pid);
      assert(row, 'A previous-process check must refer to a supplied PID');
      assert.equal(signal, 0);
      add(row.name, 'previous-process');
      throw Object.assign(new Error('Supplied previous process is absent'), { code: 'ESRCH' });
    },
  };
  const pty = { spawn(shell, args, options) {
    const row = rows.find(row => row.record.env.CLAUDE_CONFIG_DIR === options.env.CLAUDE_CONFIG_DIR);
    assert(row, 'Supplied PTY must use one saved launch environment');
    add(row.name, 'pty');
    const callbacks = [];
    const start = { name: row.name, shell, args: [...args], env: { ...options.env }, pid: 64100 + starts.length };
    starts.push(start);
    return { pid: start.pid, onData() {}, onExit(callback) { callbacks.push(callback); },
      write() { add(row.name, 'input-write'); throw new Error('Recovery must not send input'); },
      kill(signal) { assert.equal(signal, 'SIGHUP'); add(row.name, 'supplied-stop'); for (const callback of callbacks) callback({ exitCode: 0, signal: 1 }); },
    };
  } };
  const execFile = (file, argv, options, callback) => {
    const row = rows.find(row => row.executable === file);
    if (row) {
      assert.deepEqual([...argv], ['--version']);
      assert.deepEqual(toPlain(options.env), row.record.env);
      add(row.name, 'version', { executable: file, argv: [...argv] });
      callback(null, (row.badVersion ? '0.0.0 (Claude Code)' : savedVersion) + '\n', '');
      return;
    }
    assert.equal(file, '/usr/bin/python3', 'No real subprocess is allowed');
    assert.deepEqual([...argv.slice(0, 3)], ['-I', '-S', '-B']);
    assert.equal(argv[3], repo + '/workbench/src/processSnapshot.py');
    const start = starts.find(start => start.pid === Number(argv[4]));
    assert(start, 'Observer must refer to a supplied PTY');
    const processRow = rows.find(row => row.name === start.name);
    const leader = start.pid + 801;
    add(start.name, 'supplied-observer', { shell_pid: start.pid, leader_pid: leader });
    callback(null, JSON.stringify({ schema: 1, root_pid: start.pid, method: 'macOS libproc', rows: [
      { pid: start.pid, ppid: 1, pgid: start.pid, tpgid: leader, command: '/bin/zsh' },
      { pid: leader, ppid: start.pid, pgid: leader, tpgid: leader,
        command: processRow.wrongProcess ? '/supplied/unrelated-process-' + nonce : canonical(processRow) },
    ] }), '');
  };
  execFile[Symbol.for('nodejs.util.promisify.custom')] = (file, argv, options) => new Promise((resolve, reject) =>
    execFile(file, argv, options, (error, stdout, stderr) => error ? reject(error) : resolve({ stdout, stderr })));
  const context = vm.createContext({ process: suppliedProcess, Buffer, URL, TextDecoder, setTimeout, clearTimeout,
    Date: class extends Date { static now() { clock += 20000; return clock; } } });
  const synthetic = values => new vm.SyntheticModule(Object.keys(values), function() {
    for (const [name, value] of Object.entries(values)) this.setExport(name, value);
  }, { context });
  const helper = new vm.SourceTextModule(stripTypeScriptTypes(helperSource), { context,
    initializeImportMeta(meta) { meta.url = helperURL.href; } });
  const linker = async specifier => {
    if (specifier === 'node:fs') return synthetic(suppliedFs);
    if (specifier === 'node:child_process') return synthetic({ execFile });
    if (specifier === 'node:module') return synthetic({ createRequire: () => name => {
      assert.equal(name, 'node-pty'); return pty;
    } });
    if (specifier === './gates/core.ts') return synthetic({ Refusal });
    if (specifier === './store.ts') return synthetic({ OrchestrationStore });
    if (specifier === './paneRecovery.ts') return helper;
    if (specifier === './claudeLogin.ts') return synthetic({ ClaudeLogin: class {
      static prepare() { auth.push({ kind: 'ClaudeLogin.prepare' }); throw new Error('Auth preparation is forbidden'); }
    } });
    if (specifier === './claudeLaunch.ts') return synthetic({ claudeLaunch() { throw new Error('Launch preparation is outside recovery'); } });
    if (specifier === './claudeNotice.ts') return synthetic({ noticeText() { throw new Error('Notice is outside recovery'); }, SECURITY_NOTICE_TEXT: 'unused' });
    assert(specifier.startsWith('node:'), 'Unapproved import ' + specifier);
    return synthetic(await import(specifier));
  };
  const module = new vm.SourceTextModule(stripTypeScriptTypes(source), { context,
    initializeImportMeta(meta) { meta.url = panesURL.href; } });
  try {
    await module.link(linker); await module.evaluate();
    for (const [position, description] of descriptions.entries()) {
      const row = { ...description, session: randomUUID(), id: randomUUID(), thread: randomUUID(),
        oldPid: 70100 + position, privateRoot: join(root, description.name),
        executable: '/supplied/cli-' + description.name + '-' + nonce };
      const config = join(row.privateRoot, '.claude');
      const tail = ['--model', 'model-' + nonce, '--effort', 'low', '--permission-mode', 'manual',
        '--settings', JSON.stringify({ hooks: {}, permissions: { allow: ['Read(' + nonce + ')'] } }),
        '--append-system-prompt', "fresh role '" + nonce + "'\nline 2 $literal; &", '--strict-mcp-config',
        '--mcp-config', '{"mcpServers":{}}', '--tools', 'Bash,Read', '--debug-file', join(row.privateRoot, 'debug.log')];
      row.expected = [row.executable, '--resume', row.session, ...tail];
      row.record = { id: row.id, project: 'project-' + nonce, task: 'task-' + nonce,
        attempt: row.worker ? 'attempt-' + nonce : null, fence: row.worker ? 19 : null,
        role: row.worker ? 'worker' : 'controller', preset: position % 2 ? 'ideation' : 'executor',
        session: row.session, thread: row.thread, spec_rev: 41, cli: row.worker ? 'Codex' : 'Claude Code',
        cli_version: savedVersion, argv: [row.executable, '--session-id', row.session, ...tail], shell: '/bin/zsh',
        env: { HOME: join(row.privateRoot, 'home'), CLAUDE_CONFIG_DIR: config, CODEX_HOME: config, REVIEW_NONCE: nonce }, worktree: cwd,
        ...(row.auth ? { authentication: row.auth } : {}),
        ...(row.legacy ? {} : { executable_path: row.replaced ? '/supplied/previous-' + nonce : canonical(row) }) };
      rows.push(row);
      fs.mkdirSync(join(config, 'projects', 'new-' + nonce), { recursive: true });
      if (row.native) fs.writeFileSync(join(config, 'projects', 'new-' + nonce, row.session + '.jsonl'),
        JSON.stringify({ type: 'user', sessionId: row.session, cwd, review_nonce: nonce }) + '\n');
      fs.mkdirSync(join(root, 'traces', row.id), { recursive: true });
      fs.writeFileSync(join(root, 'traces', row.id, 'pty.raw'), 'prior history ' + nonce + '\n');
      store.launch(row.record); store.event('pane_started', { shell_pid: row.oldPid }, row.record);
      store.event('pane_layout_opened', { position, native_session: row.absentBinding ? null : row.session,
        resume_argv: row.absentBinding ? null : row.expected }, row.record);
    }
    const worker = rows.find(row => row.worker);
    const task = { task_id: worker.record.task, project_id: worker.record.project, spec_rev: 41, repo: cwd,
      current_attempt: { attempt_id: worker.record.attempt, thread_id: worker.thread, session_id: worker.session,
        fence: 19, workspace: cwd, state: 'running', runtime_identity: { launch: worker.id,
          shell_pid: worker.oldPid, leader_pid: 80201, native_session: worker.session } } };
    store.db.exec('CREATE TABLE tasks (id TEXT PRIMARY KEY, data TEXT NOT NULL)');
    store.db.prepare('INSERT INTO tasks VALUES (?,?)').run(task.task_id, JSON.stringify(task));
    const originalLaunches = store.db.prepare('SELECT id,data FROM launch_records ORDER BY rowid').all().map(toPlain);
    const originalTask = store.db.prepare('SELECT data FROM tasks WHERE id=?').get(task.task_id).data;
    fs.writeFileSync(join(root, 'inputs.json'), JSON.stringify({ nonce, task, launches: rows.map(row => row.record),
      layouts: store.openPanes() }, null, 2) + '\n', { flag: 'wx' });
    const panes = new module.namespace.Panes(root, store, {}, reason => { throw new Error(reason); });
    await panes.recover('fresh-ordinary-daemon-' + nonce);
    const results = rows.map(row => ({ name: row.name, launch: row.id, status: toPlain(panes.status(row.thread)),
      last_event: store.lastEvent(row.id, ['pane_restored', 'pane_restore_failed']),
      operations: operations.filter(op => op.name === row.name),
      history_unchanged: store.db.prepare('SELECT data FROM launch_records WHERE id=?').get(row.id).data ===
        originalLaunches.find(launch => launch.id === row.id).data,
      has_live_pane: panes.panes.has(row.thread),
      success_receipt: store.lastEvent(row.id, ['pane_restored']) !== null }));
    const allHistoryUnchanged = assert.deepEqual(
      store.db.prepare('SELECT id,data FROM launch_records ORDER BY rowid').all().map(toPlain), originalLaunches);
    assert.equal(store.db.prepare('SELECT data FROM tasks WHERE id=?').get(task.task_id).data, originalTask,
      'Worker attempt bytes must not change');
    assert.equal(auth.length, 0, 'Recovery must not read or prepare authentication');
    assert.equal(operations.some(op => op.kind === 'input-write'), false, 'Recovery must not send input');
    const normalBoundarySafe = results.filter(row => row.name.startsWith('normal-')).every(row =>
      row.operations.length === 0 && !row.has_live_pane && !row.success_receipt && row.history_unchanged &&
      row.status.restoration.status === 'failed' && row.status.restoration.error === businessError &&
      /正常登录入口/.test(row.status.restoration.details ?? '') && /重新启动/.test(row.status.restoration.details ?? ''));
    const outputResult = { label, revision: label === 'candidate' ? candidate : badRevision, nonce, root,
      normalBoundarySafe, auth_operations: auth, task_unchanged: true, launch_history_unchanged: true, results, starts };
    fs.writeFileSync(join(output, label + '-raw.json'), JSON.stringify(outputResult, null, 2) + '\n', { flag: 'wx' });
    for (const name of ['fake-valid', 'legacy-valid']) {
      const row = rows.find(row => row.name === name), result = results.find(row => row.name === name);
      assert.equal(result.last_event.type, 'pane_restored', name + ' must restore');
      assert.deepEqual(toPlain(result.last_event.data.argv), row.expected, 'Resume argv must preserve every original option');
      const start = starts.find(start => start.name === name);
      const quote = value => "'" + value.split("'").join("'\\''") + "'";
      assert.equal(start.shell, '/bin/zsh');
      assert.deepEqual(start.args, ['-f', '-i', '-c', row.expected.map(quote).join(' ') + '; exec /bin/zsh -f -i'],
        'The PTY boundary must receive the complete saved argv');
      assert.equal(panes.get(row.thread).record.executable_path, canonical(row));
      assert.equal(result.last_event.data.leader, start.pid + 801, 'Success must use the supplied foreground process identity');
      assert.deepEqual(result.operations.filter(op => ['version', 'canonical', 'pty', 'supplied-observer'].includes(op.kind))
        .map(op => op.kind), ['version', 'canonical', 'pty', 'supplied-observer']);
      assert.equal(panes.get(row.thread).attempt, null, 'Controller must not adopt the worker attempt');
    }
    for (const [name, error] of [['worker', 'restore_managed_attempt_requires_reclaim'],
      ['fake-bad-version', 'restore_version_mismatch'], ['fake-no-native-file', 'restore_session_missing'],
      ['fake-replaced-executable', 'restore_executable_changed'], ['fake-wrong-process', 'restore_process_missing']]) {
      const row = results.find(row => row.name === name);
      assert.equal(row.status.restoration.error, error, name + ' must retain its boundary check');
      assert.equal(row.success_receipt, false);
      if (name !== 'fake-wrong-process') assert.equal(row.has_live_pane, false);
    }
    assert.equal(results.find(row => row.name === 'worker').operations.length, 0, 'Worker must not reach a supplied process boundary');
    const openBefore = store.openPanes().map(toPlain);
    store.close();
    const reopened = new OrchestrationStore(root);
    try {
      assert.deepEqual(reopened.openPanes().map(toPlain), openBefore, 'Every historical pane must remain in the saved layout');
      assert.deepEqual(reopened.db.prepare('SELECT id,data FROM launch_records ORDER BY rowid').all().map(toPlain), originalLaunches);
      assert.equal(reopened.db.prepare('SELECT data FROM tasks WHERE id=?').get(task.task_id).data, originalTask);
      if (label === 'candidate') for (const row of rows.filter(row => row.name.startsWith('normal-'))) {
        const event = reopened.lastEvent(row.id, ['pane_restore_failed']);
        assert.equal(event.data.error, businessError, 'Normal-login refusal must persist after reopening SQLite');
      }
    } finally { reopened.close(); }
    return outputResult;
  } finally {
    try { store.close(); } catch (error) { if (error.code !== 'ERR_INVALID_STATE') throw error; }
  }
}

const report = { status: 'INCOMPLETE', candidate, known_bad_revision: badRevision,
  scope: 'L0/L1 only: actual recover with fresh real SQLite/native files; supplied CLI, PTY, old-process and observer boundaries; no auth contents',
  limitations: ['No OS sandbox/Keychain/CLI/model/daemon/socket/UI execution', 'new443 and native seven-case validation remain pending'] };
try {
  const current = await exercise(candidateSource, 'candidate');
  assert.equal(current.normalBoundarySafe, true, 'Normal-login recovery must stop before all supplied CLI/PTY/auth boundaries');
  report.candidate_result = { local: 'PASS', raw: join(output, 'candidate-raw.json'), fixture: current.root };
  const bad = await exercise(badSource, 'known-bad');
  assert.equal(bad.normalBoundarySafe, false, 'The same business signal must reject the known-bad implementation');
  const surviving = bad.results.find(row => row.name === 'normal-surviving');
  assert(surviving.operations.some(op => op.kind === 'version'), 'Known-bad must reach the version boundary');
  assert(surviving.operations.some(op => op.kind === 'pty'), 'Known-bad must reach the supplied PTY boundary');
  report.counterexample = { rejected: true, business_signal: 'normalBoundarySafe=false', raw: join(output, 'known-bad-raw.json'),
    fixture: bad.root, normal_surviving_operations: surviving.operations.map(op => op.kind),
    normal_surviving_error: surviving.status.restoration.error };
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
fs.writeFileSync(join(output, 'summary.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
