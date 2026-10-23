// Isolated signal contract; not real CLI/Electron evidence.
// Failure modes: SessionEnd without a prompt id is rejected; a foreign session,
// cwd, transcript or child agent ends this launch; Stop is mistaken for exit;
// the exit fact does not reach sidebar state; accepting exit closes the zsh PTY.
// A literal /exit input leaves activity busy without Stop; confirmed SessionEnd
// must let reclamation stop the shell, while a still-live busy session stays protected.
// Expectations use Claude's documented SessionEnd schema and T-146, not production constants.
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [output, source = '.'] = process.argv.slice(2);
if (!output || existsSync(output)) throw new Error('Fresh summary path required');
const report = { status: 'INCOMPLETE', argv: process.argv, checks: [] };
let store;
try {
  const { OrchestrationStore } = await import(pathToFileURL(resolve(source, 'workbench/src/store.ts')));
  const { Panes } = await import(pathToFileURL(resolve(source, 'workbench/src/panes.ts')));
  const { agentState } = await import(pathToFileURL(resolve(source, 'workbench/src/sidebar.ts')));
  const root = mkdtempSync('/private/tmp/t146-session-end-');
  report.fixture = root;
  store = new OrchestrationStore(root);
  const panes = new Panes(root, store, {}, () => {});
  const record = { id: 'exit-launch', thread: 'exit-thread', task: 'demo+T-exit', attempt: null, role: 'worker',
    session: 'native-session', cli: 'Claude Code', worktree: root, turn_limit: 1, created_at: new Date().toISOString() };
  store.launch(record);
  const pane = { record, native: record.session, active: null, claudePromptId: null,
    nativeEnded: false, state: 'idle', stopped: false, archived: false, failed: null,
    pty: { pid: 12345, write: () => {} }, leader: 12346, queue: [], writing: false,
    writes: Promise.resolve(), pendingInputs: 0, inputGeneration: 0, userDraft: false };
  panes.panes.set(record.thread, pane);
  const signal = extra => panes.signal(record.id, JSON.stringify({ session_id: record.session,
    cwd: root, transcript_path: join(root, 'native-session.jsonl'), hook_event_name: 'SessionEnd', reason: 'prompt_input_exit',
    ...extra }), new Date().toISOString());
  for (const [name, extra] of [
    ['foreign_session', { session_id: 'foreign-session' }], ['foreign_cwd', { cwd: '/foreign' }],
    ['foreign_transcript', { transcript_path: join(root, 'foreign.jsonl') }], ['child_agent', { agent_id: 'child' }],
    ['malformed_agent', { agent_id: {} }], ['missing_reason', { reason: null }],
  ]) {
    await assert.rejects(signal(extra), undefined, name);
    assert.equal(pane.nativeEnded, false, name);
    report.checks.push(name + '_rejected');
  }
  await signal({ hook_event_name: 'Stop', prompt_id: 'completed-turn', stop_hook_active: false });
  assert.equal(pane.nativeEnded, false);
  assert.equal(agentState(panes.status(record.thread), [], root), 'idle');
  report.checks.push('stop_is_idle_not_exit');
  await panes.userInput(record.id, '/exit\r', { request_id: 'exit-input' }, async () => {}, async () => {});
  assert.equal(pane.state, 'busy', '/exit is admitted as terminal input before the CLI exits');
  let terminations = 0;
  panes.terminate = async (target, reason) => {
    assert.equal(target, pane);
    assert.equal(reason, 'gate_reclaim');
    terminations++;
  };
  await assert.rejects(panes.stopThread(record.thread), e => e.code === 'worker_not_idle');
  assert.equal(terminations, 0, 'No stop while the CLI is still busy');
  report.checks.push('busy_live_cli_cannot_be_reclaimed');
  await signal({}); // SessionEnd has no prompt_id: it belongs to the session, not the last turn.
  assert.equal(agentState(panes.status(record.thread), [], root), 'ended');
  assert.equal(panes.status(record.thread).lifecycle, 'ended');
  assert.equal(panes.status(record.thread).stopped, false, 'zsh remains open');
  const end = store.read().filter(e => e.type === 'native_session_ended');
  assert.equal(end.length, 1);
  assert.equal(end[0].data.native_session, record.session);
  report.checks.push('session_end_without_prompt_is_ended_with_live_terminal');
  await panes.stopThread(record.thread);
  assert.equal(terminations, 1, 'Confirmed CLI exit makes its surviving shell reclaimable');
  report.checks.push('confirmed_exit_reclaim_does_not_require_another_stop_hook');
  report.status = 'PASS';
} catch (error) {
  report.error = String(error);
} finally {
  store?.close();
  writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
}
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
