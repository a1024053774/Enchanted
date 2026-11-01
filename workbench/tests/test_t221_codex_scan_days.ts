// Calendar oracles are hand-written from T-221, including every intervening local date.
// Real product calculations and filesystem consumers; no CLI, process, PTY or model is started.
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, utimesSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [productArg, output] = process.argv.slice(2);
assert(productArg && output, 'usage: node test_t221_codex_scan_days.ts PRODUCT OUTPUT.json');
assert.equal(process.env.TZ, 'America/New_York');
assert.equal(process.env.TMPDIR, '/private/tmp');
const product = resolve(productArg);
const load = (file: string) => import(pathToFileURL(join(product, 'workbench/src', file)).href);
const { codexScanDays } = await load('codexScanDays.ts');
const { nativeLink } = await load('nativeLink.ts');
const { TrajectoryArchive } = await load('trajectoryArchive.ts');
const { Panes } = await load('panes.ts');
const { OrchestrationStore } = await load('store.ts');
const cases = [
  { name: 'fall-T219-evening', since: '2026-10-30T22:34:14-04:00', now: '2026-10-31T22:35:14-04:00',
    days: ['2026/10/30', '2026/10/31', '2026/11/01'],
    archive: ['2026/10/29', '2026/10/30', '2026/10/31', '2026/11/01'], before: '2026/10/28', after: '2026/11/02' },
  { name: 'fall-T219-exact-launch', since: '2026-10-31T22:34:14-04:00', now: '2026-10-31T22:35:14-04:00',
    days: ['2026/10/31', '2026/11/01'],
    archive: ['2026/10/30', '2026/10/31', '2026/11/01'], before: '2026/10/29', after: '2026/11/02' },
  { name: 'spring', since: '2026-03-06T23:55:00-05:00', now: '2026-03-08T00:05:00-05:00',
    days: ['2026/03/06', '2026/03/07', '2026/03/08', '2026/03/09'],
    archive: ['2026/03/05', '2026/03/06', '2026/03/07', '2026/03/08', '2026/03/09'], before: '2026/03/04', after: '2026/03/10' },
  { name: 'fall-day-evening', since: '2026-11-01T00:15:00-04:00', now: '2026-11-01T22:35:00-05:00',
    days: ['2026/11/01', '2026/11/02'],
    archive: ['2026/10/31', '2026/11/01', '2026/11/02'], before: '2026/10/30', after: '2026/11/03' },
  { name: 'month-end', since: '2026-04-29T23:55:00-04:00', now: '2026-04-30T00:05:00-04:00',
    days: ['2026/04/29', '2026/04/30', '2026/05/01'],
    archive: ['2026/04/28', '2026/04/29', '2026/04/30', '2026/05/01'], before: '2026/04/27', after: '2026/05/02' },
  { name: 'year-end', since: '2026-12-30T23:55:00-05:00', now: '2026-12-31T00:05:00-05:00',
    days: ['2026/12/30', '2026/12/31', '2027/01/01'],
    archive: ['2026/12/29', '2026/12/30', '2026/12/31', '2027/01/01'], before: '2026/12/28', after: '2027/01/02' },
  { name: 'spring-previous-local-day', since: '2026-03-09T00:15:00-04:00', now: '2026-03-09T00:16:00-04:00',
    days: ['2026/03/09', '2026/03/10'],
    archive: ['2026/03/08', '2026/03/09', '2026/03/10'], before: '2026/03/07', after: '2026/03/11' },
  { name: 'fall-previous-local-day', since: '2026-11-01T23:30:00-05:00', now: '2026-11-01T23:31:00-05:00',
    days: ['2026/11/01', '2026/11/02'],
    archive: ['2026/10/31', '2026/11/01', '2026/11/02'], before: '2026/10/30', after: '2026/11/03' },
];
const root = mkdtempSync('/private/tmp/t221-days-');
const results: any[] = [];
function check(name: string, run: () => unknown) {
  try { results.push({ name, pass: true, observed: run() }); }
  catch (error) { results.push({ name, pass: false, error: String(error), actual: error.actual, expected: error.expected }); }
}
const localDate = (day: Date) => [day.getFullYear(), String(day.getMonth() + 1).padStart(2, '0'), String(day.getDate()).padStart(2, '0')].join('/');
const realNow = Date.now;
try {
  for (const c of cases) {
    const since = Date.parse(c.since), now = Date.parse(c.now);
    Date.now = () => now; // Inject the clock used by every real consumer, without changing Date constructors.
    for (const [offset, expected] of [[0, c.days], [-1, c.archive]] as const) {
      check(`${c.name}/range/${offset}`, () => {
        const actual = [...codexScanDays(since, now, offset)].map(localDate);
        assert.deepEqual(actual, expected);
        return actual;
      });
    }
    // One file at a time makes every date observable; excluded dates catch over-scanning too.
    for (const date of [c.before, ...c.archive, c.after]) {
      const dir = join(root, c.name, date.replaceAll('/', '-'));
      mkdirSync(dir, { recursive: true });
      const home = join(dir, 'home'), workspace = join(dir, 'workspace');
      const file = join(home, 'sessions', date, 'rollout-other.jsonl');
      mkdirSync(join(home, 'sessions', date), { recursive: true });
      writeFileSync(file, JSON.stringify({ type: 'session_meta', payload: { id: 'other', source: 'cli', cwd: workspace } }) + '\n');
      utimesSync(file, new Date(now), new Date(now));
      const bound = join(dir, 'rollout-bound.jsonl');
      writeFileSync(bound, 'bound record\n');
      const store = new OrchestrationStore(dir);
      const record = { id: 'managed', cli: 'Codex', role: 'worker', task: null, attempt: null, worktree: workspace,
        created_at: c.since, argv: ['/fixture/codex', '-a', 'never'], env: { CODEX_HOME: home } };
      store.launch(record);
      store.event('pane_native_session', { native_session: 'bound' }, record);
      // Public archive.sources paths: role approval by session id and retrospective by working directory.
      // Request/start timestamps, rather than insertion wall time, define the archive's scan start.
      store.db.prepare("INSERT INTO orchestration_events(time,type,launch,data) VALUES (?,?,?,?)")
        .run(c.since, 'role_requested', 'controller', JSON.stringify({ role_request: 'request-at-start', cli: 'codex', native_session: 'other', native_home: home }));
      store.event('role_request_decided', { role_request: 'request-at-start', approved: true });
      store.db.prepare("INSERT INTO orchestration_events(time,type,launch,data) VALUES (?,?,?,?)")
        .run(c.since, 'retrospective_started', 'retro-at-start', JSON.stringify({ cli: 'Codex', native_home: home, out: workspace }));
      try {
        check(`${c.name}/nativeLink/${date}`, () => {
          const link = nativeLink(store.db, dir, { sources: () => [{ launch: record.id, path: bound }] }, record.id, home, null);
          assert.equal(link.available, !c.days.includes(date), JSON.stringify(link));
          if (!link.available) assert.match(link.reason, /新线程 other/);
          return link;
        });
        check(`${c.name}/panes/${date}`, () => {
          const pane: any = { record, attempt: { workspace }, offsets: new Map(), native: null };
          mkdirSync(join(dir, 'traces', record.id), { recursive: true });
          new Panes(dir, store, {}, reason => { throw new Error(reason); }).scan(pane);
          assert.equal(pane.native, c.days.includes(date) ? 'other' : null);
          assert.deepEqual([...pane.offsets.keys()], c.days.includes(date) ? [file] : []);
          return pane.native;
        });
        const archive = new TrajectoryArchive(store.db, dir, () => {});
        for (const launch of ['controller', 'retro-at-start']) {
          check(`${c.name}/archive-${launch}/${date}`, () => {
            const paths = archive.sources(launch).map(source => source.path);
            assert.deepEqual(paths, c.archive.includes(date) ? [file] : []);
            return paths;
          });
        }
      } finally { store.close(); }
    }
  }
} finally { Date.now = realNow; }
const pass = results.every(row => row.pass);
writeFileSync(output, JSON.stringify({ status: pass ? 'PASS' : 'INCOMPLETE', product, root, argv: process.argv,
  TZ: process.env.TZ, cases, results }, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ status: pass ? 'PASS' : 'INCOMPLETE', total: results.length, failed: results.filter(row => !row.pass) }, null, 2));
process.exitCode = pass ? 0 : 1;
