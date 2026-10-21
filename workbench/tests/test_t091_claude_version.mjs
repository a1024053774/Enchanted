// Actual builder and managed startup method, with IO boundaries supplied.
// Failures: configured CLI rejected, absent executable hidden, an updated CLI
// refused (T-118: native CLIs update themselves, the version is only recorded),
// repeated/missing probes, observed version lost, updater disabled.
// No native CLI, daemon, PTY, Electron or model is started.
// Run: node --experimental-vm-modules workbench/tests/test_t091_claude_version.mjs <new report path>
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { stripTypeScriptTypes } from 'node:module';
import * as path from 'node:path';
import * as url from 'node:url';
import * as executionSettings from '../src/executionSettings.ts';

const sourceURL = new URL('../src/claudeLaunch.ts', import.meta.url);
const panesURL = new URL('../src/panes.ts', import.meta.url);
// Parent of T-118, which still refused any version other than the configured one.
const revision = process.env.T118_KNOWN_BAD ?? '3070bbe1a01c449c922d6d1c778594f7d7889827';
const report = { status: 'INCOMPLETE', scope: 'Actual builder and managed startup method with supplied IO; no real CLI or startup proof', argv: process.argv };
async function load(source, paneSource) {
  const probes = [];
  let output = '2.1.302 (Claude Code)\n', failure;
  class Refusal extends Error { constructor(code, details) { super(code); this.code = code; this.details = details; } }
  const context = vm.createContext({ URL, TextDecoder, process: { execPath: '/fixture/node', version: 'v26.5.0' } });
  const module = new vm.SourceTextModule(stripTypeScriptTypes(source, { mode: 'strip' }), {
    context, initializeImportMeta(meta) { meta.url = sourceURL.href; },
  });
  await module.link(specifier => {
    const exports = specifier === 'node:fs' ? { realpathSync: value => value, readFileSync: () => Buffer.from('fixture role') }
      : specifier === 'node:path' ? path : specifier === 'node:url' ? url
      : specifier === './gates/core.ts' ? { Refusal }
      : specifier === './executionSettings.ts' ? executionSettings
      : specifier === 'node:util' ? { promisify: fn => fn }
      : specifier === 'node:child_process' ? { execFile: async (...args) => {
        probes.push(args); if (failure) throw Object.assign(new Error('fixture exec failure'), { code: failure });
        return { stdout: output, stderr: '' };
      } } : null;
    if (!exports) throw new Error('Unexpected module boundary: ' + specifier);
    return new vm.SyntheticModule(Object.keys(exports), function() {
      for (const [key, value] of Object.entries(exports)) this.setExport(key, value);
    }, { context });
  });
  await module.evaluate();
  const code = stripTypeScriptTypes(paneSource, { mode: 'strip' });
  const start = code.search(/\n  (?:async )?startController\(/);
  const end = code.indexOf('\n  // T-078-1/#49', start);
  assert.ok(start >= 0 && end > start);
  const Fixture = new Function('factoryExecution', 'claudeLaunch', 'check', 'exec', 'Refusal', 'randomUUID', 'mkdirSync', 'dirname', 'join', 'appendFileSync', 'require', 'realpathSync',
    'return class Fixture { root = "/private/tmp/t078-2-version-sentinel/state"; panes = new Map(); store = {launch() {}, event() {}, executionSelection: (role, value) => ({ ...this.factory[role], ...value })}; factory = factoryExecution;' + code.slice(start, end) + '}')(
      executionSettings.factoryExecution, module.namespace.claudeLaunch, (value, code) => { if (!value) throw new Refusal(code); },
      async (...args) => { probes.push(args); if (failure) throw Object.assign(new Error('fixture exec failure'), { code: failure }); return { stdout: output, stderr: '' }; },
      Refusal, () => 'fixture-token', () => {}, path.dirname, path.join, () => {},
      () => ({ spawn: () => ({ pid: 91, onData() {}, onExit() {} }) }), value => value);
  const root = '/private/tmp/t078-2-version-sentinel';
  const task = { task_id: 'task-sentinel', project_id: 'project-sentinel', repo: root + '/repo', spec_rev: 4 };
  const input = { schema: 1, root, state: root + '/state', task: task.task_id, preset: 'ideation',
    launch: '00000000-0091-4000-8000-000000000001', session: '00000000-0091-4000-8000-000000000002',
    thread: '00000000-0091-4000-8000-000000000003', executable: '/fixture/configured-claude', version: '2.1.302',
    role_file: root + '/roles/ideation/role.md', code_revision: 'a'.repeat(40), source_snapshot: '/fixture/source', api_url: 'http://127.0.0.1:20001/' };
  return { run: () => new Fixture().startController(task, input), probes, input,
    concurrent: () => { const owner = new Fixture(); return Promise.allSettled([owner.startController(task, input), owner.startController(task, input)]); },
    fail: value => { failure = value; }, output: value => { output = value; } };
}
async function exercise(source, panes) {
  const fixture = await load(source, panes);
  const launch = await fixture.run();
  assert.equal(fixture.probes.length, 1, 'Exactly one --version probe per launch');
  const [executable, argv, options] = fixture.probes[0];
  assert.equal(executable, '/fixture/configured-claude');
  assert.deepEqual([...argv], ['--version']);
  assert.equal(options.env.HOME, '/private/tmp/t078-2-version-sentinel/roles/ideation/home');
  assert.equal(launch.cli_version, '2.1.302 (Claude Code)');
  assert.equal(launch.cli_version_expected, '2.1.302 (Claude Code)');
  assert.equal(launch.version_probe.stdout, '2.1.302 (Claude Code)\n');
  assert.equal(launch.env.DISABLE_AUTOUPDATER, undefined);
  fixture.fail('ENOENT');
  await assert.rejects(fixture.run, error => error.code === 'controller_executable_missing');
  fixture.fail('EACCES');
  await assert.rejects(fixture.run, error => error.code === 'controller_version_probe_failed');
  fixture.fail(undefined); fixture.output('2.1.399 (Claude Code)\n');
  const updated = await fixture.run().catch(error => assert.fail('Updated CLI version must be accepted: ' + error.code));
  assert.equal(updated.cli_version, '2.1.399 (Claude Code)', 'The observed, not the configured, version is recorded');
  assert.equal(updated.version_probe.stdout, '2.1.399 (Claude Code)\n');
  fixture.output('2.1.302 (Claude Code)\n');
  const concurrent = await fixture.concurrent();
  assert.equal(concurrent.filter(value => value.status === 'fulfilled').length, 1);
  assert.equal(concurrent.find(value => value.status === 'rejected').reason.code, 'controller_already_started');
  return ['configured_executable_and_single_probe', 'observed_version_persisted', 'missing_executable_code',
    'probe_failure_code', 'updated_version_accepted_and_recorded', 'updater_unchanged', 'concurrent_preset_claim_is_unique'];
}
try {
  try { await exercise(execFileSync('git', ['show', revision + ':workbench/src/claudeLaunch.ts'], { encoding: 'utf8' }),
    execFileSync('git', ['show', revision + ':workbench/src/panes.ts'], { encoding: 'utf8' })); }
  catch (error) { report.known_bad = { revision, rejected: error instanceof assert.AssertionError && error.message.includes('Updated CLI version must be accepted'), error: String(error) }; }
  assert.ok(report.known_bad?.rejected);
  const source = readFileSync(sourceURL, 'utf8');
  const panes = readFileSync(panesURL, 'utf8');
  report.checks = await exercise(source, panes);
  const marker = '      const version = probe.stdout.trim();\n';
  assert.equal(panes.split(marker).length, 2, 'Exactly one place to reintroduce a version comparison');
  try { await exercise(source, panes.replace(marker, marker + '      if (version !== expectedVersion) throw new Refusal("controller_version_mismatch");\n')); }
  catch (error) { report.mutant = { rejected: error instanceof assert.AssertionError && error.message.includes('Updated CLI version must be accepted'), error: String(error) }; }
  assert.ok(report.mutant?.rejected, 'A reintroduced version comparison must fail the update assertion');
  report.status = 'PASS';
} catch (error) { report.error = String(error); }
writeFileSync(process.argv[2], JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
