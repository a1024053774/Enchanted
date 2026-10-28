// Failure modes, before implementation: input typed during a working turn (not a
// Stop batch) reuses the running prompt id and is refused, poisoning the turn so
// its real Stop is refused; a fix that queues it promotes the queued transcript
// turn while the original turn is still active, so the original Stop no longer
// matches; a reused prompt id with no user Enter is accepted as queued input.
// Oracle: T-166 ticket and the user ruling relayed in 20261024T030734Z-001.
// This host controls the hook boundary; it does not prove real CLI/PTY timing.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [source, out] = process.argv.slice(2);
const { Panes } = await import(pathToFileURL(join(source, 'workbench/src/panes.ts')).href);
const { OrchestrationStore } = await import(pathToFileURL(join(source, 'workbench/src/store.ts')).href);
const checks: any[] = [];
for (const scenario of ['busy-input-queued', 'no-enter-reused']) {
  const root = join(out, scenario); mkdirSync(root);
  const store = new OrchestrationStore(root), panes = new Panes(root, store, {}, () => {});
  const record = { id: scenario, thread: scenario, task: 'demo+T-166', role: 'worker', cli: 'Claude Code',
    worktree: root, attempt: 'a1', session: 's1', fence: 1, spec_rev: 1, turn_limit: 6, env: { CLAUDE_CONFIG_DIR: root } };
  store.launch(record);
  const original = { id: 'submission-1', dispatch: 'input:first', nativeTurn: null, at: '2026-10-24T00:00:00Z' };
  const bytes: string[] = [];
  const pane: any = { record, attempt: { thread_id: scenario, workspace: root }, task: {}, token: 'test-token',
    native: 'native-session', state: 'busy', failed: null, stopped: false, archived: false, nativeEnded: false,
    interrupted: false, active: original, turn: null, claudePromptId: 'prompt-1', claudePromptIds: new Set(['prompt-1']),
    stopInProgress: false, writing: false, queue: [], writes: Promise.resolve(), pendingInputs: 0, inputGeneration: 0,
    draft: { chars: [], cursor: 0, keys: [], uncertain: false },
    pty: { pid: 101, write: (data: string) => bytes.push(data) } };
  panes.panes.set(record.thread, pane);
  panes.processInfo = async () => ({ leader: 102, failed: pane.failed });
  const projects = join(root, 'projects'); mkdirSync(projects);
  const file = join(projects, 'native-session.jsonl');
  writeFileSync(file, JSON.stringify({ type: 'user', sessionId: pane.native, cwd: root, promptId: 'prompt-1',
    timestamp: '2026-10-24T00:00:00Z', message: { role: 'user', content: 'original' } }) + '\n');
  pane.nativeFile = file;
  const note = '人工介入 / sentinel-166';
  const envelope = (name: string, prompt: string) => ({ hook_event_name: name, session_id: pane.native, prompt_id: prompt,
    cwd: root, transcript_path: file, stop_hook_active: false, effort: { level: 'low' }, prompt: note });
  try {
    if (scenario === 'no-enter-reused') {
      // No user keystroke reached the pane: a reused prompt id is not queued input.
      await assert.rejects(panes.signal(record.id, JSON.stringify(envelope('UserPromptSubmit', 'prompt-1')), '2026-10-24T00:00:30Z'));
      assert.equal(pane.claudeQueuedPrompts?.length ?? 0, 0, 'a reused prompt id without Enter must not queue');
      assert.ok(store.read().some((event: any) => event.type === 'native_question_unverified' &&
        String(event.data.reason).includes('claude_prompt_id_reused')), 'the refusal stays recorded');
      checks.push({ name: scenario, status: 'PASS' });
      continue;
    }
    // The user types into the working turn; the bytes go straight to the CLI.
    await panes.userInput(record.id, '\x1b[200~' + note + '\x1b[201~', { request_id: 'paste' }, async () => {}, async () => {});
    await panes.userInput(record.id, '\r', { request_id: 'enter' }, async () => {}, async () => {});
    assert.deepEqual(bytes, ['\x1b[200~' + note + '\x1b[201~', '\r']);
    await panes.signal(record.id, JSON.stringify(envelope('UserPromptSubmit', 'prompt-1')), '2026-10-24T00:00:31Z');
    assert.equal(pane.active, original, 'queued input must not replace the working turn');
    assert.equal(pane.claudePromptId, 'prompt-1');
    assert.equal(pane.claudeQueuedPrompts?.length, 1, 'busy input is queued');
    // The queued transcript entry is already present when the original Stop arrives.
    writeFileSync(file, JSON.stringify({ type: 'user', isSidechain: false, sessionId: pane.native, cwd: root, promptId: 'prompt-2',
      timestamp: '2026-10-24T00:00:32Z', uuid: 'native-user-2', promptSource: 'queued', turnOrigin: 'human', origin: { kind: 'human' },
      message: { role: 'user', content: note } }) + '\n');
    let matchedOriginal = false;
    await panes.signal(record.id, JSON.stringify(envelope('Stop', 'prompt-1')), '2026-10-24T00:00:33Z',
      async (_p: any, _v: any, matched: boolean) => { matchedOriginal = matched; });
    assert.equal(matchedOriginal, true, 'the original Stop stays trusted and matched');
    assert.equal(pane.failed, null);
    panes.scan(pane);
    assert.equal(pane.claudePromptId, 'prompt-2', 'the queued input opens its own turn after the original completes');
    let matchedQueued = false;
    await panes.signal(record.id, JSON.stringify(envelope('Stop', 'prompt-2')), '2026-10-24T00:00:34Z',
      async (_p: any, _v: any, matched: boolean) => { matchedQueued = matched; });
    assert.equal(matchedQueued, true);
    assert.equal(pane.state, 'idle'); assert.equal(pane.active, null); assert.equal(pane.failed, null);
    checks.push({ name: scenario, status: 'PASS', bytes });
  } catch (error) { checks.push({ name: scenario, status: 'INCOMPLETE', error: String(error), bytes }); }
  finally { writeFileSync(join(root, 'events.json'), JSON.stringify(store.read(), null, 2) + '\n'); store.close(); }
}
const report = { status: checks.every(c => c.status === 'PASS') ? 'PASS' : 'INCOMPLETE', checks,
  scope: 'controlled native-hook/identity state; no real CLI, PTY or gate submit' };
writeFileSync(join(out, 'results.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
