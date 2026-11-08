// T-251: input the user types into a Claude worker while it works in a subdirectory.
// Fact (T-249 worker transcript, 2026-11-07): every native transcript entry carries the shell's current directory, so
// after `cd workbench/app/panels` the entries say `<worktree>/workbench/app/panels`. A queued human prompt typed then
// is recorded with that cwd.
// Failure modes, listed before the fix: the queued prompt is never bound to its turn because its cwd is not the
// worktree root; the pane keeps a queue it can never drain, stays busy, and reclaim refuses it (worker_working), the
// same deadlock as the untrusted Stop. Over-correction: a prompt from a sibling directory that only shares the
// prefix, or from outside the launch directories, is bound as this session's turn.
// Oracle: the T-251 ticket (rev 2) and the rule already applied to hooks: inside the worktree or its extra
// directories, subdirectories included, is this session; anything else is not.
// Controlled host: real Panes and store, a real transcript file, no CLI or PTY.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [source, out] = process.argv.slice(2);
const { Panes } = await import(pathToFileURL(join(source, 'workbench/src/panes.ts')).href);
const { OrchestrationStore } = await import(pathToFileURL(join(source, 'workbench/src/store.ts')).href);
const checks: { name: string; pass: boolean; failure?: string }[] = [];
const cases: [string, (root: string) => string, boolean][] = [
  ['subdirectory', root => join(root, 'workbench/app/panels'), true],
  ['worktree_root', root => root, true],
  ['sibling_with_same_prefix', root => root + '-other', false],
  ['outside', () => '/private/tmp', false],
];
for (const [name, cwdOf, binds] of cases) {
  try {
    const root = join(out, name); mkdirSync(root, { recursive: true });
    const store = new OrchestrationStore(root), panes = new Panes(root, store, {}, () => {});
    panes.recordUserSubmission = () => {};
    panes.processInfo = async () => ({ leader: 102, failed: null });
    const record = { id: name, thread: name, task: 'demo+T-251', role: 'worker', cli: 'Claude Code',
      worktree: root, attempt: 'a1', session: 's1', fence: 1, spec_rev: 1, turn_limit: 6, env: {} };
    store.launch(record);
    const file = join(root, 'native-session.jsonl');
    const note = '人工介入 / sentinel-251';
    // The original turn has ended; the CLI holds the typed input as its next turn (T-166 queue).
    const pane: any = { record, attempt: { thread_id: name, workspace: root }, task: {}, token: 'test-token',
      native: 'native-session', nativeFile: file, state: 'busy', failed: null, stopped: false, archived: false, nativeEnded: false,
      interrupted: false, active: null, turn: null, claudePromptId: null, claudePromptIds: new Set(['prompt-1']),
      claudeQueuedPrompts: [{ prompt: note, received_at: '2026-11-07T18:00:00Z' }],
      stopInProgress: false, writing: false, queue: [], writes: Promise.resolve(), pendingInputs: 0, inputGeneration: 0,
      draft: { chars: [], cursor: 0, keys: [], uncertain: false }, pty: { pid: 101, write: () => {} } };
    panes.panes.set(record.thread, pane);
    const cwd = cwdOf(root);
    writeFileSync(file, JSON.stringify({ type: 'user', isSidechain: false, sessionId: pane.native, cwd, promptId: 'prompt-2',
      timestamp: '2026-11-07T18:00:01Z', uuid: 'native-user-2', promptSource: 'queued', turnOrigin: 'human', origin: { kind: 'human' },
      message: { role: 'user', content: note } }) + '\n');
    panes.scan(pane);
    if (!binds) {
      assert.equal(pane.claudePromptId, null, 'a prompt recorded outside the launch directories must not become this turn');
      assert.equal(pane.active, null);
      checks.push({ name, pass: true }); continue;
    }
    assert.equal(pane.claudePromptId, 'prompt-2', 'the queued human prompt becomes its own turn');
    assert.ok(pane.active, 'the queued prompt establishes a submission');
    // Its Stop comes from the same directory and ends the turn: the pane is idle, so the gate can reclaim it.
    await panes.signal(record.id, JSON.stringify({ hook_event_name: 'Stop', session_id: pane.native, prompt_id: 'prompt-2', cwd,
      transcript_path: file, stop_hook_active: false, effort: { level: 'low' } }), '2026-11-07T18:00:05Z',
      async (_pane: any, _value: any, matched: boolean) => assert.equal(matched, true));
    assert.equal(pane.state, 'idle', 'the queued turn ends idle');
    assert.equal(pane.claudeQueuedPrompts.length, 0);
    assert.equal(pane.failed, null);
    checks.push({ name, pass: true });
  } catch (error) {
    checks.push({ name, pass: false, failure: String(error) });
  }
}
const failed = checks.filter(check => !check.pass).map(check => check.name);
const summary = { status: failed.length ? 'FAIL' : 'PASS', source, failed, checks };
writeFileSync(join(out, 'summary.json'), JSON.stringify(summary, null, 2) + '\n');
console.log(JSON.stringify(summary));
process.exitCode = failed.length ? 1 : 0;
