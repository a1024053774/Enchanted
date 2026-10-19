#!/bin/bash
set -euo pipefail
target=${1:?传入已 npm ci 的 workbench 绝对路径}
output=${2:?传入尚不存在的外置盘记录目录}
node --input-type=module - "$target" "$output" <<'JS'
import { accessSync, closeSync, constants, existsSync, lstatSync, mkdirSync, openSync, readFileSync, realpathSync, statSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';

const volume = '/Volumes/WD-Elements';
if (!lstatSync(volume).isDirectory() || realpathSync(volume) !== volume ||
    statSync(volume).dev === statSync(dirname(volume)).dev) throw new Error('外置盘未真实挂载；不回退内置盘');
if (!isAbsolute(process.argv[2]) || !isAbsolute(process.argv[3])) throw new Error('安装目标与记录目录必须是绝对路径');
const target = realpathSync(process.argv[2]);
const output = resolve(process.argv[3]);
const inside = (root, path) => { const child = relative(root, path); return child !== '..' && !child.startsWith('../') && !isAbsolute(child); };
if (!inside(volume, output) || output === volume) throw new Error('记录目录必须在外置盘内');
mkdirSync(dirname(output), { recursive: true });
if (!inside(volume, realpathSync(dirname(output)))) throw new Error('记录目录不能通过链接落到其他磁盘');
mkdirSync(output); // 已有记录不覆盖。
const cache = join(volume, 'a2a-electron-cache');
const temporary = join(output, 'tmp');
const result = { status: 'INCOMPLETE', target, output, electron_config_cache: cache,
  temporary, node: process.version, reason: '执行主控 #9：显式安装锁定版本的 Electron 二进制',
  method: '执行已安装 electron 包的 install.js（install-electron 对应入口），不调用 npx 或改 npm 配置' };
const json = path => JSON.parse(readFileSync(path, 'utf8'));
const kib = path => {
  const readback = spawnSync('du', ['-sk', path], { encoding: 'utf8' });
  if (readback.status !== 0) throw new Error('无法核对依赖磁盘占用：' + readback.stderr);
  return Number(readback.stdout.trim().split(/\s+/)[0]);
};
try {
  if (process.platform !== 'darwin') throw new Error('本次验证只支持 macOS');
  const projectFile = join(target, 'package.json'), lockFile = join(target, 'package-lock.json');
  const projectBytes = readFileSync(projectFile), lockBytes = readFileSync(lockFile);
  const expected = JSON.parse(projectBytes).dependencies.electron;
  if (!/^\d+\.\d+\.\d+$/.test(expected)) throw new Error('Electron 必须是 package.json 中锁定的确切版本');
  const directory = realpathSync(join(target, 'node_modules/electron'));
  if (inside('/Volumes', directory) || statSync(directory).dev === statSync(volume).dev) {
    throw new Error('执行主控 #13：Electron 只能在内置盘准备并执行；外置盘依赖应指定同版本内置盘 dist');
  }
  const installed = json(join(directory, 'package.json'));
  if (installed.version !== expected || JSON.parse(lockBytes).packages['node_modules/electron'].version !== expected) {
    throw new Error('package.json、锁文件与已安装 Electron 版本不一致');
  }
  const pathFile = join(directory, 'path.txt'), dist = join(directory, 'dist');
  Object.assign(result, { expected_version: expected, installed_version: installed.version,
    package_scripts: installed.scripts ?? null,
    before: { path_txt: existsSync(pathFile), dist: existsSync(dist), node_modules_KiB: kib(join(target, 'node_modules')) },
    argv: [process.execPath, join(directory, 'install.js')] });
  mkdirSync(cache, { recursive: true });
  if (realpathSync(cache) !== cache) throw new Error('Electron 缓存目录不能是链接');
  mkdirSync(temporary);
  const env = { ...process.env, electron_config_cache: cache,
    TMPDIR: temporary, TMP: temporary, TEMP: temporary,
    ELECTRON_INSTALL_PLATFORM: process.platform, ELECTRON_INSTALL_ARCH: process.arch };
  delete env.ELECTRON_OVERRIDE_DIST_PATH;
  delete env.ELECTRON_RUN_AS_NODE;
  delete env.NODE_OPTIONS;
  delete env.force_no_cache;
  const stdout = openSync(join(output, 'install.stdout.log'), 'wx', 0o600);
  const stderr = openSync(join(output, 'install.stderr.log'), 'wx', 0o600);
  let install;
  try { install = spawnSync(result.argv[0], result.argv.slice(1), { cwd: target, env,
    stdio: ['ignore', stdout, stderr], timeout: 300_000 }); }
  finally { closeSync(stdout); closeSync(stderr); }
  result.install_exit = install.status;
  if (install.error || install.status !== 0) throw install.error ?? new Error('Electron install.js 失败，查看本目录原始日志');
  const executableRelative = readFileSync(pathFile, 'utf8').trim();
  if (executableRelative !== 'Electron.app/Contents/MacOS/Electron') throw new Error('path.txt 不是预期的 macOS Electron 路径');
  const executable = realpathSync(join(dist, executableRelative));
  if (!inside(directory, executable) || !statSync(executable).isFile()) throw new Error('Electron 二进制不在安装目录内');
  accessSync(executable, constants.X_OK);
  const distVersion = readFileSync(join(dist, 'version'), 'utf8').trim().replace(/^v/, '');
  if (distVersion !== expected) throw new Error('dist/version 与项目版本不一致');
  const probeArgv = [executable, '-p', 'process.versions.electron'];
  const probe = spawnSync(probeArgv[0], probeArgv.slice(1), {
    cwd: target, env: { ...env, ELECTRON_RUN_AS_NODE: '1' }, encoding: 'utf8', timeout: 30_000 });
  result.binary_probe = { argv: probeArgv, ELECTRON_RUN_AS_NODE: '1', exit: probe.status,
    stdout: probe.stdout, stderr: probe.stderr };
  if (probe.error || probe.status !== 0 || probe.stdout.trim() !== expected) throw new Error('实际 Electron 二进制版本探针未通过');
  if (!readFileSync(projectFile).equals(projectBytes) || !readFileSync(lockFile).equals(lockBytes)) throw new Error('安装改变了项目依赖文件');
  const afterKiB = kib(join(target, 'node_modules'));
  Object.assign(result, { status: 'PASS', executable, dist_version: distVersion,
    after: { path_txt: true, executable: true, executable_mode: (statSync(executable).mode & 0o777).toString(8), node_modules_KiB: afterKiB },
    node_modules_growth_KiB: afterKiB - result.before.node_modules_KiB,
    dependency_files_unchanged: true });
} catch (error) {
  result.error = String(error);
  process.exitCode = 1;
}
writeFileSync(join(output, 'result.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify(result) + '\n');
JS
