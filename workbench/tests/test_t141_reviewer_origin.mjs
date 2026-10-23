// Replay captured foreign-folder hooks to check the isolated runtime fault.
// Failure modes: foreign cwd accepted without corruption; corruption rewrites the
// persistent launch; forged in-memory origin still blocks the intended gate case.
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { validateHookEnvelope } from '../src/questions.ts';
const [input, output] = process.argv.slice(2);
if (!output || existsSync(output)) throw new Error('Fresh summary path required');
const report = { status: 'INCOMPLETE', scope: 'Captured native hook envelope replay only; no live reviewer/gate result claim', checks: [] };
try {
  const captured = JSON.parse(readFileSync(input, 'utf8'));
  assert.ok(Array.isArray(captured) && captured.length > 0, 'Captured hook inputs required');
  for (const item of captured) {
    const { launch, review, hook } = item;
    assert.equal(launch.worktree, review.candidate_workspace);
    assert.equal(hook.cwd, review.workspace);
    assert.notEqual(hook.cwd, launch.worktree);
    const pane = { record: structuredClone(launch), native: hook.session_id,
      active: { nativeTurn: hook.turn_id }, turn: hook.turn_id };
    assert.throws(() => validateHookEnvelope(pane, hook), error => error.code === 'question_origin_unverified');
    pane.record = { ...pane.record, worktree: review.workspace };
    validateHookEnvelope(pane, hook);
    assert.equal(launch.worktree, review.candidate_workspace);
    report.checks.push({ case: item.case, before: 'question_origin_unverified',
      forged_memory_origin: 'hook envelope passes', persistent_launch_worktree: 'unchanged' });
  }
  report.status = 'PASS';
} catch (error) { report.error = String(error); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
