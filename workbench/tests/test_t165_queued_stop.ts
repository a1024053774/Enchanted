// Failure modes, before this host test: an early Stop is lost; a foreign prompt
// completes a queued turn or transfers a request; a Stop predating the native
// turn is accepted; a retained Stop bypasses a later launch failure; a duplicate
// Stop transfers twice. Expectations come from T-165's identity/completion rule.
// This controls files/hooks/async transfer, not real CLI, PTY, or gate execution.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [source, out] = process.argv.slice(2);
const { Panes } = await import(pathToFileURL(join(source, 'workbench/src/panes.ts')).href);
const { OrchestrationStore } = await import(pathToFileURL(join(source, 'workbench/src/store.ts')).href);
const checks: any[] = [];
for (const scenario of ['stop-first', 'unrelated-stop', 'predating-stop', 'failed-launch']) {
  const root = join(out, scenario); mkdirSync(root);
  const store = new OrchestrationStore(root), panes = new Panes(root, store, {}, () => {});
  const record = { id: scenario, thread: scenario, task: 'demo+T-165', role: 'worker', cli: 'Claude Code',
    worktree: root, attempt: 'a1', session: 's1', fence: 1, spec_rev: 1, turn_limit: 6, env: {} };
  store.launch(record);
  const file = join(root, 'native.jsonl'); writeFileSync(file, '');
  const queued = { prompt: 'queued human / sentinel-165', received_at: '2026-10-24T00:01:00Z' };
  const pane: any = { record, attempt: { thread_id: scenario, workspace: root }, token: 'fixture-token',
    native: 'native', nativeFile: file, state: 'busy', active: null, claudePromptId: null,
    claudePromptIds: new Set(['old-prompt']), claudeQueuedPrompts: [queued], failed: null,
    stopped: false, archived: false, nativeEnded: false, interrupted: false, stopInProgress: false,
    writing: false, queue: [], writes: Promise.resolve(), pendingInputs: 0, inputGeneration: 0,
    pty: { pid: 101, write: () => { throw new Error('unexpected PTY input'); } } };
  panes.panes.set(record.thread, pane);
  panes.processInfo = async () => { panes.scan(pane); return { leader: 102, failed: pane.failed }; };
  let drained = 0;
  panes.drain = async () => { drained++; };
  const envelope = (prompt: string) => ({ hook_event_name: 'Stop', session_id: 'native', prompt_id: prompt,
    cwd: root, transcript_path: file, stop_hook_active: false, effort: { level: 'low' } });
  const calls: string[] = [];
  const transfer = async (_pane: any, value: any, matched: boolean) => {
    assert.equal(matched, true);
    const caller = await panes.caller({ launch: record.id, token: pane.token, native_session: 'native', prompt_id: value.prompt_id });
    await caller.assertActive();
    calls.push(value.prompt_id);
  };
  try {
    const stop = envelope(scenario === 'unrelated-stop' ? 'unrelated' : 'queued-prompt');
    const received = scenario === 'predating-stop' ? '2026-10-24T00:01:01Z' : '2026-10-24T00:01:03Z';
    await panes.signal(record.id, JSON.stringify(stop), received, transfer);
    assert.equal(pane.active, null, 'Stop alone cannot invent the queued turn');
    assert.deepEqual(calls, [], 'unbound Stop cannot transfer');
    if (scenario === 'failed-launch') pane.failed = 'fixture revoked launch';
    writeFileSync(file, JSON.stringify({ type: 'user', isSidechain: false, sessionId: 'native', cwd: root,
      promptSource: 'queued', turnOrigin: 'human', origin: { kind: 'human' }, uuid: 'native-queued-user',
      promptId: 'queued-prompt', timestamp: '2026-10-24T00:01:02Z', message: { role: 'user', content: queued.prompt } }) + '\n');
    panes.scan(pane);
    // Let the explicit async transfer and its drain settle; no timer/poll retry.
    await new Promise(resolve => setImmediate(resolve));
    if (scenario === 'stop-first') {
      assert.equal(pane.state, 'idle'); assert.equal(pane.active, null);
      assert.deepEqual(calls, ['queued-prompt']); assert.equal(drained, 1);
      await panes.signal(record.id, JSON.stringify(stop), received, transfer);
      assert.deepEqual(calls, ['queued-prompt'], 'duplicate Stop cannot transfer again');
    } else {
      assert.equal(pane.state, 'busy'); assert.ok(pane.active);
      assert.deepEqual(calls, [], 'unrelated, earlier or failed Stop must not transfer');
      assert.ok(store.read().some(e => e.type === 'stop_not_matched' && e.data.prompt_id === stop.prompt_id));
      if (scenario === 'unrelated-stop') {
        await panes.signal(record.id, JSON.stringify(envelope('queued-prompt')), '2026-10-24T00:01:04Z', transfer);
        assert.equal(pane.state, 'idle'); assert.deepEqual(calls, ['queued-prompt']);
      }
    }
    checks.push({ name: scenario, status: 'PASS', calls });
  } catch (error) { checks.push({ name: scenario, status: 'INCOMPLETE', error: String(error), calls }); }
  finally { writeFileSync(join(root, 'events.json'), JSON.stringify(store.read(), null, 2) + '\n'); store.close(); }
}
const report = { status: checks.every(c => c.status === 'PASS') ? 'PASS' : 'INCOMPLETE', checks,
  scope: 'controlled native-hook/transcript host; no real CLI/PTY/gate execution' };
writeFileSync(join(out, 'results.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
