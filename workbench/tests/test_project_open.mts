// Real daemon entry check for 打开项目目录: start an isolated daemon, send the
// same operator commands the window sends, and check the project catalog.
// Usage: node tests/test_project_open.mts <report.json> [src-dir]
// The optional src-dir runs a copied (for example mutated) source tree.
//
// Ways this can fail, each with a check below:
//  1. two concurrent opens of different directories with one basename share an id
//  2. reopening the same directory (or a symlink to it) registers it twice
//  3. a relative path or a file is accepted as a project directory
//  4. removal succeeds for an unknown project or one with open terminals
//  5. a gate task joins an opened project from another repository
//  6. the repository check blocks a task in the opened project's own repository
//  7. removal succeeds for an opened project that already has gate tasks
// Check 1 holds at the real entry, but it does not catch a mutant that drops
// the post-await reread: the catalog's gate status reads finish without a
// macrotask, so two requests do not interleave there today. The reread guards
// a catalog that starts awaiting real I/O; it is kept by reasoning, not by this run.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, realpathSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';

const [report, srcArg] = process.argv.slice(2);
const src = resolve(srcArg ?? new URL('../src', import.meta.url).pathname);
const { request, startDaemon } = await import(join(src, 'transport.ts'));
const { readOperatorCredential } = await import(join(src, 'credentials.ts'));

const root = realpathSync(mkdtempSync(join(tmpdir(), 'a2a-project-open-')));
const state = join(root, 'state');
const repo = (path: string) => {
  mkdirSync(path, { recursive: true });
  execFileSync('git', ['init', '-q', '-b', 'main', path]);
  execFileSync('git', ['-C', path, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'base']);
  return path;
};
const one = repo(join(root, 'one', 'shared')), two = repo(join(root, 'two', 'shared'));
const gated = repo(join(root, 'gated')), owned = repo(join(root, 'owned'));
symlinkSync(one, join(root, 'link'));
writeFileSync(join(root, 'file'), '');

const checks: Record<string, unknown> = {};
let operator: unknown;
const call = (input: Record<string, unknown>) => request(state, input, operator);
const createTask = async (task: string, project: string, path: string) => {
  const card = join(root, task + '.json');
  writeFileSync(card, JSON.stringify({ id: task, source: null, goal: '项目目录验收', non_goals: ['不调用模型'],
    paths: { allow: ['criterion.py'], deny: [] }, oracle_paths: ['criterion.py'],
    completion_conditions: [{ argv: ['python3', 'criterion.py'] }], red_commands: [], task_type: '前端界面',
    repair_target: null, complexity: 'M', executor: { cli: 'Codex', model: 'gpt-6.1-sol', effort: 'high' }, base_commit: null, writer: null }));
  const saved = await call({ command: 'card_save', task, card, expected_version: 0 });
  assert.ok(saved.ok, JSON.stringify(saved));
  return call({ command: 'create', task, repo: path, branch: 'refs/heads/main', card_version: 1, project, title: task });
};
try {
  process.env.A2A_OPERATOR_CREDENTIAL = join(state, `desktop-operator-${randomUUID()}.json`);
  mkdirSync(state, { mode: 0o700 });
  await startDaemon(state, {});
  operator = readOperatorCredential(state);
  for (const n of [1, 2, 3]) assert.ok((await createTask('gated-' + n, 'gated', gated)).ok);

  const [first, second] = await Promise.all([call({ command: 'project_open', repo: one }), call({ command: 'project_open', repo: two })]);
  checks.concurrent = [first, second];
  assert.ok(first.ok && second.ok);
  assert.notEqual(first.project, second.project);
  const snapshot = await call({ command: 'sidebar_snapshot' });
  const repos = Object.fromEntries(snapshot.projects.map((row: any) => [row.project_id, row.repo]));
  checks.catalog = repos;
  assert.equal(repos[first.project], one);
  assert.equal(repos[second.project], two);

  const again = await call({ command: 'project_open', repo: join(root, 'link') });
  checks.reopen = again;
  assert.deepEqual([again.ok, again.project, again.created], [true, first.project, false]);

  for (const bad of ['relative/dir', join(root, 'file')]) {
    const result = await call({ command: 'project_open', repo: bad });
    checks['bad:' + bad] = result;
    assert.equal(result.ok, false);
  }

  const unknown = await call({ command: 'project_remove', project: 'no-such-project' });
  assert.equal(unknown.error, 'unknown_project');
  const shell = await call({ command: 'shell_start', cwd: two, project: second.project });
  assert.ok(shell.ok, JSON.stringify(shell));
  const busy = await call({ command: 'project_remove', project: second.project });
  checks.removeWithPane = busy;
  assert.equal(busy.error, 'project_has_open_panes');
  assert.ok((await call({ command: 'shell_close', launch: shell.launch.id ?? shell.launch })).ok);
  const removed = await call({ command: 'project_remove', project: second.project });
  checks.remove = removed;
  assert.ok(removed.ok);

  const foreign = await createTask('foreign', first.project, two);
  checks.createForeign = foreign;
  assert.equal(foreign.error, 'project_repo_mismatch');
  const opened = await call({ command: 'project_open', repo: owned });
  const own = await createTask('owned-1', opened.project, owned);
  checks.createOwn = { ok: own.ok, error: own.error ?? null };
  assert.ok(own.ok, JSON.stringify(own));
  const withTasks = await call({ command: 'project_remove', project: opened.project });
  checks.removeWithTasks = withTasks;
  assert.equal(withTasks.error, 'project_has_tasks');
  checks.status = 'PASS';
} catch (error) {
  checks.status = 'FAIL';
  checks.error = String(error);
} finally {
  if (operator) await call({ command: 'daemon_stop' }).catch((error: unknown) => { checks.stopError = String(error); });
  checks.root = root;
  writeFileSync(report, JSON.stringify(checks, null, 2) + '\n');
  console.log(JSON.stringify({ status: checks.status, error: checks.error ?? null, report }));
  process.exitCode = checks.status === 'PASS' ? 0 : 1;
}
