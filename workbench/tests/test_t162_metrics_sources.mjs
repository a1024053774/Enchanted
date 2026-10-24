// 失败方式（先列再写）：无来源误报 0；有来源但区间内无记录误报未知；越过时间边界；
// 原生事件来源丢失；未知会话混入汇总；把请求模型当观察模型；跨项目污染。
// 此夹具只证明后台已记录事件的计数语义，不证明任何真实 CLI 日志已完整采集。
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { DatabaseSync } from 'node:sqlite';

const { values } = parseArgs({ options: { summary: { type: 'string' }, revision: { type: 'string' }, mutant: { type: 'string' } } });
assert(values.summary && !(values.revision && values.mutant), 'Use --summary and at most one target.');
assert(!existsSync(values.summary), 'Preserve the previous summary.');
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const fixture = mkdtempSync('/private/tmp/t162-metrics-');
const report = { status: 'INCOMPLETE', argv: process.argv, revision: values.revision ?? null, mutant: values.mutant ?? null, fixture, checks: [] };
const db = new DatabaseSync(':memory:');
const check = (name, actual, expected) => {
  try { assert.deepEqual(actual, expected); report.checks.push({ name, status: 'PASS' }); }
  catch (error) { report.checks.push({ name, status: 'FAIL', actual, expected }); }
};
try {
  let source = values.revision ? execFileSync('git', ['show', values.revision + ':workbench/src/metrics.ts'], { cwd: root, encoding: 'utf8' })
    : readFileSync(join(root, 'workbench/src/metrics.ts'), 'utf8');
  const mutants = {
    'unknown-as-zero': ['turns: facts?.turns ?? null,', 'turns: facts?.turns ?? 0,', 1],
    'zero-as-unknown': ["const facts = observed.get(record.id) ?? (turnSources.has(record.id) ? { models: new Set(['unknown']), efforts: new Set(['unknown']), turns: 0 } : undefined);", 'const facts = observed.get(record.id);', 1],
    'source-dropped': ['turn_sources: turnSources.get(record.id) ?? [],', 'turn_sources: [],', 1],
    'range-ignored': ['if (!inTime(String(row.time))) continue;', '', 2],
  };
  if (values.mutant) {
    assert(mutants[values.mutant], 'Unknown mutant.');
    const [old, changed, count] = mutants[values.mutant];
    assert.equal(source.split(old).length - 1, count, 'The mutation location must match.');
    source = source.replaceAll(old, changed);
  }
  const candidate = join(fixture, 'metrics.ts');
  writeFileSync(candidate, source, { flag: 'wx' });
  const { metricsSnapshot } = await import(pathToFileURL(candidate).href);
  db.exec(`CREATE TABLE tasks(id TEXT, data TEXT);
    CREATE TABLE launch_records(data TEXT);
    CREATE TABLE orchestration_events(seq INTEGER PRIMARY KEY, time TEXT, type TEXT, launch TEXT, task TEXT, data TEXT);
    CREATE TABLE events(seq INTEGER, time TEXT, type TEXT, task TEXT, details TEXT);
    CREATE TABLE user_inputs(task TEXT, data TEXT);`);
  const launch = (id, role, created, project = 'demo') => db.prepare('INSERT INTO launch_records VALUES (?)').run(JSON.stringify({
    id, project, role, created_at: created, task: null, cli: role === 'shell' ? null : 'Claude Code', model_requested: 'requested-must-not-be-observed',
  }));
  const event = (seq, time, type, id, data) => db.prepare('INSERT INTO orchestration_events VALUES (?,?,?,?,NULL,?)').run(seq, time, type, id, JSON.stringify(data));
  launch('claude', 'worker', '2026-01-01T00:00:00.000Z');
  launch('codex', 'reviewer', '2026-01-02T00:00:00.000Z');
  launch('zero', 'worker', '2026-01-02T00:00:00.000Z');
  launch('uncovered', 'shell', '2026-01-02T00:00:00.000Z');
  launch('foreign', 'worker', '2026-01-02T00:00:00.000Z', 'other');
  event(1, '2026-01-02T00:00:00.000Z', 'native_turn_facts', 'claude', { model: 'served-a', effort: 'high', prompt_id: 'first' });
  event(2, '2026-01-02T12:00:00.000Z', 'native_turn_facts', 'claude', { model: 'served-a', effort: 'high', prompt_id: 'second' });
  event(3, '2026-01-03T00:00:00.000Z', 'native_turn_facts', 'claude', { model: 'outside', effort: 'low', prompt_id: 'outside' });
  event(4, '2026-01-02T01:00:00.000Z', 'native_record', 'codex', { file: 'sessions/rollout-test.jsonl', offset: 123,
    record: { type: 'turn_context', payload: { model: 'served-b', reasoning_effort: 'medium' } } });
  event(5, '2026-01-03T00:00:00.000Z', 'native_turn_facts', 'zero', { model: 'outside', prompt_id: 'zero-outside' });
  event(6, '2026-01-02T01:00:00.000Z', 'native_turn_facts', 'foreign', { model: 'foreign-model' });
  event(100, '2026-01-02T00:00:00.000Z', 'role_requested', 'uncovered', { role_request: 'r1', role: 'executor', cli: 'claude' });
  event(101, '2026-01-02T00:00:01.000Z', 'role_request_decided', 'uncovered', { role_request: 'r1', approved: true });

  const result = metricsSnapshot(db, { project: 'demo', since: '2026-01-02T00:00:00.000Z', until: '2026-01-03T00:00:00.000Z' });
  report.snapshot = result;
  const sessions = Object.fromEntries(result.model_use.sessions.map(row => [row.launch, row]));
  check('no_source_is_unknown', sessions.uncovered.turns, null);
  check('verified_recorded_zero_is_distinct', sessions.zero.turns, 0);
  check('zero_does_not_invent_observed_model', sessions.zero.model, 'unknown');
  check('old_session_with_in_range_turns_is_included', sessions.claude.turns, 2);
  check('requested_model_is_not_observed', sessions.claude.model, 'served-a');
  check('codex_record_count', sessions.codex.turns, 1);
  check('claude_replay_sources', sessions.claude.turn_sources?.map(row => [row.sequence, row.in_range, row.prompt_id]), [[1, true, 'first'], [2, true, 'second'], [3, false, 'outside']]);
  check('codex_replay_source', sessions.codex.turn_sources?.map(row => [row.sequence, row.file, row.offset]), [[4, 'sessions/rollout-test.jsonl', 123]]);
  check('zero_has_excluded_source', sessions.zero.turn_sources?.map(row => [row.sequence, row.in_range]), [[5, false]]);
  check('no_cross_project_count', Object.keys(sessions).sort(), ['claude', 'codex', 'uncovered', 'zero']);
  const group = result.model_use.by_model.find(row => row.model === 'unknown');
  check('mixed_unknown_and_zero_group_remains_unknown', [group.turns, group.recorded_turns, group.uncovered_sessions, group.sessions], [null, 0, 1, 2]);
  check('counted_group_keeps_observed_total', result.model_use.by_model.find(row => row.model === 'served-a')?.turns, 2);
  check('scoring_contract_is_unchanged', result.first_time, { integrated: 0, first_time: 0, rate: null, rejections: {} });
  report.status = report.checks.every(row => row.status === 'PASS') ? 'PASS' : 'NO_GO';
} catch (error) {
  report.error = String(error.stack ?? error);
} finally {
  db.close();
  mkdirSync(dirname(resolve(values.summary)), { recursive: true });
  writeFileSync(values.summary, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
}
process.stdout.write(JSON.stringify({ status: report.status, summary: values.summary }) + '\n');
process.exitCode = report.status === 'PASS' ? 0 : 1;
