// Independent cache contract; do not install packages or call a downloader.
// Failures: correct npm cache masks a missing/wrong Electron cache, or the
// documented command never supplies the installer option it actually reads.
import assert from 'node:assert/strict';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import vm from 'node:vm';

const require = createRequire(import.meta.url);
const root = fileURLToPath(new URL('..', import.meta.url));
const output = resolve(process.argv[2]); mkdirSync(output);
const npmCache = '/Volumes/WD-Elements/a2a-t075-npm-cache';
const electronCache = '/Volumes/WD-Elements/a2a-electron-cache';
const checks = [];
const baseEnv = { ...process.env, npm_config_cache: npmCache };
delete baseEnv.electron_config_cache;
for (const [name, value, expectedExit] of [['missing', undefined, 1], ['internal', '/tmp/forbidden-electron-cache', 1], ['external', electronCache, 0]]) {
  const env = { ...baseEnv, ...(value === undefined ? {} : { electron_config_cache: value }) };
  const argv = [process.execPath, join(root, 'check-cache.mjs')];
  const result = spawnSync(argv[0], argv.slice(1), { cwd: root, env });
  writeFileSync(join(output, name + '.stdout.bin'), result.stdout, { flag: 'wx' });
  writeFileSync(join(output, name + '.stderr.bin'), result.stderr, { flag: 'wx' });
  checks.push({ name, argv, electron_config_cache: value ?? null, exit: result.status, expectedExit,
    status: result.status === expectedExit ? 'PASS' : 'INCOMPLETE' });
}
const lock = JSON.parse(readFileSync(join(root, 'package-lock.json'), 'utf8'));
const electronRoot = dirname(require.resolve('electron/package.json'));
const getRoot = join(root, 'node_modules/@electron/get');
const installed = JSON.parse(readFileSync(join(electronRoot, 'package.json'), 'utf8'));
assert.equal(installed.version, lock.packages['node_modules/electron'].version);
assert.equal(JSON.parse(readFileSync(join(getRoot, 'package.json'), 'utf8')).version, lock.packages['node_modules/@electron/get'].version);
const { Cache } = await import(join(getRoot, 'dist/Cache.js'));
const documented = readFileSync(join(root, 'README.md'), 'utf8').split('\n').find((line) => line.includes('npm ci --cache '));
assert.ok(documented, 'The README must contain the supported installation command');
const assignment = documented.split(' ').find((word) => word.startsWith('electron_config_cache='));
const env = { ...baseEnv, ...(assignment ? { electron_config_cache: assignment.slice('electron_config_cache='.length) } : {}) };
let captured;
const inert = { then() { return this; }, catch() { return this; } };
const localRequire = (id) => {
  if (id === '@electron/get') return { downloadArtifact(options) { captured = options; return inert; } };
  if (id === 'fs') return { readFileSync() { throw Object.assign(new Error('fixture: fresh install'), { code: 'ENOENT' }); }, existsSync() { return false; } };
  if (id === './package') return installed;
  if (id === './checksums.json') return {};
  if (id === '@electron-internal/extract-zip') throw new Error('Extraction is forbidden in this probe');
  return require(id);
};
vm.runInNewContext(readFileSync(join(electronRoot, 'install.js'), 'utf8'), {
  require: localRequire, __dirname: electronRoot, console,
  process: { env, platform: 'darwin', arch: 'arm64', exit() { throw new Error('Unexpected installer exit'); } },
});
const resolvedCache = new Cache(captured.cacheRoot).cacheRoot;
checks.push({ name: 'documented-installer-cache', command: documented, electron: installed.version,
  electron_get: lock.packages['node_modules/@electron/get'].version,
  installer_cacheRoot: captured.cacheRoot ?? null, resolved_cache_root: resolvedCache,
  expected: electronCache, status: captured.cacheRoot === electronCache && resolvedCache === electronCache ? 'PASS' : 'INCOMPLETE' });
const result = { status: checks.every((check) => check.status === 'PASS') ? 'PASS' : 'INCOMPLETE',
  network_calls: 0, package_installs: 0, cache_writes: 0, checks };
writeFileSync(join(output, 'results.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(result));
process.exitCode = result.status === 'PASS' ? 0 : 1;
