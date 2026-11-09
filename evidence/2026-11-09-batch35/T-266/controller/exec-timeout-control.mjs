import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { performance } from 'node:perf_hooks';
const exec = promisify(execFile);
const start = performance.now();
const pending = exec('/usr/bin/python3', ['-I', '-S', '-B', '-c', 'print("{\\"schema\\":1}")'], { timeout: 5000, encoding: 'utf8' });
// The fixture blocks only its own event loop, after starting its own child.
// No event-loop block in the independent control.
try {
  const result = await pending;
  console.log(JSON.stringify({settled:'resolved',...result,elapsed_ms:performance.now()-start,exit_code:pending.child.exitCode,signal:pending.child.signalCode,killed:pending.child.killed}));
} catch (error) {
  console.log(JSON.stringify({settled:'rejected',error:String(error),stdout:error.stdout,stderr:error.stderr,elapsed_ms:performance.now()-start,exit_code:pending.child.exitCode,signal:pending.child.signalCode,killed:pending.child.killed}));
}
