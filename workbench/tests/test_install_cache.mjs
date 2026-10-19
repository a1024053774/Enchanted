// Resolve actual npm and Electron defaults without installing or downloading.
import assert from 'node:assert/strict';
import { homedir } from 'node:os';
import { isAbsolute, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { Cache } from '../node_modules/@electron/get/dist/Cache.js';

const root = process.argv[2] ? resolve(process.argv[2]) : fileURLToPath(new URL('..', import.meta.url));
const env = { ...process.env };
delete env.npm_config_cache;
const npm = spawnSync('npm', ['config', 'get', 'cache', '--logs-max=0'], { cwd: root, env, encoding: 'utf8' });
assert.equal(npm.status, 0, npm.stderr);
const caches = [npm.stdout.trim(), new Cache().cacheRoot];
for (const cache of caches) {
  assert.ok(isAbsolute(cache));
  const path = relative(homedir(), cache);
  assert.ok(path && path !== '..' && !path.startsWith('../') && !isAbsolute(path), 'Default cache must be in the local user directory: ' + cache);
}
console.log('PASS: npm and Electron resolve local default caches');
