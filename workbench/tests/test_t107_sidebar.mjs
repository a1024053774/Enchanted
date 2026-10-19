// Projection contracts with real Git and append-only SQLite; supplied live pane
// signals do not prove actual CLI behavior. Failure modes: missing/stale signals
// promoted to busy/idle, role-only ancestry, ambiguous senders, cross-project
// edges, cycles, absent upstream invented as zero, and Git read failure hidden.
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { join, resolve, dirname } from 'node:path';
import { execFileSync } from 'node:child_process';
import { OrchestrationStore } from '../src/store.ts';
const { agentState, aggregate, sidebarSnapshot } = await import(process.argv[3] ? pathToFileURL(resolve(process.argv[3])).href : new URL('../src/sidebar.ts', import.meta.url).href);

const output = process.argv[2];
if (!output) throw new Error('New report path required');
const root = mkdtempSync('/private/tmp/t107-projection-');
const report = { status: 'INCOMPLETE', scope: 'real Git/SQLite; controlled status inputs; no Electron or model proof', model_calls: 0, checks: [] };
let store;
try {
  const git = (repo, ...argv) => execFileSync('git', ['-C', repo, '-c', 'core.hooksPath=/dev/null',
    '-c', 'user.name=T107 fixture', '-c', 'user.email=t107@example.invalid', ...argv], { encoding: 'utf8' });
  const repo = join(root, 'first'); mkdirSync(repo); git(repo, 'init', '-b', 'main');
  writeFileSync(join(repo, 'file'), 'base'); git(repo, 'add', '.'); git(repo, 'commit', '-m', 'base');
  const base = git(repo, 'rev-parse', 'HEAD').trim();
  git(repo, 'config', 'remote.origin.url', join(root, 'unused-origin'));
  git(repo, 'config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*');
  git(repo, 'update-ref', 'refs/remotes/origin/main', base);
  git(repo, 'branch', '--set-upstream-to=origin/main', 'main');
  writeFileSync(join(repo, 'file'), 'ahead'); git(repo, 'commit', '-am', 'ahead');
  git(repo, 'checkout', '-b', 'independent-upstream', base);
  writeFileSync(join(repo, 'other'), 'behind'); git(repo, 'add', '.'); git(repo, 'commit', '-m', 'upstream');
  git(repo, 'update-ref', 'refs/remotes/origin/main', git(repo, 'rev-parse', 'HEAD').trim());
  git(repo, 'checkout', 'main');
  assert.match(git(repo, 'status', '-sb'), /ahead 1, behind 1/);
  const second = join(root, 'second'); mkdirSync(second); git(second, 'init', '-b', 'topic');
  const state = join(root, 'state'); mkdirSync(state); store = new OrchestrationStore(state);
  store.db.exec(`CREATE TABLE relay_requests (key TEXT PRIMARY KEY,launch TEXT,task TEXT,attempt TEXT,request_id TEXT,input TEXT,created_at TEXT);
    CREATE TABLE relay_results (key TEXT PRIMARY KEY,data TEXT,created_at TEXT);`);
  const records = [
    { id: 'idea', thread: 'idea-thread', role: 'controller', preset: 'ideation', attempt: null },
    { id: 'exec', thread: 'exec-thread', role: 'controller', preset: 'executor', attempt: null },
    { id: 'worker1', thread: 'worker1-thread', role: 'worker', attempt: 'a1' },
    { id: 'worker2', thread: 'worker2-thread', role: 'worker', attempt: 'a2' },
    { id: 'review', thread: 'review-thread', role: 'reviewer', attempt: 'a1' },
    { id: 'orphan', thread: 'orphan-thread', role: 'monitor', attempt: 'a1' },
    { id: 'foreign', thread: 'foreign-thread', role: 'controller', preset: 'executor', attempt: null, project: 'second-project', task: 'second-task' },
  ].map(row => ({ project: 'first-project', task: 'first-task', cli_version: 'codex-cli 0.163.0', ...row }));
  for (const record of records) store.launch(record);
  const assign = (id, parent, child) => {
    const input = { command: 'inbox_send', kind: 'assign', launch: parent.id, project: parent.project, task: parent.task, preset: parent.preset };
    const result = { ok: true, entry: { id, kind: 'assign', from: parent.preset, to: child.preset } };
    store.db.prepare('INSERT INTO relay_requests VALUES (?,?,?,?,?,?,?)').run(id, parent.id, parent.task, null, id, JSON.stringify(input), '2026-10-19');
    store.db.prepare('INSERT INTO relay_results VALUES (?,?,?)').run(id, JSON.stringify(result), '2026-10-19');
    store.register(child.id, 'fact', 'inbox', undefined, { id, sender: parent.preset });
  };
  assign('one', records[0], records[1]);
  for (const name of ['worker1', 'worker2', 'review']) store.register(name, 'fact', 'inbox', undefined, { id: name, sender: 'executor:exec-thread' });
  store.register('orphan', 'role address is not session identity', 'inbox', undefined, { id: 'orphan', sender: 'executor' });
  store.register('orphan', 'cross-project sender', 'inbox', undefined, { id: 'cross', sender: 'executor:foreign-thread' });
  const tasks = [{ project_id: 'first-project', task_id: 'first-task', repo }, { project_id: 'second-project', task_id: 'second-task', repo: second }];
  const gates = { listProjects: () => tasks.map(row => ({ project_id: row.project_id })),
    listTasks: project => tasks.filter(row => row.project_id === project),
    call: async input => ({ ok: true, task: tasks.find(row => row.task_id === input.task) }) };
  const live = { lifecycle: 'running', state: 'unknown', active: null };
  const panes = { status: () => live };
  const persistence = () => JSON.parse(execFileSync('python3', ['-B', join(dirname(fileURLToPath(import.meta.url)), 't107_persistence.py'), state], { encoding: 'utf8' }));
  const read = async () => {
    const before = persistence();
    const value = await sidebarSnapshot(gates, store, panes);
    assert.deepEqual(persistence(), before, 'Sidebar read changed persisted tables or traces');
    return value;
  };
  let value = await read();
  assert.equal(value.projects.length, 2);
  const first = value.projects.find(row => row.project_id === 'first-project');
  assert.equal(first.git.branch, 'main'); assert.equal(first.git.ahead, 1, 'Git ahead must match the independent divergent fixture'); assert.equal(first.git.behind, 1);
  const other = value.projects.find(row => row.project_id === 'second-project');
  assert.equal(other.git.branch, 'topic'); assert.equal(other.git.ahead, null); assert.equal(other.git.behind, null);
  assert.equal(first.state, 'unknown', 'Missing signal must remain unknown');
  const byId = Object.fromEntries(value.agents.map(row => [row.id, row]));
  assert.equal(byId.exec.parent, 'idea'); assert.equal(byId.worker1.parent, null, 'Role-only parent must be rejected');
  assert.equal(byId.worker2.parent, null); assert.equal(byId.review.parent, null); assert.equal(byId.orphan.parent, null);
  assert.equal(byId.worker2.attempt, 'a2');
  assert.ok(value.agents.every(row => row.state === 'unknown'));
  report.checks.push('two_projects_real_git_divergence_and_absent_upstream', 'authenticated_relay_assign_edge_and_task_attempts', 'role_address_and_cross_project_sender_do_not_infer_parent', 'missing_signal_stays_unknown');
  const another = { ...records[0], id: 'another-idea', thread: 'another-idea-thread' };
  store.launch(another); assign('conflict', another, records[1]);
  value = await read();
  assert.equal(value.agents.find(row => row.id === 'exec').parent, null);
  const active = { ...live, state: 'busy', native_session: 'native', turn: 'turn', active: { id: 'submission', nativeTurn: 'turn' } };
  const rootEvents = [
    { type: 'native_record', data: { file: 'sessions/native.jsonl', record: { type: 'session_meta', payload: { id: 'native', source: 'cli' } } } },
    { type: 'native_record', data: { file: 'sessions/native.jsonl', record: { type: 'event_msg', payload: { type: 'task_started', turn_id: 'turn' } } } },
  ];
  assert.equal(agentState(active, rootEvents), 'running');
  assert.equal(agentState(active, []), 'unknown', 'Unproven native origin cannot prove running');
  assert.equal(agentState({ ...active, interrupted: true }, rootEvents), 'unknown');
  assert.equal(agentState({ ...active, turn: 'other' }, rootEvents), 'unknown');
  assert.equal(agentState({ ...active, failed: 'failed' }, rootEvents), 'unknown');
  assert.equal(agentState({ ...active, historical: true }, rootEvents), 'unknown');
  assert.equal(agentState(active, [{ type: 'permission_wait' }]), 'unknown');
  assert.equal(agentState({ ...live, state: 'busy' }, []), 'unknown');
  assert.equal(agentState({ ...live, state: 'idle' }, []), 'idle');
  assert.equal(agentState({ ...live, lifecycle: 'ended' }, []), 'ended');
  assert.equal(agentState({ ...live, restoration: { status: 'failed' } }, []), 'unrestored');
  const question = { type: 'native_record', data: { record: { type: 'response_item', payload: { type: 'function_call', name: 'request_user_input', call_id: 'q' } } } };
  assert.equal(agentState(active, [question]), 'unknown');
  const rootQuestion = { ...question, data: { ...question.data, file: 'sessions/native.jsonl' } };
  const auxiliary = [
    { type: 'native_record', data: { file: 'sessions/helper.jsonl', record: { type: 'session_meta', payload: { id: 'helper', source: { subagent: {} } } } } },
    { type: 'native_record', data: { file: 'sessions/helper.jsonl', record: { type: 'event_msg', payload: { type: 'task_started', turn_id: 'helper-turn' } } } },
  ];
  assert.equal(agentState(active, [...rootEvents, rootQuestion, ...auxiliary]), 'unknown', 'Auxiliary native start must not release the root question');
  assert.equal(agentState(active, [...rootEvents, rootQuestion, { type: 'native_record', data: { record: { type: 'event_msg', payload: { type: 'task_started', turn_id: 'turn' } } } }]), 'unknown');
  assert.equal(agentState({ ...active, active: { id: 'new', nativeTurn: null } }, [
    { seq: 1, type: 'turn_start_signal', data: { session_id: 'native' } },
    { seq: 2, type: 'turn_submitted', data: { id: 'new' } },
  ]), 'unknown', 'Old native start cannot prove this submission is running');
  assert.equal(aggregate(['idle', 'unknown']), 'unknown');
  assert.equal(aggregate(['unknown', 'running']), 'running');
  assert.equal(aggregate(['running', 'waiting_user_answer']), 'waiting_user_answer');
  assert.equal(aggregate(['waiting_controller_answer', 'waiting_user_answer']), 'waiting_user_answer');
  assert.equal(aggregate([]), 'unknown');
  report.checks.push('ambiguous_sender_remains_unassigned', 'current_native_turn_required', 'permission_and_questions_stay_unknown', 'known_idle_ended_unrestored', 'aggregate_keeps_unknown_and_wait_priority');
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; report.retained_fixture = root; }
finally { store?.close(); if (report.status === 'PASS') rmSync(root, { recursive: true }); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
