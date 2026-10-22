// Test-only CDP driver for T-126 on packaged test builds. It plays the user in the real app: opens a project
// terminal by clicking, types into it through xterm, approves the role request by clicking 批准, closes and reopens
// the UI. The driver reaches the daemon only as the desktop app's operator (project_open, status reads, final stop).
// Usage: node t126drive.mjs <parent .app> <new .app> <out dir> <port>
// Phases on one isolated data directory (explicit --state, so the credential belongs in <state>-credentials):
//   1 parent app: its terminal environment exports the data directory (the red for the same check as phase 3).
//   2 new app while the parent's daemon still runs: the credential migrates and the UI reconnects without a restart.
//   3 new app with its own daemon: terminal environment, a2a whoami / request, approval in the UI, the terminal's
//     attempts on its socket; then the UI closes and reopens and reconnects with the persisted credential.
// The raw terminal environment holds the user's own variables, so it stays in the fixture; only verdicts and A2A_*
// key names enter the report.
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, openSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';

const [parentApp, newApp, out, port] = process.argv.slice(2);
mkdirSync(out); // A new run directory every time.
const F = mkdtempSync('/private/tmp/t126-ui-'), state = join(F, 'state'), credentials = state + '-credentials';
const repo = join(F, 'repos/demo'), scratch = join(F, 'scratch');
mkdirSync(repo, { recursive: true }); mkdirSync(scratch);
const git = (...args) => execFileSync('git', ['-C', repo, '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false',
  '-c', 'user.name=T126 fixture', '-c', 'user.email=fixture@example.invalid', ...args]);
execFileSync('git', ['init', '-q', '-b', 'main', repo]); writeFileSync(join(repo, 'README.md'), 'demo\n'); git('add', 'README.md'); git('commit', '-q', '-m', 'init');
const report = { status: 'INCOMPLETE', argv: process.argv, fixture: F, checks: [], phases: {} };
const check = (name, ok, detail) => { if (!ok) throw new Error(`${name}: ${JSON.stringify(detail)}`); report.checks.push(name); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (read, label, ms = 30000) => { const end = Date.now() + ms; while (Date.now() < end) { try { const v = await read(); if (v) return v; } catch {} await sleep(150); } throw new Error('timeout: ' + label); };
const mode = path => statSync(path).mode & 0o777;
const alive = pid => { try { process.kill(pid, 0); return true; } catch { return false; } };
const resources = app => join(app, 'Contents/Resources/app');
const binary = app => join(app, 'Contents/MacOS/Enchanted Test');

let ws, id = 0, epoch = 0; const waiting = new Map();
const send = (method, params = {}) => new Promise((resolve, reject) => { const n = ++id;
  const timer = setTimeout(() => { waiting.delete(n); reject(new Error('CDP timeout: ' + method)); }, 8000);
  waiting.set(n, m => { clearTimeout(timer); m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result); }); ws.send(JSON.stringify({ id: n, method, params })); });
const evaluate = async expression => { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value; };
const shot = async name => { const r = await send('Page.captureScreenshot', { format: 'png' }); writeFileSync(join(out, `${name}.png`), Buffer.from(r.data, 'base64')); };

