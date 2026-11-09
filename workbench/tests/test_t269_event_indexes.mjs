// T-269: the daemon's event lookups must not read the whole orchestration event table.
// Failure modes this checks:
// 1. A new state file gets no index, so lookups by launch or type scan the whole table.
// 2. A state file written by an older version (rows, no indexes) is opened and stays unindexed.
// 3. Only one of the two indexes exists, or its columns are wrong, so by-launch lookups narrow by type only
//    (T-269 review 01 #1).
// 4. A query walks the whole table through an index (`SCAN … USING INDEX`) and is still counted as indexed
//    (T-269 review 01 #2).
// 5. A caller still reads every event and filters one launch in JavaScript (read().filter(launch)): 1.4 s per call
//    on the 2026-11-09 state, on hook and per-second snapshot paths (T-269 review 01 #5).
// 6. The launch read returns other rows, misses rows, loses seq order or leaves data unparsed.
// 7. Adding the indexes changes rows or drops the append-only triggers.
// 8. Opening the same file again (the next daemon start) fails because the indexes exist.
// The queries are the ones the real store, role requests and trajectory archive issue; the test records them
// through the store's own connection instead of copying their SQL.
import { DatabaseSync } from 'node:sqlite';
import { mkdtempSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import assert from 'node:assert/strict';
import { OrchestrationStore } from '../src/store.ts';
import { RoleRequests } from '../src/roleRequests.ts';
import { TrajectoryArchive } from '../src/trajectoryArchive.ts';

const [out] = process.argv.slice(2);
assert(out && !existsSync(out), 'New summary path required');
const source = new URL('../src/', import.meta.url);
const report = { status: 'INCOMPLETE', argv: process.argv, checks: [],
  scope: 'Real OrchestrationStore, RoleRequests and TrajectoryArchive on a fixture state file; query plans, launch read results and a source scan of workbench/src; no timing claim' };
const root = mkdtempSync('/private/tmp/t269-event-indexes-');
// A failed check is recorded and the run goes on, so a red run shows every query that scans.
const check = (name, fn) => {
  try { fn(); report.checks.push({ name, ok: true }); }
  catch (error) { report.checks.push({ name, ok: false, error: String(error?.message ?? error) }); }
};
const indexColumns = (db) => Object.fromEntries(db.prepare("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='orchestration_events' AND sql IS NOT NULL ORDER BY name").all()
  .map(row => [String(row.name), db.prepare(`PRAGMA index_info(${JSON.stringify(String(row.name))})`).all().sort((a, b) => Number(a.seqno) - Number(b.seqno)).map(column => String(column.name))]));
try {
  // An older state file: the table and its triggers as earlier versions created them, with rows in it.
  // Row i has seq i + 1 and launch `launch-${i % 40}`, so each launch's rows are known without the store.
  const old = new DatabaseSync(join(root, 'state.sqlite3'));
  old.exec(`CREATE TABLE orchestration_events (seq INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL, type TEXT NOT NULL, launch TEXT, task TEXT, attempt TEXT, data TEXT NOT NULL);
    CREATE TRIGGER orchestration_events_no_update BEFORE UPDATE ON orchestration_events BEGIN SELECT RAISE(ABORT,'append only'); END;
    CREATE TRIGGER orchestration_events_no_delete BEFORE DELETE ON orchestration_events BEGIN SELECT RAISE(ABORT,'append only'); END;`);
  const insert = old.prepare('INSERT INTO orchestration_events(time,type,launch,task,attempt,data) VALUES (?,?,?,?,?,?)');
  const types = ['request_received', 'request_result', 'native_record', 'hook_received', 'turn_submitted', 'pane_started'];
  const rows = 3000;
  for (let i = 0; i < rows; i++)
    insert.run(new Date(Date.UTC(2026, 10, 9, 0, 0, i)).toISOString(), types[i % types.length], `launch-${i % 40}`, null, null,
      JSON.stringify({ i, file: 'sessions/x.jsonl', raw_stdin: '{}' }));
  insert.run('2026-11-09T01:00:00.000Z', 'role_requested', 'shell-1', null, null,
    JSON.stringify({ role_request: 'rr-1', project: 'demo', role: 'executor', cli: 'codex', native_session: 's-1', native_home: join(root, 'codex-home') }));
  insert.run('2026-11-09T01:00:01.000Z', 'role_request_decided', 'shell-1', null, null, JSON.stringify({ role_request: 'rr-1', approved: true }));
  const rowsBefore = Number(old.prepare('SELECT count(*) AS n FROM orchestration_events').get().n);
  old.close();

  const store = new OrchestrationStore(root);
  store.launch({ id: 'launch-1', task: 'demo+T-1', attempt: 'a1', role: 'worker', cli: 'Codex', env: { CODEX_HOME: join(root, 'codex-home') } });
  store.launch({ id: 'launch-2', task: 'demo+T-1', attempt: 'a1', role: 'reviewer', cli: 'Claude Code', native_session: 'n-2' });
  mkdirSync(join(root, 'codex-home'), { recursive: true });

  check('old file opened: rows unchanged, triggers kept', () => {
    assert.equal(Number(store.db.prepare('SELECT count(*) AS n FROM orchestration_events').get().n), rowsBefore);
    assert.throws(() => store.db.exec("UPDATE orchestration_events SET type='x' WHERE seq=1"), /append only/);
    assert.throws(() => store.db.exec('DELETE FROM orchestration_events WHERE seq=1'), /append only/);
  });
  report.indexes = indexColumns(store.db);
  check('old file opened: indexes on (launch, type) and on (type)', () => {
    const shapes = Object.values(report.indexes).map(columns => columns.join(','));
    assert(shapes.includes('launch,type'), `no (launch, type) index: ${JSON.stringify(report.indexes)}`);
    assert(shapes.includes('type'), `no (type) index: ${JSON.stringify(report.indexes)}`);
  });

  check('launch read returns exactly that launch, in seq order, data parsed', () => {
    const expected = Array.from({ length: rows }, (_, i) => i).filter(i => i % 40 === 7).map(i => i + 1);
    const events = store.launchEvents('launch-7');
    assert.deepEqual(events.map(event => Number(event.seq)), expected);
    assert(events.every(event => event.launch === 'launch-7' && event.data.i === Number(event.seq) - 1));
    assert.deepEqual(store.launchEvents('launch-none'), []);
  });

  // Record the SQL the real lookups prepare on the store's connection.
  const seen = [];
  const prepare = store.db.prepare.bind(store.db);
  store.db.prepare = (sql) => { seen.push(sql); return prepare(sql); };
  const archive = new TrajectoryArchive(store.db, root, () => {});
  store.lastEvent('launch-1', ['shell_closed']);
  store.lastEvent('launch-1', ['turn_submitted', 'turn_start_signal']);
  // The parent revision has no launch read; its red run still records and judges the other lookups.
  if (typeof store.launchEvents === 'function') store.launchEvents('launch-1');
  new RoleRequests(store, () => true).all();
  archive.sources();
  store.openPanes('demo+T-1');
  store.hasPaneLayout('demo+T-1');
  store.executionSelection('worker');
  store.workBranchPrefix();
  store.db.prepare = prepare;
  const queries = [...new Set(seen)].filter(sql => /\bFROM\s+orchestration_events\b/i.test(sql) && /^\s*SELECT/i.test(sql));
  report.plans = queries.map(sql => ({ sql: sql.replace(/\s+/g, ' ').trim(),
    plan: store.db.prepare('EXPLAIN QUERY PLAN ' + sql).all().map(row => String(row.detail)) }));
  check('real lookups were recorded', () => assert(report.plans.length >= 7, `only ${report.plans.length} event queries recorded`));
  const clause = new Set(['WHERE', 'ORDER', 'GROUP', 'LIMIT', 'LEFT', 'JOIN', 'INNER', 'ON', 'UNION']);
  for (const { sql, plan } of report.plans)
    check(`no walk over the whole table: ${sql.slice(0, 90)}`, () => {
      // A join names the table by an alias (`orchestration_events e`); the plan then says `SCAN e`. A SCAN through an
      // index still visits every row, so only SEARCH counts.
      const names = ['orchestration_events', ...[...sql.matchAll(/orchestration_events\s+(?:AS\s+)?([A-Za-z_]\w*)/gi)]
        .map(match => match[1]).filter(word => !clause.has(word.toUpperCase()))];
      const scans = plan.filter(detail => names.some(name => new RegExp(`^SCAN ${name}\\b`).test(detail)));
      assert.deepEqual(scans, [], `${sql}\n${plan.join('\n')}`);
      // A lookup by launch must narrow by launch, not by type alone.
      if (/\blaunch\s*=\s*\?/.test(sql)) assert(plan.some(detail => /\(launch=\?/.test(detail)), `${sql}\n${plan.join('\n')}`);
    });

  check('no caller reads every event to pick one launch', () => {
    const offenders = [];
    for (const name of readdirSync(source, { recursive: true }).filter(name => String(name).endsWith('.ts'))) {
      const text = readFileSync(new URL(String(name), source), 'utf8');
      for (const match of text.matchAll(/\.read\(\)\.filter\(\s*\(?\s*(\w+)\s*\)?\s*=>\s*\1\.launch\s*===/g))
        offenders.push(`${name}:${text.slice(0, match.index).split('\n').length}`);
    }
    assert.deepEqual(offenders, []);
  });

  store.db.close();
  const again = new OrchestrationStore(root);
  check('second open keeps the same indexes', () => assert.deepEqual(indexColumns(again.db), report.indexes));
  again.db.close();

  const fresh = mkdtempSync('/private/tmp/t269-event-indexes-new-');
  try {
    const created = new OrchestrationStore(fresh);
    const columns = indexColumns(created.db);
    created.db.close();
    check('new file gets the same indexes', () => assert.deepEqual(columns, report.indexes));
  } finally { rmSync(fresh, { recursive: true, force: true }); }
  report.status = report.checks.every(entry => entry.ok) ? 'PASS' : 'FAIL';
} catch (error) {
  report.status = 'FAIL';
  report.error = String(error?.stack ?? error);
} finally {
  rmSync(root, { recursive: true, force: true });
  writeFileSync(out, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ status: report.status, checks: report.checks.length, indexes: report.indexes ?? null,
    failed: report.checks.filter(entry => !entry.ok).map(entry => entry.name),
    error: report.error ? report.error.split('\n').slice(0, 6).join('\n') : undefined }, null, 1));
  process.exitCode = report.status === 'PASS' ? 0 : 1;
}
