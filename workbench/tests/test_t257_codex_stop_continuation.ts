// T-257 isolated ordering check. Oracle: ticket Acceptance and recovery-v2.md.
// Failure modes fixed BEFORE implementation: a claimed UPS leaves nativeTurn null;
// scan/UPS order loses the binding; stale/foreign/child hooks acquire the submission;
// duplicate Stops transfer twice; an interrupt is cleared; completion without a
// matched Stop releases a submission. Real Panes/Store/rollout scanning are used.
// Terminal/process I/O is absent here. This does NOT prove real CLI timing, gate
// reclaim, attempt/fence/CAS or queue delivery; the Python E2E must prove those.
// node this-file.ts <product-source-root> <new-summary.json>
import assert from 'node:assert/strict';
import { appendFileSync, mkdirSync, mkdtempSync, readdirSync, lstatSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [sourceArg, summaryArg] = process.argv.slice(2);
const source = resolve(sourceArg), summary = resolve(summaryArg);
writeFileSync(summary, JSON.stringify({ status: 'INCOMPLETE', source }) + '\n', { flag: 'wx' });
const { Panes } = await import(pathToFileURL(join(source, 'workbench/src/panes.ts')).href);
const { OrchestrationStore } = await import(pathToFileURL(join(source, 'workbench/src/store.ts')).href);
const fixture = mkdtempSync(join(dirname(summary), 't257-module-'));
const results: any[] = [];
const originalAt = '2026-11-08T00:00:00Z', submittedAt = '2026-11-08T00:01:00Z';
const currentAt = '2026-11-08T00:01:01Z', staleAt = '2026-11-08T00:00:59Z';
let cases = 0;
function setup() {
  const root = join(fixture, String(++cases)); mkdirSync(root);
  const store = new OrchestrationStore(root);
  // No terminal I/O in this unit check: the constructor creates a private hc
  // socket directory. Use the real prototype without initializing that boundary.
  const host = Object.assign(Object.create(Panes.prototype), { root, store, config: {}, panes: new Map(),
    onEventWriteFailed: (reason: string) => { throw new Error(reason); } });
  const record = { id: 'launch', thread: 'thread', task: 'demo+T-257', role: 'worker', cli: 'Codex',
    worktree: root, attempt: 'attempt', session: 'managed-session', fence: 2, spec_rev: 2, env: { CODEX_HOME: root }, created_at: originalAt };
  store.launch(record);
  const dispatch = store.register(record.id, 'receipt', 'gate');
  store.event('paste_intent', { dispatch: dispatch.id, text: dispatch.text }, record);
  const active = { id: 'receipt-submission', dispatch: dispatch.id, at: submittedAt, nativeTurn: null };
  store.event('turn_submitted', active, record);
  const native = '11111111-1111-4111-8111-111111111111';
  const file = join(root, `rollout-2026-11-08T00-00-00-${native}.jsonl`);
  const meta = JSON.stringify({ type: 'session_meta', payload: { id: native, cwd: root, source: 'cli' } }) + '\n';
  writeFileSync(file, meta);
  mkdirSync(join(root, 'traces', record.id), { recursive: true });
  const pane: any = { record, attempt: { workspace: root }, native, nativeFile: file, offsets: new Map([[file, Buffer.byteLength(meta)]]),
    state: 'busy', active, turn: 'same-turn', failed: null, stopped: false, archived: false, nativeEnded: false,
    interrupted: false, interruption: null, stopInProgress: false, writing: false, queue: [], inputGeneration: 0, submitGeneration: 0,
    pty: { pid: 1, cols: 80, rows: 24 }, model: 'unknown', effort: 'unknown' };
  host.panes.set(record.thread, pane);
  host.recordUserSubmission = () => {}; // persistence boundary; dispatch provenance itself is real Store SQL.
  const envelope = (kind: string, extra: any = {}) => ({ hook_event_name: kind, session_id: native,
    turn_id: 'same-turn', cwd: root, transcript_path: file, ...extra });
  const signal = (kind: string, extra: any = {}, at = currentAt, transfer?: any) =>
    host.signal(record.id, JSON.stringify(envelope(kind, extra)), at, transfer);
  const scan = (type: string) => {
    appendFileSync(file, JSON.stringify({ type: 'event_msg', timestamp: currentAt, payload: { type, turn_id: 'same-turn' } }) + '\n');
    (host as any).scan(pane);
  };
  return { store, host, pane, active, dispatch, signal, scan };
}
async function run(name: string, sequence: string[], body: (f: ReturnType<typeof setup>) => Promise<void>, seed?: number) {
  const f = setup();
  try { await body(f); results.push({ name, seed, sequence, status: 'PASS' }); }
  catch (error) { results.push({ name, seed, sequence, status: 'FAIL', error: String(error) }); }
  finally { f.store.db.close(); }
}

// Enumerate 0..2 native task_started scans and 0..2 delayed old Stops around
// the one continuation UPS. No scan is required in the actual same-turn defect.
function orders(xs: string[]): string[][] {
  if (!xs.length) return [[]];
  return [...new Set(xs)].flatMap(x => {
    const rest = [...xs]; rest.splice(rest.indexOf(x), 1);
    return orders(rest).map(tail => [x, ...tail]);
  });
}
for (let scans = 0; scans <= 2; scans++) for (let stale = 0; stale <= 2; stale++) {
  for (const order of orders(['UPS', ...Array(scans).fill('scan-start'), ...Array(stale).fill('old-Stop')])) {
    await run('bounded-order', [...order, 'Stop', 'duplicate-Stop'], async f => {
      for (const event of order) {
        if (event === 'UPS') await f.signal('UserPromptSubmit', { prompt: f.dispatch.text });
        if (event === 'scan-start') f.scan('task_started');
        if (event === 'old-Stop') await f.signal('Stop', {}, staleAt);
        assert.equal(f.pane.state, 'busy', 'a start or old Stop cannot finish the receipt');
        assert.equal(f.pane.active, f.active);
      }
      assert.equal(f.pane.active.nativeTurn, 'same-turn', 'native UPS binds the receipt even without task_started');
      let matches = 0;
      const transfer = async (_p: any, _s: any, matched: boolean) => { if (matched) matches++; };
      await f.signal('Stop', { stop_hook_active: false }, currentAt, transfer);
      await f.signal('Stop', { stop_hook_active: true }, currentAt, transfer);
      assert.equal(f.pane.state, 'idle'); assert.equal(f.pane.active, null); assert.equal(matches, 1);
    });
  }
}

// Seeded scheduling of real asynchronous Stop handling: duplicate Stop and
// completion scans may land during the transfer await, or after it resolves.
for (let seed = 1; seed <= 24; seed++) {
  let state = seed;
  const next = () => (state = (Math.imul(state, 1664525) + 1013904223) >>> 0);
  const before = Array(next() % 3).fill('complete').concat(Array(next() % 3).fill('duplicate'));
  const after = Array(next() % 3).fill('complete').concat(Array(next() % 3).fill('duplicate'));
  for (const group of [before, after]) for (let i = group.length - 1; i > 0; i--) {
    const j = next() % (i + 1); [group[i], group[j]] = [group[j], group[i]];
  }
  await run('stop-await', ['UPS', 'Stop-enter', ...before, 'transfer-return', ...after], async f => {
    await f.signal('UserPromptSubmit', { prompt: f.dispatch.text });
    let release!: () => void, matches = 0;
    const blocked = new Promise<void>(resolve => { release = resolve; });
    const transfer = async (_p: any, _s: any, matched: boolean) => { if (matched) { matches++; await blocked; } };
    const stopping = f.signal('Stop', { stop_hook_active: Boolean(seed % 2) }, currentAt, transfer);
    // Failure paths still release the controlled promise and close SQLite.
    try {
      assert.equal(f.pane.stopInProgress, true);
      for (const event of before) {
        if (event === 'complete') f.scan('task_complete');
        else await f.signal('Stop', {}, currentAt, transfer);
        assert.equal(f.pane.state, 'busy'); assert.equal(f.pane.active, f.active);
      }
    } finally { release(); await stopping; }
    for (const event of after) {
      if (event === 'complete') f.scan('task_complete');
      else await f.signal('Stop', {}, currentAt, transfer);
    }
    assert.equal(f.pane.state, 'idle'); assert.equal(f.pane.active, null); assert.equal(matches, 1);
  }, seed);
}

for (const [name, extra, at] of [
  ['foreign-session', { session_id: 'foreign' }, currentAt],
  ['child-agent', { agent_id: 'child' }, currentAt],
  ['wrong-transcript', { transcript_path: '/unrelated.jsonl' }, currentAt],
  ['wrong-cwd', { cwd: '/unrelated' }, currentAt],
  ['missing-turn', { turn_id: '' }, currentAt],
  ['old-received-at', {}, staleAt],
] as const) await run(name, ['invalid-UPS', 'Stop'], async f => {
  await assert.rejects(f.signal('UserPromptSubmit', { prompt: f.dispatch.text, ...extra }, at));
  assert.equal(f.pane.active.nativeTurn, null);
  try { await f.signal('Stop'); } catch (error) { assert.equal((error as any).code, 'current_turn_untrusted'); }
  assert.equal(f.pane.state, 'busy'); assert.equal(f.pane.active, f.active);
});
await run('interrupt-held', ['UPS', 'interrupt', 'Stop'], async f => {
  await f.signal('UserPromptSubmit', { prompt: f.dispatch.text });
  f.pane.interrupted = true; f.pane.interruption = 7;
  await f.signal('Stop'); assert.equal(f.pane.state, 'busy'); assert.equal(f.pane.interrupted, true);
});
await run('complete-alone', ['native-task_complete'], async f => {
  f.scan('task_complete'); assert.equal(f.pane.state, 'busy'); assert.equal(f.pane.active, f.active);
});
await run('other-turn-stop', ['UPS', 'foreign-turn-Stop'], async f => {
  await f.signal('UserPromptSubmit', { prompt: f.dispatch.text });
  await f.signal('Stop', { turn_id: 'old-turn' });
  assert.equal(f.pane.state, 'busy'); assert.equal(f.pane.active, f.active);
});
const failed = results.filter(row => row.status === 'FAIL');
let files = 0, bytes = 0;
function count(path: string) {
  for (const name of readdirSync(path)) {
    const child = join(path, name), stat = lstatSync(child);
    if (stat.isDirectory()) count(child); else { files++; bytes += stat.size; }
  }
}
count(fixture);
const report = { status: failed.length ? 'FAIL' : 'PASS', source, results, failed,
  limitation: '隔离真实模块；不替代后台/门禁/CLI 真实入口红绿及回收验证',
  cleanup: { path: fixture, files, bytes, at: new Date().toISOString(), removed: false } };
writeFileSync(summary, JSON.stringify(report, null, 2) + '\n');
rmSync(fixture, { recursive: true });
report.cleanup.removed = true;
writeFileSync(summary, JSON.stringify(report, null, 2) + '\n');
console.log(`${report.status}: ${results.length} schedules; ${failed.length} failures; SUMMARY=${summary}`);
process.exitCode = failed.length ? 1 : 0;