async function launch(app, registered = true) {
  const log = openSync(join(out, `app-${++epoch}.log`), 'w');
  const argv = [binary(app), '--state', state, '--user-data', join(state, 'ui'), `--remote-debugging-port=${port}`];
  (report.launches ??= []).push(argv);
  const child = spawn(argv[0], argv.slice(1), { detached: true, stdio: ['ignore', log, log], env: Object.fromEntries(Object.entries(process.env).filter(([k]) => !k.startsWith('A2A_') && k !== 'ELECTRON_RUN_AS_NODE')) });
  child.unref();
  current = child;
  const page = await until(async () => (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page'), 'page target', 60000);
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); } };
  await until(() => evaluate(`document.readyState==='complete' && !!window.a2a`), 'page ready', 60000);
  if (registered) await until(() => evaluate(`document.querySelectorAll('[data-project-id="demo"]').length===1`), 'project listed in the UI', 60000);
  return child;
}
async function closeUI(child) {
  ws.close(); process.kill(child.pid, 'SIGTERM');
  await until(() => !alive(child.pid), 'UI process exit', 20000);
  await until(async () => { try { await fetch(`http://127.0.0.1:${port}/json/list`); return false; } catch { return true; } }, 'debug port closed', 20000);
}
// The operator as the desktop app holds it, through the app's own transport.
async function operatorOf(app, descriptor) {
  process.env.A2A_OPERATOR_CREDENTIAL = JSON.parse(readFileSync(descriptor, 'utf8')).credential;
  const { request } = await import(join(resources(app), 'src/transport.ts') + `?${app === parentApp ? 'p' : 'n'}`);
  const { readOperatorCredential } = await import(join(resources(app), 'src/credentials.ts') + `?${app === parentApp ? 'p' : 'n'}`);
  const operator = readOperatorCredential(state);
  return (input) => request(state, input, operator);
}
let terminal = null;
async function openTerminal() {
  await evaluate(`document.querySelector('[data-project-id="demo"]').click()`);
  await until(() => evaluate(`document.querySelector('h1')?.textContent==='demo' && !!document.querySelector('.task-header .primary-button')`), 'project view');
  await sleep(800);
  await evaluate(`document.querySelector('.task-header .primary-button').click()`);
  await until(() => evaluate(`document.querySelectorAll('section.pane[data-input-enabled="true"]').length===1`), 'terminal writable');
  // An ended terminal of an earlier daemon stays listed read-only; the new one is the writable pane.
  terminal = await evaluate(`document.querySelector('section.pane[data-input-enabled="true"]').dataset.launchId`);
  await until(() => evaluate(`(document.querySelector('section.pane[data-launch-id="${terminal}"] .xterm-rows')?.innerText??'').trim().length>0`), 'shell prompt');
  await sleep(2500);
}
// Type one line into the terminal the way the user pastes it, then press Enter; wait for its marker file.
async function typeLine(line, marker, ms = 30000) {
  const text = `${line}; print -r -- $? > ${join(scratch, marker)}`;
  await evaluate(`(()=>{const t=document.querySelector('section.pane[data-launch-id="${terminal}"] .xterm-helper-textarea');t.focus();const d=new DataTransfer();d.setData('text/plain',${JSON.stringify(text)});t.dispatchEvent(new ClipboardEvent('paste',{clipboardData:d,bubbles:true}))})()`);
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r' });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  return Number((await until(() => existsSync(join(scratch, marker)) && readFileSync(join(scratch, marker), 'utf8').trim(), 'terminal line ' + marker, ms)));
}
const json = name => JSON.parse(readFileSync(join(scratch, name), 'utf8'));
// The same environment check for both builds: no data directory, no credential path.
function environment(name) {
  const variables = Object.fromEntries(readFileSync(join(scratch, name), 'utf8').split('\n').filter(l => l.includes('=')).map(l => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]));
  const secrets = [state, credentials, ...(existsSync(credentials) ? readdirSync(credentials).map(f => join(credentials, f)) : [])];
  const leaking = Object.keys(variables).filter(k => secrets.some(s => variables[k].includes(s))).sort();
  return { variables, verdict: { a2a_keys: Object.keys(variables).filter(k => k.startsWith('A2A_')).sort(), leaking, has_state: 'A2A_STATE' in variables } };
}
const ATTACK = `import { connect } from "node:net";
const [roleRequest] = process.argv.slice(2);
const { A2A_TERMINAL_SOCKET: path, A2A_TERMINAL: launch, A2A_TERMINAL_TOKEN: token } = process.env;
const send = (identity) => new Promise((resolve, reject) => { const c = connect(path); let b = "";
  c.on("error", reject).on("data", (p) => { b += p; if (b.includes("\\n")) { c.end(); resolve(JSON.parse(b.split("\\n")[0])); } });
  c.write(JSON.stringify({ id: crypto.randomUUID(), identity, input: { command: "role_request_decide", role_request: roleRequest, approved: true } }) + "\\n"); });
const out = {};
for (const [name, identity] of Object.entries({ none: null, own_terminal: { kind: "terminal", launch, token }, forged_operator: { kind: "operator", token }, forged_window: { kind: "window", launch, token } }))
  out[name] = (await send(identity)).error ?? "accepted";
process.stdout.write(JSON.stringify(out) + "\\n");
`;

