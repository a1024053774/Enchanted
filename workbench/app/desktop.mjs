import { app, BrowserWindow, dialog } from 'electron';
import { mkdirSync, readFileSync, realpathSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { parseArgs, promisify } from 'node:util';
import { execFile } from 'node:child_process';
import { startDaemon, request } from './src/transport.ts';
import { readOperatorCredential } from './src/credentials.ts';
import { desktopConnection, desktopCredentialDirectory, migrateDesktopCredential, newDesktopCredential, saveDesktopConnection } from './src/desktopCredentials.ts';
import { run } from './ui/main.mjs';

// What the backend needs to start workers (T-122). The user's own claude and codex are found
// the way their terminal finds them, through their login shell; without one, no worker of that
// CLI starts. Codex sessions run in the user's own ~/.codex (user ruling 2026-10-21, T-127).
async function userExecutable(name) {
  try {
    const { stdout } = await promisify(execFile)('/bin/zsh', ['-lic', `command -v ${name}`], { timeout: 15000 });
    const found = stdout.trim().split('\n').pop() || '';
    return found.startsWith('/') ? found : null;
  } catch (error) { console.error(JSON.stringify({ warning: `${name}_not_found`, reason: String(error) })); return null; }
}
async function workerLaunchConfig(packaged) {
  const [claude, codex] = await Promise.all([userExecutable('claude'), userExecutable('codex')]);
  const revision = packaged.a2a?.revision ?? 'unknown';
  return { ...(claude ? { claude_bin: claude } : {}),
    ...(codex ? { codex_bin: codex, codex_home: join(homedir(), '.codex') } : {}), role_card: join(app.getAppPath(), 'roles/worker.md'),
    role_card_revision: revision, reviewer_role_card: join(app.getAppPath(), 'roles/reviewer.md'), reviewer_role_card_revision: revision,
    monitor_role_card: join(app.getAppPath(), 'roles/monitor.md'), monitor_role_card_revision: revision,
    code_revision: revision, turn_limit: 6,
    hook_authorization: 'Enchanted product launch: worker hooks are passed only through each session\'s launch arguments (T-071, T-122)' };
}

async function start() {
  const { values } = parseArgs({ args: process.argv.slice(1), options: Object.fromEntries(
    ['state', 'task', 'launch', 'user-data', 'remote-debugging-port'].map(key => [key, { type: 'string', ...(key === 'launch' ? { multiple: true } : {}) }])) });
  if (values.launch && !values.task) throw new Error('--launch requires --task');
  const packaged = JSON.parse(readFileSync(join(app.getAppPath(), 'package.json'), 'utf8'));
  let state = values.state ?? join(homedir(), 'Library/Application Support', packaged.a2a?.state ?? 'a2a-orchestrator');
  mkdirSync(state, { recursive: true, mode: 0o700 });
  state = realpathSync(state);
  const userData = values['user-data'] ?? join(state, 'ui');
  mkdirSync(userData, { recursive: true, mode: 0o700 });
  app.setPath('userData', userData);
  if (!app.requestSingleInstanceLock()) { app.exit(0); return; }
  app.on('second-instance', () => { const window = BrowserWindow.getAllWindows()[0]; window?.show(); window?.focus(); });
  app.on('window-all-closed', () => app.quit());

  // The operator credential lives outside the daemon's data directory (T-126).
  const credentials = desktopCredentialDirectory(state, values.state !== undefined, packaged.productName ?? 'Enchanted');
  migrateDesktopCredential(state, credentials);
  const credential = desktopConnection(credentials);
  let connected = false;
  if (credential) {
    process.env.A2A_OPERATOR_CREDENTIAL = credential;
    const operator = readOperatorCredential(state);
    if (!operator) throw new Error('operator_credential_required');
    try {
      const result = await request(state, { command: 'daemon_status' }, operator);
      if (!result.ok) throw new Error(result.error);
      connected = true;
    } catch (error) {
      // Only an absent endpoint permits a start attempt. Transport still checks
      // the original PID/socket and owns dead-epoch recovery; refusals never retry.
      if (!['ENOENT', 'ECONNREFUSED'].includes(error.code)) throw error;
    }
  }
  if (!connected) {
    process.env.A2A_OPERATOR_CREDENTIAL = newDesktopCredential(credentials);
    await startDaemon(state, await workerLaunchConfig(packaged));
    saveDesktopConnection(credentials, process.env.A2A_OPERATOR_CREDENTIAL);
  }
  await run({ state, task: values.task, launch: values.launch, userData });
}

// Module evaluation must finish before run() waits for Electron's ready event.
void start().catch(error => {
  console.error(error);
  dialog.showErrorBox('Enchanted 启动失败', String(error));
  app.exit(1);
});
