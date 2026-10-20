// Actual main command queue + actual transport; supplied Unix socket boundary.
// Failures: pre-connect gaps, unknown-outcome replay, reused request IDs,
// swallowed refusals, broken release concurrency, or a release/input ordering gap.
// This is a boundary contract, not evidence of real Electron/CLI recovery.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { EventEmitter } from 'node:events';
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';

const output = process.argv[2];
if (!output) throw new Error('Fresh report path required');
const report = { status: 'INCOMPLETE', scope: 'actual main queue and transport; supplied socket boundary', checks: [] };
const transport = readFileSync(new URL('../src/transport.ts', import.meta.url), 'utf8');
const candidate = readFileSync(new URL('../app/main.ts', import.meta.url), 'utf8');
const baseline = '4a6d6bb9ecefc2bb16196b326ff032726d4d16fb';

async function exercise(source) {
  const plans = [], sent = [], sockets = [], pending = [];
  let admitted = 0;
  class Socket extends EventEmitter {
    setEncoding() {}
    setTimeout(_milliseconds, callback) { this.deadline = callback; }
    end() { this.emit('close'); }
    destroy(error) { this.emit('error', error); this.emit('close'); }
    write(line) {
      const command = JSON.parse(line); sent.push(command);
      assert.equal(command.identity.window, 'original-window');
      const respond = value => this.emit('data', JSON.stringify(value) + '\n');
      if (command.input.sequence !== admitted + 1) {
        queueMicrotask(() => respond({ ok: false, error: 'invalid_window_sequence' })); return;
      }
      admitted = command.input.sequence;
      if (this.plan === 'unknown') queueMicrotask(() => this.destroy(new Error('daemon disconnected; outcome unknown')));
      else if (this.plan === 'refused') queueMicrotask(() => respond({ ok: false, error: 'stale_attempt' }));
      else if (this.plan === 'pending-release') pending.push(() => respond({ ok: true, written: true }));
      else queueMicrotask(() => respond({ ok: true, written: true }));
    }
  }
  const context = vm.createContext({ Buffer, process, console });
  const module = new vm.SourceTextModule(stripTypeScriptTypes(transport, { mode: 'strip' }), { context });
  await module.link(async specifier => {
    const exports = specifier === 'node:net' ? { createConnection: path => {
      assert.equal(path, '/fixture/state/control.sock');
      const socket = new Socket(); socket.plan = plans.shift(); sockets.push(socket);
      queueMicrotask(() => socket.plan === 'offline'
        ? socket.destroy(Object.assign(new Error('connect ENOENT'), { code: 'ENOENT' })) : socket.emit('connect'));
      return socket;
    } } : await import(specifier.startsWith('./') ? new URL(specifier, new URL('../src/transport.ts', import.meta.url)) : specifier);
    return new vm.SyntheticModule(Object.keys(exports), function() {
      for (const [key, value] of Object.entries(exports)) this.setExport(key, value);
    }, { context });
  });
  await module.evaluate();
  const start = source.indexOf('function sendWindowCommand('), end = source.indexOf('\nfunction registerHandlers()', start);
  assert.ok(start >= 0 && end > start);
  context.request = module.namespace.request; context.randomUUID = randomUUID;
  const send = vm.runInContext(stripTypeScriptTypes(source.slice(start, end) + '\nsendWindowCommand;', { mode: 'strip' }), context);
  const pane = { identity: { kind: 'window', window: 'original-window', token: 'fixture' }, sequence: 0,
    inputQueue: Promise.resolve(), pendingRelease: null };
  const window = { options: { state: '/fixture/state' }, closing: false };
  plans.push('offline', 'offline');
  const failures = await Promise.allSettled([
    send(window, pane, { command: 'window_resize', cols: 100, rows: 40 }),
    send(window, pane, { command: 'window_observation', type: 'focus-mode-intercept', raw_sequence: 'fixture' }),
  ]);
  assert.ok(failures.every(row => row.status === 'rejected' && row.reason.code === 'ENOENT'));
  assert.equal(sent.length, 0, 'Disconnected commands must not be sent');
  assert.equal(pane.sequence, 0, 'An unconnected command must not consume a window sequence');
  const answer = await send(window, pane, { command: 'window_answer', question: 'same-question', answers: ['west'] });
  assert.equal(answer.ok, true); assert.equal(sent[0].input.sequence, 1);
  assert.equal(sent[0].input.question, 'same-question');
  plans.push('unknown');
  await assert.rejects(() => send(window, pane, { command: 'window_input', data: 'once' }), /outcome unknown/);
  assert.equal(pane.sequence, 2, 'A sent command with unknown outcome keeps its consumed sequence');
  assert.equal(sent.filter(row => row.input.data === 'once').length, 1, 'Unknown input must never be replayed');
  plans.push('refused');
  await assert.rejects(() => send(window, pane, { command: 'window_answer', question: 'stale' }), /stale_attempt/);
  assert.equal(pane.sequence, 3, 'A daemon refusal also consumes the admitted sequence');
  plans.push('pending-release');
  const release = send(window, pane, { command: 'window_release', declaration: { statement: 'fixture' } });
  while (!pending.length) await new Promise(resolve => setImmediate(resolve));
  assert.throws(() => send(window, pane, { command: 'window_release' }), /already pending/);
  await send(window, pane, { command: 'window_input', data: 'invalidates pending declaration' });
  assert.equal(pane.pendingRelease, release, 'Input must remain able to invalidate a pending release');
  pending.shift()(); await release;
  plans.push('offline');
  await assert.rejects(() => send(window, pane, { command: 'window_release' }), /ENOENT/);
  assert.equal(pane.sequence, 5);
  await send(window, pane, { command: 'window_input', data: 'next' });
  assert.deepEqual(sent.map(row => row.input.sequence), [1, 2, 3, 4, 5, 6]);
  assert.equal(new Set(sent.map(row => row.input.request_id)).size, sent.length);
  assert.equal(sockets.length, sent.length + 3, 'No automatic reconnection or replay');
  window.closing = true;
  assert.throws(() => send(window, pane, { command: 'window_input' }), /not available/);
  return ['preconnect_failures_do_not_consume_sequence', 'same_question_original_window_answer_admitted',
    'unknown_sent_outcome_consumes_sequence_and_never_replays', 'daemon_refusal_preserved',
    'pending_release_allows_later_input_and_rejects_duplicate_release', 'request_ids_unique_no_retries'];
}
try {
  try { await exercise(execFileSync('git', ['show', baseline + ':workbench/app/main.ts'], { encoding: 'utf8' })); }
  catch (error) { report.known_bad = { revision: baseline,
    rejected: error instanceof assert.AssertionError && error.message.startsWith('An unconnected command must not consume a window sequence'), error: String(error) }; }
  assert.equal(report.known_bad?.rejected, true, 'The previous candidate must fail the disconnected sequence contract');
  report.checks = await exercise(candidate); report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify(report) + '\n');
process.exitCode = report.status === 'PASS' ? 0 : 1;