let child, current;
try {
  // Phase 1: the parent build.
  child = await launch(parentApp, false);
  const oldDescriptor = join(state, 'desktop-connection.json');
  check('parent_keeps_credential_in_data_directory', existsSync(oldDescriptor) && JSON.parse(readFileSync(oldDescriptor, 'utf8')).credential.startsWith(state + '/'));
  let call = await operatorOf(parentApp, oldDescriptor);
  const oldToken = JSON.parse(readFileSync(JSON.parse(readFileSync(oldDescriptor, 'utf8')).credential, 'utf8')).token;
  const parentDaemon = (await call({ command: 'daemon_status' })).pid;
  // What the 打开项目目录 dialog sends after the user picks a folder.
  check('project_opened', (await call({ command: 'project_open', repo })).ok);
  await until(() => evaluate(`document.querySelectorAll('[data-project-id="demo"]').length===1`), 'project listed in the UI', 60000);
  await openTerminal();
  await typeLine(`env > ${join(scratch, 'env-parent.txt')}`, 'm-env-parent');
  const parentEnv = environment('env-parent.txt').verdict;
  report.phases.parent = { daemon: parentDaemon, env: parentEnv, old_files: readdirSync(state).filter(f => f.startsWith('desktop-')).length };
  check('parent_terminal_env_exposes_data_directory', parentEnv.has_state && parentEnv.leaking.length > 0, parentEnv);
  await shot('01-parent-terminal');
  await closeUI(child);
  check('parent_daemon_survives_ui_close', alive(parentDaemon));

  // Phase 2: the new build migrates while the parent's daemon runs.
  child = await launch(newApp);
  const descriptor = join(credentials, 'desktop-connection.json');
  const moved = JSON.parse(readFileSync(descriptor, 'utf8')).credential;
  report.phases.migration = { data_directory_desktop_files: readdirSync(state).filter(f => f.startsWith('desktop-')), credential_dir_files: readdirSync(credentials).length };
  check('old_credential_files_removed', report.phases.migration.data_directory_desktop_files.length === 0, report.phases.migration);
  check('migrated_credential_private', moved.startsWith(credentials + '/') && mode(moved) === 0o600 && mode(descriptor) === 0o600 && mode(credentials) === 0o700,
    { moved, modes: [mode(moved), mode(descriptor), mode(credentials)] });
  check('migrated_credential_is_the_running_one', JSON.parse(readFileSync(moved, 'utf8')).token === oldToken);
  call = await operatorOf(newApp, descriptor);
  check('new_ui_reconnects_to_running_daemon', (await call({ command: 'daemon_status' })).pid === parentDaemon);
  await shot('02-migrated-reconnected');
  await closeUI(child);
  check('stop_parent_daemon', (await call({ command: 'daemon_stop' })).ok);
  await until(() => !existsSync(join(state, 'control.sock')) && !alive(parentDaemon), 'parent daemon stopped');

  // Phase 3: the new build with its own daemon.
  child = await launch(newApp);
  const credential = JSON.parse(readFileSync(descriptor, 'utf8')).credential;
  call = await operatorOf(newApp, descriptor);
  const daemon = (await call({ command: 'daemon_status' })).pid;
  check('new_daemon_started_with_credential_outside_data_directory', daemon !== parentDaemon && credential.startsWith(credentials + '/') && mode(credential) === 0o600);
  await openTerminal();
  await typeLine(`env > ${join(scratch, 'env-new.txt')}`, 'm-env-new');
  const { variables, verdict } = environment('env-new.txt');
  report.phases.new = { daemon, env: verdict, terminal };
  check('terminal_env_has_no_data_directory_or_credential', !verdict.has_state && verdict.leaking.length === 0, verdict);
  const terminalSocket = variables.A2A_TERMINAL_SOCKET;
  check('terminal_socket_outside_data_directory', terminalSocket && !terminalSocket.startsWith(state) && statSync(terminalSocket).isSocket(), terminalSocket);
  check('whoami_in_terminal', await typeLine(`a2a whoami > ${join(scratch, 'whoami-0.json')}`, 'm-who0') === 0 && json('whoami-0.json').project === 'demo' && json('whoami-0.json').role === null, json('whoami-0.json'));
  await typeLine(`(a2a request executor > ${join(scratch, 'request.json')} 2>/dev/null; print $? > ${join(scratch, 'request.exit')}) &!`, 'm-request-sent');
  await until(() => evaluate(`!!document.querySelector('.role-request')`), 'role request shown in the UI');
  const [pending] = (await call({ command: 'sidebar_snapshot' })).role_requests;
  writeFileSync(join(scratch, 'attack.mjs'), ATTACK);
  await typeLine(`ELECTRON_RUN_AS_NODE=1 "$A2A_NODE" ${join(scratch, 'attack.mjs')} ${pending.id} > ${join(scratch, 'attack.json')}`, 'm-attack');
  const attack = json('attack.json');
  report.phases.new.attack = attack;
  check('terminal_cannot_decide_with_what_it_sees', Object.values(attack).every(e => e !== 'accepted') &&
    ['none', 'forged_operator', 'forged_window'].every(k => attack[k] === 'terminal_socket_terminal_only'), attack);
  const refused = (await call({ command: 'orchestration_events' })).events.filter(e => e.type === 'request_rejected' && e.data.input?.command === 'role_request_decide');
  report.phases.new.recorded = refused.map(e => [e.data.socket ?? null, e.data.result.error]);
  check('terminal_attempts_recorded', refused.length === 4 && refused.every(e => e.data.socket === 'terminal'), report.phases.new.recorded);
  await shot('03-role-request-pending');
  for (let i = 0; i < 50 && await evaluate(`[...document.querySelectorAll('.role-request button')].find(b=>b.textContent.trim()==='批准')?.disabled !== false`); i++) await sleep(100);
  await evaluate(`[...document.querySelectorAll('.role-request button')].find(b=>b.textContent.trim()==='批准').click()`);
  await until(() => existsSync(join(scratch, 'request.exit')), 'a2a request returned', 20000);
  check('request_returns_after_ui_approval', readFileSync(join(scratch, 'request.exit'), 'utf8').trim() === '0' && json('request.json').role_request.state === 'approved');
  check('whoami_reports_executor', await typeLine(`a2a whoami > ${join(scratch, 'whoami-1.json')}`, 'm-who1') === 0 && json('whoami-1.json').role === 'executor', json('whoami-1.json'));
  await shot('04-approved');
  await closeUI(child);

  // Reopen: the persisted credential reconnects to the same daemon and terminal.
  check('daemon_and_terminal_survive_ui_close', alive(daemon));
  child = await launch(newApp);
  check('reopen_keeps_persisted_credential', JSON.parse(readFileSync(descriptor, 'utf8')).credential === credential);
  check('reopen_reconnects_same_daemon', (await call({ command: 'daemon_status' })).pid === daemon);
  await evaluate(`document.querySelector('[data-project-id="demo"]').click()`);
  await until(() => evaluate(`!!document.querySelector('section.pane[data-launch-id="${terminal}"][data-input-enabled="true"]')`), 'terminal reattached after reopen');
  check('whoami_after_reopen', await typeLine(`a2a whoami > ${join(scratch, 'whoami-2.json')}`, 'm-who2') === 0 && json('whoami-2.json').role === 'executor', json('whoami-2.json'));
  await shot('05-reopened');
  await closeUI(child); current = null;
  check('stop_daemon', (await call({ command: 'daemon_stop' })).ok);
  await until(() => !existsSync(join(state, 'control.sock')) && !alive(daemon), 'daemon stopped');
  check('terminal_socket_removed_on_stop', !existsSync(terminalSocket));
  report.status = 'PASS';
} catch (error) {
  report.error = String(error?.stack ?? error);
  try { await shot('99-failure'); } catch {}
} finally {
  if (current && alive(current.pid)) process.kill(current.pid, 'SIGTERM');
  writeFileSync(join(out, 'run.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ status: report.status, checks: report.checks.length, error: report.error?.slice(0, 400), fixture: F }));
}
process.exit(report.status === 'PASS' ? 0 : 1);
