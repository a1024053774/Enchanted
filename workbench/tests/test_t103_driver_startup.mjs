// Driver lifecycle check only. A host cannot release app.ready until entry
// evaluation finishes; a product window cannot exist before app.ready.
// Exercise the actual driver with that dependency still pending. No GUI,
// daemon, PTY, network, process signal, or product acceptance is simulated here.
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { readFileSync, writeFileSync } from 'node:fs';
import * as path from 'node:path';
import * as url from 'node:url';
import { parseArgs } from 'node:util';

const [output, badPath] = process.argv.slice(2);
if (!output || !badPath) throw new Error('New report path and preserved faulty driver path are required');
async function inspect(source) {
  const state = { evaluated: false, calls: [], stages: [], replies: [], error: null };
  const app = Object.assign(new EventEmitter(), { isReady: () => false, exit(code) { state.error = 'unexpected exit ' + code; } });
  const argv = ['Electron', '/fixture/driver.mjs', '--build', '/fixture/build', '--state', '/fixture/state',
    '--task', 'sentinel-task', '--user-data', '/fixture/ui', '--output', '/fixture/output'];
  const context = vm.createContext({ console, process: { argv, pid: 1, versions: { electron: '43.4.1' },
    stdout: { write(text, callback) { state.replies.push(JSON.parse(text)); callback(); } } } });
  const product = new vm.SyntheticModule(['run'], function () {
    this.setExport('run', options => {
      state.calls.push(options);
      return new Promise(() => {}); // app.ready is deliberately not available during module evaluation.
    });
  }, { context });
  await product.link(() => { throw new Error('Unexpected product import'); });
  await product.evaluate();
  const module = new vm.SourceTextModule(source, { context,
    importModuleDynamically: async () => product });
  await module.link(specifier => {
    const exports = specifier === 'electron' ? { app }
      : specifier === 'node:fs' ? {
        readFileSync: () => '{"main":"/fixture/product.mjs"}', writeFileSync() {},
        appendFileSync: (_file, line) => state.stages.push(JSON.parse(line)) }
      : specifier === 'node:path' ? path : specifier === 'node:url' ? url
      : specifier === 'node:readline' ? { createInterface: () => new EventEmitter() }
      : specifier === 'node:util' ? { parseArgs } : null;
    if (!exports) throw new Error('Unexpected driver boundary: ' + specifier);
    return new vm.SyntheticModule(Object.keys(exports), function () {
      for (const [key, value] of Object.entries(exports)) this.setExport(key, value);
    }, { context });
  });
  void module.evaluate().then(() => { state.evaluated = true; }, error => { state.error = String(error); });
  // Drain bounded event-loop turns, without starting or releasing app.ready.
  for (let index = 0; index < 8; index++) await new Promise(setImmediate);
  return state;
}
const report = { status: 'INCOMPLETE', scope: 'Actual driver module with pending window boundary; no Electron runtime evidence', argv: process.argv };
try {
  report.known_bad = await inspect(readFileSync(badPath, 'utf8'));
  assert.equal(report.known_bad.error, null);
  assert.equal(report.known_bad.calls.length, 1, 'Counterexample must reach the product window request');
  assert.equal(report.known_bad.evaluated, false, 'Faulty driver must block entry evaluation on the pending window');
  report.candidate = await inspect(readFileSync(new URL('./t103_picker_driver.mjs', import.meta.url), 'utf8'));
  assert.equal(report.candidate.error, null);
  assert.equal(report.candidate.calls.length, 1);
  assert.equal(report.candidate.calls[0].task, 'sentinel-task');
  assert.equal(report.candidate.evaluated, true, 'Entry must finish before the host can emit app.ready');
  assert.ok(report.candidate.stages.some(item => item.stage === 'driver-registered' && item.app_ready === false));
  assert.ok(!report.candidate.stages.some(item => item.stage === 'product-run-completed'));
  assert.equal(report.candidate.replies.length, 0, 'No ready handshake may precede the real window');
  report.status = 'PASS';
} catch (error) { report.error = String(error); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
