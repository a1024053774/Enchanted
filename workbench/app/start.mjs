import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ options: Object.fromEntries(
  ['build', 'state', 'task', 'launch', 'user-data'].map((key) => [key, { type: 'string', ...(key === 'launch' ? { multiple: true } : {}) }])) });
if (!values.build) throw new Error('--build DIST is required');
if (values.launch && !values.task) throw new Error('--launch requires --task');
const build = JSON.parse(readFileSync(join(resolve(values.build), 'build.json'), 'utf8'));
const executable = createRequire(import.meta.url)('electron');
const argv = [build.main];
for (const key of ['state', 'task', 'launch', 'user-data']) {
  for (const value of [].concat(values[key] ?? [])) argv.push('--' + key, value);
}
const env = { ...process.env };
delete env.ELECTRON_RUN_AS_NODE;
const child = spawn(executable, argv, { stdio: 'inherit', env });
child.on('error', (error) => { console.error(error); process.exitCode = 1; });
child.on('exit', (code) => { process.exitCode = code ?? 1; });
