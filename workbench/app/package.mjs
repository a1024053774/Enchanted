import { accessSync, chmodSync, constants, cpSync, lstatSync, mkdirSync, readFileSync, realpathSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync, spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ options: { slot: { type: 'string' } } });
const volume = resolve(process.env.A2A_BUILD_VOLUME ?? '/Volumes/WD-Elements');
// Refuse before loading dependencies, downloading, or creating output.
if (!lstatSync(volume).isDirectory() || realpathSync(volume) !== volume ||
    statSync(volume).dev === statSync(dirname(volume)).dev) throw new Error('打包要求真实挂载的外置盘；不回退到内置盘。');
if (process.platform !== 'darwin' || process.arch !== 'arm64') throw new Error('本机打包只支持 macOS arm64');
if (!values.slot || !/^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(values.slot)) throw new Error('A new --slot NAME is required');
const base = join(volume, 'a2a-workbench');
mkdirSync(base, { recursive: true });
if (realpathSync(base) !== base) throw new Error('Build base must not contain links');
const slot = join(base, values.slot);
mkdirSync(slot); // Never reuse a candidate or erase a failed build.
const temporary = join(slot, 'tmp');
mkdirSync(temporary);
Object.assign(process.env, { TMPDIR: temporary, TMP: temporary, TEMP: temporary,
  npm_config_cache: join(volume, 'a2a-t075-npm-cache'), electron_config_cache: join(volume, 'a2a-electron-cache') });
const source = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const manifest = JSON.parse(readFileSync(join(source, 'package.json'), 'utf8'));
const build = execFileSync(process.execPath, [join(source, 'app/build.mjs'), '--slot', values.slot + '-ui'], { encoding: 'utf8', env: process.env });
const ui = JSON.parse(build.trim().split('\n').at(-1));
const stage = join(slot, 'app');
mkdirSync(stage);
cpSync(ui.out, join(stage, 'ui'), { recursive: true });
for (const name of ['src', 'hooks', 'bin', 'LICENSE.synara']) cpSync(join(source, name), join(stage, name), { recursive: true });
cpSync(join(source, 'app/desktop.mjs'), join(stage, 'desktop.mjs'));
// Keep the existing dependency tree and let Packager prune declared build/UI
// dependencies. Runtime code and the only gate CLI keep their original paths.
cpSync(join(source, 'node_modules'), join(stage, 'node_modules'), { recursive: true });
const runtime = { effect: manifest.dependencies.effect, 'node-pty': manifest.dependencies['node-pty'] };
writeFileSync(join(stage, 'package.json'), JSON.stringify({ name: 'a2a', version: manifest.version, type: 'module', main: 'desktop.mjs',
  dependencies: runtime, devDependencies: { ...Object.fromEntries(Object.entries(manifest.dependencies).filter(([key]) => !(key in runtime))), ...manifest.devDependencies } }, null, 2) + '\n');
const electron = manifest.dependencies.electron;
// Direct node-gyp is Electron's documented rebuild path. --devdir keeps headers
// external; @electron/rebuild 4.0.1 hardcodes ~/.electron-gyp.
const gyp = createRequire(import.meta.url).resolve('node-gyp/bin/node-gyp.js');
const rebuild = [gyp, 'rebuild', '--target=' + electron, '--arch=arm64', '--dist-url=https://www.electronjs.org/headers',
  '--devdir=' + join(volume, 'a2a-electron-gyp')];
execFileSync(process.execPath, rebuild, { cwd: join(stage, 'node_modules/node-pty'), env: process.env, stdio: 'inherit' });
const native = join(stage, 'node_modules/node-pty/build/Release');
const helper = join(native, 'spawn-helper');
chmodSync(helper, 0o755);
accessSync(helper, constants.X_OK);
const { packager } = await import('@electron/packager');
const paths = await packager({ dir: stage, name: 'a2a', executableName: 'a2a', platform: 'darwin', arch: 'arm64',
  electronVersion: electron, out: join(slot, 'package'), tmpdir: temporary, overwrite: false, asar: false,
  appBundleId: 'org.a2a.workbench', appCategoryType: 'public.app-category.developer-tools',
  download: { cacheRoot: join(volume, 'a2a-electron-cache') },
  osxSign: { identity: '-', identityValidation: false, preAutoEntitlements: false, preEmbedProvisioningProfile: false,
    optionsForFile: () => ({ hardenedRuntime: false, signatureFlags: '0', timestamp: 'none' }) },
});
if (paths.length !== 1) throw new Error('Expected exactly one packaged application');
const app = join(paths[0], 'a2a.app');
execFileSync('/usr/bin/codesign', ['--verify', '--deep', '--strict', app], { stdio: 'inherit' });
const signatures = [];
for (const target of [app, join(app, 'Contents/Frameworks/Electron Framework.framework'),
    join(app, 'Contents/Resources/app/node_modules/node-pty/build/Release/spawn-helper'),
    join(app, 'Contents/Resources/app/node_modules/node-pty/build/Release/pty.node')]) {
  const inspected = spawnSync('/usr/bin/codesign', ['-dv', '--verbose=2', target], { encoding: 'utf8' });
  const flags = inspected.stderr.match(/^CodeDirectory .*flags=(.*)$/m)?.[1];
  if (inspected.status !== 0 || !flags || flags.includes('runtime') || !inspected.stderr.includes('Signature=adhoc')) {
    throw new Error('Expected ad-hoc signature without hardened runtime: ' + target);
  }
  signatures.push({ target, flags, signature: 'adhoc' });
}
const result = { schema: 1, app, electron, arch: 'arm64', signing: 'ad-hoc; no notarization; hardenedRuntime=false',
  slot, source, runtime: 'Electron ELECTRON_RUN_AS_NODE=1', asar: false, signatures, rebuild: [process.execPath, ...rebuild],
  helper: join(app, 'Contents/Resources/app/node_modules/node-pty/build/Release/spawn-helper'),
  sizeKiB: Number(execFileSync('/usr/bin/du', ['-sk', app], { encoding: 'utf8' }).split(/\s/)[0]) };
accessSync(result.helper, constants.X_OK);
writeFileSync(join(slot, 'package.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(result));
