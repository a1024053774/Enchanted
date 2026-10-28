// T-207: a turn the user sends after an Esc is theirs; its tool hooks count. Identity checks are not loosened.
// Failure modes, before implementation: every hook of the user's own turn is refused while the pane waits for
// release (the bug); hooks of the turn that was running when the user pressed Esc are accepted again (Codex does not
// retire that turn, so its turn id still matches); a second Esc inside the user's turn is ignored; a pane with no
// recorded interruption lets any turn through (null equals null); a hook with another prompt id is accepted.
// Oracle: T-207 ticket, 方案 2026-10-28 (user chose 回合结束就受理), and its third acceptance line.
// Usage (from the repo root): node workbench/tests/test_t207_interrupted_turn_hooks.ts <source root> <summary.json>
import assert from 'node:assert/strict';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [source, summary] = process.argv.slice(2);
const { validateHookEnvelope } = await import(pathToFileURL(join(source, 'workbench/src/questions.ts')).href);
const worktree = '/private/tmp/t207-worktree';

const codex = (active: any, interrupted: boolean, interruption: number | null) => ({
  record: { cli: 'Codex', worktree }, native: 'native-1', nativeFile: '/private/tmp/t207-rollout.jsonl', turn: 'turn-1',
  active: { id: 'submission-1', dispatch: 'input:x', at: '2026-10-28T00:00:00Z', nativeTurn: 'turn-1', ...active },
  failed: null, stopped: false, interrupted, interruption });
const codexHook = { hook_event_name: 'PreToolUse', session_id: 'native-1', cwd: worktree, turn_id: 'turn-1',
  transcript_path: '/private/tmp/t207-rollout.jsonl' };
const claude = (prompt: string) => ({
  record: { cli: 'Claude Code', worktree }, native: 'native-2', claudePromptId: prompt,
  active: { id: 'submission-2', dispatch: 'input:p', at: '2026-10-28T00:00:00Z', nativeTurn: null, interruption: 5 },
  failed: null, stopped: false, interrupted: true, interruption: 5 });
const claudeHook = (prompt: string) => ({ hook_event_name: 'PostToolUse', session_id: 'native-2', cwd: worktree, prompt_id: prompt,
  transcript_path: '/private/tmp/projects/x/native-2.jsonl' });

const cases: [string, any, any, boolean][] = [
  ['running_turn_not_interrupted', codex({}, false, null), codexHook, true],
  ['turn_cut_off_by_esc', codex({}, true, 5), codexHook, false],
  ['user_turn_after_esc', codex({ interruption: 5 }, true, 5), codexHook, true],
  ['user_turn_cut_off_again', codex({ interruption: 5 }, true, 9), codexHook, false],
  ['no_recorded_interruption', codex({ interruption: null }, true, null), codexHook, false],
  ['claude_user_turn_after_esc', claude('prompt-new'), claudeHook('prompt-new'), true],
  ['claude_other_prompt_id', claude('prompt-new'), claudeHook('prompt-old'), false],
];
const results = cases.map(([name, pane, hook, accepted]) => {
  let error: string | null = null;
  try { validateHookEnvelope(pane, hook); } catch (caught) { error = String((caught as any)?.code ?? caught); }
  return { name, expected: accepted ? 'accepted' : 'refused', actual: error === null ? 'accepted' : 'refused', error };
});
const failed = results.filter(row => row.expected !== row.actual).map(row => row.name);
writeFileSync(summary, JSON.stringify({ status: failed.length ? 'FAIL' : 'PASS', source, results, failed }, null, 2) + '\n');
console.log(failed.length ? 'FAIL ' + failed.join(', ') : 'PASS');
assert.deepEqual(failed, []);
