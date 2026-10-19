// Verify the actual keyboard driver branch. Independent input contract:
// focused native HTML buttons need Enter down, CR char (13), and Enter up.
// Failure modes: absent/wrong char, input without window/DOM focus, or input
// sent to a different task. This is an injection check, not browser evidence.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';

const [output, knownBad] = process.argv.slice(2);
if (!output || !knownBad) throw new Error('New output path and frozen faulty driver path are required');
function branch(source) {
  const marker = "        } else if (request.command === 'keyboard-select') {";
  const start = source.indexOf(marker);
  const end = source.indexOf("        } else if (request.command === 'capture') {", start);
  assert.ok(start >= 0 && end > start);
  return new Function('window', 'request', 'record', 'return (async () => { let value; ' +
    source.slice(start + marker.length, end) + '; return value; })()');
}
async function exercise(source, options = {}, events = []) {
  const stages = [];
  let focused = false;
  const request = { command: 'keyboard-select', task: 'independent-task-sentinel' };
  const window = { focus() { focused = options.focus !== false; }, isFocused: () => focused,
    webContents: { isFocused: () => focused,
      executeJavaScript: async () => ({ task: options.target ?? request.task, documentFocused: focused }),
      sendInputEvent: event => events.push({ ...event, focused }) } };
  const value = await branch(source)(window, request, item => stages.push(item));
  return { value, events, stages };
}
const expected = [
  { type: 'keyDown', keyCode: 'Enter', focused: true },
  { type: 'char', keyCode: String.fromCharCode(13), focused: true },
  { type: 'keyUp', keyCode: 'Enter', focused: true },
];
const report = { status: 'INCOMPLETE', argv: process.argv,
  scope: 'Actual injection branch with supplied Electron/DOM focus; real browser effect requires E2E' };
try {
  report.known_bad = await exercise(readFileSync(knownBad, 'utf8'));
  assert.notDeepEqual(report.known_bad.events, expected, 'Faulty driver must omit the required input sequence');
  assert.ok(!report.known_bad.events.some(event => event.type === 'char' && event.keyCode.charCodeAt(0) === 13));
  const source = readFileSync(new URL('./t103_picker_driver.mjs', import.meta.url), 'utf8');
  report.candidate = await exercise(source);
  assert.deepEqual(report.candidate.events, expected);
  assert.equal(report.candidate.value.attempted, true);
  for (const options of [{ focus: false }, { target: 'other-task' }]) {
    const events = [];
    await assert.rejects(() => exercise(source, options, events), /does not have keyboard focus/);
    assert.deepEqual(events, [], 'An invalid focus must not receive native input');
  }
  report.status = 'PASS';
} catch (error) { report.error = String(error); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
