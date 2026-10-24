// T-160 isolated state evidence, not real Codex/PTY evidence.
// Failures: matched failed review cannot stop; unmatched or replaced submission
// can stop; another unknown reason or role can stop; a throwing transfer can stop.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [source, out] = process.argv.slice(2);
const { Panes } = await import(pathToFileURL(join(source, 'workbench/src/panes.ts')).href);
const { OrchestrationStore } = await import(pathToFileURL(join(source, 'workbench/src/store.ts')).href);
const checks: any[] = [];
async function run(name: string, scenario: string, mayStop: boolean) {
  const root = join(out, name); mkdirSync(root);
  const store = new OrchestrationStore(root), panes = new Panes(root, store, {}, () => {});
  const record = { id: name, thread: name, task: 'demo+T-160', role: scenario === 'other-role' ? 'worker' : 'reviewer',
    cli: 'Codex', worktree: root, attempt: 'a1', env: {} };
  store.launch(record);
  const original = { id: 'submission-1', nativeTurn: 'turn-1', at: '2026-10-24T00:00:00Z' };
  let kills = 0, transferred = false;
  const exits: (() => void)[] = [];
  const pane: any = { record, attempt: { workspace: root }, task: {}, native: 'native-session', nativeFile: join(root, 'native.jsonl'),
    state: 'busy', failed: null, stopped: false, archived: false, nativeEnded: false, interrupted: false,
    active: original, turn: 'turn-1', stopInProgress: false, writing: false, queue: [],
    pty: { pid: 101, onExit: (callback: () => void) => exits.push(callback),
      kill: () => { kills++; pane.stopped = true; exits.forEach(callback => callback()); } } };
  panes.panes.set(record.thread, pane);
  // External process/native-record collection is absent in this state fixture.
  // The real signal, envelope/trust checks, readThread and stopThread still run.
  panes.scan = () => {};
  panes.processInfo = async () => ({ leader: 102, failed: pane.failed });
  try {
    if (scenario === 'unmatched') { pane.state = 'unknown'; pane.failed = 'invalid_review_result'; }
    if (scenario === 'other-unknown') { pane.state = 'unknown'; pane.failed = 'provider_lost'; }
    if (scenario !== 'other-unknown') {
      const stop = { hook_event_name: 'Stop', session_id: pane.native, cwd: root,
        transcript_path: pane.nativeFile, turn_id: scenario === 'unmatched' ? 'old-turn' : 'turn-1',
        last_assistant_message: '```json\n{}\n```' };
      const ending = panes.signal(record.id, JSON.stringify(stop), '2026-10-24T00:01:00Z', async (_pane: any, _stop: any, matched: boolean) => {
        if (!matched) return;
        transferred = true;
        if (scenario === 'throws') throw new Error('independent transfer failure');
        pane.failed = scenario === 'other-error' ? 'review_rejected' : 'invalid_review_result';
        if (scenario === 'replacement') {
          pane.active = { id: 'submission-2', nativeTurn: 'turn-2', at: '2026-10-24T00:01:00Z' };
          pane.turn = 'turn-2';
        }
      });
      if (scenario === 'throws') await assert.rejects(ending, /independent transfer failure/);
      else await ending;
    }
    const live = await panes.readThread(record.thread);
    if (mayStop) {
      assert.equal(transferred, true);
      assert.equal(pane.active, null);
      assert.equal(live.running, false, 'matched Stop is a completed turn');
      assert.equal(live.blocked, true, 'protocol rejection remains visible');
      assert.equal(pane.failed, 'invalid_review_result');
      await panes.stopThread(record.thread);
      assert.equal(kills, 1);
    } else {
      if (scenario === 'unmatched') assert.equal(transferred, false);
      if (scenario === 'replacement') assert.equal(pane.active?.id, 'submission-2', 'old Stop cannot clear a new submission');
      await assert.rejects(panes.stopThread(record.thread), (error: any) => error.code === 'worker_not_idle');
      assert.equal(kills, 0, 'unknown lifecycle must not stop a process');
    }
    checks.push({ name, status: 'PASS', kills, transferred });
  } catch (error) { checks.push({ name, status: 'INCOMPLETE', error: String(error), kills, transferred }); }
  finally {
    writeFileSync(join(root, 'events.json'), JSON.stringify(store.read(), null, 2) + '\n');
    store.close();
  }
}
await run('matched_parser_failure_reclaimable', 'matched', true);
await run('unmatched_stop_not_reclaimable', 'unmatched', false);
await run('different_submission_not_reclaimable', 'replacement', false);
await run('other_unknown_not_reclaimable', 'other-unknown', false);
await run('other_review_error_not_reclaimable', 'other-error', false);
await run('other_role_not_reclaimable', 'other-role', false);
await run('throwing_transfer_not_reclaimable', 'throws', false);
const report = { status: checks.every(check => check.status === 'PASS') ? 'PASS' : 'INCOMPLETE', checks,
  scope: 'isolated Codex Stop state; no real CLI, process, socket, native collector or PTY' };
writeFileSync(join(out, 'results.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
