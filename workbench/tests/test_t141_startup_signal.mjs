// Startup admission only. Native OSC was observed in the no-model probe; this
// check proves split packets, one-time release and foreground identity handling.
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const [output, source = '.'] = process.argv.slice(2);
if (!output || existsSync(output)) throw new Error('Fresh summary path required');
const report = { status: 'INCOMPLETE', checks: [] };
try {
  const { Panes } = await import(pathToFileURL(resolve(source, 'workbench/src/panes.ts')));
  const events = [];
  const host = new Panes('/fixture', { event: (type, data) => events.push({ type, data }) }, {}, () => {});
  let releases = 0, leader = true;
  host.processInfo = async () => ({ leader, failed: null });
  host.drain = async () => { releases++; };
  host.recordFailure = (pane, type) => { pane.failed = type; };
  const keys = [];
  host.serializeWrite = async (_pane, operation) => operation();
  const fresh = () => ({ record: { cli: 'Codex', thread: 'thread' }, terminalBuffer: '',
    startupScreen: '', startupOutputAt: 0, pty: { write: key => keys.push(key) },
    state: 'unknown', started: false, active: null, failed: null, stopped: false });
  const tick = () => new Promise(resolve => setImmediate(resolve));
  const pane = fresh();
  host.terminalProtocol(pane, '\x1b]7501;state=idle:app=');
  await tick(); assert.equal(releases, 0);
  host.terminalProtocol(pane, 'codex\x1b\\');
  await tick(); assert.equal(releases, 1, 'trusted native startup must release without an Open restricted dialog');
  assert.equal(pane.state, 'idle');
  report.checks.push('split_native_packet_releases_trusted_startup');
  pane.state = 'busy'; pane.active = { id: 'turn' };
  host.terminalProtocol(pane, '\x1b]7501;state=idle:app=codex\x1b\\');
  await tick(); assert.equal(releases, 1); assert.equal(pane.state, 'busy');
  report.checks.push('later_idle_does_not_replace_stop');
  for (const [name, modify, packet] of [
    ['other_app', () => {}, '\x1b]7501;state=idle:app=other\x1b\\'],
    ['plain_text', () => {}, '7501;state=idle:app=codex'],
    ['stopped', p => { p.stopped = true; }, '\x1b]7501;state=idle:app=codex\x1b\\'],
    ['unknown_foreground', () => { leader = false; }, '\x1b]7501;state=idle:app=codex\x1b\\'],
  ]) {
    const p = fresh(); modify(p); host.terminalProtocol(p, packet); await tick();
    assert.equal(releases, 1, name); report.checks.push(name + '_not_released');
  }
  leader = true;
  const captures = resolve('evidence/2026-10-23-batch23/T-141/probe-codex-start-01');
  const restricted = fresh();
  host.openCodexRestricted(restricted, JSON.parse(readFileSync(resolve(captures, 'untrusted.json'), 'utf8')).screen);
  await new Promise(resolve => setTimeout(resolve, 1000));
  assert.deepEqual(keys, ['\r']); assert.equal(releases, 1);
  report.checks.push('captured_untrusted_screen_only_selects_open_restricted');
  const unset = fresh();
  host.openCodexRestricted(unset, JSON.parse(readFileSync(resolve(captures, 'unset.json'), 'utf8')).screen);
  await tick(); assert.deepEqual(keys, ['\r']); assert.equal(unset.failed, 'codex_folder_trust_requested');
  report.checks.push('captured_unset_screen_refuses_persisted_trust');
  report.status = 'PASS';
} catch (error) { report.error = String(error); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
