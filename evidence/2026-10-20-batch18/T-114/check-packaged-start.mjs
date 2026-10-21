// Run the packaged desktop with fresh local data. Never launch an agent CLI.
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, openSync, closeSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { execFileSync, spawn } from 'node:child_process';

const app = resolve(process.argv[2]), output = resolve(process.argv[3]);
assert(app.startsWith('/private/tmp/') && app.endsWith('/Enchanted.app'));
assert(output.startsWith('/private/tmp/') && !existsSync(output));
const fixture = mkdtempSync('/private/tmp/t114-start-');
const state = join(fixture, 'state'), ui = join(fixture, 'ui');
const executableName = execFileSync('/usr/libexec/PlistBuddy', ['-c', 'Print :CFBundleExecutable', join(app, 'Contents/Info.plist')], { encoding: 'utf8' }).trim();
assert(/^[A-Za-z0-9_-]+$/.test(executableName));
const executable = join(app, 'Contents/MacOS', executableName);
const resources = join(app, 'Contents/Resources/app');
const env = Object.fromEntries(Object.entries(process.env).filter(([key]) =>
  !key.startsWith('A2A_') && !key.startsWith('GIT_CONFIG_') && !key.startsWith('ELECTRON_') &&
  !['NODE_OPTIONS', 'NODE_PATH'].includes(key)));
const report = { status: 'INCOMPLETE', app, fixture, model_calls: 0, processes: [], cleanup_complete: false };
const log = output + '.stderr.log';
const stdout = openSync(output + '.stdout.log', 'wx', 0o600), stderr = openSync(log, 'wx', 0o600);
let child, ws, daemon, helpers = [], next = 0;
const pending = new Map();
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const active = () => Number.isSafeInteger(child?.pid) && child.exitCode === null && child.signalCode === null;
function processes() {
  return execFileSync('/bin/ps', ['-axo', 'pid=,ppid=,pgid=,command='], { encoding: 'utf8' }).trim().split('\n').map(line => {
    const row = line.trim().match(/^(\d+)\s+(\d+)\s+(\d+)\s+(.*)$/);
    assert(row, line);
    return { pid: Number(row[1]), ppid: Number(row[2]), pgid: Number(row[3]), command: row[4] };
  });
}
async function until(read, description, requireMain = true) {
  const end = Date.now() + 30_000;
  while (Date.now() < end) {
    if (requireMain) assert(active(), `Desktop exited before ${description}: ${readFileSync(log, 'utf8')}`);
    const value = await read(); if (value) return value;
    await sleep(100);
  }
  throw new Error('Deadline: ' + description);
}
function call(command) {
  const { credential } = JSON.parse(readFileSync(join(state, 'desktop-connection.json'), 'utf8'));
  assert(credential.startsWith(state + '/desktop-operator-'));
  const response = JSON.parse(execFileSync(executable, [join(resources, 'src/gates/cli.ts'), '--state', state, command], {
    env: { ...env, ELECTRON_RUN_AS_NODE: '1', A2A_OPERATOR_CREDENTIAL: credential }, encoding: 'utf8', timeout: 10_000,
  }));
  assert(response.ok, JSON.stringify(response));
  return response;
}
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++next;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP deadline: ' + method)); }, 10_000);
    pending.set(id, { resolve, reject, timer });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
