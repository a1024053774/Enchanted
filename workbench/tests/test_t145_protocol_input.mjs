// Failure modes: reports are recorded as interventions or reserve a draft; PTY bytes
// disappear/change; actual keys/pastes are filtered; identity checks or write order are lost.
// This bounded method check supplies only the PTY/store boundary. The Electron test
// separately proves the native UI/daemon/gate path. Expectations come from T-145.
import assert from 'node:assert/strict';
import { writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
const [summary, source] = process.argv.slice(2);
if (!summary) throw new Error('New summary path required');
const { Panes } = await import(source ? pathToFileURL(resolve(source, 'workbench/src/panes.ts')).href : '../src/panes.ts');
const report = { status: 'INCOMPLETE', argv: process.argv, checks: [], scope: 'actual Panes.userInput; supplied PTY/store, no GUI proof' };
const reports = [
  ['\x1b[<35;9;3M', 'utf8'], ['\x1b[<0;12;4m', 'utf8'], ['\x1b[<64;12;4M', 'utf8'],
  ['\x1b[I', 'utf8'], ['\x1b[O', 'utf8'], ['\x1b[0n', 'utf8'], ['\x1b[?1;2R', 'utf8'], ['\x1b[12;34R', 'utf8'],
  ['\x1b[?1;2c', 'utf8'], ['\x1b[>0;276;0c', 'utf8'], ['\x1b[?25;1$y', 'utf8'],
  ['\x1b[8;45;160t', 'utf8'], ['\x1b]11;rgb:0000/0000/0000\x1b\\', 'utf8'],
  ['\x1b[M !!', 'binary'], ['\x1b[M\xff\xfe\xfd', 'binary'], ['\x1b[32;12;4M', 'utf8'],
  ['\x1b[<35;9;3M\x1b[O', 'utf8'],
];
const keys = ['hello', '中文', '\r', '\x1b', '\x1b[A', '\x1b[1;2R', '\x1b[<35;9;3Mhello',
  '[<35;9;3M', '\x1b[<35;9;3M\n', '\x1b[200~\x1b[<35;9;3M\x1b[201~'];
function fixture() {
  const writes = [], recorded = [], events = [];
  const pane = { record: { id: 'launch', thread: 'thread', cli: 'Codex' }, state: 'idle',
    writes: Promise.resolve(), pendingInputs: 0, inputGeneration: 7, userDraft: false, interrupted: false,
    pty: { write(data) { writes.push(data); } } };
  const panes = Object.create(Panes.prototype);
  panes.byLaunch = () => pane;
  panes.store = { event(type, data) { events.push({ type, data }); return events.length; } };
  return { panes, pane, writes, recorded, events };
}
try {
  for (const [data, encoding] of reports) {
    const f = fixture(); let checked = 0;
    await f.panes.userInput('launch', data, { request_id: 'report' }, async text => { f.recorded.push(text); }, async () => { checked++; }, encoding);
    assert.deepEqual(f.recorded, [], 'terminal report must not become user input: ' + JSON.stringify(data));
    assert.equal(f.pane.userDraft, false, 'report must not reserve a user draft');
    assert.equal(f.pane.inputGeneration, 7, 'report must not invalidate a user declaration');
    assert.equal(checked, 1, 'report still needs identity validation');
    assert.deepEqual(f.writes, [encoding === 'binary' ? Buffer.from(data, 'latin1') : data], 'report bytes must reach PTY unchanged');
  }
  report.checks.push('reports_unrecorded_unreserved_forwarded_exactly');
  for (const data of keys) {
    const f = fixture();
    await f.panes.userInput('launch', data, { request_id: 'key' }, async text => { f.recorded.push(text); }, async () => {});
    assert.equal(f.recorded.length, 1, 'actual key/paste must be recorded: ' + JSON.stringify(data));
    assert.deepEqual(f.writes, [data]);
  }
  report.checks.push('typing_keys_ambiguous_F3_and_literal_paste_preserved');
  const f = fixture();
  await assert.rejects(() => f.panes.userInput('launch', reports[0][0], {}, async () => {}, async () => { throw new Error('stale identity'); }), /stale identity/);
  assert.deepEqual(f.writes, []);
  let release;
  const held = new Promise(resolve => { release = resolve; });
  const first = f.panes.userInput('launch', reports[0][0], {}, async () => {}, async () => held);
  const second = f.panes.userInput('launch', 'z', {}, async () => {}, async () => {});
  release(); await Promise.all([first, second]);
  assert.deepEqual(f.writes, [reports[0][0], 'z']);
  report.checks.push('stale_identity_rejected_and_shared_write_order_preserved');
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(summary, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
