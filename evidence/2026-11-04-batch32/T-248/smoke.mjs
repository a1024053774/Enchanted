// T-248 packaged-app smoke test. Usage: node smoke.mjs <Enchanted.app> <summary.json>
// Opens the built app through LaunchServices with its own data directory, opens a project through the daemon's
// operator socket, creates a project terminal through the renderer's own bridge (the same IPC the "new terminal"
// button calls), types a command and reads it back. Independent facts: the marker is computed by the shell
// ($((6*7)) → 42, never typed literally), and ps shows which herdr-core binary hosts the terminal.
// The user's own daemon, Herdr and hc are never addressed: every request names this run's state directory.
import assert from 'node:assert/strict';
import { execFileSync, spawn } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { connect } from 'node:net';
import { join, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';

const app = resolve(process.argv[2]), summary = resolve(process.argv[3]);
assert.ok(!existsSync(summary), 'keep earlier evidence: choose a new summary path');
const fixture = realpathSync(mkdtempSync('/private/tmp/a2at248-'));
const state = join(fixture, 'state'), userData = join(fixture, 'ui'), repo = join(fixture, 'repo');
const report = { status: 'INCOMPLETE', argv: process.argv, app, fixture, checks: [] };
const check = (name, ok, detail) => { report.checks.push({ name, ok: Boolean(ok), detail }); assert.ok(ok, `${name}: ${JSON.stringify(detail)}`); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function until(read, what, seconds = 60) {
  const end = Date.now() + seconds * 1000;
  while (Date.now() < end) { const value = await read(); if (value) return value; await sleep(200); }
  throw new Error('timeout: ' + what);
}
const env = Object.fromEntries(Object.entries(process.env).filter(([key]) =>
  !key.startsWith('A2A_') && !key.startsWith('HC_') && !key.startsWith('HERDR') && !['NODE_OPTIONS', 'NODE_PATH', 'ELECTRON_RUN_AS_NODE'].includes(key)));
function request(command, identity) {
  return new Promise((done, fail) => {
    const socket = connect(join(state, 'control.sock'));
    let data = '';
    socket.setTimeout(60_000, () => { socket.destroy(); fail(new Error('daemon request timeout')); });
    socket.on('data', part => { data += part; if (data.includes('\n')) { socket.end(); done(JSON.parse(data.split('\n')[0])); } });
    socket.on('error', fail);
    socket.write(JSON.stringify({ id: randomUUID(), input: command, identity }) + '\n');
  });
}
class CDP {
  constructor(ws) { this.ws = ws; this.next = 0; this.pending = new Map();
    ws.addEventListener('message', event => { const m = JSON.parse(event.data); const p = this.pending.get(m.id); if (!p) return;
      this.pending.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); }); }
  send(method, params = {}) { return new Promise((resolve, reject) => { const id = ++this.next; this.pending.set(id, { resolve, reject });
    this.ws.send(JSON.stringify({ id, method, params })); }); }
  async bridge(name, ...args) {
    const result = await this.send('Runtime.evaluate', { awaitPromise: true, returnByValue: true,
      expression: `window.a2a[${JSON.stringify(name)}](...${JSON.stringify(args)})` });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  }
}
const ps = () => execFileSync('/bin/ps', ['-axww', '-o', 'pid=,command='], { encoding: 'utf8' });
const ours = () => ps().split('\n').filter(line => Number(line.trim().split(/\s+/)[0]) !== process.pid && (line.includes(fixture) || line.includes(app + '/')));
let opener;
try {
  execFileSync('git', ['init', '-q', '-b', 'main', repo]);
  writeFileSync(join(repo, 'README.md'), 'T-248 smoke\n');
  execFileSync('git', ['-C', repo, 'add', 'README.md']);
  execFileSync('git', ['-C', repo, '-c', 'user.name=T248', '-c', 'user.email=t248@example.invalid', 'commit', '-q', '-m', 'readme']);
  const plist = execFileSync('/usr/bin/plutil', ['-extract', 'CFBundleShortVersionString', 'raw', join(app, 'Contents/Info.plist')], { encoding: 'utf8' }).trim();
  check('bundle version', plist === '0.1.6', plist);
  const log = join(fixture, 'gui.stderr.log');
  const argv = ['/usr/bin/open', '-n', '-W', '--stdout', join(fixture, 'gui.stdout.log'), '--stderr', log, app,
    '--args', '--state', state, '--user-data', userData, '--remote-debugging-port=0'];
  report.launch = argv;
  opener = spawn(argv[0], argv.slice(1), { env, detached: true, stdio: 'ignore' });
  opener.unref();
  const port = await until(() => existsSync(log) && /DevTools listening on ws:\/\/127\.0\.0\.1:(\d+)\//.exec(readFileSync(log, 'utf8'))?.[1], 'devtools endpoint');
  const resources = join(app, 'Contents/Resources/app');
  const target = await until(async () => (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json())
    .find(t => t.type === 'page' && t.url.startsWith('file://' + resources)), 'packaged renderer');
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r, f) => { ws.onopen = r; ws.onerror = f; });
  const cdp = new CDP(ws);
  await until(async () => (await cdp.send('Runtime.evaluate', { expression: 'typeof window.a2a', returnByValue: true })).result.value === 'object', 'bridge');
  const descriptor = JSON.parse(readFileSync(join(`${state}-credentials`, 'desktop-connection.json'), 'utf8'));
  const operator = JSON.parse(readFileSync(descriptor.credential, 'utf8'));
  const status = await request({ command: 'daemon_status' }, operator);
  check('daemon from this state', status.ok, status);
  const opened = await request({ command: 'project_open', repo }, operator);
  check('project opened', opened.ok, opened);
  const project = opened.project;
  report.project = project;
  report.select = await cdp.bridge('selectProject', project);
  const view = await cdp.bridge('newTerminal');
  report.view = view;
  const key = view.paneKeys.find(k => view.launches[k]);
  const launch = view.launches[key];
  check('terminal created', Boolean(launch), view);
  // The pane takes input once the renderer has attached it (pane.identity); until then input is refused.
  await until(async () => { try { await cdp.bridge('input', key, 'echo T248-$((6*7))-$PWD\r'); return true; }
    catch (error) { if (/not available for input/.test(String(error))) return false; throw error; } }, 'pane attached', 30);
  const text = await until(async () => {
    // pane_output returns at most 64 KiB from an offset as data_base64; read the whole trace.
    let offset = 0, bytes = [];
    for (;;) {
      const out = await request({ command: 'pane_output', launch, offset, max_bytes: 65536 });
      if (!out.ok) throw new Error(JSON.stringify(out));
      const chunk = Buffer.from(out.data_base64, 'base64'); bytes.push(chunk); offset += chunk.length;
      if (!chunk.length || offset >= out.total_bytes) break;
    }
    const decoded = Buffer.concat(bytes).toString('utf8');
    report.last_output = decoded.slice(-1500); report.marker_lines = decoded.split(/\r?\n/).filter(line => line.includes('T248-')).map(line => line.replace(/\x1b\[[0-9;?]*[A-Za-z]/g, ''));
    return /T248-42-\//.test(decoded) ? decoded : null;
  }, 'shell echoed the computed marker', 30);
  check('shell runs commands', /T248-42-/.test(text) && text.includes(repo), text.slice(-400));
  const cores = ps().split('\n').filter(line => /herdr-core/.test(line) && (line.includes(app + '/') || line.includes(fixture)));
  check('terminal hosted by bundled hc', cores.some(line => line.includes(join(resources, 'hc/herdr-core'))), cores);
  report.status = 'PASS';
} catch (error) {
  report.error = String(error?.stack ?? error);
} finally {
  // Stop this run only: the daemon of this state directory, then its private core, then the GUI.
  try {
    const descriptor = JSON.parse(readFileSync(join(`${state}-credentials`, 'desktop-connection.json'), 'utf8'));
    report.daemon_stop = await request({ command: 'daemon_stop' }, JSON.parse(readFileSync(descriptor.credential, 'utf8')));
  } catch (error) { report.daemon_stop = String(error); }
  try {
    const identity = JSON.parse(readFileSync(join(state, 'hc-runtime.json'), 'utf8'));
    assert.ok(identity.session.startsWith('enchanted-'));
    report.core_stop = execFileSync(join(app, 'Contents/Resources/app/hc/herdr-core'), ['server', 'stop'], { encoding: 'utf8', timeout: 20_000,
      env: { ...env, HC_SESSION: identity.session, HC_SOCKET: identity.socket, XDG_STATE_HOME: join(state, 'hc/state'), XDG_CONFIG_HOME: join(state, 'hc/config') } });
  } catch (error) { report.core_stop = String(error); }
  for (const line of ps().split('\n').filter(l => l.includes(app + '/Contents/MacOS/Enchanted') && l.includes(state))) {
    try { process.kill(Number(line.trim().split(/\s+/)[0]), 'SIGTERM'); } catch {}
  }
  await sleep(3000);
  report.left = ours();
  if (report.left.length) report.status = 'INCOMPLETE';
  writeFileSync(summary, JSON.stringify(report, null, 1) + '\n', { flag: 'wx' });
  if (!report.left.length) rmSync(fixture, { recursive: true, force: true });
  console.log(JSON.stringify({ status: report.status, checks: report.checks.map(c => `${c.ok ? 'ok' : 'FAIL'} ${c.name}`), error: report.error, left: report.left }));
  process.exit(report.status === 'PASS' ? 0 : 1);
}
