// F1–F12 are listed before implementation in T-223-evidence/FAILURE-MODES.md.
// Calendar oracles are hand-written, including gaps that cross the target date's midnight.
// Real Retrospectives.due(), in-memory SQLite; no daemon, CLI, PTY or model is started.
import assert from 'node:assert/strict';
import { writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { pathToFileURL } from 'node:url';

const [productArg, output, zone] = process.argv.slice(2);
assert(productArg && output && zone, 'usage: node test_t223_retrospective_due.ts PRODUCT OUTPUT.json ZONE');
assert.equal(process.env.TZ, zone, 'the requested case group must match explicit TZ');
assert.equal(process.env.TMPDIR, '/private/tmp');
const product = resolve(productArg);
const { Retrospectives } = await import(pathToFileURL(join(product, 'workbench/src/retrospective.ts')).href);
type Stored = { project: string; scheduled_for: string | null };
type Case = { name: string; now: string; expected: string | null; weekday?: number; hour?: number; minute?: number;
  effective?: string; enabled?: boolean; stored?: Stored[] };
const newYorkCases: Case[] = [
  { name: 'F1/spring-query-for-earlier-Monday', now: '2026-03-08T12:00:00-04:00', expected: '2026-03-02T07:30:00.000Z' },
  // Gap 02:30 is interpreted with the pre-transition offset: 03:30 EDT = 07:30Z.
  { name: 'F2/gap-target-at-normalized-slot', weekday: 0, now: '2026-03-08T03:30:00-04:00', expected: '2026-03-08T07:30:00.000Z' },
  { name: 'F2/gap-target-from-next-day', weekday: 0, now: '2026-03-09T12:00:00-04:00', expected: '2026-03-08T07:30:00.000Z' },
  { name: 'F3/previous-week-is-gap-day', weekday: 0, now: '2026-03-15T01:30:00-04:00', expected: '2026-03-08T07:30:00.000Z' },
  // A normalized 03:30 must not be carried to the ordinary Sunday one week earlier.
  { name: 'F4/gap-query-before-normalized-slot', weekday: 0, now: '2026-03-08T03:00:00-04:00', expected: '2026-03-01T07:30:00.000Z' },
  { name: 'F4/one-ms-before-normalized-slot', weekday: 0, now: '2026-03-08T03:29:59.999-04:00', expected: '2026-03-01T07:30:00.000Z' },
  // Repeated 01:30 is the first occurrence, EDT: 05:30Z, never the second at 06:30Z.
  { name: 'F5/first-overlap-occurrence', weekday: 0, hour: 1, now: '2026-11-01T01:30:00-04:00', expected: '2026-11-01T05:30:00.000Z' },
  { name: 'F5/between-overlap-occurrences', weekday: 0, hour: 1, now: '2026-11-01T01:15:00-05:00', expected: '2026-11-01T05:30:00.000Z' },
  { name: 'F5/after-overlap', weekday: 0, hour: 1, now: '2026-11-01T02:00:00-05:00', expected: '2026-11-01T05:30:00.000Z' },
  { name: 'F5/before-first-overlap', weekday: 0, hour: 1, now: '2026-11-01T01:29:59.999-04:00', expected: '2026-10-25T05:30:00.000Z' },
  { name: 'F6/ordinary-summer-day', now: '2026-03-16T12:00:00-04:00', expected: '2026-03-16T06:30:00.000Z' },
  { name: 'F6/ordinary-winter-day', now: '2026-12-14T12:00:00-05:00', expected: '2026-12-14T07:30:00.000Z' },
  { name: 'F7/month-boundary', now: '2026-04-01T12:00:00-04:00', expected: '2026-03-30T06:30:00.000Z' },
  { name: 'F8/year-boundary', now: '2027-01-01T12:00:00-05:00', expected: '2026-12-28T07:30:00.000Z' },
  { name: 'F9/effective-exactly-at-slot', effective: '2026-03-02T07:30:00.000Z', now: '2026-03-02T12:00:00-05:00', expected: '2026-03-02T07:30:00.000Z' },
  { name: 'F9/effective-one-ms-after-slot', effective: '2026-03-02T07:30:00.001Z', now: '2026-03-02T12:00:00-05:00', expected: null },
  { name: 'F10/before-slot', now: '2026-03-16T02:29:59.999-04:00', expected: '2026-03-09T06:30:00.000Z' },
  { name: 'F10/exact-slot', now: '2026-03-16T02:30:00-04:00', expected: '2026-03-16T06:30:00.000Z' },
  { name: 'F10/one-ms-after-slot', now: '2026-03-16T02:30:00.001-04:00', expected: '2026-03-16T06:30:00.000Z' },
  { name: 'F10/disabled', enabled: false, now: '2026-03-16T12:00:00-04:00', expected: null },
  { name: 'F11/already-ran-same-project', now: '2026-03-08T12:00:00-04:00', expected: null,
    stored: [{ project: 'demo', scheduled_for: '2026-03-02T07:30:00.000Z' }] },
  { name: 'F11/other-project-does-not-block', now: '2026-03-08T12:00:00-04:00', expected: '2026-03-02T07:30:00.000Z',
    stored: [{ project: 'other', scheduled_for: '2026-03-02T07:30:00.000Z' }] },
  { name: 'F11/manual-run-does-not-block', now: '2026-03-08T12:00:00-04:00', expected: '2026-03-02T07:30:00.000Z',
    stored: [{ project: 'demo', scheduled_for: null }] },
  { name: 'F11/other-week-does-not-block', now: '2026-03-16T12:00:00-04:00', expected: '2026-03-16T06:30:00.000Z',
    stored: [{ project: 'demo', scheduled_for: '2026-03-09T06:30:00.000Z' }] },
  { name: 'F11/second-overlap-does-not-rerun', weekday: 0, hour: 1, now: '2026-11-01T01:30:00-05:00', expected: null,
    stored: [{ project: 'demo', scheduled_for: '2026-11-01T05:30:00.000Z' }] },
  { name: 'F11/gap-target-does-not-rerun-next-day', weekday: 0, now: '2026-03-09T12:00:00-04:00', expected: null,
    stored: [{ project: 'demo', scheduled_for: '2026-03-08T07:30:00.000Z' }] },
];
// Nuuk and Scoresbysund skip Saturday 23:00 (-02) through Sunday 00:00 (-01).
// Saturday 10:00 is still -02: add 2 hours => March 28 12:00Z.
// Missing March 28 23:30 uses -02: March 29 01:30Z = Sunday 00:30 at -01.
// Before that instant, March 21 23:30 at -02 => March 22 01:30Z.
// The next Saturday April 4 23:30 at -01 => April 5 00:30Z.
const midnightGapCases: Case[] = [
  { name: 'F12/sunday-late-query', now: '2026-03-29T23:30:00-01:00', expected: '2026-03-28T12:00:00.000Z' },
  { name: 'F12/thursday-late-query', now: '2026-04-02T23:30:00-01:00', expected: '2026-03-28T12:00:00.000Z' },
  { name: 'F12/already-ran-Saturday', now: '2026-03-29T23:30:00-01:00', expected: null,
    stored: [{ project: 'demo', scheduled_for: '2026-03-28T12:00:00.000Z' }] },
  { name: 'F12/Saturday-query-control', now: '2026-03-28T10:30:00-02:00', expected: '2026-03-28T12:00:00.000Z' },
  { name: 'F12/gap-target-after-normalized-slot', hour: 23, minute: 30, now: '2026-03-29T12:00:00-01:00', expected: '2026-03-29T01:30:00.000Z' },
  { name: 'F12/before-normalized-slot', hour: 23, minute: 30, now: '2026-03-29T00:15:00-01:00', expected: '2026-03-22T01:30:00.000Z' },
  { name: 'F12/exact-normalized-slot', hour: 23, minute: 30, now: '2026-03-29T00:30:00-01:00', expected: '2026-03-29T01:30:00.000Z' },
  { name: 'F12/next-week-before-slot', hour: 23, minute: 30, now: '2026-04-04T23:29:59.999-01:00', expected: '2026-03-29T01:30:00.000Z' },
  { name: 'F12/next-week-exact-slot', hour: 23, minute: 30, now: '2026-04-04T23:30:00-01:00', expected: '2026-04-05T00:30:00.000Z' },
  { name: 'F12/gap-target-already-ran', hour: 23, minute: 30, now: '2026-03-29T12:00:00-01:00', expected: null,
    stored: [{ project: 'demo', scheduled_for: '2026-03-29T01:30:00.000Z' }] },
  { name: 'F12/2027-sunday-late-query', now: '2027-03-28T23:30:00-01:00', expected: '2027-03-27T12:00:00.000Z' },
  // Previous Saturday March 20 23:30 at -02 => March 21 01:30Z.
  { name: 'F12/2027-before-normalized-slot', hour: 23, minute: 30, now: '2027-03-28T00:15:00-01:00', expected: '2027-03-21T01:30:00.000Z' },
];
const groups = {
  'America/New_York': { cases: newYorkCases, weekday: 1, hour: 2, minute: 30, effective: '2026-03-01T00:00:00-05:00' },
  'America/Nuuk': { cases: midnightGapCases, weekday: 6, hour: 10, minute: 0, effective: '2026-03-01T00:00:00-02:00' },
  'America/Scoresbysund': { cases: midnightGapCases, weekday: 6, hour: 10, minute: 0, effective: '2026-03-01T00:00:00-02:00' },
};
assert(Object.hasOwn(groups, zone), `unsupported case group: ${zone}`);
const group = groups[zone as keyof typeof groups];
const cases = group.cases;
const results = [];
for (const c of cases) {
  const db = new DatabaseSync(':memory:');
  try {
    const retrospectives = new Retrospectives(db, '/private/tmp/t223-unused-no-files');
    retrospectives.saveSchedule({ enabled: c.enabled ?? true, weekday: c.weekday ?? group.weekday,
      hour: c.hour ?? group.hour, minute: c.minute ?? group.minute }, new Date(c.effective ?? group.effective));
    for (const [index, stored] of (c.stored ?? []).entries()) {
      // Only persisted run data: prepare() would also build a package, unrelated to due().
      const run = { id: `stored-${index}`, project: stored.project, repo: '/private/tmp/t223-unused-no-files',
        trigger: stored.scheduled_for === null ? 'manual' : 'schedule', scheduled_for: stored.scheduled_for,
        since: null, until: '2026-03-01T00:00:00.000Z', created_at: '2026-03-01T00:00:00.000Z',
        cli: 'Claude Code', model: 'unused', effort: 'low', dir: '', package: '', out: '' };
      db.prepare('INSERT INTO retrospective_runs(id,project,data) VALUES (?,?,?)').run(run.id, run.project, JSON.stringify(run));
    }
    const now = new Date(c.now), originalNow = now.toISOString();
    const actual = retrospectives.due('demo', now);
    assert.equal(actual, c.expected, c.name);
    assert.equal(now.toISOString(), originalNow, `${c.name}: must not mutate the caller's clock`);
    results.push({ name: c.name, pass: true, actual });
  } catch (error) {
    results.push({ name: c.name, pass: false, error: String(error), stack: error.stack, actual: error.actual, expected: error.expected });
  } finally { db.close(); }
}
const pass = results.every(row => row.pass);
const report = { status: pass ? 'PASS' : 'INCOMPLETE', product, argv: process.argv, node: process.version,
  TZ: process.env.TZ, TMPDIR: process.env.TMPDIR, group: zone, cases, results };
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ status: report.status, total: results.length, failed: results.filter(row => !row.pass) }, null, 2));
process.exitCode = pass ? 0 : 1;
