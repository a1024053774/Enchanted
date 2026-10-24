// Failure modes: a retained pane consumes focus before this visibility's replay,
// then never focuses when revealed; a later snapshot steals user focus back.
// Runs the actual focus effect callback with supplied hook/DOM boundaries.
// It does not establish React scheduling, Electron focus, or timing performance.
import vm from 'node:vm';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';
const [summary, revision] = process.argv.slice(2);
assert(summary && !existsSync(summary), 'Use a new evidence path');
const report = { status: 'INCOMPLETE', revision: revision ?? 'working-tree', checks: [] };
try {
  const source = revision ? execFileSync('git', ['show', revision + ':workbench/app/renderer.tsx'], {encoding:'utf8'}) : readFileSync('workbench/app/renderer.tsx','utf8');
  const body = source.match(/const servedFocus = useRef\(0\);\s*useEffect\(\(\) => \{([\s\S]*?)\n  \}, \[([^\]]+)\]\);/);
  assert(body, 'Actual focus effect must be found');
  let hidden = true, calls = 0;
  const textarea = {};
  // T-161: only writable panes take focus; this test covers a writable retained pane.
  const context = vm.createContext({ active: true, snapshot: { input_enabled: true }, focusRequest: 8, restoring: false,
    restoredVisibility: 1, visibility: { current: { version: 2 } }, servedFocus: { current: 0 }, document: {activeElement:null},
    terminal: { textarea, focus() { calls++; if (!hidden) context.document.activeElement = textarea; } } });
  const effect = () => vm.runInContext('(function(){' + body[1] + '})()', context);
  const check = (name, condition) => { assert(condition, name); report.checks.push(name); };
  // On activation, a passive effect may still see the previous restoring=false.
  // The new visibility has not completed its replay and cannot consume focus.
  effect();
  check('activation_does_not_consume_focus_before_its_replay', calls === 0 && context.servedFocus.current === 0);
  hidden = false; context.restoredVisibility = 2;
  effect();
  check('reveal_serves_pending_focus', calls === 1 && context.document.activeElement === textarea && context.servedFocus.current === 8);
  context.document.activeElement = {};
  effect();
  check('later_snapshot_does_not_steal_focus', calls === 1);
  context.focusRequest = 9;
  effect();
  check('new_explicit_request_focuses_same_visible_pane', calls === 2 && context.servedFocus.current === 9);
  report.status = 'PASS';
} catch (error) { report.status = 'NO_GO'; report.error = String(error); process.exitCode = 1; }
writeFileSync(summary, JSON.stringify(report,null,2)+'\n', {flag:'wx'});
console.log(JSON.stringify(report));
