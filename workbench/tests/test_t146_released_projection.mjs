// Failure modes: releasing a live terminal keeps a controller row; a stale turn
// makes the ordinary terminal idle/ended; closing a terminal removes its role;
// a new role duplicates a launch; historical display re-grants authority;
// a snapshot writes events. Expectations come from T-146-4 and T-133/T-107.
// Real SQLite and production projections, supplied pane lifecycle (no CLI proof).
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [output, source = '.'] = process.argv.slice(2);
if (!output || existsSync(output)) throw new Error('Fresh summary path required');
const report = { status: 'INCOMPLETE', argv: process.argv, checks: [], observed: {} };
let store;
try {
  const load = name => import(pathToFileURL(resolve(source, 'workbench/src', name + '.ts')));
  const { OrchestrationStore } = await load('store');
  const { RoleRequests } = await load('roleRequests');
  const { sidebarSnapshot } = await load('sidebar');
  const { projectFlow } = await load('flow');
  const { reflectTree } = await load('reflect');
  report.fixture = mkdtempSync('/private/tmp/t146-release-projection-');
  store = new OrchestrationStore(report.fixture);
  store.db.exec(`CREATE TABLE relay_requests (key TEXT,launch TEXT,input TEXT);
    CREATE TABLE relay_results (key TEXT,data TEXT);
    CREATE TABLE events (seq INTEGER,details TEXT,type TEXT);`);
  const terminal = { id: 'release-terminal', thread: 'release-thread', role: 'shell', project: 'demo',
    task: null, attempt: null, created_at: '2026-10-23T00:00:00Z' };
  store.launch(terminal);
  let lifecycle = 'running';
  const roles = new RoleRequests(store, () => lifecycle === 'running');
  const confirm = role => {
    const request = roles.request(terminal, role, 'claude');
    store.event('role_request_decided', { role_request: request.id, approved: true }, terminal);
    store.event('role_request_confirmed', { role_request: request.id }, terminal);
    store.event('terminal_turn', { role_request: request.id, state: 'idle' }, terminal);
    return request.id;
  };
  const gates = { listProjects: () => [], listTasks: () => [], call: async () => ({ ok: true, issues: [] }) };
  const panes = { status: () => ({ lifecycle }) };
  const read = async name => {
    const before = store.read();
    const sidebar = await sidebarSnapshot(gates, store, panes, roles);
    const flow = projectFlow([], sidebar.agents, []);
    const reflect = reflectTree(store.db, roles.all(), 'demo', new Map(sidebar.agents.map(row => [row.id, row.state])));
    assert.deepEqual(store.read(), before, 'Read-only projections');
    return report.observed[name] = { sidebar, flow, reflect };
  };
  const first = confirm('executor');
  assert.equal((await read('approved')).sidebar.agents[0]?.state, 'idle');
  roles.end(terminal.id, 'released');
  const released = await read('released');
  assert.equal(released.sidebar.agents.length, 0, 'Released live terminal must not remain a controller');
  assert.equal(released.sidebar.terminals.length, 1);
  assert.equal(released.sidebar.terminals[0].role, 'shell');
  assert.equal(released.sidebar.terminals[0].state, 'running', 'Use pane lifecycle, not the old idle turn');
  assert.equal(released.flow.unassigned.length, 0);
  assert.equal(released.reflect.find(row => row.id === first)?.state, 'ended', 'Reflect retains the ended role session');
  assert.equal(roles.approved(terminal.id), undefined);
  report.checks.push('released_live_terminal_is_ordinary_and_history_is_ended');
  lifecycle = 'unknown';
  const unknown = await read('unknown');
  assert.equal(unknown.sidebar.agents.length, 0, 'Unknown lifecycle is not evidence of terminal closure');
  assert.equal(unknown.sidebar.terminals[0]?.state, 'unknown');
  report.checks.push('unknown_lifecycle_is_not_terminal_closure');
  lifecycle = 'running';
  const second = confirm('ideation');
  const repeated = await read('new_role');
  assert.equal(repeated.sidebar.agents.length, 1);
  assert.equal(repeated.sidebar.agents[0].preset, 'ideation');
  assert.equal(repeated.sidebar.terminals.length, 0);
  assert.equal(repeated.reflect.find(row => row.id === first)?.state, 'ended');
  assert.equal(repeated.reflect.find(row => row.id === second)?.state, 'idle');
  report.checks.push('new_role_replaces_sidebar_identity_and_keeps_history');
  lifecycle = 'ended';
  const closed = await read('closed');
  assert.equal(closed.sidebar.agents.length, 1);
  assert.equal(closed.sidebar.agents[0].preset, 'ideation');
  assert.equal(closed.sidebar.agents[0].state, 'ended');
  assert.equal(closed.sidebar.terminals.length, 0);
  assert.equal(closed.flow.unassigned[0]?.state, 'ended');
  assert.equal(closed.reflect.find(row => row.id === second)?.state, 'ended');
  assert.equal(roles.approved(terminal.id), undefined);
  report.checks.push('closed_terminal_keeps_ended_identity_without_authority');
  report.status = 'PASS';
} catch (error) {
  report.error = String(error); report.stack = error.stack;
} finally {
  store?.close();
  writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
}
console.log(`${report.status}: ${report.error ?? report.checks.join(', ')}`);
process.exitCode = report.status === 'PASS' ? 0 : 1;
