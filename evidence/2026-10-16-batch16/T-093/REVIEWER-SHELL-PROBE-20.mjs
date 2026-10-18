import fs from 'node:fs';
import path from 'node:path';
import cp from 'node:child_process';
import { createRequire, registerHooks, syncBuiltinESMExports } from 'node:module';
import { pathToFileURL } from 'node:url';
import { promisify, isDeepStrictEqual } from 'node:util';
import { randomUUID } from 'node:crypto';

const REPO = '/Users/luckye/Documents/Code/a2a-wt-t093';
const OUTPUT = '/private/tmp/t093-shell-recheck-joPlVg';
const mode = process.argv[2];
if (!['candidate', 'base'].includes(mode)) throw new Error('Use candidate or base.');
const nonce = randomUUID().slice(0, 8);
const output = path.join(OUTPUT, `${mode}-${nonce}`);
fs.mkdirSync(output, { mode: 0o700 });
const root = fs.mkdtempSync(`/private/tmp/t078-2-r20-${mode}-${nonce}-`);
const normalRoot = fs.mkdtempSync(`/private/tmp/a2a-claude-login-r20-${mode}-${nonce}-`);
const state = path.join(root, 'state');
const repo = path.join(root, 'repo');
for (const dir of [state, repo, path.join(root, 'bin')]) fs.mkdirSync(dir, { recursive: true });
const canonical = path.join(root, 'bin', 'inert-claude-canonical');
const alias = path.join(root, 'bin', 'inert-claude-alias');
fs.writeFileSync(canonical, 'This is inert fixture data. It must never execute.\n', { flag: 'wx', mode: 0o600 });
fs.symlinkSync(canonical, alias);
for (const preset of ['ideation', 'executor']) {
  const roleRoot = path.join(root, 'roles', preset);
  for (const dir of ['home', 'claude', 'tmp', 'shell', 'requests', 'hooks', 'user-data']) fs.mkdirSync(path.join(roleRoot, dir), { recursive: true });
  fs.writeFileSync(path.join(roleRoot, 'role.md'), `独立审查哨兵 ${nonce}: preserve 'quotes', spaces and 中文。\n`, { flag: 'wx' });
}
for (const dir of ['home/.claude', 'tmp', 'shell', 'audit']) fs.mkdirSync(path.join(normalRoot, dir), { recursive: true });
const isolation = { homeRoot: normalRoot, home: path.join(normalRoot, 'home'), config: path.join(normalRoot, 'home/.claude'),
  tmp: path.join(normalRoot, 'tmp'), shell: path.join(normalRoot, 'shell'), debug: path.join(normalRoot, 'debug.log'),
  api_url: 'http://127.0.0.1:51783', audit_directory: path.join(normalRoot, 'audit') };

const cases = [], byLaunch = new Map(), byPid = new Map();
const raw = (type, data) => fs.appendFileSync(path.join(output, 'boundaries.jsonl'), JSON.stringify({ type, ...data }) + '\n', { mode: 0o600 });
const prohibited = name => (...args) => { raw('UNEXPECTED_BOUNDARY', { name, first: String(args[0]) }); throw new Error(`Prohibited external boundary: ${name}`); };
const authReads = [];
const originalRead = fs.readFileSync;
const originalOpen = fs.openSync;
const authPath = value => typeof value === 'string' && /(?:\.credentials\.json|(?:^|\/)auth\.json|Library\/Keychains)/.test(value);
fs.readFileSync = function(value, ...args) { if (authPath(value)) { authReads.push(String(value)); throw new Error('No auth reads allowed.'); } return originalRead.call(fs, value, ...args); };
fs.openSync = function(value, ...args) { if (authPath(value)) { authReads.push(String(value)); throw new Error('No auth opens allowed.'); } return originalOpen.call(fs, value, ...args); };

