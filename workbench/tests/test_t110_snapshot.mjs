// Execute the inspect expression from the real Electron driver, then serialize
// through its JSON transport. Absent DOM fields must survive as explicit nulls.
// This is snapshot-boundary evidence, not an Electron or product-behavior proof.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const output = process.argv[2];
if (!output) throw new Error('Fresh report path required');
const source = readFileSync(new URL('./t108_questions_driver.mjs', import.meta.url), 'utf8');
const report = { status: 'INCOMPLETE', scope: 'actual driver inspect expression and JSON serialization; supplied DOM',
  revision: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(), checks: [], model_calls: 0 };
try {
  const matches = [...source.matchAll(/if\(request.command==='inspect'\) value=await window.webContents.executeJavaScript\(`([\s\S]*?)`\);/g)];
  assert.equal(matches.length, 1, 'Read the one actual inspect expression');
  const inspect = ({ error = null, terminal = { hidden: false }, agent = false } = {}) => {
    const row = { dataset: { agentLaunch: 'snapshot-session-73', agentState: 'unknown' } };
    const document = { body: { innerText: '' }, activeElement: null,
      querySelector: selector => selector === '.catalog-error' ? error : selector === '.terminal-page' ? terminal : null,
      querySelectorAll: selector => selector === '[data-agent-launch]' && agent ? [row] : [] };
    const value = vm.runInNewContext(matches[0][1], { document, window: {}, getComputedStyle: () => ({ backgroundColor: 'transparent' }) });
    return JSON.parse(JSON.stringify(value));
  };
  const empty = inspect();
  assert.ok(Object.hasOwn(empty, 'sidebar_error'), 'Serialized snapshot must include sidebar_error while the error element is absent');
  assert.equal(empty.sidebar_error, null);
  for (const field of ['focused_agent', 'focused_launch']) {
    assert.ok(Object.hasOwn(empty, field), 'Serialized snapshot must include ' + field + ' when focus is absent');
    assert.equal(empty[field], null);
  }
  assert.equal(empty.terminal_hidden, false);
  const error = 'snapshot-sentinel ENOENT /private/tmp/owned-fixture/control.sock';
  assert.equal(inspect({ error: { textContent: error } }).sidebar_error, error, 'Preserve the actual caller-visible failure');
  assert.equal(inspect({ error: { textContent: '' } }).sidebar_error, '', 'An empty transient element is not an invented error');
  assert.equal(inspect({ terminal: null }).terminal_hidden, null, 'An unmounted terminal has an explicit unknown value');
  const [row] = inspect({ agent: true }).agents;
  assert.equal(row.id, 'snapshot-session-73');
  assert.ok(Object.hasOwn(row, 'project'), 'Missing selected project must remain explicit through JSON');
  assert.equal(row.project, null);
  report.checks = ['missing_error_element_serializes_null', 'actual_error_text_preserved', 'empty_error_text_not_fabricated',
    'missing_focus_and_terminal_explicit', 'missing_selected_project_explicit'];
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify(report) + '\n');
process.exitCode = report.status === 'PASS' ? 0 : 1;
