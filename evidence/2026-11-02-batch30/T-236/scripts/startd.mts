import { spawn } from 'node:child_process';
import { openSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { createOperatorCredential } from '/Users/luckye/Documents/Code/a2a/workbench/src/credentials.ts';
const root = process.argv[2];
mkdirSync(root, { recursive: true, mode: 0o700 });
const credential = createOperatorCredential(root);
const env = { ...process.env, A2A_OPERATOR_CREDENTIAL: credential };
const child = spawn(process.execPath, ['/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts', root, '{}'], {
  detached: true, stdio: ['ignore', openSync(join(root, 'daemon.stdout.log'), 'a'), openSync(join(root, 'daemon.stderr.log'), 'a'), 'ipc'], env });
const t = Date.now();
child.once('message', () => { console.log(JSON.stringify({ ready_s: (Date.now() - t) / 1000, credential })); child.disconnect(); child.unref(); });
child.once('exit', (c) => { console.log('exit', c); process.exit(1); });
