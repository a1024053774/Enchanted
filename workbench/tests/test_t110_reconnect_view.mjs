// Actual renderer refresh callback, with supplied IPC and React state setters.
// Failure cases: a failed catalog drops local selection, fabricates task removal,
// loses layout/names, or a later successful read fails to clear stale errors.
// This proves the callback contract; real Electron recovery remains separate.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const output = process.argv[2];
if (!output) throw new Error('Fresh report path required');
const source = readFileSync(new URL('../app/renderer.tsx', import.meta.url), 'utf8');
const report = { status: 'INCOMPLETE', scope: 'actual renderer refresh callback; supplied IPC/state, no GUI proof',
  revision: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(), checks: [] };
try {
  const match = source.match(/const refresh = useCallback\(async \(\) => \{([\s\S]*?)\n  \}, \[applySelection, applySidebar\]\);/);
  assert.ok(match, 'Find the actual refresh callback');
  const current = { task: { task_id: 'task-reconnect-73', project_id: 'project-reconnect-47' },
    paneKeys: ['pane-bound-91'], layout: 'pane-bound-91', names: { 'pane-bound-91': 'original pane' } };
  async function exercise(failed, removed = false) {
    const state = {}, calls = [];
    const set = name => value => { state[name] = value; };
    const context = { window: { a2a: {
      selection: async () => { calls.push('selection'); return current; },
      sidebar: async () => { calls.push('sidebar'); if (failed) throw new Error('reconnect-fixture-ENOENT');
        return { projects: [{ project_id: 'project-reconnect-47', tasks: removed ? [] : [{ task_id: 'task-reconnect-73' }] }] }; },
      selectTask: async task => { calls.push(['selectTask', task]); return { task: null, paneKeys: [] }; },
    } }, setLoading: set('loading'), setCatalogError: set('error'), setProjects: set('projects'),
      setSelectedTask: set('task'), setSelectedProject: set('project'), setPaneKeys: set('panes'), setLayout: set('layout'), setNames: set('names'),
      applySidebar: value => { state.catalog = value; }, applySelection: value => { state.task = value.task; state.panes = value.paneKeys; } };
    await vm.runInNewContext(stripTypeScriptTypes('(async () => {' + match[1] + '})()', { mode: 'strip' }), context);
    return { state, calls };
  }
  const failed = await exercise(true);
  assert.equal(failed.state.project, 'project-reconnect-47', 'Disconnected reload must retain the locally bound project');
  assert.deepEqual(failed.state.task, current.task);
  assert.deepEqual(failed.state.panes, ['pane-bound-91']);
  assert.equal(failed.state.layout, 'pane-bound-91');
  assert.deepEqual(failed.state.names, { 'pane-bound-91': 'original pane' });
  assert.match(failed.state.error, /reconnect-fixture-ENOENT/, 'Preserve the actual failed read');
  assert.equal(failed.state.loading, false);
  assert.equal(failed.calls.filter(call => Array.isArray(call)).length, 0, 'A failed read cannot declare task removal');
  const restored = await exercise(false);
  assert.equal(restored.state.project, 'project-reconnect-47');
  assert.equal(restored.state.error, null);
  assert.deepEqual(restored.state.panes, ['pane-bound-91']);
  const removed = await exercise(false, true);
  assert.equal(removed.state.task, null, 'Confirmed removal must still clear the task');
  assert.deepEqual(removed.state.panes, []);
  assert.deepEqual(removed.calls.at(-1), ['selectTask', null]);
  report.status = 'PASS'; report.checks = ['local_selection_survives_failed_catalog', 'original_layout_and_names_preserved',
    'read_error_remains_visible', 'unknown_catalog_does_not_clear_task', 'successful_catalog_and_confirmed_removal_preserved'];
} catch (error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify(report) + '\n');
process.exitCode = report.status === 'PASS' ? 0 : 1;
