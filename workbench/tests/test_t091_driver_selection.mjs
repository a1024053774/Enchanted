// Supplied DOM observations test the actual driver's selection logic only.
// No Electron, DOM engine, daemon, PTY, ps or model is started.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const report = { status: 'INCOMPLETE', scope: 'driver selection over supplied observations; no actual DOM/GUI proof',
  argv: process.argv, checks: [], model_turns: 0 };
const badRevision = '6974c2aad1233133264b7448e1277cd19fa0b6ba';
const observations = { text: 'fixture', panes: [
  { pane_key: 'key-I', launch: 'launch-I', role: 'controller', preset: 'ideation', window_id: 'window-I', text: 'pane I only' },
  { pane_key: 'key-E', launch: 'launch-E', role: 'controller', preset: 'executor', window_id: 'window-E', text: 'pane E only' },
  { pane_key: 'key-W', launch: 'launch-W', role: 'worker', preset: '', window_id: 'window-W', text: 'pane W only' },
] };
function reader(source) {
  const start = source.indexOf('    const inspect =');
  const end = source.indexOf('    await reply({ ready: true', start);
  assert.ok(start >= 0 && end > start);
  const snapshots = new Map(observations.panes.map(pane => [pane.pane_key, { window_id: pane.window_id,
    pane: { interruption: pane.pane_key === 'key-E' ? 72 : 12, input_generation: 4, interrupted: true } }]));
  const window = { webContents: { executeJavaScript: async () => structuredClone(observations) } };
  return new Function('window', 'latestSnapshots', 'latestSnapshot', 'stage', 'let screenReads = 0;\n' + source.slice(start, end) + ';return inspect;')(
    window, snapshots, snapshots.get('key-I'), () => {});
}
try {
  const bad = reader(execFileSync('git', ['show', `${badRevision}:workbench/tests/electron_driver.mjs`], { encoding: 'utf8' }));
  let badRejected = false;
  try { await assert.rejects(() => bad(), /Select exactly one/); }
  catch (error) { badRejected = error instanceof assert.AssertionError; report.known_bad = { revision: badRevision, rejected: badRejected, error: String(error) }; }
  assert.ok(badRejected, 'Old driver must violate explicit selection when multiple panes exist');
  const textRevision = '5d096caa2d690fe172ba8487226e8b16cf95950a';
  const oldText = reader(execFileSync('git', ['show', `${textRevision}:workbench/tests/electron_driver.mjs`], { encoding: 'utf8' }));
  try { assert.equal((await oldText({ pane_key: 'key-E' })).text, observations.text, 'Full page text must survive pane selection'); }
  catch (error) { report.text_counterexample = { revision: textRevision, rejected: error instanceof assert.AssertionError, error: String(error) }; }
  assert.ok(report.text_counterexample?.rejected);
  const inspect = reader(readFileSync(new URL('./electron_driver.mjs', import.meta.url), 'utf8'));
  await assert.rejects(() => inspect(), /Select exactly one/);
  assert.equal((await inspect({ pane_key: 'key-E' })).preset, 'executor');
  assert.equal((await inspect({ pane_key: 'key-E' })).interruption, 72);
  assert.equal((await inspect({ pane_key: 'key-E' })).text, observations.text, 'Full page text must survive pane selection');
  assert.equal((await inspect({ launch: 'launch-W' })).pane_key, 'key-W');
  await assert.rejects(() => inspect({ pane_key: 'absent' }));
  await assert.rejects(() => inspect({ launch: 'absent' }));
  assert.equal((await inspect({ all: true })).panes.length, 3);
  report.checks = ['ambiguity_rejected', 'selected_role_and_snapshot', 'launch_selects_worker', 'unknown_key_and_launch_rejected', 'explicit_all', 'full_page_text_preserved'];
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(process.argv[2], JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify(report) + '\n');
process.exitCode = report.status === 'PASS' ? 0 : 1;
