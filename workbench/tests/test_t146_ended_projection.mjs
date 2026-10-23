// Failure modes: closed controllers disappear or become ordinary terminals;
// unconfirmed requests become historical controllers; repeat roles duplicate a
// launch; ended workers disappear from flow; reading history changes authority.
// Isolated SQLite/projection evidence only: pane liveness is supplied explicitly.
// Expected roles/states follow T-146 B, independent of projection implementation.
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [output, source = '.'] = process.argv.slice(2);
if (!output || existsSync(output)) throw new Error('Fresh summary path required');
const report = { status: 'INCOMPLETE', argv: process.argv, checks: [] };
let store;
try {
  const load = name => import(pathToFileURL(resolve(source, 'workbench/src', name + '.ts')));
  const { OrchestrationStore } = await load('store');
  const { RoleRequests } = await load('roleRequests');
  const { sidebarSnapshot } = await load('sidebar');
  const { projectFlow } = await load('flow');
  const { reflectTree } = await load('reflect');
  report.fixture = mkdtempSync('/private/tmp/t146-ended-projection-');
  store = new OrchestrationStore(report.fixture);
  store.db.exec(`CREATE TABLE relay_requests (key TEXT,launch TEXT,input TEXT);
    CREATE TABLE relay_results (key TEXT,data TEXT);
    CREATE TABLE events (seq INTEGER,details TEXT,type TEXT);`);
  const terminal = { id: 'confirmed-terminal', thread: 'controller-thread', role: 'shell', project: 'demo',
    task: null, attempt: null, created_at: '2026-10-23T00:00:00Z' };
  const ordinary = { ...terminal, id: 'ordinary-terminal', thread: 'ordinary-thread' };
  const unconfirmed = { ...terminal, id: 'unconfirmed-terminal', thread: 'unconfirmed-thread' };
  const worker = { ...terminal, id: 'ended-worker', thread: 'worker-thread', role: 'worker',
    task: 'demo+work', attempt: 'a1', parent_launch: terminal.id };
  for (const row of [terminal, ordinary, unconfirmed, worker]) store.launch(row);
  const live = new Set([terminal.id, ordinary.id, unconfirmed.id]);
  const roles = new RoleRequests(store, id => live.has(id));
  const request = roles.request(terminal, 'executor', 'claude');
  store.event('role_request_decided', { role_request: request.id, approved: true }, terminal);
  store.event('role_request_confirmed', { role_request: request.id }, terminal);
  store.event('terminal_turn', { role_request: request.id, state: 'running' }, terminal);
  roles.request(unconfirmed, 'ideation', 'claude');
  const gates = { listProjects: () => [], listTasks: () => [], call: async () => ({ ok: true, issues: [] }) };
  const panes = { status: thread => ({ lifecycle: thread === worker.thread || !live.has(
    [terminal, ordinary, unconfirmed].find(row => row.thread === thread)?.id) ? 'ended' : 'running' }) };
  const read = () => sidebarSnapshot(gates, store, panes, roles);
  const before = await read();
  assert.equal(before.agents.find(row => row.id === terminal.id)?.state, 'running');
  live.clear();
  const persisted = store.read();
  const after = await read();
  report.observed = after;
  const controller = after.agents.find(row => row.id === terminal.id);
  assert.ok(controller, 'Closed confirmed controller must remain an agent');
  assert.equal(controller.role, 'controller');
  assert.equal(controller.preset, 'executor');
  assert.equal(controller.state, 'ended');
  assert.equal(controller.state_label, '已结束');
  assert.equal(controller.task, null, 'Project terminal stays at project level');
  assert.ok(!after.terminals.some(row => row.id === terminal.id), 'No ordinary-terminal duplicate');
  assert.deepEqual(after.terminals.map(row => row.id), [ordinary.id, unconfirmed.id]);
  assert.equal(roles.approved(terminal.id), undefined, 'Historical display must not grant authority');
  assert.deepEqual(store.read(), persisted, 'Snapshot must be read-only');
  report.checks.push('closed_controller_identity_state_and_authority', 'unconfirmed_stays_ordinary');
  const flow = projectFlow([{ task_id: worker.task, project_id: 'demo', current_attempt: { attempt_id: 'a1' } }], after.agents, []);
  assert.equal(flow.lanes[0].agents.find(row => row.id === worker.id)?.state, 'ended');
  assert.equal(flow.lanes[0].agents.find(row => row.id === terminal.id)?.state, 'ended');
  const reflect = reflectTree(store.db, roles.all(), 'demo', new Map(after.agents.map(row => [row.id, row.state])));
  for (const id of [terminal.id, worker.id]) {
    assert.equal(reflect.find(row => row.launch === id)?.state, 'ended');
    assert.equal(reflect.find(row => row.launch === id)?.state_label, '已结束');
  }
  report.checks.push('ended_worker_and_controller_in_flow_and_reflect');
  // The sidebar identifies a terminal by launch. A subsequent confirmed role
  // replaces that row; Reflect keeps the distinct historical role sessions.
  live.add(terminal.id);
  roles.end(terminal.id, 'fixture');
  const next = roles.request(terminal, 'ideation', 'codex');
  store.event('role_request_decided', { role_request: next.id, approved: true }, terminal);
  store.event('role_request_confirmed', { role_request: next.id }, terminal);
  const repeated = await read();
  assert.equal(repeated.agents.filter(row => row.id === terminal.id).length, 1);
  assert.equal(repeated.agents.find(row => row.id === terminal.id).preset, 'ideation');
  assert.equal(repeated.agents.find(row => row.id === terminal.id).state, 'unknown');
  report.checks.push('latest_confirmed_role_per_terminal');
  report.status = 'PASS';
} catch (error) {
  report.error = String(error); report.stack = error.stack;
} finally {
  store?.close();
  writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
}
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
