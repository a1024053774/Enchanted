#!/bin/zsh
set -u
cd "${0:A:h}/../../.." || exit 2
node --input-type=module <<'JS'
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { spawnSync, execFileSync } from 'node:child_process';
import { join } from 'node:path';
const output = mkdtempSync('evidence/2026-10-23-batch23/T-150/local-01-');
const revision = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
const script = 'workbench/tests/test_t091_pane_ipc.mjs';
// Explicit failure signals; an import/setup failure is never a successful red state.
const failures = {
  no_key: 'Unregistered pane key was accepted',
  single_pane: 'Three selected launches must create three pane keys in one window',
  close: 'Explicit pane close must persist removal',
  empty_layout: 'Explicitly closed final pane must stay absent when app reopens',
  window_key: 'Projects must work without a pane key',
  notification: 'Only entering waiting-user emits one notification',
  history_credentials: 'Ended controller view must not issue an input credential',
  late_identity: 'Closing must wait for the admitted identity request',
  iframe: 'Iframe sender accepted: a2a:snapshot',
};
const report = { status: 'INCOMPLETE', revision, node: process.version, output, scope: 'VM contracts only; no Electron/CLI/backend proof', runs: [] };
function run(name, args, expectedError = null) {
  const summary = join(output, name + '.json');
  const argv = ['--experimental-vm-modules', ...args(summary)];
  const result = spawnSync(process.execPath, argv, { encoding: 'utf8', timeout: 60000 });
  writeFileSync(join(output, name + '.stdout.txt'), result.stdout ?? '', { flag: 'wx' });
  writeFileSync(join(output, name + '.stderr.txt'), result.stderr ?? '', { flag: 'wx' });
  let parsed;
  try { parsed = JSON.parse(readFileSync(summary, 'utf8')); } catch {}
  const pass = expectedError === null ? result.status === 0 && parsed?.status === 'PASS'
    : result.status === 1 && parsed?.error?.startsWith('AssertionError') && parsed.error.includes(expectedError);
  report.runs.push({ name, argv: [process.execPath, ...argv], exit: result.status, expectedError, pass, summary, spawn_error: result.error ? String(result.error) : null });
}
run('green', summary => [script, '--summary', summary]);
run('revision-current', summary => [script, '--summary', summary, '--revision', revision]);
for (const [name, failure] of Object.entries(failures)) run('mutant-' + name,
  summary => [script, '--summary', summary, '--mutant', name], failure);
// Existing checks for the same selection/parked credentials and input sequence boundaries.
run('regression-t139-selection', summary => ['workbench/tests/test_t139_selection.mjs', summary]);
run('regression-t110-sequence', summary => ['workbench/tests/test_t110_window_sequence.mjs', summary]);
report.status = report.runs.every(row => row.pass) ? 'PASS' : 'INCOMPLETE';
writeFileSync(join(output, 'summary.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report, null, 2));
process.exitCode = report.status === 'PASS' ? 0 : 1;
JS
