// Controller probe: Saturday 10:00 schedule in America/Nuuk, queried at 23:30 local in the week after the
// 2026-03-28 23:00 -02 -> 2026-03-29 00:00 -01 gap. Hand oracle: Saturday 2026-03-28 10:00 at -02 = 12:00Z.
import { DatabaseSync } from 'node:sqlite';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const product = resolve(process.argv[2]);
const { Retrospectives } = await import(pathToFileURL(join(product, 'workbench/src/retrospective.ts')).href);
const cases = [
  { now: '2026-03-28T10:30:00-02:00', expected: '2026-03-28T12:00:00.000Z' },
  { now: '2026-03-29T23:30:00-01:00', expected: '2026-03-28T12:00:00.000Z' },
  { now: '2026-04-02T23:30:00-01:00', expected: '2026-03-28T12:00:00.000Z' },
  { now: '2026-04-03T22:30:00-01:00', expected: '2026-03-28T12:00:00.000Z' },
];
let failed = 0;
for (const c of cases) {
  const db = new DatabaseSync(':memory:');
  const r = new Retrospectives(db, '/private/tmp/t223-unused-no-files');
  r.saveSchedule({ enabled: true, weekday: 6, hour: 10, minute: 0 }, new Date('2026-03-01T00:00:00-02:00'));
  const actual = r.due('demo', new Date(c.now));
  const ok = actual === c.expected; if (!ok) failed++;
  console.log(JSON.stringify({ TZ: process.env.TZ, now: c.now, expected: c.expected, actual, ok }));
  db.close();
}
process.exitCode = failed ? 1 : 0;
