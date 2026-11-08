// T-251: a hook's cwd follows the agent's shell. A Claude worker that runs `cd workbench/app` in Bash reports that
// subdirectory in every later hook, and the strict `cwd === worktree` check made the whole turn untrusted.
// Requirement (T-251 ticket, user 2026-11-07 “现在这样的问题得修复”): a cwd inside the worker's workspace, its
// subdirectories included, counts as this session; outside the workspace stays refused. The directories the gate
// gave this launch with --add-dir (extra_directories) are the agent's own as well; Claude Code lets it cd there.
// Failure modes, listed before the fix: a subdirectory is refused (the bug); a sibling whose name only starts with
// the worktree path is accepted (string prefix); a `..` path that leaves the worktree is accepted (no normalising);
// a relative or missing cwd is accepted; the rule differs between Claude Code and Codex.
// Usage (from the repo root): node workbench/tests/test_t251_hook_cwd.ts <source root> <summary.json>
import assert from 'node:assert/strict';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [source, summary] = process.argv.slice(2);
const { validateHookEnvelope } = await import(pathToFileURL(join(source, 'workbench/src/questions.ts')).href);
const worktree = '/private/tmp/t251-worktree';
const extra = '/private/tmp/t251-shared-data';

const claude = { record: { cli: 'Claude Code', worktree, extra_directories: [extra] }, native: 'native-c', claudePromptId: 'prompt-1',
  active: { id: 'submission-1', dispatch: 'input:p', at: '2026-11-07T00:00:00Z', nativeTurn: null, interruption: null },
  failed: null, stopped: false, interrupted: false, interruption: null };
const claudeHook = (cwd: unknown) => ({ hook_event_name: 'PostToolUse', session_id: 'native-c', cwd, prompt_id: 'prompt-1',
  transcript_path: '/private/tmp/projects/x/native-c.jsonl' });
const codex = { record: { cli: 'Codex', worktree }, native: 'native-x', nativeFile: '/private/tmp/t251-rollout.jsonl', turn: 'turn-1',
  active: { id: 'submission-2', dispatch: 'input:x', at: '2026-11-07T00:00:00Z', nativeTurn: 'turn-1', interruption: null },
  failed: null, stopped: false, interrupted: false, interruption: null };
const codexHook = (cwd: unknown) => ({ hook_event_name: 'PreToolUse', session_id: 'native-x', cwd, turn_id: 'turn-1',
  transcript_path: '/private/tmp/t251-rollout.jsonl' });

const cases: [string, any, any, boolean][] = [
  ['worktree_root', claude, claudeHook(worktree), true],
  ['subdirectory', claude, claudeHook(`${worktree}/workbench/app/panels`), true],
  ['dotdot_back_inside', claude, claudeHook(`${worktree}/workbench/..`), true],
  ['extra_directory', claude, claudeHook(extra), true],
  ['extra_subdirectory', claude, claudeHook(`${extra}/cache`), true],
  ['codex_subdirectory', codex, codexHook(`${worktree}/src`), true],
  ['outside', claude, claudeHook('/private/tmp'), false],
  ['sibling_with_same_prefix', claude, claudeHook(`${worktree}-evil`), false],
  ['dotdot_escape', claude, claudeHook(`${worktree}/sub/../../elsewhere`), false],
  ['relative', claude, claudeHook('workbench/app'), false],
  ['missing', claude, claudeHook(undefined), false],
  ['codex_outside', codex, codexHook('/private/tmp/other'), false],
  // A worker without extra directories does not gain one from another launch.
  ['no_extra_granted', { ...claude, record: { cli: 'Claude Code', worktree } }, claudeHook(extra), false],
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
