// Execute actual transport with supplied filesystem/process/socket boundaries.
// Failure list: dead endpoint blocks restart; live/unknown owner erased; another
// epoch's PID erased after an await; non-socket erased; credentials created early.
// No real process, socket, daemon, ps, PTY or model.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { EventEmitter } from 'node:events';
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import assert from 'node:assert/strict';

async function run(source, scenario) {
  const root = '/fixture/state', pid = root + '/daemon.pid', socket = root + '/control.sock';
  const files = new Map(scenario === 'clean' ? [] : [[socket, 'socket'], ...(scenario === 'unknown' ? [] : [[pid, '1234\n']])]);
  const removed = []; let spawned = 0, credentials = 0;
  const context = vm.createContext({ Buffer, URL, setTimeout, clearTimeout, process: { execPath: '/fixture/node', versions: {}, env: {}, kill() {
    if (scenario === 'alive') return;
    throw Object.assign(new Error('fixture process absent'), { code: 'ESRCH' });
  } } });
  const module = new vm.SourceTextModule(stripTypeScriptTypes(source), { context, initializeImportMeta(meta) {
    meta.url = new URL('../src/transport.ts', import.meta.url).href;
  } });
  await module.link(async specifier => {
    let values;
    if (specifier === 'node:fs') values = { existsSync: path => files.has(path), mkdirSync() {}, realpathSync: path => path,
      lstatSync: () => ({ isSocket: () => scenario !== 'not-socket' }), readFileSync: path => files.get(path),
      unlinkSync(path) { assert.ok(files.has(path)); removed.push(path); files.delete(path); }, openSync: () => 3, closeSync() {} };
    else if (specifier === 'node:net') values = { createConnection() {
      const connection = Object.assign(new EventEmitter(), { destroy() {}, setTimeout() {} });
      queueMicrotask(() => {
        if (scenario === 'changed') files.set(pid, '5678\n');
        if (scenario === 'live-socket') connection.emit('connect');
        else connection.emit('error', Object.assign(new Error('fixture refused'), { code: 'ECONNREFUSED' }));
      }); return connection;
    } };
    else if (specifier === 'node:child_process') values = { spawn() {
      spawned++; const child = Object.assign(new EventEmitter(), { disconnect() {}, unref() {} });
      queueMicrotask(() => child.emit('message', { ok: true, pid: 9876 })); return child;
    } };
    else if (specifier === './credentials.ts') values = { createOperatorCredential() { credentials++; return '/fixture/new-operator.json'; } };
    else values = await import(specifier);
    return new vm.SyntheticModule(Object.keys(values), function() { for (const [key, value] of Object.entries(values)) this.setExport(key, value); }, { context });
  });
  await module.evaluate();
  let reply, error;
  try { reply = await module.namespace.startDaemon(root, {}); } catch (caught) { error = caught; }
  if (['clean', 'dead'].includes(scenario)) {
    assert.equal(error, undefined, 'A verified dead epoch must permit a fresh daemon');
    assert.equal(reply.ok, true); assert.equal(spawned, 1); assert.equal(credentials, 1);
    assert.deepEqual(removed, scenario === 'dead' ? [socket, pid] : []);
  } else {
    assert.ok(error, 'Unverified or live endpoint must reject restart');
    assert.equal(spawned, 0); assert.equal(credentials, 0); assert.deepEqual(removed, []);
    assert.equal(files.get(pid), scenario === 'unknown' ? undefined : scenario === 'changed' ? '5678\n' : '1234\n');
    assert.equal(files.get(socket), 'socket');
  }
}
const report = { status: 'INCOMPLETE', scope: 'actual transport with supplied boundaries only; no real daemon/socket proof', checks: [] };
try {
  const revision = '3c9016d02';
  try { await run(execFileSync('git', ['show', revision + ':workbench/src/transport.ts'], { encoding: 'utf8' }), 'dead'); }
  catch (error) { report.known_bad = { revision, rejected: error instanceof assert.AssertionError && error.message.startsWith('A verified dead epoch must permit'), error: String(error) }; }
  assert.equal(report.known_bad?.rejected, true);
  const source = readFileSync(new URL('../src/transport.ts', import.meta.url), 'utf8');
  for (const scenario of ['clean', 'dead', 'alive', 'unknown', 'changed', 'live-socket', 'not-socket']) {
    await run(source, scenario); report.checks.push(scenario);
  }
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(process.argv[2], JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
