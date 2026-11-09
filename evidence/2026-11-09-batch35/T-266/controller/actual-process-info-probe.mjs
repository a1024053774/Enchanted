// Real Panes/libproc observation of one owned process. No formal daemon connection.
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtempSync, readdirSync, rmSync, rmdirSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [source, delayText] = process.argv.slice(2);
const delay = Number(delayText);
if (!source || ![0, 6500].includes(delay)) throw new Error('Expected source root and delay 0 or 6500');
const { Panes } = await import(pathToFileURL(join(source, 'workbench/src/panes.ts')));
const state = mkdtempSync('/private/tmp/t266-controller-process-');
const report = { source, delay_ms: delay, state, status: 'INCOMPLETE', cleanup: {} };
let child, closed, panes;
try {
  child = spawn('/bin/sleep', ['30'], { detached: true, stdio: 'ignore' });
  closed = once(child, 'close');
  await once(child, 'spawn');
  report.child_pid = child.pid;
  panes = new Panes(state, { event() { throw new Error('Shell observer must not mutate lifecycle'); } }, {}, () => {});
  panes.panes.set('t266-owned', { record: { role: 'shell' }, pty: { pid: child.pid }, stopped: false, failed: null });
  const started = performance.now();
  const pending = panes.processInfo('t266-owned');
  if (delay) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, delay);
  report.result = await pending;
  report.elapsed_ms = performance.now() - started;
  const result = report.result;
  if (result.shell_pid !== child.pid || result.observer.method !== 'macOS libproc' ||
      result.processes.length !== 1 || result.processes[0].pid !== child.pid ||
      result.processes[0].command !== '/bin/sleep') throw new Error('Own process snapshot contract failed');
  report.status = 'PASS';
} catch (error) {
  report.status = 'FAIL';
  report.error = String(error);
  report.stack = error.stack;
  report.process_query = error.process_query;
  process.exitCode = 1;
} finally {
  if (child?.pid) {
    if (child.exitCode === null && child.signalCode === null) child.kill('SIGTERM');
    report.cleanup.child_close = await closed;
  }
  if (panes) {
    const directory = dirname(panes.hc.socket);
    if (!directory.startsWith('/private/tmp/enchanted-hc-')) throw new Error('Unexpected owned hc directory');
    report.cleanup.hc_directory = directory;
    report.cleanup.hc_entries = readdirSync(directory);
    rmdirSync(directory); // Must be empty: this probe never starts a core.
  }
  const inventory = path => readdirSync(path, { withFileTypes: true }).flatMap(entry => {
    const target = join(path, entry.name);
    return entry.isDirectory() ? inventory(target) : [{ path: target, bytes: statSync(target).size }];
  });
  report.cleanup.state_files = inventory(state);
  rmSync(state, { recursive: true });
  report.cleanup.state_removed = true;
  console.log(JSON.stringify(report));
}
