// T-152-only host: existing controlled PTY plus the T-141 native startup packet.
// No gate method, lifecycle callback, store event or verdict is replaced.
import { mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { installControlledPTY } from './controlled_quality_pty.ts';
import { publishReady } from './ready_file.ts';

const [source, root, control, ready] = process.argv.slice(2);
if (process.argv.length !== 6) throw new Error('Expected source, state, control and ready paths.');
const load = (name: string) => import(pathToFileURL(join(source, 'workbench/src', name)).href);
const { serve } = await load('daemon.ts');
const { A2AGates } = await load('gates/core.ts');
const { createOperatorCredential } = await load('credentials.ts');
const config = JSON.parse(readFileSync(join(control, 'config.json'), 'utf8'));
const bind = installControlledPTY(source, control, config);
const require = createRequire(join(source, 'workbench/src/panes.ts'));
const pty = require('node-pty');
const spawn = pty.spawn;
pty.spawn = (...args: any[]) => {
  const terminal = spawn(...args);
  let dataCallback: (data: string) => void;
  let opened = false;
  return { ...terminal,
    onData(callback: (data: string) => void) {
      dataCallback = callback;
      terminal.onData(callback);
    },
    write(data: string) {
      terminal.write(data);
      if (data === '\r' && !opened) {
        opened = true;
        // The first Enter opens the isolated untrusted fixture folder. Only
        // the subsequent native packet admits task release under T-141.
        setTimeout(() => dataCallback('\x1b]7501;state=idle:app=codex\x07'), 0);
      }
    },
  };
};
mkdirSync(root, { recursive: true, mode: 0o700 });
createOperatorCredential(root);
await serve(root, config, (state: string, runtime: any) => {
  bind(runtime);
  return new A2AGates(state, runtime);
});
publishReady(ready, { pid: process.pid, source, root, control, argv: process.argv,
  evidence_layer: 'real CLI/daemon/relay/gates/Git/SQLite; controlled PTY/process/native startup',
  real_codex_turns: 0 });
