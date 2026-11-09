// T-269: time the store's lookups on a copy of the live state file, old way and new way side by side.
// Usage: ELECTRON_RUN_AS_NODE=1 /Applications/Enchanted.app/Contents/MacOS/Enchanted time_live_copy.mjs <dir holding state.sqlite3 copy>
// The copy is made with `sqlite3 "file:<live>?mode=ro" ".backup <dir>/state.sqlite3"` and deleted after the run.
import { DatabaseSync } from 'node:sqlite';
import { join } from 'node:path';
import { OrchestrationStore } from '../../../workbench/src/store.ts';
import { RoleRequests } from '../../../workbench/src/roleRequests.ts';
import { TrajectoryArchive } from '../../../workbench/src/trajectoryArchive.ts';

const root = process.argv[2];
const time = (fn, n = 3) => { const start = performance.now(); for (let i = 0; i < n; i++) fn(); return +((performance.now() - start) / n).toFixed(2); };
// Before the store adds its indexes: the same lookups on the unindexed file.
const raw = new DatabaseSync(join(root, 'state.sqlite3'));
const before = {
  indexes: raw.prepare("SELECT count(*) AS n FROM sqlite_master WHERE type='index' AND tbl_name='orchestration_events' AND sql IS NOT NULL").get().n,
  rows: Number(raw.prepare('SELECT count(*) AS n FROM orchestration_events').get().n),
};
const busiest = String(raw.prepare('SELECT launch, count(*) AS n FROM orchestration_events WHERE launch IS NOT NULL GROUP BY launch ORDER BY n DESC LIMIT 1').get().launch);
before.lastEvent_miss_ms = time(() => raw.prepare("SELECT seq FROM orchestration_events WHERE launch=? AND type IN ('shell_closed') ORDER BY seq DESC LIMIT 1").get('none'));
before.read_all_then_filter_busiest_launch_ms = time(() => raw.prepare('SELECT * FROM orchestration_events ORDER BY seq').all()
  .map(({ data, ...row }) => ({ ...row, data: JSON.parse(String(data)) })).filter(event => event.launch === busiest).length, 2);
raw.close();

let start = performance.now();
const store = new OrchestrationStore(root);
const after = { first_open_ms: +(performance.now() - start).toFixed(0) };
const archive = new TrajectoryArchive(store.db, root, () => {});
after.lastEvent_miss_ms = time(() => store.lastEvent('none', ['shell_closed']));
after.launchEvents_busiest_launch_ms = time(() => store.launchEvents(busiest).length);
after.busiest_launch_rows = store.launchEvents(busiest).length;
after.roleRequests_all_ms = time(() => new RoleRequests(store, () => true).all());
after.archive_sources_ms = time(() => archive.sources(), 2);
after.openPanes_ms = time(() => store.openPanes());
store.db.close();
start = performance.now();
new OrchestrationStore(root).db.close();
after.second_open_ms = +(performance.now() - start).toFixed(0);
console.log(JSON.stringify({ time: new Date().toISOString(), before, after }, null, 2));
