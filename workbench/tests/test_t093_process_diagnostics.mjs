// Actual Panes.processInfo and daemon request handler, real SQLite; supplied
// helper/connection/clock boundaries. No daemon, socket, CLI, auth or PID query.
// Failure list: empty/truncated output loses stderr; exit/signal/spawn metadata
// lost; Refusal reclassified; reply/event diverge; retry or release on failure.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { EventEmitter } from 'node:events';
import { readFileSync, writeFileSync, existsSync, mkdtempSync } from 'node:fs';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';

const output = process.argv[2];
assert(output && !existsSync(output), 'A new output path is required');
const panesURL = new URL('../src/panes.ts', import.meta.url);
const daemonURL = new URL('../src/daemon.ts', import.meta.url);
const panesSource = readFileSync(process.argv[3] ?? panesURL, 'utf8');
const daemonSource = readFileSync(process.argv[4] ?? daemonURL, 'utf8');
const nonce = randomUUID();
const root = mkdtempSync('/private/tmp/t093-helper-diagnostic-');
const healthy = JSON.stringify({ schema: 1, root_pid: 42001, method: 'macOS libproc', rows: [
  { pid: 42001, ppid: 1, pgid: 42001, tpgid: 42002, command: '/bin/zsh' },
  { pid: 42002, ppid: 42001, pgid: 42002, tpgid: 42002, command: '/fixture/claude-' + nonce },
] });
const cases = [
  { name: 'empty', stdout: '', stderr: 'empty-output-' + nonce, exit_code: 0, signal: null, killed: false },
  { name: 'truncated', stdout: '{"schema":1,', stderr: 'partial-output-' + nonce, exit_code: 0, signal: null, killed: false },
  { name: 'empty-after-kill', stdout: '', stderr: '', exit_code: 0, signal: null, killed: true },
  { name: 'query-error', stdout: '', stderr: '{"error":"process_query_failed","operation":"proc_pidinfo_failed_or_short","errno":1}', exit_code: 2, signal: null, killed: false, reject: true },
  { name: 'signal', stdout: '{', stderr: 'signal-output-' + nonce, exit_code: null, signal: 'SIGKILL', killed: false, reject: true },
  { name: 'timeout', stdout: '{"schema":', stderr: 'timeout-output-' + nonce, exit_code: null, signal: 'SIGTERM', killed: true, reject: true },
  { name: 'spawn', stdout: '', stderr: '', exit_code: null, signal: null, killed: false, reject: true, error_code: 'EPERM' },
  { name: 'schema', stdout: '[]', stderr: '', exit_code: 0, signal: null, killed: false, refusal: 'invalid_process_snapshot' },
  { name: 'row', stdout: JSON.stringify({ schema: 1, root_pid: 42001, method: 'macOS libproc', rows: [{ pid: 42001 }] }), stderr: '', exit_code: 0, signal: null, killed: false, refusal: 'invalid_process_row' },
  { name: 'healthy', stdout: healthy, stderr: '', exit_code: 0, signal: null, killed: false },
];
const checks = [];
for (const input of cases) {
  const directory = join(root, input.name), operator = { token: 'public-fixture-' + nonce, epoch: 1, state: directory };
  let captured, accept, calls = 0, writes = 0, clock = 1000;
  const elapsed = input.name === 'timeout' ? 5321.875 : 15.625 + cases.indexOf(input) * 7.125;
  const context = vm.createContext({ console, Buffer, URL, TextDecoder, setTimeout, clearTimeout,
    process: { pid: 41000, ppid: 1, argv: ['supplied-daemon'], version: process.version, env: {},
      kill() { throw new Error('Real process operations are forbidden'); } } });
  async function load(text, url, overrides) {
    const module = new vm.SourceTextModule(stripTypeScriptTypes(text), { context,
      initializeImportMeta(meta) { meta.url = url.href; } });
    await module.link(async specifier => {
      const values = overrides[specifier] ?? await import(specifier.startsWith('node:') ? specifier : new URL(specifier, url));
      return new vm.SyntheticModule(Object.keys(values), function() {
        for (const [key, value] of Object.entries(values)) this.setExport(key, value);
      }, { context });
    });
    await module.evaluate();
    return module.namespace;
  }
  const execFile = () => { throw new Error('Only the supplied promisified helper is allowed'); };
  execFile[Symbol.for('nodejs.util.promisify.custom')] = (executable, argv, options) => {
    calls++;
    assert.equal(executable, '/usr/bin/python3');
    assert.deepEqual([...argv.slice(0, 3)], ['-I', '-S', '-B']);
    assert(argv[3].endsWith('/processSnapshot.py'));
    assert.equal(argv[4], '42001');
    assert.equal(options.timeout, 5000);
    const error = Object.assign(new Error('supplied helper ' + input.name), {
      code: input.error_code ?? input.exit_code, signal: input.signal, killed: input.killed,
      stdout: input.stdout, stderr: input.stderr,
    });
    const operation = input.reject ? Promise.reject(error) : Promise.resolve({ stdout: input.stdout, stderr: input.stderr });
    operation.child = { pid: input.name === 'spawn' ? undefined : 43001, exitCode: input.exit_code,
      signalCode: input.signal, killed: input.killed };
    return operation;
  };
  const { Panes } = await load(panesSource, panesURL, {
    'node:child_process': { execFile },
    'node:perf_hooks': { performance: { now() { const value = clock; clock += elapsed; return value; } } },
  });
  class FixturePanes extends Panes {
    constructor(...args) {
      super(...args); captured = this;
      this.panes.set('fixture-thread', { record: { id: 'fixture-launch-' + nonce, task: 'fixture-task', attempt: null,
        role: 'controller', cli: 'Claude Code', executable_path: '/fixture/claude-' + nonce, session: 'fixture-session' },
        pty: { pid: 42001, write() { writes++; } }, state: 'unknown', failed: null, native: 'fixture-session', nativeEnded: false,
        stopped: false, archived: false, leader: null, active: null, queue: [], writing: false, userDraft: false });
    }
  }
  const fs = await import('node:fs');
  const { serve } = await load(daemonSource, daemonURL, {
    'node:net': { createServer(handler) { accept = handler; return Object.assign(new EventEmitter(), {
      listen(_path, done) { done(); }, close(done) { done(); },
    }); } },
    'node:fs': { ...fs, chmodSync(path, mode) { assert.equal(path, join(directory, 'control.sock')); assert.equal(mode, 0o600); } },
    './panes.ts': { Panes: FixturePanes, spawnHelper: () => '/fixture/inert-pty-helper' },
    './credentials.ts': { readOperatorCredential: () => operator, createOperatorCredential() { throw new Error('No credential creation'); } },
  });
  try {
    await serve(directory, {}, () => ({ setUserInputObserverStatus() {}, recoverReviews() {} }));
    async function request(command) {
      return await new Promise(resolve => {
        const connection = Object.assign(new EventEmitter(), { setEncoding() {}, end(raw) { resolve(JSON.parse(raw)); } });
        accept(connection);
        connection.emit('data', JSON.stringify({ id: randomUUID(), identity: { kind: 'operator', ...operator },
          input: { command, thread: 'fixture-thread', reason: 'supplied helper failure' } }) + '\n');
      });
    }
    const replies = [];
    for (const command of input.name === 'healthy' ? ['pane_process_info'] : ['pane_process_info', 'pane_release']) {
      const before = calls, reply = await request(command); replies.push(reply);
      assert.equal(calls - before, 1, 'Each request must query once without retry');
      assert.equal(writes, 0, 'Observer failure must never write terminal input');
      assert.equal(captured.get('fixture-thread').state, 'unknown', 'Observer failure must not release the pane');
      if (input.name === 'healthy') {
        assert.equal(reply.ok, true); assert.equal(reply.leader, 42002); assert.equal(reply.diagnostics, undefined);
        continue;
      }
      assert.equal(reply.ok, false, 'Helper failure must keep the existing refusal');
      assert.equal(reply.error, input.refusal ?? 'orchestration_failed', 'Original failure code must remain unchanged');
      if (['empty', 'truncated', 'empty-after-kill'].includes(input.name)) assert(reply.details.startsWith('SyntaxError:'), 'Original parse failure must survive');
      const diagnostic = reply.diagnostics?.process_query;
      assert(diagnostic, 'Helper failure diagnostics must reach the daemon response');
      assert.equal(diagnostic.stdout, input.stdout, 'Captured stdout must retain the supplied nonce');
      assert.equal(diagnostic.stderr, input.stderr, 'Captured stderr must retain the supplied nonce');
      assert.equal(diagnostic.exit_code, input.exit_code);
      assert.equal(diagnostic.signal, input.signal);
      assert.equal(diagnostic.killed, input.killed);
      assert.equal(diagnostic.helper_pid, input.name === 'spawn' ? null : 43001);
      assert.equal(diagnostic.root_pid, 42001);
      assert.equal(diagnostic.elapsed_ms, elapsed, 'Elapsed time must use the supplied monotonic clock');
      assert.equal(diagnostic.error_code, input.error_code ?? null);
      const event = captured.store.read().filter(row => row.type === 'request_rejected').at(-1);
      assert.deepEqual(event.data.result, reply, 'Persisted diagnostic must equal the refusal sent to the client');
    }
    checks.push({ case: input.name, status: 'PASS', helper_calls: calls, writes, replies });
  } catch (error) {
    checks.push({ case: input.name, status: 'FAIL', helper_calls: calls, writes, failure: String(error) });
  } finally { captured?.store.close(); }
}
const status = checks.every(row => row.status === 'PASS') ? 'PASS' : 'FAIL';
writeFileSync(output, JSON.stringify({ status, scope: 'actual daemon handler and Panes; supplied external execution/connection/clock; no real services or process query',
  nonce, root, checks, model_turns: 0 }, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ status, cases: checks.length, failed: checks.filter(row => row.status === 'FAIL').map(row => ({ case: row.case, failure: row.failure })) }));
process.exitCode = status === 'PASS' ? 0 : 2;
