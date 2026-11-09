// Oracle fixed before implementation: T-258 Acceptance and the two dated incidents.
// A late root UPS may recover ONLY its original dispatch/current attempt. Native
// identity alone, unrelated failures, stale/foreign hooks and replaced attempts
// must not release it. Old/duplicate Stops must not transfer twice or finish work.
// Real Panes/Store/drain/rollout/signal; terminal and process I/O are boundaries.
// This module check does not prove real CLI timing or the gate's reclaim/relay.
// T258_SOURCE_ROOT points at a known-bad product copy; T258_SUMMARY is a NEW file.
import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { appendFileSync, mkdirSync, mkdtempSync, readdirSync, lstatSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const source = resolve(process.env.T258_SOURCE_ROOT ?? fileURLToPath(new URL('../..', import.meta.url)));
const evidence = resolve('evidence/2026-11-08-batch34/T-258/worker');
mkdirSync(evidence, { recursive: true });
const summary = resolve(process.env.T258_SUMMARY ?? join(evidence, `module-${Date.now()}.json`));
writeFileSync(summary, JSON.stringify({ status: 'INCOMPLETE', source }) + '\n', { flag: 'wx' });
const { Panes } = await import(pathToFileURL(join(source, 'workbench/src/panes.ts')).href);
const { OrchestrationStore } = await import(pathToFileURL(join(source, 'workbench/src/store.ts')).href);
const { A2AGates } = await import(pathToFileURL(join(source, 'workbench/src/gates/core.ts')).href);
const fixture = mkdtempSync(join(dirname(summary), 't258-module-'));
const results: any[] = [];
let cases = 0;

async function setup(t: any, role = 'worker') {
  const root = join(fixture, String(++cases)); mkdirSync(root);
  const store = new OrchestrationStore(root);
  // Same isolation boundary as T-257. No hc constructor or process started.
  const host = Object.assign(Object.create(Panes.prototype), { root, store, config: {}, panes: new Map(),
    onEventWriteFailed: (reason: string) => { throw new Error(reason); } });
  const gates = new A2AGates(root, host);
  const record: any = { id: 'launch', thread: 'thread', task: 'demo+T-258', role, cli: 'Codex',
    worktree: root, attempt: 'attempt', session: 'managed-session', fence: 2, spec_rev: 2, env: { CODEX_HOME: root },
    turn_limit: 6, argv: ['/fixture/codex', '-a', 'never'], created_at: new Date(Date.now() - 1000).toISOString() };
  const attempt = { task_id: record.task, attempt_id: record.attempt, session_id: record.session,
    fence: 2, spec_rev: 2, workspace: root, thread_id: record.thread, reclaimed: false,
    runtime_identity: { launch: record.id, thread: record.thread, shell_pid: 4100, leader_pid: 4101, native_session: null } };
  const task: any = { task_id: record.task, spec_rev: 2, current_attempt: structuredClone(attempt) };
  if (role === 'reviewer') {
    Object.assign(record, { review_id: 'review-1', review_verification_id: 'verification-1' });
    // The gate's documented review is a separate session/thread/candidate copy;
    // its embedded attempt is the original worker, never the reviewer's clone.
    Object.assign(task.current_attempt, { session_id: 'worker-session', thread_id: 'worker-thread',
      workspace: join(root, 'worker'), card_snapshot_id: 'card-1',
      runtime_identity: { launch: 'worker-launch', thread: 'worker-thread', shell_pid: 4000, leader_pid: 4001, native_session: 'worker-native' } });
    Object.assign(task, { state: 'reviewing', candidate_commit: 'c'.repeat(40),
      verification: { verification_id: 'verification-1', state: 'passed' },
      review: { review_id: 'review-1', verification_id: 'verification-1', task_id: record.task, state: 'running',
        attempt: structuredClone(task.current_attempt), spec_rev: 2, card_snapshot_id: 'card-1', candidate_commit: 'c'.repeat(40),
        session_id: record.session, thread_id: record.thread, candidate_workspace: root,
        launch_id: record.id, runtime_identity: structuredClone(attempt.runtime_identity) } });
  }
  store.launch(record);
  const saveTask = () => store.db.prepare('INSERT INTO tasks(id,data) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data')
    .run(record.task, JSON.stringify(task));
  saveTask();
  const dispatch = store.register(record.id, 'T258 original ' + cases, 'controller');
  const writes: string[] = [];
  mkdirSync(join(root, 'traces', record.id), { recursive: true });
  const pane: any = { record, attempt, state: 'idle', native: null, turn: null, active: null, failed: null,
    stopped: false, archived: false, closing: false, nativeEnded: false, leader: 4101,
    interrupted: false, interruption: null, stopInProgress: false, writing: false, queue: [dispatch],
    inputGeneration: 0, submitGeneration: 0, pendingInputs: 0, userDraft: false, writes: Promise.resolve(),
    pty: { pid: 4100, cols: 80, rows: 24, write: (s: string) => writes.push(s) },
    offsets: new Map(), model: 'unknown', effort: 'unknown' };
  host.panes.set(record.thread, pane);
  host.recordUserSubmission = () => {};
  // A fixed process oracle, never derived from the implementation's return.
  let duringRead = () => {};
  const liveOverrides: any = {};
  host.processInfo = async () => {
    duringRead();
    return { shell_pid: 4100, leader: 4101, native_session: pane.native, session_ended: false, failed: pane.failed, ...liveOverrides };
  };
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const draining = host.drain(pane);
  await new Promise<void>(r => setImmediate(r));
  t.mock.timers.tick(300); await draining;
  t.mock.timers.tick(120001); // Ticket's real two-minute startup deadline, no production override.
  assert.match(pane.failed, /^native_session_unbound:/);
  assert.equal(writes.length, 2, 'exactly one paste and one Enter');
  t.mock.timers.reset();
  const active = pane.active, failed = pane.failed;
  const native = '11111111-1111-4111-8111-111111111111';
  const day = new Date();
  const dir = join(root, 'sessions', String(day.getFullYear()), String(day.getMonth()+1).padStart(2,'0'), String(day.getDate()).padStart(2,'0'));
  mkdirSync(dir, { recursive: true });
  const file = join(dir, `rollout-${native}.jsonl`);
  const at = new Date(Date.parse(active.at) + 121000).toISOString();
  const old = new Date(Date.parse(active.at) - 1).toISOString();
  const nativeStart = (source: any = 'cli') => writeFileSync(file,
    JSON.stringify({ type: 'session_meta', payload: { id: native, cwd: root, source } }) + '\n' +
    JSON.stringify({ type: 'event_msg', timestamp: at, payload: { type: 'task_started', turn_id: 'turn-late' } }) + '\n');
  const envelope = (kind: string, extra: any = {}) => ({ hook_event_name: kind, session_id: native,
    turn_id: 'turn-late', cwd: root, transcript_path: file, ...extra });
  const signal = (kind: string, extra: any = {}, received = at, transfer?: any) =>
    host.signal(record.id, JSON.stringify(envelope(kind, extra)), received, transfer);
  const events = () => store.read().filter((e: any) => e.launch === record.id);
  const observed: any = {};
  return { host, store, gates, record, pane, task, saveTask, active, dispatch, native, file, at, old, writes,
    nativeStart, signal, events, failed, observed, liveOverrides, duringRead: (fn: () => void) => { duringRead = fn; } };
}

function scenario(name: string, sequence: string[], body: (f: Awaited<ReturnType<typeof setup>>) => Promise<void>, role = 'worker') {
  test(name, async t => {
    let f: Awaited<ReturnType<typeof setup>> | undefined;
    try { f = await setup(t, role); await body(f); results.push({ name, sequence, status: 'PASS', observed: f.observed }); }
    catch (error) { results.push({ name, sequence, status: 'FAIL', error: String(error),
      failed: f?.pane.failed, state: f?.pane.state, events: f?.events().map((e: any) => ({ type: e.type, data: e.data })) }); throw error; }
    finally { f?.gates.db.close(); f?.store.db.close(); }
  });
}
function orders(xs: string[]): string[][] {
  if (!xs.length) return [[]];
  return [...new Set(xs)].flatMap(x => { const rest = [...xs]; rest.splice(rest.indexOf(x), 1); return orders(rest).map(tail => [x, ...tail]); });
}
// Timeout is a real drain timer above, followed by 0..2 scans and old Stops
// around one UPS. Native evidence is available; UPS-first must collect it too.
for (let scans = 0; scans <= 2; scans++) for (let stops = 0; stops <= 2; stops++) {
  for (const order of orders(['UPS', ...Array(scans).fill('scan'), ...Array(stops).fill('old-Stop')])) {
    scenario('late-start ' + order.join('/'), ['timeout', ...order, 'Stop', 'duplicate-Stop'], async f => {
      f.nativeStart();
      for (const event of order) {
        if (event === 'scan') f.host.scan(f.pane);
        if (event === 'UPS') await f.signal('UserPromptSubmit', { prompt: f.dispatch.text });
        if (event === 'old-Stop') await f.signal('Stop', {}, f.old);
        assert.equal(f.pane.active, f.active, 'no scan/start/old Stop finishes work');
      }
      assert.equal(f.pane.failed, null, 'verified late UPS recovers only the startup absence');
      assert.equal(f.pane.state, 'busy');
      let calls = 0;
      const transfer = async (_p: any, _s: any, matched: boolean) => { if (matched) calls++; };
      await f.signal('Stop', {}, f.at, transfer); await f.signal('Stop', {}, f.at, transfer);
      assert.equal(calls, 1); assert.equal(f.pane.active, null); assert.equal(f.pane.state, 'idle');
      assert.equal(f.writes.length, 2, 'no recovery input replay');
    });
  }
}
for (const [name, extra] of [
  ['foreign-session', { session_id: 'foreign' }], ['child', { agent_id: 'child' }],
  ['wrong-file', { transcript_path: '/foreign.jsonl' }], ['wrong-cwd', { cwd: '/foreign' }],
  ['wrong-turn', { turn_id: 'foreign-turn' }], ['no-turn', { turn_id: '' }],
] as const) scenario(name, ['timeout', 'scan', 'invalid-UPS'], async f => {
  f.nativeStart(); f.host.scan(f.pane);
  await assert.rejects(f.signal('UserPromptSubmit', { prompt: f.dispatch.text, ...extra }));
  assert.equal(f.pane.failed, f.failed); assert.equal(f.pane.active, f.active);
});
for (const name of ['no-native', 'auxiliary', 'wrong-prompt', 'stale-attempt', 'reclaimed', 'wrong-fence', 'wrong-session',
  'wrong-spec', 'other-failure', 'failure-after-timeout', 'replaced-during-read', 'trace-failed-during-read',
  'bound-native-mismatch', 'bound-launch-mismatch', 'bound-shell-mismatch', 'interrupted', 'untrusted-hook', 'wrong-submission',
  'live-leader-mismatch', 'live-shell-mismatch', 'live-native-mismatch', 'live-ended', 'live-query-error', 'recovery-event-error']) {
  scenario(name, ['timeout', name, 'UPS'], async f => {
    if (name !== 'no-native') f.nativeStart(name === 'auxiliary' ? { subagent: { parent_thread_id: 'parent' } } : 'cli');
    if (name === 'stale-attempt') f.task.current_attempt.attempt_id = 'replacement';
    if (name === 'reclaimed') f.task.current_attempt.reclaimed = true;
    if (name === 'wrong-fence') f.task.current_attempt.fence++;
    if (name === 'wrong-session') f.task.current_attempt.session_id = 'foreign';
    if (name === 'wrong-spec') f.task.spec_rev++;
    if (name === 'bound-native-mismatch') f.task.current_attempt.runtime_identity.native_session = 'foreign' as any;
    if (name === 'bound-launch-mismatch') f.task.current_attempt.runtime_identity.launch = 'foreign';
    if (name === 'bound-shell-mismatch') f.task.current_attempt.runtime_identity.shell_pid++;
    if (name === 'interrupted') { f.pane.interrupted = true; f.pane.interruption = 9; }
    if (name === 'untrusted-hook') f.store.event('native_question_unverified', { session_id: f.native, submission: f.active.id }, f.record);
    if (name === 'wrong-submission') f.pane.active = { ...f.active, id: 'replacement' };
    if (name === 'live-leader-mismatch') f.liveOverrides.leader = 9999;
    if (name === 'live-shell-mismatch') f.liveOverrides.shell_pid = 9999;
    if (name === 'live-native-mismatch') f.liveOverrides.native_session = 'foreign';
    if (name === 'live-ended') f.liveOverrides.session_ended = true;
    if (name === 'live-query-error') f.duringRead(() => { throw new Error('process observer failed'); });
    if (name === 'recovery-event-error') {
      const write = f.store.event.bind(f.store);
      f.store.event = (type: string, ...args: any[]) => {
        if (type === 'native_session_late_start_confirmed') throw new Error('recovery event write failed');
        return write(type, ...args);
      };
    }
    if (name === 'other-failure') f.pane.failed = 'restore_failed';
    if (name === 'failure-after-timeout') f.host.recordFailure(f.pane, 'trace_write_failed', new Error('fixture disk error'));
    f.saveTask();
    if (name === 'replaced-during-read') f.duringRead(() => { f.task.current_attempt.attempt_id = 'replacement'; f.saveTask(); });
    if (name === 'trace-failed-during-read') f.duringRead(() => f.host.recordFailure(f.pane, 'trace_write_failed', new Error('fixture disk error')));
    try { await f.signal('UserPromptSubmit', { prompt: name === 'wrong-prompt' ? 'unrelated' : f.dispatch.text }); }
    catch (error) { f.observed.ups_refusal = (error as any).code ?? String(error); }
    assert.ok(f.pane.failed, 'missing or mismatched proof cannot recover');
    assert.notEqual(f.pane.state, 'idle');
    assert.equal(f.writes.length, 2);
    let matched = 0;
    try { await f.signal('Stop', {}, f.at, async (_p: any, _s: any, allowed: boolean) => { if (allowed) matched++; }); }
    catch (error) { f.observed.stop_refusal = (error as any).code ?? String(error); }
    assert.equal(matched, 0, 'unverified startup cannot authorize a request');
    assert.notEqual(f.pane.state, 'idle');
  });
}
scenario('identity-only', ['timeout', 'scan', 'complete'], async f => {
  f.nativeStart(); f.host.scan(f.pane);
  appendFileSync(f.file, JSON.stringify({ type: 'event_msg', timestamp: f.at, payload: { type: 'task_complete', turn_id: 'turn-late' } }) + '\n');
  f.host.scan(f.pane);
  assert.equal(f.pane.failed, f.failed); assert.equal(f.pane.active, f.active);
});
// Dispatch may precede its first foreground observation. Existing T-253 identity
// binding permits an unbound leader, but never replaces a previously bound one.
for (const role of ['worker', 'reviewer']) {
  scenario('bound-leader-mismatch ' + role, ['timeout', 'bound-leader-mismatch', 'UPS'], async f => {
    const identity = role === 'worker' ? f.task.current_attempt.runtime_identity : f.task.review.runtime_identity;
    identity.leader_pid = 4099; // The already-bound process differs from the pane/live leader (4101).
    f.saveTask();
    f.nativeStart();
    await assert.rejects(f.signal('UserPromptSubmit', { prompt: f.dispatch.text }), (error: any) => {
      f.observed.refusal = error.code;
      return error.code === 'identity_conflict';
    }, 'bound leader mismatch must refuse recovery');
    assert.equal(f.pane.failed, f.failed, 'startup failure remains');
    assert.equal(f.pane.active, f.active, 'original active remains');
    assert.equal(f.pane.state, 'unknown');
    assert.equal(f.writes.length, 2, 'no recovery input replay');
  }, role);
}
scenario('leader-first-observed-late', ['timeout', 'native-start', 'UPS'], async f => {
  f.task.current_attempt.runtime_identity.leader_pid = null as any; f.saveTask();
  f.nativeStart(); await f.signal('UserPromptSubmit', { prompt: f.dispatch.text });
  assert.equal(f.pane.failed, null); assert.equal(f.pane.state, 'busy');
});
scenario('in-flight duplicate Stop', ['timeout', 'UPS', 'Stop-await', 'duplicate-Stop', 'finish'], async f => {
  f.nativeStart(); f.host.scan(f.pane); await f.signal('UserPromptSubmit', { prompt: f.dispatch.text });
  let release!: () => void, calls = 0;
  const blocked = new Promise<void>(r => { release = r; });
  const transfer = async (_p: any, _s: any, matched: boolean) => { if (matched) { calls++; await blocked; } };
  const first = f.signal('Stop', {}, f.at, transfer);
  try {
    assert.equal(f.pane.stopInProgress, true);
    await f.signal('Stop', {}, f.at, transfer);
    assert.equal(f.pane.active, f.active); assert.equal(f.pane.state, 'busy');
  } finally { release(); await first; }
  assert.equal(calls, 1); assert.equal(f.pane.state, 'idle');
});
for (const order of [['UPS', 'scan'], ['scan', 'UPS']]) {
  scenario('reviewer late-start ' + order.join('/'), ['real-drain-timeout', ...order, 'Stop', 'duplicate-Stop'], async f => {
    f.nativeStart();
    for (const event of order) {
      if (event === 'scan') f.host.scan(f.pane);
      else await f.signal('UserPromptSubmit', { prompt: f.dispatch.text });
    }
    assert.equal(f.pane.failed, null, 'the same deadline must not permanently fail a verified reviewer');
    assert.equal(f.pane.state, 'busy');
    let matched = 0;
    const transfer = async (_p: any, _s: any, allowed: boolean) => { if (allowed) matched++; };
    await f.signal('Stop', {}, f.at, transfer); await f.signal('Stop', {}, f.at, transfer);
    assert.equal(matched, 1); assert.equal(f.pane.active, null); assert.equal(f.pane.state, 'idle');
    assert.equal(f.writes.length, 2);
  }, 'reviewer');
}
for (const name of ['replaced', 'cancelled', 'worker-replaced', 'session', 'thread', 'workspace', 'verification',
  'candidate', 'card', 'runtime', 'changed-during-read']) {
  scenario('reviewer refuses ' + name, ['timeout', name, 'UPS'], async f => {
    f.nativeStart();
    const change = () => {
      const review = f.task.review;
      if (name === 'replaced' || name === 'changed-during-read') review.review_id = 'new-review';
      if (name === 'cancelled') review.state = 'cancelled';
      if (name === 'worker-replaced') f.task.current_attempt.attempt_id = 'new-attempt';
      if (name === 'session') review.session_id = f.task.current_attempt.session_id;
      if (name === 'thread') review.thread_id = 'other-thread';
      if (name === 'workspace') review.candidate_workspace += '-other';
      if (name === 'verification') f.task.verification.verification_id = 'other-verification';
      if (name === 'candidate') f.task.candidate_commit = 'd'.repeat(40);
      if (name === 'card') review.card_snapshot_id = 'other-card';
      if (name === 'runtime') review.runtime_identity.launch = 'worker-launch';
      f.saveTask();
    };
    if (name === 'changed-during-read') f.duringRead(change); else change();
    await assert.rejects(f.signal('UserPromptSubmit', { prompt: f.dispatch.text }), (error: any) => {
      // The contract requires refusal, not a new spelling of its reason. Keep
      // the actual code so a safe older refusal is not counted as a defect.
      f.observed.refusal = error.code; return typeof error.code === 'string' && error.code.length > 0;
    });
    assert.equal(f.pane.failed, f.failed); assert.equal(f.pane.active, f.active); assert.equal(f.writes.length, 2);
  }, 'reviewer');
}
after(() => {
  let files = 0, bytes = 0;
  function count(path: string) { for (const name of readdirSync(path)) { const child = join(path, name), s = lstatSync(child);
    if (s.isDirectory()) count(child); else { files++; bytes += s.size; } } }
  count(fixture);
  const report = { status: results.some(r => r.status === 'FAIL') ? 'FAIL' : 'PASS', source, results,
    limitation: '模块状态与顺序检查；真实 CLI、门禁回收和请求去重须另跑 E2E',
    cleanup: { path: fixture, files, bytes, at: new Date().toISOString(), removed: false } };
  writeFileSync(summary, JSON.stringify(report, null, 2) + '\n');
  rmSync(fixture, { recursive: true }); report.cleanup.removed = true;
  writeFileSync(summary, JSON.stringify(report, null, 2) + '\n');
  console.log('SUMMARY=' + summary);
});
