// Actual daemon, Unix socket, gates, Panes, collector, SQLite and trace files.
// A seeded in-memory PTY identity supplies the controlled native logs; no CLI,
// OS process identity or model behavior is claimed. No product method is mocked.
// Failure cases: auxiliary/unknown starts release a root question, status scans
// unconsumed logs, or any sidebar implementation writes a table or trace.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import * as fs from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';

const [output, sourceArg = '.', mode = 'readonly'] = process.argv.slice(2);
if (!output || fs.existsSync(output) || !['identity', 'readonly', 'filename', 'rollout', 'flow'].includes(mode)) throw new Error('New output and identity/readonly/filename/rollout/flow mode required');
const source = resolve(sourceArg), root = fs.mkdtempSync('/private/tmp/t107-daemon-read-');
const tree = join(root, 'runtime'), state = join(root, 'state'), repo = join(root, 'repo');
const report = { status: 'INCOMPLETE', mode, source, root, model_calls: 0,
  scope: 'actual daemon/socket/Panes/collector/SQLite/traces; seeded PTY identity, no CLI or model' };
const previousCredential = process.env.A2A_OPERATOR_CREDENTIAL;
let pane, host, request, operator, started = false;
try {
  fs.cpSync(join(source, 'workbench/src'), join(tree, 'src'), { recursive: true });
  fs.cpSync(process.env.T107_DEPENDENCIES ?? fileURLToPath(new URL('../node_modules', import.meta.url)), join(tree, 'node_modules'),
    { recursive: true, dereference: true });
  // npm --ignore-scripts leaves this pinned darwin-arm64 helper at 0644.
  // Prepare only the private test copy; product startup must still refuse it.
  fs.chmodSync(join(tree, 'node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper'), 0o755);
  fs.mkdirSync(state); fs.mkdirSync(repo);
  execFileSync('git', ['-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo], { env: { ...process.env, LC_ALL: 'C' } });
  const panesModule = await import(pathToFileURL(join(tree, 'src/panes.ts'))), { Panes } = panesModule;
  const { nativeSessionFile } = await import(pathToFileURL(join(tree, 'src/paneRecovery.ts')));
  const { A2AGates } = await import(pathToFileURL(join(tree, 'src/gates/core.ts')));
  const credentials = await import(pathToFileURL(join(tree, 'src/credentials.ts')));
  ({ request } = await import(pathToFileURL(join(tree, 'src/transport.ts'))));
  process.env.A2A_OPERATOR_CREDENTIAL = join(root, 'operator.json');
  credentials.createOperatorCredential(state); operator = credentials.readOperatorCredential(state);
  const home = join(state, 'native-home'), logs = join(home, 'sessions');
  fs.mkdirSync(logs, { recursive: true }); fs.mkdirSync(join(state, 'traces/launch'), { recursive: true });
  fs.writeFileSync(join(state, 'traces/launch/pty.raw'), 'independent trace sentinel\n');
  const meta = (id, source = 'cli') => ({ type: 'session_meta', payload: { id, source, cwd: repo } });
  const start = turn_id => ({ type: 'event_msg', payload: { type: 'task_started', turn_id } });
  const question = { type: 'response_item', payload: { type: 'function_call', name: 'request_user_input', call_id: 'question-1',
    internal_chat_message_metadata_passthrough: { turn_id: 'root-turn' } } };
  const filenameCase = ['filename', 'rollout'].includes(mode);
  const rootLog = join(logs, mode === 'rollout' ? 'rollout-2026-10-19T12-00-00-root-session.jsonl' : 'root-session.jsonl');
  fs.writeFileSync(rootLog, [meta('root-session'), start('root-turn'), ...filenameCase ? [] : [question]].map(JSON.stringify).join('\n') + '\n');
  class SeededPanes extends Panes {
    constructor(...args) {
      super(...args); host = this;
      const record = { id: 'launch', thread: 'thread', role: 'worker', project: 'p', task: 't', attempt: 'a', worktree: repo,
        execution_state: 'prepared', cli_version: 'codex-cli 0.163.0', env: { CODEX_HOME: home } };
      this.store.launch(record);
      pane = { record, attempt: { workspace: repo }, pty: { pid: 123 }, state: 'busy', stopped: false, archived: false,
        failed: null, native: 'root-session', turn: 'root-turn', active: { id: 'submission', nativeTurn: 'root-turn' },
        queue: [], writing: false, offsets: new Map(), interrupted: false };
      this.panes.set('thread', pane);
    }
  }
  const daemonFile = join(tree, 'src/daemon.ts'), context = vm.createContext({ process, console, Buffer, setTimeout, clearTimeout, setInterval, clearInterval });
  const module = new vm.SourceTextModule(stripTypeScriptTypes(fs.readFileSync(daemonFile, 'utf8')), {
    context, initializeImportMeta: meta => { meta.url = pathToFileURL(daemonFile).href; meta.main = false; } });
  await module.link(async spec => {
    // Everything panes.ts exports, with the seeded Panes in place of the real one.
    const exports = spec === './panes.ts' ? { ...panesModule, Panes: SeededPanes }
      : await import(spec.startsWith('.') ? new URL(spec, pathToFileURL(daemonFile)).href : spec);
    return new vm.SyntheticModule(Object.keys(exports), function () { for (const [key, value] of Object.entries(exports)) this.setExport(key, value); }, { context });
  });
  await module.evaluate();
  await module.namespace.serve(state, {}, path => {
    const gates = new A2AGates(path, host);
    const task = { task_id: 't', project_id: 'p', repo, title: 'Independent read boundary', state: 'ready', spec_rev: 1, current_attempt: null };
    gates.db.prepare('INSERT INTO tasks VALUES (?,?)').run('t', JSON.stringify(task));
    return gates;
  });
  started = true;
  for (let i = 0; i < 100; i++) {
    const ready = await request(state, { command: 'pane_layout' });
    if (!ready.recovering) break;
    await new Promise(resolve => setTimeout(resolve, 5));
  }
  const saved = () => JSON.parse(execFileSync('python3', ['-B', join(dirname(fileURLToPath(import.meta.url)), 't107_persistence.py'), state], { encoding: 'utf8' }));
  const read = async () => {
    const result = await request(state, { command: mode === 'flow' ? 'flow_snapshot' : 'sidebar_snapshot' });
    assert.equal(result.ok, true, 'Sidebar must return a business result');
    return (mode === 'flow' ? result.unassigned : result.agents).find(row => row.id === 'launch').state;
  };
  if (filenameCase) {
    host.scan(pane);
    host.store.event('turn_submitted', { id: 'submission' }, pane.record);
    host.store.event('turn_start_signal', { session_id: 'root-session' }, pane.record);
    report.before_question = await read();
    assert.equal(report.before_question, 'running', 'Same submission hook must prove the active turn before a question');
    fs.appendFileSync(rootLog, JSON.stringify(question) + '\n');
    host.scan(pane);
    const before = saved(), offsets = [...pane.offsets];
    report.observed = await read();
    assert.equal(report.observed, 'unknown', 'Unanswered root question must stay unknown under either native filename');
    assert.deepEqual(saved(), before, 'Sidebar read changed persisted tables or traces');
    assert.deepEqual([...pane.offsets], offsets, 'Sidebar read consumed native bytes');
    // The recovery locator must accept the same recorded root file and ignore
    // unrelated files before parsing; this checks its existing naming contract.
    fs.writeFileSync(join(logs, 'unrelated.jsonl'), 'unrelated malformed sentinel\n');
    assert.equal(nativeSessionFile(pane.record, 'root-session'), rootLog);
    report.filename = rootLog;
  } else if (mode === 'identity') {
    host.scan(pane); // Collection is explicit and outside the read boundary.
    assert.equal(await read(), 'unknown');
    fs.writeFileSync(join(logs, 'zz-helper.jsonl'), [meta('helper', { subagent: { parent_thread_id: 'root-session' } }), start('helper-turn')].map(JSON.stringify).join('\n') + '\n');
    host.scan(pane);
    assert.equal(pane.turn, 'root-turn'); assert.equal(pane.active.nativeTurn, 'root-turn');
    report.observed = await read();
    assert.equal(report.observed, 'unknown', 'Auxiliary native start must not release the root question');
    // Missing file/session attribution must not release it either.
    host.store.event('native_record', { record: start('root-turn') }, pane.record);
    assert.equal(await read(), 'unknown', 'Unknown native origin must not release the root question');
    // The old "another CLI session in the same directory is refused" case is gone: since T-127 the user's own sessions
    // share the sessions directory and the collector reads only this launch's dated day directories (README "用户的
    // Codex home"), so a file written here never reaches it. test_t127_codex_home_e2e.py covers other sessions.
    assert.equal(pane.native, 'root-session'); assert.equal(pane.turn, 'root-turn');
  } else {
    // Fresh native bytes remain unconsumed. Any scan or direct store.event in
    // the actual handler is rejected by exact table/trace values, not a crash.
    const before = saved(), offsets = [...pane.offsets];
    report.observed = await read(); await read();
    assert.deepEqual(saved(), before, 'Sidebar read changed persisted tables or traces');
    assert.deepEqual([...pane.offsets], offsets, 'Sidebar read consumed native bytes');
    report.databases = Object.keys(before.databases); report.trace_files = Object.keys(before.traces);
  }
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
finally {
  if (started) {
    pane.stopped = true; // The seeded PTY has no OS process to terminate.
    try {
      assert.equal((await request(state, { command: 'daemon_stop' }, operator)).ok, true);
      for (let i = 0; fs.existsSync(join(state, 'daemon.pid')) && i < 200; i++) await new Promise(resolve => setTimeout(resolve, 5));
      assert.ok(!fs.existsSync(join(state, 'daemon.pid'))); report.cleanup_complete = true;
    } catch (error) { report.status = 'INCOMPLETE'; report.cleanup_error = String(error); }
  }
  if (previousCredential === undefined) delete process.env.A2A_OPERATOR_CREDENTIAL; else process.env.A2A_OPERATOR_CREDENTIAL = previousCredential;
}
fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
