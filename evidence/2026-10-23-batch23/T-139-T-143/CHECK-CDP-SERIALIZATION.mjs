// Isolated CDP serialization check. It does not measure Electron performance.
import { Session } from 'node:inspector/promises';
import { readFileSync, writeFileSync } from 'node:fs';
import assert from 'node:assert/strict';
const summary = process.argv[2];
const source = readFileSync('workbench/tests/test_t139_t143_views_perf_e2e.py', 'utf8');
const fixed = source.match(/electron\.evaluate\(f'(void \(window\.__initialShellTerminal = \{mount\}\.__testTerminal\))'\)/)?.[1];
assert(fixed, 'The actual e2e capture expression must discard the terminal return value');
const session = new Session();
session.connect();
const run = expression => session.post('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
const report = { status: 'INCOMPLETE', boundary: 'Node V8 inspector Runtime.evaluate; not Electron', checks: [] };
try {
  await run('globalThis.window = {}; globalThis.__probeMount = {__testTerminal: {}}; __probeMount.__testTerminal.self = __probeMount.__testTerminal; void 0');
  let oldError;
  try { await run(fixed.replace('void (', '').slice(0, -1).replace('{mount}', '__probeMount')); }
  catch (error) { oldError = String(error); }
  assert.match(oldError ?? '', /Object reference chain is too long/);
  report.checks.push({ name: 'old_capture_rejects_cyclic_object', passed: true, error: oldError });
  const result = await run(fixed.replace('{mount}', '__probeMount'));
  assert.equal(result.result.type, 'undefined');
  assert.equal((await run('window.__initialShellTerminal === __probeMount.__testTerminal')).result.value, true);
  report.checks.push({ name: 'fixed_capture_retains_reference_without_returning_object', passed: true, remoteType: result.result.type });
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.status = 'NO_GO'; process.exitCode = 1; }
finally { session.disconnect(); writeFileSync(summary, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' }); }
