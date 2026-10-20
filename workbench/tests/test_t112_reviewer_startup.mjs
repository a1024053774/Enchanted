// Startup contract only. Real driver source runs with supplied daemon/process/FS
// boundaries; this is not native CLI evidence. A session appears only after the
// first release. Failures: circular wait, no leader, no session, changed leader.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import vm from 'node:vm';
const filename = new URL('./t112_reviewer_record.mjs', import.meta.url);
const source = readFileSync(filename, 'utf8');
const output = process.argv[2];
assert.ok(output);
const report = { status: 'INCOMPLETE', model_calls: 0, scope: 'actual driver with supplied startup boundaries; no native sandbox', cases: [] };
async function scenario(mode) {
  const root = '/private/tmp/T112-startup-sentinel';
  const files = new Map(), calls = [];
  let released = false, ticks = 0;
  const panes = {
    async createReview() { calls.push('create'); },
    get() { return { record: { role: 'reviewer' } }; },
    async processInfo() {
      calls.push(released ? 'identity-after-release' : 'identity-before-release');
      return { leader: mode === 'no-leader' ? null : released && mode === 'changed-leader' ? 43 : 42,
        native_session: released && mode !== 'no-session' ? 'native-sentinel' : null, failed: null };
    },
    async release() { calls.push('release'); released = true; },
  };
  const modules = {
    'daemon.ts': { serve: async (path, config, factory) => { factory(path, panes); } },
    'core.ts': { A2AGates: class {} },
    'store.ts': { OrchestrationStore: class { saveExecutionSettings() {} close() {} } },
    'credentials.ts': { createOperatorCredential() {} },
    'transport.ts': { request: async () => ({ recovering: false }) },
  };
  const context = vm.createContext({ URL, process: { argv: ['node', 'driver', '/fixture-manifest'], env: {} },
    Date: { now: () => (ticks += 10000) }, setTimeout: callback => queueMicrotask(callback) });
  async function synthetic(exports) {
    const module = new vm.SyntheticModule(Object.keys(exports), function () { for (const [key, value] of Object.entries(exports)) this.setExport(key, value); }, { context });
    await module.link(() => {}); await module.evaluate(); return module;
  }
  const driver = new vm.SourceTextModule(source, { context, identifier: filename.href,
    importModuleDynamically: async specifier => {
      const key = new URL(specifier).pathname.split('/').at(-1);
      assert.ok(modules[key], 'Unexpected dynamic dependency: ' + key);
      return synthetic(modules[key]);
    } });
  await driver.link(async specifier => {
    if (specifier === 'node:fs') return synthetic({
      mkdirSync() {}, existsSync: () => false, readdirSync: () => [], statSync: () => ({}),
      readFileSync: () => JSON.stringify({ source: '/fixture-source', root, binary: '/fixture-codex', revision: 'fixture-rev' }),
      writeFileSync: (path, bytes) => files.set(path, JSON.parse(bytes)),
    });
    return synthetic(await import(specifier));
  });
  await driver.evaluate();
  return { mode, calls, files: Object.fromEntries(files), root };
}
try {
  const success = await scenario('session-after-release');
  report.cases.push(success);
  assert.ok(!success.files[success.root + '/host-error.json'], 'Startup must release before requiring a session: ' + JSON.stringify(success.calls));
  assert.equal(success.files[success.root + '/identity.json'].native_session, 'native-sentinel');
  assert.equal(success.calls.filter(call => call === 'release').length, 1);
  assert.ok(success.calls.indexOf('identity-before-release') < success.calls.indexOf('release'));
  assert.ok(success.calls.indexOf('release') < success.calls.indexOf('identity-after-release'));
  for (const mode of ['no-leader', 'no-session', 'changed-leader']) {
    const result = await scenario(mode); report.cases.push(result);
    assert.ok(result.files[result.root + '/host-error.json'], mode + ' must fail');
    assert.ok(!result.files[result.root + '/identity.json'], mode + ' cannot publish native identity');
    if (mode === 'no-leader') assert.ok(!result.calls.includes('release'));
  }
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ status: report.status, error: report.error }));
process.exitCode = report.status === 'PASS' ? 0 : 1;
