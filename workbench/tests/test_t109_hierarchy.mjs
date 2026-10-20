// Contract from T-109: explicit ancestry, no guessing, append-only reads.
// Failure modes: absent/missing/foreign/self/cyclic parents, conflicting facts,
// later ordinary messages reparent a worker, summary hides a waiting descendant.
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import { OrchestrationStore } from '../src/store.ts';
import { Panes } from '../src/panes.ts';

const [output, source = resolve('workbench/src/sidebar.ts')] = process.argv.slice(2);
if (!output) throw new Error('A new summary path is required');
const { sidebarSnapshot } = await import(pathToFileURL(resolve(source)));
const root = mkdtempSync('/private/tmp/t109-contract-');
const state = join(root, 'state'); mkdirSync(state);
const store = new OrchestrationStore(state);
const report = { status: 'INCOMPLETE', model_calls: 0, source, checks: [], retained_fixture: root };
try {
  store.db.exec(`CREATE TABLE relay_requests (key TEXT PRIMARY KEY,launch TEXT,input TEXT);
    CREATE TABLE relay_results (key TEXT PRIMARY KEY,data TEXT);`);
  const launch = (id, role, preset, parent, project = 'p') => {
    const record = { id, project, task: 'task-' + id, thread: 'thread-' + id, attempt: role === 'controller' ? null : 'a7',
      role, preset, cli_version: 'codex-cli 0.163.0', ...(parent === undefined ? {} : { parent_launch: parent }) };
    store.launch(record); return record;
  };
  launch('idea', 'controller', 'ideation', null);
  launch('exec', 'controller', 'executor', 'idea');
  launch('worker', 'worker', null, 'exec');
  launch('review', 'reviewer', null, 'exec');
  launch('monitor', 'monitor', null, 'exec');
  launch('legacy', 'worker');
  launch('missing', 'worker', null, 'absent');
  launch('foreign', 'controller', 'executor', null, 'q');
  launch('cross', 'worker', null, 'foreign');
  launch('self', 'worker', null, 'self');
  launch('wrong-role', 'worker', null, 'worker');
  // Invalid ancestry must stay visible rather than disappearing recursively.
  launch('cycle-a', 'controller', 'ideation', 'cycle-b');
  launch('cycle-b', 'controller', 'executor', 'cycle-a');
  const gates = { listProjects: () => [{ project_id: 'p' }, { project_id: 'q' }], listTasks: () => [] };
  const panes = { status: thread => ({ lifecycle: 'running', state: thread === 'thread-worker' ? 'idle' : 'unknown' }) };
  const persistence = () => JSON.parse(execFileSync('python3', ['-B', 'workbench/tests/t107_persistence.py', state], { encoding: 'utf8' }));
  let before = persistence();
  const read = async () => {
    const snapshot = await sidebarSnapshot(gates, store, panes);
    assert.deepEqual(persistence(), before, 'Hierarchy query must never change tables, schema or trace');
    return Object.fromEntries(snapshot.agents.map(row => [row.id, row]));
  };
  const rows = await read();
  assert.equal(rows.exec.parent, 'idea', 'Explicit executor parent launch must be projected');
  for (const child of ['worker', 'review', 'monitor']) assert.equal(rows[child].parent, 'exec', child + ' must be below its recorded executor');
  for (const child of ['legacy', 'missing', 'cross', 'self', 'wrong-role', 'cycle-a', 'cycle-b']) assert.equal(rows[child].parent, null, child + ' must remain unassigned');
  assert.equal(rows.worker.attempt, 'a7');
  assert.equal(rows.exec.descendants.count, 3);
  assert.equal(rows.idea.descendants.count, 4);
  assert.equal(rows.exec.descendants.state, 'unknown');
  assert.deepEqual(rows.exec.descendants.counts, [{ state: 'idle', label: '空闲', count: 1 }, { state: 'unknown', label: '未知', count: 2 }]);
  report.checks.push('explicit_three_levels_and_all_child_roles', 'legacy_missing_cross_project_self_wrong_role_and_cycles_unassigned', 'read_is_zero_write');
  const relay = (id, kind, parent, child) => {
    const input = { command: 'inbox_send', kind, launch: parent.id, project: parent.project, task: parent.task, preset: parent.preset };
    const result = { ok: true, entry: { id, kind, from: parent.preset, to: child.role === 'controller' ? child.preset : `${child.role}:${child.thread}` } };
    store.db.prepare('INSERT INTO relay_requests VALUES (?,?,?)').run(id, parent.id, JSON.stringify(input));
    store.db.prepare('INSERT INTO relay_results VALUES (?,?)').run(id, JSON.stringify(result));
    store.register(child.id, 'sentinel message', 'inbox', undefined, { id, sender: parent.preset });
  };
  const otherExecutor = launch('another-exec', 'controller', 'executor', 'idea');
  relay('ordinary-reply', 'reply', otherExecutor, store.launchRecord('worker'));
  relay('conflicting-assign', 'assign', otherExecutor, store.launchRecord('review'));
  before = persistence();
  const changed = await read();
  assert.equal(changed.worker.parent, 'exec', 'Ordinary later messages cannot reassign a recorded parent');
  assert.equal(changed.review.parent, null, 'Conflicting explicit parent and authenticated successful assign must remain unassigned');
  report.checks.push('ordinary_later_reply_does_not_reparent', 'explicit_parent_conflicting_with_successful_assign_is_unassigned');
  const host = new Panes(state, store, {}, reason => { throw new Error(reason); });
  const queued = id => ({ record: { id, role: 'worker', task: 'task', attempt: 'a7' }, queue: [], state: 'unknown', failed: null, stopped: false });
  const first = queued('first'), second = queued('second');
  await Promise.all([
    host.parentLaunch.run('caller-one', async () => { await new Promise(resolve => setTimeout(resolve, 10)); await host.dispatch(first, 'sentinel one'); }),
    host.parentLaunch.run('caller-two', async () => { await new Promise(resolve => setTimeout(resolve, 1)); await host.dispatch(second, 'sentinel two'); }),
  ]);
  await host.dispatch(first, 'ordinary operator input');
  const dispatches = store.db.prepare("SELECT launch,data FROM dispatch_records WHERE launch IN ('first','second') ORDER BY seq").all()
    .map(row => ({ ...JSON.parse(row.data), launch: row.launch }));
  assert.deepEqual(dispatches.map(row => [row.launch, row.parent_launch]), [['second', 'caller-two'], ['first', 'caller-one'], ['first', null]],
    'Concurrent caller ancestry must remain request-local and never leak to later operator input');
  report.checks.push('descendant_summary_counts_all_levels', 'concurrent_dispatch_parent_isolation_and_no_later_leak');
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
finally { store.close(); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
