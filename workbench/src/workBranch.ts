// T-180: when the controller creates a task without naming a work branch, the backend picks one: the branch the
// repo's earlier tasks use (the gate keeps one work branch per repo), else `<prefix><project>` made from the repo's
// current HEAD. A branch of that name already there is used as it is. main/master are never written; nothing is pushed.
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { Refusal } from './gates/core.ts';

const run = promisify(execFile);
export const defaultWorkBranchPrefix = 'enchanted/';

async function git(repo: string, args: string[]) {
  return (await run('git', ['-C', repo, ...args], { encoding: 'utf8' })).stdout.trim();
}
async function exists(repo: string, ref: string) {
  try { await git(repo, ['rev-parse', '--verify', '--quiet', ref]); return true; }
  catch { return false; }
}

// A prefix is valid when `<prefix>name` is a legal branch name.
export async function checkWorkBranchPrefix(prefix: unknown) {
  if (typeof prefix !== 'string' || !prefix || prefix.startsWith('-') || /\s/.test(prefix)) throw new Refusal('invalid_work_branch_prefix');
  try { await run('git', ['check-ref-format', '--branch', prefix + 'name']); }
  catch { throw new Refusal('invalid_work_branch_prefix'); }
  return prefix;
}

export async function defaultWorkBranch(repo: string, project: string, prefix: string, repoBranch: string | null) {
  if (repoBranch) return { branch: repoBranch, work_branch: { ref: repoBranch, created: false, reason: 'repo_tasks' } };
  const ref = `refs/heads/${prefix}${project}`;
  try { await run('git', ['check-ref-format', ref]); }
  catch { throw new Refusal('invalid_work_branch', { ref }); }
  if (await exists(repo, ref)) return { branch: ref, work_branch: { ref, created: false, reason: 'existing' } };
  const from = await git(repo, ['rev-parse', '--abbrev-ref', 'HEAD']).catch(() => null);
  try { await git(repo, ['branch', ref.slice('refs/heads/'.length), 'HEAD']); }
  catch (error) { throw new Refusal('work_branch_create_failed', { ref, reason: String(error) }); }
  return { branch: ref, work_branch: { ref, created: true, reason: 'default', from } };
}
