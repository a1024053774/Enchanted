// Execute the real launcher with process/file/spawn boundaries supplied.
// Failure: repeated public --launch options are lost before Electron sees them.
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { parseArgs } from 'node:util';
import * as path from 'node:path';

const launches = ['launch-worker-sentinel', 'launch-ideation-sentinel', 'launch-executor-sentinel'];
async function exercise(source) {
  let spawned;
  const argv = ['node', '/source/start.mjs', '--build', '/fixture/dist', '--task', 'sentinel-task',
    ...launches.flatMap(launch => ['--launch', launch]), '--state', '/fixture/state', '--user-data', '/fixture/ui'];
  const context = vm.createContext({ process: { argv, env: { ELECTRON_RUN_AS_NODE: '1', SENTINEL: 'kept' } }, console });
  const module = new vm.SourceTextModule(source, { context, initializeImportMeta(meta) { meta.url = 'file:///source/start.mjs'; } });
  await module.link(specifier => {
    const values = specifier === 'node:child_process' ? { spawn(executable, args, options) {
      spawned = { executable, args, options }; return new EventEmitter();
    } } : specifier === 'node:fs' ? { readFileSync: () => '{"main":"/fixture/dist/main.js"}' }
      : specifier === 'node:module' ? { createRequire: () => () => '/owned/Electron' }
      : specifier === 'node:path' ? path
      : specifier === 'node:util' ? { parseArgs: options => parseArgs({ ...options, args: argv.slice(2) }) } : null;
    if (!values) throw new Error('Unexpected launcher boundary: ' + specifier);
    return new vm.SyntheticModule(Object.keys(values), function() {
      for (const [key, value] of Object.entries(values)) this.setExport(key, value);
    }, { context });
  });
  await module.evaluate();
  const passed = spawned.args.flatMap((value, index, all) => value === '--launch' ? [all[index + 1]] : []);
  assert.deepEqual([...passed], launches, 'Launcher must forward all three explicit launches');
  assert.equal(spawned.options.env.ELECTRON_RUN_AS_NODE, undefined);
  assert.equal(spawned.options.env.SENTINEL, 'kept');
  assert.equal(spawned.executable, '/owned/Electron');
}
const report = { status: 'INCOMPLETE', argv: process.argv,
  scope: 'Actual start.mjs with supplied spawn/filesystem, no Electron or backend start', checks: [] };
try {
  const revision = '44bbb7828459d81fab0d46069a19d3dd515a7732';
  try { await exercise(execFileSync('git', ['show', revision + ':workbench/app/start.mjs'], { encoding: 'utf8' })); }
  catch (error) {
    report.known_bad = { revision, rejected: error instanceof assert.AssertionError && error.message.startsWith('Launcher must forward all three explicit launches'), error: String(error) };
  }
  assert.ok(report.known_bad?.rejected);
  await exercise(readFileSync(new URL('../app/start.mjs', import.meta.url), 'utf8'));
  report.status = 'PASS'; report.checks = ['all_three_launches_forwarded', 'electron_executable_and_environment'];
} catch (error) { report.error = String(error); }
writeFileSync(process.argv[2], JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
