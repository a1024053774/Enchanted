// Use the same native HTML-button input contract established by T-103:
// Enter down, CR char (13), Enter up, with window/content/DOM/target focus.
// This executes the driver's real branch with supplied Electron boundaries;
// it does not prove the browser effect. Retain the real E2E assertion too.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { EventEmitter } from 'node:events';

const [output, sourcePath = new URL('./t107_sidebar_driver.mjs', import.meta.url)] = process.argv.slice(2);
if (!output) throw new Error('A new report path is required');
const report = { status: 'INCOMPLETE', source: String(sourcePath), model_calls: 0,
  scope: 'Actual driver branch, supplied Electron focus; GUI effect requires external E2E', checks: [] };
const expected = [
  { type: 'keyDown', keyCode: 'Enter', focused: true },
  { type: 'char', keyCode: String.fromCharCode(13), focused: true },
  { type: 'keyUp', keyCode: 'Enter', focused: true },
];
try {
  const source = readFileSync(sourcePath, 'utf8');
  const marker = "        } else if (['toggle', 'toggle-keyboard'].includes(request.command)) {";
  const start = source.indexOf(marker);
  const end = source.indexOf("        } else if (request.command === 'resize')", start);
  assert.ok(start >= 0 && end > start, 'Actual disclosure driver branch must exist');
  const invoke = new Function('window', 'request', 'log', 'app', 'return (async () => { let value; ' +
    source.slice(start + marker.length, end) + '; return value; })()');
  const exercise = async (options = {}, events = []) => {
    let focused = false, activeApp = false;
    const request = { command: 'toggle-keyboard', target: 'nonce-executor-parent' };
    // outside-02: assigning document.activeElement succeeded, while native
    // window/content/document focus all stayed false in an inactive macOS app.
    const window = Object.assign(new EventEmitter(), { focus() {
      focused = activeApp && options.window !== false;
      if (focused) this.emit('focus');
    }, isFocused: () => focused,
      webContents: { isFocused: () => focused && options.contents !== false,
        executeJavaScript: async () => ({ target: options.target ?? request.target,
          documentFocused: focused && options.document !== false, expanded: false, tabIndex: options.tabIndex ?? 0 }),
        sendInputEvent: event => events.push({ ...event, focused }) } });
    const app = { focus: settings => { activeApp = settings?.steal === true && options.app !== false; } };
    return { value: await invoke(window, request, () => {}, app), events };
  };
  const good = await exercise();
  assert.deepEqual(good.events, expected, 'Disclosure keyboard injection must deliver Enter/CR/Enter with focus');
  assert.equal(good.value.attempted, true);
  for (const options of [{ app: false }, { window: false }, { contents: false }, { document: false }, { target: 'different-parent' }, { tabIndex: -1 }]) {
    const events = [];
    await assert.rejects(() => exercise(options, events), /does not have keyboard focus/);
    assert.deepEqual(events, [], 'Unverified keyboard target must receive no input');
  }
  report.checks.push('inactive_application_requires_explicit_activation', 'native_button_enter_cr_sequence',
    'window_contents_document_exact_target_and_tab_stop_required', 'bad_focus_never_sends_native_input');
  report.status = 'PASS';
} catch (error) { report.error = String(error); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
