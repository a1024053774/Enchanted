// T-270: an issue still open on an ended task (accepted, abandoned or upgraded) leaves the waiting count (state 可能已随任务结束失效) and stays open until
// the user confirms. Expectations come from the ticket (user, 2026-11-09: "这个问题都被处理了,但是这里还是展示这有 5 个问题待修复"),
// not from the implementation. Usage: node tests/test_t270_integrated_issues.mjs [core.ts module]
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const { A2AGates } = await import(process.argv[2] ? pathToFileURL(resolve(process.argv[2])).href : new URL('../src/gates/core.ts', import.meta.url).href);

const NOW = Date.parse('2026-11-09T18:00:00Z');
const dir = mkdtempSync(join(tmpdir(), 't270-'));
const checks = [];
const check = (name, actual, expected) => { assert.deepEqual(actual, expected, name); checks.push(name); };
try {
  new A2AGates(dir, undefined, () => NOW);
  const db = new DatabaseSync(join(dir, 'state.sqlite3'));
  const attempt = (task, id, state) => ({ task_id: task, attempt_id: id, session_id: 's-' + id, thread_id: 'th-' + id, fence: 1, spec_rev: 1,
    workspace: dir, state, revocation_reason: null, reclaimed: true, runtime_identity: null, turn_id: null });
  const task = (id, state, current) => ({ task_id: id, project_id: 'p', title: id, repo: dir, state, spec_rev: 1, current_attempt: current,
    attachments: [], version: 1, fence_counter: 1, integration_ref: 'refs/heads/main' });
  const tasks = [task('p+done', 'accepted', attempt('p+done', 'a2', 'accepted')), task('p+live', 'ready', attempt('p+live', 'b1', 'claimed')),
    task('p+up', 'upgraded', attempt('p+up', 'c1', 'upgraded')), task('p+gone', 'abandoned', attempt('p+gone', 'd1', 'abandoned')),
    task('p+review', 'reviewing', attempt('p+review', 'e1', 'submitted'))];
  for (const t of tasks) db.prepare('INSERT INTO tasks(id,data) VALUES (?,?)').run(t.task_id, JSON.stringify(t));
  const at = ms => new Date(NOW - ms).toISOString();
  const records = [];
  const issue = (taskId, id, from, attemptId, events = []) => {
    const base = { id, issue_id: id, schema: 1, kind: 'issue', task_id: taskId, attempt_id: attemptId, thread_id: 'th-' + attemptId, turn_id: null,
      number: records.length + 1, title: id, body: '原文 ' + id, blocking: true, from, to: 'executor', reply_to: null, refs: [], created_at: at(3_600_000) };
    records.push(base);
    events.forEach((action, i) => records.push({ ...base, id: id + '-' + i, kind: action === 'executor' ? 'answer' : 'disposition',
      from: action === 'executor' ? 'executor' : action === 'close' ? 'user' : 'executor', reply_to: id, created_at: at(1_800_000 - i),
      body: '处置 ' + id, ...(action === 'executor' ? {} : { action, reason: '测试', basis: '测试' }) }));
  };
  // Integrated task: the five live cases were gate-raised (system) issues of earlier attempts, escalated to the user.
  issue('p+done', 'sys-old-attempt', 'system', 'a1', ['needs-user']);
  issue('p+done', 'worker-current', 'worker:th-a2', 'a2', []);
  issue('p+done', 'closed', 'system', 'a1', ['needs-user', 'close']);
  issue('p+done', 'answered', 'worker:th-a2', 'a2', ['executor']);
  // Same shapes on a task that is not integrated: nothing changes.
  issue('p+live', 'live-sys', 'system', 'b1', ['needs-user']);
  issue('p+live', 'live-worker', 'worker:th-b1', 'b1', []);
  // The real case: T-249-2 ended as upgraded with gate-raised issues still escalated to the user.
  issue('p+up', 'up-sys', 'system', 'c1', ['needs-user']);
  issue('p+gone', 'gone-sys', 'system', 'd1', ['needs-user']);
  issue('p+review', 'review-sys', 'system', 'e1', ['needs-user']);
  for (const r of records) db.prepare('INSERT INTO issue_records(id,task,thread,data) VALUES (?,?,?,?)').run(r.id, r.task_id, r.thread_id, JSON.stringify(r));
  db.close();
  const gate = new A2AGates(dir, undefined, () => NOW);
  const states = async taskId => Object.fromEntries((await gate.call({ command: 'issues', task: taskId })).issues.map(v => [v.issue.id, v.state]));
  check('integrated_task_open_issues_are_stale', await states('p+done'),
    { 'sys-old-attempt': '可能已随任务结束失效', 'worker-current': '可能已随任务结束失效', closed: '已关闭', answered: '主控已答' });
  check('not_integrated_task_unchanged', await states('p+live'), { 'live-sys': '等你决定', 'live-worker': '等你决定' });
  check('upgraded_task_issue_is_stale', await states('p+up'), { 'up-sys': '可能已随任务结束失效' });
  check('abandoned_task_issue_is_stale', await states('p+gone'), { 'gone-sys': '可能已随任务结束失效' });
  check('task_still_in_review_unchanged', await states('p+review'), { 'review-sys': '等你决定' });
  const waiting = (await gate.call({ command: 'issues', task: 'p+done' })).issues.filter(v => v.state === '等你决定').length;
  check('integrated_task_waiting_count_zero', waiting, 0);
  const view = (await gate.call({ command: 'issues', task: 'p+done' })).issues.find(v => v.issue.id === 'sys-old-attempt');
  check('stale_reason_recorded', view.superseded_by_revision, { attempt: 'a1', reason: 'task ended' });
  const closed = await gate.call({ command: 'disposition', task: 'p+done', issue: 'sys-old-attempt', action: 'close', reason: '已随任务结束失效', basis: '任务已结束' });
  check('user_close_settles_it', closed.ok && closed.issues.find(v => v.issue.id === 'sys-old-attempt').state, '已关闭');
  check('user_close_recorded_as_user_input', closed.user_inputs.filter(i => i.reply_to === 'sys-old-attempt').map(i => i.form), ['action']);
  console.log(JSON.stringify({ status: 'PASS', checks }));
} finally { rmSync(dir, { recursive: true, force: true }); }