try {
  report.argv = [executable, '--state', state, '--user-data', ui, '--remote-debugging-port=0'];
  child = spawn(executable, report.argv.slice(1), { env, detached: true, stdio: ['ignore', stdout, stderr] });
  const spawned = new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
  closeSync(stdout); closeSync(stderr);
  await spawned;
  report.main_pid = child.pid;
  const port = await until(() => /DevTools listening on ws:\/\/127\.0\.0\.1:(\d+)\//.exec(readFileSync(log, 'utf8'))?.[1], 'DevTools endpoint');
  const target = await until(async () => {
    const response = await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(3000) });
    return (await response.json()).find(target => target.type === 'page' && target.url.startsWith('file://' + resources + '/'));
  }, 'packaged renderer');
  ws = new WebSocket(target.webSocketDebuggerUrl);
  ws.addEventListener('message', event => {
    const message = JSON.parse(event.data), entry = pending.get(message.id);
    if (!entry) return;
    clearTimeout(entry.timer); pending.delete(message.id);
    message.error ? entry.reject(new Error(JSON.stringify(message.error))) : entry.resolve(message.result);
  });
  await new Promise((resolve, reject) => { ws.addEventListener('open', resolve, { once: true }); ws.addEventListener('error', reject, { once: true }); });
  await until(async () => {
    const value = await send('Runtime.evaluate', { expression: `document.readyState === 'complete' && document.title === 'Enchanted' && document.querySelector('.brand')?.textContent.includes('Enchanted') && typeof window.a2a?.sidebar === 'function'`, returnByValue: true });
    assert(!value.exceptionDetails, JSON.stringify(value));
    return value.result.value === true;
  }, 'Enchanted UI');
  await until(() => existsSync(join(state, 'desktop-connection.json')), 'desktop connection');
  daemon = call('daemon_status').pid;
  assert(Number.isSafeInteger(daemon) && daemon > 1 && daemon !== child.pid);
  const rows = await until(() => {
    const rows = processes();
    const owned = new Set([child.pid]);
    for (let changed = true; changed;) {
      changed = false;
      for (const row of rows) if (owned.has(row.ppid) && !owned.has(row.pid)) { owned.add(row.pid); changed = true; }
    }
    helpers = rows.filter(row => owned.has(row.pid) && row.command.startsWith(app + '/Contents/Frameworks/Enchanted Helper'));
    return helpers.some(row => row.command.includes('--type=renderer')) && rows;
  }, 'live Enchanted renderer helper');
  const main = rows.find(row => row.pid === child.pid), background = rows.find(row => row.pid === daemon);
  assert(main?.command.startsWith(executable + ' ') && main.pgid === child.pid);
  assert(background?.command.startsWith(executable + ' ' + join(resources, 'src/daemon.ts') + ' ' + state + ' '));
  assert.equal(background.pgid, daemon, 'daemon needs its own process group');
  report.processes = [main, ...helpers, background];
  report.renderer_ready = true;
  await send('Page.close');
  await until(() => !active(), 'desktop exit', false);
  assert.equal(child.exitCode, 0, 'desktop exit code');
  report.startup_passed = true;
} catch (error) {
  report.error = String(error);
} finally {
  // Only stop this spawned desktop. The gate stops only this fresh state daemon.
  ws?.close();
  for (const entry of pending.values()) clearTimeout(entry.timer);
  if (active()) child.kill('SIGTERM');
  try {
    await until(() => !active(), 'desktop stopped', false);
    if (existsSync(join(state, 'desktop-connection.json'))) {
      const current = call('daemon_status').pid;
      if (daemon !== undefined) assert.equal(current, daemon, 'daemon identity changed');
      daemon = current;
      const row = processes().find(row => row.pid === daemon);
      assert(row?.command.startsWith(executable + ' ' + join(resources, 'src/daemon.ts') + ' ' + state + ' '));
      call('daemon_stop');
    }
    await until(() => {
      const rows = processes();
      return !existsSync(join(state, 'control.sock')) && !existsSync(join(state, 'daemon.pid')) &&
        !rows.some(row => row.pid === child?.pid || row.pid === daemon || helpers.some(helper => helper.pid === row.pid) ||
          (row.command.startsWith(app + '/Contents/') && row.pgid === child?.pid));
    }, 'main/helper/daemon cleanup', false);
    rmSync(fixture, { recursive: true });
    report.cleanup_complete = true;
  } catch (error) {
    report.cleanup_error = String(error); // Preserve the isolated state if cleanup cannot be confirmed.
  }
  report.status = report.startup_passed && report.cleanup_complete ? 'PASS' : 'NO_GO';
  writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify(report, null, 2));
}
process.exit(report.status === 'PASS' ? 0 : 1);