const fakeExec = async (file, args, options) => {
  if (args.length === 1 && args[0] === '--version') {
    const item = byLaunch.get(options?.env?.A2A_LAUNCH);
    if (!item) return prohibited('unbound version probe')(file);
    const call = { file, args, launch: item.record.id };
    item.versions.push(call); raw('version', call);
    return { stdout: `${item.versionOverride ?? '2.1.302 (Claude Code)'}\n`, stderr: '' };
  }
  if (file === '/usr/bin/python3' && args.includes('-I') && args.includes('-S') && args.includes('-B') && String(args[3]).endsWith('processSnapshot.py')) {
    const pid = Number(args[4]), item = byPid.get(pid);
    if (!item) return prohibited('unbound process observer')(file);
    item.processCalls++; raw('process_snapshot_supplied', { launch: item.record.id, pid, args });
    const leader = item.replacedLeader ? item.leader + 7 : item.leader;
    return { stdout: JSON.stringify({ schema: 1, root_pid: pid, method: 'macOS libproc', rows: [
      { pid, ppid: 0, pgid: pid, tpgid: leader, command: '/bin/zsh' },
      { pid: leader, ppid: pid, pgid: leader, tpgid: leader, command: canonical }
    ] }), stderr: '' };
  }
  return prohibited('execFile')(file);
};
function execBoundary(...args) { return prohibited('unpromisified execFile')(...args); }
execBoundary[promisify.custom] = fakeExec;
cp.execFile = execBoundary;
for (const name of ['exec', 'execSync', 'execFileSync', 'spawn', 'spawnSync', 'fork']) cp[name] = prohibited(name);
process.kill = (pid, signal) => {
  const item = cases.find(item => item.oldPid === pid);
  if (!item || signal !== 0) return prohibited('process.kill')(pid);
  item.pidChecks++; raw('old_pid_check_supplied_ESRCH', { launch: item.record.id, pid, signal });
  const error = new Error('Synthetic old process absent.'); error.code = 'ESRCH'; throw error;
};
syncBuiltinESMExports();
const require = createRequire(path.join(REPO, 'workbench/src/panes.ts'));
const ptyPath = require.resolve('node-pty');
require.cache[ptyPath] = { id: ptyPath, filename: ptyPath, loaded: true, exports: { spawn(shell, argv, options) {
  const item = byLaunch.get(options.env.A2A_LAUNCH);
  if (!item) return prohibited('unbound PTY')(shell);
  item.spawns.push({ shell, argv, cwd: options.cwd, env: options.env });
  raw('PTY_supplied', { launch: item.record.id, shell, argv, cwd: options.cwd });
  byPid.set(item.ptyPid, item);
  return { pid: item.ptyPid, onData() {}, onExit() {}, write(text) { item.writes.push(text); }, resize() {}, kill: prohibited('PTY.kill') };
} } };
const panesURL = pathToFileURL(path.join(REPO, 'workbench/src/panes.ts')).href + `?targeted-shell-recheck=${mode}`;
if (mode === 'base') registerHooks({ load(url, context, nextLoad) {
  if (url === panesURL) return { format: 'module-typescript', source: fs.readFileSync(path.join(OUTPUT, 'panes-base.ts'), 'utf8'), shortCircuit: true };
  return nextLoad(url, context);
} });
const { Panes } = await import(panesURL);
const { claudeLaunch } = await import(pathToFileURL(path.join(REPO, 'workbench/src/claudeLaunch.ts')).href);
const { ClaudeLogin } = await import(pathToFileURL(path.join(REPO, 'workbench/src/claudeLogin.ts')).href);
let authPrepareCalls = 0;
ClaudeLogin.prepare = async () => { authPrepareCalls++; throw new Error('No authentication boundary allowed.'); };
const { OrchestrationStore } = await import(pathToFileURL(path.join(REPO, 'workbench/src/store.ts')).href);
const store = new OrchestrationStore(state);
store.db.exec('CREATE TABLE tasks (id TEXT PRIMARY KEY, data TEXT NOT NULL); CREATE TABLE attempts (id TEXT PRIMARY KEY, data TEXT NOT NULL);');
const sentinelAttempt = `attempt-${nonce}`;
store.db.prepare('INSERT INTO attempts(id,data) VALUES (?,?)').run(sentinelAttempt, JSON.stringify({ attempt_id: sentinelAttempt, state: 'working', fence: 42, session_id: `worker-${nonce}`, owner: 'original worker' }));
const clone = value => JSON.parse(JSON.stringify(value));
const normalEnvironment = { NODE_OPTIONS: process.env.NODE_OPTIONS, A2A_PROFILE_PROCESS_LOG: process.env.A2A_PROFILE_PROCESS_LOG };
process.env.NODE_OPTIONS = `--import=${REPO}/workbench/src/claudeLoginProcessTrace.mjs`;
process.env.A2A_PROFILE_PROCESS_LOG = path.join(normalRoot, 'process-nonce.jsonl');
function add(name, expected, patch = () => {}, normal = false, preset = 'ideation') {
  const n = cases.length, launch = randomUUID(), session = randomUUID(), thread = randomUUID();
  const task = { task_id: `r20-${nonce}-${n}`, project_id: `project-${nonce}`, repo, spec_rev: 31, base_commit: '0123456789abcdef0123456789abcdef01234567' };
  const input = { schema: 1, root, state, task: task.task_id, preset, launch, session, thread, executable: alias,
    version: '2.1.302', role_file: path.join(root, 'roles', preset, 'role.md'), code_revision: '1db51d21d19e462e54360cb6d53f0c04026bf18b', source_snapshot: path.join(root, `source-${nonce}`),
    api_url: 'http://127.0.0.1:51783', ...(normal ? { authentication: 'normal-login', credential_source: 'file' } : {}) };
  const generated = claudeLaunch(task, input, normal ? isolation : undefined);
  const record = { ...clone(generated), cli_version: '2.1.302 (Claude Code)', executable_path: canonical, created_at: '2026-10-19T00:00:00.000Z' };
  const item = { name, expected, task, input, generated: clone(generated), record, versions: [], spawns: [], writes: [], pidChecks: 0, processCalls: 0,
    oldPid: 710000 + n * 100, ptyPid: 710001 + n * 100, leader: 710002 + n * 100, failures: [] };
  patch(record, item);
  // The expected argv is derived directly from this external fixture, without importing resumeArgv.
  const resume = Array.isArray(record.argv) ? record.argv.map((token, index) => index === record.argv.indexOf('--session-id') ? '--resume' : token) : null;
  item.expectedArgv = resume;
  store.db.prepare('INSERT INTO tasks(id,data) VALUES (?,?)').run(task.task_id, JSON.stringify(task));
  store.launch(record);
  store.event('pane_started', { shell_pid: item.oldPid, sentinel: nonce }, record);
  store.event('pane_layout_opened', { position: n, native_session: session, resume_argv: item.savedArgvOverride ?? resume }, record);
  const trace = path.join(state, 'traces', record.id, 'pty.raw');
  fs.mkdirSync(path.dirname(trace), { recursive: true }); fs.writeFileSync(trace, `immutable prefix ${nonce}\n`, { flag: 'wx' });
  if (record.env && typeof record.env.CLAUDE_CONFIG_DIR === 'string' && path.isAbsolute(record.env.CLAUDE_CONFIG_DIR) && !item.missingNative) {
    const file = path.join(record.env.CLAUDE_CONFIG_DIR, 'projects', `fixture-${nonce}`, `${session}.jsonl`);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, JSON.stringify({ sessionId: session, cwd: repo, type: 'system', nonce }) + '\n', { flag: 'wx' });
  }
  item.recordBefore = store.db.prepare('SELECT data FROM launch_records WHERE id=?').get(record.id).data;
  cases.push(item); byLaunch.set(record.id, item);
  return item;
}
add('explicit-fake-ideation', 'restored');
add('legacy-fake-executor-no-auth-no-canonical', 'restored', r => { delete r.authentication; delete r.executable_path; }, false, 'executor');
add('normal-generated-minus-authentication', 'normal_login_restore_requires_protected_start', r => { delete r.authentication; }, true);
add('partial-normal-shell-exec-only', 'normal_login_restore_requires_protected_start', (r, item) => {
  delete r.authentication;
  const normal = claudeLaunch(item.task, { ...item.input, authentication: 'normal-login', credential_source: 'file' }, isolation);
  item.normalCounterpart = clone(normal);
  const fakeDebug = r.argv[r.argv.indexOf('--debug-file') + 1];
  const normalDebug = normal.argv[normal.argv.indexOf('--debug-file') + 1];
  // Same input identities and complete argv; isolate the actual normal shell execution form.
  r.shell_argv = clone(normal.shell_argv);
  r.shell_argv[3] = r.shell_argv[3].replaceAll(normalDebug, fakeDebug);
});
function stripNormal(r) {
  delete r.authentication; delete r.login_audit_directory; delete r.login_preflight_file;
  r.role_card_revision = `unrecognized-${nonce}`; r.hook_authorization = 'unknown';
  r.env.HOME = path.join(root, 'roles/ideation/home'); r.env.CLAUDE_CONFIG_DIR = path.join(root, 'roles/ideation/claude');
  delete r.env.NODE_OPTIONS; delete r.env.A2A_PROFILE_PROCESS_LOG;
}
add('normal-stripped-but-exec-marker-survives', 'normal_login_restore_requires_protected_start', stripNormal, true);
add('normal-stripped-and-shell-unknown', 'restore_record_unrecognized', r => { stripNormal(r); r.shell_argv = ['-f', '-i', '-c', `unrecognized-${nonce}`]; }, true);
add('unknown-shell-missing', 'restore_record_unrecognized', r => { delete r.shell_argv; });
add('unknown-shell-non-array', 'restore_record_unrecognized', r => { r.shell_argv = { command: `unrecognized-${nonce}` }; });
add('unknown-shell-extra-argument', 'restore_record_unrecognized', r => { r.shell_argv.push(`unknown-${nonce}`); });
add('unknown-shell-option', 'restore_record_unrecognized', r => { r.shell_argv[0] = '-unknown'; });
add('unknown-shell-empty-command', 'restore_record_unrecognized', r => { r.shell_argv[3] = ''; });
add('unknown-shell-leading-space-exec', 'restore_record_unrecognized', r => { r.shell_argv[3] = ' exec ' + r.argv[0]; });
add('unknown-shell-command-sentinel-with-fake-envelope', 'restore_record_unrecognized', r => {
  // Prefix/suffix alone cannot establish that this is the recorded fake P1 command.
  r.shell_argv[3] = "'/private/tmp/unrecognized-" + nonce + "' 'different-input'" + '; exec /bin/zsh -f -i';
});
add('worker-attempt-retained', 'restore_managed_attempt_requires_reclaim', r => { r.attempt = sentinelAttempt; r.role = 'worker'; });
add('fake-version-mismatch', 'restore_version_mismatch', (r, item) => { item.versionOverride = '9.8.7 (Claude Code)'; });
add('fake-missing-native-session', 'restore_session_missing', (r, item) => { item.missingNative = true; });
add('fake-missing-argv', 'restore_argv_missing', r => { delete r.argv; });
add('fake-layout-argv-tampered', 'restore_argv_changed', (r, item) => { item.savedArgvOverride = ['bare-resume-must-not-run', nonce]; });
add('fake-canonical-identity-changed', 'restore_executable_changed', r => { r.executable_path = path.join(root, 'bin', 'different'); });
for (const [key, value] of Object.entries(normalEnvironment)) { if (value === undefined) delete process.env[key]; else process.env[key] = value; }
const initialEvents = store.db.prepare('SELECT * FROM orchestration_events ORDER BY seq').all();
const initialAttempts = store.db.prepare('SELECT * FROM attempts ORDER BY id').all();
fs.writeFileSync(path.join(output, 'inputs.json'), JSON.stringify({ mode, nonce, root, normalRoot, cases: cases.map(({ name, expected, generated, normalCounterpart, record, expectedArgv }) => ({ name, expected, generated, normalCounterpart, record, expectedArgv })), initialEvents, initialAttempts }, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
const failures = [], pass = (condition, message, item) => { if (!condition) { failures.push({ case: item?.name ?? 'global', message }); item?.failures.push(message); } };
const panes = new Panes(state, store, {}, reason => { failures.push({ case: 'global', message: `event-write-failure: ${reason}` }); });
await panes.recover(`independent-${nonce}`);
for (const item of cases) {
  const { record } = item;
  const status = panes.status(record.thread), events = store.read().filter(row => row.launch === record.id);
  const restored = events.filter(row => row.type === 'pane_restored');
  const failed = events.filter(row => row.type === 'pane_restore_failed');
  item.observed = { restoration: status.restoration, live: panes.panes.has(record.thread), restored: restored.length, failed: failed.length,
    versions: item.versions.length, ptys: item.spawns.length, processCalls: item.processCalls, pidChecks: item.pidChecks };
  pass(store.db.prepare('SELECT data FROM launch_records WHERE id=?').get(record.id).data === item.recordBefore, 'Immutable launch history changed.', item);
  if (item.expected === 'restored') {
    pass(status.restoration?.status === 'restored' && restored.length === 1 && failed.length === 0, 'Known fake profile must restore exactly once.', item);
    pass(item.versions.length === 1 && item.versions[0].file === alias && isDeepStrictEqual(item.versions[0].args, ['--version']), 'Original CLI version check missing or changed.', item);
    pass(item.spawns.length === 1 && item.writes.length === 0, 'Restore must create one PTY without prompt writes.', item);
    pass(isDeepStrictEqual(restored[0]?.data.argv, item.expectedArgv), 'Complete original argv not preserved except session selector.', item);
    const quote = text => "'" + text.replaceAll("'", "'\\''") + "'";
    const expectedShell = ['-f', '-i', '-c', item.expectedArgv.map(quote).join(' ') + '; exec /bin/zsh -f -i'];
    pass(isDeepStrictEqual(item.spawns[0]?.argv, expectedShell), 'PTY did not receive complete quoted argv.', item);
    const pane = panes.panes.get(record.thread);
    pass(pane?.record.executable_path === canonical && restored[0]?.data.leader === item.leader, 'Canonical runtime identity not proven by supplied process snapshot.', item);
    item.replacedLeader = true;
    const replaced = await panes.processInfo(record.thread);
    pass(replaced.failed === 'claude_leader_replaced_or_exited' && pane.leader === item.leader, 'Fixed leader identity must reject replacement.', item);
    item.fixedLeaderResult = replaced.failed;
  } else {
    pass(status.restoration?.status === 'failed' && status.restoration.error === item.expected && failed.length === 1 && restored.length === 0 && !panes.panes.has(record.thread), `Expected explicit ${item.expected} and unrestored pane.`, item);
    pass(item.spawns.length === 0 && item.writes.length === 0, 'Refused record reached PTY or prompt boundary.', item);
    if (['normal_login_restore_requires_protected_start', 'restore_record_unrecognized', 'restore_managed_attempt_requires_reclaim'].includes(item.expected)) {
      pass(item.versions.length === 0 && item.processCalls === 0 && item.pidChecks === 0, 'Refused profile crossed CLI/version/process boundary.', item);
    }
    if (item.expected === 'normal_login_restore_requires_protected_start') pass(status.restoration?.details === '正常登录会话不自动续接，请经正常登录入口重新启动。', 'Normal-login refusal omitted actionable Chinese details.', item);
  }
}
pass(authReads.length === 0 && authPrepareCalls === 0, 'Recovery entered authentication boundary.');
pass(isDeepStrictEqual(store.db.prepare('SELECT * FROM attempts ORDER BY id').all(), initialAttempts), 'Worker attempt state changed.');
pass(isDeepStrictEqual(store.db.prepare('SELECT * FROM orchestration_events ORDER BY seq LIMIT ?').all(initialEvents.length), initialEvents), 'Existing event history changed.');
const result = { status: failures.length ? 'FAIL' : 'PASS', layer: 'L1', mode, nonce, output, fixtures: { root, normalRoot, state },
  count: cases.length, passed: cases.filter(item => item.failures.length === 0).length, authReads, authPrepareCalls,
  realCLI: 0, realPTY: 0, realProcessQueries: 0, cases: cases.map(({ name, expected, observed, fixedLeaderResult, failures }) => ({ name, expected, observed, fixedLeaderResult, failures })), failures };
fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
store.close();
console.log(JSON.stringify({ status: result.status, mode, count: result.count, passed: result.passed, artifact: path.join(output, 'result.json'), failures }, null, 2));
process.exitCode = failures.length ? 1 : 0;
