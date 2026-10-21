import { app, BrowserWindow, dialog } from 'electron';
import { existsSync, mkdirSync, readFileSync, realpathSync, renameSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { parseArgs } from 'node:util';
import { randomUUID } from 'node:crypto';
import { startDaemon, request } from './src/transport.ts';
import { readOperatorCredential } from './src/credentials.ts';
import { run } from './ui/main.mjs';

async function start() {
  const { values } = parseArgs({ args: process.argv.slice(1), options: Object.fromEntries(
    ['state', 'task', 'launch', 'user-data', 'remote-debugging-port'].map(key => [key, { type: 'string', ...(key === 'launch' ? { multiple: true } : {}) }])) });
  if (values.launch && !values.task) throw new Error('--launch requires --task');
  let state = values.state ?? join(homedir(), 'Library/Application Support/a2a-orchestrator');
  mkdirSync(state, { recursive: true, mode: 0o700 });
  state = realpathSync(state);
  const userData = values['user-data'] ?? join(state, 'ui');
  mkdirSync(userData, { recursive: true, mode: 0o700 });
  app.setPath('userData', userData);
  if (!app.requestSingleInstanceLock()) { app.exit(0); return; }
  app.on('second-instance', () => { const window = BrowserWindow.getAllWindows()[0]; window?.show(); window?.focus(); });
  app.on('window-all-closed', () => app.quit());

  const connection = join(state, 'desktop-connection.json');
  let connected = false;
  if (existsSync(connection)) {
    const { credential } = JSON.parse(readFileSync(connection, 'utf8'));
    if (typeof credential !== 'string' || !credential.startsWith(join(state, 'desktop-operator-')) ||
        !/\/desktop-operator-[0-9a-f-]{36}\.json$/.test(credential)) throw new Error('Invalid desktop connection descriptor');
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
    process.env.A2A_OPERATOR_CREDENTIAL = join(state, `desktop-operator-${randomUUID()}.json`);
    await startDaemon(state, {});
    const pending = join(state, `desktop-connection-${randomUUID()}.json`);
    writeFileSync(pending, JSON.stringify({ credential: process.env.A2A_OPERATOR_CREDENTIAL }) + '\n', { flag: 'wx', mode: 0o600 });
    renameSync(pending, connection);
  }
  await run({ state, task: values.task, launch: values.launch, userData });
}

// Module evaluation must finish before run() waits for Electron's ready event.
void start().catch(error => {
  console.error(error);
  dialog.showErrorBox('Enchanted 启动失败', String(error));
  app.exit(1);
});
